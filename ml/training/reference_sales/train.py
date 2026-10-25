"""Reproducible Part B training/evaluation. No application pipeline integration.

Run from repository root: python -m ml.training.reference_sales.train
"""
import csv
import datetime as dt
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path
import subprocess
import time
import traceback

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from .features import FEATURES, NUMERIC, DAYPART, TARGET, feature_frame, feature_schema
from .metrics import regression_metrics
from .models import BoundedSalesModel, preprocessing_record
from .simulator import config, generate, CATEGORY_WEIGHTS

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'ml/training/data/reference_sales_v1'
EVAL=ROOT/'ml/evaluation/reference_sales_v1'
ART=ROOT/'ml/artifacts/reference_sales_v1'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read_json(path):return json.loads(path.read_text(encoding='utf-8'))
def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def write_csv(path,frame):frame.to_csv(path,index=False,float_format='%.17g',lineterminator='\n')


def verify_preserved_inputs():
    frozen=read_json(EVAL/'preserved_input_hashes.json')
    changed=[name for name,digest in frozen['files'].items() if not (ROOT/name).is_file() or sha(ROOT/name)!=digest]
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    if changed or branch!=frozen['branch'] or branch!='ML' or head!=frozen['head']:
        raise RuntimeError('Preservation check failed: '+str(dict(changed=changed,branch=branch,head=head)))
    return dict(files_checked=len(frozen['files']),files_unchanged=len(frozen['files']),branch=branch,head=head)


def inspect_source_inventory():
    report=read_json(ROOT/'data/bengaluru/revised_v2/validation_report.json')
    if report['status']!='DATA_INTEGRITY_READY_WITH_LIMITATIONS' or report['failures'] or report['errors']:
        raise RuntimeError('Part A validation is not ready')
    inventory={}
    for folder in ['final','revised_v2']:
        for path in sorted((ROOT/'data/bengaluru'/folder).glob('*')):
            if not path.is_file():continue
            profile=dict(bytes=path.stat().st_size,sha256=sha(path))
            if path.suffix=='.csv':
                with path.open(encoding='utf-8-sig',newline='') as handle:
                    reader=csv.DictReader(handle);rows=list(reader);cols=reader.fieldnames
                profile.update(rows=len(rows),columns=cols,nulls_by_column={k:sum(r[k]=='' for r in rows) for k in cols})
            elif path.suffix=='.geojson':
                geo=read_json(path);profile.update(features=len(geo['features']),geometry_types=sorted({f['geometry']['type'] for f in geo['features']}))
            inventory[path.relative_to(ROOT).as_posix()]=profile
    canonical=pd.read_csv(ROOT/'data/bengaluru/revised_v2/site_features_enriched.csv')
    if canonical.shape!=(10,70) or not set(FEATURES)<=set(canonical):raise RuntimeError('Unexpected canonical feature view')
    feature_frame(canonical[list(FEATURES)].to_dict('records'))
    compatibility=[]
    for name in canonical:
        used=name in FEATURES
        reason='Used: supported baseline catchment/store/POI descriptor' if used else 'Excluded: metadata, redundant enrichment or unsupported model input'
        if name in ['population_10min_est','accessible_households_est']:reason='Excluded: unsupported routing/household evidence; all ten remain null'
        elif name in ['monthly_rent_inr','capex_inr','annual_opex_excl_rent_inr','gross_margin_fraction']:reason='Excluded: downstream economics, not reference-sales evidence'
        elif name=='source_quality_score':reason='Excluded: uncalibrated constant 0.75, not confidence'
        elif 'metro' in name:reason='Excluded: historical transit support/identity, separate measurement and unresolved rights; no store-footfall interpretation'
        elif name.endswith('_id') or name in ['city','locality','latitude','longitude']:reason='Excluded: identity/geographic label, not a model predictor'
        compatibility.append(dict(column=name,used=used,missing_count=int(canonical[name].isna().sum()),reason=reason))
    write_csv(EVAL/'feature_compatibility.csv',pd.DataFrame(compatibility))
    write_json(EVAL/'source_inventory.json',dict(part_a_status=report['status'],part_a_file_count=report['file_count'],
        part_a_validation_sha256=sha(ROOT/'data/bengaluru/revised_v2/validation_report.json'),inventory=inventory,
        no_bengaluru_data_in_simulator=True,source_use='Schema and read-only inference examples only; no observed-sales labels exist'))
    return canonical


def model_x(frame,features=FEATURES):
    return feature_frame(frame[list(features)].to_dict('records'),features=features)


def fit_candidates(train,validation,cfg):
    x=model_x(train);vx=model_x(validation);y=train[TARGET].to_numpy(float)
    grids={'median':[{}],'ridge':[dict(alpha=v) for v in cfg['ridge_alpha_grid']],'catboost':cfg['catboost_grid']}
    fitted={};search=[];issues=[]
    for name,grid in grids.items():
        for parameters in grid:
            started=time.perf_counter()
            try:
                model=BoundedSalesModel(name,parameters,cfg['model_seed']).fit(x,y)
                metrics=regression_metrics(validation[TARGET],model.predict(vx))
                record=dict(model=name,parameters=parameters,status='FITTED',validation=metrics,fit_seconds=time.perf_counter()-started)
                if name not in fitted or metrics['WAPE']<fitted[name][1]['WAPE']:
                    fitted[name]=(model,metrics)
            except Exception as exc:
                if name!='catboost':raise
                record=dict(model=name,parameters=parameters,status='FAILED',issue=type(exc).__name__+': '+str(exc),traceback=traceback.format_exc())
                issues.append(record)
            search.append(record)
    selected=min(fitted,key=lambda name:fitted[name][1]['WAPE'])
    return {name:value[0] for name,value in fitted.items()},selected,search,issues


def evaluation_exports(models,frames):
    metrics={};predictions=[];segments=[]
    for name,model in models.items():
        metrics[name]={}
        for split,frame in frames.items():
            actual=frame[TARGET].to_numpy(float);pred=model.predict(model_x(frame,model.features))
            metrics[name][split]=regression_metrics(actual,pred)
            for row,value in zip(frame.to_dict('records'),pred):
                predictions.append(dict(model=name,split=split,market_id=row['market_id'],observation_id=row['observation_id'],
                    actual_reference_annual_sales_inr=row[TARGET],predicted_reference_annual_sales_inr=float(value),
                    annual_wallet_inr=row['annual_wallet_inr'],method_mode='model_simulated'))
            labels={'store_format':frame['store_format'].to_numpy(),
                'external_competitor_count':np.where(frame['competitor_count_1500m']<=3,'0_to_3',np.where(frame['competitor_count_1500m']<=12,'4_to_12','13_plus')),
                'market':frame['market_id'].to_numpy()}
            for segment,values in labels.items():
                for value in sorted(set(values)):
                    mask=values==value
                    segments.append(dict(model=name,split=split,segment=segment,value=value,method_mode='model_simulated',**regression_metrics(actual[mask],pred[mask])))
    write_csv(EVAL/'heldout_predictions.csv',pd.DataFrame(predictions))
    write_csv(EVAL/'segment_metrics.csv',pd.DataFrame(segments))
    return metrics


def latency(model,frame):
    x=model_x(frame.head(1),model.features)
    for _ in range(5):model.predict(x)
    times=[]
    for _ in range(50):
        start=time.perf_counter_ns();model.predict(x);times.append((time.perf_counter_ns()-start)/1e6)
    return dict(repetitions=50,batch_size=1,warmups=5,unit='milliseconds',p50=float(np.median(times)),p95=float(np.quantile(times,.95)),minimum=float(min(times)),scope='Fitted prediction including preprocessing; excludes artifact loading',model_mode='model_simulated')


def perturbations(model,test):
    base=test.head(40).copy();x=model_x(base);pred=model.predict(x)
    rows=[];summary={}
    for change,expected in [('store_size_plus_25pct','increase'),('wallet_plus_25pct','increase'),('external_competition_added','decrease'),('daypart_plus_25pct','increase')]:
        changed=x.copy()
        if change.startswith('store_size'):changed['store_size_sqm']*=1.25
        elif change.startswith('wallet'):changed['annual_wallet_inr']*=1.25
        elif change.startswith('external'):
            changed['competitor_count_1500m']+=5
            changed['competitor_attraction_index']+=2
            changed['nearest_competitor_distance_m']=changed['nearest_competitor_distance_m'].fillna(750).clip(upper=750)
        else:changed[list(DAYPART)]*=1.25
        after=model.predict(changed);delta=after-pred;sign=1 if expected=='increase' else -1
        summary[change]=dict(examples=len(base),expected_direction=expected,changed_examples=int((np.abs(delta)>1e-6).sum()),
            expected_direction_examples=int((sign*delta>1e-6).sum()),opposite_direction_examples=int((sign*delta < -1e-6).sum()),median_change_inr=float(np.median(delta)),
            interpretation='Controlled held-out synthetic feature perturbation, not a validated causal intervention')
        for row,before,value in zip(base.to_dict('records'),pred,after):
            rows.append(dict(observation_id=row['observation_id'],market_id=row['market_id'],perturbation=change,
                original_reference_prediction_inr=float(before),perturbed_reference_prediction_inr=float(value),
                difference_inr=float(value-before),expected_direction=expected,method_mode='model_simulated'))
    write_csv(EVAL/'heldout_perturbations.csv',pd.DataFrame(rows))
    write_json(EVAL/'perturbation_report.json',summary)
    return summary


def export_artifacts(models,selected,ablation,canonical,train,cfg,metrics,search,issues):
    files={}
    for name,model in {**models,'ablation_no_daypart':ablation}.items():
        path=ART/(name+'.joblib');joblib.dump(model,path,compress=3);files[path.name]=sha(path)
    best=models[selected]
    if 'catboost' in models:
        models['catboost'].estimator.save_model(str(ART/'catboost.cbm'));files['catboost.cbm']=sha(ART/'catboost.cbm')
    joblib.dump(best.transformer,ART/'preprocessor.joblib',compress=3);files['preprocessor.joblib']=sha(ART/'preprocessor.joblib')
    write_json(ART/'feature_schema.json',feature_schema(canonical.columns));files['feature_schema.json']=sha(ART/'feature_schema.json')
    write_json(ART/'preprocessing.json',preprocessing_record(best));files['preprocessing.json']=sha(ART/'preprocessing.json')
    median=metrics['median']['test']['WAPE'];best_test=metrics[selected]['test']['WAPE'];ood=metrics[selected]['ood']['WAPE']
    gain=(median-best_test)/median if median is not None and median>0 and best_test is not None else None
    passed=gain is not None and gain>=cfg['activation_relative_test_WAPE_gain']
    ratio=ood/best_test if best_test is not None and best_test>0 else None
    warning=(ratio is not None and ratio>cfg['ood_test_WAPE_warning_ratio']) or (best_test==0 and ood>0)
    identifier=cfg['model_version']+'-'+files[selected+'.joblib'][:12]
    dependencies={name:importlib.metadata.version(name) for name in ['numpy','pandas','scipy','scikit-learn','catboost','joblib','threadpoolctl'] if importlib.util.find_spec('sklearn' if name=='scikit-learn' else name)}
    manifest=dict(model_artifact_id=identifier,method_mode='model_simulated',model_version=cfg['model_version'],
        selected_model=selected,selected_model_file=selected+'.joblib',selected_parameters=best.parameters,
        selected_by='Lowest validation WAPE among supported median/Ridge/CatBoost; no test/OOD tuning and no post-selection refit',
        activation_gate_passed=passed,activation_relative_test_WAPE_gain=gain,activation_threshold=cfg['activation_relative_test_WAPE_gain'],
        ood_test_WAPE_ratio=ratio,ood_warning=warning,required_file_sha256=files,
        feature_schema_version=cfg['feature_schema_version'],feature_allowlist=list(FEATURES),
        train_feature_ranges={name:dict(min=float(train[name].min()),max=float(train[name].max())) for name in NUMERIC},
        training_rows=len(train),training_market_ids=sorted(train['market_id'].unique().tolist()),
        regular_dataset_sha256=sha(DATA/'synthetic_regular.csv'),shifted_dataset_sha256=sha(DATA/'synthetic_shifted.csv'),
        split_sha256=sha(DATA/'market_splits.csv'),generator_configuration_sha256=sha(Path(__file__).with_name('config.json')),
        selection_lock_sha256=sha(EVAL/'selection_lock.json'),python=platform.python_version(),dependencies=dependencies,
        target_definition=cfg['target_definition'],uncertainty_status='NO_REAL_OUTCOME_VALIDATION_OR_CALIBRATED_INTERVALS',
        source_mode='TRAINED_EXCLUSIVELY_ON_CONTROLLED_SYNTHETIC_MARKETS',catboost_issues=issues,
        baseline_economic_inputs='NO_OWN_BRANCH_DISPLACEMENT_NO_RENT_NO_CAPEX_NO_FUTURE_INFRASTRUCTURE',
        physical_prediction_policy='Sigmoid capture fraction times input catchment wallet; median baseline projected to [0,wallet]')
    write_json(ART/'manifest.json',manifest)
    return manifest


def main():
    started=dt.datetime.now(dt.timezone.utc).isoformat()
    for directory in [DATA,EVAL,ART]:directory.mkdir(parents=True,exist_ok=True)
    preservation=verify_preserved_inputs();canonical=inspect_source_inventory();cfg=config()
    # Exact reproduction of the approved matrix is checked, not changed.
    approved=read_json(ROOT/'data/demo/weights.json')['category_weights']
    matrix=np.array([[approved[c][k.removesuffix('_raw')] for k in DAYPART] for c in ['office','shopping','leisure','school','hospital','transit']])
    if not np.array_equal(matrix,CATEGORY_WEIGHTS):raise RuntimeError('Approved category matrix mismatch')
    regular,shifted,splits,markets=generate(cfg)
    write_csv(DATA/'synthetic_regular.csv',regular);write_csv(DATA/'synthetic_shifted.csv',shifted);write_csv(DATA/'market_splits.csv',splits)
    write_json(DATA/'market_manifest.json',dict(generator_version=cfg['generator_version'],configuration=cfg,markets=markets,
        geometry='Independently generated synthetic local Cartesian metric coordinates; no city/candidate coordinates copied',
        pricing='Synthetic nominal INR, not a real release year or inflation estimate',
        alternative_policy='20 sites are alternatives. Each target is computed alone against external competitors and outside; never sum alternative targets as jointly achieved sales.'))
    assignments=dict(zip(splits['market_id'],splits['split']))
    frames={name:regular[regular['market_id'].map(assignments)==name].reset_index(drop=True) for name in ['train','validation','test']}
    frames['ood']=shifted
    with threadpool_limits(limits=1):
        models,selected,search,issues=fit_candidates(frames['train'],frames['validation'],cfg)
        # Freeze before evaluating any held-out or shifted target.
        write_json(EVAL/'selection_lock.json',dict(selected_model=selected,selected_parameters=models[selected].parameters,
            selection='VALIDATION_WAPE_ONLY',search=search,train_markets=sorted(frames['train']['market_id'].unique().tolist()),
            validation_markets=sorted(frames['validation']['market_id'].unique().tolist()),
            test_and_ood_used_for_selection=False,created_at_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
        without_daypart=tuple(k for k in FEATURES if k not in DAYPART)
        ablation=BoundedSalesModel(selected,models[selected].parameters,cfg['model_seed'],features=without_daypart)
        ablation.fit(model_x(frames['train'],without_daypart),frames['train'][TARGET])
        metrics=evaluation_exports({**models,'ablation_no_daypart':ablation},{name:frames[name] for name in ['validation','test','ood']})
        manifest=export_artifacts(models,selected,ablation,canonical,frames['train'],cfg,metrics,search,issues)
        timings={name:latency(model,frames['test']) for name,model in models.items()}
        perturb=perturbations(models[selected],frames['test'])
    ablation_report=dict(selected_full_model=selected,removed_features=list(DAYPART),
        same_train_markets=True,same_selected_hyperparameters=True,no_ablation_test_tuning=True,method_mode='model_simulated',
        splits={name:dict(full=metrics[selected][name],without_daypart=metrics['ablation_no_daypart'][name],
            full_relative_WAPE_reduction=(metrics['ablation_no_daypart'][name]['WAPE']-metrics[selected][name]['WAPE'])/metrics['ablation_no_daypart'][name]['WAPE'] if metrics['ablation_no_daypart'][name]['WAPE'] else None) for name in ['validation','test','ood']},
        interpretation='Generator explicitly assumes temporal utility. Ablation is simulator evidence only; no real-market predictive advantage or economic ordering is established in Part B.')
    write_json(EVAL/'daypart_ablation.json',ablation_report)
    from ml.inference.reference_sales import ReferenceSalesEstimator
    if manifest['activation_gate_passed']:
        start=time.perf_counter_ns();adapter=ReferenceSalesEstimator();load_ms=(time.perf_counter_ns()-start)/1e6
        examples=adapter.predict_many(canonical.to_dict('records'))
        write_csv(EVAL/'bengaluru_inference_examples.csv',pd.DataFrame([dict(site_id=row['site_id'],**{k:v for k,v in prediction.items() if k!='diagnostics'},diagnostics=';'.join(prediction['diagnostics']),
            usage='UNVALIDATED_INFERENCE_EXAMPLE_NOT_ACHIEVED_SALES_NOT_A_RANKING') for row,prediction in zip(canonical.to_dict('records'),examples)]))
        times=[];row=canonical.iloc[0].to_dict()
        for _ in range(5):adapter.predict(row)
        for _ in range(50):
            start=time.perf_counter_ns();adapter.predict(row);times.append((time.perf_counter_ns()-start)/1e6)
        timings['selected_adapter']=dict(p50=float(np.median(times)),p95=float(np.quantile(times,.95)),repetitions=50,warmups=5,batch_size=1,
            unit='milliseconds',cold_artifact_load_ms=load_ms,scope='Local adapter validation + preprocessing + fitted prediction; warm process')
    else:
        timings['selected_adapter']=dict(status='UNAVAILABLE_ACTIVATION_GATE_FAILED')
    write_json(EVAL/'metrics.json',dict(method_mode='model_simulated',metrics=metrics,latency=timings,
        selected_model=selected,activation_gate=dict(status='PASS' if manifest['activation_gate_passed'] else 'FAIL',
            relative_test_WAPE_gain=manifest['activation_relative_test_WAPE_gain'],required_gain=.1),
        ood_warning=manifest['ood_warning'],ood_test_WAPE_ratio=manifest['ood_test_WAPE_ratio'],catboost_issues=issues,
        training_started_at_utc=started,training_completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        observation_counts={name:len(frame) for name,frame in frames.items()},market_counts={name:frame['market_id'].nunique() for name,frame in frames.items()},
        preprocessing_fit_on='TRAIN_MARKETS_ONLY',final_model_refit_on_validation=False,selection_lock_sha256=manifest['selection_lock_sha256'],
        preservation_before=preservation,preservation_after=verify_preserved_inputs(),
        limitations='Synthetic benchmark only; no real revenue validation, calibrated intervals, actual achieved sales or downstream analytical implementation.'))
    lock=Path(__file__).with_name('requirements-lock.txt')
    lock.write_text('# Exact locally executed Part B environment; Python '+platform.python_version()+'\n'+'\n'.join(name+'=='+version for name,version in manifest['dependencies'].items())+'\n',encoding='utf-8')
    print(json.dumps(dict(selected_model=selected,model_artifact_id=manifest['model_artifact_id'],activation_gate='PASS' if manifest['activation_gate_passed'] else 'FAIL',
        counts={name:len(frame) for name,frame in frames.items()},test_WAPE=metrics[selected]['test']['WAPE'],ood_WAPE=metrics[selected]['ood']['WAPE'],preservation=verify_preserved_inputs()),indent=2))


if __name__=='__main__':main()
