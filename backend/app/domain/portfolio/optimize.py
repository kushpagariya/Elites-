"""Exact full-network subset selection for the capped ten-site prototype."""
from decimal import Decimal, ROUND_HALF_UP
from time import monotonic
from ..pipeline import evaluate_subset


def paise(amount):
    return int((Decimal(str(amount)) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def optimise_portfolio(project, context, max_stores, acknowledged_risk_site_ids, *, deadline_seconds=5.0):
    evaluation = context["evaluation"]
    scenario = context["scenario"]
    network = context["network_context"]
    sites = sorted(project["sites"], key=lambda site: site["site_id"])
    if len(sites) > 10 or not 0 <= max_stores <= 10:
        raise ValueError("Prototype supports at most ten sites")
    analyses = {row["site_id"]: row for row in evaluation["site_analyses"]}
    known = {site["site_id"] for site in sites}
    if set(acknowledged_risk_site_ids) - known:
        raise ValueError("Unknown risk acknowledgement")
    budget = paise(scenario["budget_inr"])
    end = monotonic() + max(0, deadline_seconds)
    eligible = set()
    exclusions = []
    for site in sites:
        identity = site["site_id"]
        diagnosis = analyses[identity]["failfast"]
        status = diagnosis["status"]
        codes, reasons = [], []
        if status in {"REJECTED", "REVIEW_REQUIRED"}:
            codes = diagnosis["failed_rule_ids"] or [status]
            reasons = diagnosis["reasons"] or ["This location is not eligible."]
        elif status == "AT_RISK" and identity not in acknowledged_risk_site_ids:
            codes, reasons = ["RISK_NOT_ACKNOWLEDGED"], ["Acknowledge this location's downside risk before inclusion."]
        elif paise(site["capex_inr"]) > budget:
            codes, reasons = ["CAPEX_OVER_BUDGET"], ["Initial investment exceeds the saved scenario budget."]
        else:
            eligible.add(identity)
        if codes:
            exclusions.append({"site_id": identity, "reason_codes": codes, "reasons": reasons})
    # Empty zero is always feasible. Full precision values are returned; the
    # documented comparison/tie precision is one paise.
    best = {"ids": [], "cost": 0, "value": 0.0}
    def order(row):
        return (-paise(row["value"]), row["cost"], len(row["ids"]), tuple(row["ids"]))
    total, examined = 2 ** len(sites), 0
    for mask in range(total):
        if mask and monotonic() >= end:
            break
        examined += 1
        selected = [site for index, site in enumerate(sites) if mask & (1 << index)]
        ids = [site["site_id"] for site in selected]
        cost = sum(paise(site["capex_inr"]) for site in selected)
        if not ids or len(ids) > max_stores or cost > budget or not set(ids) <= eligible:
            continue
        value = evaluate_subset(network, ids)["npv_inr"]
        row = {"ids": ids, "cost": cost, "value": value}
        if order(row) < order(best):
            best = row
    complete = examined == total
    chosen = set(best["ids"])
    for identity in sorted(eligible - chosen):
        site = next(site for site in sites if site["site_id"] == identity)
        if max_stores == 0 or len(chosen) >= max_stores:
            code, reason = "STORE_COUNT_LIMIT", "The selected combination respects the store-count cap."
        elif best["cost"] + paise(site["capex_inr"]) > budget:
            code, reason = "BUDGET_COMBINATION", "This site does not fit the remaining capital budget."
        else:
            code, reason = "LOWER_NETWORK_VALUE", "Including this site did not improve the best evaluated network value."
        exclusions.append({"site_id": identity, "reason_codes": [code], "reasons": [reason]})
    return {
        "selected_site_ids": best["ids"],
        "budget_used_inr": best["cost"] / 100,
        "budget_unused_inr": (budget - best["cost"]) / 100,
        "full_network_npv_inr": best["value"],
        "status": "FULL_NETWORK_EXACT" if complete else "FEASIBLE_PARTIAL",
        "evaluated_subsets": examined, "total_subsets": total,
        "solver_status": "OPTIMAL" if complete else "PARTIAL",
        "solver_name": "Exact full-network enumeration", "solver_version": "stdlib",
        "exclusions": exclusions, "objective_precision_inr": 0.01,
        "optimality_gap": 0 if complete else None,
        "limitations": ["SYNTHETIC/ASSUMED inputs; not an empirically validated forecast.",
                        "Full-network values include branch displacement and candidate overlap once.",
                        "NPV comparison/tie precision is INR 0.01; incomplete search has an unknown gap."],
    }
