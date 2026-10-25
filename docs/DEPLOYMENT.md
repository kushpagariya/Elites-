# Vercel frontend and Render API

The public website is `https://elites-ivory.vercel.app`; the API is `https://elites-n3v9.onrender.com`.

## Existing Render service

Keep **Root Directory empty** (repository root). The API requires `backend/`, `ml/` and `data/` together.

- Build: `pip install -r backend/requirements.txt && python scripts/prepare_deployment.py`
- Start: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --workers 1`
- Python: 3.12 (the Blueprint pins 3.12.10).
- Health check: `/api/v1/ready`.
- `FRONTEND_ORIGIN=https://elites-ivory.vercel.app`
- `STORESCOUT_SECURE_COOKIES=1`
- `STORESCOUT_DB_PATH=/var/data/storescout/storescout-bengaluru.sqlite3` when a persistent disk is mounted at `/var/data`.

`render.yaml` describes a disk-backed Starter service. Applying it to an existing service requires matching its settings in Render; committing a Blueprint does not change an independently created service. It is configuration only and does not purchase a plan. Do not create a second API accidentally. A free service without persistent storage cannot retain SQLite accounts across replacement deployments; migrate/back up existing account and per-user workspace files before moving their directory.

Only the five approved files under `ml/artifacts/reference_sales_v2/` are trackable. Other generated artifacts remain ignored. They match the committed, allowlisted ZIP and checksum manifest in `ml/evaluation/decision_engine_v1/`. Build preparation verifies these files, restores missing package files, imports the fitted estimator and computes the three-state public preview. Missing native dependencies, corrupt artifacts or incompatible schemas fail the build. API startup also restores missing package files for existing services that have not yet adopted the build command. Differing installed files are never overwritten and no model is retrained or silently replaced with another estimator. Failure details go to backend logs.

`/api/v1/health` is liveness plus honest `analytics_status`; `/api/v1/ready` returns 503 unless startup has loaded the analytical path. Mapped POIs, catchments and infrastructure do not depend on CatBoost availability. If build/startup fails, inspect Render logs for artifact verification or inference import errors rather than asking users to install the model.

## Vercel project

- Root Directory: `frontend`.
- Framework: Next.js.
- Install: `pnpm install --frozen-lockfile`.
- Build: `pnpm build` (direct `next build` is also supported).
- `STORESCOUT_API_ORIGIN=https://elites-n3v9.onrender.com`
- `NEXT_PUBLIC_API_BASE_URL=/api/v1`

Redeploy after changing environment variables. Browser requests and session cookies stay on the Vercel origin through the existing API rewrite. Do not set the browser API base to the Render domain. HTTPS proxy configuration is checked at build time on Vercel.

Next configuration now prepares the version-matched module worker independently of package-script overrides. Check `/vendor/maplibre/maplibre-gl-worker.mjs`: it must return 200 and a JavaScript content type. A 404 HTML response means the worker was not packaged into that deployment. The application still uses the real OpenFreeMap style, tiles, fonts and sprites, with provider attribution. External provider/network/WebGL failures remain explicit and retryable.

## Release checks

1. Render `/api/v1/ready` returns 200, `method_mode=model_simulated` and model `reference-sales-sim-v2-438774e0a585`.
2. The same `/api/v1/showcase` through Vercel returns six periods and Current/Opens/Delayed outputs.
3. The map worker returns JavaScript; real street tiles and labels appear. Candidate, branch and competitor records are distinct.
4. With a disposable test account, run analysis, compare two locations, switch periods, save a scenario, request/apply rescue, optimise and download a saved PDF. Sign out/in to check the saved identity.

Official configuration references: [Render Blueprints](https://render.com/docs/blueprint-spec), [persistent disks](https://render.com/docs/disks), [Python versions](https://render.com/docs/python-version), [Vercel external rewrites](https://vercel.com/docs/routing/rewrites).
