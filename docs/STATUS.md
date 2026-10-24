# Frontend/backend integration status

Working branch: frontend-backend-integration.

Integrated sources:
- Backend: cedbce2 (also present on main through merge 8db534b).
- Frontend: 4d04832, including the new map-first workspace, expandable feature navigation and retail landing redesign. Prior integration baseline: 4e5345f.
- ML branch remains at the original scaffold; no trained ML artifact is activated.

## Connected prototype

Latest frontend increment: preserved the incoming design and shared evaluation state. The online OpenFreeMap street basemap, selection details, Daypart period controls, percent-based scenario inputs, before/after view and investment-plan presentation connect to the existing transactional backend. Local CORS permits the explicit localhost/127.0.0.1 origins on ports 3000 and 3001; arbitrary external origins are rejected. Report header exposure remains enabled. No numerical engine or ML mode was changed by this increment.

Browser checks on the built refreshed app: selected an existing assumed growth scenario, ran analysis, compared two sites, opened a map location, inspected backend-supplied POI/daypart and financial data, and saved/evaluated a rent edit through the new percentage controls. Verified the resulting before/after values, calculated its investment plan, downloaded its saved report and reopened its preview. The redesigned landing page rendered without captured console errors. Online map streets and attribution rendered. An online basemap is a network dependency; synthetic business locations remain clearly labelled and a table/shortlist is still available if the map fails.

- Landing page and single frontend application root preserved.
- /app: ten Navi Mumbai grocery candidates, four fictional branches, saved evaluation, two-site financial comparison, sensitivity, branch impacts, map evidence and six-bin DaypartDNA.
- /app/scenarios: full immutable assumptions, rent/demand/margin/OPEX/competition controls, Current/Opens/Delayed, bounded rescue proposals and explicit apply/re-evaluate.
- /app/portfolio: evaluated-scenario budget, count/risk constraints, full-network selection, exclusions and matching saved report download/preview.
- Backend retains atomic evaluation/context saves, idempotency, source/model/engine hashes, independent budget/eligibility checks, bounded workers and safe error envelopes.
- Rich frontend result DTOs are integrated into canonical Pydantic/OpenAPI schemas. Saved geographic reads use original evaluation inputs.
- Assumption mode is visible throughout. No trained model, calibrated interval, measured footfall or empirical retail accuracy is claimed.

## Integration decisions

The incoming branch also changed backend transport and added a competing services.py. Kept the transactional services package and adapted the incoming numerical functions rather than replacing persistence with the less complete duplicate service. Added frozen-context adapters and preserved both rescue verification field names for compatibility.

Replaced the extra CP-SAT dependency with the PRD's capped exact full-network enumeration. It examines up to 1,024 subsets, includes empty zero, preserves budget/count/eligibility/risk constraints and returns truthful exact/partial status. No individual NPV summation or additional pair penalty is used. Comparison/tie precision is INR 0.01; returned financial values retain full precision.

Fixed a rescue boundary case: a viable upper rent bound is not a break-even threshold. A range without a crossing now returns an explicit bounded no-solution explanation rather than an invalid SOLVED response.

## Checks completed on this integration

- Python unit/numerical checks: 12 passed, zero skipped.
- Python API/repository checks: 23 passed, including allowed local-origin preflight, report-header exposure and rejection of an unapproved origin.
- Frontend node tests: 28 passed, including new presentation, geographic geometry and expandable-navigation checks.
- Frontend type generation and TypeScript no-emit: passed.
- Production build: passed; routes /, /app, /app/scenarios and /app/portfolio generated.
- OpenAPI regenerated.
- Real HTTP smoke uses frontend's actual runtime-guarded API adapters against an isolated local verification database: all three infrastructure states, saved reopening, geography, DaypartDNA, bounded rescue/application, cached evaluation, nonempty exact portfolio, zero-budget/count plan, matching saved report and invalid-budget rejection.
- Browser on the actual production frontend: evaluated baseline, selected two sites and read financial/sensitivity/daypart results; saved an explicit demand/rent/OPEX scenario; computed its 1,024-subset portfolio; downloaded the saved report and reopened its exact content in the preview.
- Browser navigation preserved active context across the three workspace routes. Reload/return preserved the selected saved scenario.
- SYNTHETIC/ASSUMED labels and scenario_assumptions mode stayed visible.

For this frontend refresh, typecheck and production build both passed. The previous integration's initial sandbox EPERM and successful retry are historical; no product configuration workaround was introduced.

Test doubles remain isolated in tests. Numerical fixtures establish synthetic invariants, not empirical forecast quality. The positive portfolio demonstration uses explicitly changed assumed demand and costs; it is not an observed investment outcome.

## Run

From the repository root:

    python -m venv .venv
    .venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
    .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000

In another terminal:

    cd frontend
    pnpm install --frozen-lockfile
    pnpm dev

Open http://127.0.0.1:3000/app.
API docs: http://127.0.0.1:8000/docs.
Optional local backend reload: add --reload --reload-dir backend.
The current local session runs the refreshed built frontend on port 3001: http://127.0.0.1:3001/app. The standard pnpm dev command still defaults to port 3000.

For verification only, run an isolated backend with STORESCOUT_DB_PATH pointing to a separate local SQLite file and port 8001, then in frontend:

    $env:STORESCOUT_TEST_API='http://127.0.0.1:8001/api/v1'
    pnpm test:live

This creates labelled smoke scenarios; it does not delete/reset stored user data.

## Remaining acceptance gaps

- Meaningful-AI gate: fit and validate a real learned artifact on the agreed synthetic/real target contract, then integrate inference and model card. Current wallet-share estimates are explicit assumption mode.
- Project creation and validated CSV imports.
- Remaining full-PRD source quality/model evaluation/user validation/performance/reliability checks. No full AC01-32 completion claim.
- Further analytical review should assess synthetic defaults and commercial parameter behavior before any real investment use.
- The previously configured branch-check automation is currently PAUSED in app configuration. Do not silently reactivate it; preserve its expiry and user preference.

No main/frontend/ML branch is overwritten or force-pushed by this integration. The combined result is published on frontend-backend-integration.
