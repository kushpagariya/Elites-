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
from starlette.concurrency import run_in_threadpool

from .repositories import store
from . import auth
from .schemas import Project, Scenario, ScenarioCreate, EvaluateRequest, PortfolioRequest, RescueRequest, EvaluationData, PortfolioResult, RescueResult, SiteAnalysis, Envelope, ErrorEnvelope, GeographicContext, DaypartsData
from .domain import pipeline
from .services import analytics, catalogue, reports, sources
from .services.errors import ServiceError

app = FastAPI(title="StoreScout API", version="1", responses={status: {"model": ErrorEnvelope} for status in (404, 409, 422, 500, 502, 503)})
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
    expose_headers=["Content-Disposition"],
)
Token = Annotated[str | None, Header(alias="Idempotency-Key", min_length=1, max_length=128)]


def envelope(data, **meta):
    return {"data": data, "meta": {"contract_version": "1", "schema_revision": "analytical-2", "fixture_id": "demo-1", **meta}}


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
    return envelope({"status": "ok", "implementation_status": "assumption_based_analytics", "analytics_readiness": "Assumption-based engine connected; no trained model is active."})


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


@app.get("/api/v1/projects/{project_id}/features", response_model=Envelope[GeographicContext] | Envelope[dict])
def features(project_id: str, evaluation_id: str | None = None):
    catalogue.project(project_id)
    if evaluation_id is not None:
        analytics.saved(project_id, "evaluation", evaluation_id)
        context = analytics.saved(project_id, "evaluation_context", evaluation_id)
        frozen = context["project"]["inputs"]
        radius = frozen["weights"]["catchment_radius_m"]
        catchments = [{"site_id": site["site_id"], "geometry": pipeline.catchment_ring(site["latitude"], site["longitude"], radius)} for site in context["project"]["sites"]]
        return envelope({"evaluation_id": evaluation_id, "pois": frozen["pois"], "cells": frozen["cells"], "roads": [], "competitors": [], "catchments": catchments, "catchment_radius_m": radius, "limitations": ["Road and observed competitor inventories are unavailable.", "SYNTHETIC points and assumed straight-line catchments; not travel-time isochrones."]}, evaluation_id=evaluation_id)
    snapshot = sources.installed_snapshot()
    return envelope({**snapshot, "prepared": False, "note": "Frozen source inputs; derived spatial features require the ML implementation."})


@app.get("/api/v1/projects/{project_id}/model")
def model_card(project_id: str):
    catalogue.project(project_id)
    bundle = sources.model_bundle()
    if bundle is None:
        return envelope({"method_mode": "scenario_assumptions", "model_artifact_id": None, "estimator_version": pipeline.ENGINE_VERSION, "feature_schema": "wallet-reference-v1", "trained_model_available": False, "metrics": None, "limitations": ["No approved trained model is installed. The connected wallet-share estimator is assumption-based."]})
    return envelope({key: value for key, value in bundle.items() if key != "artifact_path"})


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


@app.get("/api/v1/projects/{project_id}/reports/{evaluation_id}", response_class=HTMLResponse)
def report(project_id: str, evaluation_id: str, portfolio_run_id: str | None = None, format: Literal["html", "json"] = "html"):
    value = reports.report_data(project_id, evaluation_id, portfolio_run_id)
    headers = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    if format == "json":
        return JSONResponse(envelope(value, evaluation_id=evaluation_id), headers=headers)
    headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'"
    return HTMLResponse(reports.render_html(value), headers=headers)
