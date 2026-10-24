# Shared implementation contract

Backend owns changes. Canonical types: `backend/app/schemas.py`; generated OpenAPI: `contracts/openapi.json`; frontend mirrors: `frontend/src/lib/types.ts`. Regenerate with `python scripts/export_contract.py`. Runtime docs: `/docs`. Schema identifiers are technical identifiers, not a document release badge.

## Common rules

Base URL `http://127.0.0.1:8000/api/v1`. Success `{data: ..., meta: {contract_version:'1',fixture_id:'demo-1',...}}`; errors `{error:{code,message,details:[{field,reason}]}}`. INR amounts, decimal fractions, square metres, WGS84 coordinates; use metric/geodesic distances. Nonfinite values are invalid; unknown is null plus a reason. Source labels are SYNTHETIC, ASSUMED, REAL. Never interpret synthetic as observed.

Identifiers in this seed: project `demo`; immutable scenario `baseline`; feature snapshot `features-demo-1`; fixture `demo-1`; weight matrix `weights-demo-1`. Backend allocates other scenario/evaluation/run IDs. All requests validate project/object association. Finance uses full precision; round only display/accepted paise. Candidate cap 10; branch cap four.

## Routes and implementation state

| Method/path | Input -> success | Setup state / H4 owner |
| --- | --- | --- |
| GET /health | none -> status and implementation_status | Working / backend |
| GET /projects/demo | none -> Project | Working synthetic fixture |
| GET /projects/demo/scenarios | none -> Scenario[] | Working saved list |
| POST /projects/demo/scenarios | ScenarioCreate -> Scenario, 201 | Working immutable SQLite save |
| GET /projects/demo/infrastructure | none -> infrastructure records | Working hypothetical event |
| POST /projects/demo/evaluate | EvaluateRequest -> EvaluationData | 501 until backend+logic integrate |
| GET /projects/demo/sites/{id}/analysis?evaluation_id=... | saved analysis | Backend adds route for H4 |
| GET /projects/demo/rankings?evaluation_id=... | saved sorted site IDs + diagnoses | 501; backend derives from saved evaluation |
| POST /projects/demo/sites/{id}/rescue | RescueRequest -> verified threshold plus fixed-input assumptions | 501; logic computes/backend persists no scenario mutation |
| POST /projects/demo/portfolios | PortfolioRequest -> PortfolioResult | 501; exact full-network pipeline |
| GET /projects/demo/dayparts?evaluation_id=...&time_bin=... | raw index/share/support/source IDs | 501; coordinate additions before UI depends on them |
| GET /projects/demo/features | prepared snapshot | 501; backend reads logic-prepared snapshot |
| GET /projects/demo/model | model mode/artifact/split/metrics/features | 501; backend exposes actual model card |
| GET /projects/demo/reports/{evaluation_id}?portfolio_run_id=... | saved printable HTML/JSON | Backend adds route; no unsaved slider state |

Project creation/CSV import, richer financial assumptions, detailed evidence/Daypart response models and full report styling follow the H4 slice. Backend freezes those small schemas with consumers before they implement them; no owner independently invents endpoint shapes.

## Scenario request

```json
{"base_scenario_id":"baseline","name":"Rent negotiation","budget_inr":20000000,"assumptions":{"demand_multiplier":1,"rent_multiplier":1,"site_overrides":{"site-01":{"monthly_rent_inr":150000}},"infrastructure_state":"current","infrastructure_effect_fraction":0,"opening_date":null,"delay_months":24}}
```

`assumptions` is a **complete replacement snapshot**, not a patch. UI first reads/copies the selected scenario, edits it, and sends the complete result. `base_scenario_id` tracks provenance. Budget inherits only when omitted. Missing overrides mean no override; unknown site IDs are rejected. Current setup uses strings for dates; backend must add ISO date and horizon validation before infrastructure activation.

## Evaluation request and response

Request `{"scenario_id":"baseline","feature_snapshot_id":"features-demo-1"}`. Domain returns computed fields; service adds identities/time then validates `EvaluationData`:

- `evaluation_id, project_id, scenario_id, created_at_utc, model_artifact_id`.
- `method_mode`: model_simulated, model_real_evaluated or scenario_assumptions. Missing model never silently claims ML.
- `site_analyses[]`: site_id, annual_revenue_inr, lost_existing_contribution_inr, annual_cashflows_inr, npv_inr, roi_fraction?, payback_years?, failfast, drivers[], source_ids[].
- `failfast`: status, failed_rule_ids[], reasons[], max_viable_monthly_rent_inr?, required_sales_multiplier?, rescue_status.
- `rankings[]`: site IDs sorted by NPV, lower CAPEX and stable ID; excluded diagnoses remain in site_analyses.

Full sensitivity and POI support fields need a coordinated schema extension during H1-H2. Don't encode annual revenue as a 0-100 score or ROI as percent when its field expects a decimal.

## Portfolio request and response

Request `{"evaluation_id":"<saved-id>","max_stores":2,"acknowledged_risk_site_ids":[]}`. Budget comes only from the evaluation's saved scenario. Response data fields are portfolio_run_id, evaluation_id, selected_site_ids[], budget_used_inr, budget_unused_inr, full_network_npv_inr, status, evaluated_subsets and total_subsets. Status: FULL_NETWORK_EXACT, FEASIBLE_PARTIAL or UNKNOWN. Empty set with zero NPV is valid; incomplete search cannot prove no positive portfolio exists.

Logic receives private context with exact scenario, public evaluation and frozen network/model inputs. It must recompute joint allocation; sum of individual NPVs is invalid. Backend rechecks budget/count/acknowledgements independently.

## Persistence and idempotency to implement

Create an evaluation cache key from SHA-256 of canonical sorted-key JSON: project/scenario hash + feature/source snapshot IDs + model artifact hash + rule/weight/finance versions. Portfolio key adds evaluation ID, max count and sorted acknowledgements. Same input returns the same saved evaluation; changed inputs create a new immutable record. Current scaffold only persists scenarios; backend implements result/context transactions before H3. UI keys every result by evaluation/scenario ID and rejects obsolete responses.

## Internal seams

`domain.pipeline.run_evaluation(project_dict, scenario_dict) -> computed_fields_dict`. Project internal inputs contains source files/feature snapshot; logic performs no HTTP/SQL. Backend adds identity/time fields before `EvaluationData.model_validate`.

`run_portfolio(project_dict, evaluation_context_dict, max_stores, acknowledged_risk_site_ids) -> computed_fields_dict`; service adds portfolio_run_id/evaluation_id and validates `PortfolioResult`. Logic owns the full-network operation; backend owns retrieval and atomic persistence. These seams currently raise NotImplementedError.
