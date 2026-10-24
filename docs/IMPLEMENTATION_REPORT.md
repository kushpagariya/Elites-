# StoreScout implementation report

The original application, landing page, light white/black/purple design, SQLite object structure and tested finance helper were preserved. Changes add a computed, assumption-based analytical path and typed frontend consumption. No final end-to-end acceptance test was performed. The initial implemented/partial/missing/dependency classification is in STATUS.md.

## Delivered

- Deterministic geodesic catchments, disclosed wallet-share reference estimator, bounded attraction calibration, shared cell-wallet allocation, branch contribution displacement once, operating profit, cash flow, NPV/ROI/payback, low/base/high sensitivity, ranked eligibility and three computed drivers.
- Six DaypartDNA periods with category counts, distance/duration weights, null-vs-zero evidence and explicit reliability/source-date limitations.
- Immutable global/site margin, operating-cost and competition edits; existing rent/demand/budget controls preserved. Calendar-valid event dates, geographic exposure, Current/Opens/Delayed and per-year active fractions affect the reference target once.
- FailFast classifications and all applicable reasons. Exact discounted rent-annuity rescue and bounded sales search, verified against the same saved network. Applying rescue saves a complete new scenario and rechecks other failures.
- OR-Tools CP-SAT implementation selects among full-network subset values, with integer-paise feasibility/objective and deterministic ties. Risk acknowledgement, zero stores, budget, exclusions, deadline and solver states are explicit. This implementation is integration-ready but its numerical solver check is blocked on this host.
- Atomic public/private evaluation snapshots, deterministic deduplication, Idempotency-Key conflict handling, saved query endpoints, matching portfolio records and escaped downloadable HTML/JSON reports.
- Compact comparison cards and table, period controls, POI/catchment map layers, useful empty/error/unavailable states and expandable Technical Details. Request aborts and incrementing tokens prevent obsolete finance/geography/rescue output from replacing current state.

## API and compatibility

Canonical Pydantic schemas, generated OpenAPI, TypeScript types and runtime guards were updated together. Envelope contract_version remains 1; schema_revision analytical-2 identifies additive fields. Existing scenario records acquire neutral defaults during deserialization; the baseline and database tables are unchanged. Strict consumers must update before consuming added fields. Units and existing wire status values are preserved. CONTRACT.md contains exact fields, endpoints, bounds, inheritance, solver and null semantics.

## Checks actually run

System pnpm wrapper used because the bundled pnpm launcher previously failed; from repository root:

~~~powershell
$pnpmCli = 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.mjs'
node $pnpmCli --dir frontend test
node $pnpmCli --dir frontend typecheck
node $pnpmCli --dir frontend build
python -m unittest tests.unit.test_finance tests.unit.test_decision_engine tests.contract.test_scaffold -q
python -m pip install ortools==9.14.6206 --disable-pip-version-check --quiet
python -c "from ortools.sat.python import cp_model; print('CP-SAT ready')"
python scripts/export_contract.py
node frontend/tests/render-analytical-preview.cjs
~~~

Results: 23 frontend tests passed; TypeScript passed; production build passed with /, /app, /app/scenarios and /app/portfolio routes. Python: 18 run, 17 passed, one solver check skipped. The independent single-cell closed-form revenue/branch-loss/NPV oracle and real bounded sales/rent rescue checks passed. Atomic rollback, saved evaluation retrieval, idempotency conflict, six-bin/geographic/ranking/model response contracts and report identity/evidence serialization passed. A changed method version rejects new rescue decisions with 409 while the historical report remains readable.

Failures recorded: the first TypeScript check found a nullable rescue access (fixed); the first canonical evaluation check found missing additive response fields (fixed). The initial solver test failed because importing OR-Tools imports pandas._libs.sparse, which Windows Application Control blocks. Solver check is now explicitly skipped on unavailable runtime; it has NOT passed. The standard Python OpenAPI writer failed with Windows bad-file-descriptor; OpenAPI was generated from app.openapi() through Node fs.writeFileSync/execFileSync instead. Starting a second server on ports 3000/8000 returned address-in-use; existing servers were left intact. A temporary port-3001 frontend rendered its connection error correctly but lacked API CORS access. The temporary preview and isolated rendering servers were stopped after inspection.

The isolated component rendering helper uses clearly labelled TEST-ONLY synthetic transport state, never imported by the application. Desktop comparison hierarchy/spacing were visually inspected in the browser. It stubs the map surface and has static controls; it does not verify live map layers, complete routing or acceptance. Generated preview HTML is ignored and was removed. No new responsive browser acceptance claim is made; responsive CSS and existing keyboard semantics are retained. Prettier 3.6.2 formatted only changed frontend files through pnpm dlx, without adding a project dependency.

## Remaining dependencies and unverified behavior

1. Backend/runtime: OR-Tools is installed but not importable under this host's application-control policy. Verify a permitted Python environment; do not weaken system policy. Portfolio numerical correctness, optimal/partial solver behavior and a report generated from a real solved run remain unverified. UI shows unavailable rather than fake zero decision totals.
2. ML: no trained CatBoost artifact exists. All output is scenario_assumptions with null model ID and null accuracy metrics. Before promotion, ML must supply the artifact SHA-256, ordered compatible feature manifest, training-only preprocessing, reference-sales target definition, grouped split/model card and the README evaluation gates. Own-branch and outcome features must remain excluded. Then replace the estimator seam in prepare_context while preserving the shared allocation/result contracts and new artifact-based evaluation identity.
3. Data: all demo business/geographic inputs remain SYNTHETIC; category, availability, competitive pressure and financial inputs are ASSUMED. No observed road/competitor inventory, source observation dates, measured footfall, real-sales validation or calibrated intervals were added. Roads/competitors have empty typed layers plus limitations. Catchments are radial, not travel-time isochrones. Daypart profiles describe baseline POI support; evidence-backed future-event temporal changes need new permitted destination/date data, using the same profile contract.
4. Validation boundaries: sales monotonicity is checked at 13 bounded samples before bisection; no global mathematical monotonicity proof or claim outside the range. Model OOD regime detection requires the approved model/feature manifest. API/scenario error paths are covered by focused checks, not exhaustive adversarial tests.
5. Scope: this remains the fixed 10-candidate/four-branch demonstration. New-project/CSV onboarding, broader geography, data/model research gates and full PRD AC01–32 acceptance are not declared complete. No backend input fixtures, baseline records or database structure were deleted.
6. Runtime parity: checked with Python 3.13 / FastAPI 0.141.1 / Pydantic 2.13.4. Existing core pins target FastAPI 0.115.14 / Pydantic 2.11.7; a clean pinned runtime needs verification. Added numerical dependency versions are recorded in backend requirements files. One frontend pnpm lockfile is retained.

## Exact next integration steps

- Backend: create/choose a permitted clean runtime, install backend/requirements-lock.txt, confirm CP-SAT import, then run python -m unittest tests.unit.test_decision_engine.DecisionTests.test_portfolio_full_network_empty_risk_and_cutoff -v without a skip. Check all 1,024 masks/exactness, risk acknowledgement, valid empty and forced cutoff. Restart the existing API from this checkout, with STORESCOUT_DB_PATH pointing to a writable persistent SQLite file (OneDrive journal writes failed earlier).
- Frontend: restart the existing port-3000 server from frontend/ so it loads this build. Keep NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1. Re-evaluating the selected saved scenario reopens its deduplicated evaluation. Verify candidate selection, advanced controls, actual POI/catchment layers and stale notices with the restarted API; then verify a genuine completed portfolio/report when the solver works.
- ML: deliver the approved compatible artifact/model card, activate it with a new estimator/model identity and rerun targeted inference/allocation tests; do not reuse assumption-mode cache identities or invent quality metrics.
- After integration: arrange the deferred full journey, rapid-switch/restart/keyboard/backend-failure checks and reopen an actually solved report. Only then conduct final PRD acceptance. No full-acceptance evidence has been claimed here.

Design guidance actually used: Impeccable for hierarchy/states, Emil design engineering for restrained interaction/accessibility details, and Taste's app-screen guidance for the compact comparison composition. Existing brand/type choices were preserved. Handbook v3.0 process guidance was read in the appended 70-page handbook (combined 107-page handoff), especially typed contracts, incremental integration and compatibility/evidence practices; product facts remain governed by the project's PRD.

## Changed files

- backend/app/domain/pipeline.py
- backend/app/domain/portfolio/optimize.py
- backend/app/main.py
- backend/app/services.py
- backend/app/repositories/store.py
- backend/app/schemas.py
- backend/requirements.txt
- backend/requirements-lock.txt
- contracts/openapi.json
- docs/ARCHITECTURE.md
- docs/CONTRACT.md
- docs/STATUS.md
- docs/IMPLEMENTATION_REPORT.md
- frontend/.gitignore
- frontend/src/app/(workspace)/workspace.css
- frontend/src/components/WorkspaceShell.tsx
- frontend/src/features/explore/Explore.tsx
- frontend/src/features/explore/LocationMap.tsx
- frontend/src/features/scenarios/Scenarios.tsx
- frontend/src/features/portfolio/Portfolio.tsx
- frontend/src/lib/api.ts
- frontend/src/lib/types.ts
- frontend/src/lib/guards.ts
- frontend/src/lib/workspace.tsx
- frontend/src/lib/workspace-model.ts
- frontend/tests/analytical-ui.test.cjs
- frontend/tests/render-analytical-preview.cjs
- tests/unit/test_decision_engine.py
- tests/contract/test_scaffold.py
