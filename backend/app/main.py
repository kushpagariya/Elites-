"""StoreScout HTTP boundary. Domain modules own every numerical decision."""
import logging
import os
import sqlite3
from typing import Annotated, Literal

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException

from .repositories import store
from .schemas import Project, Scenario, ScenarioCreate, EvaluateRequest, PortfolioRequest, RescueRequest, EvaluationData, PortfolioResult, RescueResult, SiteAnalysis, Envelope, ErrorEnvelope
from .services import analytics, catalogue, reports, sources
from .services.errors import ServiceError

app = FastAPI(title="StoreScout API", version="1", responses={status: {"model": ErrorEnvelope} for status in (404, 409, 422, 500, 502, 503)})
app.add_middleware(CORSMiddleware, allow_origins=list(dict.fromkeys([os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"), "http://127.0.0.1:3000"])), allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Idempotency-Key"], expose_headers=["Content-Disposition"])
Token = Annotated[str | None, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


def envelope(data, **meta):
    return {"data": data, "meta": {"contract_version": "1", "fixture_id": "demo-1", **meta}}


def error(status, code, message, details=None):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details or []}})


@app.exception_handler(ServiceError)
async def service_error(request: Request, exc: ServiceError):
    return error(exc.status, exc.code, exc.message)


@app.exception_handler(store.IdempotencyConflict)
async def idempotency_error(request: Request, exc: store.IdempotencyConflict):
    return error(409, "IDEMPOTENCY_CONFLICT", str(exc))


@app.exception_handler(sqlite3.OperationalError)
async def database_error(request: Request, exc: sqlite3.OperationalError):
    logging.getLogger(__name__).exception("Persistence operation failed")
    return error(503, "PERSISTENCE_UNAVAILABLE", "Local persistence is unavailable; retry after checking the database.")


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 409: "CONFLICT", 501: "NOT_IMPLEMENTED"}.get(exc.status_code, "REQUEST_FAILED")
    return error(exc.status_code, code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return error(422, "INVALID_INPUT", "Correct the indicated fields.", [{"field": ".".join(map(str, e["loc"])), "reason": e["msg"]} for e in exc.errors()])


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Unexpected API failure")
    return error(500, "INTERNAL_ERROR", "Request failed; no partial result is available.")


@app.get("/api/v1")
def api_index():
    return envelope({"service": "StoreScout", "docs_url": "/docs", "health_url": "/api/v1/health"})


@app.get("/api/v1/health")
def health():
    # Liveness is deliberately distinct from model/analytical readiness.
    return envelope({"status": "ok", "implementation_status": "integration", "analytics_readiness": "Check model endpoint and evaluate; health does not certify analytics."})


@app.get("/api/v1/projects/{project_id}", response_model=Envelope[Project])
def read_project(project_id: str):
    return envelope(catalogue.project(project_id).model_dump(mode="json"))


@app.get("/api/v1/projects/{project_id}/scenarios", response_model=Envelope[list[Scenario]])
def read_scenarios(project_id: str):
    return envelope([catalogue.scenario(project_id, "baseline"), *store.list_objects("scenario", project_id)])


@app.get("/api/v1/projects/{project_id}/scenarios/{scenario_id}", response_model=Envelope[Scenario])
def read_scenario(project_id: str, scenario_id: str):
    return envelope(catalogue.scenario(project_id, scenario_id), scenario_id=scenario_id)


@app.post("/api/v1/projects/{project_id}/scenarios", status_code=201, response_model=Envelope[Scenario])
def create_scenario(project_id: str, body: ScenarioCreate, idempotency_key: Token = None):
    result = catalogue.create_scenario(project_id, body, idempotency_key)
    return envelope(result, scenario_id=result["scenario_id"])


@app.get("/api/v1/projects/{project_id}/infrastructure")
def infrastructure(project_id: str):
    catalogue.project(project_id)
    return envelope(sources.installed_snapshot()["infrastructure"])


@app.get("/api/v1/projects/{project_id}/features")
def features(project_id: str):
    catalogue.project(project_id)
    snapshot = sources.installed_snapshot()
    return envelope({**snapshot, "prepared": False, "note": "Frozen source inputs; derived spatial features require the ML implementation."})


@app.get("/api/v1/projects/{project_id}/model")
def model_card(project_id: str):
    catalogue.project(project_id)
    bundle = sources.model_bundle()
    if bundle is None:
        raise ServiceError(503, "MODEL_UNAVAILABLE", "No fitted model bundle is installed; no model metrics are claimed.")
    return envelope({key: value for key, value in bundle.items() if key != "artifact_path"})


@app.post("/api/v1/projects/{project_id}/evaluate", response_model=Envelope[EvaluationData])
def evaluate(project_id: str, body: EvaluateRequest, idempotency_key: Token = None):
    result = analytics.evaluate(project_id, body, idempotency_key)
    return envelope(result, scenario_id=result["scenario_id"], evaluation_id=result["evaluation_id"])


@app.get("/api/v1/projects/{project_id}/evaluations/{evaluation_id}", response_model=Envelope[EvaluationData])
def read_evaluation(project_id: str, evaluation_id: str):
    value = analytics.saved(project_id, "evaluation", evaluation_id)
    return envelope(value, scenario_id=value["scenario_id"], evaluation_id=evaluation_id)


@app.get("/api/v1/projects/{project_id}/sites/{site_id}/analysis", response_model=Envelope[SiteAnalysis])
def read_analysis(project_id: str, site_id: str, evaluation_id: str):
    value = analytics.saved(project_id, "evaluation", evaluation_id)
    item = next((row for row in value["site_analyses"] if row["site_id"] == site_id), None)
    if item is None:
        raise ServiceError(404, "NOT_FOUND", "Site not found in evaluation")
    return envelope(item, scenario_id=value["scenario_id"], evaluation_id=evaluation_id)


@app.get("/api/v1/projects/{project_id}/rankings")
def rankings(project_id: str, evaluation_id: str):
    value = analytics.saved(project_id, "evaluation", evaluation_id)
    return envelope({"evaluation_id": evaluation_id, "rankings": value["rankings"], "diagnoses": {row["site_id"]: row["failfast"] for row in value["site_analyses"]}}, scenario_id=value["scenario_id"], evaluation_id=evaluation_id)


@app.get("/api/v1/projects/{project_id}/dayparts")
def dayparts(project_id: str, evaluation_id: str, time_bin: str | None = None):
    analytics.saved(project_id, "evaluation", evaluation_id)
    context = analytics.saved(project_id, "evaluation_context", evaluation_id)
    if time_bin is not None and time_bin not in context["project"]["inputs"]["weights"]["time_bins"]:
        raise ServiceError(422, "INVALID_INPUT", "Unknown DaypartDNA time bin")
    raise ServiceError(503, "DAYPARTS_UNAVAILABLE", "Detailed computed DaypartDNA response is awaiting the agreed ML schema; raw weights are not opportunity results.")


@app.post("/api/v1/projects/{project_id}/portfolios", response_model=Envelope[PortfolioResult])
def portfolios(project_id: str, body: PortfolioRequest, idempotency_key: Token = None):
    value = analytics.portfolio(project_id, body, idempotency_key)
    return envelope(value, evaluation_id=value["evaluation_id"])


@app.get("/api/v1/projects/{project_id}/portfolios/{portfolio_run_id}", response_model=Envelope[PortfolioResult])
def read_portfolio(project_id: str, portfolio_run_id: str):
    value = analytics.saved(project_id, "portfolio", portfolio_run_id)
    return envelope(value, evaluation_id=value["evaluation_id"])


@app.post("/api/v1/projects/{project_id}/sites/{site_id}/rescue", response_model=Envelope[RescueResult])
def rescue(project_id: str, site_id: str, body: RescueRequest, idempotency_key: Token = None):
    value = analytics.rescue(project_id, site_id, body, idempotency_key)
    return envelope(value, evaluation_id=value["evaluation_id"])


@app.get("/api/v1/projects/{project_id}/rescues/{rescue_id}", response_model=Envelope[RescueResult])
def read_rescue(project_id: str, rescue_id: str):
    value = analytics.saved(project_id, "rescue", rescue_id)
    return envelope(value, evaluation_id=value["evaluation_id"])


@app.get("/api/v1/projects/{project_id}/reports/{evaluation_id}", response_class=HTMLResponse)
def report(project_id: str, evaluation_id: str, portfolio_run_id: str | None = None, format: Literal["html", "json"] = "html"):
    value = reports.report_data(project_id, evaluation_id, portfolio_run_id)
    headers = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    if format == "json":
        return JSONResponse(envelope(value, evaluation_id=evaluation_id), headers=headers)
    headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'"
    return HTMLResponse(reports.render_html(value), headers=headers)
