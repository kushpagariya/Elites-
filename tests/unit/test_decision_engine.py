"""Independent arithmetic, leakage, saved-context and actual fitted-path checks."""
from copy import deepcopy
from datetime import date
from itertools import combinations
import json
import unittest
from unittest.mock import patch
import numpy as np

from backend.app.domain.geospatial.features import distances, daypart_profiles, TIME_BINS
from backend.app.domain.network.allocation import allocate, calibrate, network_cashflows
from backend.app.domain.scenario.timing import active_fractions, add_months, infrastructure_multipliers
from backend.app.domain.failfast.rules import diagnose, rent_rescue, sales_rescue
from backend.app.domain.portfolio.search import enumerate_portfolios, paise
from backend.app.domain.pipeline import prepare_evaluation, run_evaluation, run_portfolio, calculate_rescue
from backend.app.domain.validation import DomainUnavailable, digest


def fixture():
    """Deliberately assumed test targets, never exported as fitted model evidence."""
    sites = [dict(site_id=f's{i}', name=f'Synthetic test {i}', latitude=12., longitude=77.+i*.001,
                  store_size_sqm=100., capex_inr=100., monthly_rent_inr=1., annual_opex_inr=2., gross_margin_fraction=.3) for i in range(2)]
    weights = dict(time_bins=list(TIME_BINS), category_weights={'office':dict.fromkeys(TIME_BINS,1.)},
                   catchment_radius_m=1500., decay_scale_m=750., weight_version='test-assumed',
                   unknown_hours_assumption=dict(availability_fraction=.5, evidence_weight=.5))
    project = dict(project_id='test', city='Synthetic test', category='grocery', budget_inr=1000.,
                   discount_rate_fraction=.1, projection_years=5, sites=sites,
                   stores=[dict(store_id='b', latitude=12., longitude=77., store_size_sqm=100., theta=0., variable_contribution_margin=.2)],
                   inputs=dict(cells=[dict(cell_id='g',latitude=12.,longitude=77.,annual_wallet_inr=10000.)],
                     competitors=[], outside=1., weights=weights, pois=[], poi_coverage_supported=True,
                     source_ids=['SYNTHETIC_UNIT_TEST_ONLY'], valuation_date='2026-10-24', feature_snapshot_id='test',
                     reference_predictions={s['site_id']:dict(reference_annual_sales_inr=3000., wallet_upper_bound_inr=10000.,
                       joint_support_pass=True, hard_schema_compatible=True, method_mode='model_simulated', model_artifact_id='UNIT_TEST_ASSUMED_INPUT') for s in sites}))
    scenario = dict(scenario_id='test-baseline',project_id='test',budget_inr=1000., assumptions=dict(demand_multiplier=1.,rent_multiplier=1.,site_overrides={}))
    return project,scenario


class GeometryAndDaypart(unittest.TestCase):
    def test_geodesic_metres_and_invalid_coordinates(self):
        self.assertAlmostEqual(distances([dict(latitude=0,longitude=0)],[dict(latitude=0,longitude=1)])[0,0],111194.9266,delta=.1)
        with self.assertRaises(ValueError): distances([dict(latitude=91,longitude=0)],[])

    def test_dayparts_duration_and_frequency(self):
        p,_=fixture(); sites=p['sites'][:1]; w=p['inputs']['weights']
        poi=dict(poi_id='p',latitude=12.,longitude=77.,category='office',source_id='test')
        out=daypart_profiles(sites,[poi],w,coverage_supported=True)['s0']
        self.assertEqual(list(out['raw'].values()),[.25]*6)
        self.assertAlmostEqual(out['weekly_exposure_share']['weekday_night'],50/168)
        self.assertAlmostEqual(sum(out['weekly_exposure_share'].values()),1.)
        self.assertEqual(out['assumed_hours_count'],1)

    def test_unknown_differs_from_supported_zero(self):
        p,_=fixture(); w=p['inputs']['weights']
        known=daypart_profiles(p['sites'],[],w,coverage_supported=True)['s0']
        unknown=daypart_profiles(p['sites'],[],w,coverage_supported=False)['s0']
        self.assertEqual(known['raw']['weekday_lunch'],0.)
        self.assertIsNone(unknown['raw']['weekday_lunch'])
        self.assertEqual(known['support_count'],0)

    def test_availability_override_and_duplicate_rejection(self):
        p,_=fixture(); poi=dict(poi_id='p',latitude=12.,longitude=77.,category='office')
        availability=[dict(poi_id='p',time_bin=t,availability_fraction=1.,evidence_weight=1.,availability_status='RECORDED') for t in TIME_BINS]
        r=daypart_profiles(p['sites'],[poi],p['inputs']['weights'],availability=availability,coverage_supported=True)['s0']
        self.assertEqual(r['raw']['weekday_lunch'],1.)
        with self.assertRaises(ValueError): daypart_profiles(p['sites'],[poi],p['inputs']['weights'],availability=availability*2)


class AllocationChecks(unittest.TestCase):
    def test_hand_calculated_shares_and_money_conservation(self):
        r=allocate([100.],[1.],[[2.,3.]])
        np.testing.assert_allclose(r['revenues_inr'],[200/7,300/7])
        self.assertAlmostEqual(sum(r['revenues_inr'])+r['external_inr']+r['outside_inr'],100.)
        self.assertLessEqual(r['conservation_error'],1e-6)

    def test_calibration_and_unattainable_target(self):
        r=calibrate([1000.],[1.],[1.],400.,tolerance=.001)
        self.assertEqual(r['status'],'CALIBRATED'); self.assertAlmostEqual(r['achieved_inr'],400.,delta=.001)
        bad=calibrate([1000.],[1.],[1.],1001.)
        self.assertEqual(bad['requested_inr'],1001.); self.assertIn('REVIEW_REQUIRED',bad['status'])
        self.assertLess(bad['achieved_inr'],1001.)
        zero=calibrate([1000.],[1.],[1.],0.)
        self.assertEqual(zero['achieved_inr'],0.); self.assertEqual(zero['attraction'][0],0.)

    def test_wallet_scaling_and_competition(self):
        a=allocate([100.],[1.],[[2.,3.]])['revenues_inr']
        b=allocate([125.],[1.],[[2.,3.]])['revenues_inr']
        np.testing.assert_allclose(b,1.25*a)
        self.assertTrue(np.all(allocate([100.],[2.],[[2.,3.]])['revenues_inr']<a))

    def test_own_branch_loss_deducted_once(self):
        frozen=dict(wallet_by_year=[[100.]],external_attraction=[1.],branch_attraction=[[2.]],
                    candidate_attraction_by_year=[[[3.]]],outside=1.)
        site=dict(site_id='s',capex_inr=0.,annual_opex_inr=0.,gross_margin_fraction=.3)
        r=network_cashflows(frozen,[site],[dict(variable_contribution_margin=.2)],['s'],{'s':0.},0.)
        self.assertAlmostEqual(r['lost_existing_contribution_by_year_inr'][0],(50-200/7)*.2)
        self.assertAlmostEqual(r['npv_inr'],300/7*.3-(50-200/7)*.2)

    def test_invalid_numerics_fail(self):
        for w,e,a,o in [([-1],[1],[[1]],1),([1],[1],[[1]],0),([1],[1],[[float('nan')]],1)]:
            with self.assertRaises(ValueError): allocate(w,e,a,o)


class TimingChecks(unittest.TestCase):
    def test_midyear_and_delay_fraction(self):
        f=active_fractions('2026-10-24','2028-04-01',5)
        self.assertEqual(f[0],0.); self.assertEqual(f[2:], [1.,1.,1.])
        self.assertAlmostEqual(f[1],(date(2028,10,24)-date(2028,4,1)).days/366)
        self.assertEqual(active_fractions('2026-10-24','2030-04-01',5)[:3],[0.,0.,0.])
        self.assertEqual(add_months(date(2024,2,29),12),date(2025,2,28))

    def test_current_operational_cancelled_unknown_and_effect_signs(self):
        p,_=fixture(); event=dict(infra_project_id='e',status='proposed',hypothetical_demo=True,
                                  geometry=dict(type='Point',coordinates=[77.,12.]),assumed_demo_open_date='2026-10-24')
        for effect in (0.,.2,-.2):
            r,_=infrastructure_multipliers(p['sites'],[event],dict(infrastructure_state='opens',infrastructure_effect_fraction=effect),'2026-10-24',5)
            self.assertAlmostEqual(r[0,0],1+effect)
        for status in ('operational','cancelled'):
            e=dict(event,status=status)
            r,_=infrastructure_multipliers(p['sites'],[e],dict(infrastructure_state='opens',infrastructure_effect_fraction=.5),'2026-10-24',5)
            np.testing.assert_equal(r,np.ones((5,2)))
        with self.assertRaises(DomainUnavailable):
            infrastructure_multipliers(p['sites'],[dict(infra_project_id='e',status='unknown')],dict(infrastructure_state='opens'),'2026-10-24',5)


class FailFastChecks(unittest.TestCase):
    def test_all_states_and_full_precedence(self):
        self.assertEqual(diagnose(1,1)[0]['status'],'VIABLE')
        self.assertEqual(diagnose(1,-1)[0]['status'],'AT_RISK')
        self.assertEqual(diagnose(-1,-1)[0]['status'],'REJECTED')
        self.assertEqual(diagnose(-1,-1,review_reasons=['missing'])[0]['status'],'REVIEW_REQUIRED')
        r,rules=diagnose(-1,-1,hard_reasons=['unavailable'],review_reasons=['missing'])
        self.assertEqual(r['status'],'REJECTED'); self.assertEqual(len([r for r in rules if not r['passed']]),4)

    def test_rent_threshold_oracle_and_no_rescue(self):
        factor=12*sum(1.1**(-y) for y in range(1,6))
        r=rent_rescue(lambda rent:12345.-factor*rent,.1,5,1000.)
        self.assertEqual(r['status'],'SOLVED'); self.assertAlmostEqual(r['threshold'],12345/factor)
        self.assertGreater(r['below_npv_inr'],0); self.assertLess(r['above_npv_inr'],0)
        self.assertIsNone(rent_rescue(lambda r:-10-factor*r,.1,5,100.)['threshold'])
        viable=rent_rescue(lambda r:100000-factor*r,.1,5,1.)
        self.assertEqual(viable['status'],'SOLVED'); self.assertFalse(viable['threshold_within_bounds'])
        self.assertEqual(viable['reason'],'CURRENT_RENT_ALREADY_FINANCIALLY_VIABLE')

    def test_sales_bounds_nonmonotonic_and_verified_root(self):
        r=sales_rescue(lambda m:1000*m-1100)
        self.assertEqual(r['status'],'SOLVED'); self.assertAlmostEqual(r['threshold'],1.1,delta=.001)
        self.assertEqual(sales_rescue(lambda m:-m)['status'],'NON_MONOTONIC')
        self.assertEqual(sales_rescue(lambda m:-100)['status'],'NOT_RECOVERABLE_WITHIN_BOUNDS')
        from backend.app.domain.failfast.rules import UnattainableRescue
        def bounded(m):
            if m>1.12: raise UnattainableRescue('Physical wallet bound')
            return 1000*(m-1.1)
        frontier=sales_rescue(bounded)
        self.assertEqual(frontier['status'],'SOLVED')
        self.assertAlmostEqual(frontier['threshold'],1.1,delta=.001)
        self.assertGreaterEqual(frontier['verified_npv_inr'],0.)


class PortfolioChecks(unittest.TestCase):
    def test_full_network_1024_sets_against_independent_cashflow_formula(self):
        sites=[dict(site_id=f's{i}',capex_inr=1.,annual_opex_inr=10.,gross_margin_fraction=.3) for i in range(10)]
        strengths=np.arange(1,11,dtype=float)
        frozen=dict(wallet_by_year=[[10000.]],external_attraction=[1.],branch_attraction=[[2.]],
                    candidate_attraction_by_year=[[strengths.tolist()]],outside=1.)
        rents={s['site_id']:0. for s in sites}; branches=[dict(variable_contribution_margin=.2)]
        def value(ids):
            return network_cashflows(frozen,sites,branches,ids,rents,0.)['npv_inr']
        r=enumerate_portfolios(sites,[s['site_id'] for s in sites],10.,10,value)
        def oracle(ids):
            a=sum(strengths[int(i[1:])] for i in ids)
            new_revenue=10000*a/(4+a)
            lost=(5000-20000/(4+a))*.2
            return new_revenue*.3-lost-11*len(ids)
        sets=[c for k in range(11) for c in combinations(sorted(rents),k)]
        expected=min(sets,key=lambda c:(-oracle(c),len(c),len(c),c))
        self.assertEqual(r['selected_site_ids'],list(expected))
        self.assertAlmostEqual(r['full_network_npv_inr'],oracle(expected))
        self.assertEqual(r['evaluated_subsets'],1024)

    def test_all_1024_sets_and_independent_overlap_oracle(self):
        sites=[dict(site_id=f's{i}',capex_inr=1.) for i in range(10)]
        strengths={f's{i}':i+1 for i in range(10)}
        def value(ids):
            a=sum(strengths[i] for i in ids)
            return 100*a/(1+a)-10*len(ids)
        r=enumerate_portfolios(sites,list(strengths),10.,10,value)
        brute=[(value(list(s)),len(s),s) for k in range(11) for s in combinations(sorted(strengths),k)]
        expected=min(brute,key=lambda x:(-x[0],x[1],x[1],x[2]))
        self.assertEqual(r['evaluated_subsets'],1024); self.assertEqual(r['status'],'FULL_NETWORK_EXACT')
        self.assertEqual(r['selected_site_ids'],list(expected[2])); self.assertAlmostEqual(r['full_network_npv_inr'],expected[0])
        self.assertNotAlmostEqual(value(['s8','s9']),value(['s8'])+value(['s9']))

    def test_paise_budget_ties_and_empty_zero(self):
        self.assertEqual(paise(.105),11)
        sites=[dict(site_id='b',capex_inr=.11),dict(site_id='a',capex_inr=.11)]
        r=enumerate_portfolios(sites,['b','a'],.11,2,lambda ids:100*len(ids))
        self.assertEqual(r['selected_site_ids'],['a'])
        self.assertEqual(enumerate_portfolios(sites,['a','b'],0.,2,lambda ids:100)['selected_site_ids'],[])
        self.assertEqual(enumerate_portfolios(sites,['a','b'],1.,2,lambda ids:-1)['full_network_npv_inr'],0.)

    def test_forced_cutoff_is_truthful(self):
        ticks=iter([0.,6.])
        r=enumerate_portfolios([dict(site_id='a',capex_inr=1)],['a'],1,1,lambda ids:100,clock=lambda:next(ticks))
        self.assertEqual(r['status'],'FEASIBLE_PARTIAL'); self.assertEqual(r['evaluated_subsets'],1)
        self.assertEqual(r['selected_site_ids'],[])


class PipelineChecks(unittest.TestCase):
    def test_pure_deterministic_immutable_pipeline_and_schema(self):
        from backend.app.schemas import EvaluationData, PortfolioResult
        p,s=fixture(); before=digest([p,s])
        a=prepare_evaluation(p,s); b=prepare_evaluation(p,s)
        self.assertEqual(a,b); self.assertEqual(before,digest([p,s]))
        EvaluationData.model_validate(dict(a['evaluation'],evaluation_id='test-e',project_id='test',scenario_id='test-baseline',created_at_utc='2026-10-25T00:00:00Z'))
        risks=[r['site_id'] for r in a['evaluation']['site_analyses'] if r['failfast']['status']=='AT_RISK']
        portfolio=run_portfolio(p,a['context'],2,risks)
        PortfolioResult.model_validate(dict(portfolio,portfolio_run_id='test-r',evaluation_id='test-e'))
        json.dumps(a,allow_nan=False)

    def test_rent_only_preserves_network_and_dayparts(self):
        p,s=fixture(); a=prepare_evaluation(p,s)
        s['assumptions']['rent_multiplier']=1.2; b=prepare_evaluation(p,s)
        self.assertEqual(a['context']['frozen_network'],b['context']['frozen_network'])
        self.assertEqual(a['diagnostics']['dayparts'],b['diagnostics']['dayparts'])
        self.assertLess(b['evaluation']['site_analyses'][0]['npv_inr'],a['evaluation']['site_analyses'][0]['npv_inr'])

    def test_demand_scale_and_zero_demand(self):
        p,s=fixture(); a=prepare_evaluation(p,s)
        s['assumptions']['demand_multiplier']=.8; b=prepare_evaluation(p,s)
        self.assertAlmostEqual(b['evaluation']['site_analyses'][0]['annual_revenue_inr'],.8*a['evaluation']['site_analyses'][0]['annual_revenue_inr'],delta=.02)
        s['assumptions']['demand_multiplier']=0; z=prepare_evaluation(p,s)
        self.assertEqual(z['evaluation']['site_analyses'][0]['annual_revenue_inr'],0.)

    def test_risk_acknowledgement_and_budget_source(self):
        p,s=fixture(); a=prepare_evaluation(p,s)
        self.assertEqual(run_portfolio(p,a['context'],2,[])['selected_site_ids'],[])
        self.assertTrue(run_portfolio(p,a['context'],2,['s0','s1'])['selected_site_ids'])
        s['budget_inr']=0.; zero=prepare_evaluation(p,s)
        self.assertEqual(run_portfolio(p,zero['context'],2,[])['budget_used_inr'],0.)
        with self.assertRaises(ValueError): run_portfolio(p,a['context'],2,['unknown'])

    def test_stale_modified_and_missing_context_rejected(self):
        p,s=fixture(); a=prepare_evaluation(p,s)
        for mutate in (lambda c:c['scenario'].update(budget_inr=9999), lambda c:c['frozen_network'].update(outside=2.)):
            c=deepcopy(a['context']); mutate(c)
            with self.assertRaises(ValueError): run_portfolio(p,c,2,[])
        p['sites'][0]['capex_inr']+=1
        with self.assertRaises(ValueError): run_portfolio(p,a['context'],2,[])
        with self.assertRaises(DomainUnavailable): run_portfolio(p,a['evaluation'],2,[])

    def test_missing_unsupported_and_invalid_inputs_fail_explicitly(self):
        p,s=fixture(); del p['inputs']
        with self.assertRaises(DomainUnavailable): run_evaluation(p,s)
        p,s=fixture(); p['inputs']['reference_predictions']['s0']['reference_annual_sales_inr']=None
        with self.assertRaises(DomainUnavailable): run_evaluation(p,s)
        p,s=fixture(); p['sites'].append(deepcopy(p['sites'][0]))
        with self.assertRaises(ValueError): run_evaluation(p,s)
        p,s=fixture(); s['assumptions']['site_overrides']['bad']={}
        with self.assertRaises(ValueError): run_evaluation(p,s)

    def test_unattainable_target_is_review_not_silent_clipping(self):
        p,s=fixture(); s['assumptions']['site_overrides']={'s0':dict(sales_multiplier=3.)}
        p['inputs']['reference_predictions']['s0']['reference_annual_sales_inr']=9000.
        a=prepare_evaluation(p,s)
        self.assertEqual(a['evaluation']['site_analyses'][0]['failfast']['status'],'REVIEW_REQUIRED')
        c=a['diagnostics']['site_details']['s0']['calibration'][0]
        self.assertEqual(c['requested_inr'],27000.); self.assertLess(c['achieved_inr'],27000.)

    def test_rescue_does_not_clear_hard_failure(self):
        p,s=fixture(); p['inputs']['site_eligibility']={'s0':dict(hard_failures=['UNAVAILABLE'])}
        a=prepare_evaluation(p,s); r=calculate_rescue(p,a['context'],'s0','rent')
        self.assertFalse(r['clears_unrelated_failures'])
        self.assertEqual(a['evaluation']['site_analyses'][0]['failfast']['status'],'REJECTED')
        self.assertAlmostEqual(r['verified_npv_inr'],0.,delta=1)

    def test_future_effect_applied_once_with_frozen_model(self):
        p,s=fixture(); p['inputs']['infrastructure']=[dict(infra_project_id='e',status='proposed',hypothetical_demo=True,
            geometry=dict(type='Point',coordinates=[77.,12.]),assumed_demo_open_date='2026-10-24')]
        s['assumptions'].update(infrastructure_state='opens',infrastructure_effect_fraction=.2)
        a=prepare_evaluation(p,s)
        self.assertAlmostEqual(a['context']['frozen_network']['target_by_year_inr'][0][0],3600.)
        self.assertEqual(p['inputs']['reference_predictions']['s0']['reference_annual_sales_inr'],3000.)


class ActualFittedBengaluru(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from ml.decision_engine.run import build_project, baseline_scenario
        with patch('socket.socket.connect',side_effect=AssertionError('Network forbidden')):
            cls.project=build_project(); cls.scenario=baseline_scenario(cls.project)
            cls.result=prepare_evaluation(cls.project,cls.scenario)

    def test_actual_artifact_and_ten_site_end_to_end(self):
        a=self.result
        self.assertEqual(a['evaluation']['model_artifact_id'],'reference-sales-sim-v2-438774e0a585')
        self.assertEqual(len(a['evaluation']['site_analyses']),10)
        self.assertEqual(a['evaluation']['method_mode'],'model_simulated')
        self.assertEqual(len(self.project['inputs']['competitors']),219)
        self.assertTrue(all('REVIEW_REQUIRED' not in c['status'] for c in a['context']['frozen_network']['calibration']))

    def test_portable_bundle_restores_inference_without_original_artifact_directory(self):
        import tempfile
        from pathlib import Path
        from ml.decision_engine.package import ROOT, install_bundle
        from ml.inference.reference_sales_v2 import ReferenceSalesEstimatorV2
        from ml.training.reference_sales.features import FEATURES
        from ml.decision_engine.run import rows, REVISED
        parent=(ROOT/'.runtime/decision-engine-tests').resolve()
        self.assertTrue(parent.is_relative_to(ROOT)); parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as directory:
            target=Path(directory)/'restored'
            install_bundle(target)
            model=ReferenceSalesEstimatorV2(target)
            row=rows(REVISED/'site_features_enriched.csv')[0]
            result=model.predict({f:row[f] for f in FEATURES},allow_csv_strings=True)
            self.assertEqual(result['raw_reference_annual_sales_inr'],self.project['inputs']['reference_predictions']['site-01']['raw_reference_annual_sales_inr'])
            (target/'support.json').write_text('{}',encoding='utf-8')
            with self.assertRaises(ValueError): install_bundle(target)

    def test_model_perturbation_changes_economics_not_only_label(self):
        from ml.inference.reference_sales_v2 import ReferenceSalesEstimatorV2
        from ml.training.reference_sales.features import FEATURES
        from ml.decision_engine.run import rows, REVISED
        row=rows(REVISED/'site_features_enriched.csv')[0]
        features={f:row[f] for f in FEATURES}; features['annual_wallet_inr']=str(float(features['annual_wallet_inr'])*1.1)
        altered=ReferenceSalesEstimatorV2().predict(features,allow_csv_strings=True)
        p=deepcopy(self.project); p['inputs']['reference_predictions']['site-01']=altered
        b=prepare_evaluation(p,self.scenario)
        original=self.result['evaluation']['site_analyses'][0]; modified=b['evaluation']['site_analyses'][0]
        self.assertGreater(modified['annual_revenue_inr'],original['annual_revenue_inr'])
        self.assertGreater(modified['npv_inr'],original['npv_inr'])

    def test_frozen_arrays_unchanged_by_joint_search(self):
        context=self.result['context']; before=digest(context)
        risk=[a['site_id'] for a in self.result['evaluation']['site_analyses'] if a['failfast']['status']=='AT_RISK']
        r=run_portfolio(self.project,context,10,risk)
        self.assertEqual(before,digest(context)); self.assertEqual(r['status'],'FULL_NETWORK_EXACT')
        self.assertGreaterEqual(r['full_network_npv_inr'],0.)
        self.assertLessEqual(r['budget_used_inr'],self.scenario['budget_inr'])

    def test_actual_model_changes_boundary_diagnosis_and_selected_set(self):
        from ml.inference.reference_sales_v2 import ReferenceSalesEstimatorV2
        from ml.training.reference_sales.features import FEATURES
        from ml.decision_engine.run import rows, REVISED
        row=rows(REVISED/'site_features_enriched.csv')[0]
        x={f:row[f] for f in FEATURES}; x['annual_wallet_inr']=str(float(x['annual_wallet_inr'])*1.1)
        estimate=ReferenceSalesEstimatorV2().predict(x,allow_csv_strings=True)
        p=deepcopy(self.project); p['sites']=p['sites'][:1]
        p['inputs']['reference_predictions']={'site-01':p['inputs']['reference_predictions']['site-01']}
        p['sites'][0]['capex_inr']=0.
        s=deepcopy(self.scenario); s['budget_inr']=1e10
        low=prepare_evaluation(p,s)
        high_p=deepcopy(p); high_p['inputs']['reference_predictions']['site-01']=estimate
        high=prepare_evaluation(high_p,s)
        capex=(low['evaluation']['site_analyses'][0]['npv_inr']+high['evaluation']['site_analyses'][0]['npv_inr'])/2
        # Explicit synthetic boundary fixture, separate from all ten unchanged
        # demonstration rows: no hardcoded production ranking or fitted label.
        p['sites'][0]['capex_inr']=capex; high_p['sites'][0]['capex_inr']=capex
        low=prepare_evaluation(p,s); high=prepare_evaluation(high_p,s)
        self.assertLess(low['evaluation']['site_analyses'][0]['npv_inr'],0.)
        self.assertGreater(high['evaluation']['site_analyses'][0]['npv_inr'],0.)
        self.assertEqual(low['evaluation']['site_analyses'][0]['failfast']['status'],'REJECTED')
        self.assertEqual(run_portfolio(p,low['context'],1,[])['selected_site_ids'],[])
        self.assertEqual(run_portfolio(high_p,high['context'],1,['site-01'])['selected_site_ids'],['site-01'])


if __name__ == '__main__':
    unittest.main()
