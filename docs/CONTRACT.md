# Shared implementation contract

Backend owns schema changes. Canonical types: backend/app/schemas.py; generated OpenAPI: contracts/openapi.json; TypeScript mirror/client: frontend/src/lib/. Regenerate using python scripts/export_contract.py. The internal integration agreement is in docs/BACKEND_INTEGRATION_WORKFLOW.md.

## Common rules

Authentication: POST `/api/v1/auth/register` accepts name, email and a 12–128 character password; POST `/auth/login` accepts email/password. Both return `{data: {id, name, email}}` and a seven-day HttpOnly, SameSite=Lax session cookie. GET `/auth/me` reads the signed-in account; POST `/auth/logout` revokes the session. `/projects/*` requires a valid session (401 otherwise). Each account has separate saved scenarios/evaluations/reports; shared synthetic baseline inputs remain labelled. Browser calls use the frontend's same-origin `/api/v1` proxy; direct clients must retain cookies. Authentication attempts are rate-limited. For HTTPS hosting set `STORESCOUT_SECURE_COOKIES=1` and the explicit `FRONTEND_ORIGIN`. Email verification and password recovery are not connected.

Base URL: http://127.0.0.1:8000/api/v1. Success is {data, meta: {contract_version: "1", fixture_id: "demo-1", ...}}. Errors are {error: {code, message, details: [{field, reason}]}}. OpenAPI includes this error shape.

Local browser origins: localhost and 127.0.0.1 on ports 3000 and 3001, plus the single configured FRONTEND_ORIGIN. The API exposes Content-Disposition for report consumers. No wildcard origin or arbitrary-port pattern is enabled.

Money is INR; revenue and other OPEX are annual; rent monthly; CAPEX upfront; rates/ROI decimal fractions; area square metres; coordinates WGS84. Nonfinite values are invalid. Unknown is null, never zero. Source labels are SYNTHETIC, ASSUMED, REAL.

Seed identities: project demo, scenario baseline, feature snapshot bengaluru-features-20261024-v1, fixture bengaluru-20261024, weights weights-demo-1. Backend allocates other IDs. Candidate cap ten; existing branch cap four. The 219 contextual competitor POIs do not count as candidates. Valuation date is pinned to 2026-10-24 in frozen inputs.

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
| GET /features | GeographicContext with nullable evaluation_id | Source map context before analysis; saved evaluation geometry when an ID is supplied |
| GET /model | Active estimator disclosure or installed card/hash details | Missing fitted bundle explicitly reports assumption mode; invalid bundle is 503 |
| POST /evaluate | EvaluateRequest -> EvaluationData | Connected B.2 fitted CatBoost and domain engine with atomic save |
| GET /evaluations/{id} | Saved EvaluationData | Implemented; 404 until result saved |
| GET /sites/{id}/analysis?evaluation_id=... | Saved SiteAnalysis | Implemented; no recomputation |
| GET /rankings?evaluation_id=... | evaluation_id, rankings[], diagnoses keyed by site ID | Implemented from saved evaluation |
| GET /dayparts?evaluation_id=...&time_bin=... | Saved sites/profiles, optionally filtered by bin | Connected; no measured footfall implied |
| POST /sites/{id}/rescue | RescueRequest -> RescueResult | Connected bounded solver; saved proposal only |
| GET /rescues/{id} | Saved RescueResult | Implemented |
| POST /portfolios | PortfolioRequest -> PortfolioResult | Exact full-network enumeration; checks and atomic save |
| GET /portfolios/{id} | Saved PortfolioResult | Implemented |
| GET /reports/{evaluation_id}?portfolio_run_id=... | Stored application/pdf bytes | PDF is saved atomically with the portfolio. Correct filename, IDs and SHA256 in response headers; mismatched run is 409. Diagnostic format=json/html remains available. |
| GET /workspace?scenario_id=... | WorkspaceView | Last view per account, or saved view for one scenario. Restores evaluation/portfolio, two candidate IDs and before/after references. |
| POST /workspace | WorkspaceState | Account-scoped current and per-scenario pointers; validates every referenced identity and candidate selection. |

The fitted B.2 CatBoost and deterministic domain engine are connected in model_simulated mode. The model was trained on synthetic labels, not observed store sales; no empirical forecasting accuracy or automatic investment approval is established. Missing/invalid model bundles fail explicitly.

GET /features?evaluation_id=... returns GeographicContext from that evaluation's saved inputs. Without evaluation_id it returns source map records with evaluation_id=null, before any financial analysis. Competitors are POIs whose category is competitor; names are nullable. No competitor financial results are invented. Cells/catchment geometry are labelled proxies; roads and the legacy competitors array remain empty.

## Scenario

Example POST /scenarios:

    {"base_scenario_id":"baseline","name":"Rent negotiation","budget_inr":20000000,"assumptions":{"demand_multiplier":1,"rent_multiplier":1,"site_overrides":{"site-01":{"monthly_rent_inr":150000}},"infrastructure_state":"current","infrastructure_effect_fraction":0,"opening_date":null,"delay_months":24}}

Assumptions are a complete replacement snapshot, not a patch. Copy the selected scenario before editing; preserve unchanged fields and overrides. Pydantic supplies defaults for omitted fields, so omission does not inherit an override. Budget inherits when omitted or null. Unknown site overrides fail validation. Dates must be ISO calendar dates YYYY-MM-DD.

Date/horizon activation and partial-year effects come from the domain engine. Supported controls are demand_multiplier, rent_multiplier, site_overrides (base monthly_rent_inr and absolute sales_multiplier), budget and infrastructure timing/effect. Margin/OPEX/CAPEX/competition/horizon/valuation-date edits and project creation/imports remain deferred; unsupported request fields are rejected. Switching infrastructure states preserves an intentional zero commercial effect.

## Evaluation

POST /evaluate:

    {"scenario_id":"baseline","feature_snapshot_id":"bengaluru-features-20261024-v1"}

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

Bounds above are an example. Default rent bounds are 0 to twice saved base monthly rent; default sales bounds are 0.5 to 3 relative to the current target. Supplied bounds must be finite/nonnegative/ordered. The returned sales override is absolute relative to baseline, intersected with the canonical limit of 3.

RescueResult: rescue_id, evaluation_id, site_id, lever, lower_bound, upper_bound, status, threshold?, verification_npv_inr?, npv_at_threshold?, verified, reasons[], remaining_failed_rule_ids[]. Both NPV fields identify the same verification value; the latter matches the frontend's guarded adapter.

Status: SOLVED | NOT_RECOVERABLE_WITHIN_BOUNDS | NON_MONOTONIC. SOLVED requires a canonical in-bounds override and fresh-scenario verification with nonnegative NPV. BREAK_EVEN means residual within INR1; VIABLE_BOUND is an already-viable tested bound and can have positive NPV. Rent is base INR/month, sales is absolute baseline multiplier. Numerical verification belongs to logic; backend validates the evidence and units.

A saved proposal does not mutate the scenario/evaluation. Applying actionable_site_override creates a new what-if scenario/evaluation and saves before/after references. Financial recovery never clears hard rejection or evidence risks. Zero-rent default upper bound has a minimum of INR1; zero global rent multiplier and zero current sales multiplier are explicitly blocked when no actionable inverse is defined.

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

Saved reads/report use the original snapshot and never rerun calculations. Portfolio/rescue reject changed engine/model identities with 409 before recomputation. PDF bytes, evidence and SHA256 are stored atomically with new portfolios. Legacy plans freeze their original saved evidence on first PDF export; historical missing metadata cannot be reconstructed. Reopening an existing PDF never runs the renderer again. The client validates MIME, signature, evaluation/run headers and checksum, and previews the downloaded bytes.

## Internal domain seams

run_evaluation(project_dict, scenario_dict) returns computed EvaluationData fields without IDs/time/envelope. Backend loads files into project.inputs. Optional private _context must be a finite JSON object. Backend removes it before public validation and saves it as evaluation_context.prepared_network. Missing frozen context prevents portfolio/rescue.

run_portfolio(project_dict, evaluation_context, max_stores, acknowledged_risk_site_ids) returns computed PortfolioResult fields without IDs. Context has project, scenario, evaluation, prepared_network and snapshot. Supplied project budget is the saved scenario budget.

The domain seam is calculate_rescue(project, prepared_network, site_id, lever, lower_bound=..., upper_bound=...). Backend maps canonical application evidence into RescueResult. Portfolio calls run_portfolio(project, prepared_network, max_stores, acknowledgements). Both use frozen original assumptions and inputs.

The active bundle is ml/artifacts/reference_sales_v2: manifest.json, catboost.joblib, feature_schema.json, support.json and MODEL_CARD.md. Approved file hashes are in ml/evaluation/decision_engine_v1/artifact_bundle_manifest.json. The backend checks every file and model_simulated identity; synthetic metrics do not establish real-sales accuracy. The historical v1 model remains blocked.

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
