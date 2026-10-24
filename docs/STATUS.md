# StoreScout implementation status

Baseline inspected: frontend branch, commit 7ea235b. The existing landing/workspace, immutable scenarios and finance helper were preserved. The latest request authorizes backend/domain integration as well as frontend work. Final end-to-end acceptance is explicitly deferred.

| Requirement | Initial audit | Current implementation / dependency |
|---|---|---|
| Explore financial comparison | Partial UI; no analytical endpoint | Computed reference/allocation sales, operating profit, branch displacement, NPV/ROI/payback, low/base/high cases and explanations; assumption mode |
| Ranking / exclusions | Missing computation | Saved economic ordering, budget/coverage/calibration/evidence/downside rule reasons; rejected/review sites stay visible |
| Geographic context | Candidate/branch map only | Frozen synthetic POIs and selected geodesic catchments; roads/observed competitors remain a data dependency |
| DaypartDNA | Placeholder | All six canonical bins, category support, duration/decay weighting, reliability/date details, zero vs missing |
| Advanced scenarios | Rent/demand/budget only | Global and site-specific margin/OPEX/competition, immutable snapshots and date validation |
| Infrastructure | Form/event record only | Site exposure, explicit hypothetical dates, Current/Opens/Delayed, calendar-year fractions and single financial bridge |
| FailFast / rescue | Missing | All four classifications; exact bounded rent threshold, bounded sales bisection, numerical monotonicity check and preserved unrelated failures |
| Portfolio | Missing | Full-network subset table + OR-Tools CP-SAT, eligibility/count/budget/acknowledgements/exclusions/empty/partial status; host runtime blocked on pandas DLL |
| Decision report | Missing endpoint | Saved HTML/JSON serialization, matching run checks, assumptions/evidence/methods/identities; completed solver output needed for real download |
| ML | No trained artifact | Explicit versioned assumption estimator; model card has null artifact/metrics. ML promotion remains blocked |
| UI polish / state | Basic working workspace | Compact investment cards/table, business copy, Technical Details disclosure, independent cancellable geography, stale/export/risk gating preserved |

Checks: frontend 23/23 targeted tests; TypeScript and production build passed. Python targeted suite: 18 run, 17 passed, one OR-Tools numerical test skipped after the actual import failure. One-cell independent allocation oracle, finance oracles, branch-loss accounting, overlap, sensitivity, event timing/cancellation, rent and sales rescue, atomic rollback, idempotency, typed query endpoints and report serialization passed. These checks do not constitute final acceptance.

Current host: Python 3.13, FastAPI 0.141.1, Pydantic 2.13.4, NumPy 2.5.2; repository core dependency pins remain unchanged at FastAPI 0.115.14/Pydantic 2.11.7. A clean pinned environment has not been revalidated. OR-Tools 9.14.6206 installed; Windows Application Control blocks pandas 3.0.5 sparse DLL. No security setting was changed. Solver unavailable state is explicit, decision totals hidden and export disabled.

Next dependencies: backend verifies OR-Tools in a permitted clean runtime and restarts the API with a writable SQLite path; frontend restarts its existing server and checks the new contracts; ML supplies an approved artifact/schema/model card and evaluates promotion gates. Real geographic inventories and future-event temporal evidence remain data work. Then schedule final integration/acceptance, which has not been run. See IMPLEMENTATION_REPORT.md for commands and limitations.
