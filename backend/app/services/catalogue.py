from uuid import uuid4

from ..repositories import store
from ..schemas import Assumptions, Project, Scenario
from . import sources
from .errors import ServiceError


def project(project_id):
    if project_id != "demo":
        raise ServiceError(404, "NOT_FOUND", "Project not found")
    try:
        return Project.model_validate(sources.project_data())
    except (OSError, ValueError) as exc:
        raise ServiceError(503, "SOURCE_UNAVAILABLE", "Project fixture is missing or invalid.") from exc


def scenario(project_id, scenario_id):
    p = project(project_id)
    if scenario_id == "baseline":
        return Scenario(scenario_id="baseline", project_id=project_id, name="Current baseline", budget_inr=p.budget_inr, assumptions=Assumptions()).model_dump(mode="json")
    item = store.get("scenario", project_id, scenario_id)
    if item is None:
        raise ServiceError(404, "NOT_FOUND", "Scenario not found")
    return item


def create_scenario(project_id, body, token=None):
    base = scenario(project_id, body.base_scenario_id)
    known = {s.site_id for s in project(project_id).sites}
    if set(body.assumptions.site_overrides) - known:
        raise ServiceError(422, "INVALID_INPUT", "site_overrides contains an unknown site")
    request_hash = store.fingerprint(body.model_dump(mode="json"))
    # Scenario creation without a key intentionally makes a new immutable record.
    cache_key = request_hash if token else str(uuid4())
    existing = store.cached_id(project_id, "scenario", cache_key, token, request_hash) if token else None
    if existing:
        return store.get("scenario", project_id, existing)
    item = Scenario(scenario_id=str(uuid4()), project_id=project_id, base_scenario_id=body.base_scenario_id, name=body.name, budget_inr=base["budget_inr"] if body.budget_inr is None else body.budget_inr, assumptions=body.assumptions).model_dump(mode="json")
    identity = store.save_result(project_id, "scenario", cache_key, token, request_hash, item["scenario_id"], [("scenario", item["scenario_id"], item)])
    return store.get("scenario", project_id, identity)
