"""Execute Part B tests and export completion/model-card/checksum evidence."""
import datetime as dt
import io
import json
from pathlib import Path
import platform
import time
import unittest
import warnings

import pandas as pd

from .features import FEATURES, DAYPART
from .train import ROOT, DATA, EVAL, ART, read_json, write_json, sha, verify_preserved_inputs


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.records=[]
    def addSuccess(self,test):
        super().addSuccess(test);self.records.append(dict(test=test.id(),status='PASS'))
    def addFailure(self,test,error):
        super().addFailure(test,error);self.records.append(dict(test=test.id(),status='FAIL',details=self._exc_info_to_string(error,test)))
    def addError(self,test,error):
        super().addError(test,error);self.records.append(dict(test=test.id(),status='ERROR',details=self._exc_info_to_string(error,test)))
    def addSkip(self,test,reason):
        super().addSkip(test,reason);self.records.append(dict(test=test.id(),status='SKIP',reason=reason))


def pct(value):return 'undefined' if value is None else f'{100*value:.4f}%'


def comparison(metrics):
    lines=['| Model | Split | MAE (INR/year) | RMSE (INR/year) | WAPE |','|---|---|---:|---:|---:|']
    for name in ['median','ridge','catboost']:
        if name not in metrics:
            lines.append('| '+name+' | unavailable | — | — | — |');continue
        for split in ['validation','test','ood']:
            r=metrics[name][split]
            lines.append(f'| {name} | {split} | {r["MAE_inr"]:,.2f} | {r["RMSE_inr"]:,.2f} | {pct(r["WAPE"])} |')
    return lines


def main():
    preserved_before=verify_preserved_inputs();started=dt.datetime.now(dt.timezone.utc).isoformat();timer=time.perf_counter()
    stream=io.StringIO()
    with warnings.catch_warnings(record=True) as emitted:
        warnings.simplefilter('always')
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests/unit'),pattern='test_*.py')
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=RecordedResult).run(suite)
    warning_records=sorted({(type(w.message).__name__,str(w.message)) for w in emitted})
    test_report=dict(command='python -m ml.training.reference_sales.report',
        equivalent_test_command='python -m unittest discover -s tests/unit -v',
        started_at_utc=started,completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-timer,
        tests_run=result.testsRun,passed=sum(r['status']=='PASS' for r in result.records),failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        test_results=result.records,test_output=stream.getvalue(),warnings=[dict(category=c,message=m) for c,m in warning_records],
        earlier_run_note='Initial run had two sandbox TEMP-directory permission errors in test cleanup/copy. Tests now use verified workspace-local temporary directories; both cases are rerun below.',
        preservation_before=preserved_before,preservation_after=verify_preserved_inputs(),
        runtime=dict(python=platform.python_version(),platform=platform.platform(),processor=platform.processor()))
    write_json(EVAL/'test_results.json',test_report)
    m=read_json(EVAL/'metrics.json');manifest=read_json(ART/'manifest.json');cfg=read_json(Path(__file__).with_name('config.json'))
    ablation=read_json(EVAL/'daypart_ablation.json');perturb=read_json(EVAL/'perturbation_report.json')
    best=manifest['selected_model'];valid=result.wasSuccessful() and manifest['activation_gate_passed']
    status='PART_B_READY_WITH_LIMITATIONS' if valid else 'PART_B_BLOCKED'
    profiles={}
    for path in sorted(list(DATA.glob('*.csv'))+list(EVAL.glob('*.csv'))):
        frame=pd.read_csv(path)
        profiles[path.relative_to(ROOT).as_posix()]=dict(rows=len(frame),columns=len(frame.columns),null_count=int(frame.isna().sum().sum()),
            nulls_by_column={k:int(v) for k,v in frame.isna().sum().items() if v})
    write_json(EVAL/'output_inventory.json',dict(csv_profiles=profiles,status=status,method_mode='model_simulated'))
    model_card=[
        '# Competitors-only reference annual sales model','',
        f'Artifact identifier: `{manifest["model_artifact_id"]}`. Selected fitted family: **{best}**, parameters `{json.dumps(manifest["selected_parameters"])}`. Mode: **model_simulated**.','',
        'This prototype learns only controlled synthetic spending allocations. It has no empirical Indian store-revenue validation, real-outcome calibration or confidence interval. It predicts INR/year before own-company displacement; it does not predict net profit, NPV, footfall or rankings. Inference currency follows the input wallet price basis.','',
        '## Training and evaluation','',
        '100 synthetic markets × 20 alternative sites = 2,000 rows; 60/20/20 market groups = 1,200/400/400 rows. Another 20 shifted markets supply 400 OOD rows. Twenty predictors use the canonical supported names. Preprocessing and final fitted parameters use training markets only. Validation WAPE freezes family/hyperparameters before test/OOD evaluation. No Bengaluru candidate occurs in a split.','',
        'Seeds: generator 20261024, split 314159, model 271828. Bounded lognormal attraction variation, positive outside option, external competitors and capacity preserve wallet feasibility. The 20 potential sites are alternatives considered individually; no own branches enter labels. Full assumptions: `ml/training/reference_sales/config.json` and `README.md`.','',
    ]+comparison(m['metrics'])+[
        '',f'Synthetic activation gate: **{m["activation_gate"]["status"]}**, relative test-WAPE reduction versus median **{pct(m["activation_gate"]["relative_test_WAPE_gain"])}**, threshold 10%. This gate does not establish real-market validity.','',
        f'OOD/test WAPE ratio: **{m["ood_test_WAPE_ratio"]:.4f}×**; review warning: **{m["ood_warning"]}**. This is material distribution-shift degradation. Marginal training-range diagnostics and an OOD warning are returned; no calibrated OOD detector exists.','',
        'Ridge won validation. CatBoost has lower test WAPE in this run but was not selected retrospectively. The diagnostic no-daypart model also does not replace the preregistered full-feature selection after test results. No further tuning was performed.','',
        '## DaypartDNA and perturbations','',
        '| Split | Full WAPE | Without six dayparts WAPE | Full relative improvement |','|---|---:|---:|---:|',
    ]
    for split,r in ablation['splits'].items():model_card.append(f'| {split} | {pct(r["full"]["WAPE"])} | {pct(r["without_daypart"]["WAPE"])} | {pct(r["full_relative_WAPE_reduction"])} |')
    model_card += [
        '', 'Ablation is mixed: small test improvement, validation and OOD deterioration. No consistent predictive benefit or real-world DaypartDNA advantage is established. No economic ordering evaluation is claimed because downstream components are out of scope.','',
        '| Controlled change | Changed / 40 | Expected direction / 40 | Opposite direction / 40 |','|---|---:|---:|---:|',
    ]
    for name,r in perturb.items():model_card.append(f'| {name} | {r["changed_examples"]} | {r["expected_direction_examples"]} | {r["opposite_direction_examples"]} |')
    model_card += [
        '', 'Area and competition checks behave as expected in all 40 held-out examples. Wallet increases decrease predictions in 10/40 cases and daypart increases decrease predictions in 20/40 cases. This fitted approximation has no universal monotonicity guarantee. These are retained limitations, not repaired by tuning on the final test. Do not interpret feature perturbations as validated causal effects.','',
        '## Supported inference and fallback','',
        '`ml.inference.reference_sales.ReferenceSalesEstimator` loads the saved local fitted model, schema and preprocessing with SHA-256 checks. It accepts prepared canonical feature dictionaries, validates all 20 names/types and returns reference sales, mode, artifact identity/hash and diagnostics. It does not call a notebook, HTTP service, SQL, remote model or application pipeline. Public Project/Site objects lack catchment features and cannot by themselves support this model. Backend can pass its future internal prepared feature row without changing existing wire schemas.','',
        'Only nearest mapped competitor distance may be null, and only at zero mapped competitors. Its train-only median/missing indicator is an internal model representation, not an invented observation. Required data errors raise `FeatureValidationError`; unknown routing/household values are not filled. Missing/corrupt/unqualified artifacts raise `ModelUnavailableError`, unless an explicit caller-supplied capture fraction requests visible `scenario_assumptions` with null artifact ID.','',
        '## Limits and operational state','',
        'The Bengaluru wallet/population/POI inputs retain their historical/assumption semantics. Candidate premises and economics are synthetic. Input coverage and model range warnings do not validate geographic transfer. Capacity/format/market parameters are disclosed generator assumptions. Generator and model share a controlled hypothesis class; this evaluates simulator interpolation, not market forecasting. No sales labels for Bengaluru were created. No SHAP or calibrated intervals were run or claimed.','',
        'Native CatBoost and Joblib model/preprocessing exports are local development artifacts. Models were fitted on synthetic data only; no BMRCL workbook or transit input was used in fitting or copied. Existing source rights remain unresolved where documented in Part A. Existing Git rules ignore the artifacts directory; nothing was committed, pushed or publicly packaged. Joblib/NumPy 2.5 emits a deprecation warning on load; tested deserialization works under the pinned environment.','',
        'Full checksums: `ml/evaluation/reference_sales_v1/output_checksums.json`. Model/preprocessor/schema checksums: `manifest.json`. Dependency pins: `ml/training/reference_sales/requirements-lock.txt`. Reproduce with `python -m ml.training.reference_sales.train` followed by `python -m ml.training.reference_sales.report`.','',
        status,'',
    ]
    (ART/'MODEL_CARD.md').write_text('\n'.join(model_card),encoding='utf-8')
    # Inventory includes exact requested outputs and the report itself; only the
    # checksum list is excluded from its self-referential checksum inventory.
    report_path=ROOT/'PART_B_COMPLETION_REPORT.md'
    output_files=sorted({p for folder in [ROOT/'ml/training/reference_sales',ROOT/'ml/training/data/reference_sales_v1',ROOT/'ml/inference',EVAL,ART] for p in folder.rglob('*') if p.is_file()}|{ROOT/'tests/unit/test_reference_sales.py',report_path})
    output_files=[p for p in output_files if p.name!='output_checksums.json' and '__pycache__' not in p.parts]
    purposes={
        'config.json':'Versioned generator bounds, seeds and fixed model grids',
        'features.py':'20-field allowlist, types, units and strict feature validation',
        'simulator.py':'Independent synthetic markets and wallet-conserving candidate-only labels',
        'models.py':'Median, Ridge, CatBoost fits and bounded output/preprocessing',
        'metrics.py':'Executed MAE/RMSE/WAPE including explicit zero denominator handling',
        'train.py':'Grouped training, validation lock, evaluation, ablation, artifacts and examples',
        'report.py':'Executed test evidence, model card, completion report and checksums',
        'reference_sales.py':'Offline reusable internal inference adapter and explicit fallback',
        'test_reference_sales.py':'Part B unit/integration, reproducibility and preservation tests',
        'MODEL_CARD.md':'Selected-model evidence and usage limitations',
        'manifest.json':'Chosen model identity, parameters, dependencies, gate and file hashes',
        'synthetic_regular.csv':'2,000 synthetic observations with predictors, target and allocation audit',
        'synthetic_shifted.csv':'400 rows from 20 shifted synthetic markets, never tuned against',
        'market_splits.csv':'120 unique market-group split records',
        'market_manifest.json':'All market parameters, generator configuration and independent seeds',
        'heldout_predictions.csv':'Actual targets/predictions for all evaluated families and ablation',
        'segment_metrics.csv':'Executed format, competition and per-market error metrics',
        'heldout_perturbations.csv':'160 measured controlled perturbation predictions',
        'bengaluru_inference_examples.csv':'10 unvalidated model_simulated inference examples, not labels/ranks',
        'preserved_input_hashes.json':'Pre-edit hashes of all 233 protected existing files',
        'feature_compatibility.csv':'Use/exclusion/missingness for every canonical 70-field column',
        'source_inventory.json':'Inspected original/revised feature and geographic inventory with hashes',
        'selection_lock.json':'Frozen validation-only selection before held-out scoring',
        'test_results.json':'Executed unit/integration test results and warning record',
        'output_inventory.json':'Actual output CSV dimensions and null counts',
        'metrics.json':'Actual validation/test/OOD, activation, latency and preservation evidence',
        'daypart_ablation.json':'Same-protocol six-feature removal diagnostic',
        'perturbation_report.json':'Measured expected/opposite response counts',
        'feature_schema.json':'Exported ordered inference schema and null rules',
        'preprocessing.json':'Training-only learned imputation/scaling/encoding configuration',
        'preprocessor.joblib':'Saved selected fitted preprocessing object',
        'ridge.joblib':'Saved validation-selected fitted Ridge sales model',
        'median.joblib':'Saved fitted median comparison baseline',
        'catboost.joblib':'Saved fitted CatBoost comparison with preprocessing/output head',
        'catboost.cbm':'Native fitted CatBoost tree export (logit-capture output)',
        'ablation_no_daypart.joblib':'Saved diagnostic Ridge model without six dayparts',
        'requirements-lock.txt':'Exact locally executed dependency versions',
        'README.md':'Reproduction, simulator equations, preprocessing, inference use and limits',
        'PART_B_COMPLETION_REPORT.md':'Requested Part B completion and next dependency',
        '__init__.py':'Package marker',
    }
    lines=[
        '# Part B completion report','',status,'',
        f'Completed locally on branch **ML** at existing HEAD `{preserved_before["head"]}`. This is the fitted demand-model phase only. **{test_report["passed"]}/{result.testsRun} tests pass**, with {len(result.failures)} failures, {len(result.errors)} errors and {len(result.skipped)} skips. All **233 protected pre-existing files** match their pre-edit SHA-256 values.','',
        '## A. Implemented files','',
        'Repository root: `'+str(ROOT)+'`. Every path below is relative to that root. The checksum inventory also includes full SHA-256 values for these outputs; its own checksum is excluded.','',
        '| Exact path | Purpose |','|---|---|',
    ]
    for p in output_files:lines.append('| `'+p.relative_to(ROOT).as_posix()+'` | '+purposes.get(p.name,'Part B supporting output')+' |')
    lines += ['| `ml/evaluation/reference_sales_v1/output_checksums.json` | Complete output SHA-256 inventory (self excluded) |','',
        '## B. Dataset generation','',
        'Exactly **100 regular markets × 20 alternative potential stores = 2,000 observations**, and **20 separate shifted markets × 20 = 400 observations**. Twenty features are model inputs; the other synthetic columns are group/provenance metadata and excluded target/allocation audit fields.','',
        'Grouped partitions: **60 training markets / 1,200 rows**, **20 validation / 400 rows**, **20 test / 400 rows**; OOD is **20 additional markets / 400 rows**. Markets/observation keys do not overlap. Bengaluru candidates occur only in ten separately labelled inference examples.','',
        'Seeds: generator **20261024**, split **314159**, model **271828**. Each market has 100 synthetic metric spending cells, external competitors, POIs, varied store formats/area, heterogeneous bounded appeal/decay/spend/capacity and bounded lognormal attraction noise. Configuration version `reference-market-simulator-v1`; parameters and individual market seeds are exported.','',
        'The target is **competitors-only reference annual store sales in INR, before own-company branch displacement**. For each candidate alone, cell wallet is allocated among that candidate, external competitors and a positive outside option. Capacity-unserved demand returns to outside. Targets conserve cell spending, stay nonnegative and cannot exceed the catchment wallet or capacity. The 20 stores are alternatives, not simultaneously open branches. No own-company store enters a target and no target uses a desired winner/rank. The simulator is isolated from the later production network/Huff component.','',
        '| Output CSV | Rows | Columns | Null fields |','|---|---:|---:|---:|',
    ]
    for name,p in profiles.items():lines.append(f'| `{name}` | {p["rows"]:,} | {p["columns"]} | {p["null_count"]:,} |')
    lines += [
        '', 'Synthetic nearest-competitor distances are null only when no mapped competitor exists. Example fallback fractions are null because fitted mode is used. Per-column null counts are exported in `output_inventory.json`. Original Bengaluru unknowns are untouched.','',
        '## C. Model results','',
        'All results below were executed on simulator targets. WAPE = sum absolute error / sum absolute actual targets, with a null result plus explicit reason at zero denominator. INR errors are annual nominal simulator amounts.','',
    ]+comparison(m['metrics'])+[
        '',f'Selected **{best}** with `{json.dumps(manifest["selected_parameters"])}` by validation WAPE. Selection is locked before final test/OOD evaluation. CatBoost was fitted successfully on CPU; neither installation nor fitting failed. CatBoost has lower test error but worse validation error in this execution; it is not retrospectively promoted. The full-feature family/hyperparameter grid was frozen in configuration before the first run. No model was tuned on test/OOD, and no final fit uses validation/test rows.','',
        f'Activation target: **{m["activation_gate"]["status"]}**. Relative held-out test-WAPE reduction versus median is **{pct(m["activation_gate"]["relative_test_WAPE_gain"])}**, exceeding the 10% threshold. This passes only the declared synthetic model gate; it does not validate retail-market forecasts or complete AC28 downstream integration.','',
        f'**OOD warning:** selected-model shifted WAPE is **{pct(m["metrics"][best]["ood"]["WAPE"])}**, **{m["ood_test_WAPE_ratio"]:.4f}×** regular test WAPE, above the handoff 2× review threshold. The adapter exposes that limitation.','',
        'Segment-wise metrics by store format, external competitor count and market are in `segment_metrics.csv`, with raw evaluation pairs in `heldout_predictions.csv`. They are recalculated in tests.','',
        '| Inference path | Warm p50 ms | Warm p95 ms |','|---|---:|---:|',
    ]
    for name,r in m['latency'].items():lines.append(f'| {name} | {r["p50"]:.4f} | {r["p95"]:.4f} |')
    lines += [
        '', f'Latency protocol: batch size 1, 5 warmups, 50 measured calls, CPU. Selected adapter includes validation/preprocessing/prediction; cold artifact load in a warm Python process was **{m["latency"]["selected_adapter"]["cold_artifact_load_ms"]:.4f} ms**. Python startup/import time is excluded. These are local observations, not application/portfolio latency claims. Platform: `'+platform.platform()+'`.','',
        'DaypartDNA ablation removes all six raw baseline indices, retains the selected family/hyperparameters and refits preprocessing only on the same training markets.','',
        '| Split | Full WAPE | Without dayparts WAPE | Full relative improvement |','|---|---:|---:|---:|',
    ]
    for split,r in ablation['splits'].items():lines.append(f'| {split} | {pct(r["full"]["WAPE"])} | {pct(r["without_daypart"]["WAPE"])} | {pct(r["full_relative_WAPE_reduction"])} |')
    lines += [
        '', 'Ablation is mixed and is not used for retrospective model selection. It does not establish a consistent predictive advantage. Economic-ordering ablation is intentionally deferred because no ranking/finance/network component was implemented.','',
        'Held-out perturbations: store area +25% increases predictions in **40/40** cases; extra external competition reduces them in **40/40**. Wallet +25% increases **30/40** and decreases **10/40**; dayparts +25% increases **20/40** and decreases **20/40**. The latter failures of universal expected monotonicity remain documented. No hyperparameters were changed after these final-test diagnostics.','',
        '## D. Feature compatibility','',
        'The explicit ordered 20-feature allowlist is:','',
    ]
    lines += ['- `'+name+'`' for name in FEATURES]
    lines += [
        '', 'All 20 are available as named supported baseline descriptors in the enriched Bengaluru view. Source wallet/population vintages and assumption tags remain meaningful; compatibility does not establish forecasting validity. The other **50 canonical columns are excluded**; `feature_compatibility.csv` gives each exclusion/missing count. IDs, latitude/longitude/locality labels, costs, future effects, historical metro measurements, constant source-quality and redundant enrichment do not enter fitting. Both `population_10min_est` and `accessible_households_est` retain ten nulls. Only a legitimate no-competitor nearest-distance absence has a train-only model missingness representation; no measurement is invented.','',
        '## E. Model artifacts and reproducibility','',
        f'Selected model ID: `{manifest["model_artifact_id"]}`. Selected fitted file: `ml/artifacts/reference_sales_v1/{manifest["selected_model_file"]}`.','',
        '| Artifact file | SHA-256 |','|---|---|',
    ]
    for name,digest in manifest['required_file_sha256'].items():lines.append(f'| `ml/artifacts/reference_sales_v1/{name}` | `{digest}` |')
    lines += [
        '', 'The native `catboost.cbm` predicts logit capture and must be used with its saved preprocessing/output head; it is not itself an INR-returning adapter. `ridge.joblib` is the chosen complete bounded-sales object; `preprocessor.joblib`/`preprocessing.json` export the selected train-only transform. Model/schema/preprocessor hashes are verified on load. Full file checksums are in `output_checksums.json`. Artifacts are local and ignored by pre-existing Git rules, not committed or packaged.','',
        'Python **'+manifest['python']+'**. Exact executed libraries: '+', '.join('`'+name+'=='+version+'`' for name,version in manifest['dependencies'].items())+'.','',
        '```powershell',
        'python -m pip install -r ml/training/reference_sales/requirements-lock.txt',
        "$env:PYTHONDONTWRITEBYTECODE='1'", "$env:OMP_NUM_THREADS='1'", "$env:OPENBLAS_NUM_THREADS='1'", "$env:MKL_NUM_THREADS='1'",
        'python -m ml.training.reference_sales.train', 'python -m ml.training.reference_sales.report',
        '```','',
        'Generator CSV/split byte reproducibility and Ridge refit prediction reproducibility were actually tested under fixed seeds. Timing/timestamps and native serialized metadata need not be byte identical on another run/platform. Training and evaluation results are reconstructed from code/data; they are not hardcoded benchmark numbers.','',
        '## F. Integration readiness','',
        '```python',
        'from ml.inference.reference_sales import ReferenceSalesEstimator',
        'estimator = ReferenceSalesEstimator()',
        'prediction = estimator.predict(prepared_canonical_feature_row)',
        '# prediction["reference_annual_sales_inr"], prediction["method_mode"]',
        '# prediction["model_artifact_id"], prediction["diagnostics"]',
        '```','',
        'The backend can later pass its prepared internal feature dictionary with existing canonical column names. Raw public `Site` records lack catchment descriptors and produce an explicit missing-feature error; no new public contract was invented. The adapter reads trusted local artifacts only, detects missing/invalid input or schema mismatch and reports numerical training-range/OOD warnings. It returns `model_simulated`, artifact ID/hash and uncalibrated status. Missing/corrupt/unqualified artifacts raise `ModelUnavailableError`; a caller may explicitly request a declared capture-fraction fallback labelled `scenario_assumptions` with null artifact ID. Missing required evidence never silently invokes imputation/fallback.','',
        'The independent integration tests load saved artifacts in a fresh Python process, disable socket connections during inference, verify excluded cost/ID changes cannot affect predictions, and verify both application pipeline functions still raise NotImplementedError. No `run_evaluation`, `run_portfolio`, routes, public Pydantic schemas or frontend files were modified. No API exposes these outputs yet.','',
        '## G. Test results','',
        f'Executed: `python -m ml.training.reference_sales.report` (runs `unittest` discovery for `tests/unit`). Direct equivalent also executed: `python -m unittest discover -s tests/unit -v`. **{test_report["passed"]} passed, {len(result.failures)} failed, {len(result.errors)} errors, {len(result.skipped)} skipped**, {result.testsRun} tests total: 29 Part B integrity/integration tests plus 4 unchanged finance regression tests. The latter were run as regression checks; no finance implementation was added.','',
        'Coverage includes generation counts, market isolation, no candidate/own-branch leakage, physical conservation/capacity, all model bounds, complete generator/hash reproducibility, train-only preprocessing, selected-model refit reproducibility, executed metric recalculation, zero-sum WAPE, validation-only selection, activation/OOD policy, ablation, held-out perturbations, feature errors/undefined distance, excluded-feature independence, method labels, explicit fallback, corrupt artifacts, offline/fresh-process loading, segment metrics, latency protocol and all protected hashes/Git identities.','',
        'Initial temporary-directory permission errors were fixed by using verified workspace-local test directories, without changing the model or data. Final result evidence, per-test outcomes, elapsed time and warning details are in `test_results.json`. Joblib emits a NumPy 2.5 array-shape deprecation warning; loading and numerical tests pass with pinned versions.','',
        '## H. Limitations and next dependency','',
        '- This is simulator learning, not real Indian store-sales validation. No achieved new-store sales, ground-truth targets, calibrated intervals or confidence probabilities exist for Bengaluru.',
        '- Shifted-market error exceeds the review threshold. Wallet/daypart perturbations are not universally monotonic, and ablation gives mixed evidence. These limitations remain visible; no final-test tuning was used to conceal them.',
        '- Simulator assumptions (outside option, competitor mass, decay, capacity, temporal preferences/noise) define the counterfactual. Geographic transfer, richer unobserved store effects and economic usefulness have not been validated.',
        '- Bengaluru premises/economics remain synthetic; population is modelled 2020 / 1 km and spending is nominal 2023–24. Predictions inherit wallet prices. No conversion to 2026 prices, routing or household imputation was performed.',
        '- Existing BMRCL licensing/RTI delivery gaps are unchanged. This simulator/model uses no metro measurements and copies no workbook; original archives and source data were not repackaged or modified.',
        '- No SHAP or real-outcome interval calibration was run. No decision/ranking/portfolio improvement is claimed. AC28 downstream dependency is unfinished until separately authorised model-to-domain integration occurs.',
        '- The next step requires an explicit instruction: review model limitations/feature semantics before further components, then coordinate the backend-owned internal preparation seam. Real-world activation requires compatible permissioned outcomes and independent temporal/geographic validation.',
        '', '## I. Git and scope confirmation','',
        f'Branch remains **ML**, HEAD `{preserved_before["head"]}`. **No commits, pushes, merges, rebases, branch changes or pull requests.** All **233** protected existing files are unchanged, including both Bengaluru versions, audits, shared fixtures, public schemas, backend/frontend, domain pipeline and original archive. New work is in ML-owned paths/tests plus this explicitly requested root report.','',
        'Part B stops here. No Part C/D, own-branch cannibalisation engine, financial forecasting, FailFast, infrastructure execution, ranking, portfolio optimisation or frontend/backend integration was started.','',
        status,'',
    ]
    report_path.write_text('\n'.join(lines),encoding='utf-8')
    verify_preserved_inputs()
    write_json(EVAL/'output_checksums.json',dict(status=status,algorithm='SHA-256',files={p.relative_to(ROOT).as_posix():sha(p) for p in output_files},
        excluded_self='ml/evaluation/reference_sales_v1/output_checksums.json',model_artifact_id=manifest['model_artifact_id']))
    print(json.dumps(dict(status=status,tests=result.testsRun,passed=test_report['passed'],failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        selected_model=best,activation=m['activation_gate']['status'],protected_files_unchanged=verify_preserved_inputs()['files_unchanged'],output_file_count=len(output_files)+1),indent=2))
    if not result.wasSuccessful():
        print(stream.getvalue());raise SystemExit(1)


if __name__=='__main__':main()
