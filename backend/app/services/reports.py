import html
import json

from .analytics import saved
from .errors import ServiceError


def report_data(project_id, evaluation_id, portfolio_run_id=None):
    evaluation = saved(project_id, "evaluation", evaluation_id)
    context = saved(project_id, "evaluation_context", evaluation_id)
    portfolio = saved(project_id, "portfolio", portfolio_run_id) if portfolio_run_id else None
    if portfolio and portfolio["evaluation_id"] != evaluation_id:
        raise ServiceError(409, "CONTEXT_MISMATCH", "Portfolio does not belong to this evaluation.")
    project = {key: value for key, value in context["project"].items() if key != "inputs"}
    inputs = context["project"]["inputs"]
    model = inputs.get("model_bundle")
    selected = set(portfolio["selected_site_ids"]) if portfolio else set()
    return {
        "project": project,
        "scenario": context["scenario"],
        "evaluation": evaluation,
        "portfolio": portfolio,
        "portfolio_request": saved(project_id, "portfolio_context", portfolio_run_id)["request"] if portfolio else None,
        "excluded_site_ids": [s["site_id"] for s in project["sites"] if s["site_id"] not in selected] if portfolio else [],
        "snapshot": context["snapshot"],
        "sources": inputs["source_manifest"],
        "model_card": model["card"] if model else None,
        "limitations": [
            "Demo geographic and business inputs are synthetic; infrastructure event is hypothetical.",
            "POI-derived opportunity is not measured footfall. Sensitivity is not a calibrated forecast interval.",
            "Synthetic model evaluation does not establish real-world retail accuracy.",
            "A report records saved scenario assumptions, not guaranteed investment returns.",
        ],
    }


def render_html(data):
    """No executable content or interpolated raw HTML from data/model explanations."""
    evaluation = data["evaluation"]
    names = {s["site_id"]: s["name"] for s in data["project"]["sites"]}
    rows = []
    for item in evaluation["site_analyses"]:
        values = (names[item["site_id"]], item["annual_revenue_inr"], item["npv_inr"], item["roi_fraction"], item["payback_years"], item["failfast"]["status"])
        rows.append("<tr>" + "".join(f"<td>{html.escape('Unknown / not applicable' if value is None else str(value))}</td>" for value in values) + "</tr>")
    details = html.escape(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False))
    identity = html.escape(evaluation["evaluation_id"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>StoreScout saved decision report</title>
<style>body{{font:15px system-ui;margin:2rem auto;max-width:1100px;padding:0 1rem;color:#181818}}table{{width:100%;border-collapse:collapse}}th,td{{padding:.5rem;border:1px solid #ccc;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}}@media print{{body{{margin:0}}}}</style></head>
<body><h1>StoreScout saved decision report</h1><p>Evaluation: {identity}</p>
<p>Amounts are INR. Revenue is annual. ROI is a decimal fraction over the saved horizon, not IRR. Payback is years.</p>
<table><thead><tr><th>Candidate</th><th>Annual sales</th><th>Incremental NPV</th><th>Horizon ROI fraction</th><th>Payback</th><th>Diagnosis</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<h2>Saved assumptions, portfolio, evidence and limitations</h2><pre>{details}</pre></body></html>"""
