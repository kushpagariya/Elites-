# StoreScout

Retail location planning with a connected Next.js interface, FastAPI backend and the delivered Bengaluru CatBoost/decision engine. Integrated on `full-integration` from frontend/backend `ff6d2c3` and ML `d7373f8`.

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

Explore ten Bengaluru candidates and four assumed existing branches, compare locations, inspect six DaypartDNA periods, test demand/rent and infrastructure, apply verified rescue settings, select a budgeted full-network portfolio after explicit risk review, and download saved reports. The landing preview uses the live engine and public snapshot, without account data.

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

See [integration workflow](docs/FULL_INTEGRATION.md), [current status](docs/STATUS.md), and the original [ML handoff](ML_FINAL_HANDOFF_REPORT.md).
