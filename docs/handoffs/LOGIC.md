# Prompt for the logic and ML person

Build StoreScout's deterministic decision engine from `docs/PRD.md`,
`docs/CONTRACT.md` and `docs/FOUR_HOUR_PLAN.md`. Deliver a working vertical
prototype by H4, then finish every F01-F08/AC01-32 requirement within the full
36-hour scope. A starter folder or passing finance oracle does not imply a
working evaluation pipeline.

## Ownership and integration

Own `backend/app/domain/**`, `ml/**` and `tests/unit/**`. Coordinate shared
fixtures with the backend person. Do not edit UI, API routes, persistence,
`backend/app/schemas.py`, `backend/app/services.py` or canonical demo JSON without
agreement. Backend owns validation, IDs, versioning and storage; you own all
computed economics. Import canonical public models from `backend.app.schemas` at
the serialization boundary; propose missing fields before either teammate builds
against an alternative. Public field names, units, enums and null semantics come
from CONTRACT and schemas, never an independent response shape.

Implement `run_evaluation(project: dict, scenario: dict) -> dict` and
`run_portfolio(project: dict, evaluation: dict, max_stores: int,
acknowledged_risk_site_ids: list[str]) -> dict` in `domain/pipeline.py`. Backend
passes frozen JSON snapshots. Read canonical `data/demo/{project,cells,pois,
infrastructure,weights,source_manifest}.json` through its loader. Return computed
fields without an envelope: evaluation returns `method_mode`, `site_analyses`,
`rankings`, `model_artifact_id`; each site matches `SiteAnalysis` and maps the
finance helper's `horizon_roi` to `roi_fraction`. Backend supplies identity/time
fields, validates `EvaluationData` and persists. Portfolio returns
`selected_site_ids`, `budget_used_inr`, `budget_unused_inr`,
`full_network_npv_inr`, `status`, `evaluated_subsets`, `total_subsets`; backend
adds identities and validates `PortfolioResult`. Its input is an internal
evaluation context: saved public evaluation, original Scenario and frozen
network/wallets loaded by backend. Preserve that context outside public schema;
singleton analyses cannot reproduce portfolio interactions. Return a useful
failure when required context is missing. Preserve explicit
`NotImplementedError` until real implementation exists. No FastAPI, database,
network calls or random values inside domain evaluation. Consume a saved seed
for offline simulation; identical versioned inputs must reproduce outputs.

## H0-H4 execution

- H0-H0.5: agree contracts and sample request/response; run the supplied finance
  oracle; load ten candidates, four branches, bounded geographic cells and one
  hypothetical event. Mark synthetic business records and assumed parameters.
- H0.5-H1.5: generate training markets, fit a regularised linear model, save its
  artifact/hash and grouped evaluation; implement distances and bounded network.
  CatBoost is the next comparison, not a reason to miss actual local inference.
- H1.5-H2.5: connect inference, attraction calibration, network allocation,
  cashflows, downside, status and ranking; deliver the first complete evaluation
  to backend. Exercise the higher-sales/lower-NPV reversal.
- H2.5-H3.5: add immutable rent/demand changes, verified rent rescue,
  Current/Opens/Delayed and exact subset optimisation. Reuse frozen matrices.
- H3.5-H4: integrate all three UI screens, frozen report and local trained model;
  rehearse saved baseline -> comparison -> scenario/rescue -> portfolio/export.
  Record incomplete gates honestly. H4 is a prototype checkpoint, not proof that
  all acceptance checks or empirical retail validation are complete.

## Numerical implementation

Separate modules already exist for geospatial, demand, network, finance,
failfast, scenario, ranking, portfolio and evidence. Start with at most 2,000
cells; reduce resolution through a recorded fixture version if runtime demands.
Use WGS84 inputs and metric/geodesic distances. Distances in degrees are invalid.

Predict competitors-only reference annual sales. Inputs include households,
spending, external competition, access, area and baseline POI/daypart descriptors.
Exclude own-branch proximity/coverage, site IDs, desired rankings and post-opening
outcomes. Own-company effects enter network allocation exactly once.

For each candidate alone, calibrate theta against competitors plus outside only:
`A(g,s)=exp(theta_s)*(area_s/100)^gamma*exp(-distance_m/tau)`, gamma 1, tau 750 m,
outside 1 as disclosed defaults. Bisection uses bounded expansion in [-30,30],
100 iterations and INR 1 revenue tolerance. Compare requested/achieved target;
unattainable wallet targets require review. Existing branches use saved assumed
theta and jointly generated baseline sales. Never independently calibrate each
branch as though it owned the whole network.

For every scenario/year, freeze calibrated attractions before testing subsets.
Shares equal attraction divided by outside plus all external and company
attractions; allocated revenue is the sum of cell wallet times share. Shares
including outside conserve one within 1e-6. Compare the same baseline to the
selected set with identical cell wallets and competitor assumptions. Deduct lost
existing contribution once: sum of baseline-minus-after branch revenue times
that branch's variable contribution margin. Never add model sales to allocated
sales or deduct displaced sales a second time.

Compute new-store gross profit from revenue times gross margin; subtract twelve
monthly rents and annual OPEX excluding rent/COGS. Network cashflow subtracts
lost branch contribution. NPV subtracts initial CAPEX and discounts yearly
cashflows; ROI is `(sum(cashflows)-CAPEX)/CAPEX`, null at zero CAPEX. Simple
payback interpolates first cumulative recovery; null means unrecovered.
`finance/cashflows.py` supplies this real building block. Low sensitivity uses
-20% cell spending/+10% rent; high +20% spending/base rent. Reallocate for demand
changes. Rent-only changes may reuse allocation.

## Differentiators and portfolio

Implement all six Asia/Kolkata DaypartDNA bins and category/duration weights in
the PRD. Raw opportunity uses category weight, distance decay, availability and
evidence weight. Shares normalise supported nonzero raw values; unknown differs
from supported zero. This is a POI proxy, never measured footfall.

Use the single infrastructure bridge:
`target_y=baseline_target*(1+exposure*assumed_effect*active_fraction_y)`.
Apply once per year; recalibrate then freeze. Current includes operational
assets; Opens uses explicit completion; Delayed adds 24 months; cancelled never
activates. Opening midyear uses the active fraction from the valuation date.
Do not rerun model features with the same uplift. Unknown dates/geometry need
explicit hypothetical assumptions or review. Permit zero/negative effects while
keeping target nonnegative.

Record every rule. Display precedence: hard REJECTED, REVIEW_REQUIRED, economic
REJECTED, AT_RISK, VIABLE. Respect acknowledged risk and budget. Rent threshold
equals zero-rent NPV divided by twelve discounted yearly factors; verify either
side in the same engine. Negative zero-rent NPV is no feasible rent rescue.
Sales rescue rescales reference target and reallocates within 0.5-3.0; check
monotonicity. Report NON_MONOTONIC or NOT_RECOVERABLE_WITHIN_BOUNDS explicitly.
Rescue never clears unrelated hard failures.

Rank by NPV descending, lower CAPEX, stable ID. Enumerate at most 1,024 sets;
recompute full-network value, never sum singleton NPVs or pairwise penalties.
Use integer paise for budget/CAPEX feasibility. Include empty zero. Ties prefer
lower CAPEX, fewer stores, sorted IDs. Five-second deadline returns
FULL_NETWORK_EXACT only when complete; otherwise FEASIBLE_PARTIAL/UNKNOWN,
evaluated/total counts and unknown gap. Recheck incumbent eligibility and budget.

## Evidence and handoff

Follow `ml/README.md`: >=2,000 examples, grouped 60/20/20 split, 20 separate OOD
markets, median/linear/CatBoost metrics, >=10% relative test-WAPE gain gate,
DaypartDNA ablation, held-out perturbation and artifact hash. Synthetic evidence
supports `model_simulated` only. Missing/unqualified model remains visible.

Run the INR 137,236.03 NPV/50% ROI/3.3333-year oracle, worked-site reversal,
wallet conservation, overlap, zero budget, event-year fractions, rescue sides
and forced cutoff. Preserve source/method/version labels and return actual
computed drivers. Hand backend reproducible commands, measured outputs,
unsupported inputs and remaining AC gaps; never replace missing logic with
prewritten showcase results.
