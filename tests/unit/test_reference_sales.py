"""Part B invariants and local artifact integration; never rewrite input data."""
import hashlib
import inspect
import io
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from ml.inference.reference_sales import ReferenceSalesEstimator, ModelUnavailableError
from ml.training.reference_sales.features import FEATURES, NUMERIC, DAYPART, TARGET, FeatureValidationError, feature_frame
from ml.training.reference_sales.metrics import regression_metrics
from ml.training.reference_sales.models import BoundedSalesModel
from ml.training.reference_sales.simulator import generate, generate_market, allocate_reference, config, CATEGORY_WEIGHTS, COUNT_MAP
from ml.training.reference_sales.train import ROOT, DATA, EVAL, ART, model_x, verify_preserved_inputs, sha


class ReferenceSalesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regular=pd.read_csv(DATA/'synthetic_regular.csv')
        cls.ood=pd.read_csv(DATA/'synthetic_shifted.csv')
        cls.splits=pd.read_csv(DATA/'market_splits.csv')
        cls.metrics=json.loads((EVAL/'metrics.json').read_text())
        cls.manifest=json.loads((ART/'manifest.json').read_text())
        cls.schema=json.loads((ART/'feature_schema.json').read_text())
        cls.predictions=pd.read_csv(EVAL/'heldout_predictions.csv')
        cls.canonical=pd.read_csv(ROOT/'data/bengaluru/revised_v2/site_features_enriched.csv')
        cls.adapter=ReferenceSalesEstimator()
        assignment=dict(zip(cls.splits['market_id'],cls.splits['split']))
        cls.frames={name:cls.regular[cls.regular['market_id'].map(assignment)==name].reset_index(drop=True) for name in ['train','validation','test']}
        cls.frames['ood']=cls.ood

    def test_01_regular_and_shifted_counts(self):
        self.assertEqual(len(self.regular),2000)
        self.assertEqual(self.regular['market_id'].nunique(),100)
        self.assertEqual(len(self.ood),400)
        self.assertEqual(self.ood['market_id'].nunique(),20)
        for frame in [self.regular,self.ood]:
            self.assertEqual(set(frame.groupby('market_id').size()),{20})
            self.assertEqual(frame['observation_id'].nunique(),len(frame))

    def test_02_grouped_splits_disjoint_and_proportional(self):
        sets={name:set(self.splits.loc[self.splits['split']==name,'market_id']) for name in ['train','validation','test','ood']}
        self.assertEqual([len(sets[name]) for name in sets],[60,20,20,20])
        self.assertEqual(len(self.splits),len(set(self.splits['market_id'])))
        for a in sets:
            for c in sets:
                if a!=c:self.assertFalse(sets[a]&sets[c])
        self.assertEqual([len(self.frames[name]) for name in sets],[1200,400,400,400])

    def test_03_no_showcase_or_own_branch_leakage(self):
        allrows=pd.concat([self.regular,self.ood],ignore_index=True)
        self.assertFalse(set(allrows['observation_id'])&set(self.canonical['site_id']))
        self.assertFalse(any(value.startswith('site-') for value in allrows['observation_id']))
        forbidden=['site_id','market_id','observation_id',TARGET,'allocated_external_inr','capacity_limit_inr','source_quality_score',
            'monthly_rent_inr','capex_inr','gross_margin_fraction','population_10min_est','accessible_households_est']
        self.assertFalse(set(FEATURES)&set(forbidden))
        self.assertFalse(any('branch' in f or 'own_' in f or 'future' in f for f in FEATURES))
        signatures=set(inspect.signature(allocate_reference).parameters)
        self.assertEqual(signatures,{'wallets','candidate_attraction','external_attraction','outside_attraction','capacity'})
        manifest=json.loads((DATA/'market_manifest.json').read_text())
        self.assertTrue(all(m['own_company_branches']==0 and not m['alternatives_simultaneously_open'] for m in manifest['markets']))

    def test_04_targets_nonnegative_and_wallet_bounded(self):
        for frame in [self.regular,self.ood]:
            self.assertTrue(np.isfinite(frame[TARGET]).all())
            self.assertTrue((frame[TARGET]>=0).all())
            self.assertTrue((frame[TARGET]<=frame['annual_wallet_inr']+1e-6).all())
            self.assertTrue((frame[TARGET]<=frame['capacity_limit_inr']+1e-6).all())
            np.testing.assert_allclose(frame['annual_wallet_inr'],frame['addressable_wallet_bound_inr'],rtol=1e-14)

    def test_05_spending_conservation_for_every_alternative(self):
        for frame in [self.regular,self.ood]:
            total=frame[TARGET]+frame['allocated_external_inr']+frame['allocated_outside_inr']
            np.testing.assert_allclose(total,frame['annual_wallet_inr'],rtol=1e-13,atol=1e-5)
            self.assertTrue((frame[['allocated_external_inr','allocated_outside_inr']]>=0).all().all())
            self.assertTrue(frame['purchase_completion_fraction'].between(0,1).all())
            self.assertTrue((frame['max_cell_conservation_error_inr']<1e-5).all())

    def test_06_hand_checked_allocator_and_capacity_outside_option(self):
        a=allocate_reference([100,200],[1,1],[1,1],1,1000)
        self.assertAlmostEqual(a[TARGET],100)
        self.assertAlmostEqual(a['allocated_external_inr'],100)
        self.assertAlmostEqual(a['allocated_outside_inr'],100)
        c=allocate_reference([100,200],[1,1],[1,1],1,40)
        self.assertAlmostEqual(c[TARGET],40)
        self.assertAlmostEqual(c['allocated_external_inr'],100)
        self.assertAlmostEqual(c['allocated_outside_inr'],160)
        z=allocate_reference([0],[1],[1],1,1)
        self.assertEqual(z[TARGET],0)
        for arguments in [([-1],[1],[1],1,1),([1],[1],[1],0,1),([1],[1],[-1],1,1),([1],[1],[1],1,-1),([float('nan')],[1],[1],1,1)]:
            with self.assertRaises(ValueError):allocate_reference(*arguments)

    def test_07_full_generation_reproducible_with_fixed_seed(self):
        regular,ood,splits,_=generate()
        for name,frame in [('synthetic_regular.csv',regular),('synthetic_shifted.csv',ood),('market_splits.csv',splits)]:
            expected=hashlib.sha256(frame.to_csv(index=False,float_format='%.17g',lineterminator='\n').encode()).hexdigest()
            self.assertEqual(expected,sha(DATA/name))
        cfg=config();cfg['seed']+=1
        altered,_=generate_market(0,cfg=cfg)
        self.assertNotEqual(altered[0][TARGET],self.regular.iloc[0][TARGET])

    def test_08_category_mapping_and_supported_daypart_matrix(self):
        approved=json.loads((ROOT/'data/demo/weights.json').read_text())['category_weights']
        categories=['office','shopping','leisure','school','hospital','transit']
        self.assertEqual(COUNT_MAP,(0,3,4,5,1,2))
        expected=np.array([[approved[c][k.removesuffix('_raw')] for k in DAYPART] for c in categories])
        np.testing.assert_array_equal(CATEGORY_WEIGHTS,expected)
        self.assertEqual(len(FEATURES),20)
        self.assertTrue(set(FEATURES)<=set(self.canonical))
        self.assertTrue(all(self.regular[f].nunique(dropna=True)>1 for f in FEATURES))

    def test_09_training_and_inference_schema_exact_match(self):
        self.assertEqual(self.schema['feature_allowlist'],list(FEATURES))
        self.assertEqual(self.manifest['feature_allowlist'],list(FEATURES))
        self.assertEqual(list(self.adapter.model.features),list(FEATURES))
        self.assertEqual(self.schema['canonical_input_columns'],list(self.canonical))
        frame=feature_frame(self.canonical.to_dict('records'),allowed_extra=self.schema['canonical_input_columns'])
        self.assertEqual(list(frame),list(FEATURES))

    def test_10_all_models_finite_nonnegative_bounded_predictions(self):
        for name in ['median','ridge','catboost','ablation_no_daypart']:
            if name=='catboost' and self.metrics['catboost_issues'] and not (ART/(name+'.joblib')).exists():continue
            model=joblib.load(ART/(name+'.joblib'))
            for frame in [self.frames['test'],self.ood]:
                pred=model.predict(model_x(frame,model.features))
                self.assertTrue(np.isfinite(pred).all())
                self.assertTrue((pred>=0).all())
                self.assertTrue((pred<=frame['annual_wallet_inr'].to_numpy()+1e-6).all())

    def test_11_preprocessing_fitted_only_on_training_markets(self):
        train=self.frames['train']
        for name in ['ridge','catboost','ablation_no_daypart']:
            if not (ART/(name+'.joblib')).exists():continue
            model=joblib.load(ART/(name+'.joblib'))
            numeric=[f for f in model.features if f in NUMERIC]
            imputer=model.transformer.named_transformers_['numeric'].named_steps['impute']
            self.assertEqual(model.fit_row_count,1200)
            np.testing.assert_allclose(imputer.statistics_,train[numeric].median().to_numpy(),rtol=1e-14)
            self.assertEqual(model.transformer.named_transformers_['numeric'].named_steps['scale'].n_samples_seen_,1200)
        self.assertEqual(set(self.manifest['training_market_ids']),set(train['market_id']))

    def test_12_selected_ridge_fitted_reproducibly(self):
        # Refit only the saved training partition; no held-out tuning.
        saved=joblib.load(ART/'ridge.joblib');train=self.frames['train']
        with threadpool_limits(limits=1):
            again=BoundedSalesModel('ridge',saved.parameters,saved.seed).fit(model_x(train),train[TARGET])
        np.testing.assert_allclose(saved.predict(model_x(self.frames['test'])),again.predict(model_x(self.frames['test'])),rtol=1e-11,atol=1e-5)

    def test_13_metrics_recomputed_from_saved_predictions(self):
        for (name,split),part in self.predictions.groupby(['model','split']):
            actual=part['actual_reference_annual_sales_inr'].to_numpy()
            predicted=part['predicted_reference_annual_sales_inr'].to_numpy()
            result=regression_metrics(actual,predicted);saved=self.metrics['metrics'][name][split]
            self.assertEqual(result['n'],saved['n'])
            for key in ['MAE_inr','RMSE_inr','WAPE','absolute_error_sum_inr','absolute_actual_sum_inr']:
                self.assertAlmostEqual(result[key]/max(1.,abs(saved[key])),saved[key]/max(1.,abs(saved[key])),places=12)

    def test_14_wape_formula_and_zero_denominator(self):
        m=regression_metrics([1,3],[2,1])
        self.assertEqual(m['WAPE'],.75)
        z=regression_metrics([0,0],[0,1])
        self.assertIsNone(z['WAPE'])
        self.assertEqual(z['WAPE_undefined_reason'],'ZERO_ABSOLUTE_ACTUAL_TARGET_SUM')
        self.assertTrue(np.isfinite(z['RMSE_inr']))

    def test_15_validation_only_model_selection_not_test_choice(self):
        lock=json.loads((EVAL/'selection_lock.json').read_text())
        fitted=[r for r in lock['search'] if r['status']=='FITTED']
        winner=min(fitted,key=lambda r:r['validation']['WAPE'])
        self.assertEqual(lock['selected_model'],winner['model'])
        self.assertEqual(lock['selected_parameters'],winner['parameters'])
        self.assertFalse(lock['test_and_ood_used_for_selection'])
        self.assertFalse(self.metrics['final_model_refit_on_validation'])
        self.assertEqual(sha(EVAL/'selection_lock.json'),self.manifest['selection_lock_sha256'])
        for record in lock['search']:self.assertNotIn('test',record)

    def test_16_actual_activation_gate_and_ood_warning(self):
        name=self.manifest['selected_model'];metric=self.metrics['metrics']
        gain=1-metric[name]['test']['WAPE']/metric['median']['test']['WAPE']
        self.assertAlmostEqual(gain,self.metrics['activation_gate']['relative_test_WAPE_gain'])
        self.assertEqual(self.metrics['activation_gate']['status'],'PASS' if gain>=.1 else 'FAIL')
        ratio=metric[name]['ood']['WAPE']/metric[name]['test']['WAPE']
        self.assertAlmostEqual(ratio,self.metrics['ood_test_WAPE_ratio'])
        self.assertEqual(ratio>2,self.manifest['ood_warning'])

    def test_17_daypart_ablation_same_protocol_actual_metrics(self):
        report=json.loads((EVAL/'daypart_ablation.json').read_text())
        self.assertEqual(report['removed_features'],list(DAYPART))
        without=joblib.load(ART/'ablation_no_daypart.joblib')
        self.assertEqual(list(without.features),[f for f in FEATURES if f not in DAYPART])
        self.assertEqual(without.parameters,self.adapter.model.parameters)
        self.assertEqual(without.fit_row_count,1200)
        for split in ['validation','test','ood']:
            result=regression_metrics(self.frames[split][TARGET],without.predict(model_x(self.frames[split],without.features)))
            self.assertAlmostEqual(result['WAPE'],report['splits'][split]['without_daypart']['WAPE'],places=12)

    def test_18_known_heldout_area_and_competition_perturbations(self):
        report=json.loads((EVAL/'perturbation_report.json').read_text())
        for key in ['store_size_plus_25pct','external_competition_added']:
            self.assertEqual(report[key]['changed_examples'],40)
            self.assertEqual(report[key]['expected_direction_examples'],40)
            self.assertEqual(report[key]['opposite_direction_examples'],0)
        # Wallet/daypart responses are measured but not asserted universally
        # monotonic: their observed opposite-direction cases are limitations.
        rows=pd.read_csv(EVAL/'heldout_perturbations.csv')
        np.testing.assert_allclose(rows['difference_inr'],rows['perturbed_reference_prediction_inr']-rows['original_reference_prediction_inr'],rtol=1e-8,atol=1e-5)

    def test_19_invalid_or_missing_features_never_imputed_as_measurements(self):
        row=self.canonical.iloc[0].to_dict()
        for change in [{'population_1500m_est':None},{'weekday_night_raw':None},{'annual_wallet_inr':float('inf')},{'store_size_sqm':True},{'competitor_count_1500m':1.5},{'store_format':'unsupported'},{'store_size_sqm':'575'}]:
            with self.assertRaises(FeatureValidationError):self.adapter.predict(dict(row,**change))
        broken=dict(row);del broken['annual_wallet_inr']
        with self.assertRaises(FeatureValidationError):self.adapter.predict(broken)
        with self.assertRaises(FeatureValidationError):self.adapter.predict(dict(row,own_branch_distance_m=50))
        with self.assertRaises(FeatureValidationError):self.adapter.predict(dict(row,reference_annual_sales_inr=1))
        with self.assertRaises(FeatureValidationError):self.adapter.predict(row,schema_version='wrong-version')

    def test_20_declared_zero_competitor_null_distance_is_supported(self):
        row=self.canonical.iloc[0].to_dict();row.update(competitor_count_1500m=0,competitor_attraction_index=0,nearest_competitor_distance_m=None)
        pred=self.adapter.predict(row)
        self.assertTrue(np.isfinite(pred['reference_annual_sales_inr']))
        self.assertIn('NO_MAPPED_COMPETITOR_NEAREST_DISTANCE_UNDEFINED',pred['diagnostics'])
        row['competitor_count_1500m']=1
        with self.assertRaises(FeatureValidationError):self.adapter.predict(row)

    def test_21_ignored_canonical_metadata_and_costs_cannot_drive_model(self):
        row=self.canonical.iloc[0].to_dict();base=self.adapter.predict(row)['reference_annual_sales_inr']
        changed=dict(row,site_id='different-context-id',monthly_rent_inr=9e12,capex_inr=0,source_quality_score=.01,
            accessible_households_est=None,population_10min_est=None)
        self.assertEqual(self.adapter.predict(changed)['reference_annual_sales_inr'],base)

    def test_22_all_ten_candidate_examples_are_honestly_labelled(self):
        examples=pd.read_csv(EVAL/'bengaluru_inference_examples.csv')
        self.assertEqual(len(examples),10)
        self.assertEqual(set(examples['site_id']),set(self.canonical['site_id']))
        self.assertEqual(set(examples['method_mode']),{'model_simulated'})
        self.assertEqual(set(examples['model_artifact_id']),{self.manifest['model_artifact_id']})
        self.assertTrue(examples['usage'].str.contains('NOT_ACHIEVED_SALES_NOT_A_RANKING').all())
        self.assertEqual(len(self.predictions),1200*len(self.metrics['metrics']))
        self.assertEqual(set(self.predictions['method_mode']),{'model_simulated'})

    def test_23_explicit_fallback_and_missing_artifact_error(self):
        row={k:v for k,v in self.canonical.iloc[0].to_dict().items() if k in FEATURES}
        with tempfile.TemporaryDirectory(prefix='reference-sales-test-',dir=EVAL) as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(EVAL.resolve()))
            with self.assertRaises(ModelUnavailableError):ReferenceSalesEstimator(tmp)
            fallback=ReferenceSalesEstimator(tmp,assumption_capture_fraction=.1)
            result=fallback.predict(row)
            self.assertEqual(result['method_mode'],'scenario_assumptions')
            self.assertIsNone(result['model_artifact_id'])
            self.assertAlmostEqual(result['reference_annual_sales_inr'],.1*row['annual_wallet_inr'])
            with self.assertRaises(FeatureValidationError):fallback.predict({k:v for k,v in row.items() if k!='population_1500m_est'})
        for value in [-1,1.1,float('nan'),True]:
            with self.assertRaises(ValueError):ReferenceSalesEstimator(assumption_capture_fraction=value)

    def test_24_local_artifact_checksums_and_corruption_detection(self):
        for name,expected in self.manifest['required_file_sha256'].items():self.assertEqual(sha(ART/name),expected)
        with tempfile.TemporaryDirectory(prefix='reference-sales-test-',dir=EVAL) as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(EVAL.resolve()))
            folder=Path(tmp)
            for path in ART.iterdir():
                if path.is_file():shutil.copyfile(path,folder/path.name)
            path=folder/self.manifest['selected_model_file'];path.write_bytes(path.read_bytes()+b'corruption')
            with self.assertRaises(ModelUnavailableError):ReferenceSalesEstimator(folder)

    def test_25_adapter_offline_and_no_backend_public_api_dependency(self):
        with patch.object(socket.socket,'connect',side_effect=AssertionError('Network prohibited')):
            adapter=ReferenceSalesEstimator()
            result=adapter.predict(self.canonical.iloc[0].to_dict())
        self.assertEqual(result['method_mode'],'model_simulated')
        self.assertEqual(result['uncertainty_status'],'NOT_CALIBRATED_FOR_REAL_MARKETS')
        for key in ['confidence','confidence_interval','net_profit','npv_inr','rank']:
            self.assertNotIn(key,result)
        from backend.app.domain.pipeline import run_evaluation,run_portfolio
        with self.assertRaises(NotImplementedError):run_evaluation({}, {})
        with self.assertRaises(NotImplementedError):run_portfolio({}, {},1,[])

    def test_26_fresh_python_process_reloads_without_notebook(self):
        row={k:v for k,v in self.canonical.iloc[0].to_dict().items() if k in FEATURES}
        code='import json,sys; from ml.inference.reference_sales import ReferenceSalesEstimator; print(json.dumps(ReferenceSalesEstimator().predict(json.load(sys.stdin))))'
        result=subprocess.run([sys.executable,'-B','-c',code],input=json.dumps(row),cwd=ROOT,text=True,capture_output=True,timeout=60,check=True)
        loaded=json.loads(result.stdout)
        self.assertEqual(loaded['reference_annual_sales_inr'],self.adapter.predict(row)['reference_annual_sales_inr'])
        self.assertEqual(loaded['model_artifact_id'],self.manifest['model_artifact_id'])

    def test_27_original_data_audits_contracts_and_git_unchanged(self):
        result=verify_preserved_inputs()
        self.assertEqual(result['files_checked'],233)
        self.assertEqual(result['files_unchanged'],233)
        self.assertEqual(result['branch'],'ML')
        self.assertEqual(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).strip(),'')
        self.assertEqual(self.canonical.shape,(10,70))
        self.assertEqual(int(self.canonical.isna().sum().sum()),24)
        for f in ['population_10min_est','accessible_households_est']:self.assertTrue(self.canonical[f].isna().all())

    def test_28_segment_metrics_are_executed_group_errors(self):
        segments=pd.read_csv(EVAL/'segment_metrics.csv')
        for r in segments[segments['segment']=='store_format'].to_dict('records'):
            frame=self.frames[r['split']];ids=set(frame.loc[frame['store_format']==r['value'],'observation_id'])
            p=self.predictions[(self.predictions['model']==r['model'])&(self.predictions['split']==r['split'])&self.predictions['observation_id'].isin(ids)]
            computed=regression_metrics(p['actual_reference_annual_sales_inr'],p['predicted_reference_annual_sales_inr'])
            self.assertEqual(computed['n'],r['n'])
            self.assertAlmostEqual(computed['WAPE'],r['WAPE'],places=12)

    def test_29_latency_is_measured_with_protocol(self):
        for name,record in self.metrics['latency'].items():
            self.assertEqual(record['repetitions'],50)
            self.assertEqual(record['batch_size'],1)
            self.assertEqual(record['unit'],'milliseconds')
            self.assertGreater(record['p50'],0)
            self.assertGreaterEqual(record['p95'],record['p50'])


if __name__=='__main__':unittest.main(verbosity=2)
