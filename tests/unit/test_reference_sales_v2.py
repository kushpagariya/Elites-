"""B.2 acceptance tests; no fitting or writes to prior versions."""
import copy
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch
import joblib
import numpy as np
import pandas as pd
from ml.training.reference_sales.features import FEATURES,DAYPART,FeatureValidationError
from ml.training.reference_sales_v2.simulator import generate,generate_market,sources,allocation,config
from ml.training.reference_sales_v2.train import ROOT,DATA,OUT,ART,read,sha,frame,preservation,reference_probe
from ml.inference.reference_sales_v2 import ReferenceSalesEstimatorV2


class V2Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg=pd.read_csv(DATA/'synthetic_regular.csv');cls.ood=pd.read_csv(DATA/'synthetic_shifted.csv')
        cls.split=pd.read_csv(DATA/'market_splits.csv');cls.adapter=ReferenceSalesEstimatorV2()
        cls.candidates=pd.read_csv(ROOT/'data/bengaluru/revised_v2/site_features_enriched.csv')

    def test_01_counts_new_identity_and_no_split_overlap(self):
        self.assertEqual((len(self.reg),self.reg.market_id.nunique(),len(self.ood),self.ood.market_id.nunique()),(2000,100,400,20))
        self.assertEqual(self.reg.groupby('market_id').size().unique().tolist(),[20])
        self.assertEqual(self.split.groupby('split').size().to_dict(),{'ood':20,'test':20,'train':60,'validation':20})
        self.assertEqual(self.split.market_id.nunique(),120)
        self.assertFalse(set(self.reg.observation_id)&set(pd.read_csv(ROOT/'ml/training/data/reference_sales_v1/synthetic_regular.csv').observation_id))

    def test_02_all_targets_feasible_conserved_and_uncapped(self):
        for df in [self.reg,self.ood]:
            self.assertTrue(np.isfinite(df.reference_annual_sales_inr).all())
            self.assertTrue((df.reference_annual_sales_inr>0).all())
            self.assertTrue((df.reference_annual_sales_inr<df.annual_wallet_inr).all())
            self.assertFalse(df.capacity_applied.any())
            np.testing.assert_array_equal(df.reference_annual_sales_inr,df.raw_pre_bound_sales_inr)
            np.testing.assert_allclose(df.reference_annual_sales_inr+df.allocated_external_inr+df.allocated_outside_inr,df.annual_wallet_inr,rtol=1e-13,atol=1e-5)
            self.assertTrue((df.max_cell_conservation_error_inr<1e-5).all())
        self.assertGreater(self.reg.reference_annual_sales_inr.std()/self.reg.reference_annual_sales_inr.mean(),.1)

    def test_03_simulator_wallet_scaling_and_competition(self):
        w=np.array([100.,200.]);d=np.array([200.,600.]);comp=np.array([[300.],[500.]])
        base=allocation(w,d,comp,500,.1)
        for factor in [.25,.5,1.25,3]:
            scaled=allocation(w*factor,d,comp,500,.1)
            self.assertAlmostEqual(scaled['reference_annual_sales_inr'],base['reference_annual_sales_inr']*factor,places=10)
        more=allocation(w,d,np.column_stack([comp,comp]),500,.1)
        self.assertLess(more['reference_annual_sales_inr'],base['reference_annual_sales_inr'])
        self.assertGreater(allocation(w,d,comp,500,.4)['reference_annual_sales_inr'],base['reference_annual_sales_inr'])

    def test_04_fitted_wallet_scaling_structural_all_candidates(self):
        model=self.adapter.model
        self.assertNotIn('annual_wallet_inr',model.features)
        for df in [self.reg.head(100),self.ood.head(100),self.candidates]:
            x=frame(df);base=model.predict(x)
            for scale in [0,.1,.5,1.25,2,10]:
                y=x.copy();y.annual_wallet_inr*=scale
                np.testing.assert_allclose(model.predict(y),base*scale,rtol=1e-13,atol=1e-6)

    def test_05_candidate_usable_scaling_and_support_invariance(self):
        for row in self.candidates.to_dict('records'):
            a=self.adapter.predict(row)
            for factor in [.5,1.25,2]:
                b=self.adapter.predict(dict(row,annual_wallet_inr=row['annual_wallet_inr']*factor))
                self.assertEqual(a['joint_support_pass'],b['joint_support_pass'])
                self.assertEqual(a['joint_distance'],b['joint_distance'])
                if a['reference_annual_sales_inr'] is not None:
                    self.assertAlmostEqual(b['reference_annual_sales_inr']/a['reference_annual_sales_inr'],factor,places=12)

    def test_06_no_candidate_or_own_branch_label_leakage(self):
        self.assertFalse(set(self.reg.observation_id)&set(self.candidates.site_id))
        self.assertTrue(self.reg.observation_id.str.startswith('v2-market-').all())
        self.assertFalse(set(self.adapter.model.features)&{'market_id','observation_id','generator_theta','reference_annual_sales_inr','candidate_x_m','candidate_y_m','capex_inr','source_quality_score'})
        self.assertTrue(all(m['own_branches']==0 and not m['alternatives_simultaneously_open'] for m in read(DATA/'markets.json')['markets']))
        # Source geometry resampling never consumes candidate feature rows.
        code=Path(ROOT/'ml/training/reference_sales_v2/simulator.py').read_text()
        self.assertNotIn('site_features_enriched.csv',code)

    def test_07_train_only_preprocessing_and_fixed_support(self):
        ids=set(self.split.loc[self.split.split=='train','market_id']);train=self.reg[self.reg.market_id.isin(ids)]
        model=self.adapter.model;numeric=[f for f in model.features if f!='store_format']
        imputer=model.preprocessor.named_transformers_['numeric'].named_steps['impute']
        np.testing.assert_allclose(imputer.statistics_,train[numeric].median().to_numpy(),rtol=1e-13)
        self.assertEqual(model.fit_rows,1200);self.assertEqual(self.adapter.support['fit_rows'],1200)
        self.assertEqual(self.adapter.support['quantile'],.99)
        self.assertEqual(read(OUT/'protocol_lock.json')['support_quantile'],config()['support_quantile'])
        for fmt,g in self.adapter.support['groups'].items():self.assertEqual(g['rows'],int((train.store_format==fmt).sum()))

    def test_08_validation_only_selection_and_actual_metrics(self):
        lock=read(OUT/'selection_lock.json');winner=min(lock['validation_trials'],key=lambda x:x['validation']['WAPE'])
        self.assertEqual(winner['family'],lock['selected_family']);self.assertEqual(winner['parameters'],lock['parameters'])
        self.assertFalse(lock['final_test_ood_used_for_selection'])
        from ml.training.reference_sales.metrics import regression_metrics
        pairs=pd.read_csv(OUT/'predictions.csv');metrics=read(OUT/'metrics.json')['models']
        for (name,split),p in pairs.groupby(['model','split']):
            m=regression_metrics(p.actual,p.raw_prediction_inr)
            self.assertAlmostEqual(m['WAPE'],metrics[name][split]['WAPE'],places=12)

    def test_09_all_models_bounds_and_same_saved_transform(self):
        for name in read(OUT/'metrics.json')['models']:
            model=joblib.load(ART/(name+'.joblib'));pred=model.predict(frame(self.ood))
            self.assertTrue(np.isfinite(pred).all());self.assertTrue((pred>=0).all());self.assertTrue((pred<=self.ood.annual_wallet_inr).all())
        x=frame(self.candidates);saved=joblib.load(ART/'preprocessor.joblib')
        np.testing.assert_array_equal(saved.transform(x[list(self.adapter.model.features)]),self.adapter.model.preprocessor.transform(x[list(self.adapter.model.features)]))

    def test_10_invalid_features_and_wrong_schema_rejected(self):
        row=self.candidates.iloc[0].to_dict()
        for key in FEATURES:
            bad=dict(row);del bad[key]
            with self.assertRaises(FeatureValidationError):self.adapter.predict(bad)
        for patch_values in [{'annual_wallet_inr':-1},{'population_1500m_est':None},{'store_format':'unknown'},{'store_size_sqm':float('inf')},{'annual_wallet_inr':True}]:
            with self.assertRaises(FeatureValidationError):self.adapter.predict(dict(row,**patch_values))
        with self.assertRaises(FeatureValidationError):self.adapter.predict(row,schema_version='old')

    def test_11_unknown_joint_geometry_never_silently_usable(self):
        row=self.candidates.iloc[0].to_dict();row['weekday_morning_raw']=1e12
        r=self.adapter.predict(row);self.assertFalse(r['joint_support_pass']);self.assertIsNone(r['reference_annual_sales_inr'])
        self.assertIsNotNone(r['raw_reference_annual_sales_inr']);self.assertFalse(r['prediction_adjustment']['applied'])

    def test_12_candidate_support_and_reference_endpoints(self):
        records=read(OUT/'bengaluru_readiness.json');self.assertEqual(len(records),10)
        for r in records:
            self.assertEqual(r['method_mode'],'model_simulated');self.assertEqual(r['prediction_units'],'INR/year')
            self.assertFalse(r['observed_target_available']);self.assertFalse(r['automatic_calibration_permitted'])
            if r['reference_annual_sales_inr'] is not None:
                self.assertLessEqual(r['raw_reference_annual_sales_inr'],r['wallet_upper_bound_inr'])
                self.assertLessEqual(r['reference_min_theta_sales_inr'],r['raw_reference_annual_sales_inr'])
                self.assertGreaterEqual(r['reference_max_theta_sales_inr'],r['raw_reference_annual_sales_inr'])

    def test_13_bad_reference_bracket_rejects_without_adjustment(self):
        row=self.candidates.iloc[0].to_dict();base=self.adapter.predict(row)
        r=self.adapter.predict(row,reference_bracket=(0,base['raw_reference_annual_sales_inr']/2))
        self.assertIsNone(r['reference_annual_sales_inr']);self.assertEqual(r['raw_reference_annual_sales_inr'],base['raw_reference_annual_sales_inr'])
        self.assertFalse(r['prediction_adjustment']['applied'])

    def test_14_full_generator_reproducibility(self):
        reg,ood,split,_=generate()
        for name,df in [('synthetic_regular.csv',reg),('synthetic_shifted.csv',ood),('market_splits.csv',split)]:
            import hashlib
            self.assertEqual(hashlib.sha256(df.to_csv(index=False,float_format='%.17g',lineterminator='\n').encode()).hexdigest(),sha(DATA/name))

    def test_15_ablation_is_real_and_same_family_parameters(self):
        ablation=read(OUT/'ablation.json');model=joblib.load(ART/'ablation.joblib')
        self.assertFalse(set(model.features)&set(DAYPART));self.assertEqual(model.parameters,self.adapter.model.parameters)
        self.assertEqual(model.fit_rows,1200);self.assertTrue(ablation['same_training_groups_and_selected_parameters'])

    def test_16_original_versions_and_public_contracts_unchanged(self):
        self.assertEqual(preservation(),294)
        self.assertEqual(sha(ROOT/'ml/inference/reference_sales.py'),read(OUT/'preservation.json')['files']['ml/inference/reference_sales.py'])

    def test_17_offline_local_artifact_and_no_orchestration(self):
        with patch.object(socket.socket,'connect',side_effect=AssertionError('offline')):
            r=ReferenceSalesEstimatorV2().predict(self.candidates.iloc[0].to_dict())
        self.assertEqual(r['model_artifact_id'],read(ART/'manifest.json')['model_artifact_id'])
        from backend.app.domain.pipeline import run_evaluation,run_portfolio
        with self.assertRaises(NotImplementedError):run_evaluation({}, {})
        with self.assertRaises(NotImplementedError):run_portfolio({}, {},1,[])

    def test_18_demand_shape_competition_and_daypart_probe_records(self):
        probes=read(OUT/'candidate_perturbations.json');self.assertEqual(len(probes),100)
        for row in probes:
            if row['change']=='wallet_x1.25':self.assertAlmostEqual(row['modified_raw']/row['base_raw'],1.25,places=12)
        self.assertEqual(len(set(self.reg.reference_annual_sales_inr)),2000)

    def test_19_selected_fit_reproducible_with_training_seed(self):
        from ml.training.reference_sales_v2.model import CaptureModel
        ids=set(self.split.loc[self.split.split=='train','market_id']);train=self.reg[self.reg.market_id.isin(ids)]
        original=self.adapter.model
        again=CaptureModel(original.family,original.parameters,original.seed).fit(frame(train),train.reference_annual_sales_inr)
        ids=set(self.split.loc[self.split.split=='validation','market_id']);validation=self.reg[self.reg.market_id.isin(ids)].head(40)
        np.testing.assert_allclose(again.predict(frame(validation)),original.predict(frame(validation)),rtol=1e-12,atol=1e-6)

if __name__=='__main__':unittest.main(verbosity=2)
