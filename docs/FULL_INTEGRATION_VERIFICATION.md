# Integration verification

Verified on 2026-10-25 using Python 3.12 and Node 24.22.1. Branch baselines: frontend/backend `ff6d2c3`, ML `d7373f8`.

## Checks

- `python scripts/check_integration.py`: **83 passed**. Finance, delivered engine/rescue behavior, real-model API integration, account isolation, persistence, cache/idempotency, stale inputs, atomic saves, failure handling, public-preview provenance and artifact-tampering rejection.
- `pnpm test`: **30 passed**. Runtime response validation, request-order protection, empty/error states, controls, charts, navigation, rescue validation and report identity.
- Production build and TypeScript passed; OpenAPI regenerated.
- Live frontend adapters passed current/open/delayed scenarios, six dayparts, geography, canonical rent rescue/apply, portfolio and saved report, invalid budget rejection, repeated preference updates, logout/login and restored workspace IDs.
- Numerical engine, inference code, training inputs and Bengaluru data compare unchanged against `origin/ML`. Baseline financial values/rankings match exactly. The selected artifact retains SHA-256 `438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998`.

## Browser acceptance

The production build was exercised through the real interface: register; evaluate; compare two locations; inspect six dayparts and cash-flow charts; save an opening scenario; calculate and apply a verified rescue to a new scenario; acknowledge two locations; optimise; download the matching report; sign out; sign back in; restore the same scenario, analysis, risk choices and portfolio. Backend restart preserved the session and saved records. Code/source freshness changes correctly marked older results stale.

The landing preview loaded computed model output. Current/open/delayed buttons displayed distinct backend values, including exact NPV changes. MapLibre basemap, supplied locations, POIs, catchments and competitor controls are connected. Concept artwork/film remains identified as illustration.

Desktop and 390px mobile views were inspected. The measured mobile document width matched its viewport, with no horizontal page overflow. Existing cream/forest/terracotta styling, motion controls and reduced-motion behavior were retained. This is an emulated mobile check, not a physical-device certification.

## Local timings

Warm local server, three distinct scenarios, including HTTP, numerical computation and SQLite save:

- Fresh evaluation: 1.577–1.859 seconds; median 1.658 seconds.
- Cached evaluation: 0.299 seconds.
- Portfolio selection: 0.789 seconds.

These are local observations, not production load-test guarantees. Startup warms the model before accepting requests.

## Data scope

The delivered model uses synthetic sales labels; real-store accuracy and calibrated intervals are unvalidated. Historical population/spending, assumed business economics, partial mapped coverage and infrastructure timing/geometry proxies remain visible. Risk acknowledgement does not confer automatic investment approval. The active portfolio implementation uses exact capped enumeration and deterministic stress cases; it does not claim Monte Carlo/SALib/OR-Tools integrations that the supplied runtime does not implement.

Accounts and saved work use local SQLite on persistent disk. Existing workspace files are left in place during preview cutover; account storage uses persistent workspace disk and Bengaluru workspaces use a separate filename from older Navi Mumbai records. No accounts, credentials, test databases or runtime artifacts are committed. Historical model-development audits remain unchanged and require their full original training artifact sets.
