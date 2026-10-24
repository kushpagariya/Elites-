"""Validate and persist domain results; never duplicate numerical models."""
import copy
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import uuid4

from pydantic import ValidationError

from ..repositories import store
from ..schemas import EvaluationData, PortfolioResult, RescueResult
from . import catalogue, gateway, sources
from .errors import ServiceError


def invalid(message):
    raise ServiceError(502, "ENGINE_INVALID_OUTPUT", message)


def validate(model, body):
    try:
        return model.model_validate(body).model_dump(mode="json")
    except ValidationError as exc:
        raise ServiceError(502, "ENGINE_INVALID_OUTPUT", "Analytical output does not match the agreed schema; no result was saved.") from exc


def saved(project_id, kind, identity):
    catalogue.project(project_id)
    value = store.get(kind, project_id, identity)
    if value is None:
        raise ServiceError(404, "NOT_FOUND", f"Saved {kind} not found")
    return value


def _cached(project_id, operation, key, token, request_hash):
    identity = store.cached_id(project_id, operation, key, token, request_hash)
    return saved(project_id, operation.split(":")[0], identity) if identity else None


def evaluate(project_id, body, token=None):
    scenario = catalogue.scenario(project_id, body.scenario_id)
    inputs = sources.load_snapshot(body.feature_snapshot_id)
    project = catalogue.project(project_id).model_dump(mode="json")
    bundle = sources.model_bundle()
    snapshot = {
        "feature_snapshot_id": body.feature_snapshot_id,
        "source_snapshot_hash": inputs["snapshot_hash"],
        "source_hashes": inputs["source_hashes"],
        "engine_sha256": sources.engine_identity(),
        "model_artifact_sha256": bundle["artifact_sha256"] if bundle else None,
        "model_card_sha256": bundle["card_sha256"] if bundle else None,
        "valuation_date": scenario["assumptions"].get("valuation_date", sources.VALUATION_DATE),
        "orchestration_version": "integration-2",
    }
    request_hash = store.fingerprint(body.model_dump(mode="json"))
    key = store.fingerprint({"project": project, "scenario": scenario, "snapshot": snapshot})
    cached = _cached(project_id, "evaluation", key, token, request_hash)
    if cached:
        return cached
    project["inputs"] = {**inputs, "snapshot_id": inputs["snapshot_hash"], "model_bundle": bundle}
    computed = gateway.invoke("run_evaluation", copy.deepcopy(project), copy.deepcopy(scenario))
    if not isinstance(computed, dict):
        invalid("Evaluation engine must return an object.")
    computed = dict(computed)
    prepared = computed.pop("_context", None)
    if prepared is not None and not isinstance(prepared, dict):
        invalid("Frozen network context must be a JSON object.")
    protected = {"evaluation_id", "project_id", "scenario_id", "created_at_utc"}
    if protected.intersection(computed):
        invalid("Domain output must not supply backend-owned identities.")
    result = validate(EvaluationData, {**computed, "evaluation_id": str(uuid4()), "project_id": project_id, "scenario_id": body.scenario_id, "created_at_utc": datetime.now(timezone.utc).isoformat()})
    by_id = {row["site_id"]: row for row in result["site_analyses"]}
    expected = {s["site_id"] for s in project["sites"]}
    if len(by_id) != len(result["site_analyses"]) or set(by_id) != expected:
        invalid("Evaluation must contain exactly one analysis for every candidate.")
    eligible = {identity for identity, row in by_id.items() if row["failfast"]["status"] in {"VIABLE", "AT_RISK"}}
    capex = {s["site_id"]: s["capex_inr"] for s in project["sites"]}
    expected_ranking = sorted(eligible, key=lambda identity: (-by_id[identity]["npv_inr"], capex[identity], identity))
    if result["rankings"] != expected_ranking:
        invalid("Ranking must cover eligible sites in NPV/CAPEX/ID order.")
    known_sources = set(inputs["source_manifest"]["source_ids"])
    for row in by_id.values():
        if len(row["annual_cashflows_inr"]) != project["projection_years"]:
            invalid("Annual cash flows must cover the saved projection horizon.")
        if set(row["source_ids"]) - known_sources:
            invalid("Analysis refers to a source outside the frozen manifest.")
    if result["method_mode"] != "scenario_assumptions":
        if not bundle or result["model_artifact_id"] != bundle["card"]["model_artifact_id"] or result["method_mode"] != bundle["card"]["method_mode"]:
            invalid("Trained inference requires the matching installed model artifact and mode.")
    elif result["model_artifact_id"] is not None:
        invalid("Assumption mode must not claim a model artifact.")
    context = {"project": project, "scenario": scenario, "evaluation": result, "prepared_network": prepared, "snapshot": snapshot}
    try:
        store.canonical_json(context)
    except (ValueError, TypeError) as exc:
        raise ServiceError(502, "ENGINE_INVALID_OUTPUT", "Frozen context must contain finite JSON values; no result was saved.") from exc
    # Source/model replacement while a worker runs cannot publish a mixed snapshot.
    ensure_engine(context)
    if sources.load_snapshot(body.feature_snapshot_id)["snapshot_hash"] != inputs["snapshot_hash"]:
        raise ServiceError(409, "STALE_SNAPSHOT", "Source files changed during evaluation; retry.")
    identity = store.save_result(project_id, "evaluation", key, token, request_hash, result["evaluation_id"], [("evaluation", result["evaluation_id"], result), ("evaluation_context", result["evaluation_id"], context)])
    return saved(project_id, "evaluation", identity)


def ensure_engine(context):
    if sources.engine_identity() != context["snapshot"]["engine_sha256"]:
        raise ServiceError(409, "STALE_ENGINE", "Analytical code changed; create a new evaluation before calculating again.")
    bundle = sources.model_bundle()
    actual = (bundle["artifact_sha256"], bundle["card_sha256"]) if bundle else (None, None)
    expected = (context["snapshot"]["model_artifact_sha256"], context["snapshot"]["model_card_sha256"])
    if actual != expected:
        raise ServiceError(409, "STALE_MODEL", "Installed model changed; create a new evaluation before calculating again.")


def context_for(project_id, evaluation_id):
    saved(project_id, "evaluation", evaluation_id)
    context = saved(project_id, "evaluation_context", evaluation_id)
    if not context.get("prepared_network"):
        raise ServiceError(503, "CONTEXT_UNAVAILABLE", "Evaluation has no frozen network context; ML must supply _context.")
    ensure_engine(context)
    return context


def paise(value):
    return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def portfolio(project_id, body, token=None):
    context = context_for(project_id, body.evaluation_id)
    analyses = {row["site_id"]: row for row in context["evaluation"]["site_analyses"]}
    acknowledgements = body.acknowledged_risk_site_ids
    if len(set(acknowledgements)) != len(acknowledgements) or any(identity not in analyses or analyses[identity]["failfast"]["status"] != "AT_RISK" for identity in acknowledgements):
        raise ServiceError(422, "INVALID_INPUT", "Acknowledge each AT_RISK site at most once using this evaluation's IDs.")
    request = body.model_dump(mode="json")
    request["acknowledged_risk_site_ids"] = sorted(acknowledgements)
    key = request_hash = store.fingerprint(request)
    cached = _cached(project_id, "portfolio", key, token, request_hash)
    if cached:
        return cached
    project = copy.deepcopy(context["project"])
    project["budget_inr"] = context["scenario"]["budget_inr"]
    domain_context = {**copy.deepcopy(context), "network_context": copy.deepcopy(context["prepared_network"])}
    computed = gateway.invoke("run_portfolio", project, domain_context, body.max_stores, sorted(acknowledgements))
    if not isinstance(computed, dict) or {"portfolio_run_id", "evaluation_id"}.intersection(computed):
        invalid("Portfolio engine must return computed fields without backend-owned identities.")
    result = validate(PortfolioResult, {**computed, "portfolio_run_id": str(uuid4()), "evaluation_id": body.evaluation_id, "max_stores": body.max_stores, "acknowledged_risk_site_ids": sorted(acknowledgements)})
    selected = result["selected_site_ids"]
    if len(set(selected)) != len(selected) or len(selected) > body.max_stores or set(selected) - set(analyses):
        invalid("Portfolio selected invalid, duplicate or too many sites.")
    for identity in selected:
        diagnosis = analyses[identity]["failfast"]["status"]
        if diagnosis not in {"VIABLE", "AT_RISK"} or diagnosis == "AT_RISK" and identity not in acknowledgements:
            invalid("Portfolio contains an excluded or unacknowledged risk site.")
    capex = sum(paise(site["capex_inr"]) for site in project["sites"] if site["site_id"] in selected)
    budget = paise(context["scenario"]["budget_inr"])
    if capex > budget or paise(result["budget_used_inr"]) != capex or paise(result["budget_unused_inr"]) != budget - capex:
        invalid("Portfolio budget does not reconcile with saved scenario CAPEX.")
    if result["evaluated_subsets"] > result["total_subsets"] or result["total_subsets"] > 2 ** len(analyses):
        invalid("Portfolio search counts are inconsistent.")
    if result["status"] == "FULL_NETWORK_EXACT" and result["evaluated_subsets"] != result["total_subsets"]:
        invalid("An incomplete search cannot claim an exact result.")
    if (not selected and result["full_network_npv_inr"] != 0) or result["full_network_npv_inr"] < 0 or (result["status"] == "UNKNOWN" and selected):
        invalid("Portfolio must respect the feasible empty zero alternative.")
    ensure_engine(context)
    record = {"request": request, "scenario_id": context["scenario"]["scenario_id"], "snapshot": context["snapshot"]}
    identity = store.save_result(project_id, "portfolio", key, token, request_hash, result["portfolio_run_id"], [("portfolio", result["portfolio_run_id"], result), ("portfolio_context", result["portfolio_run_id"], record)])
    return saved(project_id, "portfolio", identity)


def rescue(project_id, site_id, body, token=None):
    context = context_for(project_id, body.evaluation_id)
    sites = {site["site_id"]: site for site in context["project"]["sites"]}
    if site_id not in sites:
        raise ServiceError(404, "NOT_FOUND", "Site not found")
    request = body.model_dump(mode="json")
    assumptions = context["scenario"]["assumptions"]
    override = assumptions["site_overrides"].get(site_id, {}).get("monthly_rent_inr")
    current_rent = override if override is not None else sites[site_id]["monthly_rent_inr"] * assumptions["rent_multiplier"]
    defaults = (0, max(2 * current_rent, 1)) if body.lever == "rent" else (0.5, 3)
    request["lower_bound"] = defaults[0] if body.lower_bound is None else body.lower_bound
    request["upper_bound"] = defaults[1] if body.upper_bound is None else body.upper_bound
    if request["lower_bound"] > request["upper_bound"] or body.lever == "sales" and request["upper_bound"] > 3:
        raise ServiceError(422, "INVALID_INPUT", "Rescue bounds are invalid or exceed the supported sales multiplier.")
    operation = f"rescue:{site_id}"
    key = request_hash = store.fingerprint(request)
    cached = _cached(project_id, operation, key, token, request_hash)
    if cached:
        return cached
    computed = gateway.invoke("run_rescue", copy.deepcopy(context["prepared_network"]), site_id, body.lever, request["lower_bound"], request["upper_bound"])
    accepted = {"status", "threshold", "verification_npv_inr", "npv_at_threshold", "verified", "reasons", "remaining_failed_rule_ids", "site_id", "lever", "lower_bound", "upper_bound"}
    if not isinstance(computed, dict) or set(computed) - accepted:
        invalid("Rescue engine returned fields outside the agreed computed result.")
    computed = dict(computed)
    npv = computed.get("npv_at_threshold", computed.get("verification_npv_inr"))
    computed.update(npv_at_threshold=npv, verification_npv_inr=npv)
    computed.setdefault("verified", computed.get("status") == "SOLVED" and npv is not None and abs(npv) <= 1)
    result = validate(RescueResult, {**computed, **request, "site_id": site_id, "rescue_id": str(uuid4())})
    if result["status"] == "SOLVED":
        threshold, npv = result["threshold"], result["verification_npv_inr"]
        if threshold is None or not request["lower_bound"] <= threshold <= request["upper_bound"] or npv is None or abs(npv) > 1 or not result["verified"]:
            invalid("Solved rescue must contain an in-bounds threshold verified within INR 1 of break-even.")
    elif result["threshold"] is not None:
        invalid("An unsolved rescue cannot claim a threshold.")
    ensure_engine(context)
    identity = store.save_result(project_id, operation, key, token, request_hash, result["rescue_id"], [("rescue", result["rescue_id"], result)])
    return saved(project_id, "rescue", identity)
