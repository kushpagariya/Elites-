# Frontend implementation prompt

Copy this prompt to the frontend teammate or coding agent.

You own StoreScout's browser application. Read `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/CONTRACT.md` and the four-hour plan before changing code. Deliver the smallest connected prototype demonstrating the PRD's investment journey in four hours. The current screen is a connectivity diagnostic; analytical capabilities still require implementation. The four-hour demonstration is an integration checkpoint, not evidence that all PRD acceptance criteria or research targets passed.

## Ownership and startup

Own `frontend/**` and this handoff. Put routes in `frontend/src/app/`, reusable controls in `src/components/`, Explore components in `src/features/explore/`, scenario/rescue components in `src/features/scenarios/`, portfolio/report components in `src/features/portfolio/`, and transport/types in `src/lib/`. Coordinate changes to the API contract with the backend teammate. Backend owns HTTP, persistence, validation and export; logic owns predictions, finance, allocation, ranking, rescue and optimisation. Never duplicate those calculations in the browser. Format backend amounts and render backend explanations; totals used for investment decisions come from the saved evaluation.

From the repository root:

```powershell
Copy-Item frontend/.env.example frontend/.env.local
Set-Location frontend
pnpm install
pnpm dev
```

Use Node 22 or newer; the UI is at `http://127.0.0.1:3000`. `NEXT_PUBLIC_API_BASE_URL` defaults to `http://127.0.0.1:8000/api/v1`. Keep a single package-manager lockfile after the first successful install. Before handoff run `pnpm typecheck` and `pnpm build`. Record actual failures rather than claiming a successful build.

## Three screens and the complete journey

**Explore & Compare:** Load `GET /projects/demo`; show Navi Mumbai, grocery, ten candidate sites and four branches from the response. Use a candidate table immediately, then a local GeoJSON map with MapLibre if time permits. The table remains an equivalent keyboard-accessible decision surface. Show selected scenario, sources and REAL/SYNTHETIC/ASSUMED labels. Select exactly two sites to compare modelled annual sales, CAPEX, rent, branch contribution lost, incremental NPV, ROI, payback, low/base/high sensitivity, diagnosis, evidence and three computed drivers. Display rejected/review-required candidates alongside the ranked list. Provide weekday-lunch and weekend-evening DaypartDNA comparisons as POI-derived opportunity, with support and date details. Zero opportunity and missing evidence are different states.

**Scenario & Rescue:** Expose rent and demand changes first; extend the same form to margin, operating cost, competition and budget. Save a new immutable scenario before evaluating. Add Current, Opens and Delayed infrastructure states, including the 24-month delay control and hypothetical-event label. Show all rule failures and VIABLE / AT_RISK / REJECTED / REVIEW_REQUIRED as text. Request maximum viable rent or minimum sales multiplier from the rescue endpoint. Display bounds, verified threshold, and explicit no-solution/non-monotonic results. Applying rescue creates and evaluates a scenario; it never clears unrelated failures in the UI.

**Portfolio & Report:** Submit the active evaluation, store-count cap and explicit acknowledgement of each AT_RISK site. Show selected sites, full-network NPV, CAPEX/budget, exclusions, evaluated-subset count and exact/partial/unknown status. An empty portfolio is a supported result. Enable report download only for a completed saved evaluation and a matching saved portfolio run. Reopen the downloaded report to confirm evidence labels and identities survive.

## API integration and consistency

Use `src/lib/api.ts`; its two implemented methods check health and load the labelled demo fixture. An HTTP 501 means the capability is pending. Handle network, validation and server errors separately with retry; never fabricate financial results. `src/lib/types.ts` mirrors planned schemas in `backend/app/schemas.py`: evaluations contain `site_analyses`, ROI is `roi_fraction`, and `model_artifact_id` may be null. Read backend OpenAPI at `http://127.0.0.1:8000/openapi.json` and update typed adapters when schemas change. The labelled development inputs live under `data/demo/`; `public/demo-boundary.geojson` is explicitly synthetic. Default judging flow uses backend responses; remove frontend fixture mode from the final demo path.

Keep one active context containing project/scenario/evaluation, source snapshot and model identities. A new edit marks derived output stale and disables export/portfolio actions until the matching completed evaluation arrives. Abort superseded requests and also check an incrementing request token before committing state. A late response must never overwrite the current scenario. Display versions in the evidence/details surface when useful; avoid release-version badges. Preserve last successful values during refresh with a clear stale notice. Never mix an old ranking with a new map or report.

## Four-hour checkpoints

- **0–1 hour:** Confirm setup, fetch the backend demo, build navigation/table/selection and all loading/error/empty states. Agree analytical payloads with backend and logic. Establish the active evaluation context. Demonstrate a real API request before adding visual polish.
- **1–2 hours:** Integrate evaluate, site analysis and ranking as backend endpoints become available. Render two-site comparison and the economic reversal. Save a rent-edit scenario and show its recomputed result. Report blockers immediately; do not hide 501 responses.
- **2–3 hours:** Connect rescue and all three infrastructure states, then daypart/evidence/sensitivity panels and remaining assumption fields. Confirm every derived panel shares the active evaluation.
- **3–4 hours:** Connect portfolio/report, verify empty budget and risk acknowledgement, exercise rapid scenario switching, restart/reopen, keyboard flow and one backend failure. Rehearse the complete three-screen journey with the team. Cut animation, optional map layers and extra page layouts before cutting required outcomes.

Use restrained light styling, visible focus, labelled units, readable text and responsive layouts. INR belongs in labels; fractions become percentages only at presentation. Null means unknown/not applicable with its reason; null is never zero. Do not claim calibrated prediction intervals, real footfall, user validation or measured speed without evidence. Finish with the changed files, exact commands run, remaining acceptance gaps and one known-good commit for the integrator.

## Implementation handoff

The browser workspace now has /app, /app/scenarios and /app/portfolio with shared scenario/evaluation context, real demo/scenario requests and explicit unavailable computation. See ../../frontend/docs/FRONTEND_HANDOFF.md for the changed-file map, exact checks, PDF source identity, real API verification and remaining backend/contract dependencies. The authoritative user-supplied PDF confirms the three-screen investment flow; wire fields continue to follow backend schemas. The complete H4 analytical journey remains blocked by the unconnected computation and report endpoints.
