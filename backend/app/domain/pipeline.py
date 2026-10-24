"""Stable backend-to-logic boundaries. The complete pipeline is not implemented.

Backend owns transport validation, IDs, persistence and response envelopes. The
logic owner implements these deterministic functions. They return computed
fields without a response envelope or generated identity metadata. Backend
composes identities and validates against backend.app.schemas before saving.
Do not generate fake results while these seams remain unimplemented.
"""

from typing import Any

JsonObject = dict[str, Any]


def run_evaluation(project: JsonObject, scenario: JsonObject) -> JsonObject:
    """Return complete analysis for the supplied frozen project/scenario inputs.

    Required stages: features -> fitted inference -> frozen attraction -> bounded
    network -> finance -> sensitivity/diagnosis -> ranking/evidence. Return
    method_mode, site_analyses, rankings and model_artifact_id. Each site matches
    SiteAnalysis, including roi_fraction (map FinanceResult.horizon_roi here).
    Backend supplies evaluation_id/project_id/scenario_id/created_at_utc, then
    validates EvaluationData and commits atomically. No generated IDs or wrapper.
    Freeze the prepared network alongside this evaluation through the backend's
    internal persistence seam; it is not an extra public EvaluationData field.
    Map this explicit unavailable state to a useful API error until implemented.
    """
    raise NotImplementedError("Evaluation pipeline awaits logic implementation")


def run_portfolio(
    project: JsonObject,
    evaluation: JsonObject,
    max_stores: int,
    acknowledged_risk_site_ids: list[str],
) -> JsonObject:
    """Return feasible best-known set using this evaluation's scenario budget.

    evaluation is an internal context containing the saved public evaluation,
    original Scenario and frozen prepared network/wallets. Backend loads these
    by evaluation_id; public singleton analyses cannot reconstruct the network.
    Recompute full-network economics for every eligible subset. Never sum site
    NPVs or use baseline Project budget instead of Scenario budget. Include
    empty zero, cap candidates at ten, obey a five-second deadline. Return
    selected_site_ids, budget_used_inr, budget_unused_inr, full_network_npv_inr,
    status, evaluated_subsets and total_subsets. Backend adds portfolio_run_id
    and evaluation_id, then validates PortfolioResult. No envelope or invented
    identities. Acknowledgements bind to the supplied evaluation.
    """
    raise NotImplementedError("Full-network portfolio awaits logic implementation")
