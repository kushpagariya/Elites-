# StoreScout browser application

StoreScout uses one Next.js application: the landing page is at /; the investment workspace is at /app, /app/scenarios and /app/portfolio. Read DESIGN.md here for the workspace and ../DESIGN.md for the original landing identity. The user-provided PRD PDF is the product source of truth; see docs/FRONTEND_HANDOFF.md for its identity and the implemented/blocked requirement map.

## Run

From frontend, with Node 22+: pnpm install, pnpm dev. The app binds to http://127.0.0.1:3000. Copy .env.example to .env.local only when configuring the API URL; the default is http://127.0.0.1:8000/api/v1. Start the backend separately using the repository README.

pnpm build creates the production build; pnpm start serves it. Both dev and build prepare a version-matched local MapLibre worker from the installed package. The map uses the local synthetic boundary and API coordinates; it does not fetch online map tiles. The generated public/vendor/maplibre directory is ignored and recreated by these commands. Keep pnpm-lock.yaml as the only active package lockfile.

## Checks

- pnpm typecheck: routes and strict TypeScript.
- pnpm test: 19 frontend integrity tests using test-only transport payloads; no application fixture mode.
- pnpm test:live: real API smoke check; run only against an isolated local database. Creates labelled Current/Opens/Delayed verification scenarios and confirms reopening, zero budget, unchanged baseline and validation rejection. Current evaluation endpoint is expected to return 501; this check does not establish analytics readiness.
- pnpm build: production compilation.

Exact session commands, environment caveats, screenshots and acceptance gaps are recorded in docs/FRONTEND_HANDOFF.md.

## Structure

- src/app/(marketing): landing route and scoped styling.
- src/app/(workspace): shared provider/shell and three workspace routes.
- src/features/explore: candidate table, two-site comparison, local MapLibre map, ranking/exclusions and DaypartDNA surfaces.
- src/features/scenarios: complete immutable assumption snapshots, infrastructure controls and bounded rescue requests.
- src/features/portfolio: evaluation-bound risk acknowledgements, full-network result rendering and saved-report download/preview.
- src/components: shared shell, error and unavailable feedback.
- src/lib: transport, canonical types, runtime guards, formatting and request identity handling.
- tests: isolated integrity tests and live smoke script.
- scripts/prepare-map.mjs: local worker/NOTICE preparation; no CDN.

A single provider retains the selected project/scenario/evaluation, model and feature identities across routes. Edits and scenario selection abort outstanding work, advance a request token and disable derived actions. Late or malformed responses are discarded. Only a saved scenario ID is kept in localStorage; the actual scenario is always reloaded from the API. Evaluation and portfolio responses are never reconstructed from browser storage.

The backend currently connects demo/scenario/infrastructure requests, while computation returns 501. Financial outputs, ranking and portfolio success rendering use the agreed schemas; no browser finance, fallback predictions or mock judging data exist. Standalone rescue, detailed dayparts, sensitivity/source freshness and advanced assumption edits require agreed response/request extensions before they can complete. Report download requires the matching saved evaluation and portfolio, then reopens the exact downloaded bytes in a sandboxed preview. Its real endpoint remains a backend dependency.

Historical landing evidence is preserved in docs/landing-reference; the former nested app and generated caches were consolidated in the preceding change. The obsolete frontend/Elites app and tracked .next-dev output have been removed from Git. Active landing sources and historical reference assets are preserved under src/features/landing and docs/landing-reference.
