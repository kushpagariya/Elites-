# Backend integration status

Branch: backend-integration. Starting scaffold: 569f4f52f459ed09129c04a17ac97485601d7bb7.

## Implemented

- API index, health, project and hypothetical infrastructure/source snapshot reads.
- Immutable scenario create/list/read, ISO date validation and ordered rescue bounds.
- Evaluation service loading frozen sources, actual model/card hashes and domain source identity.
- Strict complete-result validation, candidate coverage/ranking/source checks.
- Atomic SQLite public result + private frozen context + cache/idempotency saves.
- Deduplication, conflicting idempotency keys and concurrent publication handling.
- Saved evaluation/site/ranking/portfolio/rescue reads.
- Portfolio orchestration with saved scenario budget; independent CAPEX/count/eligibility/risk checks.
- Rescue orchestration and persisted proposals; applying a proposal still requires a new scenario.
- Escaped printable HTML/JSON report preserving saved identities, assumptions and provenance.
- Bounded analytical worker slots, timeout handling and no late result publication.
- Typed frontend transport helpers and updated shared types/OpenAPI.
- Complete implementation/integration order in BACKEND_INTEGRATION_WORKFLOW.md.

## Checks actually completed

- 19 API/repository contract tests passed, including rollback, concurrent cache publication, idempotency conflict, stale model/engine, invalid analytical output, budget/risk checks, rescue proposal immutability, report escaping/mismatched run and timeout behavior.
- Four finance oracle unit tests passed.
- Frontend route type generation and TypeScript no-emit check passed.
- Next.js 16.4.3 default production build passed from this checkout.
- OpenAPI regenerated; git diff whitespace check passed.
- Live HTTP smoke check: API index/health/project/source reads 200; exactly ten candidates/four branches; model 503 MODEL_UNAVAILABLE; evaluation 503 ENGINE_UNAVAILABLE. OpenAPI has 18 paths.
- Local backend started on 127.0.0.1:8000 with backend source reload enabled.

Contract tests explicitly inject TEST-ONLY engines and an invalid-as-a-model test artifact. They establish transport/persistence behavior, not trained inference, network correctness, portfolio optimality, forecast accuracy or complete PRD acceptance.

The first production-build attempt reused dependencies through an external junction, which Turbopack rejected. Replaced that temporary link with a normal locked install; the default production build then passed. No product configuration workaround was committed.

## Current teammate heads inspected

- origin/frontend: e56dd84621ba63885f7506a3d399c7e6d1e0543b, Landing Page.
- origin/ML: 569f4f52f459ed09129c04a17ac97485601d7bb7, original scaffold.
- origin/backend and origin/main: original scaffold.

There were no newer teammate commits at the last fetch. The existing frontend marketing app is still nested under frontend/Elites/storescout and /app is a placeholder. Its illustrative local calculations have not been promoted into analytical results. Do not merge generated .next-dev output or declare this landing page a connected workspace.

## Remaining integration dependencies

1. ML: implement domain.pipeline.run_evaluation and supply actual fitted bundle/model card. Include JSON _context for frozen network persistence. Existing domain functions are still stubs; backend execution honestly returns 503.
2. ML: implement full-network run_portfolio and proposed run_rescue seam against saved context. Numerical invariants remain ML-owned.
3. Backend + ML + frontend: freeze additive sensitivity, detailed evidence, DaypartDNA and infrastructure result DTOs. Current daypart endpoint intentionally returns 503; raw source weights are not computed opportunity.
4. Frontend: consolidate one application root; connect workspace to typed helpers; verify annual INR/decimal horizon ROI, six time bins, 24-month delay and evaluation identity.
5. Integration: merge compatible new branch commits, run relevant checks and then the real end-to-end investment journey. Preserve the last verified state if a merge fails.
6. Complete-PRD follow-up: coordinated margin/OPEX/competition controls, project creation/import validation and remaining AC01-32. These are not claimed complete by the H4 infrastructure increment.

A recurring check for new frontend/ML/backend commits is configured every ten minutes. It should stay quiet for unchanged heads, preserve uncommitted work, integrate only verified updates onto backend-integration, and notify on meaningful integration outcomes or blockers. It cannot guarantee a complete analytical prototype before the required teammate code arrives.

## Immediate integration agreement

Read CONTRACT.md and BACKEND_INTEGRATION_WORKFLOW.md before changing the seam. Backend adds all public identities; domain supplies computed values only. Do not reconstruct full-network state from public rounded site cards. Do not silently mix changed engine/model implementations with a saved evaluation. Reports always read saved results.

No main promotion, full UI journey rehearsal, actual model inference, model benchmark, infrastructure activation calculation, DaypartDNA numerical check or full-network optimality proof has been completed in this increment.
