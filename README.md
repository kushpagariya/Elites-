# StoreScout

Retail expansion planning: compare network economics, diagnose weak sites and allocate a capital budget. Read [the PRD](docs/PRD.md) for the full product.

## Start here

The `frontend-backend-integration` branch combines the frontend workspace with backend orchestration, atomic SQLite saves, idempotency, evidence and reports. Explore, scenarios/rescue and portfolio/report now connect to the deterministic assumption-based engine. **No trained model is active:** synthetic/assumed results are not empirically validated forecasts and do not pass the PRD's meaningful-AI gate. See [integration status](docs/STATUS.md) for checks and remaining gaps.

1. Read [architecture](docs/ARCHITECTURE.md), [contract](docs/CONTRACT.md), and [four-hour plan](docs/FOUR_HOUR_PLAN.md).
2. Give each owner their prompt: [frontend](docs/handoffs/FRONTEND.md), [logic](docs/handoffs/LOGIC.md), [backend](docs/handoffs/BACKEND.md).
3. Backend owner is also the integration owner. First real merged slice is due at H1; a full connected prototype is due at H4.

Follow the [backend integration workflow](docs/BACKEND_INTEGRATION_WORKFLOW.md). Teammates continue on `frontend` and `ML`; the current combined branch is `frontend-backend-integration`. Main and the teammate branches are preserved.

## Run locally

Use Python 3.12 and Node.js 22 or newer. Run commands from the repository root unless stated otherwise.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
cd frontend
corepack pnpm install
Copy-Item .env.example .env.local
corepack pnpm dev
```

If Corepack is unavailable, use an installed pnpm; `npm install`/`npm run dev` also works, but keep only one lockfile after the team chooses its package manager. On macOS/Linux activate `.venv/bin/activate` and use `python` rather than the Windows executable path.

Open `http://127.0.0.1:3000`; API docs: `http://127.0.0.1:8000/docs`. SQLite defaults to `.runtime/storescout.sqlite3`; no external database is required. Optional server variables: `FRONTEND_ORIGIN`, `STORESCOUT_DB_PATH`, `STORESCOUT_MODEL_DIR`, `STORESCOUT_COMPUTE_TIMEOUT_SECONDS` (default 15, maximum 120). The backend does not automatically load `.env`. Model bundles require `model_card.json` and its artifact within `ml/artifacts/` or the configured directory; see the workflow for fields.

## Check

```powershell
python -m unittest discover -s tests/unit -v
python -m unittest discover -s tests/contract -v
python scripts/export_contract.py
cd frontend
corepack pnpm typecheck
corepack pnpm build
```

Contract checks need backend dependencies installed. `docs/STATUS.md` records actual scaffold checks and remaining gaps. Data in `data/demo/` is synthetic; the infrastructure event is hypothetical. No real forecast accuracy or completed product acceptance is claimed.

## Layout

`frontend/` UI; `backend/app/api/` HTTP boundary; `backend/app/domain/` logic; `backend/app/repositories/` SQLite; `ml/` training/evaluation/artifacts; `data/` fixtures/manifests; `contracts/` generated OpenAPI/examples; `tests/` unit/contract/e2e; `scripts/` checks/export; `demo/` rehearsal assets; `docs/` decisions and handoffs.
