# Frontend/backend integration status

Working branch: frontend-backend-integration.

Integrated sources:
- Backend: cedbce2 (also present on main through merge 8db534b).
- Frontend: d694ef2, including the consolidated workspace and assumption-based analytical engine.
- ML branch remains at the original scaffold; no trained ML artifact is activated.

## Connected prototype

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
- Python API/repository checks: 22 passed.
- Frontend node tests: 23 passed.
- Frontend type generation and TypeScript no-emit: passed.
- Production build: passed; routes /, /app, /app/scenarios and /app/portfolio generated.
- OpenAPI regenerated.
- Real HTTP smoke uses frontend's actual runtime-guarded API adapters against an isolated local verification database: all three infrastructure states, saved reopening, geography, DaypartDNA, bounded rescue/application, cached evaluation, nonempty exact portfolio, zero-budget/count plan, matching saved report and invalid-budget rejection.
- Browser on the actual production frontend: evaluated baseline, selected two sites and read financial/sensitivity/daypart results; saved an explicit demand/rent/OPEX scenario; computed its 1,024-subset portfolio; downloaded the saved report and reopened its exact content in the preview.
- Browser navigation preserved active context across the three workspace routes. Reload/return preserved the selected saved scenario.
- SYNTHETIC/ASSUMED labels and scenario_assumptions mode stayed visible.

The first production-build attempt was blocked by Windows sandbox EPERM when creating generated Next.js output. Reran the same build outside that sandbox; it passed without a product configuration workaround.

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
The current local session also runs the built frontend on port 3000.

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
