"""B.1 engineering safety tests; behavioral failures are separately reported."""
import copy
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
import joblib
import numpy as np
import pandas as pd
from ml.inference.reference_sales import ReferenceSalesEstimator,ModelUnavailableError
from ml.inference.reference_sales_safety import raw_predictions,ridge_wallet_elasticity,joint_support_score,load_policy
from ml.training.reference_sales.features import FEATURES,DAYPART,FeatureValidationError
from ml.training.reference_sales.train import model_x
from ml.evaluation.reference_sales_b1.run_hardening import ROOT,OUT,OLD,POLICY,DATA,EV,read,sha,preserve


class B1SafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter=ReferenceSalesEstimator();cls.canonical=pd.read_csv(ROOT/'data/bengaluru/revised_v2/site_features_enriched.csv')
        cls.row=cls.canonical.iloc[0].to_dict();cls.diagnosis=read(OUT/'diagnostic_summary.json')
        cls.perturb=pd.read_csv(OUT/'controlled_perturbations.csv')
        cls.regular=pd.read_csv(DATA/'synthetic_regular.csv');cls.ood=pd.read_csv(DATA/'synthetic_shifted.csv')

    def test_01_local_selected_artifact_id_and_no_replacement(self):
        m=read(OLD/'manifest.json');self.assertEqual(m['selected_model'],'ridge')
        self.assertEqual(self.adapter.manifest['model_artifact_id'],'reference-sales-sim-v1-3f162d1da91a')
        self.assertEqual(self.adapter.model.parameters,{'alpha':20.})
        self.assertEqual(sha(OLD/'ridge.joblib'),read(POLICY/'manifest.json')['base_model_sha256'])

    def test_02_schema_and_missing_or_invalid_inputs(self):
        for key in FEATURES:
            row=copy.deepcopy(self.row);del row[key]
            with self.assertRaises(FeatureValidationError):self.adapter.predict(row)
        for patch_values in [{'annual_wallet_inr':-1},{'annual_wallet_inr':float('inf')},{'store_size_sqm':True},{'weekday_night_raw':None},{'store_format':'unknown'}]:
            with self.assertRaises(FeatureValidationError):self.adapter.predict(dict(self.row,**patch_values))
        with self.assertRaises(FeatureValidationError):self.adapter.predict(dict(self.row,own_branch_distance_m=1))
        with self.assertRaises(FeatureValidationError):self.adapter.predict(self.row,schema_version='bad')

    def test_03_units_and_distinct_spending_wallet_and_store_sales(self):
        r=self.adapter.predict(self.row)
        self.assertEqual(r['prediction_units'],'INR/year')
        self.assertEqual(r['addressable_wallet_inr'],self.row['annual_wallet_inr'])
        self.assertLess(r['reference_annual_sales_inr'],r['addressable_wallet_inr'])
        self.assertEqual(r['method_mode'],'model_simulated')
        self.assertEqual(r['wallet_price_basis'],'INHERITED_FROM_INPUT_WALLET_NO_CONVERSION')

    def test_04_all_raw_predictions_finite_nonnegative_and_bounded(self):
        for frame in [self.regular,self.ood,self.canonical]:
            x=model_x(frame);raw=raw_predictions(self.adapter.model,x)
            self.assertTrue(np.isfinite(raw).all());self.assertTrue((raw>=0).all())
            self.assertTrue((raw<=x.annual_wallet_inr.to_numpy()).all())
            np.testing.assert_allclose(raw,self.adapter.model.predict(x),rtol=0,atol=0)

    def test_05_supplied_reference_bound_rejects_without_clipping(self):
        base=self.adapter.predict(self.row);raw=base['reference_annual_sales_inr']
        rejected=self.adapter.predict(self.row,reference_wallet_bound_inr=raw/2)
        self.assertIsNone(rejected['reference_annual_sales_inr'])
        self.assertEqual(rejected['raw_reference_annual_sales_inr'],raw)
        self.assertEqual(rejected['integration_status'],'UNAVAILABLE')
        self.assertFalse(rejected['prediction_adjustment']['applied'])
        self.assertFalse(rejected['numerical_and_wallet_bounds_valid'])
        accepted=self.adapter.predict(self.row,reference_wallet_bound_inr=raw*2)
        self.assertEqual(accepted['raw_reference_annual_sales_inr'],raw)
        self.assertIn('UNVERIFIED',accepted['reference_allocation_feasibility'])
        for value in [-1,float('inf'),True]:
            with self.assertRaises(FeatureValidationError):self.adapter.predict(self.row,reference_wallet_bound_inr=value)

    def test_06_invalid_raw_never_becomes_usable(self):
        for value in [-1,float('nan'),float('inf'),self.row['annual_wallet_inr']*2]:
            with patch('ml.inference.reference_sales.raw_predictions',return_value=np.array([value])):
                r=self.adapter.predict(self.row)
            self.assertIsNone(r['reference_annual_sales_inr']);self.assertFalse(r['usable_for_automatic_integration'])
            self.assertEqual(r['integration_status'],'UNAVAILABLE')
            self.assertFalse(r['prediction_adjustment']['applied'])

    def test_07_wallet_derivative_matches_finite_difference(self):
        x=model_x(self.regular.head(100));eps=1e-4
        analytic=ridge_wallet_elasticity(self.adapter.model,x)
        plus=x.copy();minus=x.copy();plus.annual_wallet_inr*=1+eps;minus.annual_wallet_inr*=1-eps
        finite=(np.log(raw_predictions(self.adapter.model,plus))-np.log(raw_predictions(self.adapter.model,minus)))/(np.log(1+eps)-np.log(1-eps))
        np.testing.assert_allclose(analytic,finite,rtol=1e-5,atol=1e-7)

    def test_08_known_negative_wallet_response_is_flagged_not_hidden(self):
        rows=self.perturb[(self.perturb.perturbation=='wallet_x1.25')&(self.perturb.delta_inr<0)]
        self.assertGreater(len(rows),0)
        row=json.loads(rows.iloc[0]['modified_features_json']);r=self.adapter.predict(row)
        self.assertIn('NEGATIVE_LOCAL_WALLET_RESPONSE_REQUIRES_REVIEW',r['diagnostics'])
        self.assertFalse(r['usable_for_automatic_integration'])
        self.assertEqual(r['reference_annual_sales_inr'],r['raw_reference_annual_sales_inr'])

    def test_09_competition_probes_preserve_recorded_input_changes(self):
        rows=self.perturb[self.perturb.perturbation=='competition_plus5'];self.assertEqual(len(rows),410)
        for r in rows.to_dict('records'):
            a=json.loads(r['original_features_json']);b=json.loads(r['modified_features_json'])
            self.assertEqual(b['competitor_count_1500m'],a['competitor_count_1500m']+5)
            self.assertEqual(b['annual_wallet_inr'],a['annual_wallet_inr'])
        self.assertTrue((rows.delta_inr<0).all())

    def test_10_each_daypart_varied_independently_and_not_forced_positive(self):
        for name in DAYPART:
            rows=self.perturb[self.perturb.perturbation==name+'_x1.25'];self.assertEqual(len(rows),410)
            r=rows.iloc[0];a=json.loads(r.original_features_json);b=json.loads(r.modified_features_json)
            self.assertEqual({k for k in a if a[k]!=b[k]},{name})
            self.assertAlmostEqual(b[name],a[name]*1.25)
            self.assertEqual(r.assessment,'CONTEXT_DEPENDENT_NOT_A_CAUSAL_CLAIM')

    def test_11_training_inference_preprocessing_agree(self):
        stored=joblib.load(OLD/'preprocessor.joblib');x=model_x(self.canonical)
        np.testing.assert_array_equal(stored.transform(x),self.adapter.model.transformer.transform(x))
        split=pd.read_csv(DATA/'market_splits.csv');ids=set(split.loc[split.split=='train','market_id'])
        self.assertEqual(set(self.adapter.support_policy['training_market_ids']),ids)
        self.assertFalse(self.adapter.support_policy['model_refitted']);self.assertFalse(self.adapter.support_policy['preprocessing_refitted'])

    def test_12_bengaluru_examples_unlabelled_and_all_warned(self):
        results=self.adapter.predict_many(self.canonical.to_dict('records'));self.assertEqual(len(results),10)
        for r in results:
            self.assertIn('OUTSIDE_TRAIN_JOINT_SUPPORT_EMPIRICAL_REVIEW',r['diagnostics'])
            self.assertFalse(r['usable_for_automatic_integration'])
            self.assertEqual(r['integration_status'],'INTEGRATION_BLOCKED')
            self.assertTrue(r['numerical_and_wallet_bounds_valid'])
        self.assertTrue(all(r['accuracy_not_evaluated'] for r in read(OUT/'bengaluru_support.json')))

    def test_13_support_warning_is_empirical_and_reproducible(self):
        a=self.adapter.predict(self.row);b=ReferenceSalesEstimator().predict(self.row)
        self.assertEqual(a,b)
        self.assertIn('NOT_CALIBRATED',a['support_warning_interpretation'])
        self.assertNotIn('confidence',a)
        self.assertGreater(a['empirical_joint_support_squared_distance'],self.adapter.support_policy['training_squared_distance_p99'])

    def test_14_original_bytes_contracts_and_current_git_preserved(self):
        result=preserve();self.assertEqual(result['existing_files_checked'],273)
        self.assertEqual(sha(OUT/'original_reference_sales.py.txt'),read(OUT/'preservation.json')['files']['ml/inference/reference_sales.py'])

    def test_15_validation_selection_and_original_metrics_unchanged(self):
        lock=read(EV/'selection_lock.json');winner=min([r for r in lock['search'] if r['status']=='FITTED'],key=lambda x:x['validation']['WAPE'])
        self.assertEqual(winner['model'],'ridge');self.assertEqual(winner['parameters'],{'alpha':20.})
        self.assertFalse(lock['test_and_ood_used_for_selection'])
        self.assertEqual(sha(EV/'selection_lock.json'),self.diagnosis['selection_lock_sha256'])
        for family in ['ridge','catboost']:
            for split in ['test','ood']:
                self.assertAlmostEqual(self.diagnosis['recomputed_test_ood'][family][split]['WAPE'],read(EV/'metrics.json')['metrics'][family][split]['WAPE'],places=13)

    def test_16_capacity_degenerate_targets_are_not_misrepresented(self):
        markets=read(DATA/'market_manifest.json')['markets'];density={r['market_id']:r['annual_capacity_inr_per_sqm'] for r in markets}
        splits=pd.read_csv(DATA/'market_splits.csv');assignment=dict(zip(splits.market_id,splits.split))
        saturated=self.regular[self.regular.market_id.map(assignment).isin(['train','test'])]
        for frame in [saturated,self.ood]:
            self.assertTrue((frame.purchase_completion_fraction<1).all())
            np.testing.assert_allclose(frame.reference_annual_sales_inr,frame.store_size_sqm*frame.market_id.map(density),rtol=1e-14,atol=1e-6)
        self.assertEqual(int((self.regular.purchase_completion_fraction==1).sum()),3)
        self.assertEqual(self.diagnosis['behavior_gates']['nondegenerate_training_allocation_target'],'FAIL')
        self.assertIn('INTEGRATION_BLOCK:ALL_TRAINING_TARGETS_CAPACITY_SATURATED',self.adapter.predict(self.row)['diagnostics'])

    def test_17_no_network_or_orchestration_implementation(self):
        with patch.object(socket.socket,'connect',side_effect=AssertionError('Network disabled')):
            self.assertEqual(ReferenceSalesEstimator().predict(self.row)['method_mode'],'model_simulated')
        from backend.app.domain.pipeline import run_evaluation,run_portfolio
        with self.assertRaises(NotImplementedError):run_evaluation({}, {})
        with self.assertRaises(NotImplementedError):run_portfolio({}, {},1,[])

    def test_18_explicit_fallback_and_no_fabricated_missing_features(self):
        row={k:self.row[k] for k in FEATURES}
        with tempfile.TemporaryDirectory(dir=OUT,prefix='b1-test-') as tmp:
            self.assertTrue(Path(tmp).resolve().is_relative_to(OUT.resolve()))
            with self.assertRaises(ModelUnavailableError):ReferenceSalesEstimator(tmp)
            fallback=ReferenceSalesEstimator(tmp,assumption_capture_fraction=.1);r=fallback.predict(row)
            self.assertEqual(r['method_mode'],'scenario_assumptions');self.assertIsNone(r['model_artifact_id'])
            self.assertFalse(r['usable_for_automatic_integration'])
            broken=dict(row);del broken['population_1500m_est']
            with self.assertRaises(FeatureValidationError):fallback.predict(broken)

    def test_19_invalid_bound_batch_and_zero_wallet(self):
        with self.assertRaises(FeatureValidationError):self.adapter.predict_many([self.row],reference_wallet_bounds_inr=[])
        row=dict(self.row,annual_wallet_inr=0);r=self.adapter.predict(row)
        self.assertEqual(r['reference_annual_sales_inr'],0)
        self.assertEqual(r['raw_reference_annual_sales_inr'],0)
        self.assertFalse(r['prediction_adjustment']['applied'])

    def test_20_behavior_failures_and_probe_coverage_are_explicit(self):
        self.assertEqual(self.diagnosis['final_status'],'PART_B_INTEGRATION_BLOCKED')
        self.assertEqual(self.diagnosis['behavior_gates']['wallet_monotonicity'],'FAIL')
        self.assertEqual(len(self.perturb),7388)
        self.assertTrue(any(self.perturb.perturbation.str.contains('outside_max')))
        self.assertEqual(int(self.perturb.assessment.str.startswith('QUESTIONABLE').sum()),271)

if __name__=='__main__':unittest.main(verbosity=2)
