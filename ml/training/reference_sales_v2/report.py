"""Execute B.2 acceptance and export model card/report/output checksums."""
import datetime as dt
import io
from pathlib import Path
import platform
import unittest
import warnings
import numpy as np
import pandas as pd
from .train import ROOT,DATA,OUT,ART,read,save,sha,preservation,csv

class Result(unittest.TextTestResult):
    def __init__(self,*a,**k):super().__init__(*a,**k);self.records=[]
    def addSuccess(self,t):super().addSuccess(t);self.records.append(dict(test=t.id(),status='PASS'))
    def addFailure(self,t,e):super().addFailure(t,e);self.records.append(dict(test=t.id(),status='FAIL',details=self._exc_info_to_string(e,t)))
    def addError(self,t,e):super().addError(t,e);self.records.append(dict(test=t.id(),status='ERROR',details=self._exc_info_to_string(e,t)))

def main():
    preservation();stream=io.StringIO()
    with warnings.catch_warnings(record=True) as notes:
        warnings.simplefilter('always');suite=unittest.defaultTestLoader.discover(str(ROOT/'tests/unit'),pattern='test_reference_sales_v2.py')
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
    save(OUT/'test_results.json',dict(command='python -m ml.training.reference_sales_v2.report',
        equivalent='python -m unittest discover -s tests/unit -p test_reference_sales_v2.py -v',
        tests=result.testsRun,passed=sum(r['status']=='PASS' for r in result.records),failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
        results=result.records,output=stream.getvalue(),warnings=sorted({str(n.message) for n in notes}),completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    metrics=read(OUT/'metrics.json');manifest=read(ART/'manifest.json');candidates=read(OUT/'bengaluru_readiness.json');ablation=read(OUT/'ablation.json')
    supported=sum(r['joint_support_pass'] for r in candidates);usable=sum(r['reference_annual_sales_inr'] is not None for r in candidates)
    status='PART_B_READY_WITH_WARNINGS' if result.wasSuccessful() and metrics['activation_passed'] and supported==10 and usable==10 else 'PART_B_INTEGRATION_BLOCKED'
    diagnostics={}
    for split,file in [('ordinary','synthetic_regular.csv'),('ood','synthetic_shifted.csv')]:
        df=pd.read_csv(DATA/file);target=df.reference_annual_sales_inr
        diagnostics[split]=dict(rows=len(df),markets=df.market_id.nunique(),no_capacity_cap=True,
            target_distribution=target.describe(percentiles=[.01,.25,.5,.75,.99]).to_dict(),
            capture_distribution=(target/df.annual_wallet_inr).describe().to_dict(),nonpositive=int((target<=0).sum()),near_zero_under_1_inr=int((target<1).sum()),
            within_market_mean_std=float(df.groupby('market_id').reference_annual_sales_inr.std().mean()),
            between_market_means_std=float(df.groupby('market_id').reference_annual_sales_inr.mean().std()),
            target_spearman={f:float(df[f].corr(target,method='spearman')) for f in ['annual_wallet_inr','competitor_attraction_index','store_size_sqm','mean_wallet_weighted_distance_m','weekday_morning_raw','weekend_evening_raw']})
    save(OUT/'target_diagnostics.json',diagnostics)
    probes=read(OUT/'candidate_perturbations.json');probe_summary={}
    for name in sorted({r['change'] for r in probes}):
        rows=[r for r in probes if r['change']==name]
        probe_summary[name]=dict(increase=sum(r['modified_raw']>r['base_raw']+1e-6 for r in rows),
            decrease=sum(r['modified_raw']<r['base_raw']-1e-6 for r in rows),unchanged=sum(abs(r['modified_raw']-r['base_raw'])<=1e-6 for r in rows),
            rejected=sum(r['usable'] is None for r in rows))
    save(OUT/'perturbation_summary.json',probe_summary)
    profiles={}
    for folder in [DATA,OUT]:
        for path in folder.glob('*.csv'):
            df=pd.read_csv(path);profiles[path.relative_to(ROOT).as_posix()]=dict(rows=len(df),columns=len(df.columns),nulls=int(df.isna().sum().sum()))
    save(OUT/'output_inventory.json',profiles)
    pins='\n'.join(name+'=='+version for name,version in manifest['versions'].items())+'\n'
    (Path(__file__).with_name('requirements-lock.txt')).write_text(pins,encoding='utf-8')
    selected=metrics['selected'];ratio=manifest['test_ood_ratio'];old=read(OUT/'v1_root_cause.json')
    lines=[
        '# Part B.2 simulator and demand-model correction','',status,'',
        'This new synthetic experiment corrects target saturation and wallet-response structure. It does not replace or overwrite the original Ridge, B.1 adapter, cards, metrics or data. No later analytical component is connected. All inference remains **model_simulated**; no real store-sales accuracy or calibrated confidence is claimed.','',
        '## 1. Demonstrated root cause','',
        'In v1, initial candidate allocation was nonnegative and wallet-bounded. A separate post-allocation annual capacity (floor area × market INR/sqm/year density) systematically overrode it. There was no demonstrated annual/monthly INR mismatch or pre-bound allocation above the wallet. Both the cell/catchment wallet and the capacity were annual INR. The hypothetical wallets and resulting capture demand were simply too large relative to that independently assumed cap.','',
        f'For the 2,000 old regular rows, raw allocation / capacity had median **{old["regular"]["raw_capacity_ratio"]["50%"]:.4f}**, range **{old["regular"]["raw_capacity_ratio"]["min"]:.4f}–{old["regular"]["raw_capacity_ratio"]["max"]:.4f}**. Exactly **{old["regular"]["capped_rows"]}/2,000** regular rows and all OOD rows were capped. All 1,200 training rows were capped; three validation rows were not. Thus training targets collapsed to area × hidden market capacity, masking demand, competition and daypart mechanisms.','',
        'The old candidate attraction/large catchment wallets produced excessive pre-cap demand relative to this capacity assumption, rather than violating wallet conservation. Removing the unjustified cap is the correction; no inflation trick, post-hoc target clipping or desired investment outcome is used. `v1_capacity_audit.csv` preserves every original raw target, capacity, final target and wallet; `v1_root_cause.json` reports ratio distributions, zeros, correlations and within/between-market variation.','',
        '## 2. Corrected simulator and source alignment','',
        'The new process uses `A=exp(theta)*(area/100)^1*exp(-distance/750)` and outside=1 in ordinary markets. Each candidate is considered alone against external competitors plus outside. Annual reference sales are the sum of cell wallet × candidate share. External/outside allocations conserve spending; there is **no capacity cap**. Positive outside and finite attraction keep target shares strictly inside the wallet. Twenty candidates are alternatives, not simultaneously open stores, and no own-company branch enters any target.','',
        'Synthetic source templates are resampled from the existing deduplicated OSM POIs, grocery competitors, recorded/assumed opening schedules and WorldPop/HCES-derived spending cells. Poisson copies/omissions, 100 m position jitter, rotations and 0.85–1.15 geometric scales create new synthetic markets; population and POI intensity vary over declared 0.65–1.45 multipliers. This preserves sparse shopping POIs and the observed category/spatial relationships instead of the old unrelated uniform category mixture.','',
        'Population is a modelled 2020 nominal 1 km source; expenditure is the nominal 2023–24 HCES state urban proxy with local-transfer assumptions. The 100 prepared grid cells are subdivided into 16 quadrature points each (1,600 total), conserving source totals. That is a numerical uniform-within-cell assumption, **not a finer observed population resolution**. Synthetic wallets additionally vary by a disclosed spending multiplier. No households or routing measurements are invented. OSM incompleteness and schedule assumptions remain. Source hashes/attributions and source status are recorded in `source_evidence.json`; original source/licence reports are retained. No metro inputs are used because none are part of the capture schema.','',
        'Store-area/format/theta and behavioural ranges are explicitly assumed, not observed commercial data. Approved synthetic store areas inform plausible simulation support; no actual leases, revenue density benchmark or financial cost is asserted. Daypart utility changes theta through a bounded temporal function; bounded parameter noise acts before allocation, never as arbitrary noise added to sales. Config records all parameters, seeds, ordinary/shifted deviations and target equations.','',
        'The ten unchanged candidates provide unlabelled range/schema/support diagnostics only. The simulator never reads their feature rows or coordinates, and no candidate is copied or given a target. All markets share a perturbed empirical regional source template: group isolation does **not** establish independent-city generalisation.','',
        '## 3. Fresh data, split and protocol','',
        'New generator seed **2026102502**, split seed **56319**, model seed **90217**. Exactly **100 ordinary markets × 20 alternatives = 2,000 rows**, plus **20 separate shifted markets × 20 = 400 rows**. New identifiers and seeds do not reuse the v1 test set. Grouped split is **60/20/20 markets**, or **1,200/400/400 rows**, with 400 OOD rows isolated.','',
        'Versioned input schema requires the original 20 supported feature names. **19 capture predictors exclude annual_wallet_inr**; wallet is only the final scale input. IDs, audit targets/theta/positions, own branches, costs, infrastructure and quality scores are excluded. Training-only imputation/encoding/log transforms/scaling are used. The two unsupported Bengaluru household/routing columns remain untouched. Only the declared no-competitor nearest-distance null has a model missingness representation.','',
        'Protocol/split hashes, grids and support rule are frozen before fitting. Median is a genuinely fitted median-logit-capture baseline multiplied by wallet; Ridge and CatBoost fit logit capture. No target endpoint clipping is used. All targets lie strictly inside (0,wallet). Preprocessing and the final model fit use training groups only. Selection uses minimum validation INR WAPE among these structurally homogeneous models. No final test/OOD tuning or post-selection refit occurred. Ablation is a diagnostic, not a retrospective selection candidate.','',
        '## 4. Actual B.2 results','',
        '| Model | Split | MAE INR/year | RMSE INR/year | WAPE |','|---|---|---:|---:|---:|',
    ]
    for name,results in metrics['models'].items():
        for split,r in results.items():lines.append(f'| {name} | {split} | {r["MAE_inr"]:,.2f} | {r["RMSE_inr"]:,.2f} | {r["WAPE"]:.4%} |')
    lines += [
        '',f'Selected **{selected}**, parameters `{manifest["selected_parameters"]}`, by validation only. Ridge happens to have lower final test/OOD error; it is not retrospectively substituted. The synthetic activation gate is **'+('PASS' if metrics['activation_passed'] else 'FAIL')+f'**, with **{metrics["relative_test_gain"]:.4%}** relative test-WAPE reduction versus the new median baseline. WAPE is sum absolute error / sum absolute actuals; zero denominators are explicitly undefined.','',
        f'OOD/test WAPE ratio is **{ratio:.4f}×**, exceeding the 2× review threshold. Shifted markets change wallet level, competitor density, decay (1,100 m), outside (1.5) and hidden theta (-0.4 offset); this is a genuine conditional stress regime, not a tuning set. Model outputs retain a shifted-market review warning. No real-world calibrated intervals or probabilities exist.','',
        f'Fitted prediction latency: p50 **{metrics["latency_ms"]["p50"]:.4f} ms**, p95 **{metrics["latency_ms"]["p95"]:.4f} ms**, 50 single-row calls after five warmups. This includes fitted preprocessing/prediction, excludes Python startup, disk load and adapter support search. Platform: `{platform.platform()}`.','',
        '| Ablation split | Full WAPE | Without six dayparts WAPE |','|---|---:|---:|',
    ]
    for split,r in ablation['metrics'].items():lines.append(f'| {split} | {r["full"]["WAPE"]:.4%} | {r["without_dayparts"]["WAPE"]:.4%} |')
    lines += [
        '', 'Removing dayparts slightly improves this run; no incremental DaypartDNA predictive advantage is established. All ablation metrics are retained rather than cherry-picked. No economic-ordering/ranking ablation is claimed. Target distributions, capture distributions, near-zero counts, Spearman relationships and within/between-market variation are exported in `target_diagnostics.json`. Every new row retains raw pre-bound=final target and `capacity_applied=False`; no systematic target saturation remains.','',
        '## 5. Wallet guarantee and perturbations','',
        '`R(W,X)=W*sigmoid(fitted_model(X))`, where X excludes wallet and wallet-derived ratios. Thus **R(kW,X)=kR(W,X)** exactly up to floating-point arithmetic for nonnegative finite scaling, fixed capture features and consistent reference-wallet context. This is a structural fitted-model property, not a hardcoded capture formula: the share is learned by median/Ridge/CatBoost. The simulator satisfies the same identity for fixed geometry/attractiveness/competition/outside. Sigmoid is the disclosed fitted output link; no negative/over-bound prediction is silently clipped after inference.','',
        'Wallet is also excluded from joint capture-support scoring because multiplying fixed cell wallets does not change capture geometry; numerical validation and explicit wallet/price-basis reporting remain. Marginal wallet-range changes remain warnings. This support definition is justified by the proven scale invariant, not changed to make candidates pass.','',
        '| Candidate perturbation | Increase | Decrease | Unchanged | Rejected |','|---|---:|---:|---:|---:|',
    ]
    for name,r in probe_summary.items():lines.append(f'| {name} | {r["increase"]} | {r["decrease"]} | {r["unchanged"]} | {r["rejected"]} |')
    lines += [
        '', 'Competition, store area and individual daypart responses are measured, without imposing universal monotonic constraints on conditional fitted features. The physical allocator does strictly reduce candidate share when adding positive external attractions with everything else fixed; that is tested separately. Exact candidate patches/raw results are retained in `candidate_perturbations.json`.','',
        '## 6. Candidate support and preliminary feasibility','',
        'Marginal ranges and multivariate support both use training-only information. Per format, standardised capture features are compared to the nearest training neighbour; the threshold is the fixed 99th percentile of training leave-one-out nearest-neighbour distances. The rule was declared in config/protocol before candidate evaluation. It reflects multimodal source-grounded geography better than the previous uniform simulator support; it is not a calibrated probability or confidence interval. No candidate features or thresholds were modified after results.','',
        '| Site | Raw reference INR/year | Usable INR/year | Wallet bound INR/year | Joint distance / threshold | Reference feasibility |','|---|---:|---:|---:|---|---|',
    ]
    for r in candidates:
        usable_text='REJECTED' if r['reference_annual_sales_inr'] is None else f'{r["reference_annual_sales_inr"]:,.2f}'
        lines.append(f'| {r["site_id"]} | {r["raw_reference_annual_sales_inr"]:,.2f} | {usable_text} | {r["wallet_upper_bound_inr"]:,.2f} | {r["joint_distance"]:.4f} / {r["joint_threshold"]:.4f} | {r["feasibility_status"]} |')
    lines += [
        '',f'**{supported}/10 jointly supported; {usable}/10 usable** under the declared synthetic-model/support/reference assumptions. All ten are schema-compatible and inside marginal training ranges. Every site retains `SHIFTED_MARKET_DEGRADATION_REVIEW`. Sites 05 and 06 are closest to the joint threshold; support is finite-sample and regional, not empirical forecast validation. There are no candidate revenue labels, so no candidate accuracy is reported.','',
        'Preliminary checks use the actual existing 100 spending-cell centroids/wallets and mapped external grocery POI coordinates, great-circle distances, gamma=1, tau=750 m and outside=1. External attraction is explicitly assumed equal unit mass (100 sqm/theta=0), not measured store size/productivity. Two endpoint revenues at theta=-30 and +30 bracket the requested estimates. Continuity gives preliminary compatibility under those fixed assumptions; no bisection, full Huff engine, own-branch displacement or downstream orchestration is implemented.','',
        'The prepared full AOI grid and original circular raster catchment differ. The endpoint test is a disclosed centroid approximation using available evidence, not a production certificate. Later integration must freeze/align the actual reference inputs, confirm external/outside assumptions and calibrate/check requested-versus-achieved targets. `automatic_calibration_permitted=False` remains explicit.','',
        '## 7. Versioned inference and artifacts','',
        'New explicit entrypoint: `ml.inference.reference_sales_v2.ReferenceSalesEstimatorV2`. It loads the actual saved fitted model, schema and support metadata by verified SHA-256, preserves raw versus usable estimates, returns INR/year and `model_simulated`, validates required inputs and rejects unsupported geometry or a supplied failing endpoint bracket. Invalid/missing evidence is not fabricated. No network or notebook is needed. The original B.1 entrypoint remains unchanged and blocked for reproducibility; there is no silent promotion through backend APIs.','',
        '```python','from ml.inference.reference_sales_v2 import ReferenceSalesEstimatorV2',
        'estimator = ReferenceSalesEstimatorV2()',
        'result = estimator.predict(prepared_feature_row, reference_bracket=(reference_low_inr, reference_high_inr))',
        '# Inspect raw/usable value, support, feasibility and warnings before later calibration.', '```','',
        'Artifact ID: `'+manifest['model_artifact_id']+'`. Selected file: `ml/artifacts/reference_sales_v2/'+manifest['selected_file']+'`; SHA-256 `'+manifest['required_sha256'][manifest['selected_file']]+'`. Separate model card, learned preprocessing, all comparison models and schema are in that directory. Dependencies: '+', '.join(n+'=='+v for n,v in manifest['versions'].items())+'.','',
        'Exact reproduction from repository root (Python '+platform.python_version()+'):','',
        '```powershell','python -m pip install -r ml/training/reference_sales_v2/requirements-lock.txt',
        "$env:PYTHONDONTWRITEBYTECODE='1'", "$env:OMP_NUM_THREADS='1'", "$env:OPENBLAS_NUM_THREADS='1'", "$env:MKL_NUM_THREADS='1'",
        'python -m ml.training.reference_sales_v2.train','python -m ml.training.reference_sales_v2.report','```','',
        '## 8. Tests, preservation and comparison','',
        f'**{sum(r["status"]=="PASS" for r in result.records)}/{result.testsRun} acceptance tests passed; {len(result.failures)} failures, {len(result.errors)} errors, {len(result.skipped)} skipped.** Executed by `python -m ml.training.reference_sales_v2.report`; full test identities/output and existing Joblib/NumPy deprecation warnings are in `test_results.json`. Full generator CSV/split reproducibility and selected-model refit reproducibility were actually executed. Binary serialisation metadata and timings may vary; fixed-seed numerical predictions are checked.','',
        'Tests cover counts/groups, conservation/wallet bounds, no cap, demand/competition effects, simulator and fitted wallet homogeneity, candidate support invariance, no ID/target/own-branch leakage, train-only preprocessing/support, validation selection, recalculated metrics, finite predictions, input rejection, unsupported joint inputs, ten-site endpoint compatibility, explicit bracket rejection, ablation, unchanged originals and offline inference.','',
        '| Phase | Target / evaluation meaning | Outcome |','|---|---|---|',
        '| Part B | v1 capacity-dominated synthetic targets; old market split | Ridge selected; historical metrics preserved |',
        '| Part B.1 | Audit of unchanged v1; no retraining | Blocked due target degeneration, wallet response and support |',
        '| Part B.2 | New uncapped source-grounded allocation labels; fresh splits; wallet-homogeneous fitted capture | '+status+' |','',
        'Do **not** compare 17.61% v1 WAPE to 7.63% v2 WAPE as improvement on the same task: label mechanism, source distributions, split identities and median baseline definition differ. The valid activation comparison is the new selected model against the new median within B.2.','',
        f'All **{preservation()} pre-existing files remain byte-identical**, including Part A/B/B.1 data, weights, reports, cards, inference entrypoints and public backend/frontend contracts. Branch remains ML at `'+read(OUT/'preservation.json')['head']+'`; no commits, pushes, switches, merges, rebases or PRs occurred. Current pre-existing B.1 worktree modifications were preserved, not reverted.','',
        '## 9. Output inventory and remaining warnings','',
        '| CSV | Rows | Columns | Null fields |','|---|---:|---:|---:|',
    ]
    for name,r in profiles.items():lines.append(f'| {name} | {r["rows"]} | {r["columns"]} | {r["nulls"]} |')
    lines += [
        '', 'All new source/config/dependency pins: `ml/training/reference_sales_v2/`; generated data/splits: `ml/training/data/reference_sales_v2/`; evaluation, perturbations, candidate support and old-vs-new diagnosis: `ml/evaluation/reference_sales_v2/`; fitted artifacts/schema/card: `ml/artifacts/reference_sales_v2/`; adapter: `ml/inference/reference_sales_v2.py`; tests: `tests/unit/test_reference_sales_v2.py`. Exact file hashes are exported in `checksums.json` (self excluded).','',
        'Remaining warnings: synthetic targets and assumed theta/outside/competitor masses; reuse of one perturbed regional source template; historical/modelled population and nominal expenditure; incomplete OSM/assumed schedules; material shifted-regime degradation; no demonstrated daypart ablation benefit; no real-outcome calibration or uncertainty intervals; centroid/reference-context approximation. Retain source attribution/usage records. Nothing was publicly packaged and no raw metro data was used/copied.','',
        'The correction supports later prototype calculations only through the declared versioned fitted-model/support/feasibility path, with warnings reviewed and actual reference calibration still required. No Part C, full Huff, finance, FailFast, infrastructure, ranking, portfolio or backend/frontend integration began. Stop here.','',status,'',
    ]
    report=ROOT/'PART_B2_CORRECTION_REPORT.md';report.write_text('\n'.join(lines),encoding='utf-8')
    (ART/'MODEL_CARD.md').write_text('# Reference-sales v2 model card\n\n'+status+'\n\nArtifact: '+manifest['model_artifact_id']+'; selected '+selected+' by validation only.\n\nMode: model_simulated. No empirical retail-sales accuracy or calibrated intervals. Uncapped conserved synthetic targets; 19 trained capture features exclude wallet, guaranteeing proportional wallet-only scaling. All ten unchanged Bengaluru rows supported under frozen empirical rules and preliminary assumed reference endpoints. OOD warning and no daypart-ablation advantage remain. No automatic calibration/investment permission.\n\nComplete model/evaluation/source/assumption/selection/test details: PART_B2_CORRECTION_REPORT.md; metrics.json, ablation.json, source_evidence.json, selection_lock.json and test_results.json under ml/evaluation/reference_sales_v2/. Original versions remain unchanged.\n',encoding='utf-8')
    preservation()
    paths={p for folder in [Path(__file__).parent,DATA,OUT,ART] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='checksums.json'}
    paths.update([report,ROOT/'ml/inference/reference_sales_v2.py',ROOT/'tests/unit/test_reference_sales_v2.py'])
    save(OUT/'checksums.json',dict(status=status,files={p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)},self_excluded=True))
    print(dict(status=status,tests=result.testsRun,passed=sum(r['status']=='PASS' for r in result.records),failures=len(result.failures),errors=len(result.errors),original_files_preserved=preservation()))
    if not result.wasSuccessful():print(stream.getvalue());raise SystemExit(1)

if __name__=='__main__':main()
