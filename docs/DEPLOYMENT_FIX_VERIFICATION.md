# Deployment recovery verification

Verified locally on 25 October 2026 using Python 3.12.14, CatBoost 1.2.10, joblib 1.5.3 and NumPy 2.5.2. Production configuration pins Python 3.12.10; both use the supported Python 3.12 minor version. This record distinguishes local acceptance from public deployment status.

## Confirmed production failures before this patch

- Render `/api/v1/health`: 200 despite `/api/v1/showcase` returning 503 `MODEL_UNAVAILABLE` with an internal installation command.
- Public Vercel `/api/v1/health`: 200 and `/api/v1/showcase`: the same backend 503. The current same-origin API proxy was connected; an API 404 was not reproduced in this deployment.
- Public Vercel `/vendor/maplibre/maplibre-gl-worker.mjs`: 404 HTML instead of JavaScript. The generated worker was ignored by Git and prepared only by package scripts, which direct deployment builds could skip.
- Render CORS preflight: the protected preview domain was allowed; `https://elites-ivory.vercel.app` was rejected. This needs the existing Render service's `FRONTEND_ORIGIN` environment value corrected.
- The repository's selected artifact files were ignored. The backend lockfile already pinned CatBoost; no version upgrade or replacement model was needed. The public 503 occurs at artifact verification before deserialization, so a missing production CatBoost package cannot be inferred from that response alone. The new build check exercises actual inference, which also catches dependency failures.

## Fixes and files

| Files | Change |
| --- | --- |
| `.gitignore`, `.gitattributes`, five `ml/artifacts/reference_sales_v2/` files | Track only the approved package and preserve byte-exact checksums across Windows/Linux. Other artifacts remain ignored. |
| `scripts/prepare_deployment.py`, `render.yaml` | Install/verify the package and exercise public-preview inference at build time, supported Python, correct entry point, readiness and persistent-storage configuration. |
| `backend/app/services/sources.py`, `backend/app/main.py` | Safe startup restore, internal failure logs, honest liveness/readiness, independent geographic/infrastructure data and customer-safe model errors. |
| `backend/app/services/presentation.py` | Populate DaypartDNA category evidence using the delivered domain function, without changing financial values or model predictions. |
| `frontend/next.config.ts`, `frontend/scripts/map-assets.cjs`, `frontend/scripts/prepare-map.mjs`, `frontend/vercel.json` | Prepare the matched worker during direct Next builds as well as package builds; explicit Vercel build settings, JavaScript headers and production API-origin validation. |
| `frontend/src/lib/{workspace.tsx,types.ts}`, workspace shell, Explore, LocationMap and workspace CSS | Accurate service status, concise pre-analysis/loading/error states, independent competitor inventory with retry, style-ready layer attachment and bounded failed-map space. |
| Contract, tests, docs and environment examples | New readiness route, targeted recovery coverage and exact deployment steps. |

The existing landing layout and animation sources, ML inference/training/domain logic and input datasets were not changed. No assumption estimator was substituted for the fitted model.

## Passed checks

- `.venv/Scripts/python.exe scripts/check_integration.py`: **91 passed**, including numerical finance/engine/rescue, actual fitted baseline, API/auth/account isolation, snapshot identity, saved scenarios, PDF evidence and four new deployment regressions. Expected failure-injection tracebacks stay in test logs and do not indicate failed tests.
- `node --test frontend/tests/*.test.cjs`: **32 passed**, including missing-versus-zero evidence, compact pre-analysis/loading/failure states, controls and request-order handling.
- Direct `node node_modules/next/dist/bin/next build` from `frontend/`: **passed**, including TypeScript and all seven static pages. Used a local API proxy on port 8015; Vercel must build again with its Render origin.
- `python scripts/prepare_deployment.py`: **ready**. Verified model `reference-sales-sim-v2-438774e0a585`, six periods and Current/Opens/Delayed preview. All five recorded SHA-256 checksums match; model SHA-256 is `438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998`.
- `STORESCOUT_TEST_API=http://127.0.0.1:8015/api/v1 node tests/live-smoke.mjs` from `frontend/`: **passed**. Current/Opens/Delayed, six dayparts/geography, rescue/apply, full-network portfolio, saved PDF, invalid-budget rejection and sign-in/restoration.
- Local production HTTP: worker **200**, `text/javascript`, 518806 bytes; `/api/v1/ready` **200**, correct model identity. OpenAPI regenerated and `git diff --check` passed.
- Real browser against the local production build: created an isolated local account, rendered actual OpenFreeMap streets and neighbourhood labels in both workspace maps, displayed 219 competitors before evaluation, clicked a candidate, ran analysis, saw sales/NPV/risk, selected two candidates and saw populated comparison and six-period/category evidence. This check did **not** replace the street provider with a test background. Fit/reset controls and attribution were present.

The full live-smoke flow uses temporary local accounts; production user passwords/tokens were not submitted or logged. Screenshots are stored outside the repository in this chat's output folder. Historical model-development audits that require unbundled training artifacts are outside the supported application suite. Real-world sales accuracy remains unvalidated.

## Deployment handoff

See [DEPLOYMENT.md](DEPLOYMENT.md) for exact commands and environment values. Committing configuration does not edit the existing services' dashboard settings or guarantee a redeploy. In particular, correct Render's `FRONTEND_ORIGIN` to the public domain, keep the repository root, install backend requirements, use Python 3.12 and rebuild/redeploy. Existing data needs persistent disk and a migration before changing its path. Vercel must use the `frontend` root and rebuild with `STORESCOUT_API_ORIGIN=https://elites-n3v9.onrender.com` and browser API base `/api/v1`.

Public post-release status must be checked separately. This record does not claim the live deployment has recovered merely because local tests passed.
