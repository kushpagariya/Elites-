# Part B.2 simulator and demand-model correction

PART_B_READY_WITH_WARNINGS

This new synthetic experiment corrects target saturation and wallet-response structure. It does not replace or overwrite the original Ridge, B.1 adapter, cards, metrics or data. No later analytical component is connected. All inference remains **model_simulated**; no real store-sales accuracy or calibrated confidence is claimed.

## 1. Demonstrated root cause

In v1, initial candidate allocation was nonnegative and wallet-bounded. A separate post-allocation annual capacity (floor area × market INR/sqm/year density) systematically overrode it. There was no demonstrated annual/monthly INR mismatch or pre-bound allocation above the wallet. Both the cell/catchment wallet and the capacity were annual INR. The hypothetical wallets and resulting capture demand were simply too large relative to that independently assumed cap.

For the 2,000 old regular rows, raw allocation / capacity had median **11.1721**, range **0.8036–113.2062**. Exactly **1997/2,000** regular rows and all OOD rows were capped. All 1,200 training rows were capped; three validation rows were not. Thus training targets collapsed to area × hidden market capacity, masking demand, competition and daypart mechanisms.

The old candidate attraction/large catchment wallets produced excessive pre-cap demand relative to this capacity assumption, rather than violating wallet conservation. Removing the unjustified cap is the correction; no inflation trick, post-hoc target clipping or desired investment outcome is used. `v1_capacity_audit.csv` preserves every original raw target, capacity, final target and wallet; `v1_root_cause.json` reports ratio distributions, zeros, correlations and within/between-market variation.

## 2. Corrected simulator and source alignment

The new process uses `A=exp(theta)*(area/100)^1*exp(-distance/750)` and outside=1 in ordinary markets. Each candidate is considered alone against external competitors plus outside. Annual reference sales are the sum of cell wallet × candidate share. External/outside allocations conserve spending; there is **no capacity cap**. Positive outside and finite attraction keep target shares strictly inside the wallet. Twenty candidates are alternatives, not simultaneously open stores, and no own-company branch enters any target.

Synthetic source templates are resampled from the existing deduplicated OSM POIs, grocery competitors, recorded/assumed opening schedules and WorldPop/HCES-derived spending cells. Poisson copies/omissions, 100 m position jitter, rotations and 0.85–1.15 geometric scales create new synthetic markets; population and POI intensity vary over declared 0.65–1.45 multipliers. This preserves sparse shopping POIs and the observed category/spatial relationships instead of the old unrelated uniform category mixture.

Population is a modelled 2020 nominal 1 km source; expenditure is the nominal 2023–24 HCES state urban proxy with local-transfer assumptions. The 100 prepared grid cells are subdivided into 16 quadrature points each (1,600 total), conserving source totals. That is a numerical uniform-within-cell assumption, **not a finer observed population resolution**. Synthetic wallets additionally vary by a disclosed spending multiplier. No households or routing measurements are invented. OSM incompleteness and schedule assumptions remain. Source hashes/attributions and source status are recorded in `source_evidence.json`; original source/licence reports are retained. No metro inputs are used because none are part of the capture schema.

Store-area/format/theta and behavioural ranges are explicitly assumed, not observed commercial data. Approved synthetic store areas inform plausible simulation support; no actual leases, revenue density benchmark or financial cost is asserted. Daypart utility changes theta through a bounded temporal function; bounded parameter noise acts before allocation, never as arbitrary noise added to sales. Config records all parameters, seeds, ordinary/shifted deviations and target equations.

The ten unchanged candidates provide unlabelled range/schema/support diagnostics only. The simulator never reads their feature rows or coordinates, and no candidate is copied or given a target. All markets share a perturbed empirical regional source template: group isolation does **not** establish independent-city generalisation.

## 3. Fresh data, split and protocol

New generator seed **2026102502**, split seed **56319**, model seed **90217**. Exactly **100 ordinary markets × 20 alternatives = 2,000 rows**, plus **20 separate shifted markets × 20 = 400 rows**. New identifiers and seeds do not reuse the v1 test set. Grouped split is **60/20/20 markets**, or **1,200/400/400 rows**, with 400 OOD rows isolated.

Versioned input schema requires the original 20 supported feature names. **19 capture predictors exclude annual_wallet_inr**; wallet is only the final scale input. IDs, audit targets/theta/positions, own branches, costs, infrastructure and quality scores are excluded. Training-only imputation/encoding/log transforms/scaling are used. The two unsupported Bengaluru household/routing columns remain untouched. Only the declared no-competitor nearest-distance null has a model missingness representation.

Protocol/split hashes, grids and support rule are frozen before fitting. Median is a genuinely fitted median-logit-capture baseline multiplied by wallet; Ridge and CatBoost fit logit capture. No target endpoint clipping is used. All targets lie strictly inside (0,wallet). Preprocessing and the final model fit use training groups only. Selection uses minimum validation INR WAPE among these structurally homogeneous models. No final test/OOD tuning or post-selection refit occurred. Ablation is a diagnostic, not a retrospective selection candidate.

## 4. Actual B.2 results

| Model | Split | MAE INR/year | RMSE INR/year | WAPE |
|---|---|---:|---:|---:|
| median | validation | 56,189,122.30 | 80,736,092.47 | 48.5944% |
| median | test | 52,024,756.17 | 76,925,723.45 | 44.9718% |
| median | ood | 84,733,361.71 | 119,955,556.82 | 75.1071% |
| ridge | validation | 7,474,130.92 | 11,312,858.24 | 6.4639% |
| ridge | test | 8,443,417.84 | 14,513,074.79 | 7.2988% |
| ridge | ood | 35,938,211.53 | 47,558,214.30 | 31.8554% |
| catboost | validation | 7,402,550.33 | 10,759,234.07 | 6.4020% |
| catboost | test | 8,824,469.50 | 15,816,629.10 | 7.6281% |
| catboost | ood | 37,495,970.52 | 50,525,227.74 | 33.2362% |

Selected **catboost**, parameters `{'iterations': 450, 'depth': 5, 'learning_rate': 0.06, 'l2_leaf_reg': 6}`, by validation only. Ridge happens to have lower final test/OOD error; it is not retrospectively substituted. The synthetic activation gate is **PASS**, with **83.0379%** relative test-WAPE reduction versus the new median baseline. WAPE is sum absolute error / sum absolute actuals; zero denominators are explicitly undefined.

OOD/test WAPE ratio is **4.3570×**, exceeding the 2× review threshold. Shifted markets change wallet level, competitor density, decay (1,100 m), outside (1.5) and hidden theta (-0.4 offset); this is a genuine conditional stress regime, not a tuning set. Model outputs retain a shifted-market review warning. No real-world calibrated intervals or probabilities exist.

Fitted prediction latency: p50 **7.9994 ms**, p95 **10.6350 ms**, 50 single-row calls after five warmups. This includes fitted preprocessing/prediction, excludes Python startup, disk load and adapter support search. Platform: `Windows-11-10.0.26200-SP0`.

| Ablation split | Full WAPE | Without six dayparts WAPE |
|---|---:|---:|
| validation | 6.4020% | 6.2698% |
| test | 7.6281% | 7.5880% |
| ood | 33.2362% | 32.6806% |

Removing dayparts slightly improves this run; no incremental DaypartDNA predictive advantage is established. All ablation metrics are retained rather than cherry-picked. No economic-ordering/ranking ablation is claimed. Target distributions, capture distributions, near-zero counts, Spearman relationships and within/between-market variation are exported in `target_diagnostics.json`. Every new row retains raw pre-bound=final target and `capacity_applied=False`; no systematic target saturation remains.

## 5. Wallet guarantee and perturbations

`R(W,X)=W*sigmoid(fitted_model(X))`, where X excludes wallet and wallet-derived ratios. Thus **R(kW,X)=kR(W,X)** exactly up to floating-point arithmetic for nonnegative finite scaling, fixed capture features and consistent reference-wallet context. This is a structural fitted-model property, not a hardcoded capture formula: the share is learned by median/Ridge/CatBoost. The simulator satisfies the same identity for fixed geometry/attractiveness/competition/outside. Sigmoid is the disclosed fitted output link; no negative/over-bound prediction is silently clipped after inference.

Wallet is also excluded from joint capture-support scoring because multiplying fixed cell wallets does not change capture geometry; numerical validation and explicit wallet/price-basis reporting remain. Marginal wallet-range changes remain warnings. This support definition is justified by the proven scale invariant, not changed to make candidates pass.

| Candidate perturbation | Increase | Decrease | Unchanged | Rejected |
|---|---:|---:|---:|---:|
| area_x1.25 | 10 | 0 | 0 | 0 |
| competition_plus5 | 0 | 10 | 0 | 0 |
| wallet_x0.5 | 0 | 10 | 0 | 0 |
| wallet_x1.25 | 10 | 0 | 0 | 0 |
| weekday_evening_raw_x1.25 | 7 | 0 | 3 | 0 |
| weekday_lunch_raw_x1.25 | 4 | 5 | 1 | 0 |
| weekday_morning_raw_x1.25 | 8 | 1 | 1 | 0 |
| weekday_night_raw_x1.25 | 6 | 3 | 1 | 0 |
| weekend_day_raw_x1.25 | 7 | 0 | 3 | 0 |
| weekend_evening_raw_x1.25 | 8 | 1 | 1 | 0 |

Competition, store area and individual daypart responses are measured, without imposing universal monotonic constraints on conditional fitted features. The physical allocator does strictly reduce candidate share when adding positive external attractions with everything else fixed; that is tested separately. Exact candidate patches/raw results are retained in `candidate_perturbations.json`.

## 6. Candidate support and preliminary feasibility

Marginal ranges and multivariate support both use training-only information. Per format, standardised capture features are compared to the nearest training neighbour; the threshold is the fixed 99th percentile of training leave-one-out nearest-neighbour distances. The rule was declared in config/protocol before candidate evaluation. It reflects multimodal source-grounded geography better than the previous uniform simulator support; it is not a calibrated probability or confidence interval. No candidate features or thresholds were modified after results.

| Site | Raw reference INR/year | Usable INR/year | Wallet bound INR/year | Joint distance / threshold | Reference feasibility |
|---|---:|---:|---:|---|---|
| site-01 | 101,985,994.35 | 101,985,994.35 | 418,637,242.85 | 0.9909 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |
| site-02 | 73,864,281.27 | 73,864,281.27 | 359,636,436.34 | 1.7944 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |
| site-03 | 140,228,096.57 | 140,228,096.57 | 399,816,206.84 | 0.7761 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |
| site-04 | 94,750,639.84 | 94,750,639.84 | 472,657,518.64 | 1.5567 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |
| site-05 | 267,957,144.95 | 267,957,144.95 | 597,618,387.63 | 2.5078 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |
| site-06 | 197,107,450.50 | 197,107,450.50 | 540,624,490.89 | 2.3777 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |
| site-07 | 93,059,667.12 | 93,059,667.12 | 272,460,167.33 | 1.0495 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |
| site-08 | 96,069,934.62 | 96,069,934.62 | 190,220,719.85 | 1.0639 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |
| site-09 | 115,178,485.29 | 115,178,485.29 | 219,997,007.35 | 2.0479 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |
| site-10 | 249,386,682.64 | 249,386,682.64 | 504,439,009.74 | 1.5679 / 2.5906 | PRELIMINARY_ENDPOINT_COMPATIBLE_ASSUMPTIONS_REQUIRE_CONFIRMATION |

**10/10 jointly supported; 10/10 usable** under the declared synthetic-model/support/reference assumptions. All ten are schema-compatible and inside marginal training ranges. Every site retains `SHIFTED_MARKET_DEGRADATION_REVIEW`. Sites 05 and 06 are closest to the joint threshold; support is finite-sample and regional, not empirical forecast validation. There are no candidate revenue labels, so no candidate accuracy is reported.

Preliminary checks use the actual existing 100 spending-cell centroids/wallets and mapped external grocery POI coordinates, great-circle distances, gamma=1, tau=750 m and outside=1. External attraction is explicitly assumed equal unit mass (100 sqm/theta=0), not measured store size/productivity. Two endpoint revenues at theta=-30 and +30 bracket the requested estimates. Continuity gives preliminary compatibility under those fixed assumptions; no bisection, full Huff engine, own-branch displacement or downstream orchestration is implemented.

The prepared full AOI grid and original circular raster catchment differ. The endpoint test is a disclosed centroid approximation using available evidence, not a production certificate. Later integration must freeze/align the actual reference inputs, confirm external/outside assumptions and calibrate/check requested-versus-achieved targets. `automatic_calibration_permitted=False` remains explicit.

## 7. Versioned inference and artifacts

New explicit entrypoint: `ml.inference.reference_sales_v2.ReferenceSalesEstimatorV2`. It loads the actual saved fitted model, schema and support metadata by verified SHA-256, preserves raw versus usable estimates, returns INR/year and `model_simulated`, validates required inputs and rejects unsupported geometry or a supplied failing endpoint bracket. Invalid/missing evidence is not fabricated. No network or notebook is needed. The original B.1 entrypoint remains unchanged and blocked for reproducibility; there is no silent promotion through backend APIs.

```python
from ml.inference.reference_sales_v2 import ReferenceSalesEstimatorV2
estimator = ReferenceSalesEstimatorV2()
result = estimator.predict(prepared_feature_row, reference_bracket=(reference_low_inr, reference_high_inr))
# Inspect raw/usable value, support, feasibility and warnings before later calibration.
```

Artifact ID: `reference-sales-sim-v2-438774e0a585`. Selected file: `ml/artifacts/reference_sales_v2/catboost.joblib`; SHA-256 `438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998`. Separate model card, learned preprocessing, all comparison models and schema are in that directory. Dependencies: numpy==2.5.2, pandas==2.3.3, scipy==1.18.1, scikit-learn==1.9.0, catboost==1.2.10, joblib==1.5.3.

Exact reproduction from repository root (Python 3.12.10):

```powershell
python -m pip install -r ml/training/reference_sales_v2/requirements-lock.txt
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -m ml.training.reference_sales_v2.train
python -m ml.training.reference_sales_v2.report
```

## 8. Tests, preservation and comparison

**19/19 acceptance tests passed; 0 failures, 0 errors, 0 skipped.** Executed by `python -m ml.training.reference_sales_v2.report`; full test identities/output and existing Joblib/NumPy deprecation warnings are in `test_results.json`. Full generator CSV/split reproducibility and selected-model refit reproducibility were actually executed. Binary serialisation metadata and timings may vary; fixed-seed numerical predictions are checked.

Tests cover counts/groups, conservation/wallet bounds, no cap, demand/competition effects, simulator and fitted wallet homogeneity, candidate support invariance, no ID/target/own-branch leakage, train-only preprocessing/support, validation selection, recalculated metrics, finite predictions, input rejection, unsupported joint inputs, ten-site endpoint compatibility, explicit bracket rejection, ablation, unchanged originals and offline inference.

| Phase | Target / evaluation meaning | Outcome |
|---|---|---|
| Part B | v1 capacity-dominated synthetic targets; old market split | Ridge selected; historical metrics preserved |
| Part B.1 | Audit of unchanged v1; no retraining | Blocked due target degeneration, wallet response and support |
| Part B.2 | New uncapped source-grounded allocation labels; fresh splits; wallet-homogeneous fitted capture | PART_B_READY_WITH_WARNINGS |

Do **not** compare 17.61% v1 WAPE to 7.63% v2 WAPE as improvement on the same task: label mechanism, source distributions, split identities and median baseline definition differ. The valid activation comparison is the new selected model against the new median within B.2.

All **294 pre-existing files remain byte-identical**, including Part A/B/B.1 data, weights, reports, cards, inference entrypoints and public backend/frontend contracts. Branch remains ML at `adcabc63a1f15911d6f10afa3c1dc2a146c1468f`; no commits, pushes, switches, merges, rebases or PRs occurred. Current pre-existing B.1 worktree modifications were preserved, not reverted.

## 9. Output inventory and remaining warnings

| CSV | Rows | Columns | Null fields |
|---|---:|---:|---:|
| ml/training/data/reference_sales_v2/market_splits.csv | 120 | 2 | 0 |
| ml/training/data/reference_sales_v2/synthetic_regular.csv | 2000 | 34 | 437 |
| ml/training/data/reference_sales_v2/synthetic_shifted.csv | 400 | 34 | 64 |
| ml/evaluation/reference_sales_v2/bengaluru_source_ranges.csv | 19 | 5 | 0 |
| ml/evaluation/reference_sales_v2/predictions.csv | 3600 | 8 | 0 |
| ml/evaluation/reference_sales_v2/segments.csv | 27 | 10 | 27 |
| ml/evaluation/reference_sales_v2/v1_capacity_audit.csv | 2400 | 7 | 0 |

All new source/config/dependency pins: `ml/training/reference_sales_v2/`; generated data/splits: `ml/training/data/reference_sales_v2/`; evaluation, perturbations, candidate support and old-vs-new diagnosis: `ml/evaluation/reference_sales_v2/`; fitted artifacts/schema/card: `ml/artifacts/reference_sales_v2/`; adapter: `ml/inference/reference_sales_v2.py`; tests: `tests/unit/test_reference_sales_v2.py`. Exact file hashes are exported in `checksums.json` (self excluded).

Remaining warnings: synthetic targets and assumed theta/outside/competitor masses; reuse of one perturbed regional source template; historical/modelled population and nominal expenditure; incomplete OSM/assumed schedules; material shifted-regime degradation; no demonstrated daypart ablation benefit; no real-outcome calibration or uncertainty intervals; centroid/reference-context approximation. Retain source attribution/usage records. Nothing was publicly packaged and no raw metro data was used/copied.

The correction supports later prototype calculations only through the declared versioned fitted-model/support/feasibility path, with warnings reviewed and actual reference calibration still required. No Part C, full Huff, finance, FailFast, infrastructure, ranking, portfolio or backend/frontend integration began. Stop here.

PART_B_READY_WITH_WARNINGS
