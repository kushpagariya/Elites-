"""StoreScout HTTP boundary. Domain modules own every numerical decision."""
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from starlette.exceptions import HTTPException
from starlette.concurrency import run_in_threadpool

from .repositories import store
from . import auth
from .schemas import Project, Scenario, ScenarioCreate, EvaluateRequest, PortfolioRequest, RescueRequest, EvaluationData, PortfolioResult, RescueResult, SiteAnalysis, Envelope, ErrorEnvelope, GeographicContext, DaypartsData, WorkspaceState, WorkspaceView
from .services import analytics, catalogue, reports, sources, presentation, showcase, workspaces
from .services.errors import ServiceError

@asynccontextmanager
async def lifespan(app):
    # Load native model dependencies once, before users reach the website.
    app.state.analytics_status = 'starting'
    try:
        await run_in_threadpool(sources.restore_packaged_model)
        await run_in_threadpool(showcase.load)
        app.state.analytics_status = 'ready'
    except Exception:
        app.state.analytics_status = 'unavailable'
        logging.getLogger(__name__).exception("Analytics initialization failed; accounts and mapped evidence remain accessible. Check the build's model-bundle installation and runtime dependencies.")
    yield


app = FastAPI(title="StoreScout API", version="1", lifespan=lifespan, responses={status: {"model": ErrorEnvelope} for status in (404, 409, 422, 500, 502, 503)})
app.include_router(auth.router)


@app.middleware("http")
async def authenticated_workspace(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS" or not path.startswith("/api/v1/"):
        return await call_next(request)
    if request.method not in ("GET", "HEAD"):
        origin = request.headers.get("origin")
        allowed = {os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"), "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"}
        if origin and origin not in allowed:
            return error(403, "ORIGIN_NOT_ALLOWED", "This request came from an unapproved website.")
        if request.headers.get("sec-fetch-site") == "cross-site":
            return error(403, "ORIGIN_NOT_ALLOWED", "Please open StoreScout directly to continue.")
    if not path.startswith("/api/v1/projects/"):
        return await call_next(request)
    user = await run_in_threadpool(auth.session_user, request.cookies.get(auth.COOKIE))
    if not user:
        return error(401, "SIGN_IN_REQUIRED", "Please sign in to continue.")
    context = store.current_user.set(user["id"])
    try:
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response
    finally:
        store.current_user.reset(context)


app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys([
        os.getenv("FRONTEND_ORIGIN", "http://localhost:3000"),
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ])),
    allow_methods=["GET", "POST"],
    allow_credentials=True,
    allow_headers=["Content-Type", "Idempotency-Key"],
    expose_headers=["Content-Disposition", "X-Evaluation-ID", "X-Portfolio-Run-ID", "X-Report-SHA256"],
)
Token = Annotated[str | None, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


def envelope(data, **meta):
    return {"data": data, "meta": {"contract_version": "1", "schema_revision": "bengaluru-1", "fixture_id": "bengaluru-20261024", "feature_snapshot_id": sources.FEATURE_SNAPSHOT_ID, **meta}}


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
def health(request: Request):
    # Liveness is deliberately distinct from model/analytical readiness.
    status = getattr(request.app.state, 'analytics_status', 'starting')
    return envelope({"status": "ok", "implementation_status": "fitted_model_integration",
                     "analytics_status": status,
                     "analytics_readiness": 'Synthetic-trained model ready.' if status == 'ready' else 'Location analysis is temporarily unavailable; saved work and mapped evidence remain accessible.'})


@app.get('/api/v1/ready')
def readiness(request: Request):
    if getattr(request.app.state, 'analytics_status', 'starting') != 'ready':
        return error(503, 'ANALYTICS_UNAVAILABLE', 'Location analysis is temporarily unavailable. Please retry shortly.')
    return envelope({'status': 'ready', **sources.model_bundle()['card']})


@app.get("/api/v1/showcase")
def product_showcase():
    return envelope(showcase.load())


@app.get("/api/v1/projects/{project_id}", response_model=Envelope[Project])
def read_project(project_id: str):
    return envelope(catalogue.project(project_id).model_dump(mode="json"))


@app.get("/api/v1/projects/{project_id}/scenarios", response_model=Envelope[list[Scenario]])
def read_scenarios(project_id: str):
    return envelope([catalogue.scenario(project_id, "baseline"), *store.list_objects("scenario", project_id)])


@app.get("/api/v1/projects/{project_id}/workspace", response_model=Envelope[WorkspaceView])
def read_workspace(project_id: str, scenario_id: str | None = None):
    return envelope(workspaces.view(project_id, scenario_id))


@app.post("/api/v1/projects/{project_id}/workspace", response_model=Envelope[WorkspaceState])
def save_workspace(project_id: str, body: WorkspaceState):
    return envelope(workspaces.save(project_id, body))


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
    return envelope([sources.infrastructure_event()])


@app.get("/api/v1/projects/{project_id}/features", response_model=Envelope[GeographicContext] | Envelope[dict])
def features(project_id: str, evaluation_id: str | None = None):
    catalogue.project(project_id)
    if evaluation_id is not None:
        analytics.saved(project_id, "evaluation", evaluation_id)
        context = analytics.saved(project_id, "evaluation_context", evaluation_id)
        return envelope(presentation.geographic(context, evaluation_id), evaluation_id=evaluation_id)
    return envelope(presentation.geographic({'project': {**sources.project_data(), 'inputs': sources.geographic_snapshot()}}, None))


@app.get("/api/v1/projects/{project_id}/model")
def model_card(project_id: str):
    catalogue.project(project_id)
    return envelope(sources.model_bundle()["card"])


@app.post("/api/v1/projects/{project_id}/evaluate", response_model=Envelope[EvaluationData])
def evaluate(project_id: str, body: EvaluateRequest, idempotency_key: Token = None):
    result = analytics.evaluate(project_id, body, idempotency_key)
    return envelope(result, scenario_id=result["scenario_id"], evaluation_id=result["evaluation_id"])


@app.get("/api/v1/projects/{project_id}/evaluations/{evaluation_id}", response_model=Envelope[EvaluationData])
def read_evaluation(project_id: str, evaluation_id: str):
    value = analytics.saved(project_id, "evaluation", evaluation_id)
    return envelope(value, scenario_id=value["scenario_id"], evaluation_id=evaluation_id)


@app.get("/api/v1/projects/{project_id}/evaluations", response_model=Envelope[list[EvaluationData]])
def list_evaluations(project_id: str):
    catalogue.project(project_id)
    return envelope(store.list_objects("evaluation", project_id))


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
    return envelope({"evaluation_id": evaluation_id, "rankings": value["rankings"], "diagnoses": {row["site_id"]: row["failfast"] for row in value["site_analyses"]}, "exclusions": [row for row in value["site_analyses"] if row["failfast"]["status"] in {"REJECTED", "REVIEW_REQUIRED"}]}, scenario_id=value["scenario_id"], evaluation_id=evaluation_id)


@app.get("/api/v1/projects/{project_id}/dayparts")
def dayparts(project_id: str, evaluation_id: str, time_bin: str | None = None):
    evaluation = analytics.saved(project_id, "evaluation", evaluation_id)
    context = analytics.saved(project_id, "evaluation_context", evaluation_id)
    if time_bin is not None and time_bin not in context["project"]["inputs"]["weights"]["time_bins"]:
        raise ServiceError(422, "INVALID_INPUT", "Unknown DaypartDNA time bin")
    if not all(row.get("dayparts") for row in evaluation["site_analyses"]):
        raise ServiceError(503, "DAYPARTS_UNAVAILABLE", "No computed DaypartDNA profiles were saved with this evaluation.")
    value = DaypartsData(evaluation_id=evaluation_id, sites=[{"site_id": row["site_id"], "profiles": [profile for profile in row["dayparts"] if time_bin is None or profile["time_bin"] == time_bin]} for row in evaluation["site_analyses"]])
    return envelope(value.model_dump(mode="json"), evaluation_id=evaluation_id, scenario_id=evaluation["scenario_id"])


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


@app.get("/api/v1/projects/{project_id}/reports/{evaluation_id}", response_class=Response,
         responses={200: {'description': 'Frozen PDF by default; diagnostic HTML/JSON only when explicitly requested.',
                          'content': {'application/pdf': {'schema': {'type': 'string', 'format': 'binary'}},
                                      'text/html': {'schema': {'type': 'string'}}, 'application/json': {'schema': {'type': 'object'}}}}})
def report(project_id: str, evaluation_id: str, portfolio_run_id: str | None = None, format: Literal["pdf", "html", "json"] = "pdf"):
    value = reports.report_data(project_id, evaluation_id, portfolio_run_id)
    headers = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    if format == "pdf":
        document = reports.pdf_document(project_id, evaluation_id, portfolio_run_id)
        headers.update({'Content-Disposition': f'attachment; filename="{document["filename"]}"',
                        'X-Evaluation-ID': evaluation_id, 'X-Portfolio-Run-ID': portfolio_run_id or '',
                        'X-Report-SHA256': document['sha256']})
        return Response(reports.pdf_bytes(document), media_type='application/pdf', headers=headers)
    if format == "json":
        return JSONResponse(envelope(value, evaluation_id=evaluation_id), headers=headers)
    headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'"
    return HTMLResponse(reports.render_html(value), headers=headers)
