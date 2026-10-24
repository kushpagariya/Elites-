"""Runnable scaffold. Analytics seams deliberately return 501 until connected."""
import json
import os
from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .schemas import Project, Scenario, ScenarioCreate, Assumptions, EvaluateRequest, PortfolioRequest, RescueRequest, EvaluationData, PortfolioResult, Envelope
from .repositories import store

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "data" / "demo"
app = FastAPI(title="StoreScout API", version="1")
app.add_middleware(CORSMiddleware, allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"), "http://127.0.0.1:3000"], allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Idempotency-Key"])


def envelope(data, **meta):
    return {"data": data, "meta": {"contract_version": "1", "fixture_id": "demo-1", **meta}}


def project(project_id):
    if project_id != "demo":
        raise HTTPException(404, "Project not found")
    return Project.model_validate_json((DATA_ROOT / "project.json").read_text(encoding="utf-8"))


def scenario(project_id, scenario_id):
    p = project(project_id)
    if scenario_id == "baseline":
        return Scenario(scenario_id="baseline", project_id=project_id, name="Current baseline", budget_inr=p.budget_inr, assumptions=Assumptions()).model_dump()
    value = store.get("scenario", project_id, scenario_id)
    if not value:
        raise HTTPException(404, "Scenario not found")
    return value


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    code = {404: "NOT_FOUND", 409: "CONFLICT", 501: "NOT_IMPLEMENTED"}.get(exc.status_code, "REQUEST_FAILED")
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": code, "message": str(exc.detail), "details": []}})


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": {"code": "INVALID_INPUT", "message": "Correct the indicated fields.", "details": [{"field": ".".join(map(str, e["loc"])), "reason": e["msg"]} for e in exc.errors()]}})


@app.get("/api/v1/health")
def health():
    return envelope({"status": "ok", "implementation_status": "scaffold"})


@app.get("/api/v1/projects/{project_id}", response_model=Envelope[Project])
def read_project(project_id: str):
    return envelope(project(project_id).model_dump())


@app.get("/api/v1/projects/{project_id}/scenarios", response_model=Envelope[list[Scenario]])
def read_scenarios(project_id: str):
    return envelope([scenario(project_id, "baseline"), *store.list_objects("scenario", project_id)])


@app.post("/api/v1/projects/{project_id}/scenarios", status_code=201, response_model=Envelope[Scenario])
def create_scenario(project_id: str, body: ScenarioCreate):
    base = scenario(project_id, body.base_scenario_id)
    known = {s.site_id for s in project(project_id).sites}
    if set(body.assumptions.site_overrides) - known:
        raise HTTPException(422, "site_overrides contains an unknown site")
    item = Scenario(scenario_id=str(uuid4()), project_id=project_id, base_scenario_id=body.base_scenario_id, name=body.name, budget_inr=base["budget_inr"] if body.budget_inr is None else body.budget_inr, assumptions=body.assumptions).model_dump()
    store.save("scenario", project_id, item["scenario_id"], item)
    return envelope(item, scenario_id=item["scenario_id"])


@app.get("/api/v1/projects/{project_id}/infrastructure")
def infrastructure(project_id: str):
    project(project_id)
    return envelope(json.loads((DATA_ROOT / "infrastructure.json").read_text(encoding="utf-8")))


@app.post("/api/v1/projects/{project_id}/evaluate", response_model=Envelope[EvaluationData])
def evaluate(project_id: str, body: EvaluateRequest):
    scenario(project_id, body.scenario_id)
    # Backend owner connects domain.pipeline.run_evaluation and validates EvaluationData.
    raise HTTPException(501, "Analytical pipeline is not connected. Follow docs/handoffs/BACKEND.md and LOGIC.md.")


@app.post("/api/v1/projects/{project_id}/portfolios", response_model=Envelope[PortfolioResult])
def portfolios(project_id: str, body: PortfolioRequest):
    project(project_id)
    raise HTTPException(501, "Portfolio pipeline is not connected; no recommendation has been computed.")


@app.post("/api/v1/projects/{project_id}/sites/{site_id}/rescue")
def rescue(project_id: str, site_id: str, body: RescueRequest):
    if site_id not in {s.site_id for s in project(project_id).sites}:
        raise HTTPException(404, "Site not found")
    raise HTTPException(501, "Rescue calculation is not connected.")


@app.get("/api/v1/projects/{project_id}/{resource}")
def planned_query(project_id: str, resource: str):
    project(project_id)
    if resource not in {"features", "dayparts", "rankings", "model"}:
        raise HTTPException(404, "Resource not found")
    raise HTTPException(501, f"{resource} is not implemented yet; see the shared contract.")
