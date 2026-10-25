# Part B completion report

PART_B_READY_WITH_LIMITATIONS

Completed locally on branch **ML** at existing HEAD `569f4f52f459ed09129c04a17ac97485601d7bb7`. This is the fitted demand-model phase only. **33/33 tests pass**, with 0 failures, 0 errors and 0 skips. All **233 protected pre-existing files** match their pre-edit SHA-256 values.

## A. Implemented files

Repository root: `C:\Users\Office Pc\OneDrive\Documents\Elites-`. Every path below is relative to that root. The checksum inventory also includes full SHA-256 values for these outputs; its own checksum is excluded.

| Exact path | Purpose |
|---|---|
| `ml/artifacts/reference_sales_v1/ablation_no_daypart.joblib` | Saved diagnostic Ridge model without six dayparts |
| `ml/artifacts/reference_sales_v1/catboost.cbm` | Native fitted CatBoost tree export (logit-capture output) |
| `ml/artifacts/reference_sales_v1/catboost.joblib` | Saved fitted CatBoost comparison with preprocessing/output head |
| `ml/artifacts/reference_sales_v1/feature_schema.json` | Exported ordered inference schema and null rules |
| `ml/artifacts/reference_sales_v1/manifest.json` | Chosen model identity, parameters, dependencies, gate and file hashes |
| `ml/artifacts/reference_sales_v1/median.joblib` | Saved fitted median comparison baseline |
| `ml/artifacts/reference_sales_v1/MODEL_CARD.md` | Selected-model evidence and usage limitations |
| `ml/artifacts/reference_sales_v1/preprocessing.json` | Training-only learned imputation/scaling/encoding configuration |
| `ml/artifacts/reference_sales_v1/preprocessor.joblib` | Saved selected fitted preprocessing object |
| `ml/artifacts/reference_sales_v1/ridge.joblib` | Saved validation-selected fitted Ridge sales model |
| `ml/evaluation/reference_sales_v1/bengaluru_inference_examples.csv` | 10 unvalidated model_simulated inference examples, not labels/ranks |
| `ml/evaluation/reference_sales_v1/daypart_ablation.json` | Same-protocol six-feature removal diagnostic |
| `ml/evaluation/reference_sales_v1/feature_compatibility.csv` | Use/exclusion/missingness for every canonical 70-field column |
| `ml/evaluation/reference_sales_v1/heldout_perturbations.csv` | 160 measured controlled perturbation predictions |
| `ml/evaluation/reference_sales_v1/heldout_predictions.csv` | Actual targets/predictions for all evaluated families and ablation |
| `ml/evaluation/reference_sales_v1/metrics.json` | Actual validation/test/OOD, activation, latency and preservation evidence |
| `ml/evaluation/reference_sales_v1/output_inventory.json` | Actual output CSV dimensions and null counts |
| `ml/evaluation/reference_sales_v1/perturbation_report.json` | Measured expected/opposite response counts |
| `ml/evaluation/reference_sales_v1/preserved_input_hashes.json` | Pre-edit hashes of all 233 protected existing files |
| `ml/evaluation/reference_sales_v1/segment_metrics.csv` | Executed format, competition and per-market error metrics |
| `ml/evaluation/reference_sales_v1/selection_lock.json` | Frozen validation-only selection before held-out scoring |
| `ml/evaluation/reference_sales_v1/source_inventory.json` | Inspected original/revised feature and geographic inventory with hashes |
| `ml/evaluation/reference_sales_v1/test_results.json` | Executed unit/integration test results and warning record |
| `ml/inference/__init__.py` | Package marker |
| `ml/inference/reference_sales.py` | Offline reusable internal inference adapter and explicit fallback |
| `ml/training/data/reference_sales_v1/market_manifest.json` | All market parameters, generator configuration and independent seeds |
| `ml/training/data/reference_sales_v1/market_splits.csv` | 120 unique market-group split records |
| `ml/training/data/reference_sales_v1/synthetic_regular.csv` | 2,000 synthetic observations with predictors, target and allocation audit |
| `ml/training/data/reference_sales_v1/synthetic_shifted.csv` | 400 rows from 20 shifted synthetic markets, never tuned against |
| `ml/training/reference_sales/__init__.py` | Package marker |
| `ml/training/reference_sales/config.json` | Versioned generator bounds, seeds and fixed model grids |
| `ml/training/reference_sales/features.py` | 20-field allowlist, types, units and strict feature validation |
| `ml/training/reference_sales/metrics.py` | Executed MAE/RMSE/WAPE including explicit zero denominator handling |
| `ml/training/reference_sales/models.py` | Median, Ridge, CatBoost fits and bounded output/preprocessing |
| `ml/training/reference_sales/README.md` | Reproduction, simulator equations, preprocessing, inference use and limits |
| `ml/training/reference_sales/report.py` | Executed test evidence, model card, completion report and checksums |
| `ml/training/reference_sales/requirements-lock.txt` | Exact locally executed dependency versions |
| `ml/training/reference_sales/simulator.py` | Independent synthetic markets and wallet-conserving candidate-only labels |
| `ml/training/reference_sales/train.py` | Grouped training, validation lock, evaluation, ablation, artifacts and examples |
| `PART_B_COMPLETION_REPORT.md` | Requested Part B completion and next dependency |
| `tests/unit/test_reference_sales.py` | Part B unit/integration, reproducibility and preservation tests |
| `ml/evaluation/reference_sales_v1/output_checksums.json` | Complete output SHA-256 inventory (self excluded) |

## B. Dataset generation

Exactly **100 regular markets × 20 alternative potential stores = 2,000 observations**, and **20 separate shifted markets × 20 = 400 observations**. Twenty features are model inputs; the other synthetic columns are group/provenance metadata and excluded target/allocation audit fields.

Grouped partitions: **60 training markets / 1,200 rows**, **20 validation / 400 rows**, **20 test / 400 rows**; OOD is **20 additional markets / 400 rows**. Markets/observation keys do not overlap. Bengaluru candidates occur only in ten separately labelled inference examples.

Seeds: generator **20261024**, split **314159**, model **271828**. Each market has 100 synthetic metric spending cells, external competitors, POIs, varied store formats/area, heterogeneous bounded appeal/decay/spend/capacity and bounded lognormal attraction noise. Configuration version `reference-market-simulator-v1`; parameters and individual market seeds are exported.

The target is **competitors-only reference annual store sales in INR, before own-company branch displacement**. For each candidate alone, cell wallet is allocated among that candidate, external competitors and a positive outside option. Capacity-unserved demand returns to outside. Targets conserve cell spending, stay nonnegative and cannot exceed the catchment wallet or capacity. The 20 stores are alternatives, not simultaneously open branches. No own-company store enters a target and no target uses a desired winner/rank. The simulator is isolated from the later production network/Huff component.

| Output CSV | Rows | Columns | Null fields |
|---|---:|---:|---:|
| `ml/evaluation/reference_sales_v1/bengaluru_inference_examples.csv` | 10 | 11 | 10 |
| `ml/evaluation/reference_sales_v1/feature_compatibility.csv` | 70 | 4 | 0 |
| `ml/evaluation/reference_sales_v1/heldout_perturbations.csv` | 160 | 8 | 0 |
| `ml/evaluation/reference_sales_v1/heldout_predictions.csv` | 4,800 | 8 | 0 |
| `ml/evaluation/reference_sales_v1/segment_metrics.csv` | 304 | 12 | 304 |
| `ml/training/data/reference_sales_v1/market_splits.csv` | 120 | 2 | 0 |
| `ml/training/data/reference_sales_v1/synthetic_regular.csv` | 2,000 | 33 | 58 |
| `ml/training/data/reference_sales_v1/synthetic_shifted.csv` | 400 | 33 | 0 |

Synthetic nearest-competitor distances are null only when no mapped competitor exists. Example fallback fractions are null because fitted mode is used. Per-column null counts are exported in `output_inventory.json`. Original Bengaluru unknowns are untouched.

## C. Model results

All results below were executed on simulator targets. WAPE = sum absolute error / sum absolute actual targets, with a null result plus explicit reason at zero denominator. INR errors are annual nominal simulator amounts.

| Model | Split | MAE (INR/year) | RMSE (INR/year) | WAPE |
|---|---|---:|---:|---:|
| median | validation | 25,729,867.53 | 36,356,935.52 | 61.7772% |
| median | test | 27,993,008.97 | 42,379,433.33 | 59.9154% |
| median | ood | 20,187,297.34 | 25,564,104.97 | 64.0335% |
| ridge | validation | 8,166,757.00 | 12,491,378.57 | 19.6083% |
| ridge | test | 8,229,053.74 | 12,754,632.55 | 17.6132% |
| ridge | ood | 17,005,124.27 | 22,945,245.54 | 53.9398% |
| catboost | validation | 11,069,095.35 | 16,927,461.55 | 26.5768% |
| catboost | test | 7,752,451.69 | 12,306,383.91 | 16.5931% |
| catboost | ood | 57,831,672.79 | 82,164,896.92 | 183.4404% |

Selected **ridge** with `{"alpha": 20.0}` by validation WAPE. Selection is locked before final test/OOD evaluation. CatBoost was fitted successfully on CPU; neither installation nor fitting failed. CatBoost has lower test error but worse validation error in this execution; it is not retrospectively promoted. The full-feature family/hyperparameter grid was frozen in configuration before the first run. No model was tuned on test/OOD, and no final fit uses validation/test rows.

Activation target: **PASS**. Relative held-out test-WAPE reduction versus median is **70.6032%**, exceeding the 10% threshold. This passes only the declared synthetic model gate; it does not validate retail-market forecasts or complete AC28 downstream integration.

**OOD warning:** selected-model shifted WAPE is **53.9398%**, **3.0625×** regular test WAPE, above the handoff 2× review threshold. The adapter exposes that limitation.

Segment-wise metrics by store format, external competitor count and market are in `segment_metrics.csv`, with raw evaluation pairs in `heldout_predictions.csv`. They are recalculated in tests.

| Inference path | Warm p50 ms | Warm p95 ms |
|---|---:|---:|
| median | 0.0132 | 0.0153 |
| ridge | 3.4388 | 6.0068 |
| catboost | 3.0545 | 4.2056 |
| selected_adapter | 2.3332 | 4.1159 |

Latency protocol: batch size 1, 5 warmups, 50 measured calls, CPU. Selected adapter includes validation/preprocessing/prediction; cold artifact load in a warm Python process was **16.5095 ms**. Python startup/import time is excluded. These are local observations, not application/portfolio latency claims. Platform: `Windows-11-10.0.26200-SP0`.

DaypartDNA ablation removes all six raw baseline indices, retains the selected family/hyperparameters and refits preprocessing only on the same training markets.

| Split | Full WAPE | Without dayparts WAPE | Full relative improvement |
|---|---:|---:|---:|
| validation | 19.6083% | 19.1401% | -2.4465% |
| test | 17.6132% | 17.8962% | 1.5812% |
| ood | 53.9398% | 51.7996% | -4.1316% |

Ablation is mixed and is not used for retrospective model selection. It does not establish a consistent predictive advantage. Economic-ordering ablation is intentionally deferred because no ranking/finance/network component was implemented.

Held-out perturbations: store area +25% increases predictions in **40/40** cases; extra external competition reduces them in **40/40**. Wallet +25% increases **30/40** and decreases **10/40**; dayparts +25% increases **20/40** and decreases **20/40**. The latter failures of universal expected monotonicity remain documented. No hyperparameters were changed after these final-test diagnostics.

## D. Feature compatibility

The explicit ordered 20-feature allowlist is:

- `store_size_sqm`
- `annual_wallet_inr`
- `population_1500m_est`
- `competitor_count_1500m`
- `competitor_attraction_index`
- `nearest_competitor_distance_m`
- `mean_wallet_weighted_distance_m`
- `office_poi_count_1500m`
- `education_poi_count_1500m`
- `healthcare_poi_count_1500m`
- `transit_poi_count_1500m`
- `shopping_poi_count_1500m`
- `food_leisure_poi_count_1500m`
- `weekday_morning_raw`
- `weekday_lunch_raw`
- `weekday_evening_raw`
- `weekday_night_raw`
- `weekend_day_raw`
- `weekend_evening_raw`
- `store_format`

All 20 are available as named supported baseline descriptors in the enriched Bengaluru view. Source wallet/population vintages and assumption tags remain meaningful; compatibility does not establish forecasting validity. The other **50 canonical columns are excluded**; `feature_compatibility.csv` gives each exclusion/missing count. IDs, latitude/longitude/locality labels, costs, future effects, historical metro measurements, constant source-quality and redundant enrichment do not enter fitting. Both `population_10min_est` and `accessible_households_est` retain ten nulls. Only a legitimate no-competitor nearest-distance absence has a train-only model missingness representation; no measurement is invented.

## E. Model artifacts and reproducibility

Selected model ID: `reference-sales-sim-v1-3f162d1da91a`. Selected fitted file: `ml/artifacts/reference_sales_v1/ridge.joblib`.

| Artifact file | SHA-256 |
|---|---|
| `ml/artifacts/reference_sales_v1/median.joblib` | `fda7953a3033f11e36471d92e084cd7c0cc3bdd0a390dd862f10f0d9601b4b46` |
| `ml/artifacts/reference_sales_v1/ridge.joblib` | `3f162d1da91a45b206af4b4d1ab3377b493371a087cb06abed0cad9c3990a3e9` |
| `ml/artifacts/reference_sales_v1/catboost.joblib` | `35e276e79262cfff7e942e87cc999dafb8772b2d7b540e74a07148ccf0f8eb8c` |
| `ml/artifacts/reference_sales_v1/ablation_no_daypart.joblib` | `97a1190584e0517378f19203951aa03edb22bc20b5b92f5ba22b3a55c6efaa33` |
| `ml/artifacts/reference_sales_v1/catboost.cbm` | `41d8474543a790fe86aa6101d7fc41eeb07eab6631ba5e2281548a4bc34a570c` |
| `ml/artifacts/reference_sales_v1/preprocessor.joblib` | `49a5a23b59bb9ef2f3b8d63717f287657e36aebbf21018e64812c367fd183353` |
| `ml/artifacts/reference_sales_v1/feature_schema.json` | `5d614da0751e9fa5e93a91d67fb0f03174371c52d2f513b7c8730870b8b6dcfe` |
| `ml/artifacts/reference_sales_v1/preprocessing.json` | `5b3e5ba47306a6d3d3b08fd4dac5ab3c522d690fbd122908b7818a81b7580be5` |

The native `catboost.cbm` predicts logit capture and must be used with its saved preprocessing/output head; it is not itself an INR-returning adapter. `ridge.joblib` is the chosen complete bounded-sales object; `preprocessor.joblib`/`preprocessing.json` export the selected train-only transform. Model/schema/preprocessor hashes are verified on load. Full file checksums are in `output_checksums.json`. Artifacts are local and ignored by pre-existing Git rules, not committed or packaged.

Python **3.12.10**. Exact executed libraries: `numpy==2.5.2`, `pandas==2.3.3`, `scipy==1.18.1`, `scikit-learn==1.9.0`, `catboost==1.2.10`, `joblib==1.5.3`, `threadpoolctl==3.6.0`.

```powershell
python -m pip install -r ml/training/reference_sales/requirements-lock.txt
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -m ml.training.reference_sales.train
python -m ml.training.reference_sales.report
```

Generator CSV/split byte reproducibility and Ridge refit prediction reproducibility were actually tested under fixed seeds. Timing/timestamps and native serialized metadata need not be byte identical on another run/platform. Training and evaluation results are reconstructed from code/data; they are not hardcoded benchmark numbers.

## F. Integration readiness

```python
from ml.inference.reference_sales import ReferenceSalesEstimator
estimator = ReferenceSalesEstimator()
prediction = estimator.predict(prepared_canonical_feature_row)
# prediction["reference_annual_sales_inr"], prediction["method_mode"]
# prediction["model_artifact_id"], prediction["diagnostics"]
```

The backend can later pass its prepared internal feature dictionary with existing canonical column names. Raw public `Site` records lack catchment descriptors and produce an explicit missing-feature error; no new public contract was invented. The adapter reads trusted local artifacts only, detects missing/invalid input or schema mismatch and reports numerical training-range/OOD warnings. It returns `model_simulated`, artifact ID/hash and uncalibrated status. Missing/corrupt/unqualified artifacts raise `ModelUnavailableError`; a caller may explicitly request a declared capture-fraction fallback labelled `scenario_assumptions` with null artifact ID. Missing required evidence never silently invokes imputation/fallback.

The independent integration tests load saved artifacts in a fresh Python process, disable socket connections during inference, verify excluded cost/ID changes cannot affect predictions, and verify both application pipeline functions still raise NotImplementedError. No `run_evaluation`, `run_portfolio`, routes, public Pydantic schemas or frontend files were modified. No API exposes these outputs yet.

## G. Test results

Executed: `python -m ml.training.reference_sales.report` (runs `unittest` discovery for `tests/unit`). Direct equivalent also executed: `python -m unittest discover -s tests/unit -v`. **33 passed, 0 failed, 0 errors, 0 skipped**, 33 tests total: 29 Part B integrity/integration tests plus 4 unchanged finance regression tests. The latter were run as regression checks; no finance implementation was added.

Coverage includes generation counts, market isolation, no candidate/own-branch leakage, physical conservation/capacity, all model bounds, complete generator/hash reproducibility, train-only preprocessing, selected-model refit reproducibility, executed metric recalculation, zero-sum WAPE, validation-only selection, activation/OOD policy, ablation, held-out perturbations, feature errors/undefined distance, excluded-feature independence, method labels, explicit fallback, corrupt artifacts, offline/fresh-process loading, segment metrics, latency protocol and all protected hashes/Git identities.

Initial temporary-directory permission errors were fixed by using verified workspace-local test directories, without changing the model or data. Final result evidence, per-test outcomes, elapsed time and warning details are in `test_results.json`. Joblib emits a NumPy 2.5 array-shape deprecation warning; loading and numerical tests pass with pinned versions.

## H. Limitations and next dependency

- This is simulator learning, not real Indian store-sales validation. No achieved new-store sales, ground-truth targets, calibrated intervals or confidence probabilities exist for Bengaluru.
- Shifted-market error exceeds the review threshold. Wallet/daypart perturbations are not universally monotonic, and ablation gives mixed evidence. These limitations remain visible; no final-test tuning was used to conceal them.
- Simulator assumptions (outside option, competitor mass, decay, capacity, temporal preferences/noise) define the counterfactual. Geographic transfer, richer unobserved store effects and economic usefulness have not been validated.
- Bengaluru premises/economics remain synthetic; population is modelled 2020 / 1 km and spending is nominal 2023–24. Predictions inherit wallet prices. No conversion to 2026 prices, routing or household imputation was performed.
- Existing BMRCL licensing/RTI delivery gaps are unchanged. This simulator/model uses no metro measurements and copies no workbook; original archives and source data were not repackaged or modified.
- No SHAP or real-outcome interval calibration was run. No decision/ranking/portfolio improvement is claimed. AC28 downstream dependency is unfinished until separately authorised model-to-domain integration occurs.
- The next step requires an explicit instruction: review model limitations/feature semantics before further components, then coordinate the backend-owned internal preparation seam. Real-world activation requires compatible permissioned outcomes and independent temporal/geographic validation.

## I. Git and scope confirmation

Branch remains **ML**, HEAD `569f4f52f459ed09129c04a17ac97485601d7bb7`. **No commits, pushes, merges, rebases, branch changes or pull requests.** All **233** protected existing files are unchanged, including both Bengaluru versions, audits, shared fixtures, public schemas, backend/frontend, domain pipeline and original archive. New work is in ML-owned paths/tests plus this explicitly requested root report.

Part B stops here. No Part C/D, own-branch cannibalisation engine, financial forecasting, FailFast, infrastructure execution, ranking, portfolio optimisation or frontend/backend integration was started.

PART_B_READY_WITH_LIMITATIONS
