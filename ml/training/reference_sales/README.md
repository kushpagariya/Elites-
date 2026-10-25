# Part B reference-sales model

This is an offline, controlled synthetic training experiment and a local Python inference adapter. It estimates competitors-only reference annual store sales before displacement from our own branches. It is not achieved store sales, footfall, net profit, NPV or a ranking. All fitted inference uses `method_mode="model_simulated"`. An explicitly requested fallback uses `scenario_assumptions`.

The ten Bengaluru candidates are read-only inference examples. Neither those rows nor hypothetical sales labels for them enter training/validation/test. The simulator does not load any Bengaluru table. The existing public schemas, application pipeline stubs, fixtures, source data and Part A audits remain unchanged.

## Reproduce locally

From the repository root, using Python 3.12.10:

```powershell
python -m pip install -r ml/training/reference_sales/requirements-lock.txt
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -m ml.training.reference_sales.train
python -m ml.training.reference_sales.report
```

The first command is needed only to provision dependencies. Training/inference require no network. `report` runs the actual unit/integration suite, exports its results, writes the model card and root `PART_B_COMPLETION_REPORT.md`, and calculates output checksums. The frozen input inventory is `ml/evaluation/reference_sales_v1/preserved_input_hashes.json`; both commands verify it and the original ML branch/HEAD. Reproduction replaces only Part B outputs. It must not overwrite Part A snapshots or silently recapture the protected-file inventory.

Generator seed: **20261024**; market split seed: **314159**; fitted model seed: **271828**. Configuration and all numerical bounds are in `config.json`. Exact executed library versions are pinned in `requirements-lock.txt` and recorded in the artifact manifest. Determinism means identical generated CSVs/splits and fitted predictions under these versions/seeds. Runtime timestamps, latency and serialized-library metadata may vary; byte-identical model archives across retraining/platforms are not promised. The report test reruns the entire generator and verifies the CSV hashes, then refits Ridge on the training partition and verifies predictions.

## Simulator assumptions and physical target

Each of 100 independent synthetic markets has 100 spending cells, synthetic external competitors/POIs and 20 alternative potential sites. Twenty additional markets change population, spending, competition, decay, outside attraction, appeal and capacity. They are reserved entirely for OOD stress testing. All coordinates are independently generated Cartesian metres; no Bengaluru coordinates, rankings, store outcomes or desired winners influence the generator. Formats vary among supermarket/grocery/convenience with disclosed area/appeal/preferences. The local feature catchment is 1,500 m and the feature distance decay is 750 m.

For each candidate considered alone:

1. Select cells within 1,500 m. Each cell's annual wallet is synthetic population × synthetic annual grocery spending/person. Their sum is the candidate's addressable wallet feature and physical bound.
2. Use external competitors within the same site catchment; remaining shopping channels are represented by a strictly positive outside option. Feature attraction is the baseline equal-unit `sum(exp(-candidate_competitor_distance/750))`. Allocation uses bounded heterogeneous competitor masses, disclosed market-level decay and outside attraction; these hidden generator quantities are not training features.
3. Construct baseline POI counts and the six raw DaypartDNA descriptors using the approved category matrix, metric distances, availability fractions and evidence weights. Synthetic missing schedules use explicit 0.5 availability/evidence. Format preferences and [25,20,25,50,24,24] representative weekly bin-hours produce a temporal appeal term. This is an assumed utility link, not observed visitation.
4. Candidate attraction per cell is `(area/100) * format_appeal * market_appeal * bounded_lognormal_appeal_noise * exp(0.8*tanh(weighted_daypart/50)) * exp(-distance/allocation_decay)`. Noise is clipped to [0.8,1.25] upstream of allocation, so it cannot create negative or unbounded sales.
5. Initial share is candidate attraction / (candidate + external + outside). Initial candidate demand is the sum of cell wallet × share. Capacity is area × the disclosed market capacity density. Multiply candidate shares by `min(1,capacity/initial_demand)`; route unserved demand to outside. External allocation remains unchanged. Candidate + external + outside spending conserves each cell's wallet.

The target is the resulting candidate annual allocation. Each row includes an audit ledger of wallet bound, external/outside allocation, capacity, unbounded demand and completion fraction, all excluded from predictors. Every target is nonnegative and at most its catchment wallet/capacity. Twenty alternatives are **not simultaneously operating stores**; their targets must never be summed as a joint network. There are zero own-company branches in every market. This isolated label simulator is not the later Part D network/cannibalisation engine and performs no theta calibration, financial analysis or optimisation.

## Feature/preprocessing protocol

`features.py` fixes 20 predictors: area, annual wallet, population, external competitor count/attraction/nearest distance, wallet-weighted mean distance, six supported POI counts, six raw DaypartDNA indices and store format. `ml/artifacts/reference_sales_v1/feature_schema.json` is the exported ordered allowlist. `ml/evaluation/reference_sales_v1/feature_compatibility.csv` accounts for every one of the 70 canonical columns.

Identifiers, coordinates/locality labels, own branches, rents/capex/opex/margins, future infrastructure, constant source quality, unsupported households/routing and historical transit fields are excluded. Other enriched features are redundant/contextual and do not enter automatically. The two all-null Bengaluru household/routing columns remain null. A null nearest-competitor distance with zero mapped competitors is a legitimate undefined feature; it is the only permitted nullable predictor. A train-only median plus missing indicator represents that absence internally, without fabricating a geographic measurement. Missing required columns/other values, invalid counts, nonfinite values, unknown formats and unknown extra keys are errors.

All preprocessing fits the 60 training markets only: numeric median/missing indicator, log1p, standard scaling and format one-hot encoding. The two fitted regressors learn log-odds of capture fraction; inference uses sigmoid × the supplied wallet to guarantee a finite [0,wallet] output. Median is a fitted annual-sales constant projected onto that same feasible interval. These output constraints are disclosed for every baseline comparison. Predicted INR inherits the supplied wallet's nominal price basis; the adapter does not convert historical prices to 2026 or treat historical population as current.

Ridge alphas and two CatBoost configurations are declared before execution. Both CatBoost trials use CPU, one thread and a fixed seed; no early stopping is fitted against test/OOD. Select the full-feature model by validation WAPE, freeze selection, then evaluate test/OOD once. The final model remains trained on 60 markets; no post-selection train+validation refit occurs. Ablation removes all six raw dayparts with the selected family's same parameters and train markets. It is a diagnostic experiment, not an extra model-selection candidate after seeing test results.

The implemented preprocessing isolation follows [scikit-learn's train-only preprocessing guidance](https://scikit-learn.org/stable/common_pitfalls.html). CatBoost's CPU/seed/file options and native model export use its [official regressor interface](https://catboost.ai/docs/en/concepts/python-reference_catboostregressor). Exact local versions, rather than the current online documentation version, identify the executed environment.

## Internal inference seam

```python
from ml.inference.reference_sales import ReferenceSalesEstimator

estimator = ReferenceSalesEstimator()  # trusted local manifest, schema and hashes
result = estimator.predict(prepared_canonical_feature_row)
# result["reference_annual_sales_inr"], result["method_mode"],
# result["model_artifact_id"], result["diagnostics"]
```

Pass a Python dictionary with the 20 named features (optionally canonical metadata fields) from the backend's prepared internal feature view. `predict_many` accepts a sequence of such mappings. `allow_csv_strings=True` explicitly enables numeric parsing for CSV dictionaries; backend numeric dictionaries are strict by default. Unknown keys are rejected. The canonical public `Site` does not contain catchment features and cannot itself produce an estimate; the backend must supply the prepared evidence dictionary later. This internal result is not a replacement public API schema or `SiteAnalysis` response. Neither `run_evaluation` nor `run_portfolio` has been changed or connected.

Missing, corrupt, schema-incompatible or unqualified artifacts raise `ModelUnavailableError`. To explicitly request the architecture's assumption mode, pass `assumption_capture_fraction=<declared fraction in [0,1]>`. There is no hidden default share. This fallback requires the valid allowlisted feature dictionary (plus optional site ID if no saved schema is available), returns a null artifact ID and exposes the unavailable reason; it cannot repair missing source evidence. Saved models/schema/preprocessor files have SHA-256 verification. Load only this trusted local output; no remote model downloads occur.

Inference diagnostics flag numerical training-range violations and shifted-market degradation. These are evidence/support warnings, not calibrated probabilities, confidence intervals or guarantees of domain detection. Training ranges cannot establish joint-distribution similarity. Real-world validity is absent even for a point inside every marginal range.

## Results and limitations

Actual values are in the generated completion report, model card and metrics/ablation/perturbation JSONs. Ridge won the frozen validation comparison; CatBoost's slightly lower test WAPE does not retrospectively change selection. The synthetic gate passes; shifted-market error triggers review. Daypart ablation has mixed validation/test/OOD results, so no proven DaypartDNA advantage is claimed. Controlled area/competition changes behave as expected, but wallet/daypart responses are not universally monotonic; opposite-direction counts are retained and discussed. The model is not ready for unsupervised commercial decisions or a real-revenue accuracy claim.

The local environment emits a Joblib/NumPy 2.5 deprecation warning while reading arrays. Deserialization and all numerical tests are executed; keep the recorded versions. No dependency upgrade or unrequested shared requirements change was made. Existing Git rules ignore `ml/artifacts/*`; artifacts exist locally and are checksummed, but have not been committed/pushed or publicly packaged.

Stop after Part B. Remaining public endpoints, evaluation/portfolio stubs and Parts C/D/finance/FailFast/scenarios/ranking/optimisation are outside this implementation.
