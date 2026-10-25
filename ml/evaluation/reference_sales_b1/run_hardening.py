"""Read-only B.1 diagnosis; builds train-only support metadata, not new weights.

python -m ml.evaluation.reference_sales_b1.run_hardening
"""
import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import subprocess
import unittest
import warnings
import joblib
import numpy as np
import pandas as pd
from ml.training.reference_sales.features import FEATURES, NUMERIC, DAYPART
from ml.training.reference_sales.train import model_x
from ml.training.reference_sales.metrics import regression_metrics
from ml.inference.reference_sales_safety import raw_predictions, ridge_wallet_elasticity

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=ROOT/'ml/artifacts/reference_sales_v1'
POLICY=ROOT/'ml/artifacts/reference_sales_b1'
DATA=ROOT/'ml/training/data/reference_sales_v1'
EV=ROOT/'ml/evaluation/reference_sales_v1'

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def clean(value):
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple,np.ndarray)):return [clean(v) for v in value]
    if isinstance(value,np.generic):value=value.item()
    return None if isinstance(value,float) and not np.isfinite(value) else value
def save(path,data):path.write_text(json.dumps(clean(data),indent=2,allow_nan=False),encoding='utf-8')
def csv(path,rows):pd.DataFrame(rows).to_csv(path,index=False,float_format='%.17g',lineterminator='\n')

def preserve():
    baseline=read(OUT/'preservation.json');changed=[]
    for name,digest in baseline['files'].items():
        path=OUT/'original_reference_sales.py.txt' if name==baseline['allowed_modified_source'] else ROOT/name
        if not path.is_file() or sha(path)!=digest:changed.append(name)
    assert not changed,changed
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==baseline['head']
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='ML'
    return dict(existing_files_checked=len(baseline['files']),all_original_bytes_preserved=True,
        source_revised_with_original_backup=baseline['allowed_modified_source'],head=baseline['head'])

def main():
    preserve();POLICY.mkdir(exist_ok=True)
    manifest=read(OLD/'manifest.json');model=joblib.load(OLD/manifest['selected_model_file'])
    regular=pd.read_csv(DATA/'synthetic_regular.csv');ood=pd.read_csv(DATA/'synthetic_shifted.csv')
    splits=pd.read_csv(DATA/'market_splits.csv');assignment=dict(zip(splits.market_id,splits.split))
    train=regular[regular.market_id.map(assignment)=='train'].copy()
    test=regular[regular.market_id.map(assignment)=='test'].copy()
    capacity_audit={}
    for name,frame in [(n,regular[regular.market_id.map(assignment)==n]) for n in ['train','validation','test']]+[('ood',ood)]:
        capacity_audit[name]=dict(rows=len(frame),capped_rows=int((frame.purchase_completion_fraction<1).sum()),uncapped_rows=int((frame.purchase_completion_fraction==1).sum()))
    save(OUT/'capacity_audit.json',capacity_audit)
    design=model.transformer.transform(model_x(train));mean=design.mean(axis=0)
    covariance=np.cov(design,rowvar=False);pinv=np.linalg.pinv(covariance,rcond=1e-6)
    delta=design-mean;distance=np.einsum('ij,jk,ik->i',delta,pinv,delta)
    support=dict(version='reference-sales-support-b1',base_model_sha256=sha(OLD/'ridge.joblib'),
        training_market_ids=sorted(train.market_id.unique()),training_rows=len(train),
        design_mean=mean.tolist(),design_covariance_pinv=pinv.tolist(),training_squared_distance_p99=float(np.quantile(distance,.99)),
        rule='Fixed empirical training-only 99th percentile of squared pseudoinverse-covariance distance; not a calibrated probability or CI',
        model_refitted=False,preprocessing_refitted=False,
        training_capacity_binding_fraction=float((train.purchase_completion_fraction<1).mean()),
        integration_block_reasons=['ALL_TRAINING_TARGETS_CAPACITY_SATURATED'] if bool((train.purchase_completion_fraction<1).all()) else [])
    save(POLICY/'support_policy.json',support);digest=sha(POLICY/'support_policy.json')
    save(POLICY/'manifest.json',dict(hardening_policy_id='reference-sales-safety-b1-'+digest[:12],
        support_policy_sha256=digest,base_model_sha256=sha(OLD/'ridge.joblib'),base_model_artifact_id=manifest['model_artifact_id'],
        action='Evidence/feasibility guards only; no new weights, clipping, hyperparameters or selected-model changes'))
    from ml.inference.reference_sales import ReferenceSalesEstimator
    adapter=ReferenceSalesEstimator()
    canonical=pd.read_csv(ROOT/'data/bengaluru/revised_v2/site_features_enriched.csv')
    # Entire held-out test plus ten unlabelled candidates. OOD labels do not
    # determine the support rule or any model parameter.
    baselines=test[list(FEATURES)].to_dict('records')+canonical[list(FEATURES)].to_dict('records')
    ids=test.observation_id.tolist()+canonical.site_id.tolist()
    base_predictions=adapter.predict_many(baselines)
    modified=[];contexts=[]
    for i,row in enumerate(baselines):
        changes=[('wallet_x0.5',{'annual_wallet_inr':row['annual_wallet_inr']*.5},'wallet_down'),
            ('wallet_x0.8',{'annual_wallet_inr':row['annual_wallet_inr']*.8},'wallet_down'),
            ('wallet_x1.25',{'annual_wallet_inr':row['annual_wallet_inr']*1.25},'wallet_up'),
            ('wallet_x2',{'annual_wallet_inr':row['annual_wallet_inr']*2},'wallet_up'),
            ('store_size_x1.25',{'store_size_sqm':row['store_size_sqm']*1.25},'context_dependent'),
            ('competition_plus5',{'competitor_count_1500m':row['competitor_count_1500m']+5,
             'competitor_attraction_index':row['competitor_attraction_index']+2,
             'nearest_competitor_distance_m':min(row['nearest_competitor_distance_m'],750) if np.isfinite(row['nearest_competitor_distance_m']) else 750},'competition_up')]
        for field in DAYPART:
            for factor in [.8,1.25]:changes.append((field+'_x'+str(factor),{field:row[field]*factor},'context_dependent'))
        for name,patch,expect in changes:
            modified.append(dict(row,**patch));contexts.append((i,name,expect))
    # Near and outside observed ranges, based only on training limits.
    anchor=baselines[0]
    for field in ['annual_wallet_inr','store_size_sqm']:
        for label,value in [('near_min',train[field].min()*1.001),('outside_min',train[field].min()*.99),('near_max',train[field].max()*.999),('outside_max',train[field].max()*1.01)]:
            modified.append(dict(anchor,**{field:float(value)}));contexts.append((0,field+'_'+label,'boundary_probe'))
    predicted=adapter.predict_many(modified);perturb=[]
    for (i,name,expect),row,result in zip(contexts,modified,predicted):
        before=base_predictions[i]['raw_reference_annual_sales_inr'];after=result['raw_reference_annual_sales_inr'];difference=after-before
        questionable=(expect=='wallet_up' and difference < -1e-6) or (expect=='wallet_down' and difference>1e-6) or (expect=='competition_up' and difference>1e-6)
        perturb.append(dict(example_id=ids[i],population='bengaluru_unlabelled' if i>=len(test) else 'heldout_synthetic',perturbation=name,
            original_features_json=json.dumps(clean(baselines[i]),sort_keys=True),modified_features_json=json.dumps(clean(row),sort_keys=True),
            original_prediction_inr=before,modified_prediction_inr=after,delta_inr=difference,
            direction='increase' if difference>1e-6 else 'decrease' if difference < -1e-6 else 'unchanged',
            expected_relationship=expect,assessment='QUESTIONABLE_SPENDING_OR_COMPETITION_RESPONSE' if questionable else 'CONTEXT_DEPENDENT_NOT_A_CAUSAL_CLAIM' if expect=='context_dependent' else 'EXPECTED_OR_EXPLAINABLE',
            modified_joint_support_score=result['empirical_joint_support_squared_distance'],warnings=';'.join(result['diagnostics'])))
    csv(OUT/'controlled_perturbations.csv',perturb)
    numeric=model.transformer.named_transformers_['numeric'];scales=numeric.named_steps['scale'].scale_
    names=model.transformer.get_feature_names_out();coeff=[]
    for index,name in enumerate(names):
        coeff.append(dict(transformed_feature=name,coefficient=float(model.estimator.coef_[index]),
            coefficient_per_log1p_unit=float(model.estimator.coef_[index]/scales[index]) if index<len(scales) else None))
    csv(OUT/'ridge_coefficients.csv',coeff)
    wallet_index=list(names).index('numeric__annual_wallet_inr');beta=float(model.estimator.coef_[wallet_index]/scales[wallet_index])
    correlation=train[list(NUMERIC)].corr();pairs=[]
    for i,a in enumerate(NUMERIC):
        for c in NUMERIC[i+1:]:pairs.append(dict(a=a,b=c,correlation=float(correlation.loc[a,c])))
    save(OUT/'coefficient_diagnosis.json',dict(wallet_effective_log_coefficient=beta,
        exact_elasticity_formula='1 + beta*(1-sigmoid(z))*W/(1+W)',
        finite_difference_explanation='Negative elasticity means wallet alone increases while predicted store sales falls. Scaling is analytically inverted; this is a fitted capture-head coefficient/relationship problem, not arithmetic clipping.',
        top_absolute_correlations=sorted(pairs,key=lambda x:abs(x['correlation']),reverse=True)[:15],
        wallet_population_correlation=float(correlation.loc['annual_wallet_inr','population_1500m_est']),
        positive_subspace_condition_number=float(np.linalg.cond(covariance+np.eye(len(covariance))*1e-6)),
        training_capacity_binding_fraction=float((train.purchase_completion_fraction<1).mean()),
        no_retraining=True))
    support_rows=[];feature_rows=[];pool=float(pd.read_csv(ROOT/'data/bengaluru/final/spending_cells.csv').annual_wallet_inr.sum())
    for raw,result in zip(canonical.to_dict('records'),adapter.predict_many(canonical.to_dict('records'))):
        outside=[]
        for field in NUMERIC:
            value=float(raw[field]);lo=float(train[field].min());hi=float(train[field].max())
            is_out=bool(value<lo or value>hi)
            if is_out:outside.append(field)
            feature_rows.append(dict(site_id=raw['site_id'],feature=field,value=value,train_min=lo,train_max=hi,
                training_empirical_percentile=float((train[field].dropna()<=value).mean()*100),outside_marginal_range=is_out))
        support_rows.append(dict(site_id=raw['site_id'],**result,outside_marginal_features=outside,
            full_aoi_grid_wallet_inr=pool,below_full_aoi_wallet_necessary_bound=result['raw_reference_annual_sales_inr']<=pool,
            observed_revenue_target_available=False,accuracy_not_evaluated=True,
            reference_pool_note='AOI grid is not the circular raster catchment; this global bound cannot certify finite-theta attainability.'))
    save(OUT/'bengaluru_support.json',support_rows);csv(OUT/'bengaluru_feature_ranges.csv',feature_rows)
    market_manifest=read(DATA/'market_manifest.json');market_rows=market_manifest['markets']
    shift_parameters={}
    for field in ['allocation_decay_m','outside_attraction','market_appeal','annual_capacity_inr_per_sqm','external_competitors','poi_count','market_population','market_wallet_inr']:
        shift_parameters[field]={regime:dict(min=min(r[field] for r in market_rows if r['regime']==regime),median=float(np.median([r[field] for r in market_rows if r['regime']==regime])),max=max(r[field] for r in market_rows if r['regime']==regime)) for regime in ['regular','shifted']}
    reevaluated={};shift_summary=[]
    for family in ['ridge','catboost']:
        fitted=joblib.load(OLD/(family+'.joblib'));reevaluated[family]={}
        for split,frame in [('test',test),('ood',ood)]:
            pred=raw_predictions(fitted,model_x(frame));reevaluated[family][split]=regression_metrics(frame.reference_annual_sales_inr,pred)
            saved=read(EV/'metrics.json')['metrics'][family][split]
            assert np.isclose(reevaluated[family][split]['WAPE'],saved['WAPE'],rtol=1e-12)
            shift_summary.append(dict(model=family,split=split,median_actual_capture=float(np.median(frame.reference_annual_sales_inr/frame.annual_wallet_inr)),
                median_predicted_capture=float(np.median(pred/frame.annual_wallet_inr)),mean_signed_error_inr=float(np.mean(pred-frame.reference_annual_sales_inr)),
                capacity_binding_fraction=float((frame.purchase_completion_fraction<1).mean()),**reevaluated[family][split]))
    csv(OUT/'ood_diagnosis.csv',shift_summary);save(OUT/'shift_parameters.json',shift_parameters)
    selection=read(EV/'selection_lock.json');winner=min([r for r in selection['search'] if r['status']=='FITTED'],key=lambda r:r['validation']['WAPE'])
    assert winner['model']=='ridge' and winner['parameters']=={'alpha':20.}
    save(OUT/'diagnostic_summary.json',dict(base_model_artifact_id=manifest['model_artifact_id'],hardening_policy=read(POLICY/'manifest.json'),
        selection_confirmed='VALIDATION_ONLY_RIDGE_ALPHA_20_NO_POST_TEST_TUNING',selection_lock_sha256=sha(EV/'selection_lock.json'),
        no_new_model_fit=True,no_prediction_adjustments=True,perturbation_count=len(perturb),questionable_perturbations=sum(r['assessment'].startswith('QUESTIONABLE') for r in perturb),
        bengaluru_count=10,bengaluru_outside_joint_support=sum('OUTSIDE_TRAIN_JOINT_SUPPORT_EMPIRICAL_REVIEW' in r['diagnostics'] for r in support_rows),
        bengaluru_negative_wallet_elasticity=sum(r['wallet_local_elasticity']<0 for r in support_rows),
        preservation=preserve(),recomputed_test_ood=reevaluated,
        behavior_gates=dict(wallet_monotonicity='FAIL',nondegenerate_training_allocation_target='FAIL' if bool((train.purchase_completion_fraction<1).all()) else 'PASS',
            bengaluru_joint_support='FAIL' if all('OUTSIDE_TRAIN_JOINT_SUPPORT_EMPIRICAL_REVIEW' in r['diagnostics'] for r in support_rows) else 'REVIEW',
            finite_theta_reference_feasibility='NOT_CERTIFIED'),
        final_status='PART_B_INTEGRATION_BLOCKED'))
    print('Diagnosis exported; original models/metrics unchanged; '+str(len(perturb))+' controlled probes.')

if __name__=='__main__':main()
