# Analytical engine handoff

This is the completed **offline numerical path**, using the actual selected B.2
CatBoost artifact. It is not an API/UI release or empirical business forecast.
All original Bengaluru tables and historical experiments remain unchanged.

## Run from the repository root

Python 3.12 was used. Install `backend/requirements-lock.txt` for the canonical
schemas/API checks, and `ml/training/reference_sales_v2/requirements-lock.txt`
for the frozen model dependencies. In PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -m ml.decision_engine.package --install
python -m ml.decision_engine.run
python -m ml.decision_engine.verify
python -m ml.decision_engine.report
```

The bundle restores five exact, hashed selected-model files into the ignored
`ml/artifacts/reference_sales_v2/` directory. It refuses to replace differing
files. The bundle contains fitted artifacts and a model card, not raw external
workbooks. It provides the selected inference path; reproducing all historical
training experiments also requires those experiments' separate preserved inputs
and artifacts. Never load an untrusted joblib/pickle file.

## Integration boundary

`backend.app.domain.pipeline` exports:

- `prepare_evaluation(project, scenario) -> {evaluation, context, diagnostics}`.
  Backend loads sources and genuine saved-model predictions into the internal
  `project['inputs']` mapping. `ml.decision_engine.run.build_project()` is the
  concrete Bengaluru loader example, with explicit source/column mappings.
- `run_evaluation(project, scenario) -> evaluation` retains the canonical seam.
  Use `prepare_evaluation` for a persisted flow so the private context is saved
  **atomically with** public computed fields. Backend adds identities/time and
  validates `EvaluationData`; diagnostic/context fields are not public-schema
  additions.
- `run_portfolio(project, context, max_stores, acknowledged_risk_site_ids)`
  returns canonical computed `PortfolioResult` fields. It verifies the exact
  project, scenario and frozen-network digest before any search. Acknowledgements
  refer only to AT_RISK sites in that context. Backend must additionally bind
  request/evaluation identity and independently recheck eligibility/budget.
- `calculate_rescue(project, context, site_id, lever, ...)` returns private
  numerical evidence for the backend-owned rescue response. It never changes the
  scenario or clears unrelated failures. Apply a chosen rescue through a new
  scenario, then evaluate again.

Numerical evaluation performs no disk/network/SQLite operations and generates
no IDs, times or random values. Inputs must have typed nonnegative INR values,
WGS84 coordinates, unique IDs, source IDs, valuation date, weights, saved-model
prediction records, explicit competitors and positive outside mass. Unsupported
predictions raise `DomainUnavailable`, not an invented zero-sales estimate.
Empty candidate projects are unsupported. No fallback target formula claims ML.

## Implemented semantics

Geodesic distances; six Asia/Kolkata dayparts with weekly hours
`[25,20,25,50,24,24]`; null unknown versus supported zero; explicit availability
and evidence weights; standalone competitor-only calibration in `[-30,30]`;
0.01 INR target tolerance/100 iterations; joint baseline/after spending shares;
lost branch variable contribution deducted once; five-year economics and
nonprobabilistic low/base/high stress; full rule precedence; verified rent and
sampled-monotonic sales rescue; one dated infrastructure bridge; NPV ranking;
full-network subset enumeration with paise budgets and a five-second search
deadline. Budget/count-pruned subsets count as examined without an objective
calculation. A deadline is checked between subsets (a single in-flight numerical
evaluation is not preempted). Partial search returns a feasible incumbent with
unknown optimality gap; the schema exposes no numerical gap field.

Unattainable calibration keeps requested and achieved targets and assigns
REVIEW_REQUIRED; those sites cannot enter a portfolio. Raw model estimates and
warnings are retained in prepared inputs. Rent thresholds above requested bounds
are explicitly marked; an already viable current rent is not described as a
failed recovery. Sales rescue samples 17 points, checks cumulative decreases
above INR1, and verifies a feasible-side root within INR1. This sampled check is
not a proof of global monotonicity.

## What the saved demonstration means

The 100-cell allocation uses actual source cell **centroids**, all 219 mapped
external grocery POIs with assumed equal mass, and four fictional branches.
Candidate floor areas, rents, margins, CAPEX and OPEX remain synthetic/assumed.
WorldPop is a historical 2020 model, HCES a 2023-24 state-urban spending proxy;
the nominal wallet/cost price-period mismatch is retained and flagged. No
households, routing or sales labels are fabricated. Whole-AOI allocation differs
from the 1500m circular feature wallet; calibration reports the exact bounded
reference result. No real-store accuracy, calibrated intervals, measured
footfall or investment lift is claimed.

All ten candidates retain AT_RISK evidence warnings. The **default** portfolio
contains no unacknowledged risky sites. A separately named illustrative
acknowledged-risk policy exercises the search; it is not human approval.
The three infrastructure states use a separately flagged hypothetical point,
2028-04-01 opening and +15% assumed effect; operational Yellow Line data is not
falsely treated as a future opening. Daypart recomputation uses geodesic
distances, while legacy features used projected geometry; small proxy differences
are reported rather than overwriting or re-inferring the frozen model features.

## Remaining integration and release work

API routes still return their truthful 501 states. Backend must load the
prepared snapshots, connect these seams, atomically persist result/context,
serve dayparts/model/rescue/report fields under agreed schemas, and regenerate
OpenAPI/TypeScript together if extending them. The existing Navi Mumbai demo
lacks the required fitted-feature context; this loader prepares Bengaluru and
does not silently impute Navi Mumbai population/features. Frontend must consume
the saved evaluation/scenario identities and replace its scaffold. No owner
files or shared schemas were edited for this handoff.

Full PRD acceptance remains open for imports, stale response/atomic-failure
integration, UI accessibility, three rehearsals, clean-checkout full application
startup, 30-run latency percentiles, five-user comprehension and independent
100-market decision-regret evaluation (K09). New stage tests do not reclassify
historical stage-specific preservation/stub tests as current release gates.
The root completion report records actual results and exact paths. Review the
existing source presentation report and licensing/distribution notes before a
public data upload; source permission gaps have not been resolved here.
