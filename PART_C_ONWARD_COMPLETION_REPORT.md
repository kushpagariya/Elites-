# StoreScout remaining analytical stages — completion and integration handoff

Status: **offline ML/domain path implemented with warnings; full application integration remains open.**

Branch `ML`; baseline commit `adcabc63a1f15911d6f10afa3c1dc2a146c1468f`. No commit, push, branch switch, merge, rebase or PR.

## Completed behavior

- Geodesic spatial calculations and all six source-supported DaypartDNA profiles, availability/evidence weights and duration/day-frequency shares.
- Actual saved B.2 fitted inference feeds standalone competitor/outside calibration, full existing-network allocation and exactly-once displacement contribution.
- Annual network cashflows, NPV, ROI/payback, downside/base/upside stress and four-state FailFast precedence; same-engine verified rent and sales rescue.
- Current/Opens/Delayed timing, leap-year fractions, positive/zero/negative effects and one target-only bridge; cancelled/operational assets never receive duplicate future uplift.
- NPV ranking and exact/partial full-network portfolio search, stable ties, integer paise, scenario budget, risk acknowledgements and immutable frozen context.
- Offline JSON/HTML evidence, per-transformation source lineage, selected-artifact restoration bundle and canonical public-schema validation.

## Measured Bengaluru result

10 unchanged candidates, 100 spending cells, 219 mapped external competitors, 4 fictional existing branches.

Model `reference-sales-sim-v2-438774e0a585`; mode `model_simulated`. All ten results are **AT_RISK** because source/model/business assumptions remain explicit. No real sales labels were invented.

| Site | Allocated annual sales INR | Lost existing contribution INR | NPV INR | Status |
| --- | ---: | ---: | ---: | --- |
| site-01 | 95,898,836.37 | 970,541.09 | 29,869,219.53 | AT_RISK |
| site-02 | 64,363,933.14 | 1,379,860.16 | 16,375,975.79 | AT_RISK |
| site-03 | 116,036,540.75 | 3,636,489.80 | 32,517,567.48 | AT_RISK |
| site-04 | 78,797,348.39 | 2,395,374.37 | 26,017,568.07 | AT_RISK |
| site-05 | 224,165,824.62 | 7,554,382.47 | 117,137,491.51 | AT_RISK |
| site-06 | 160,266,490.15 | 5,905,987.27 | 61,268,994.93 | AT_RISK |
| site-07 | 67,593,510.78 | 3,516,209.73 | 14,947,858.17 | AT_RISK |
| site-08 | 71,546,104.23 | 3,343,286.20 | 13,138,227.89 | AT_RISK |
| site-09 | 92,496,496.10 | 3,137,319.40 | 21,216,102.84 | AT_RISK |
| site-10 | 227,679,913.59 | 3,831,456.90 | 118,497,754.18 | AT_RISK |

The default policy excludes all unacknowledged risky sites and returns empty zero. A separately named **illustrative acknowledged-risk policy**, not human approval, returns:

- Sites: site-05, site-10; CAPEX INR 19,800,000.00; remaining INR 200,000.00.
- Full-network NPV INR 235,102,400.74; `FULL_NETWORK_EXACT`; 1024/1024 subsets examined (including budget-pruned sets).
- Single measured warm numerical evaluation 0.921s; portfolio 0.396s. Not a p95 benchmark; excludes model loading/source parsing/UI.
- Maximum share conservation error 2.22e-16.

## Exact files and outputs

- `backend/app/domain/pipeline.py`: canonical seams, now connected to the pure engine.
- `backend/app/domain/engine.py`, `validation.py`, `geospatial/features.py`, `network/allocation.py`, `scenario/timing.py`, `failfast/rules.py`, `portfolio/search.py`: numerical implementation.
- `ml/decision_engine/{run,verify,report,package}.py` and `README.md`: offline loader, verification, evidence and portable selected model.
- `tests/unit/test_decision_engine.py`: current domain/inference/restore invariants.
- `ml/evaluation/decision_engine_v1/prepared_project.json`: exact typed sources and raw/usable model records.
- `ml/evaluation/decision_engine_v1/baseline.json`: canonical evaluation, frozen private context, complete rules/sensitivity/Daypart diagnostics.
- `ml/evaluation/decision_engine_v1/portfolios.json`, `rescues.json`, `scenario_comparisons.json`, `hypothetical_infrastructure.json`: computed policy/scenario/rescue evidence.
- `ml/evaluation/decision_engine_v1/field_lineage.json`, `daypart_recomputation_audit.json`, `run_summary.json`, `test_results.json`, `implementation_manifest.json`, `checksums.json`: lineage, numerical differences, exact code/output hashes and actual validation.
- `ml/evaluation/decision_engine_v1/reference_sales_v2_artifacts.zip` and `artifact_bundle_manifest.json`: five exact selected-model files; no raw external workbooks.
- `ml/evaluation/decision_engine_v1/decision_report.html`: frozen readable offline report.

## Source and transformation boundaries

Observed inputs are mapped OSM records, not verified comprehensive business coverage. WorldPop 2020 population is modelled; HCES 2023-24 state-urban expenditure is transferred through documented assumptions. Store sizes/costs/margins and branches are synthetic/assumed. Sales/NPVs are derived synthetic-model scenarios, not observations or investment advice.

Supporting source tables incorporated: `site_features_enriched.csv`, `spending_cells.csv`, `pois.csv`, `existing_stores.csv`, `daypart_weights.csv`, `poi_daypart_availability.csv`, `project_assumptions.csv`. All are read-only. Household/routing gaps and unrelated ridership/ward/census tables are not imputed, flattened or used as invented demand drivers. Original exact source URLs remain documented in `data/bengaluru/reports/data_sources_for_presentation.md` and the revised source manifest/acquisition ledger.

The model receives the existing 20-field feature allowlist. Daypart profiles are recomputed with great-circle distances for diagnostics; legacy projected features still drive inference unchanged. `daypart_recomputation_audit.json` exposes the differences. Network allocation uses 100 cell centroids over the bounded source AOI; the feature wallet uses a 1500m circle. Requested/achieved calibration and each bounded reference are retained. Equal external attractiveness (100 sqm, theta0), outside1, gamma1/tau750 are explicit assumptions.

The only event added is a separately flagged hypothetical connector at 12.8808,77.6472, opening 2028-04-01, +15% assumed effect. Its delayed case adds24 months. It is not an observed infrastructure announcement. Operational metro records are not assigned future uplift.

Price-period mismatch remains flagged: HCES nominal2023-24 wallet versus synthetic2026 costs. No inflation adjustment or growth, measured footfall, calibrated probability/interval, observed sales accuracy or business lift is claimed. B.2 shifted-market degradation and lack of Daypart ablation advantage remain limitations.

## Validation and preservation

Current gate: **36/36 passed**, 0 failures, 0 errors, 0 skips; 14.44s. Command: `python -m ml.decision_engine.verify`.

Includes independent finance oracles, hand-calculated conservation/displacement, calibration boundaries, 1,024-set independent full-network oracle, zero/tight budgets, cutoff truthfulness, daypart null/zero/weights, event dates/signs, full FailFast precedence, rescue residuals, immutable rent/demand changes, actual fitted-model financial/decision-boundary changes, offline inference, canonical schema validation and portable artifact restoration. The additional unchanged scaffold API contract suite stalled and was interrupted; it is not counted as passing. API routes remain unchanged with their explicit501 implementation states; HTTP integration is still a backend gate.

250 historical source/data/model/report files checked byte-identical. Original `site_features.csv` remains unchanged. The authorized domain seam `pipeline.py` is the only previously existing file changed during this increment; the existing `ml/inference/reference_sales.py` modification predates it.

Historical B/B.1/B.2 tests remain preserved; their original HEAD/pipeline-stub assertions describe earlier stages and are not the current-stage gate. A broad historical unittest discovery is not claimed green. The initial focused run exposed cumulative monotonicity detection; it was corrected and the expanded current gate rerun. Dependency deprecation warnings are retained in `test_results.json`.

## Backend/frontend handoff and remaining gates

`prepare_evaluation(project, scenario)` returns `{evaluation, context, diagnostics}`. Persist evaluation and the serializable context atomically, then add backend-owned identities/time and validate the existing public schema. `run_portfolio` requires that exact context; it refuses stale/tampered/cross-project state. `calculate_rescue` returns private numerical evidence to map through an agreed backend response. No new public endpoint/schema shape was invented.

Still open: backend source loading/API persistence/integration and report serving; frontend screens and stale-response handling; coordinated public daypart/rescue/evidence schema extensions; import/security/accessibility acceptance; full clean-checkout application run and three rehearsals; 30-run latency percentiles; independent100-market K09 regret experiment; real-outcome validation when compatible labels exist. The Navi Mumbai scaffold needs its own valid fitted features or an explicit integration decision to use Bengaluru. No required missing feature is advertised as complete.

Before a GitHub upload, review source distribution permissions using the existing licensing report. The selected-model zip makes inference portable despite `ml/artifacts/*` being ignored. No files have been staged, committed or pushed, and the branch remains `ML`.

Reproduce with the exact commands in `ml/decision_engine/README.md`.
