# Setup status

## Available in this setup

- Next.js/TypeScript connectivity page and shared typed API client.
- FastAPI health, synthetic project and hypothetical infrastructure reads.
- Immutable scenario create/list using SQLite; baseline unchanged; connections close after each transaction.
- Canonical Pydantic schemas, generated OpenAPI and matching frontend planned types.
- Synthetic seed: 10 sites, four branches, 100 cells, 60 POIs, one event and assumed time weights.
- Real pure-Python NPV/ROI/payback helper; all other analytical modules have explicit unimplemented seams.
- Three owner prompts, architecture, contract, folder ownership and H1/H2/H3/H4 integration gates.

## Checks actually run

- Python 3.12; Node.js 24.22.1.
- Four finance unit checks passed: known NPV, sales/NPV reversal, zero CAPEX/no recovery and invalid values.
- Four API contract checks passed: health/fixture, persistent immutable scenario, explicit 501 analytics and invalid/unknown input.
- Frontend TypeScript check passed; Next.js 16.4.3 production build passed.
- Generated `contracts/openapi.json`. Python resolved dependency lock and pnpm lock are included.

The initial SQLite cleanup test exposed an unclosed connection; repository context management was fixed and all API checks rerun successfully. No model training, model accuracy, numerical network/portfolio result, UI journey acceptance or latency target has been established by these scaffold checks.

## Remaining work and first assignments

1. Logic: real fitted synthetic model -> bounded allocation -> complete finance/site output. Backend: connect evaluation service and atomically save it. Frontend: table/selection and actual API result. Due H1 from team kickoff.
2. Logic/backend: FailFast/rent rescue + recomputed scenario. Frontend: comparison/rescue. Due H2.
3. One infrastructure open/delay bridge, DaypartDNA profile and exact subset portfolio plus saved report. Due H3; integrate and verify by H4.

Until implemented, evaluate, rescue, portfolio, model and feature/daypart/ranking routes return 501; analysis/report reads are also integration work. The current page is a development diagnostic, not the completed product UI.

Next exact action: three owners read their prompts, start from this main commit, run README setup, then agree the minimal shared schema additions in the first 15 minutes. Backend owns further integration. No P1/P2 work starts before the H4 path is connected.
