# StoreScout Part B final offline model verification

Verdict: **PART_B_OFFLINE_VERIFIED_WITH_LIMITATIONS**

Review timestamp (UTC): 2026-10-24T23:40:42.919958+00:00. Current branch `ML`; unchanged HEAD `adcabc63a1f15911d6f10afa3c1dc2a146c1468f`. Verification only; no retraining, replacement, tuning, API route tests/integration, schema/frontend/persistence edits or Git mutations.

## 1. Executive findings

The active **offline-engine** model is the separately versioned B.2 CatBoost capture estimator, not the original blocked Ridge. The three demonstrated B.1 defects are resolved **for this selected v2 artifact under its declared synthetic/reference assumptions**:

- Capacity degeneration: all2400 v2 targets are strict positive fractions of their respective wallets; no capacity cap is applied and none reaches the wallet ceiling. The generation equation allocates candidate, external and outside spending coherently.
- Wallet response: wallet is excluded from the learned capture predictors. Reference sales equal wallet×fitted sigmoid(capture score); positive finite wallet-only scaling therefore scales predictions proportionally. No decreasing usable prediction was observed in tested supported candidate inputs.
- Candidate transfer support: all ten unchanged Bengaluru candidates pass both marginal and joint checks. Thresholds were independently reconstructed from training data and were not changed.

Actual existing-test result: **55 cases: 52 PASS, 1 FAIL, 1 ERROR, 1 SKIP**. The36 current engine/finance checks pass. The two unsuccessful historical B.2 tests require the old pipeline snapshot/stubs and are explained below; they are not hidden or reported as passing. One fitting/retraining test was skipped to obey this task. Separately, **20/20 targeted verification checks passed**, with no model fitting.

Limitations prevent an unqualified verdict: substantial OOD degradation; unvalidated real-world sales and capacity assumptions; a regional synthetic support envelope; no demonstrated DaypartDNA ablation improvement; unresolved automatic-calibration/readiness flag semantics; and a repository-wide historical suite that is not green. This is not permission to treat synthetic estimates as investment forecasts.

## 2. Active model identity and dependency trace

| Item | Verified value |
| --- | --- |
| Offline caller | `ml/decision_engine/run.py:build_project` explicitly imports `ReferenceSalesEstimatorV2` |
| Active adapter | `ml.inference.reference_sales_v2.ReferenceSalesEstimatorV2` |
| Fitted wrapper / estimator | `ml.training.reference_sales_v2.model.CaptureModel` / `catboost.core.CatBoostRegressor` |
| Model artifact ID | `reference-sales-sim-v2-438774e0a585` |
| Selected parameters | iterations450, depth5, learning_rate.06, l2_leaf_reg6; seed90217; CPU/thread1 |
| Selected file | `ml/artifacts/reference_sales_v2/catboost.joblib` |
| Selected SHA256 | `438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998` |
| Schema / mode | `reference-sales-features-v2` / `model_simulated` |
| Required input fields / learned capture predictors | 20 /19; annual_wallet_inr is only the final scale factor |
| Input/target units | annual INR wallet / annual INR competitors-only reference sales before own-company displacement |
| Available real candidate sales labels | None |

The old `ReferenceSalesEstimator` in `ml/inference/reference_sales.py` still points to v1 Ridge `reference-sales-sim-v1-3f162d1da91a` with B.1 hardening. Its historical PART_B_INTEGRATION_BLOCKED verdict remains valid; that artifact was not repaired or promoted by this review. The explicit v2 route has B.2 PART_B_READY_WITH_WARNINGS evidence. There is no claim that every default/legacy import now selects v2, and no API integration was performed.

Read sources: [PART_B_COMPLETION_REPORT.md](<C:/Users/Office Pc/OneDrive/Documents/Elites-/PART_B_COMPLETION_REPORT.md>), [PART_B1_HARDENING_REPORT.md](<C:/Users/Office Pc/OneDrive/Documents/Elites-/PART_B1_HARDENING_REPORT.md>), [PART_B2_CORRECTION_REPORT.md](<C:/Users/Office Pc/OneDrive/Documents/Elites-/PART_B2_CORRECTION_REPORT.md>), [PART_C_ONWARD_COMPLETION_REPORT.md](<C:/Users/Office Pc/OneDrive/Documents/Elites-/PART_C_ONWARD_COMPLETION_REPORT.md>), [OFFLINE_ENGINE_REVIEW_REPORT.md](<C:/Users/Office Pc/OneDrive/Documents/Elites-/OFFLINE_ENGINE_REVIEW_REPORT.md>). The generator, fitting/selection source, both adapters, saved model/schema/support/preprocessing, split/selection locks, predictions and ablation artifacts were inspected.

## 3. Synthetic targets: all splits and historical contrast

For each alternative candidate alone, v2 computes `A=exp(theta)*(area/100)*exp(-distance/tau)` and `sales=Σ wallet*A/(outside+external+A)`. External attraction is the sum of distance-decayed unit competitor masses. The three allocations share exactly the same denominator. Ordinary gamma1/tau750m/outside1 match the approved reference; shifted markets deliberately use tau1100/outside1.5, wallet×1.7, higher competitor multiplicity and theta offset−.4. Those are disclosed synthetic stress variations, not measured economic changes.

Only cells within the candidate1500m synthetic circle and mapped competitors within that circle enter each synthetic reference label. Twenty alternatives in a market are **not** opened together; no own branches enter the labels. All splits use this same allocation logic. Bounded parameter noise changes attraction before allocation; there is no unconstrained sales noise, throughput cap or post-hoc target clipping. Raw pre-bound values equal final targets in every row.

The source template uses historical WorldPop/HCES-derived cell distributions and partial OSM category/schedule geometry. Each100-cell source is subdivided into16 numerical quadrature points (1600 per synthetic market) while conserving totals; this is uniform-within-cell numerical sampling, not1600 new observations. Rotations/scales, Poisson POI/competitor resampling and position jitter generate synthetic markets. No actual commercial throughput capacity is validated by removing the artificial v1 cap.

| Split | Rows / markets | Target/wallet min | Median | P99 | Max | Capacity-bound | At wallet ceiling |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 1200 / 60 | 0.03266547 | 0.26293987 | 0.65315955 | 0.70057156 | 0 (0.00%) | 0 |
| validation | 400 / 20 | 0.04889358 | 0.27601510 | 0.66641504 | 0.71681835 | 0 (0.00%) | 0 |
| test | 400 / 20 | 0.02303259 | 0.27840654 | 0.64835290 | 0.67832247 | 0 (0.00%) | 0 |
| ood | 400 / 20 | 0.01730627 | 0.17912743 | 0.56603530 | 0.58319913 | 0 (0.00%) | 0 |

Ratios are dimensionless, not percentages. All targets/wallets are finite; every target is positive and below its own addressable wallet. No zero/near-zero target below INR1 exists in the v2 saved data. Per-row candidate+external+outside totals agree with wallet to at most INR1.1920929e-06, and maximum per-cell residual is INR1.49011612e-08. These are floating-point-scale errors, not created spending.

The v1 capacity defect was independently reconfirmed from its preserved CSVs:

| Historical v1 split | Rows | Capacity-bound rows | Percentage |
| --- | ---: | ---: | ---: |
| train | 1200 | 1200 | 100.00% |
| validation | 400 | 397 | 99.25% |
| test | 400 | 400 | 100.00% |
| ood | 400 | 400 | 100.00% |

This structural contrast does not establish improvement on the same forecasting task: v1 and v2 have different generators, targets, seeds and holdouts. The historical Ridge remains unsafe on the B.1 findings. Current target validity is supported by all2400 saved rows, current source equations and the existing in-memory full-generator reproducibility test, which reproduces all regular/OOD/split CSV bytes without overwriting them.

## 4. Wallet-only perturbation verification

The active model has `R(W,X)=W*sigmoid(fitted_model(preprocess(X)))`, with W absent from X. For fixed capture features and finite nonnegative W, `R(kW,X)=kR(W,X)` and the derivative with respect to W is a nonnegative fitted capture share. It is strictly positive for current tested predictions. No `np.clip` is used in this v2 prediction head. This is a fitted-model parameterisation, not an inserted arbitrary sales formula.

Batch checks cover every2000 ordinary+400OOD feature row at wallet factors0,.1,.5,1.01,1.25,2,10: **16,800 changed predictions**. All satisfy proportionality at rtol1e−13/atol1e−6; no increasing-wallet raw prediction decreases. These raw-head checks include rows that may be unsupported; they do not bypass the adapter or imply every synthetic/OOD row is usable.

| Wallet factor | Rows | Proportionality failures | Decreases when wallet increases | Max absolute floating error INR |
| --- | ---: | ---: | ---: | ---: |
| 0 | 2400 | 0 | N/A | 0 |
| 0.1 | 2400 | 0 | N/A | 7.4505806e-09 |
| 0.5 | 2400 | 0 | N/A | 0 |
| 1.01 | 2400 | 0 | 0 | 1.1920929e-07 |
| 1.25 | 2400 | 0 | 0 | 2.38418579e-07 |
| 2 | 2400 | 0 | 0 | 0 |
| 10 | 2400 | 0 | 0 | 1.90734863e-06 |

Additionally, all ten supported Bengaluru inputs were passed through the actual adapter at factors.5,1.01,1.25,2,10: **50 changed adapter predictions**, all usable under its declared support policy, all proportional, no decreasing usable result, and exactly unchanged joint distance. At extreme wallet multipliers, marginal-range warnings may be added: wallet is excluded from **joint capture** geometry by design, while its marginal training range remains visible. A wallet-only test is not a new calibrated income/population observation. With an independently supplied fixed reference bracket, a sufficiently large scaled target can become infeasible and must be rejected; proportionality does not override a physical reference limit.

Cause of the old failure versus current resolution: v1 learned a negative wallet coefficient inside capture while also multiplying by wallet, producing negative local revenue elasticities. V2 removes that wallet predictor from the capture score, so that particular economic inconsistency is structurally excluded. This guarantee is specific to wallet-only changes; universal monotonicity in area/competition/dayparts is not established or imposed.

## 5. Bengaluru candidate support and economic feasibility

Support policy is unchanged: per-format training leave-one-out nearest-neighbour99th-percentile distance in the22-dimensional training-transformed capture design. It is a finite-sample geometry rule, not calibrated confidence. Training design and thresholds were independently reconstructed without fitting a model:

| Format | Training rows | Saved threshold | Recomputed threshold |
| --- | ---: | ---: | ---: |
| convenience | 414 | 2.581768312781 | 2.581768312781 |
| grocery | 396 | 2.490857287898 | 2.490857287898 |
| supermarket | 390 | 2.590644167643 | 2.590644167643 |

All ten candidates are supermarkets, hence threshold2.5906441676425054. Every candidate has a valid20-field schema, no marginal training-range violation, a passing joint distance and a finite/nonnegative raw prediction within its1500m feature-wallet upper bound. Raw and usable predictions are identical at baseline: no clipping, fabricated label or forced support pass was applied.

For reference feasibility, the existing100 cell-centroid wallets and all219 mapped external grocery POIs were used with gamma1/tau750m/outside1 and equal unit competitor attractiveness (100sqm/theta0). No own-company branch enters this reference. An independently calculated revenue curve at theta−30/+30 brackets every target. Independent Brent roots and the existing bounded-bisection helper both attain them; bisection residuals are below.01INR and iterations≤100.

| Site | Raw = usable INR/year | Feature-wallet limit INR/year | Marginal | Joint distance / limit | Calibrated theta | Bisection residual INR | Status |
| --- | ---: | ---: | --- | --- | ---: | ---: | --- |
| site-01 | 101,985,994.35 | 418,637,242.85 | PASS | 0.990893 / 2.590644 | -0.080210625 | +0.00430204 | SUPPORTED / ATTAINABLE WITH WARNINGS |
| site-02 | 73,864,281.27 | 359,636,436.34 | PASS | 1.794442 / 2.590644 | -0.011668886 | -0.00844745 | SUPPORTED / ATTAINABLE WITH WARNINGS |
| site-03 | 140,228,096.57 | 399,816,206.84 | PASS | 0.776084 / 2.590644 | 0.072674741 | +0.00588918 | SUPPORTED / ATTAINABLE WITH WARNINGS |
| site-04 | 94,750,639.84 | 472,657,518.64 | PASS | 1.556693 / 2.590644 | -0.033746574 | +0.00672406 | SUPPORTED / ATTAINABLE WITH WARNINGS |
| site-05 | 267,957,144.95 | 597,618,387.63 | PASS | 2.507816 / 2.590644 | 0.759981319 | +0.00956681 | SUPPORTED / ATTAINABLE WITH WARNINGS |
| site-06 | 197,107,450.50 | 540,624,490.89 | PASS | 2.377660 / 2.590644 | -0.073199600 | -0.00847727 | SUPPORTED / ATTAINABLE WITH WARNINGS |
| site-07 | 93,059,667.12 | 272,460,167.33 | PASS | 1.049542 / 2.590644 | -0.483184381 | -0.00243008 | SUPPORTED / ATTAINABLE WITH WARNINGS |
| site-08 | 96,069,934.62 | 190,220,719.85 | PASS | 1.063875 / 2.590644 | -0.516702613 | -0.00098921 | SUPPORTED / ATTAINABLE WITH WARNINGS |
| site-09 | 115,178,485.29 | 219,997,007.35 | PASS | 2.047932 / 2.590644 | -0.573263585 | +0.00347991 | SUPPORTED / ATTAINABLE WITH WARNINGS |
| site-10 | 249,386,682.64 | 504,439,009.74 | PASS | 1.567908 / 2.590644 | -0.417992557 | -0.00628641 | SUPPORTED / ATTAINABLE WITH WARNINGS |

**Unsupported baseline sites: none. Shared warning for every site:** `SHIFTED_MARKET_DEGRADATION_REVIEW`. No hidden warnings/rejection reasons were removed. Sites05/06 lie nearest the joint boundary;05 has only about3.2% distance margin to its threshold, not a probability/confidence margin. There are no candidate ground-truth sales, so these statuses report input support and numerical feasibility only.

The full source-grid annual wallet is INR9,920,688,680.87. It is distinct from each circular feature-wallet bound. Centroid versus quadrature/raster geometry and equal competitor masses are material assumptions. Attainability under this approved bounded mathematical reference is not proof of actual customer capture, throughput, market completeness, profit or achieved store sales.

Rejection safeguards were exercised without modifying thresholds: a weekday-morning input1e12 fails joint support and returns no usable estimate while retaining raw output; a supplied reference bracket capped at half the raw prediction rejects the usable target without clipping. Schema/missing/nonfinite/type errors are covered by existing tests.

Adapter fields still state `automatic_calibration_permitted=False`; its feasibility status is preliminary endpoint compatibility when a bracket is supplied, or REFERENCE_CONTEXT_NOT_SUPPLIED otherwise. This verification adds numerical root evidence but does **not** silently promote that flag or grant automatic integration. The prior C–G review found that the consumer ignores this flag/hard-block semantics; that contract gap remains unresolved.

## 6. Splits, leakage, preprocessing and selection

Verified100 regular market groups with20 alternatives each;60training/20validation/20test groups (1200/400/400rows) and20separate OOD groups (400rows). Market IDs are unique in the split manifest and no groups intersect. Generator/split/model seeds are2026102502/56319/90217. Test14 regenerates current dataset/split bytes in memory and matches all saved checksums.

Showcase IDs do not occur as labelled observation IDs, and no candidate20-feature row exactly matches a saved labelled row. The generator reads source POIs, availability and spending-cell distributions; it does not read candidate feature rows or coordinates. Training main reads candidate ranges only for unlabelled diagnostics, not as generator/model-fitting arguments. Metadata confirms zero own branches and alternative openings, not20simultaneous stores. Learned features exclude IDs, latent theta/positions, targets, own-branch proximity/coverage, costs and the legacy.75 quality score.

These exclusions do not make the evaluation independent-city validation: all markets reuse perturbed empirical regional source geometry. Shared source structure and assumed allocation mechanics limit external validity, even with correct grouped identities.

Training-only preprocessing was checked by independently computing the1200-row medians, imputed/missing-indicator log1p matrix, population-standard-deviation scaler and sorted format categories, without any fit call. Median max discrepancy is 2.27e-13, mean discrepancy 0, scale discrepancy 6.94e-18. The fitted pipeline has18numeric capture fields, one nearest-distance missing indicator and3format columns (22design columns). Nearest competitor distance is nullable only when mapped competitor count is0; missing routing/households are not imputed as model features. Saved support designs match the training matrix within2.1e−14.

Selection source evaluates one median baseline, three Ridge alphas and two CatBoost configurations on validation only, writes the selection lock, then evaluates test/OOD. The recorded winning validation trial matches active CatBoost450/depth5/.06/l2=6. Protocol config/split hashes match the actual saved files. The full chosen model fit_rows remains1200; no train+validation refit occurs in the source path.

Verification limits: saved artifacts/source/metadata are consistent with that protocol; historical execution order and every unretained losing-trial score cannot be independently proven without original fitted alternatives or a refit. No refit was authorized or performed here. Test/OOD outcomes were not used to choose a different model.

## 7. Fresh metric verification and DaypartDNA ablation

All nine median/Ridge/CatBoost×validation/test/OOD result sets were recomputed from actual saved fitted objects and source rows. MAE=mean absolute INR error; RMSE=sqrt(mean squared INR error); WAPE=sum absolute error/sum absolute actual, shown as percentages. Saved prediction records and MAE/RMSE/WAPE match fresh results to floating-point precision (maximum absolute discrepancy<1e−5INR for checked values). Each evaluation split has400 rows.

| Fitted model | Split | MAE INR/year | RMSE INR/year | WAPE |
| --- | --- | ---: | ---: | ---: |
| median | validation | 56,189,122.30 | 80,736,092.47 | 48.594390% |
| median | test | 52,024,756.17 | 76,925,723.45 | 44.971809% |
| median | ood | 84,733,361.71 | 119,955,556.82 | 75.107146% |
| ridge | validation | 7,474,130.92 | 11,312,858.24 | 6.463899% |
| ridge | test | 8,443,417.84 | 14,513,074.79 | 7.298752% |
| ridge | ood | 35,938,211.53 | 47,558,214.30 | 31.855416% |
| catboost | validation | 7,402,550.33 | 10,759,234.07 | 6.401994% |
| catboost | test | 8,824,469.50 | 15,816,629.10 | 7.628145% |
| catboost | ood | 37,495,970.52 | 50,525,227.74 | 33.236204% |

Synthetic activation gate: relative test-WAPE reduction versus the v2 fitted median baseline = **83.037942%**, exceeding10%: PASS. The v2 median is a fitted median-logit-capture×wallet baseline, not the v1 constant annual-sales baseline; old/new gains must not be compared as the same benchmark.

Shifted-market warning: selected OOD/test WAPE ratio **4.357050×**, exceeding2×. CatBoost was selected by validation (6.401994% versus Ridge6.463899%), although Ridge is better on the subsequently observed test/OOD. No retrospective replacement is justified by this verification. The lower test/OOD Ridge scores are reported honestly.

| Split | Full CatBoost WAPE | Saved no-Daypart CatBoost WAPE | Full minus ablated (percentage points) |
| --- | ---: | ---: | ---: |
| validation | 6.401994% | 6.269818% | +0.132176 |
| test | 7.628145% | 7.587982% | +0.040163 |
| ood | 33.236204% | 32.680616% | +0.555588 |

Ablation was recomputed from the saved genuine fitted no-Daypart artifact: same selected family/parameters/seed,1200training rows, six raw Daypart columns excluded. The ablated model is slightly better on validation, test and OOD; **no incremental predictive advantage from DaypartDNA is demonstrated**. It remains a contextual POI-derived opportunity proxy, not measured footfall. The ablation was not a retrospective selection candidate, and the selected full model was not changed.

Support is not a guarantee of prediction reliability under hidden parameter shift:

| Split | Joint-supported / rows | Joint-unsupported | Rows with any marginal-range warning |
| --- | ---: | ---: | ---: |
| validation | 397/400 | 3 | 4 |
| test | 396/400 | 4 | 6 |
| ood | 387/400 | 13 | 25 |

Thus387/400 shifted rows remain inside joint feature support despite degraded OOD performance. Their changed hidden decay/outside/theta parameters are not all observable model inputs. Keeping the global OOD warning is essential; a joint PASS cannot be interpreted as calibrated real-market accuracy.

## 8. Artifact and inference reproducibility

| Required file | Actual SHA256 | Verified |
| --- | --- | --- |
| catboost.joblib | `438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998` | PASS |
| feature_schema.json | `a4de657d927f22d9f44db34a829f7d9f6d7a02fa38937ba9125cf5946986059a` | PASS |
| support.json | `12a404bafdf9c36b8f27af05b2cf1bf2661a05486a700e3fed2818bc79b5e11f` | PASS |

The active selected filename is present in the verified hash map. Required20-feature schema/order and19capture-feature order match the saved wrapper. Training/inference transformations agree; saved separate preprocessing produces the same design as the wrapper. A fresh Python process loads the unchanged selected artifacts and reproduces the exact bytes of the ten raw prediction float64 values. Offline socket-denial inference checks pass. Installed versions match the artifact environment: numpy==2.5.2, pandas==2.3.3, scipy==1.18.1, scikit-learn==1.9.0, catboost==1.2.10, joblib==1.5.3.

This establishes saved-artifact integrity and deterministic local inference. It does not establish a fresh retraining run reproduces the same weights: the existing training-seed reproduction test was deliberately skipped because it calls CaptureModel.fit. The portable restoration test loads copied existing bytes into a temporary directory; it does not train or replace any original artifact.

## 9. Actual existing-test results

The instrumented unittest runner loaded `tests.unit.test_reference_sales_v2`, `tests.unit.test_decision_engine` and `tests.unit.test_finance`, with only B.2 test19 replaced in the temporary harness by an explicit SKIP. **55 total cases:52PASS,1FAIL,1ERROR,1SKIP, 6.289s.** Original source/tests were not decorated or edited. No API/contract-route suite was loaded. `ml.decision_engine.verify` and model/data report-writer entrypoints were not invoked, so original reports remain unchanged.

The instrumented command is saved in temporary test_results.json. Equivalent non-fitting model coverage can be selected from the existing unittest cases; a plain unrestricted full-suite invocation is not an acceptable reproduction command for this task because test19 retrains. Thread environment: OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1; PYTHONDONTWRITEBYTECODE=1.

Two unsuccessful historical assertions, preserved exactly:

1. **FAIL** `V2Acceptance.test_16_original_versions_and_public_contracts_unchanged`: preservation asserts the B.2 stage’s294-file inventory; it reports only `backend/app/domain/pipeline.py` changed. That seam was deliberately implemented in the later authorized C–G stage. This is a genuine current test failure with an outdated stage premise, not evidence that this verification changed it or that the model weights changed.
2. **ERROR** `V2Acceptance.test_17_offline_local_artifact_and_no_orchestration`: its actual local hashed-model prediction assertion succeeds, then it expects the old pipeline to raise NotImplementedError on `run_evaluation({}, {})`. Current implemented validation raises KeyError(project_id) for those empty inputs. The obsolete no-orchestration assertion fails; no HTTP/API route was tested. This also records a generic empty-input error-contract limitation rather than concealing it.
3. **SKIP** `V2Acceptance.test_19_selected_fit_reproducible_with_training_seed`: would call CaptureModel.fit and retrain. Deferred under the user restriction; historical prior success is not substituted for a current run.

The other16 B.2 cases pass, covering generator byte reproduction, allocation/target physics, wallet scaling, leakage, training preprocessing/support, metrics/selection, schemas, rejection, ablation and saved probe evidence. The36 current decision-engine/finance tests all pass again. Older v1/B.1 suites were not rerun as current-model gates; their reports and datasets were read for comparison.

| Exact existing test | Result |
| --- | --- |
| `V2Acceptance.test_01_counts_new_identity_and_no_split_overlap` | PASS |
| `V2Acceptance.test_02_all_targets_feasible_conserved_and_uncapped` | PASS |
| `V2Acceptance.test_03_simulator_wallet_scaling_and_competition` | PASS |
| `V2Acceptance.test_04_fitted_wallet_scaling_structural_all_candidates` | PASS |
| `V2Acceptance.test_05_candidate_usable_scaling_and_support_invariance` | PASS |
| `V2Acceptance.test_06_no_candidate_or_own_branch_label_leakage` | PASS |
| `V2Acceptance.test_07_train_only_preprocessing_and_fixed_support` | PASS |
| `V2Acceptance.test_08_validation_only_selection_and_actual_metrics` | PASS |
| `V2Acceptance.test_09_all_models_bounds_and_same_saved_transform` | PASS |
| `V2Acceptance.test_10_invalid_features_and_wrong_schema_rejected` | PASS |
| `V2Acceptance.test_11_unknown_joint_geometry_never_silently_usable` | PASS |
| `V2Acceptance.test_12_candidate_support_and_reference_endpoints` | PASS |
| `V2Acceptance.test_13_bad_reference_bracket_rejects_without_adjustment` | PASS |
| `V2Acceptance.test_14_full_generator_reproducibility` | PASS |
| `V2Acceptance.test_15_ablation_is_real_and_same_family_parameters` | PASS |
| `V2Acceptance.test_16_original_versions_and_public_contracts_unchanged` | FAIL |
| `V2Acceptance.test_17_offline_local_artifact_and_no_orchestration` | ERROR |
| `V2Acceptance.test_18_demand_shape_competition_and_daypart_probe_records` | PASS |
| `V2Acceptance.test_19_selected_fit_reproducible_with_training_seed` | SKIP |
| `ActualFittedBengaluru.test_actual_artifact_and_ten_site_end_to_end` | PASS |
| `ActualFittedBengaluru.test_actual_model_changes_boundary_diagnosis_and_selected_set` | PASS |
| `ActualFittedBengaluru.test_frozen_arrays_unchanged_by_joint_search` | PASS |
| `ActualFittedBengaluru.test_model_perturbation_changes_economics_not_only_label` | PASS |
| `ActualFittedBengaluru.test_portable_bundle_restores_inference_without_original_artifact_directory` | PASS |
| `AllocationChecks.test_calibration_and_unattainable_target` | PASS |
| `AllocationChecks.test_hand_calculated_shares_and_money_conservation` | PASS |
| `AllocationChecks.test_invalid_numerics_fail` | PASS |
| `AllocationChecks.test_own_branch_loss_deducted_once` | PASS |
| `AllocationChecks.test_wallet_scaling_and_competition` | PASS |
| `FailFastChecks.test_all_states_and_full_precedence` | PASS |
| `FailFastChecks.test_rent_threshold_oracle_and_no_rescue` | PASS |
| `FailFastChecks.test_sales_bounds_nonmonotonic_and_verified_root` | PASS |
| `GeometryAndDaypart.test_availability_override_and_duplicate_rejection` | PASS |
| `GeometryAndDaypart.test_dayparts_duration_and_frequency` | PASS |
| `GeometryAndDaypart.test_geodesic_metres_and_invalid_coordinates` | PASS |
| `GeometryAndDaypart.test_unknown_differs_from_supported_zero` | PASS |
| `PipelineChecks.test_demand_scale_and_zero_demand` | PASS |
| `PipelineChecks.test_future_effect_applied_once_with_frozen_model` | PASS |
| `PipelineChecks.test_missing_unsupported_and_invalid_inputs_fail_explicitly` | PASS |
| `PipelineChecks.test_pure_deterministic_immutable_pipeline_and_schema` | PASS |
| `PipelineChecks.test_rent_only_preserves_network_and_dayparts` | PASS |
| `PipelineChecks.test_rescue_does_not_clear_hard_failure` | PASS |
| `PipelineChecks.test_risk_acknowledgement_and_budget_source` | PASS |
| `PipelineChecks.test_stale_modified_and_missing_context_rejected` | PASS |
| `PipelineChecks.test_unattainable_target_is_review_not_silent_clipping` | PASS |
| `PortfolioChecks.test_all_1024_sets_and_independent_overlap_oracle` | PASS |
| `PortfolioChecks.test_forced_cutoff_is_truthful` | PASS |
| `PortfolioChecks.test_full_network_1024_sets_against_independent_cashflow_formula` | PASS |
| `PortfolioChecks.test_paise_budget_ties_and_empty_zero` | PASS |
| `TimingChecks.test_current_operational_cancelled_unknown_and_effect_signs` | PASS |
| `TimingChecks.test_midyear_and_delay_fraction` | PASS |
| `FinanceOracleTests.test_invalid_values_rejected` | PASS |
| `FinanceOracleTests.test_prd_cashflow_oracle` | PASS |
| `FinanceOracleTests.test_worked_sites_reverse_sales_order` | PASS |
| `FinanceOracleTests.test_zero_capex_and_no_recovery` | PASS |

| Targeted verification check (no model fitting) | Result |
| --- | --- |
| Feasible coherent targets train | PASS |
| Feasible coherent targets validation | PASS |
| Feasible coherent targets test | PASS |
| Feasible coherent targets ood | PASS |
| Grouped60/20/20 plus separate OOD | PASS |
| Active saved artifact hashes | PASS |
| Actual model identity and wallet exclusion | PASS |
| Training-only preprocessing reconstructed without fitting | PASS |
| Fixed training-only joint support independently reconstructed | PASS |
| All model metrics recomputed from fitted artifacts | PASS |
| Validation-only selection consistent with saved protocol | PASS |
| Daypart ablation verified from saved fitted artifact | PASS |
| All2400 fitted wallet perturbations preserve homogeneity | PASS |
| All10 Bengaluru support gates | PASS |
| Bengaluru50 adapter wallet perturbations | PASS |
| All10 target/reference roots attainable and finite | PASS |
| Showcase/own-company leakage absent from saved feature rows | PASS |
| Unsupported combination and infeasible supplied bracket rejected | PASS |
| Fresh-process deterministic inference | PASS |
| Runtime versions match recorded artifact environment | PASS |

A joblib/NumPy2.5 deprecated array-shape-assignment warning recurred. Numeric predictions/metrics remained consistent; the warning is retained in temporary evidence rather than suppressed as a passing-test claim.

## 10. Unresolved risks and interpretation

- **Real-world validation unavailable.** All training labels are synthetic allocation outputs. No comparable observed-store sales targets, candidate labels or calibrated intervals exist. Wallet feasibility and support do not measure actual sales accuracy or business lift.
- **OOD warning remains material.** Selected stress WAPE33.236204%,4.357× ordinary test WAPE; most shifted rows still pass feature support. Keep review/restrictions for matching unsupported regimes rather than weakening or rebranding support.
- **Automatic readiness contract unresolved.** Actual v2 records retain automatic_calibration_permitted=False. Prior offline-engine review documents that the consumer does not enforce that field or explicit hard integration blocks. Numerical feasibility verified here does not authorize silent policy promotion. Resolve the contract before automatic integration.
- **Regional/source assumptions.** Shared empirical templates, partial OSM coverage, assumed availability/category weights, historical2020 modelled population, nominal2023-24 state-urban spending, synthetic premises/areas and equal competitor mass limit transferability. Current support envelopes reflect those assumptions, not empirical calibration.
- **Geometry and price basis.** Synthetic1500m quadrature circles differ from actual100-cell whole-AOI centroid reference. Historical wallet prices and synthetic2026 commercial costs are not matched by an inflation conversion. No new assumptions or conversions were invented.
- **Daypart advantage not demonstrated.** All saved no-Daypart evaluations slightly outperform the full selected model. No predictive benefit, causal effect or measured store footfall claim is justified.
- **Historical tests not all green / refit reproduction deferred.** The two stage-specific failure/error cases must remain visible; test19 was not executed under this scope. Current saved inference is reproducible, while fresh-weight reproducibility was not newly established.
- **Separate C–G issues remain.** Rescue-application coordinate semantics, hard portfolio deadline and source/flag validation gaps in OFFLINE_ENGINE_REVIEW_REPORT.md were not fixed or reclassified by this model verification. Full application readiness is outside scope.

No active baseline model target, wallet response, or ten-site support/feasibility failure was found that warrants blocking the **restricted offline synthetic-model verification**. These limitations preclude an unqualified VERIFIED verdict or any real-sales/automatic-deployment claim.

## 11. File and Git safety

Before verification, SHA256 values were recorded for **365 existing project files**: datasets/source snapshots, source code, all saved model artifacts, tests and prior reports. All365 still match. Excluded locations are `.git`, `.runtime`, dependency/virtualenv/build/cache directories and the new report. The only new non-temporary deliverable is `PART_B_FINAL_VERIFICATION_REPORT.md`; optional evidence is under `.runtime/part-b-final-verification/`.

Branch remains `ML`, HEAD `adcabc63a1f15911d6f10afa3c1dc2a146c1468f`. The pre-existing uncommitted changes were preserved. No commit, push, branch switch, merge, rebase or PR; no CaptureModel.fit, sales-estimator refit, training entrypoint, tuning, artifact replacement, dataset overwrite, API route test, FastAPI/SQLite/Next.js integration, frontend or public-schema edit occurred.

Temporary evidence comprises baseline.json, test_results.json, verification_results.json and the review scripts. Controlled inference, in-memory generator reproduction, analytic preprocessing/support reconstruction and independent attraction roots wrote nothing to original datasets or artifacts. Stop here and wait for the next instruction.

**Final verdict: PART_B_OFFLINE_VERIFIED_WITH_LIMITATIONS.**
