# StoreScout frontend implementation handoff

## Scope and source

The implementation follows the user-provided C:/Users/ASUS/Downloads/StoreScout_PRD_Final (1).pdf (16 pages; SHA-256 a16bb42078cbafaaf5855db8b4b1d5227b54e05eef5766b9edd5841048a8c59e), the root design guide, docs/PRD.md, ARCHITECTURE.md, CONTRACT.md, FOUR_HOUR_PLAN.md and the frontend handoff. The PDF supplies product semantics; live OpenAPI and backend/app/schemas.py supply accepted wire shapes. No numerical examples from the PDF were inserted as application output.

Frontend-only implementation plus this handoff. Backend/domain/data/contracts were not edited. Work remains on the existing frontend branch. Pre-existing deletions under frontend/Elites are excluded from this implementation commit. The preceding landing consolidation is included because it provides the active routes and design reference. Current source paths are documented in frontend/README.md.

## Delivered behavior

- /app: real demo project, ten candidates/four branches, source labels, exactly-two comparison, offline MapLibre coordinate map, backend financial/diagnosis rendering, backend ranking/exclusions and explicit missing evidence/sensitivity/dayparts states.
- /app/scenarios: complete copied assumptions, new scenario name/budget, rent/demand multipliers, per-site rent/sales overrides, Current/Opens/Delayed, opening date and 24-month delay, hypothetical event evidence, bounded rescue request controls. A saved SOLVED threshold in the agreed evaluation schema can be applied through a new immutable scenario/evaluation; untyped standalone rescue responses never mutate inputs.
- /app/portfolio: evaluation-bound risk acknowledgements and count cap including zero; renders returned full-network exact/partial/unknown results, selected/excluded sites, budgets and empty sets. Export requires matching saved identities and validates the downloaded content before sandboxed preview. No investment arithmetic is implemented in React.
- One route-persistent provider holds project/scenario/evaluation/model/source context. Edits/selections increment a revision token, abort obsolete requests and mark retained output stale. Runtime guards reject incomplete/nonfinite/mismatched responses. Portfolio/report actions are disabled while stale, missing, loading or superseded. Only a selected scenario ID persists in localStorage; server payloads remain authoritative.

TODO: needs backend — connect saved evaluation/portfolio computation, agree rescue/daypart/evidence schemas and advanced assumptions, and implement saved reports/imports.

## Current integration boundary

| Requirement | Frontend status | Remaining producer dependency |
| --- | --- | --- |
| F01 sales/cash flow/NPV/ROI/payback | Agreed evaluation fields render; null/zero distinct | Evaluation pipeline returns 501 |
| F02 immutable what-if/infrastructure | Real scenario save/list connected, all three states persist | Evaluation propagation; margin/OPEX/competition request extensions; backend date/horizon validation |
| F03 ordering/drivers/exclusions | Renders saved rankings, first three supplied drivers, all diagnoses | Computed evaluation; no separate ranking schema assumed |
| F04 source/method/sensitivity | IDs and method shown; missing dates/support/low/high explicit | Agreed detailed evidence/sensitivity schema |
| F05 branch displacement | Aggregate loss renders from analysis; no frontend allocation | Full-network allocation and branch-level output |
| F06 exact portfolio | Request/result controls connected to defined adapter; zero count supported | Portfolio pipeline returns 501 |
| F07 DaypartDNA | Two named profile surfaces and evaluation-bound request seam | Agreed time-bin/profile/support/date schema and actual computation |
| F08 FailFast/rescue | All status/reasons/threshold fields supported from evaluation; bounded request seam | Rescue returns 501 and lacks agreed success schema |
| Report/export | Matching-ID gating, saved endpoint request and exact-byte preview | Backend saved report route absent; real download/reopen remains unverified |
| Project creation/validated CSV import | Not introduced into the fixed demo path | Backend routes and schemas absent; required P0 acceptance gap remains |

This is not a complete H4 investment demonstration. Real inference, economic reversal, sensitivity, verified rescue, full-network enumeration and saved report acceptance remain blocked. The frontend must be exercised with real successful responses when backend integration lands; test fixtures do not certify them.

## Exact checks

The installed pnpm wrapper uses a bundled Node that failed creating a temporary file (ENOENT). Successful package commands used system Node with the installed pnpm entry point:

node C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.mjs --dir frontend test

node C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.mjs --dir frontend test:live

node C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.mjs --dir frontend typecheck

node C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pnpm/bin/pnpm.mjs --dir frontend build

- Unit/transport integrity: 19 passed, 0 failed. Includes reversed completion, edits during pending requests, missing/nonfinite/mismatched outputs, baseline copy isolation, empty/max-zero portfolios, AT_RISK acknowledgement, rejected/review exclusions, 0 versus null, 501/network/422/abort, incomplete 200 and foreign report identities. Test-only synthetic payloads are isolated under tests/ and never imported by application code.
- Live smoke: passed against the unchanged local backend. GET project returned 10/four SYNTHETIC data; three new Current/Opens/Delayed scenarios saved, including a zero-budget delayed case; GET reopening matched exact saved snapshots; baseline remained unchanged; negative budget returned 422 with no save; evaluation returned explicit 501.
- Backend stop/restart against the same verification DB: all four saved browser/smoke scenarios remained; baseline rent multiplier remained 1. Saved smoke IDs: 59aa257f-3b0a-434c-b7a3-74a991667c67, fa5d2547-d71b-43e9-b874-99ddc25ded78, 173d35a0-1573-4dbf-a885-c50782732777. Browser-created rent review: 70402646-28c3-42c9-b298-b8011eef4f53.
- Browser: two selections enable comparison and disable a third; evaluation 501 is visible; editing marks stale; save then evaluate retains saved scenario on 501; route navigation preserves state; delayed zero-budget scenario reopened after reload with 2028-04-01 and 24 months; portfolio/report remained disabled without evaluation. Keyboard Tab reached the skip link; Enter then Tab reached the saved-scenario selector. Full assistive-technology certification and physical touch testing were not performed.
- Map: initial worker error was found by visually reading full-page captures and the browser console; fixed by scripts/prepare-map.mjs plus explicit local worker URL. Final map captures show API markers and the local boundary. No online basemap or live traffic is claimed. WebGL-failure text leaves the table usable.
- TypeScript: passed. Production build: passed; /, /app, /app/scenarios and /app/portfolio generated.
- Source lint: node C:/Users/ASUS/.agents/skills/design-taste-frontend/scripts/lint.mjs --app frontend/src/components frontend/src/features/explore frontend/src/features/scenarios frontend/src/features/portfolio — 0 FAIL, 0 WARN.
- Responsive checks: node C:/Users/ASUS/.agents/skills/design-taste-frontend/scripts/inspect.mjs --app http://127.0.0.1:3000/app --out frontend/docs/verification/workspace/explore --allow palette-purple,palette-cream; repeated with /app/scenarios and scenarios output, /app/portfolio and portfolio output. Final reports: 0 FAIL, 0 WARN at 1440/768/390 for each screen. All 18 final fold/page captures were opened. Brand palette allowances preserve the supplied design; no other check was waived.

## Verification environment and limits

System Node 24.19.0, pnpm 11.25.0; frontend dependencies locked in pnpm-lock.yaml. Backend verification used installed Python 3.13 and FastAPI 0.141.1, rather than the recommended Python 3.12/locked FastAPI 0.115.14 environment; no locked-backend-environment claim is made. OneDrive prevented SQLite journal creation, so the server used STORESCOUT_DB_PATH=C:/Users/ASUS/AppData/Local/Temp/storescout-frontend-urz3sx6q.sqlite3. This isolates verification scenarios from normal project data. The database is not committed.

Initial test script URL-expression syntax errors were corrected before the final passing run. An initial map worker error and disabled-label contrast warning were fixed. Transient formatter invocations with root-relative globs failed; the package-relative formatting succeeded. The earlier landing-only inspector's design findings are historical and do not apply to the new workspace reports.

No model results, performance benchmarks, optimality claims, user validation or complete PRD acceptance are asserted. Report download/reopen was checked with test-only matching/foreign identity payloads, not a real computed report. Late-response protection has focused unit/transport coverage; actual reversed successful analytical requests await a connected evaluation producer.

## Next integration increment

Backend should connect and atomically persist EvaluationData first, preserving the agreed identities; frontend can immediately render its fields and submit portfolio requests. Agree rescue/daypart/evidence/sensitivity and expanded assumptions before extending their adapters. Then demonstrate the PDF's lower-sales/higher-NPV reversal, apply verified rescue without clearing hard failures, switch infrastructure, enumerate a budget-feasible portfolio and reopen the saved report. Rerun the source/transport/UI checks with those real responses. Do not reinterpret this frontend handoff as full AC01–32 acceptance.

Skills used: Impeccable document/craft-floor/Operate guidance, Emil interaction guidance, Taste Framed sheet direction seed 940076972, and PDF reading for the authoritative source. The Impeccable context loader was unavailable earlier in this chat; existing product/design/contracts were read directly. No subagents or external task messages were used.
