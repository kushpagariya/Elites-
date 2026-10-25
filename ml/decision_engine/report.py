"""Generate a frozen local report and implementation handoff from saved results."""
from html import escape
import json
from pathlib import Path
from .run import ROOT, OUTPUT, rows, REVISED, sha, save
from backend.app.domain.geospatial.features import TIME_BINS


def read(name):
    return json.loads((OUTPUT/name).read_text(encoding='utf-8'))


def main():
    summary, baseline, portfolios = read('run_summary.json'), read('baseline.json'), read('portfolios.json')
    tests, rescues, comparisons = read('test_results.json'), read('rescues.json'), read('scenario_comparisons.json')
    if not tests['success']:
        raise RuntimeError('Current-stage test gate failed; no completion report generated')
    project = read('prepared_project.json')
    from backend.app.schemas import EvaluationData, PortfolioResult
    # Validate the actual ten-site response and both actual portfolio results,
    # adding clearly local report identities (not a persisted API evaluation).
    EvaluationData.model_validate(dict(baseline['evaluation'], evaluation_id='offline-baseline',
        project_id=project['project_id'], scenario_id='baseline-offline', created_at_utc='2026-10-25T00:00:00Z'))
    for name in ('default_unacknowledged','illustrative_acknowledged_risk_policy'):
        PortfolioResult.model_validate(dict(portfolios[name],portfolio_run_id=f'offline-{name}',evaluation_id='offline-baseline'))
    analyses = baseline['evaluation']['site_analyses']
    source_features = {r['site_id']:r for r in rows(REVISED/'site_features_enriched.csv')}
    proxy_deltas = []
    for sid, profile in baseline['diagnostics']['dayparts'].items():
        for time_bin in TIME_BINS:
            original = float(source_features[sid][time_bin+'_raw'])
            recomputed = profile['raw'][time_bin]
            proxy_deltas.append(dict(site_id=sid,time_bin=time_bin,legacy_projected_raw=original,
                recomputed_geodesic_raw=recomputed,absolute_difference=recomputed-original,
                relative_difference=(recomputed-original)/original if original else None))
    save(OUTPUT/'daypart_recomputation_audit.json',dict(records=proxy_deltas,
        note='Geodesic recomputation is separate diagnostic evidence. Frozen inference uses original source features; no feedback uplift or master rewrite.',
        max_absolute_relative_difference=max(abs(r['relative_difference']) for r in proxy_deltas if r['relative_difference'] is not None)))
    plan=portfolios['illustrative_acknowledged_risk_policy']
    lines = ['# StoreScout remaining analytical stages — completion and integration handoff', '',
        'Status: **offline ML/domain path implemented with warnings; full application integration remains open.**', '',
        f'Branch `ML`; baseline commit `{summary["head"]}`. No commit, push, branch switch, merge, rebase or PR.', '',
        '## Completed behavior', '',
        '- Geodesic spatial calculations and all six source-supported DaypartDNA profiles, availability/evidence weights and duration/day-frequency shares.',
        '- Actual saved B.2 fitted inference feeds standalone competitor/outside calibration, full existing-network allocation and exactly-once displacement contribution.',
        '- Annual network cashflows, NPV, ROI/payback, downside/base/upside stress and four-state FailFast precedence; same-engine verified rent and sales rescue.',
        '- Current/Opens/Delayed timing, leap-year fractions, positive/zero/negative effects and one target-only bridge; cancelled/operational assets never receive duplicate future uplift.',
        '- NPV ranking and exact/partial full-network portfolio search, stable ties, integer paise, scenario budget, risk acknowledgements and immutable frozen context.',
        '- Offline JSON/HTML evidence, per-transformation source lineage, selected-artifact restoration bundle and canonical public-schema validation.', '',
        '## Measured Bengaluru result', '',
        f'{summary["candidates"]} unchanged candidates, {summary["cells"]} spending cells, {summary["external_competitors"]} mapped external competitors, {summary["branches"]} fictional existing branches.', '',
        f'Model `{summary["model_artifact_id"]}`; mode `{summary["method_mode"]}`. All ten results are **AT_RISK** because source/model/business assumptions remain explicit. No real sales labels were invented.', '',
        '| Site | Allocated annual sales INR | Lost existing contribution INR | NPV INR | Status |',
        '| --- | ---: | ---: | ---: | --- |']
    for a in analyses:
        lines.append(f'| {a["site_id"]} | {a["annual_revenue_inr"]:,.2f} | {a["lost_existing_contribution_inr"]:,.2f} | {a["npv_inr"]:,.2f} | {a["failfast"]["status"]} |')
    lines += ['', 'The default policy excludes all unacknowledged risky sites and returns empty zero. A separately named **illustrative acknowledged-risk policy**, not human approval, returns:', '',
        f'- Sites: {", ".join(plan["selected_site_ids"])}; CAPEX INR {plan["budget_used_inr"]:,.2f}; remaining INR {plan["budget_unused_inr"]:,.2f}.',
        f'- Full-network NPV INR {plan["full_network_npv_inr"]:,.2f}; `{plan["status"]}`; {plan["evaluated_subsets"]}/{plan["total_subsets"]} subsets examined (including budget-pruned sets).',
        f'- Single measured warm numerical evaluation {summary["evaluation_seconds"]:.3f}s; portfolio {summary["portfolio_seconds"]:.3f}s. Not a p95 benchmark; excludes model loading/source parsing/UI.',
        f'- Maximum share conservation error {summary["max_conservation_error"]:.3g}.', '',
        '## Exact files and outputs', '',
        '- `backend/app/domain/pipeline.py`: canonical seams, now connected to the pure engine.',
        '- `backend/app/domain/engine.py`, `validation.py`, `geospatial/features.py`, `network/allocation.py`, `scenario/timing.py`, `failfast/rules.py`, `portfolio/search.py`: numerical implementation.',
        '- `ml/decision_engine/{run,verify,report,package}.py` and `README.md`: offline loader, verification, evidence and portable selected model.',
        '- `tests/unit/test_decision_engine.py`: current domain/inference/restore invariants.',
        '- `ml/evaluation/decision_engine_v1/prepared_project.json`: exact typed sources and raw/usable model records.',
        '- `ml/evaluation/decision_engine_v1/baseline.json`: canonical evaluation, frozen private context, complete rules/sensitivity/Daypart diagnostics.',
        '- `ml/evaluation/decision_engine_v1/portfolios.json`, `rescues.json`, `scenario_comparisons.json`, `hypothetical_infrastructure.json`: computed policy/scenario/rescue evidence.',
        '- `ml/evaluation/decision_engine_v1/field_lineage.json`, `daypart_recomputation_audit.json`, `run_summary.json`, `test_results.json`, `implementation_manifest.json`, `checksums.json`: lineage, numerical differences, exact code/output hashes and actual validation.',
        '- `ml/evaluation/decision_engine_v1/reference_sales_v2_artifacts.zip` and `artifact_bundle_manifest.json`: five exact selected-model files; no raw external workbooks.',
        '- `ml/evaluation/decision_engine_v1/decision_report.html`: frozen readable offline report.', '',
        '## Source and transformation boundaries', '',
        'Observed inputs are mapped OSM records, not verified comprehensive business coverage. WorldPop 2020 population is modelled; HCES 2023-24 state-urban expenditure is transferred through documented assumptions. Store sizes/costs/margins and branches are synthetic/assumed. Sales/NPVs are derived synthetic-model scenarios, not observations or investment advice.', '',
        'Supporting source tables incorporated: `site_features_enriched.csv`, `spending_cells.csv`, `pois.csv`, `existing_stores.csv`, `daypart_weights.csv`, `poi_daypart_availability.csv`, `project_assumptions.csv`. All are read-only. Household/routing gaps and unrelated ridership/ward/census tables are not imputed, flattened or used as invented demand drivers. Original exact source URLs remain documented in `data/bengaluru/reports/data_sources_for_presentation.md` and the revised source manifest/acquisition ledger.', '',
        'The model receives the existing 20-field feature allowlist. Daypart profiles are recomputed with great-circle distances for diagnostics; legacy projected features still drive inference unchanged. `daypart_recomputation_audit.json` exposes the differences. Network allocation uses 100 cell centroids over the bounded source AOI; the feature wallet uses a 1500m circle. Requested/achieved calibration and each bounded reference are retained. Equal external attractiveness (100 sqm, theta0), outside1, gamma1/tau750 are explicit assumptions.', '',
        'The only event added is a separately flagged hypothetical connector at 12.8808,77.6472, opening 2028-04-01, +15% assumed effect. Its delayed case adds24 months. It is not an observed infrastructure announcement. Operational metro records are not assigned future uplift.', '',
        'Price-period mismatch remains flagged: HCES nominal2023-24 wallet versus synthetic2026 costs. No inflation adjustment or growth, measured footfall, calibrated probability/interval, observed sales accuracy or business lift is claimed. B.2 shifted-market degradation and lack of Daypart ablation advantage remain limitations.', '',
        '## Validation and preservation', '',
        f'Current gate: **{tests["tests_run"]}/{tests["tests_run"]} passed**, {tests["failures"]} failures, {tests["errors"]} errors, {tests["skipped"]} skips; {tests["seconds"]:.2f}s. Command: `python -m ml.decision_engine.verify`.', '',
        'Includes independent finance oracles, hand-calculated conservation/displacement, calibration boundaries, 1,024-set independent full-network oracle, zero/tight budgets, cutoff truthfulness, daypart null/zero/weights, event dates/signs, full FailFast precedence, rescue residuals, immutable rent/demand changes, actual fitted-model financial/decision-boundary changes, offline inference, canonical schema validation and portable artifact restoration. The additional unchanged scaffold API contract suite stalled and was interrupted; it is not counted as passing. API routes remain unchanged with their explicit501 implementation states; HTTP integration is still a backend gate.', '',
        f'{summary["protected_files"]} historical source/data/model/report files checked byte-identical. Original `site_features.csv` remains unchanged. The authorized domain seam `pipeline.py` is the only previously existing file changed during this increment; the existing `ml/inference/reference_sales.py` modification predates it.', '',
        'Historical B/B.1/B.2 tests remain preserved; their original HEAD/pipeline-stub assertions describe earlier stages and are not the current-stage gate. A broad historical unittest discovery is not claimed green. The initial focused run exposed cumulative monotonicity detection; it was corrected and the expanded current gate rerun. Dependency deprecation warnings are retained in `test_results.json`.', '',
        '## Backend/frontend handoff and remaining gates', '',
        '`prepare_evaluation(project, scenario)` returns `{evaluation, context, diagnostics}`. Persist evaluation and the serializable context atomically, then add backend-owned identities/time and validate the existing public schema. `run_portfolio` requires that exact context; it refuses stale/tampered/cross-project state. `calculate_rescue` returns private numerical evidence to map through an agreed backend response. No new public endpoint/schema shape was invented.', '',
        'Still open: backend source loading/API persistence/integration and report serving; frontend screens and stale-response handling; coordinated public daypart/rescue/evidence schema extensions; import/security/accessibility acceptance; full clean-checkout application run and three rehearsals; 30-run latency percentiles; independent100-market K09 regret experiment; real-outcome validation when compatible labels exist. The Navi Mumbai scaffold needs its own valid fitted features or an explicit integration decision to use Bengaluru. No required missing feature is advertised as complete.', '',
        'Before a GitHub upload, review source distribution permissions using the existing licensing report. The selected-model zip makes inference portable despite `ml/artifacts/*` being ignored. No files have been staged, committed or pushed, and the branch remains `ML`.', '',
        'Reproduce with the exact commands in `ml/decision_engine/README.md`.' ]
    (ROOT/'PART_C_ONWARD_COMPLETION_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Escape every stored value; this file reads no live UI/scenario state.
    cells=''.join('<tr>'+''.join(f'<td>{escape(str(value))}</td>' for value in
        [a['site_id'],f'{a["annual_revenue_inr"]:,.2f}',f'{a["npv_inr"]:,.2f}',a['failfast']['status']])+'</tr>' for a in analyses)
    html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>StoreScout frozen decision report</title>
<style>body{font:16px system-ui;max-width:1100px;margin:40px auto;padding:0 24px;color:#18302d}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid #ccd6d4}p{line-height:1.6}.notice{padding:16px;background:#fff3d6}pre{white-space:pre-wrap;font-size:13px}@media print{body{margin:0}}</style>
<h1>StoreScout — frozen offline decision report</h1>
<p class="notice">SYNTHETIC MODEL / ASSUMED BUSINESS INPUTS. No real sales accuracy, measured footfall or investment approval. All ten sites remain AT_RISK. The default unacknowledged-risk portfolio is empty.</p>'''
    html+=f'<p>Scenario: baseline-offline · Feature snapshot: {escape(baseline["diagnostics"]["feature_snapshot_id"])} · Model: {escape(summary["model_artifact_id"])} · Engine: {escape(summary["engine_version"])}</p>'
    html+='<table><thead><tr><th>Site</th><th>Year-1 sales INR</th><th>Network NPV INR</th><th>Status</th></tr></thead><tbody>'+cells+'</tbody></table>'
    html+='<h2>Illustrative acknowledged-risk policy</h2><p>This separate policy is an offline demonstration, not human approval.</p><pre>'+escape(json.dumps(plan,indent=2))+'</pre>'
    html+='<h2>Evidence and limits</h2><p>WorldPop2020 modelled population; HCES2023-24 nominal state-urban spending proxy; partial mapped OSM coverage; 100 source cell centroids; assumed equal external attraction; four fictional branches; synthetic2026 business costs. Price-period mismatch is flagged. Low/base/high values are sensitivity cases, not calibrated prediction intervals.</p>'
    html+='<p>Sources: '+escape(', '.join(baseline['diagnostics']['source_ids']))+'</p>'
    html+='<h2>Computed drivers and rule evidence</h2>'
    for a in analyses:
        html+='<h3>'+escape(a['site_id'])+'</h3><ul>'+''.join('<li>'+escape(d)+'</li>' for d in a['drivers']+a['failfast']['reasons'])+'</ul>'
    html+='<p>Complete reproducible context, source lineage, scenario comparisons, rescues and exact hashes accompany this file. API/UI integration is still open.</p></html>'
    (OUTPUT/'decision_report.html').write_text(html,encoding='utf-8')
    implementation = list((ROOT/'backend/app/domain').rglob('*.py')) + list((ROOT/'ml/decision_engine').glob('*.py'))
    implementation += [ROOT/'ml/decision_engine/README.md', ROOT/'tests/unit/test_decision_engine.py', ROOT/'PART_C_ONWARD_COMPLETION_REPORT.md']
    save(OUTPUT/'implementation_manifest.json',dict(engine_version=summary['engine_version'],base_commit=summary['head'],
        source_sha256={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in sorted(implementation)},
        note='Uncommitted implementation identified by exact file hashes; no new Git commit is claimed'))
    save(OUTPUT/'checksums.json',{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in OUTPUT.iterdir() if p.is_file() and p.name!='checksums.json'})
    print('Wrote PART_C_ONWARD_COMPLETION_REPORT.md and ml/evaluation/decision_engine_v1/decision_report.html')


if __name__=='__main__': main()
