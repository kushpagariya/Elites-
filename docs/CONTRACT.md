# StoreScout interface contract

The canonical schema is backend/app/schemas.py; contracts/openapi.json is generated from the application. frontend/src/lib/types.ts and runtime guards consume the same fields. Backend/integration owns changes. Envelope contract_version stays "1"; additive analytical fields use meta.schema_revision "analytical-2". Strict consumers must update with this increment. No units or existing status meanings changed.

## Semantics and compatibility

Base URL: http://127.0.0.1:8000/api/v1. Success is {data,meta}; errors are {error:{code,message,details:[{field,reason}]}}. 422 invalid input, 404 missing/cross-project identity, 409 snapshot/idempotency/report mismatch, 503 unavailable computation. No stack traces in responses. INR base amounts, monthly rent, annual OPEX excluding rent/COGS, ROI fractions, payback years, WGS84 input coordinates and metre distances. Null is unknown/not applicable, never zero. JSON rejects nonfinite numbers and unknown request fields.

Old saved scenarios are normalized with additive defaults: operating_cost_multiplier=1, competition_multiplier=1, gross_margin_fraction=null, valuation_date=2026-10-24. Dates use exact YYYY-MM-DD and must exist in the calendar. Baseline is immutable. Scenario assumptions are a complete replacement snapshot; base_scenario_id is provenance, not an instruction to apply a partial patch. Omitted budget inherits from the base. No schema/table migration or data deletion is needed.

## Operations

| Operation under /projects/{project_id} | Input / result | State |
|---|---|---|
| GET project, GET/POST scenarios, GET infrastructure | Existing Project, Scenario and labelled event records | Preserved |
| POST evaluate | EvaluateRequest -> Envelope[EvaluationData] | Computed assumption mode, atomically saved |
| GET evaluations, GET evaluations/{evaluation_id} | All saved evaluations / one matching project | Implemented |
| GET sites/{site_id}/analysis?evaluation_id= | Saved SiteAnalysis | Implemented |
| GET rankings?evaluation_id= | RankingData including rejected/review-required analyses | Implemented |
| GET dayparts?evaluation_id=&time_bin= | DaypartsData; bin optional, unknown bins 422 | Implemented |
| GET features?evaluation_id= | GeographicContext from frozen sources | Implemented; missing roads/competitors explicitly empty |
| GET model | ModelCard, artifact null, metrics null, trained_model_available false | Honest assumption estimator; ML promotion blocked |
| POST sites/{site_id}/rescue | RescueRequest -> RescueResult | Bounded, verified; never mutates a scenario |
| POST portfolios | PortfolioRequest -> PortfolioResult | OR-Tools integration; explicit UNAVAILABLE if runtime cannot import |
| GET portfolios/{portfolio_run_id} | Saved PortfolioResult | Implemented |
| GET reports/{evaluation_id}?portfolio_run_id=&format=html\|json | Frozen HTML download / JSON | Requires matching saved, completed portfolio |

## Scenario fields

Existing rent_multiplier, demand_multiplier, budget, infrastructure_state current/opens/delayed, effect fraction, opening_date and delay_months remain. New global gross_margin_fraction (null inherits per-site), operating_cost_multiplier 0–3 and competition_multiplier 0–3 are supported. Site overrides accept monthly_rent_inr, sales_multiplier 0–3, gross_margin_fraction 0–1, annual_opex_inr >=0 and competition_multiplier 0–3. Null/omitted overrides inherit. Explicit rent/OPEX overrides replace globally adjusted costs; local competition multiplies global pressure. Competition is a disclosed external-attraction assumption, not an observed competitor count.

## Evaluation fields

Existing fields remain, including site_analyses and roi_fraction. SiteAnalysis adds operating_profit_inr; effective_inputs; branch_impacts; low/base/high sensitivity FinanceSnapshots; calibration; infrastructure_exposure[]; dayparts[]. Operating profit is before existing-branch displacement; network cash flow subtracts displaced contribution exactly once. Sensitivity reallocates -20%/+20% wallet spending; low also adds 10% rent. These are deterministic commercial cases, never confidence intervals.

Evaluation evidence identifies feature/source snapshots, finance/rule/weight/estimator versions, valuation date, disclosed parameters and limitations. model_artifact_id stays null for scenario_assumptions. No trained model or accuracy claim is fabricated.

Six canonical bins: weekday_morning (06–11), weekday_lunch (11–15), weekday_evening (15–20), weekday_night (20–06), weekend_day (06–18), weekend_evening (18–06), Asia/Kolkata. Raw POI opportunity weights category, decay and weekly duration (25/20/25/50/24/24 hours). Unknown opening hours assume availability. opportunity_index is 0–100 within-site share of the six supported raw bins, NOT a cross-city calibrated score. No supported POIs gives null; supported zero gives 0. Each profile carries categories/counts, source IDs, reliability, source status and nullable observation date. Synthetic fixture dates remain unknown. Baseline POI profiles do not claim observed changes from hypothetical future infrastructure.

Infrastructure exposure uses a disclosed 3 km radial linear decay. The reference-sales bridge is applied once per year, before attraction calibration, using geographic exposure × assumed effect × active-year fraction. Current excludes proposed events; Opens uses an explicit/labelled hypothetical date; Delayed shifts it by the saved month count. Cancelled events never activate. Missing dates/geometry require review when a nonzero future effect is requested. One valuation date/horizon is shared across scenarios. Catchments on the map are geodesic display circles, not road isochrones.

## Rescue

RescueResult: evaluation_id, site_id, lever, status, lower_bound, upper_bound, threshold|null, verified, npv_at_threshold|null, reasons[], remaining_failed_rule_ids[]. Status is SOLVED, NOT_RECOVERABLE_WITHIN_BOUNDS or NON_MONOTONIC. Rent defaults to [0,max(3× effective rent,1,000,000)] INR/month; the exact zero-rent-NPV / discounted rent-annuity threshold is clipped to bounds and verified through the same network. Sales defaults to [0.5,3], checks 13 samples for monotonicity, then bisects and verifies. This is a bounded numerical monotonicity check, not a global proof outside the range. A no-solution result is not a transport error. Applying a verified result creates/evaluates a complete new scenario; unrelated budget, coverage, evidence and downside rules are rechecked.

## Portfolio

Budget, original assumptions and all attractions come from the saved private evaluation context. Eligibility is VIABLE or explicitly acknowledged AT_RISK. Request max_stores includes zero. Amount feasibility is in integer paise. Enumerate at most 1,024 subsets and compute each feasible set using the common network denominator, then OR-Tools CP-SAT selects a table row with maximum paise-rounded NPV, lower CAPEX, fewer stores and sorted IDs as deterministic ties. No sum of singleton NPVs or second candidate-pair penalty. Five seconds covers enumeration and solving; incomplete search never claims exactness.

Existing status FULL_NETWORK_EXACT / FEASIBLE_PARTIAL / UNKNOWN remains. Additional solver_status OPTIMAL / FEASIBLE / PARTIAL / UNAVAILABLE / UNKNOWN, name/version, objective_precision_inr=.01, optimality_gap (0 if proven, null otherwise), exclusions with reason codes/reasons, limitations, max_stores and acknowledged_risk_site_ids are saved. evaluated_subsets counts examined masks, including infeasible/filtered masks. Empty is a valid zero-valued computed plan; UNAVAILABLE is not an empty-plan recommendation. UI hides decision totals and disables export for unavailable/unknown output.

## Persistence, retries and identity

SHA-256 over canonical sorted project/scenario/source content, engine version and schema revision identifies immutable evaluations. Changed source content changes the ID even if a fixture label is reused. Public evaluation and private frozen context commit in one existing SQLite transaction; failure rolls back both. Same inputs return the original saved result. Finance/rule/model identities and declared parameters are part of the key. New rescue/portfolio requests reject incompatible saved method versions with 409; historical reports remain readable. Optional Idempotency-Key cannot identify different inputs (409). Portfolio runs are immutable and uniquely identified; retry can create another equivalent run. Report retrieval is read-only and rechecks evaluation/run association.

The client aborts superseded requests and checks incrementing tokens and project/scenario/evaluation identities. Edits mark all derived output stale; old successful values remain visibly stale while portfolio/export is disabled. Optional geography is keyed to the displayed evaluation. A failed geography request cannot overwrite finances.

## Verification

python -m unittest tests.unit.test_finance tests.unit.test_decision_engine tests.contract.test_scaffold -q

From frontend: pnpm test; pnpm typecheck; pnpm build. Final end-to-end acceptance is deliberately deferred. The current Windows OR-Tools import is blocked by Application Control on pandas._libs.sparse; the optimization integration is implemented but has not been numerically verified in this host. Report serialization uses an explicitly test-only saved completed portfolio fixture. See docs/IMPLEMENTATION_REPORT.md.
