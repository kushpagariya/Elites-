"""New frozen B.2 experiment; no writes to any A/B/B.1 output."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from ml.training.reference_sales.features import FEATURES,NUMERIC,DAYPART,feature_frame,feature_schema
from ml.training.reference_sales.metrics import regression_metrics
from .simulator import generate,config,ROOT
from .model import CaptureModel,CAPTURE_FEATURES

DATA=ROOT/'ml/training/data/reference_sales_v2'
OUT=ROOT/'ml/evaluation/reference_sales_v2'
ART=ROOT/'ml/artifacts/reference_sales_v2'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def clean(x):
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(tuple,list,np.ndarray)):return [clean(v) for v in x]
    if isinstance(x,np.generic):x=x.item()
    return None if isinstance(x,float) and not np.isfinite(x) else x
def save(p,x):p.write_text(json.dumps(clean(x),indent=2,allow_nan=False),encoding='utf-8')
def csv(p,frame):pd.DataFrame(frame).to_csv(p,index=False,float_format='%.17g',lineterminator='\n')
def frame(df,features=FEATURES):return feature_frame(df[list(features)].to_dict('records'),features=features)

def preservation():
    s=read(OUT/'preservation.json')
    changed=[p for p,h in s['files'].items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
    assert not changed,changed
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==s['head']
    assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='ML'
    return len(s['files'])

def old_diagnosis():
    regular=pd.read_csv(ROOT/'ml/training/data/reference_sales_v1/synthetic_regular.csv')
    shifted=pd.read_csv(ROOT/'ml/training/data/reference_sales_v1/synthetic_shifted.csv')
    rows=[];stats={}
    for name,df in [('regular',regular),('ood',shifted)]:
        raw=df.unconstrained_candidate_sales_inr;cap=df.capacity_limit_inr;y=df.reference_annual_sales_inr
        stats[name]=dict(rows=len(df),raw_capacity_ratio=(raw/cap).describe(percentiles=[.01,.25,.5,.75,.99]).to_dict(),
            final_capacity_ratio=(y/cap).describe().to_dict(),capped_rows=int((df.purchase_completion_fraction<1).sum()),
            raw_exceeds_wallet=int((raw>df.annual_wallet_inr+1e-5).sum()),near_zero=int((y<1).sum()),
            mean_within_market_sales_std=float(df.groupby('market_id').reference_annual_sales_inr.std().mean()),
            between_market_mean_sales_std=float(df.groupby('market_id').reference_annual_sales_inr.mean().std()),
            target_spearman={f:float(df[f].corr(y,method='spearman')) for f in ['annual_wallet_inr','competitor_attraction_index','store_size_sqm','mean_wallet_weighted_distance_m',*DAYPART]})
        for r in df.to_dict('records'):
            rows.append(dict(regime=name,market_id=r['market_id'],observation_id=r['observation_id'],raw_pre_bound_target_inr=r['unconstrained_candidate_sales_inr'],
                capacity_inr=r['capacity_limit_inr'],final_target_inr=r['reference_annual_sales_inr'],annual_wallet_inr=r['annual_wallet_inr']))
    csv(OUT/'v1_capacity_audit.csv',rows);save(OUT/'v1_root_cause.json',stats)

def make_support(model,train,cfg):
    design=model.preprocessor.transform(frame(train)[list(model.features)])
    groups={}
    for fmt in sorted(train.store_format.unique()):
        mask=train.store_format.to_numpy()==fmt;xx=design[mask]
        d=NearestNeighbors(n_neighbors=2).fit(xx).kneighbors(xx)[0][:,1]
        groups[fmt]=dict(design=xx.tolist(),loo_distance_p99=float(np.quantile(d,cfg['support_quantile'])),rows=len(xx))
    return dict(groups=groups,rule=cfg['support_rule'],quantile=cfg['support_quantile'],fit_rows=len(train),
        capture_features=list(model.features),training_numeric_ranges={f:dict(min=float(train[f].min()),max=float(train[f].max())) for f in NUMERIC},
        wallet_excluded_from_joint_support='Scaling a fixed market wallet is a proven structural transformation, not a change in capture-feature geometry',
        calibrated_probability=False)

def reference_probe(row):
    """Two endpoint checks only: no calibration/bisection or network engine."""
    cells=pd.read_csv(ROOT/'data/bengaluru/final/spending_cells.csv')
    pois=pd.read_csv(ROOT/'data/bengaluru/final/pois.csv');comp=pois[pois.category=='competitor']
    def haversine(lat1,lon1,lat2,lon2):
        p1=np.deg2rad(lat1);p2=np.deg2rad(lat2);dl=np.deg2rad(lon2-lon1)
        a=np.sin((p2-p1)/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
        return 6371008.8*2*np.arcsin(np.sqrt(np.minimum(1,a)))
    d=haversine(row['latitude'],row['longitude'],cells.latitude.to_numpy(),cells.longitude.to_numpy())
    dc=haversine(cells.latitude.to_numpy()[:,None],cells.longitude.to_numpy()[:,None],comp.latitude.to_numpy()[None,:],comp.longitude.to_numpy()[None,:])
    external=np.exp(-dc/750).sum(axis=1);base=row['store_size_sqm']/100*np.exp(-d/750)
    values=[]
    for theta in [-30,30]:
        attraction=np.exp(theta)*base
        values.append(float(np.dot(cells.annual_wallet_inr.to_numpy(),attraction/(1+external+attraction))))
    return dict(reference_min_theta_sales_inr=values[0],reference_max_theta_sales_inr=values[1],
        reference_grid_wallet_inr=float(cells.annual_wallet_inr.sum()),cell_count=len(cells),competitor_count=len(comp),
        assumptions='Existing 100 cell-centroid wallets; all mapped external grocery POIs as equal unit masses (100sqm, theta0); gamma1/tau750/outside1. Preliminary point approximation, not production calibration.')

def main():
    preservation()
    for p in [DATA,ART]:p.mkdir(parents=True,exist_ok=True)
    cfg=config();old_diagnosis()
    # Record exact source evidence and its historical/assumed status.
    sources=['pois.csv','spending_cells.csv','poi_daypart_availability.csv','daypart_weights.csv']
    save(OUT/'source_evidence.json',dict(source_files={n:sha(ROOT/'data/bengaluru/final'/n) for n in sources},
        population='WorldPop 2020 modelled 1km, historical; population-cell distribution derived with assumptions',
        spending='HCES 2023-24 nominal state urban proxy, transferred locally; no inflation conversion',
        pois='OSM partial mapped POIs and recorded/assumed schedules; resampled records are synthetic, not new observations',
        store_area='Synthetic approved demonstration area, not observed premises; ranges expanded as explicit simulation assumptions',
        candidate_use='Ten unlabelled rows are schema/range/support diagnostics only; no coordinate/feature row is copied into labels',
        limitations='All markets reuse a perturbed empirical regional template; grouped synthetic tests do not establish independent-city generalisation.'))
    canonical=pd.read_csv(ROOT/'data/bengaluru/revised_v2/site_features_enriched.csv')
    csv(OUT/'bengaluru_source_ranges.csv',[dict(feature=f,min=float(canonical[f].min()),median=float(canonical[f].median()),max=float(canonical[f].max()),used_for_capture=f in CAPTURE_FEATURES) for f in NUMERIC])
    regular,ood,splits,markets=generate(cfg)
    csv(DATA/'synthetic_regular.csv',regular);csv(DATA/'synthetic_shifted.csv',ood);csv(DATA/'market_splits.csv',splits)
    save(DATA/'markets.json',dict(config=cfg,markets=markets))
    mapping=dict(zip(splits.market_id,splits.split));parts={n:regular[regular.market_id.map(mapping)==n].reset_index(drop=True) for n in ['train','validation','test']};parts['ood']=ood
    save(OUT/'protocol_lock.json',dict(configuration_sha256=sha(Path(__file__).with_name('config.json')),splits_sha256=sha(DATA/'market_splits.csv'),
        selection='VALIDATION_ONLY',support_quantile=cfg['support_quantile'],preprocessing='train-only; wallet never a capture predictor',final_test_ood_used_for_tuning=False))
    models={};search=[];issues=[]
    for name,grid in [('median',[{}]),('ridge',[dict(alpha=a) for a in cfg['ridge_alphas']]),('catboost',cfg['catboost_grid'])]:
        for parameters in grid:
            try:
                model=CaptureModel(name,parameters,cfg['model_seed']).fit(frame(parts['train']),parts['train'].reference_annual_sales_inr)
                score=regression_metrics(parts['validation'].reference_annual_sales_inr,model.predict(frame(parts['validation'])))
                search.append(dict(family=name,parameters=parameters,validation=score))
                if name not in models or score['WAPE']<models[name][1]['WAPE']:models[name]=(model,score)
            except Exception as e:
                if name!='catboost':raise
                issues.append(dict(family=name,parameters=parameters,error=repr(e)))
    selected=min(models,key=lambda n:models[n][1]['WAPE']);best=models[selected][0]
    save(OUT/'selection_lock.json',dict(selected_family=selected,parameters=best.parameters,validation_trials=search,issues=issues,
        final_test_ood_used_for_selection=False,selection='Lowest validation INR WAPE among wallet-homogeneous, finite sigmoid-share estimators'))
    metrics={};predictions=[];segments=[]
    for name,(model,_) in models.items():
        metrics[name]={}
        for split in ['validation','test','ood']:
            df=parts[split];pred=model.predict(frame(df));metrics[name][split]=regression_metrics(df.reference_annual_sales_inr,pred)
            for r,v in zip(df.to_dict('records'),pred):predictions.append(dict(model=name,split=split,observation_id=r['observation_id'],market_id=r['market_id'],actual=r['reference_annual_sales_inr'],raw_prediction_inr=float(v),wallet_inr=r['annual_wallet_inr'],method_mode='model_simulated'))
            for fmt in sorted(df.store_format.unique()):
                mask=df.store_format.to_numpy()==fmt;segments.append(dict(model=name,split=split,format=fmt,**regression_metrics(df.reference_annual_sales_inr[mask],pred[mask])))
        joblib.dump(model,ART/(name+'.joblib'),compress=3)
    no_dp=tuple(f for f in CAPTURE_FEATURES if f not in DAYPART)
    ablated=CaptureModel(selected,best.parameters,cfg['model_seed'],features=no_dp).fit(frame(parts['train']),parts['train'].reference_annual_sales_inr)
    ablation={s:dict(full=metrics[selected][s],without_dayparts=regression_metrics(parts[s].reference_annual_sales_inr,ablated.predict(frame(parts[s])))) for s in ['validation','test','ood']}
    save(OUT/'ablation.json',dict(removed=list(DAYPART),same_training_groups_and_selected_parameters=True,not_a_retroactive_selection_candidate=True,metrics=ablation));joblib.dump(ablated,ART/'ablation.joblib',compress=3)
    csv(OUT/'predictions.csv',predictions);csv(OUT/'segments.csv',segments)
    schema=feature_schema(canonical.columns);schema.update(schema_version='reference-sales-features-v2',capture_features=list(CAPTURE_FEATURES),wallet_scale_field='annual_wallet_inr',wallet_homogeneity='EXACT_FOR_FIXED_CAPTURE_FEATURES')
    save(ART/'feature_schema.json',schema);save(ART/'support.json',make_support(best,parts['train'],cfg))
    model_file=selected+'.joblib';model_sha=sha(ART/model_file);gate=1-metrics[selected]['test']['WAPE']/metrics['median']['test']['WAPE']
    manifest=dict(model_artifact_id='reference-sales-sim-v2-'+model_sha[:12],method_mode='model_simulated',selected_family=selected,selected_parameters=best.parameters,
        selected_file=model_file,required_sha256={n:sha(ART/n) for n in [model_file,'feature_schema.json','support.json']},activation_relative_test_gain=gate,activation_passed=gate>=.1,
        test_ood_ratio=metrics[selected]['ood']['WAPE']/metrics[selected]['test']['WAPE'],base_versions_preserved=True,model_prediction_policy='raw sigmoid capture times wallet; no post-hoc clipping',
        versions={n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','scikit-learn','catboost','joblib']})
    save(ART/'manifest.json',manifest)
    # Export explicit learned preprocessing as well as its complete fitted wrapper.
    joblib.dump(best.preprocessor,ART/'preprocessor.joblib',compress=3)
    save(ART/'preprocessing.json',dict(fit_rows=best.fit_rows,feature_names=best.preprocessor.get_feature_names_out().tolist(),
        median_imputation=best.preprocessor.named_transformers_['numeric'].named_steps['impute'].statistics_.tolist(),
        standard_scale_mean=best.preprocessor.named_transformers_['numeric'].named_steps['scale'].mean_.tolist()))
    from ml.inference.reference_sales_v2 import ReferenceSalesEstimatorV2
    adapter=ReferenceSalesEstimatorV2();candidates=[];perturbations=[]
    for r in canonical.to_dict('records'):
        probe=reference_probe(r);answer=adapter.predict(r,reference_bracket=(probe['reference_min_theta_sales_inr'],probe['reference_max_theta_sales_inr']))
        candidates.append(dict(site_id=r['site_id'],**answer,**probe,observed_target_available=False))
        for label,patch in [('wallet_x0.5',dict(annual_wallet_inr=r['annual_wallet_inr']*.5)),('wallet_x1.25',dict(annual_wallet_inr=r['annual_wallet_inr']*1.25)),('area_x1.25',dict(store_size_sqm=r['store_size_sqm']*1.25)),
            ('competition_plus5',dict(competitor_count_1500m=r['competitor_count_1500m']+5,competitor_attraction_index=r['competitor_attraction_index']+2,nearest_competitor_distance_m=min(r['nearest_competitor_distance_m'],750)))]+[(b+'_x1.25',{b:r[b]*1.25}) for b in DAYPART]:
            changed=adapter.predict(dict(r,**patch));perturbations.append(dict(site_id=r['site_id'],change=label,changed_fields=patch,base_raw=answer['raw_reference_annual_sales_inr'],modified_raw=changed['raw_reference_annual_sales_inr'],usable=changed['reference_annual_sales_inr'],warnings=changed['warnings']))
    save(OUT/'bengaluru_readiness.json',candidates);save(OUT/'candidate_perturbations.json',perturbations)
    x=frame(parts['test'].head(1));times=[]
    for _ in range(5):best.predict(x)
    for _ in range(50):
        start=time.perf_counter_ns();best.predict(x);times.append((time.perf_counter_ns()-start)/1e6)
    save(OUT/'metrics.json',dict(method_mode='model_simulated',models=metrics,selected=selected,activation_passed=gate>=.1,relative_test_gain=gate,
        latency_ms=dict(p50=float(np.median(times)),p95=float(np.quantile(times,.95)),calls=50,warmups=5,batch_size=1),catboost_issues=issues,
        target_diagnostics=dict(no_cap=True,nonpositive_targets=int((regular.reference_annual_sales_inr<=0).sum()),max_wallet_capture=float((regular.reference_annual_sales_inr/regular.annual_wallet_inr).max()),
            target_relative_std=float(regular.reference_annual_sales_inr.std()/regular.reference_annual_sales_inr.mean()),mean_within_market_std=float(regular.groupby('market_id').reference_annual_sales_inr.std().mean())),
        candidate_supported=sum(r['joint_support_pass'] for r in candidates),candidate_usable=sum(r['reference_annual_sales_inr'] is not None for r in candidates),preserved_files=preservation()))
    print(json.dumps(dict(selected=selected,test_wape=metrics[selected]['test']['WAPE'],ood_wape=metrics[selected]['ood']['WAPE'],activation=gate>=.1,candidate_supported=sum(r['joint_support_pass'] for r in candidates),candidate_usable=sum(r['reference_annual_sales_inr'] is not None for r in candidates)),indent=2))

if __name__=='__main__':main()
