# Backend and integration workflow

Current integration: `frontend-backend-integration` merges frontend commit `d694ef2` with backend commit `cedbce2`. The existing frontend architecture is preserved. Richer schema extensions, actual assumption-based evaluation, DaypartDNA/geographic reads and rescue/portfolio/report are connected. The original steps below remain the design rationale; use current CONTRACT.md and STATUS.md for delivered behavior. ML training/inference is still unavailable. The imported rescue signature is `run_rescue(prepared_network, site_id, lever, lower_bound, upper_bound)`; the backend adapter handles persistence/verification fields. Exact full-network enumeration replaces the extra CP-SAT dependency for this capped prototype.

Work on `backend-integration`, starting from scaffold commit `569f4f5`. Frontend continues on `frontend`; analytical modules continue on `ML` or the logic owner's branch. Do not overwrite either owner's files. This plan implements transport and persistence independently of the numerical engine.

## Delivery order

| Gate | Backend deliverable | Required teammate input | Verification |
| --- | --- | --- | --- |
| 1 | Frozen source loading, model identity, stable errors, immutable scenarios | Read agreed interfaces | Invalid dates/IDs rejected; sources honestly labelled |
| 2 | Evaluation orchestration, atomic result/context save, cache and idempotency | `run_evaluation` | No partial writes; repeated requests replay; unavailable engine is explicit |
| 3 | Saved evaluation/site/ranking/daypart reads and rescue orchestration | Computed profiles and `run_rescue` | All output refers to the same evaluation; rescue does not mutate it |
| 4 | Portfolio persistence, independent eligibility/budget checks, printable report | `run_portfolio` with frozen network | Budget/count/risk checks; matching report IDs; empty set supported |
| 5 | Bring compatible teammate commits into integration, clean start and rehearse | Frontend connected to actual endpoints, actual fitted model | Typecheck/build, analytical invariants, whole journey |

Integrate bounded commits every 30–45 minutes. Reserve the last 30 minutes of the four-hour checkpoint for verification. Four hours is a prototype checkpoint within the event, not full PRD acceptance. Cut decorative work before correctness. Full scope remains F01–F08 and AC01–32.

## Runtime sequence

1. Browser reads project/scenarios/infrastructure and prepares a complete assumptions snapshot.
2. Scenario POST validates and saves a new immutable record. GET by ID supports reopening.
3. Evaluate POST loads that scenario, all local fixture sources, source content hashes, actual model bundle identity and domain source hash. These identities define the evaluation cache key.
4. Backend calls the synchronous domain seam on a bounded worker pool. No backend financial formulas or simulated production outputs are supplied.
5. Validate the entire public evaluation, candidate coverage, ranking identities and source references. Save public result and private frozen context in one SQLite transaction. Return only the public result.
6. Saved analysis/ranking/profile reads use the evaluation ID; they never recompute against current files.
7. Rescue loads original context and calls the domain rescue function. It saves a proposal only. Applying it requires a new scenario/evaluation.
8. Portfolio loads original context and budget, calls domain, independently validates IDs/eligibility/count/CAPEX/search status, then atomically saves the run.
9. Report reads a saved evaluation and optional matching portfolio. Escape all strings; preserve source/method identities. No unsaved browser state enters a report.

## Domain integration seam

Existing public computed fields and the two existing function signatures remain unchanged. Domain owner supplies implementations in `backend/app/domain/pipeline.py`.

`run_evaluation(project, scenario)` returns the computed `EvaluationData` fields without generated IDs/time. One optional internal key, `_context`, holds JSON-serializable frozen network state. Backend removes it before strict public validation and stores it privately as `prepared_network`. A nonempty frozen context is required before portfolio/rescue can run. No domain function reads SQLite or performs HTTP.

`project['inputs']` includes `cells`, `pois`, `infrastructure`, `weights`, `source_manifest`, `feature_snapshot_id`, `snapshot_hash`, source file hashes and local model bundle information. The fixture valuation date is pinned to `2026-10-24`, never the wall clock. No real population fields are implied by the supplied synthetic wallets.

`run_portfolio(project, evaluation_context, max_stores, acknowledged_risk_site_ids)` receives context keys `project`, `scenario`, `evaluation`, `prepared_network`, and `snapshot`. Return existing `PortfolioResult` computed fields without IDs. The saved scenario budget overrides the baseline project budget in this call. Full-network NPV must be recomputed by logic, never summed by backend.

The proposed rescue seam is `run_rescue(project, evaluation_context, site_id, request)`. Return `status`, `threshold` (nullable), `verification_npv_inr` (nullable), and `reasons[]`. Bounds are supplied after backend normalization. Backend supplies IDs, lever and bounds. `SOLVED` requires threshold inside bounds and a verified NPV within INR 1 of zero. This is an integration extension for the domain owner to implement; backend does not add a fake domain function.

Detailed sensitivity, POI support and infrastructure analysis output extensions remain a coordinated producer/consumer task. Do not smuggle unvalidated fields into the public evaluation. Until then daypart reads honestly report unavailable, rather than returning illustrative scores.

## Model bundle agreement

Default directory: `ml/artifacts/`; override with server-only `STORESCOUT_MODEL_DIR`. Supply `model_card.json` with `artifact_file` (relative file within this directory), `model_artifact_id`, `method_mode` (`model_simulated` or `model_real_evaluated`), plus actual feature schema/split/metrics. Backend calculates SHA-256 of the artifact and card; it does not invent metrics or infer accuracy. Domain's returned model ID/mode must match the installed bundle. A missing bundle is visible and prevents a result claiming trained inference. Transparent `scenario_assumptions` output remains possible but does not pass the AI readiness gate.

Model artifacts are currently Git-ignored: agree artifact transfer with ML owner and document installation. Preserve the artifact hash with saved evaluations. Persisted portfolio/rescue must fail with 409 if the current analytical source differs from the saved engine, rather than silently mix implementations.

## Integration acceptance

- Contract tests use explicit injected test engines; their fixture outputs are not production analytics or model evidence.
- Test atomic rollback, duplicate/concurrent cache requests, idempotency conflict, restart retrieval, invalid output, stale model/engine, budget/risk constraints and HTML escaping.
- Run actual finance/network/model invariants with the ML implementation when delivered.
- Merge frontend only after its one-app consolidation; verify annual INR, decimal ROI, ten/four Navi Mumbai fixture, 24-month delay and six time bins.
- Run frontend typecheck/build and the whole saved scenario → evaluation → rescue → portfolio → report journey. Record exact commit, model hash, checks and remaining gaps.
- Push integration commits to `backend-integration`; promote to main only after the complete slice is checked. Never force-push.
