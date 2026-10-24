"""Local StoreScout API: immutable scenarios, saved evidence and deterministic analytics."""
import json
import os
import logging
from html import escape
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from .schemas import Project, Scenario, ScenarioCreate, Assumptions, EvaluateRequest, PortfolioRequest, RescueRequest, RescueResult, EvaluationData, PortfolioResult, Envelope, GeographicContext, DaypartsData, RankingData, ModelCard, SiteAnalysis
from .repositories import store
from . import services

ROOT=Path(__file__).resolve().parents[2]
DATA_ROOT=ROOT/"data"/"demo"
app=FastAPI(title="StoreScout API",version="1.1")
app.add_middleware(CORSMiddleware,allow_origins=[os.getenv("FRONTEND_ORIGIN","http://localhost:3000"),"http://127.0.0.1:3000"],allow_methods=["GET","POST"],allow_headers=["Content-Type","Idempotency-Key"])


def envelope(data,**meta):
    return {"data":data,"meta":{"contract_version":"1","schema_revision":"analytical-2","fixture_id":"demo-1",**meta}}


def project(project_id):
    if project_id!="demo": raise HTTPException(404,"Project not found")
    return Project.model_validate_json((DATA_ROOT/"project.json").read_text(encoding="utf-8"))


def scenario(project_id,scenario_id):
    p=project(project_id)
    if scenario_id=="baseline":
        return Scenario(scenario_id="baseline",project_id=project_id,name="Current baseline",budget_inr=p.budget_inr,assumptions=Assumptions()).model_dump()
    value=store.get("scenario",project_id,scenario_id)
    if not value: raise HTTPException(404,"Scenario not found")
    return Scenario.model_validate(value).model_dump()


def saved_evaluation(project_id,evaluation_id):
    project(project_id)
    value=store.get("evaluation",project_id,evaluation_id)
    if not value: raise HTTPException(404,"Saved evaluation not found")
    return value


def invoke(function,*args):
    try: return function(*args)
    except KeyError: raise HTTPException(404,"Saved input or result not found")
    except LookupError as exc: raise HTTPException(409,str(exc))
    except ValueError as exc: raise HTTPException(422,str(exc))
    except Exception:
        logging.exception("StoreScout computation failed")
        raise HTTPException(503,"The calculation could not be completed. Your saved inputs are unchanged.")


@app.exception_handler(HTTPException)
async def http_error(request:Request,exc:HTTPException):
    code={404:"NOT_FOUND",409:"CONFLICT",422:"INVALID_INPUT",501:"NOT_IMPLEMENTED",503:"UNAVAILABLE"}.get(exc.status_code,"REQUEST_FAILED")
    return JSONResponse(status_code=exc.status_code,content={"error":{"code":code,"message":str(exc.detail),"details":[]}})


@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):
    return JSONResponse(status_code=422,content={"error":{"code":"INVALID_INPUT","message":"Correct the indicated fields.","details":[{"field":".".join(map(str,e["loc"])),"reason":e["msg"]} for e in exc.errors()]}})


@app.get("/api/v1/health")
def health(): return envelope({"status":"ok","implementation_status":"assumption_based_analytics"})


@app.get("/api/v1/projects/{project_id}",response_model=Envelope[Project])
def read_project(project_id:str): return envelope(project(project_id).model_dump())


@app.get("/api/v1/projects/{project_id}/scenarios",response_model=Envelope[list[Scenario]])
def read_scenarios(project_id:str):
    return envelope([scenario(project_id,"baseline"),*[Scenario.model_validate(s).model_dump() for s in store.list_objects("scenario",project_id)]])


@app.post("/api/v1/projects/{project_id}/scenarios",status_code=201,response_model=Envelope[Scenario])
def create_scenario(project_id:str,body:ScenarioCreate):
    base=scenario(project_id,body.base_scenario_id)
    if set(body.assumptions.site_overrides)-{s.site_id for s in project(project_id).sites}: raise HTTPException(422,"A location override contains an unknown site.")
    item=Scenario(scenario_id=str(uuid4()),project_id=project_id,base_scenario_id=body.base_scenario_id,name=body.name,budget_inr=base["budget_inr"] if body.budget_inr is None else body.budget_inr,assumptions=body.assumptions).model_dump()
    store.save("scenario",project_id,item["scenario_id"],item)
    return envelope(item,scenario_id=item["scenario_id"])


@app.get("/api/v1/projects/{project_id}/infrastructure")
def infrastructure(project_id:str):
    project(project_id)
    return envelope(json.loads((DATA_ROOT/"infrastructure.json").read_text(encoding="utf-8")))


@app.post("/api/v1/projects/{project_id}/evaluate",response_model=Envelope[EvaluationData])
def evaluate(project_id:str,body:EvaluateRequest,request:Request):
    value=invoke(services.evaluate,project(project_id).model_dump(),scenario(project_id,body.scenario_id),body.feature_snapshot_id,request.headers.get("Idempotency-Key"))
    return envelope(value,evaluation_id=value["evaluation_id"],source_snapshot_id=value["evidence"]["source_snapshot_id"])


@app.get("/api/v1/projects/{project_id}/evaluations",response_model=Envelope[list[EvaluationData]])
def evaluations(project_id:str):
    project(project_id)
    return envelope(store.list_objects("evaluation",project_id))


@app.get("/api/v1/projects/{project_id}/evaluations/{evaluation_id}",response_model=Envelope[EvaluationData])
def evaluation(project_id:str,evaluation_id:str): return envelope(saved_evaluation(project_id,evaluation_id))


@app.get("/api/v1/projects/{project_id}/sites/{site_id}/analysis",response_model=Envelope[SiteAnalysis])
def site_analysis(project_id:str,site_id:str,evaluation_id:str):
    value=saved_evaluation(project_id,evaluation_id)
    found=next((s for s in value["site_analyses"] if s["site_id"]==site_id),None)
    if not found: raise HTTPException(404,"Location not found")
    return envelope(found,evaluation_id=evaluation_id)


@app.post("/api/v1/projects/{project_id}/portfolios",response_model=Envelope[PortfolioResult])
def portfolios(project_id:str,body:PortfolioRequest):
    return envelope(invoke(services.portfolio,project(project_id).model_dump(),body))


@app.get("/api/v1/projects/{project_id}/portfolios/{portfolio_run_id}",response_model=Envelope[PortfolioResult])
def saved_portfolio(project_id:str,portfolio_run_id:str):
    project(project_id); value=store.get("portfolio",project_id,portfolio_run_id)
    if not value: raise HTTPException(404,"Saved portfolio not found")
    return envelope(value)


@app.post("/api/v1/projects/{project_id}/sites/{site_id}/rescue",response_model=Envelope[RescueResult])
def rescue(project_id:str,site_id:str,body:RescueRequest):
    if site_id not in {s.site_id for s in project(project_id).sites}: raise HTTPException(404,"Location not found")
    return envelope(invoke(services.rescue,project_id,site_id,body))


@app.get("/api/v1/projects/{project_id}/dayparts",response_model=Envelope[DaypartsData])
def dayparts(project_id:str,evaluation_id:str,time_bin:str|None=None):
    value=saved_evaluation(project_id,evaluation_id)
    bins={"weekday_morning","weekday_lunch","weekday_evening","weekday_night","weekend_day","weekend_evening"}
    if time_bin is not None and time_bin not in bins: raise HTTPException(422,"Unknown time period")
    return envelope({"evaluation_id":evaluation_id,"sites":[{"site_id":s["site_id"],"profiles":[p for p in s["dayparts"] if time_bin is None or p["time_bin"]==time_bin]} for s in value["site_analyses"]]})


@app.get("/api/v1/projects/{project_id}/rankings",response_model=Envelope[RankingData])
def rankings(project_id:str,evaluation_id:str):
    value=saved_evaluation(project_id,evaluation_id)
    return envelope({"evaluation_id":evaluation_id,"rankings":value["rankings"],"exclusions":[s for s in value["site_analyses"] if s["failfast"]["status"] in {"REJECTED","REVIEW_REQUIRED"}]})


@app.get("/api/v1/projects/{project_id}/features",response_model=Envelope[GeographicContext])
def features(project_id:str,evaluation_id:str):
    saved_evaluation(project_id,evaluation_id); context=invoke(services.load_context,project_id,evaluation_id)
    frozen=context["network_context"]["inputs"]
    from .domain.pipeline import catchment_ring
    catchments=[{"site_id":site["site_id"],"geometry":catchment_ring(site["latitude"],site["longitude"],frozen["weights"]["catchment_radius_m"])} for site in context["network_context"]["project"]["sites"]]
    return envelope({"evaluation_id":evaluation_id,"pois":frozen["pois"],"cells":frozen["cells"],"roads":[],"competitors":[],"catchments":catchments,"catchment_radius_m":frozen["weights"]["catchment_radius_m"],"limitations":["Road and observed competitor layers are unavailable.","All geographic points are SYNTHETIC; catchments show assumed straight-line radii."]})


@app.get("/api/v1/projects/{project_id}/model",response_model=Envelope[ModelCard])
def model(project_id:str):
    # TODO: needs ML — activate only an approved artifact plus compatible feature manifest and held-out model card.
    project(project_id)
    return envelope({"method_mode":"scenario_assumptions","model_artifact_id":None,"estimator_version":services.ENGINE_VERSION,"feature_schema":"wallet-reference-v1","trained_model_available":False,"metrics":None,"limitations":["No approved trained CatBoost artifact or compatible feature manifest exists. A versioned assumption-based estimator is active."]})


@app.get("/api/v1/projects/{project_id}/reports/{evaluation_id}")
def report(project_id:str,evaluation_id:str,portfolio_run_id:str,format:str=Query("html",pattern="^(html|json)$")):
    value=saved_evaluation(project_id,evaluation_id); portfolio=store.get("portfolio",project_id,portfolio_run_id)
    if not portfolio: raise HTTPException(404,"Saved portfolio not found")
    if portfolio["evaluation_id"]!=evaluation_id: raise HTTPException(409,"The portfolio belongs to another saved evaluation.")
    if portfolio["solver_status"] in {"UNAVAILABLE","UNKNOWN"}: raise HTTPException(409,"A completed portfolio calculation is required.")
    context=invoke(services.load_context,project_id,evaluation_id)
    data={"evaluation":value,"portfolio":portfolio,"scenario":context["scenario"],"project":context["network_context"]["project"],"evidence":value["evidence"],"method":"Assumption-based reference sales; calibrated attraction; full-network wallet allocation; discounted incremental cash flow; OR-Tools subset selection."}
    if format=="json": return JSONResponse(data,headers={"Content-Disposition":f'attachment; filename="storescout-{evaluation_id}.json"'})
    def safe(v): return escape(str(v),quote=True)
    rows="".join(f'<tr><th>{safe(s["site_id"])}</th><td>{s["annual_revenue_inr"]:,.2f}</td><td>{s["operating_profit_inr"]:,.2f}</td><td>{s["npv_inr"]:,.2f}</td><td>{safe(s["failfast"]["status"])}</td></tr>' for s in value["site_analyses"])
    limitations="".join(f'<li>{safe(x)}</li>' for x in value["evidence"]["limitations"])
    html=f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>StoreScout decision report</title><style>body{{font:16px/1.6 system-ui;color:#17151c;max-width:1000px;margin:3rem auto;padding:0 1.5rem}}h1{{letter-spacing:-.04em}}h2{{color:#6940b5}}table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}td,th{{padding:.7rem;border-bottom:1px solid #ddd;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}}.label{{background:#f1eafc;padding:.4rem .7rem}}@media print{{body{{margin:0}}}}</style><h1>StoreScout · Decision report</h1><p class="label">SYNTHETIC inputs · ASSUMED commercial parameters · Assumption-based estimates</p><p>Saved scenario: {safe(value["scenario_id"])}<br>Evaluation: {safe(evaluation_id)}<br>Portfolio: {safe(portfolio_run_id)}</p><h2>Investment decision</h2><p>Selected locations: {safe(", ".join(portfolio["selected_site_ids"]) or "None — a valid empty portfolio")}<br>Network NPV (INR): {portfolio["full_network_npv_inr"]:,.2f}<br>CAPEX (INR): {portfolio["budget_used_inr"]:,.2f}<br>Remaining budget (INR): {portfolio["budget_unused_inr"]:,.2f}<br>Solver: {safe(portfolio["solver_status"])} · {portfolio["evaluated_subsets"]} / {portfolio["total_subsets"]} subsets examined</p><h2>Saved location results</h2><table><thead><tr><th>Location</th><th>Annual sales (INR)</th><th>Operating profit (INR)</th><th>Network NPV (INR)</th><th>Diagnosis</th></tr></thead><tbody>{rows}</tbody></table><h2>Methods and limitations</h2><p>{safe(data["method"])}</p><ul>{limitations}</ul><h2>Saved assumptions, evidence and full results</h2><p>Amounts are INR; rent is monthly, operating cost annual, ROI a fraction and payback years. Null means unknown or not applicable. Source dates are not available for synthetic POIs. Sensitivity is not a prediction interval. Branch losses and candidate overlap enter the shared allocation once.</p><pre>{safe(json.dumps(data,indent=2,ensure_ascii=False))}</pre></html>'
    return HTMLResponse(html,headers={"Content-Disposition":f'attachment; filename="storescout-{evaluation_id}.html"',"Content-Security-Policy":"default-src 'none'; style-src 'unsafe-inline'"})
