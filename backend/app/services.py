"""Saved analytical orchestration; all economics stay in the pure domain engine."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from .repositories import store
from .schemas import EvaluationData, PortfolioResult, RescueResult
from .domain.pipeline import run_evaluation, run_portfolio, run_rescue, ENGINE_VERSION, FINANCE_VERSION, RULE_VERSION, MODEL_ARTIFACT_ID, PARAMETERS

DATA_ROOT=Path(__file__).resolve().parents[2]/"data"/"demo"


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()


def inputs():
    value={name:json.loads((DATA_ROOT/(name+".json")).read_text(encoding="utf-8")) for name in ["cells","pois","infrastructure","weights","source_manifest"]}
    value["snapshot_id"]=digest(value)
    return value


def evaluate(project, scenario, feature_snapshot_id, idempotency_key=None):
    frozen=inputs()
    if feature_snapshot_id!=frozen["source_manifest"]["feature_snapshot_id"]:
        raise LookupError("The requested source snapshot is no longer available. Reload the project.")
    fingerprint=digest({"project":project,"scenario":scenario,"inputs":frozen,"engine":ENGINE_VERSION,"model_artifact_id":MODEL_ARTIFACT_ID,"finance_version":FINANCE_VERSION,"rule_version":RULE_VERSION,"parameters":PARAMETERS,"schema":"analytical-2"})
    key_id=digest(idempotency_key) if idempotency_key else None
    previous=store.get("idempotency",project["project_id"],key_id) if key_id else None
    if previous and previous["fingerprint"]!=fingerprint: raise LookupError("This request key already identifies different inputs.")
    evaluation_id="eval-"+fingerprint[:24]
    saved=store.get("evaluation",project["project_id"],evaluation_id)
    if saved:
        if key_id and not previous: store.save("idempotency",project["project_id"],key_id,{"fingerprint":fingerprint,"evaluation_id":evaluation_id})
        return saved
    computed=run_evaluation({**project,"inputs":frozen},scenario)
    network=computed.pop("_context")
    result=EvaluationData(evaluation_id=evaluation_id,project_id=project["project_id"],scenario_id=scenario["scenario_id"],created_at_utc=datetime.now(timezone.utc).isoformat(),**computed).model_dump()
    private={"evaluation":result,"scenario":scenario,"network_context":network,"fingerprint":fingerprint}
    records=[("evaluation",evaluation_id,result),("evaluation_context",evaluation_id,private)]
    if key_id: records.append(("idempotency",key_id,{"fingerprint":fingerprint,"evaluation_id":evaluation_id}))
    try: store.save_many(project["project_id"],records)
    except Exception:
        # Concurrent equivalent immutable computation can safely reuse the committed result.
        existing=store.get("evaluation",project["project_id"],evaluation_id)
        if existing and store.get("evaluation_context",project["project_id"],evaluation_id): return existing
        raise
    return result


def load_context(project_id,evaluation_id,require_current=False):
    context=store.get("evaluation_context",project_id,evaluation_id)
    if context is None: raise KeyError("Saved evaluation not found")
    evidence=context["evaluation"].get("evidence") or {}
    if require_current and (evidence.get("estimator_version")!=ENGINE_VERSION or evidence.get("finance_version")!=FINANCE_VERSION or evidence.get("rule_version")!=RULE_VERSION or evidence.get("assumed_parameters")!=PARAMETERS or context["evaluation"].get("model_artifact_id")!=MODEL_ARTIFACT_ID):
        raise LookupError("The calculation method has changed. Re-evaluate this saved scenario before requesting a new decision.")
    return context


def portfolio(project,body):
    context=load_context(project["project_id"],body.evaluation_id,require_current=True)
    computed=run_portfolio(context["network_context"]["project"],context,body.max_stores,body.acknowledged_risk_site_ids)
    result=PortfolioResult(portfolio_run_id="portfolio-"+uuid4().hex,evaluation_id=body.evaluation_id,max_stores=body.max_stores,acknowledged_risk_site_ids=body.acknowledged_risk_site_ids,**computed).model_dump()
    # Independently check exact investment feasibility against the frozen scenario.
    from .domain.portfolio.optimize import paise
    sites={s["site_id"]:s for s in context["network_context"]["project"]["sites"]}
    actual=sum(paise(sites[s]["capex_inr"]) for s in result["selected_site_ids"])
    statuses={s["site_id"]:s["failfast"]["status"] for s in context["evaluation"]["site_analyses"]}
    if actual>paise(context["scenario"]["budget_inr"]) or actual!=paise(result["budget_used_inr"]) or len(result["selected_site_ids"])>body.max_stores:
        raise ValueError("Portfolio investment validation failed")
    if any(statuses[s] not in {"VIABLE","AT_RISK"} or (statuses[s]=="AT_RISK" and s not in body.acknowledged_risk_site_ids) for s in result["selected_site_ids"]):
        raise ValueError("Portfolio eligibility validation failed")
    store.save("portfolio",project["project_id"],result["portfolio_run_id"],result)
    return result


def rescue(project_id,site_id,body):
    context=load_context(project_id,body.evaluation_id,require_current=True)
    result=run_rescue(context["network_context"],site_id,body.lever,body.lower_bound,body.upper_bound)
    return RescueResult(evaluation_id=body.evaluation_id,**result).model_dump()
