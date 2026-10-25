# StoreScout ML final handoff

Verification date: 2026-10-25. Branch: `ML`. Starting and finishing HEAD: `16728c7cd5f4268c6309a44f056c03cf0c207694`.

**ML_HANDOFF_READY_WITH_LIMITATIONS** — the three requested Part E corrections pass canonical fresh-scenario application checks; 57 current offline tests pass, and measured Part G runtime meets five seconds. This is an offline ML/domain handoff with explicit integration and evidence limitations. No empirical sales accuracy or investment approval is established.

## A. ML ownership completion

| Part | Implemented offline behavior | Remaining limitation |
| --- | --- | --- |
| A | Reproducible Bengaluru tables, source/field lineage, corrected enriched feature view and licensing notes | Historical/modelled population, partial POIs, proxy wallets; business inputs and four branches are synthetic/assumed. Existing source permission gaps remain. |
| B | Saved fitted B.2 capture model, support checks, deterministic local INR inference | Synthetic targets only; shifted-market degradation; automatic calibration permission remains false. Blocked v1 Ridge stays blocked. |
| C | Six DaypartDNA bins, distance/availability weighting, weekly exposure shares | Proxy opportunity, not measured visits. Mostly assumed hours; H06/H07 below remain open. |
| D | Competitors-plus-outside reference calibration; full-network Huff allocation; own-branch displacement; unchanged finance helper | Equal external attraction, cell centroids and financial assumptions; bounded calibration can be unattainable. |
| E | FailFast precedence; canonical rent/sales rescue; feasible-bracket search; fresh-copy verification | Search monotonicity is sampled; safety blocks yield no actionable override. Readiness/snapshot gaps H02/H03 remain. |
| F | Dated current/open/delayed infrastructure effects applied once | Demonstration event/effect is explicitly hypothetical; no causal uplift accuracy claim. |
| G | NPV ranking and exact full-network subset search with budget/count/risk rules | Measured runtime passes; strict hard deadline is not guaranteed (H04). |

Backend/API persistence and frontend connection remain owner integration work. This task does not establish full PRD acceptance, real-store validation, 30-run latency percentiles or decision-regret validation.

## B. Part E fixes

Changed production files: `backend/app/domain/engine.py` and `backend/app/domain/failfast/rules.py`. Added `tests/unit/test_rescue_handoff.py`. No other production algorithm, shared contract or schema changed.

**H01 rent:** the numerical helper returns effective monthly rent, whereas canonical `monthly_rent_inr` is base rent before the global multiplier. Returning effective rent as the override applied the multiplier twice. The domain response now separates `current_base_monthly_rent_inr`, `current_effective_monthly_rent_inr`, `max_viable_effective_monthly_rent_inr` and `max_viable_base_monthly_rent_inr`. For positive global multiplier g, canonical cap = effective cap / g. Requested rent bounds are retained as base INR/month. If the configured upper bound is below the economic cap, the returned action is that viable upper bound, explicitly labelled; its NPV need not be zero.

Zero global multiplier is contract-valid, but has no finite inverse base-rent cap: return `BLOCKED_ZERO_RENT_MULTIPLIER`, no threshold/action. Invalid negative, nonfinite, boolean or above-contract multipliers are rejected. Negative zero-rent NPV gives no financial rescue.

**H01 sales:** the numerical adjustment is relative to the already-scaled current target, whereas canonical `sales_multiplier` is absolute relative to baseline. The response now separates `current_absolute_sales_multiplier`, `relative_rescue_multiplier` and `new_absolute_sales_multiplier`. Canonical override = current absolute × relative rescue. Existing configured relative bounds stay within 0.5–3; their intersection with absolute multiplier <=3 and every year's attainable reference endpoints is explicitly reported. A zero current multiplier has no effect under a relative search and returns `BLOCKED_ZERO_CURRENT_SALES_MULTIPLIER`.

Every objective uses baseline fitted target × demand multiplier × new absolute sales multiplier × that year's infrastructure multiplier, in the same order as normal preparation. It recalibrates with the existing 0.01 INR reference tolerance, recomputes Huff allocation and own-store displacement, then runs the same finance engine. NPV or previously allocated revenue is never scaled as a substitute.

**H05 lower endpoint:** an unattainable lower endpoint previously terminated the search. The helper now checks all 17 grid points, refines lower and upper feasibility frontiers, rejects disconnected tested intervals and sampled NPV decreases, and bisects a verified feasible bracket. Physical infeasibility, no recovery, non-monotonicity and numerical failure have different reasons/statuses. Work is deterministic and bounded at 17 grid evaluations + 120 frontier refinements + 100 root iterations, with cached duplicate points. The domain additionally intersects analytically attainable reference bounds before searching, so a narrow physically attainable interval is not lost between coarse probes. An arbitrary black-box feasible island can still be missed by finite sampling; no global monotonicity/completeness proof is claimed.

**Action contract:** private response version `canonical-site-override-1`, `threshold_coordinates=CANONICAL_SITE_OVERRIDE`. Use `actionable_site_override` only when status is `SOLVED` and `application_status=VERIFIED_FRESH_SCENARIO_COPY`. `threshold` is the canonical value, never an effective rent or relative factor. Raw solver thresholds remain named diagnostics. An independent fresh copy passes through `prepare_evaluation`; actual applied NPV, revenue, displacement, cashflows, FailFast and model identity are attached as `applied_verification`. A hard eligibility failure always blocks the action and remains REJECTED even at a financial root. REVIEW_REQUIRED/negative-NPV applied results also block. AT_RISK warnings and required acknowledgement remain. No scenario is mutated or persisted and no ID is generated; backend must create a new scenario identity when applying a chosen override.

Actual reproduction results (explicit synthetic unit fixtures, INR; these are arithmetic checks, not fitted-model accuracy):

| Reproduction | Before fix | After fix / fresh application |
| --- | --- | --- |
| Rent, global multiplier 1.2 | Returned effective rent 44.68347724160228; solver NPV +0.0000454894, canonical direct application NPV **-406.5252369233** | Base override **37.23623103466857**; effective cap 44.68347724160228; independently applied NPV **+0.0000454894** |
| Sales, current absolute multiplier 2 | Returned relative 0.535552978515625; solver NPV +0.7490390018, canonical direct application NPV **-1826.4052045591** | Relative 0.5355224609375; absolute override **1.071044921875**; independently applied NPV **+0.5406117817**; relative bounds [0.5,3] intersect to [0.5,1.5] |
| Lower infeasible for x<1; NPV=1000(x-1.2) otherwise | NOT_RECOVERABLE_WITHIN_BOUNDS, no threshold | SOLVED at **1.20068359375**, NPV **+0.6835937500**; feasible bounds [1,3] |

New tests cover global rent 1 and 1.2, zero/invalid rent multipliers, the root and both rent sides, rent search bounds, unrecoverable economics, hard rejections, current absolute sales 1 and 2, unattainable targets, full displacement recalculation, exactly-once demand, canonical bounds, infeasible endpoints/interior, numeric errors and bounded determinism. Root cases require 0 <= applied NPV <= INR1 and independent annuity checks. Already-viable boundary cases are explicitly distinguished from zero-NPV roots.

The real ten-site smoke run also exercised all 20 rent/sales queries: 20/20 SOLVED with fresh-copy verification, still subject to AT_RISK warnings. Some are already viable at a configured boundary; this does not mean all 20 have zero residual. No unresolved failure was found in the requested Part E regression cases. Historical obsolete-test conflicts are listed in E; other review findings remain in F.

Evidence: `.runtime/ml-final-handoff/before.json`, `after.json`, `test_results.json` and `offline_smoke/rescues.json`. Old reports are retained as historical evidence, not rewritten to erase their findings.

## C. Part G performance

Actual local Python 3.12.10 workload: ten Bengaluru sites, 100 spending-cell centroids, 219 mapped external competitors, four synthetic existing branches, five-year projection, budget INR20,000,000, max_stores=10. Saved V2 inference is performed for each rebuilt project; frozen evaluation and portfolio are separately timed. Five runs per policy, ten runs total. OMP/OpenBLAS/MKL thread counts were set to 1.

Default policy acknowledges no AT_RISK sites and returns the empty portfolio. The separately declared illustrative policy acknowledges `site-01` through `site-10`, exercising all 1,024 subsets; these declarations are test policy inputs, not human investment approval. Existing `automatic_calibration_permitted=False` and shifted-market warnings are preserved, not overridden. The existing offline consumer's readiness-policy gap is explicitly recorded as H02 in F.

All times below are actual wall-clock seconds, rounded to six decimals:

| Policy/run | Source + inference | Frozen preparation | Portfolio search | Total flow | Examined/possible subsets | Search status |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Default 1 | 0.533624 | 0.264054 | 0.082810 | 0.880488 | 1/1 | FULL_NETWORK_EXACT |
| Default 2 | 0.203647 | 0.254624 | 0.077989 | 0.536260 | 1/1 | FULL_NETWORK_EXACT |
| Default 3 | 0.215416 | 0.264622 | 0.081562 | 0.561600 | 1/1 | FULL_NETWORK_EXACT |
| Default 4 | 0.199127 | 0.259281 | 0.084579 | 0.542987 | 1/1 | FULL_NETWORK_EXACT |
| Default 5 | 0.218736 | 0.263584 | 0.089631 | 0.571950 | 1/1 | FULL_NETWORK_EXACT |
| Acknowledged 1 | 0.204816 | 0.294880 | 0.113826 | 0.613522 | 1024/1024 | FULL_NETWORK_EXACT |
| Acknowledged 2 | 0.217960 | 0.268658 | 0.111868 | 0.598486 | 1024/1024 | FULL_NETWORK_EXACT |
| Acknowledged 3 | 0.202526 | 0.281217 | 0.105993 | 0.589736 | 1024/1024 | FULL_NETWORK_EXACT |
| Acknowledged 4 | 0.202485 | 0.270013 | 0.113371 | 0.585869 | 1024/1024 | FULL_NETWORK_EXACT |
| Acknowledged 5 | 0.214965 | 0.272449 | 0.108770 | 0.596185 | 1024/1024 | FULL_NETWORK_EXACT |

| Policy | Phase | Median seconds | Maximum seconds |
| --- | --- | ---: | ---: |
| Default | source_and_inference_seconds | 0.215416 | 0.533624 |
| Default | evaluation_prepare_seconds | 0.263584 | 0.264622 |
| Default | portfolio_search_seconds | 0.082810 | 0.089631 |
| Default | total_flow_seconds | 0.561600 | 0.880488 |
| Acknowledged | source_and_inference_seconds | 0.204816 | 0.217960 |
| Acknowledged | evaluation_prepare_seconds | 0.272449 | 0.294880 |
| Acknowledged | portfolio_search_seconds | 0.111868 | 0.113826 |
| Acknowledged | total_flow_seconds | 0.596185 | 0.613522 |

All ten searches returned FULL_NETWORK_EXACT; partial=0. Counts include budget/count-pruned subsets examined without a full objective. Each acknowledged run selected `site-05` + `site-10`, used INR19,800,000, left INR200,000 and returned simulated network NPV INR235,102,400.7403289. Default used zero budget and returned zero incremental network NPV.

The **measured portfolio target passes**: meaningful search maximum 0.113826 seconds; meaningful total-flow maximum 0.613522 seconds. Across both policies total-flow maximum was 0.880488 seconds. The slowest measured single phase was first-run source/model loading (0.533624 seconds). No Part G code change was necessary or made.

Timer scope begins with project/source/model loading and ends with the requested portfolio result; Python startup/imports, subsequent rescue queries, UI, persistence and other scenarios are excluded. Projects/evaluations are rebuilt per run; filesystem caches may be warm. Five observations per policy do not establish a production p95 or worst-case bound. The existing search checks its clock between objectives and cannot preempt a single in-flight objective. Passing this benchmark **does not establish a strict five-second hard deadline** for arbitrary inputs. Raw evidence: `.runtime/ml-final-handoff/portfolio_benchmark.json`.

## D. Active model

| Item | Verified identity / behavior |
| --- | --- |
| Adapter | `from ml.inference.reference_sales_v2 import ReferenceSalesEstimatorV2` |
| Artifact ID | `reference-sales-sim-v2-438774e0a585` |
| Artifact file | `ml/artifacts/reference_sales_v2/catboost.joblib` |
| SHA256 | `438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998` |
| Fitted estimator | CaptureModel wrapper with CatBoostRegressor; saved fitted preprocessing; CPU single-thread inference |
| Schema | `reference-sales-features-v2`; 20 required model inputs, 19 capture predictors excluding annual_wallet_inr |
| Output | `method_mode=model_simulated`, annual INR reference sales before own-company displacement |
| Wallet response | Fitted capture share × supplied annual wallet; exactly proportional wallet-only response for fixed supported capture features |
| Missingness | Only nearest competitor distance can be missing when mapped competitor count is zero; train-only fitted median/missing indicator. No invented household or routing inputs. |

Recorded synthetic metrics from unchanged `ml/evaluation/reference_sales_v2/metrics.json` (re-read, not refit or regenerated):

| Split | Rows | MAE INR/year | RMSE INR/year | WAPE |
| --- | ---: | ---: | ---: | ---: |
| validation | 400 | 7402550.33 | 10759234.07 | 6.401994% |
| test | 400 | 8824469.50 | 15816629.10 | 7.628145% |
| ood | 400 | 37495970.52 | 50525227.74 | 33.236204% |

CatBoost was selected by validation; B.2 Ridge has better test/OOD WAPE but was not substituted after test evaluation. These synthetic results establish no real-store accuracy. OOD/test WAPE ratio is about 4.357; `SHIFTED_MARKET_DEGRADATION_REVIEW` remains on every current candidate. Existing DaypartDNA ablation gives no demonstrated improvement; no optional model tuning was performed.

The loaded ten-site path remains supported: `site-01`, `site-02`, `site-03`, `site-04`, `site-05`, `site-06`, `site-07`, `site-08`, `site-09`, `site-10` pass the active schema, marginal and joint checks; sites 05/06 are near the existing support boundary. No threshold was weakened. Every site remains AT_RISK on evidence/reliability and `automatic_calibration_permitted=False`. Supported features do not mean qualified automatic calibration or investment readiness. Source reference geometry and whole-AOI centroid allocation differ, and commercial inputs are synthetic. Historically blocked `ml.inference.reference_sales.ReferenceSalesEstimator`/v1 Ridge is not promoted or used.

## E. Offline verification

Final combined command (from repository root):

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -m unittest tests.unit.test_decision_engine tests.unit.test_finance tests.unit.test_rescue_handoff -v
```

Result: **57 tests, 57 PASS, 0 failures, 0 errors, 0 skipped**. Original decision-engine/finance tests: 36/36; newly added rescue tests: 21/21. Harness wall time 5.968612 seconds (unittest's internal run time 5.714 seconds). The table lists every test in that final run; prior intermediate reruns are not counted as extra tests. Recorded warning: joblib/NumPy 2.5 array-shape deprecation; inference completed successfully.

| Test (under tests.unit) | Result |
| --- | --- |
| `test_decision_engine.ActualFittedBengaluru.test_actual_artifact_and_ten_site_end_to_end` | PASS |
| `test_decision_engine.ActualFittedBengaluru.test_actual_model_changes_boundary_diagnosis_and_selected_set` | PASS |
| `test_decision_engine.ActualFittedBengaluru.test_frozen_arrays_unchanged_by_joint_search` | PASS |
| `test_decision_engine.ActualFittedBengaluru.test_model_perturbation_changes_economics_not_only_label` | PASS |
| `test_decision_engine.ActualFittedBengaluru.test_portable_bundle_restores_inference_without_original_artifact_directory` | PASS |
| `test_decision_engine.AllocationChecks.test_calibration_and_unattainable_target` | PASS |
| `test_decision_engine.AllocationChecks.test_hand_calculated_shares_and_money_conservation` | PASS |
| `test_decision_engine.AllocationChecks.test_invalid_numerics_fail` | PASS |
| `test_decision_engine.AllocationChecks.test_own_branch_loss_deducted_once` | PASS |
| `test_decision_engine.AllocationChecks.test_wallet_scaling_and_competition` | PASS |
| `test_decision_engine.FailFastChecks.test_all_states_and_full_precedence` | PASS |
| `test_decision_engine.FailFastChecks.test_rent_threshold_oracle_and_no_rescue` | PASS |
| `test_decision_engine.FailFastChecks.test_sales_bounds_nonmonotonic_and_verified_root` | PASS |
| `test_decision_engine.GeometryAndDaypart.test_availability_override_and_duplicate_rejection` | PASS |
| `test_decision_engine.GeometryAndDaypart.test_dayparts_duration_and_frequency` | PASS |
| `test_decision_engine.GeometryAndDaypart.test_geodesic_metres_and_invalid_coordinates` | PASS |
| `test_decision_engine.GeometryAndDaypart.test_unknown_differs_from_supported_zero` | PASS |
| `test_decision_engine.PipelineChecks.test_demand_scale_and_zero_demand` | PASS |
| `test_decision_engine.PipelineChecks.test_future_effect_applied_once_with_frozen_model` | PASS |
| `test_decision_engine.PipelineChecks.test_missing_unsupported_and_invalid_inputs_fail_explicitly` | PASS |
| `test_decision_engine.PipelineChecks.test_pure_deterministic_immutable_pipeline_and_schema` | PASS |
| `test_decision_engine.PipelineChecks.test_rent_only_preserves_network_and_dayparts` | PASS |
| `test_decision_engine.PipelineChecks.test_rescue_does_not_clear_hard_failure` | PASS |
| `test_decision_engine.PipelineChecks.test_risk_acknowledgement_and_budget_source` | PASS |
| `test_decision_engine.PipelineChecks.test_stale_modified_and_missing_context_rejected` | PASS |
| `test_decision_engine.PipelineChecks.test_unattainable_target_is_review_not_silent_clipping` | PASS |
| `test_decision_engine.PortfolioChecks.test_all_1024_sets_and_independent_overlap_oracle` | PASS |
| `test_decision_engine.PortfolioChecks.test_forced_cutoff_is_truthful` | PASS |
| `test_decision_engine.PortfolioChecks.test_full_network_1024_sets_against_independent_cashflow_formula` | PASS |
| `test_decision_engine.PortfolioChecks.test_paise_budget_ties_and_empty_zero` | PASS |
| `test_decision_engine.TimingChecks.test_current_operational_cancelled_unknown_and_effect_signs` | PASS |
| `test_decision_engine.TimingChecks.test_midyear_and_delay_fraction` | PASS |
| `test_finance.FinanceOracleTests.test_invalid_values_rejected` | PASS |
| `test_finance.FinanceOracleTests.test_prd_cashflow_oracle` | PASS |
| `test_finance.FinanceOracleTests.test_worked_sites_reverse_sales_order` | PASS |
| `test_finance.FinanceOracleTests.test_zero_capex_and_no_recovery` | PASS |
| `test_rescue_handoff.FeasibleSearchTests.test_execution_is_deterministic_and_bounded` | PASS |
| `test_rescue_handoff.FeasibleSearchTests.test_feasible_but_unrecoverable_objective` | PASS |
| `test_rescue_handoff.FeasibleSearchTests.test_feasible_interior_with_both_endpoints_infeasible` | PASS |
| `test_rescue_handoff.FeasibleSearchTests.test_known_infeasible_lower_endpoint_still_finds_root_one_point_two` | PASS |
| `test_rescue_handoff.FeasibleSearchTests.test_no_feasible_point_is_distinct_from_numeric_failure` | PASS |
| `test_rescue_handoff.FeasibleSearchTests.test_nonmonotonic_objective_does_not_produce_action` | PASS |
| `test_rescue_handoff.FeasibleSearchTests.test_numerical_error_and_nonfinite_are_explicit_failures` | PASS |
| `test_rescue_handoff.RentApplicationTests.test_base_rent_search_bound_is_preserved` | PASS |
| `test_rescue_handoff.RentApplicationTests.test_hard_rejection_blocks_rent_action_and_survives_financial_threshold` | PASS |
| `test_rescue_handoff.RentApplicationTests.test_invalid_global_multipliers_rejected` | PASS |
| `test_rescue_handoff.RentApplicationTests.test_multiplier_one_applied_root_and_both_sides` | PASS |
| `test_rescue_handoff.RentApplicationTests.test_multiplier_one_point_two_applied_root_and_both_sides` | PASS |
| `test_rescue_handoff.RentApplicationTests.test_negative_zero_rent_npv_is_not_recoverable` | PASS |
| `test_rescue_handoff.RentApplicationTests.test_zero_global_multiplier_has_no_finite_inverse` | PASS |
| `test_rescue_handoff.SalesApplicationTests.test_configured_relative_bounds_intersect_canonical_limit` | PASS |
| `test_rescue_handoff.SalesApplicationTests.test_current_absolute_one_applies_zero_npv_scenario` | PASS |
| `test_rescue_handoff.SalesApplicationTests.test_current_absolute_two_applies_zero_npv_scenario` | PASS |
| `test_rescue_handoff.SalesApplicationTests.test_demand_once_and_existing_store_displacement_recomputed` | PASS |
| `test_rescue_handoff.SalesApplicationTests.test_hard_rejection_blocks_sales_action` | PASS |
| `test_rescue_handoff.SalesApplicationTests.test_unattainable_reference_range_returns_no_action` | PASS |
| `test_rescue_handoff.SalesApplicationTests.test_zero_current_absolute_multiplier_is_explicitly_blocked` | PASS |

These tests include conservation, exactly-once displacement, independent finance oracles, FailFast precedence, current/open/delayed effects, 1,024-set independent portfolio oracles, immutable deterministic contexts, actual saved CatBoost loading/ten-site predictions and portable bundle restoration. Negative tests assert explicit unavailable/blocked outcomes; they are not counted as successful rescues.

Additional executions:

- `python -m tests.unit.test_rescue_handoff --benchmark`: ten repeated actual fitted-path runs, all exact; results in C.
- Existing `ml.decision_engine.run.main()` with OUTPUT redirected in memory to `.runtime/ml-final-handoff/offline_smoke/`: actual data/model path, all ten AT_RISK, all 20 verified rescue actions, rent/demand comparisons and three hypothetical infrastructure states completed. Maximum share-conservation residual: 2.220446049250313e-16. No source edits were needed for redirection.
- Read-only pre-fix and post-fix H01/H05 reproductions: results in B. Artifact/baseline checks and Git diff validation: results in G.

Historical stage-specific tests were separately re-executed unchanged:

| Historical test (under tests.unit) | Actual result | Conflict |
| --- | --- | --- |
| `test_reference_sales_v2.V2Acceptance.test_16_original_versions_and_public_contracts_unchanged` | FAIL | Historical preservation baseline expects the pre-implementation pipeline; first mismatch is `backend/app/domain/pipeline.py`. |
| `test_reference_sales_v2.V2Acceptance.test_17_offline_local_artifact_and_no_orchestration` | ERROR | Expects an unimplemented seam to raise NotImplementedError; implemented input validation raises KeyError(project_id) on its empty fixture. |

These two obsolete baseline/stub assertions remain unresolved; production code was not reverted to satisfy them. The entire repository suite is **not** reported green. Training/retraining tests and training/report writers were not run. The prior 20/20 Part B verification is historical evidence from `PART_B_FINAL_VERIFICATION_REPORT.md`, not a new 20-test execution in this task. API/browser tests were not run.

## F. Backend teammate handoff

**Bundle and runtime.** Transfer `ml/evaluation/decision_engine_v1/reference_sales_v2_artifacts.zip` with `artifact_bundle_manifest.json`. Bundle SHA256: `daeb226f25d1c8b156cd8b753af550fcd4b01db3b0e8d71265123a27aeec50ab`. Its five required files are `manifest.json`, `catboost.joblib`, `feature_schema.json`, `support.json`, `MODEL_CARD.md`. The fitted preprocessor is embedded in the saved wrapper; retain the corresponding `ml/training/reference_sales_v2/model.py`, feature code and inference adapter. Required file hashes are in the manifest and verified on loading. Restore a missing local artifact directory with `python -m ml.decision_engine.package --install`; existing differing files are refused. No restoration is needed in the current checked environment.

Python 3.12.10 was used. Model dependency lock: `ml/training/reference_sales_v2/requirements-lock.txt` (numpy2.5.2, pandas2.3.3, scipy1.18.1, scikit-learn1.9.0, catboost1.2.10, joblib1.5.3). Existing backend Pydantic/schema dependencies remain in `backend/requirements-lock.txt`; keep the existing lockfiles unchanged.

**Entry points.** Local inference is `ReferenceSalesEstimatorV2().predict(typed_feature_row)`. Prefer typed inputs; explicit `allow_csv_strings=True` is only for the documented CSV adapter. `ml/decision_engine/run.py:build_project()` loads the actual Bengaluru source/mapping/model inputs; `baseline_scenario(project)` supplies the existing scenario. Pure domain exports in `backend.app.domain.pipeline`:

- `prepare_evaluation(project, scenario)` returns `{evaluation, context, diagnostics}`; context contains the frozen network and integrity digest.
- `run_evaluation(project, scenario)` returns the evaluation projection only.
- `run_portfolio(project, prepared['context'], max_stores, acknowledged_risk_site_ids)` consumes the private frozen context returned by preparation, including its evaluation and identity checks. A public evaluation projection alone is insufficient.
- `calculate_rescue(project, context, site_id, lever='rent'/'sales', lower_bound=..., upper_bound=...)` returns the private canonical action/evidence described in B. Backend owns public response mapping and scenario creation; no shared schema changes were made here.

Keep evaluation/scenario/input snapshot identity bound, and atomically persist result plus its private frozen context. Do not recompute financial outputs in frontend or duplicate the engine in transport. Use only a verified `actionable_site_override`; raw effective-rent diagnostics, relative rescue factors and public affordability display fields are not interchangeable with canonical overrides. Re-evaluate a newly identified scenario after application and independently enforce eligibility, acknowledgements and budget.

**Data locations.** `data/bengaluru/final/` retains the original 27 CSVs and unchanged 10x50 master. `data/bengaluru/revised_v2/site_features_enriched.csv` is the corrected 10x70 model feature view. Revised assumptions, lineage and quality/source/licensing evidence remain beside it and under `data/bengaluru/reports/`; raw snapshots remain under `data/bengaluru/raw/`. Original source-presentation report: `data/bengaluru/reports/data_sources_for_presentation.md`. Frozen prior engine evidence remains at `ml/evaluation/decision_engine_v1/`; new verification evidence is isolated under `.runtime/ml-final-handoff/`.

Exact offline run command, preserving frozen evidence by redirecting output before invoking the existing main:

```powershell
@'
from pathlib import Path
from ml.decision_engine import run
run.OUTPUT = Path('.runtime/ml-final-handoff/offline_smoke').resolve()
run.main()
'@ | python -
```

Use the environment and exact regression command in E first. Benchmark command: `python -m tests.unit.test_rescue_handoff --benchmark`. Do not run the unredirected evidence/training/report writers when preserving old results. These are local offline commands, not API orchestration.

**Canonical units/IDs.** Ten sites are `site-01` through `site-10`; use stable IDs rather than locality labels. Latitude/longitude are WGS84 degrees, distance metres, area square metres; annual wallet/reference revenue/OPEX/NPV/CAPEX are INR, base rent INR/month; margin/discount/ROI are fractions, not percentages. OPEX excludes rent and COGS; rent is annualised once; own-branch variable contribution lost is subtracted once. Shares are dimensionless. Six weekly bin durations are [25,20,25,50,24,24] hours in Asia/Kolkata. Preserve scenario/evaluation IDs, source IDs, model artifact ID and explicit synthetic/assumed status. No fabricated real sales target exists.

**Warnings and coordination dependencies (still open).**

| Finding | Required handoff behavior / limitation |
| --- | --- |
| H02 readiness/integration blocks | Existing private consumer gates do not fully enforce readiness flags/provenance; actual V2 predictions still have automatic_calibration_permitted=False although the offline demonstration calibrates. This benchmark exercises that existing policy without clearing/overriding the flag. Agree an explicit preliminary-to-approved calibration policy and enforce hard integration blocks before production use. The domain's current executable path is not approval. Keep v1 blocked. |
| H03 snapshot/input binding | Integrity/hash and basic identity checks pass current tests, but per-record feature/prediction/source snapshot binding and strict boolean validation remain incomplete. Coordinate typed validation, feature hashes/units/source revision and atomic persistence before integration. Passing a sealed-context test does not close this finding. |
| H04 timeout | Deadline checked between objectives only; strict in-flight cancellation/worst-case deadline is not guaranteed. Measured target passes; optimiser unchanged. |
| H06 opening hours | Source parser's accepted `off` exception can skip rather than clear previous schedule. No current candidate corruption was demonstrated for accepted source strings; source data was not regenerated. Correct or reject exception syntax in its own scoped change. |
| H07 Daypart explanation | Category/bin contributions, raw-normalized versus weekly shares and full per-profile dates/coverage/assumed fractions are incomplete. Parsed-hours support is only about 2.46–9.22%; preserve the assumed-hours distinction. These profiles are opportunity proxies, not measured footfall. |
| Spending/commercial price year | Modelled WorldPop2020 and nominal HCES2023–24 Karnataka urban spending (wallet ending-year2024) are compared with assumed/synthetic2026 commercial costs. No invented inflation adjustment was inserted; these NPVs are not consistent-price current commercial forecasts. |
| Model/support uncertainty | All ten sites retain SHIFTED_MARKET_DEGRADATION_REVIEW and AT_RISK. Marginal/joint support is not real-market validation. No calibrated confidence interval or measured sales accuracy exists; Daypart ablation does not prove benefit. |

Preserve null unknowns versus supported zero, source/assumption tags and model warnings. Invalid/unsupported fitted inputs must remain explicit errors/unavailable; unattainable reference calibration remains REVIEW_REQUIRED, not silent clipping. Hard rejection has precedence over finance and rescue; unacknowledged AT_RISK sites stay out of portfolios. This task does not connect API routes, SQLite, public schemas or frontend. The remaining readiness decisions require owner coordination, not automatic promotion.

## G. File and Git safety

Branch remains `ML`; HEAD remains `16728c7cd5f4268c6309a44f056c03cf0c207694`. No commits, pushes, branch switches, merges, rebases or pull requests were made. Current work is uncommitted.

Baseline comparison covers 366 existing files, excluding Git/runtime/dependency/cache directories. Only the two authorised domain files changed; the other 364 existing files are byte-identical. Added reviewable files: `tests/unit/test_rescue_handoff.py` and this report. Temporary scripts/results are isolated in ignored `.runtime/ml-final-handoff/`. No shared API/schema/frontend/database/root-configuration edits. `backend/app/domain/portfolio/search.py` is unchanged.

The preserved set includes B.2 fitted CatBoost and preprocessing/schema/support/manifest, synthetic training/validation/test/OOD source datasets, Bengaluru final/revised_v2 data, source/licence metadata, raw snapshots and all existing reports. Model SHA256 matches D. The real-source smoke run independently checked 250 protected model/data/source files unchanged. The broader 366-file baseline also preserves original offline engine evidence and bundle. No model was retrained, tuned or replaced, and no dataset was overwritten.
