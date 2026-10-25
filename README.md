# StoreScout

Grocery-location planning in Bengaluru with a connected Next.js interface, FastAPI backend and the delivered CatBoost/decision engine. The prototype supports ten candidates, four fictional existing branches and 219 contextual mapped competitor shops. Integrated on `full-integration` from frontend/backend `ff6d2c3` and ML `d7373f8`.

## Run

Use Python 3.12 and Node 22+. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m ml.decision_engine.package --install
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

The installer verifies the supplied archive and restores the selected model without retraining. Startup warms the model before accepting requests. In another terminal:

```powershell
cd frontend
corepack pnpm install --frozen-lockfile
corepack pnpm dev
```

Open [StoreScout](http://127.0.0.1:3000). Create an account or sign in. [API documentation](http://127.0.0.1:8000/docs). For a production frontend, run `corepack pnpm build` then `corepack pnpm start`. The frontend proxies `/api/v1` to port 8000. Set `STORESCOUT_API_ORIGIN` before frontend build/dev for another backend. Backend environment variables must be set explicitly; `.env` is not automatically loaded.

## Saved accounts and work

Passwords use salted scrypt. HttpOnly session cookies expire after seven days and are revoked at sign-out. Accounts live in `.runtime/accounts.sqlite3`; each account has a separate `storescout-bengaluru-<user-id>.sqlite3` workspace. Scenarios, evaluations, frozen network inputs, plans and rescues are saved server-side. The last saved view is restored after sign-in/refresh. Changed sources/model/code mark results stale while preserving saved reports.

Keep the database directory on persistent storage and back it up. Set `STORESCOUT_DB_PATH` to a stable absolute path when moving checkouts or deploying; accounts use the same parent directory. Set `STORESCOUT_SECURE_COOKIES=1` behind HTTPS and configure `FRONTEND_ORIGIN`. Runtime data and credentials stay out of Git. Older Navi Mumbai workspaces use a separate database filename.

## Connected workflow

Explore candidate locations and fictional branches alongside clustered competitor shops, visible before financial analysis. Explicitly compare two candidates, inspect six DaypartDNA periods, test demand/rent and infrastructure, apply verified rescue settings, select a budgeted full-network portfolio after risk review, and download/preview a paginated PDF. Competitors are contextual evidence and cannot enter comparison or portfolio.

Each scenario restores its own saved evaluation and plan. Reset restores saved inputs; repeated unchanged saves preserve valid results. Before/after references persist through navigation, refresh, sign-in and rescue application. New portfolio saves include the exact PDF bytes, evidence and checksum in one transaction; older PDFs do not re-render after software/model updates. Legacy plans freeze their saved evidence when first exported. Historical metadata that was never saved cannot be reconstructed. The landing preview uses the engine and public snapshot without account data.

Supported edits: budget, area-wide demand/rent, location base rent/sales adjustment and infrastructure timing/effect. CSV imports, new projects and additional financial controls remain explicitly deferred. Other shop categories and verified rental listings require separate data/model integrations. Public rollout additionally requires persistent hosting, backups, HTTPS and monitoring; the local prototype does not claim production readiness.

CatBoost is trained on synthetic sales targets. Real-store accuracy is unvalidated. Historical population/spending, assumed business inputs, partial OSM coverage and scenario infrastructure dates remain identified. Outputs and rankings are computed by the delivered engine, never fixture scores.

## Check

```powershell
.\.venv\Scripts\python.exe scripts/check_integration.py
.\.venv\Scripts\python.exe scripts/export_contract.py
cd frontend
corepack pnpm test
corepack pnpm typecheck
corepack pnpm build
```

For live API checks against an isolated local test database, set `STORESCOUT_TEST_API=http://127.0.0.1:8001/api/v1` then run `corepack pnpm test:live`; it creates disposable accounts/scenarios. Historical training audits require their larger original artifact sets; the runtime archive deliberately contains only the selected model.

For rendered desktop/mobile regression, install Playwright as a test tool with Chrome, set `STORESCOUT_UI` to the isolated frontend URL and run `node tests/product-journey.mjs` from `frontend`. Optionally set `STORESCOUT_PLAYWRIGHT` to an existing Playwright module path. This journey uses actual backend data/calculations and a deterministic street-background style; external basemap availability is a separate dependency. Review [product verification](docs/PRODUCT_READINESS_VERIFICATION.md) for exact results and remaining limits.

See [integration workflow](docs/FULL_INTEGRATION.md), [current status](docs/STATUS.md), and the original [ML handoff](ML_FINAL_HANDOFF_REPORT.md).
