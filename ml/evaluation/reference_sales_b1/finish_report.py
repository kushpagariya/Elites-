"""Execute focused tests and write the requested B.1 report, preserving v1."""
import datetime as dt
import io
import json
import unittest
import warnings
import pandas as pd
from .run_hardening import ROOT,OUT,OLD,POLICY,EV,read,save,sha,preserve


class Result(unittest.TextTestResult):
    def __init__(self,*a,**k):super().__init__(*a,**k);self.records=[]
    def addSuccess(self,t):super().addSuccess(t);self.records.append(dict(test=t.id(),status='PASS'))
    def addFailure(self,t,e):super().addFailure(t,e);self.records.append(dict(test=t.id(),status='FAIL',error=self._exc_info_to_string(e,t)))
    def addError(self,t,e):super().addError(t,e);self.records.append(dict(test=t.id(),status='ERROR',error=self._exc_info_to_string(e,t)))


def main():
    stream=io.StringIO()
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always')
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests/unit'),pattern='test_reference_sales_b1.py')
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
    save(OUT/'test_results.json',dict(command='python -m ml.evaluation.reference_sales_b1.finish_report',
        equivalent='python -m unittest discover -s tests/unit -p test_reference_sales_b1.py -v',
        completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),tests_run=result.testsRun,
        passed=sum(r['status']=='PASS' for r in result.records),failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        results=result.records,output=stream.getvalue(),
        initial_run=dict(passed=19,failed=1,reason='Test incorrectly asserted all regular observations were capped; 3 validation observations are uncapped. Corrected scope to actual training/test/OOD findings, retaining the uncapped-validation check.'),
        warnings=sorted({str(n.message) for n in notes}),preservation=preserve()))
    summary=read(OUT/'diagnostic_summary.json');coeff=read(OUT/'coefficient_diagnosis.json');cap=read(OUT/'capacity_audit.json')
    support=read(OUT/'bengaluru_support.json');policy=read(POLICY/'manifest.json');old=read(EV/'metrics.json')
    pert=pd.read_csv(OUT/'controlled_perturbations.csv');questionable=pert[pert.assessment.str.startswith('QUESTIONABLE')]
    threshold=read(POLICY/'support_policy.json')['training_squared_distance_p99']
    inside=int((questionable.modified_joint_support_score<=threshold).sum())
    status='PART_B_INTEGRATION_BLOCKED'
    lines=[
        '# Part B.1 reference-sales hardening report','',status,'',
        'The existing Ridge is preserved and **not replaced or retrained**. Engineering guards are implemented, but automatic downstream integration is blocked by simulator target degeneration, non-monotonic wallet responses and unsupported Bengaluru transfer. This is a completed focused audit/hardening task; it is not approval to build later components.','',
        '## Existing model and selection verification','',
        'Base artifact: `reference-sales-sim-v1-3f162d1da91a`, Ridge alpha 20. Model SHA-256: `'+sha(OLD/'ridge.joblib')+'`. Selection-lock records and training source confirm minimum validation WAPE selection before test/OOD scoring. No B.1 fitting, hyperparameter change or model selection occurred. Original metrics, ablation, model card, datasets and fitted preprocessing/weights remain unchanged.','',
        '| Model | Validation WAPE | Test WAPE | OOD WAPE |','|---|---:|---:|---:|',
    ]
    for name in ['median','ridge','catboost']:
        r=old['metrics'][name];lines.append(f'| {name} | {r["validation"]["WAPE"]:.6%} | {r["test"]["WAPE"]:.6%} | {r["ood"]["WAPE"]:.6%} |')
    lines += [
        '', 'Ridge and CatBoost test/OOD values were recomputed from saved models and original rows, matching the recorded WAPE. CatBoost remains a comparison artifact. Synthetic evaluation does not establish real retail sales accuracy. The historical 33/33 Part B result is preserved as historical evidence, not overwritten by this task.','',
        '## Root cause: target saturation and non-monotonic wallet response','',
        '| Split | Rows | Capacity-bound targets | Uncapped targets |','|---|---:|---:|---:|',
    ]
    for name,r in cap.items():lines.append(f'| {name} | {r["rows"]} | {r["capped_rows"]} | {r["uncapped_rows"]} |')
    lines += [
        '', '**All 1,200 training targets equal area × hidden market capacity density.** All test and OOD targets are also capacity-bound; only three validation observations are uncapped. Therefore training labels have no remaining direct response to wallets, competition, access or daypart utility once capacity binds. The simulator contains those allocation mechanisms, but capacity cancels their target effect in every training example. The original WAPE improvement largely measures learning the capacity/area relationship; it cannot demonstrate a fitted geographic demand response.','',
        'The fitted capture head has `R = W × sigmoid(z)` and `z = a + b × log1p(W)` with other features held constant. The effective original-unit coefficient is **b = '+str(coeff['wallet_effective_log_coefficient'])+'**. Exact wallet elasticity is `1 + (1-sigmoid(z)) × b × W/(1+W)`. A constant negative capture-head slope slightly below -1 makes this negative at sufficiently low capture fractions. Finite-difference tests verify the derivative. This is a misspecified fitted capture relationship, not an arithmetic/scaling bug. In a genuinely capacity-limited allocation, extra spending should plateau, not lower store sales.','',
        'High feature correlation also limits interpretation: the largest recorded daypart correlation is '+str(coeff['top_absolute_correlations'][0]['correlation'])+'. The saved scaler was inverted analytically and training/inference transformations agree exactly. Correlated POI/daypart descriptors, omitted market capacity and capture normalisation make coefficients conditional statistical effects, not causal effects. No universally positive daypart or store-size relationship is imposed.','',
        f'**{len(pert):,} controlled probes** cover 400 held-out synthetic rows and all ten unlabelled Bengaluru rows: wallet increases/decreases, competition, area, each daypart independently and near/outside training ranges. **{len(questionable)} questionable responses** occurred; **{inside}** are within the empirical joint-support threshold, so the problem is not solely extrapolation. Exact original/modified feature dictionaries, predictions, direction, magnitude and classification are in `controlled_perturbations.csv`.','',
        '| Perturbation | Questionable cases |','|---|---:|',
    ]
    for name,count in questionable.groupby('perturbation').size().items():lines.append(f'| {name} | {count} |')
    lines += [
        '', 'All 410 competition additions lower predictions. Individual daypart changes are recorded as context-dependent coefficient effects without assuming a positive sign. No Bengaluru example has negative local wallet elasticity at its original input, but that does not validate its forecast or surrounding response surface.','',
        '## Hardening changes and interface','',
        '- `ml/inference/reference_sales.py`: retains existing entrypoint, feature names, selected model and method mode; validates saved units/types/null rules; uses the exact saved preprocessing and exposes the unadjusted saved output head before legacy clipping.',
        '- `ml/inference/reference_sales_safety.py`: reports raw prediction, INR/year units, input spending wallet, capture fraction, explicit no-adjustment rule, local wallet elasticity, support warnings and integration status. Negative/nonfinite or wallet-infeasible raw results cannot become usable predictions. No value is silently clipped or repaired.',
        '- Every response has `usable_for_automatic_integration=False`. Valid numerical outputs with the degenerate-target policy have `integration_status="INTEGRATION_BLOCKED"`; invalid/bound-violating outputs are `UNAVAILABLE` with a null usable result and the raw finite result retained. This guard is an internal seam, not a public Pydantic schema change or FailFast implementation.',
        '- Optional `predict(row, reference_wallet_bound_inr=...)` / batch `reference_wallet_bounds_inr` accepts a caller-established reference-pool bound. A failed bound rejects the usable result transparently; passing it remains a necessary-condition check, not a calibration certificate.',
        '- `ml/artifacts/reference_sales_b1/` contains separate support-policy metadata, not revised model weights. Policy ID: `'+policy['hardening_policy_id']+'`. SHA-256: `'+policy['support_policy_sha256']+'`. It is tied to the unchanged Ridge checksum.',
        '- Empirical joint support uses the original training-only transformed design, mean and pseudoinverse covariance with a fixed training 99th-percentile squared-distance threshold. No preprocessing/model is refitted and no validation/test/OOD outcome chooses that threshold. It is an empirical support rule, never a calibrated probability or confidence interval.',
        '- Missing required evidence remains an error. The only missing predictor representation is the pre-existing declared nearest-competitor absence with zero competitors. Explicit caller-requested fallback remains visibly `scenario_assumptions`, with null model artifact identity and no automatic integration permission.','',
        '## Reference-sales feasibility boundary','',
        'The target remains competitors-only reference annual store sales before own-company displacement. All 2,400 original synthetic rows and the ten Bengaluru examples have finite, nonnegative raw predictions within their supplied catchment wallets. Units are INR/year and price basis is inherited from the input wallet; no price conversion or household/routing imputation occurs. Spending wallet and store revenue are separate fields.','',
        'Wallet bounds alone cannot prove later Huff feasibility. With aligned positive cell wallets and finite positive external/outside terms, a scalar attraction can span the interior wallet range in an unbounded theoretical reference. The specified theta bracket [-30,30], actual cell accessibility, competitors/outside denominator and wallet alignment can still make a requested target unattainable. Those inputs and the later calibrator are not implemented here. All valid responses therefore explicitly say reference allocation feasibility is **UNVERIFIED**. No production Huff engine, bisection or own-branch displacement calculation was added.','',
        'The Bengaluru support records also check the full existing AOI spending-grid total as a necessary global upper bound. That grid is not identical to the circular raster catchment, so it is not used as an invented catchment measurement or a calibration certificate. Later integration must check requested versus achievable target in its actual fixed reference and expose any adjustment; this task performs no adjustment.','',
        '## Bengaluru support and shifted markets','',
        'All ten Bengaluru records pass the existing feature/type checks and numerical wallet bounds. **All ten lie beyond the new empirical joint-support threshold**, and each has at least one marginal range violation. Actual ten-site revenues do not exist: no accuracy metric, sales label or ranking is computed for them.','',
        '| Site | Raw reference INR/year | Local wallet elasticity | Marginal range violations |','|---|---:|---:|---|',
    ]
    for r in support:lines.append(f'| {r["site_id"]} | {r["raw_reference_annual_sales_inr"]:,.2f} | {r["wallet_local_elasticity"]:.6f} | '+', '.join(r['outside_marginal_features'])+' |')
    lines += [
        '', 'These are unvalidated diagnostic outputs, not achieved store sales or investment recommendations. Per-feature original values, training minima/maxima and empirical percentiles are in `bengaluru_feature_ranges.csv`; full support/feasibility/warning records are in `bengaluru_support.json`. Historical 2020 population, 2023–24 wallet prices and synthetic premises remain as documented in Part A.','',
        'OOD is a joint covariate and target-relationship shift: wallets/population/competition/POIs increase, allocation decay/outside attraction change, appeal decreases, and hidden capacity density falls from the configured 90,000–160,000 to 65,000–100,000 INR/sqm/year range. Exported `shift_parameters.json` gives executed market distributions; this is not a causal apportionment among simultaneous changes. Because every OOD target is capacity-bound, altered hidden capacity—not unconstrained spending—is decisive for actual targets.','',
        'Median actual capture falls from about 3.000% in test to 0.414% OOD. Ridge predicts median OOD capture about 0.613%; CatBoost about 1.091%. Mean OOD overprediction is about INR 17.0 million and INR 57.8 million respectively. CatBoost trees extrapolate poorly beyond trained relationships; Ridge partially scales capture with wallet but cannot infer the shifted hidden capacity. Thus CatBoost WAPE can exceed 100% despite satisfying a much larger wallet upper bound. These are observed associations under the disclosed simulator, not real-world validation or proof of one-feature causation.','',
        'Original mixed daypart ablation results are preserved. Given training target saturation, they cannot establish an economic DaypartDNA benefit. No new weights or hyperparameters were developed using final test/OOD results.','',
        '## Tests, preservation and Git','',
        f'Final focused engineering suite: **{sum(r["status"]=="PASS" for r in result.records)}/{result.testsRun} passed; {len(result.failures)} failures; {len(result.errors)} errors; {len(result.skipped)} skipped**. Results and full names/output: `ml/evaluation/reference_sales_b1/test_results.json`. The first run had 19 passes and one failed overbroad assertion about all regular rows being capped; the three uncapped validation rows were retained and the test corrected to the actual training/test/OOD finding.','',
        'Behavioral gates remain **FAIL** for wallet monotonicity, informative/nondegenerate training targets and Bengaluru joint support. Finite-theta feasibility is not certified. Passing engineering tests verifies that these risks are detected and exposed; it does not override the failed integration gates.','',
        'Test coverage: local loading; exact model identity; schema/errors; INR/year; finite/nonnegative and wallet bounds; explicit invalid-output rejection; raw retention/no clipping; wallet analytic/finite-difference agreement; competition/daypart probes; original preprocessing; ten-site compatibility; empirical OOD warnings; deterministic loading; original artifact preservation; offline operation; visible fallback; unchanged backend orchestration stubs and contracts. Existing Joblib/NumPy array-shape deprecation warnings remain recorded, without numerical failures.','',
        'Reproduce without training or rewriting Part B outputs:','',
        '```powershell',"$env:PYTHONDONTWRITEBYTECODE='1'", "$env:OMP_NUM_THREADS='1'", "$env:OPENBLAS_NUM_THREADS='1'", "$env:MKL_NUM_THREADS='1'",
        'python -m ml.evaluation.reference_sales_b1.run_hardening',
        'python -m ml.evaluation.reference_sales_b1.finish_report',
        '```','',
        'All **273 pre-existing files** are checked: 272 remain byte-identical in place; the one revised adapter has its exact original bytes preserved at `ml/evaluation/reference_sales_b1/original_reference_sales.py.txt`. All original weights, metrics, cards, datasets, shared fixtures, backend/frontend and contracts are unchanged. Original Part B checksum entries remain historical; its old adapter checksum now resolves to the archived original source, rather than falsely claiming the revised source is identical. New output hashes are separate in `checksums.json`.','',
        'Current checkout began and remains on ML at `'+preserve()['head']+'`. The newer checkout predates B.1; the historical Part B report records its earlier HEAD. No commits, pushes, branch switches, merges, rebases or PRs were performed in this task. No Part C/later engine or backend orchestration was implemented.','',
        '## Remaining integration blockers','',
        'A subsequent explicitly authorised development phase must repair the simulator using training/validation-only design so demand, competition and temporal mechanisms affect non-saturated targets, then evaluate a frozen replacement without final-test tuning. Do not automatically promote it or silently overwrite this Ridge. Geographic transfer still needs suitable permissioned outcomes and support analysis; later reference attraction calibration needs aligned cell evidence and explicit bracket attainability. Until these issues are resolved, keep automatic integration blocked.','',status,'',
    ]
    report=ROOT/'PART_B1_HARDENING_REPORT.md';report.write_text('\n'.join(lines),encoding='utf-8')
    (POLICY/'HARDENING_CARD.md').write_text('# Reference-sales B.1 safety policy\n\n'+status+'\n\nBase fitted model unchanged: '+summary['base_model_artifact_id']+'.\n\nPolicy: '+policy['hardening_policy_id']+'. Evidence guards only; no fitted weights, clipping or calibration. All training targets are capacity-bound. All ten Bengaluru cases require support review. See PART_B1_HARDENING_REPORT.md and B.1 test/diagnostic outputs.\n',encoding='utf-8')
    preserve()
    paths=[p for folder in [OUT,POLICY] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='checksums.json']
    paths += [report,ROOT/'ml/inference/reference_sales.py',ROOT/'ml/inference/reference_sales_safety.py',ROOT/'tests/unit/test_reference_sales_b1.py']
    save(OUT/'checksums.json',dict(status=status,files={p.relative_to(ROOT).as_posix():sha(p) for p in paths},self_excluded=True))
    print(json.dumps(dict(status=status,tests=result.testsRun,passed=sum(r['status']=='PASS' for r in result.records),failures=len(result.failures),errors=len(result.errors),original_files_preserved=273),indent=2))
    if not result.wasSuccessful():print(stream.getvalue());raise SystemExit(1)

if __name__=='__main__':main()
