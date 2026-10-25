# Bengaluru grocery prototype journey verification

Work is on `full-integration`, based on `5cbc5c42b6e92aec9962dc2e19b932017f88d1ee`. No commit or push was made for these changes.

## Delivered against the priority list

| Priority | Implementation and evidence |
| --- | --- |
| 1 | Decision PDF with recommendation, selected sites, budget allocation, joint network NPV, financial comparison, NPV chart, risks, assumptions and sources. No raw JSON/code appendix. Final representative document is three A4 pages. |
| 2 | PDF MIME/signature, descriptive .pdf filename, readable INR/percentages and Page X of Y. Preview reopens the same downloaded bytes. New portfolio and PDF/evidence/SHA256 save atomically; existing bytes survive renderer/model/code replacement. |
| 3 | Account-scoped current/per-scenario view pointers restore matching evaluations and portfolios. Edited drafts hide mismatched decision values. Reset/repeated unchanged save preserve valid results. Request tokens continue to reject late responses. |
| 4 | Keyboard-accessible numbered candidate map buttons show annual sales, incremental NPV and risk from the matching saved evaluation. Missing analysis has an explicit Run Analysis action. |
| 5 | All 219 loaded competitor POIs appear before financial analysis; toggle and zoom-dependent clustering. Counts come from loaded records. Candidate cap remains ten. |
| 6 | Candidate, fictional branch and competitor markers/legend differ. Competitor popups show available name/category/source and explain unavailable financial observations. Branch popups identify fictional records. |
| 7 | Explicit two-candidate selectors plus map/card selection share one saved selection. Comparison cards/table use one evaluation. Competitors cannot enter comparison or portfolio. |
| 8 | Scenario naming is in the main form, capped at 100 characters, with no automatic revised suffix. Area-wide and individual controls have distinct labels/semantics. |
| 9 | Before/after scenario/evaluation references are server saved, validated and restored. Sales, NPV, effective rent and viability use their corresponding saved snapshots, including rescue-created scenarios. |
| 10 | Infrastructure state changes do not substitute a default for intentional zero effect. Reset restores selected saved values. Location overrides identify inherited versus overridden values; blank is inheritance. |
| 11 | Both assumed and effective delayed opening dates, representative OSM geometry note and official evidence link are disclosed. Dates/effects are assumptions rather than measured commercial uplift. |
| 12 | Rescue shows current settings, canonical proposed setting, verification NPV and remaining risks. Maximum affordable rent need not be below current rent; minimum required sales need not exceed current sales. Applying explicitly creates a new what-if scenario. |
| 13 | Annual sales/operating profit, horizon ROI and incremental NPV are separately labelled. Single-location estimates are distinguished from joint portfolio results; network totals come from the domain optimiser. |
| 14 | Bengaluru/grocery onboarding, workspace, README, architecture and current PRD scope agree. Imports/new projects/additional financial controls are explicitly deferred rather than presented as delivered. |
| 15 | API, adapter, rendered component and real Chrome desktop/mobile regression cover the named journeys. Rendered PDF pages are also inspected. Results below distinguish these checks. |

## Actual checks

- **87/87 Python tests passed**: original finance/domain/rescue checks, auth and integration contracts, and four new product-journey tests. The full run completed in 75.638 seconds. After the final PDF layout change, the four new tests passed again in 14.375 seconds.
- **31/31 frontend behavior tests passed**, including PDF identity/integrity rejection, unchanged drafts/zero overrides, and existing stale-response, financial guard and unavailable-state coverage.
- **TypeScript and production Next.js build passed.** All seven static routes generated successfully.
- **11/11 real Chrome journey checkpoints passed**: competitor visibility before analysis; map click to matching metrics; two-site comparison; reset/zero effect; repeated save and refresh; saved scenario switching; portfolio/PDF preview; mobile Explore; mobile Portfolio; sign-in restoration; rescue application and refreshed before/after references.
- Existing **live-adapter smoke passed** for Current/Opens/Delayed, model_simulated inference, geography/dayparts, verified rescue application, exact portfolio, PDF, invalid budget, baseline immutability and sign-in restoration.
- Final representative PDF rendered to **three PNG pages**, visually inspected for readable tables, chart labels, currency/percentages, footers and pagination. Page text had no out-of-page bounding boxes in the inspected render. Text extraction alone was not the acceptance check.
- Generated OpenAPI updated with coordinated Python/TypeScript changes; `git diff --check` passed.

Commands from repo root:

```powershell
.\.venv\Scripts\python.exe scripts/check_integration.py
.\.venv\Scripts\python.exe scripts/export_contract.py
cd frontend
corepack pnpm test
corepack pnpm typecheck
corepack pnpm build
# Against separately started isolated API/frontend:
$env:STORESCOUT_TEST_API='http://127.0.0.1:8011/api/v1'
node tests/live-smoke.mjs
$env:STORESCOUT_UI='http://127.0.0.1:3011'
node tests/product-journey.mjs
```

Browser artifacts and temporary accounts/results are under ignored `.runtime/product-readiness/`, separate from source data and original ML evidence. Backend test accounts use temporary databases. Local socket access was required for Windows TestClient and Chrome; the sandbox-only attempt stalled before reaching application logic. The test environment used the branch's pinned FastAPI/Starlette/Pydantic API versions. A joblib/NumPy deprecation warning remains; inference completed successfully.

## Limits retained

Chrome checks used the real MapLibre renderer and actual saved backend data/model calculations with a deterministic background style. They do not certify the availability of external OpenFreeMap tiles/fonts or every browser/device. Mobile layout checks used 390x844, plus desktop 1440x1000. Authentication/account-isolation checks establish the tested local boundaries, not a public security audit.

Historical stage-specific training/stub tests were not reclassified or retrained. This is not a claim that every historical repository test passes. Model-realism, shifted-market, source/price-year, opening-hours/Daypart explanation and strict optimiser deadline limitations in the ML handoff remain. The active model is unchanged: `reference-sales-sim-v2-438774e0a585`, CatBoost SHA256 `438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998`, mode `model_simulated`. Real-world sales accuracy is unvalidated. Dataset/model/domain files were not modified.

New PDFs are frozen when portfolios are saved. Legacy portfolios freeze on first PDF export using their existing saved evidence; metadata never recorded historically cannot be recovered. Saved historical analyses/PDFs remain reviewable even when computation is stale; new rescue/portfolio calculation still requires a current supported evaluation.

Public hosting/persistent volumes, backup/restore operations, HTTPS, monitoring, email recovery/verification, new categories, verified rental data and empirical outcome validation remain separate rollout work. CSV/project import and extra financial controls remain unmet full-PRD requirements, explicitly deferred for this prototype.
