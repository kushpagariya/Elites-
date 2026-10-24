# Shared implementation contract

Backend owns schema changes. Canonical types: backend/app/schemas.py; generated OpenAPI: contracts/openapi.json; TypeScript mirror/client: frontend/src/lib/. Regenerate using python scripts/export_contract.py. The internal integration agreement is in docs/BACKEND_INTEGRATION_WORKFLOW.md.

## Common rules

Base URL: http://127.0.0.1:8000/api/v1. Success is {data, meta: {contract_version: "1", fixture_id: "demo-1", ...}}. Errors are {error: {code, message, details: [{field, reason}]}}. OpenAPI includes this error shape.

Local browser origins: localhost and 127.0.0.1 on ports 3000 and 3001, plus the single configured FRONTEND_ORIGIN. The API exposes Content-Disposition for report consumers. No wildcard origin or arbitrary-port pattern is enabled.

Money is INR; revenue and other OPEX are annual; rent monthly; CAPEX upfront; rates/ROI decimal fractions; area square metres; coordinates WGS84. Nonfinite values are invalid. Unknown is null, never zero. Source labels are SYNTHETIC, ASSUMED, REAL.

Seed identities: project demo, scenario baseline, feature snapshot features-demo-1, fixture demo-1, weights weights-demo-1. Backend allocates other IDs. Candidate cap ten; existing branch cap four. Fixture valuation date is pinned to 2026-10-24 in frozen inputs.

## Routes and current state

Paths below are relative to /api/v1/projects/demo unless indicated otherwise.

| Method/path | Input/output | Current implementation |
| --- | --- | --- |
| GET /api/v1/health | Liveness/integration status | Working; never proof of analytical readiness |
| GET /api/v1/projects/demo | Project | Working synthetic fixture |
| GET /scenarios | Scenario[] including baseline | Working |
| POST /scenarios | ScenarioCreate -> Scenario, 201 | Immutable SQLite save; optional idempotency |
| GET /scenarios/{id} | Saved Scenario | Working |
| GET /infrastructure | Hypothetical event records | Working |
| GET /features | Frozen raw source snapshot; prepared=false | Working; not computed spatial features |
| GET /model | Active estimator disclosure or installed card/hash details | Missing fitted bundle explicitly reports assumption mode; invalid bundle is 503 |
| POST /evaluate | EvaluateRequest -> EvaluationData | Connected assumption-based engine with atomic save |
| GET /evaluations/{id} | Saved EvaluationData | Implemented; 404 until result saved |
| GET /sites/{id}/analysis?evaluation_id=... | Saved SiteAnalysis | Implemented; no recomputation |
| GET /rankings?evaluation_id=... | evaluation_id, rankings[], diagnoses keyed by site ID | Implemented from saved evaluation |
| GET /dayparts?evaluation_id=...&time_bin=... | Saved sites/profiles, optionally filtered by bin | Connected; no measured footfall implied |
| POST /sites/{id}/rescue | RescueRequest -> RescueResult | Connected bounded solver; saved proposal only |
| GET /rescues/{id} | Saved RescueResult | Implemented |
| POST /portfolios | PortfolioRequest -> PortfolioResult | Exact full-network enumeration; checks and atomic save |
| GET /portfolios/{id} | Saved PortfolioResult | Implemented |
| GET /reports/{evaluation_id}?portfolio_run_id=... | Printable saved HTML | Implemented; format=json returns envelope; mismatched run is 409 |

The frontend branch's deterministic assumption-based engine is now connected. It is not a trained ML model and does not pass the meaningful-AI readiness gate. Missing numerical modules still map to explicit 503 errors. Numerical tests establish bounded synthetic invariants, not empirical forecast accuracy.

GET /features?evaluation_id=... returns the frontend GeographicContext: evaluation_id, cells, POIs, ten catchment polygons, radius, empty unavailable roads/competitors and limitations. Without evaluation_id, the original frozen raw source snapshot remains available for compatibility. All saved geographic reads use original evaluation inputs.

## Scenario

Example POST /scenarios:

    {"base_scenario_id":"baseline","name":"Rent negotiation","budget_inr":20000000,"assumptions":{"demand_multiplier":1,"rent_multiplier":1,"site_overrides":{"site-01":{"monthly_rent_inr":150000}},"infrastructure_state":"current","infrastructure_effect_fraction":0,"opening_date":null,"delay_months":24}}

Assumptions are a complete replacement snapshot, not a patch. Copy the selected scenario before editing; preserve unchanged fields and overrides. Pydantic supplies defaults for omitted fields, so omission does not inherit an override. Budget inherits when omitted or null. Unknown site overrides fail validation. Dates must be ISO calendar dates YYYY-MM-DD.

Date/horizon activation and partial-year effects now come from the connected domain engine. Expanded assumptions support gross_margin_fraction, operating_cost_multiplier, competition_multiplier and valuation_date. Per-site overrides additionally support gross_margin_fraction, annual_opex_inr and competition_multiplier. Project creation/imports remain unavailable.

## Evaluation

POST /evaluate:

    {"scenario_id":"baseline","feature_snapshot_id":"features-demo-1"}

Public EvaluationData:

- evaluation_id, project_id, scenario_id, created_at_utc
- method_mode: model_simulated | model_real_evaluated | scenario_assumptions
- model_artifact_id (nullable)
- site_analyses[]
- rankings[]: eligible site IDs sorted by descending NPV, lower CAPEX, stable ID

Each SiteAnalysis has site_id, annual_revenue_inr, lost_existing_contribution_inr, annual_cashflows_inr[], npv_inr, roi_fraction?, payback_years?, failfast, drivers[], source_ids[].

FailFast has status (VIABLE/AT_RISK/REJECTED/REVIEW_REQUIRED), failed_rule_ids[], reasons[], max_viable_monthly_rent_inr?, required_sales_multiplier?, rescue_status.

All candidates must have exactly one analysis; annual cash flows cover the saved horizon; source IDs belong to the frozen manifest. No trained mode may claim an absent/mismatched model artifact.

SiteAnalysis now includes operating_profit_inr, low/base/high sensitivity snapshots, branch_impacts, effective_inputs, infrastructure_exposure, calibration and six dayparts. EvaluationData adds evidence with source/model/formula identifiers and limitations. Full schemas are in schemas.py/OpenAPI and matching frontend types/guards. Do not invent frontend-only analytical values.

## Rescue

POST /sites/site-01/rescue:

    {"evaluation_id":"<saved-id>","lever":"rent","lower_bound":0,"upper_bound":800000}

Bounds above are an example. Default rent bounds are 0 to twice effective saved monthly rent; default sales bounds are 0.5 to 3. Supplied bounds must be finite/nonnegative/ordered; sales upper bound cannot exceed 3.

RescueResult: rescue_id, evaluation_id, site_id, lever, lower_bound, upper_bound, status, threshold?, verification_npv_inr?, npv_at_threshold?, verified, reasons[], remaining_failed_rule_ids[]. Both NPV fields identify the same verification value; the latter matches the frontend's guarded adapter.

Status: SOLVED | NOT_RECOVERABLE_WITHIN_BOUNDS | NON_MONOTONIC. SOLVED requires an in-bounds threshold and domain verification NPV within INR 1 of zero. Threshold units are monthly INR for rent or a sales multiplier. The backend checks the returned verification; numerical verification itself belongs to logic.

A saved proposal does not mutate the scenario/evaluation. Applying it requires a new scenario and evaluation. A viable search bound is not falsely labelled break-even: when no crossing lies in the bounds, the response explains that the range must change. Zero-rent default upper bound has a minimum of INR 1 to keep the search interval valid.

## Portfolio

POST /portfolios:

    {"evaluation_id":"<saved-id>","max_stores":2,"acknowledged_risk_site_ids":[]}

Budget comes from the evaluation's saved scenario, never the current UI or baseline project budget. Acknowledgements identify AT_RISK sites in that evaluation.

PortfolioResult: portfolio_run_id, evaluation_id, selected_site_ids[], budget_used_inr, budget_unused_inr, full_network_npv_inr, status, evaluated_subsets, total_subsets. Extensions include max_stores, acknowledged_risk_site_ids, solver_status/name/version, exclusions, objective_precision_inr, optimality_gap and limitations. The capped prototype uses exact enumeration without an OR-Tools dependency; tie precision is INR 0.01 and returned financial values retain full precision.

Status: FULL_NETWORK_EXACT | FEASIBLE_PARTIAL | UNKNOWN. Exact requires completed counts. Empty zero is valid. An incomplete search cannot claim global optimality. Backend independently checks IDs, count, eligibility, acknowledgements and CAPEX/budget reconciliation in paise. It cannot prove numerical optimality without the logic invariants.

Full-network NPV is supplied by logic. Never sum individual site NPVs.

## Persistence and replay

Canonical SHA-256 cache keys include project/scenario values, source file hashes, feature snapshot ID, actual model/card hashes, domain Python source hash and orchestration identifier. Weights/rules/financial source changes invalidate the key. Portfolio adds evaluation ID, max count and sorted acknowledgements.

Public evaluation, private frozen context, cache index and successful idempotency record commit in one transaction. Failed stages/invalid results commit nothing. Concurrent identical requests return the first committed result.

Optional Idempotency-Key is 1–128 characters, scoped by project and operation. Reusing it with different request input returns 409 IDEMPOTENCY_CONFLICT. Successful replay returns the original record; failed calculation does not reserve the key. Scenario creation without a key always creates a new immutable record.

Saved reads/report use the original snapshot and never rerun calculations. Portfolio/rescue reject changed engine/model identities with 409 before recomputation.

## Internal domain seams

run_evaluation(project_dict, scenario_dict) returns computed EvaluationData fields without IDs/time/envelope. Backend loads files into project.inputs. Optional private _context must be a finite JSON object. Backend removes it before public validation and saves it as evaluation_context.prepared_network. Missing frozen context prevents portfolio/rescue.

run_portfolio(project_dict, evaluation_context, max_stores, acknowledged_risk_site_ids) returns computed PortfolioResult fields without IDs. Context has project, scenario, evaluation, prepared_network and snapshot. Supplied project budget is the saved scenario budget.

The imported domain rescue function is run_rescue(prepared_network, site_id, lever, lower_bound, upper_bound). Backend adapts its verified/npv_at_threshold/remaining_failed_rule_ids response to the persisted RescueResult. Portfolio receives network_context as an internal alias of the saved prepared_network. Both use the frozen original assumptions and inputs.

Model bundles contain model_card.json and a relative artifact_file within STORESCOUT_MODEL_DIR (default ml/artifacts/). Card requires model_artifact_id and method_mode. Backend computes hashes and checks optional artifact_sha256. Model metrics are only what the actual card records; a valid file hash alone cannot prove real inference or forecast accuracy.

## Runtime errors and limits

At most two analytical worker slots; default timeout 15 seconds, configurable up to 120. A timed-out worker retains its slot until completion and cannot publish a late result.

- 404 NOT_FOUND: unknown/cross-project object.
- 409 STALE_SNAPSHOT/STALE_ENGINE/STALE_MODEL/IDEMPOTENCY_CONFLICT.
- 422 INVALID_INPUT: invalid dates, bounds, IDs or request fields.
- 502 ENGINE_INVALID_OUTPUT: bad analytical schema or integrity checks.
- 503 ENGINE_UNAVAILABLE/MODEL_UNAVAILABLE/CONTEXT_UNAVAILABLE.
- 503 ENGINE_BUSY/ENGINE_TIMEOUT/COMPUTATION_FAILED.

Raw sources cap cells at 2,000 and POIs at 10,000. Input/output numbers must remain finite. Report strings are HTML-escaped and reports use a restrictive content-security policy.

Contract tests use explicitly injected test engines. They validate transport/persistence and do not establish numerical correctness, model quality or complete product acceptance.
