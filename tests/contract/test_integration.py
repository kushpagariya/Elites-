"""Real fitted-model/API integration, persistence and failure boundaries."""
import copy
import os
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.repositories import store
from backend.app.services import gateway, sources
from backend.app.domain.engine import prepare_evaluation

BASE = '/api/v1/projects/demo'


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {'STORESCOUT_DB_PATH': str(Path(self.tmp.name)/'state.sqlite3')})
        self.env.start()
        self.client = TestClient(app)
        account = self.client.post('/api/v1/auth/register', json=dict(name='Contract account', email='contract@example.test', password='contract-passphrase-2026'))
        self.assertEqual(account.status_code, 201, account.text)
        self.user_context = store.current_user.set(account.json()['data']['id'])

    def tearDown(self):
        store.current_user.reset(self.user_context)
        self.client.close()
        self.env.stop()
        self.tmp.cleanup()

    def evaluate(self, scenario_id='baseline', **kwargs):
        response = self.client.post(BASE+'/evaluate', json={'scenario_id':scenario_id}, **kwargs)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['data']

    def scenario(self, **kwargs):
        response = self.client.post(BASE+'/scenarios', json={'name':'Saved conditions','assumptions':{}, **kwargs})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()['data']

    def test_fitted_model_matches_delivered_baseline_without_revaluing(self):
        result = self.evaluate()
        original = sources.read_json(sources.ROOT/'ml/evaluation/decision_engine_v1/baseline.json')['evaluation']
        self.assertEqual(result['method_mode'], 'model_simulated')
        self.assertEqual(result['model_artifact_id'], original['model_artifact_id'])
        self.assertEqual(result['rankings'], original['rankings'])
        for actual, expected in zip(result['site_analyses'], original['site_analyses']):
            for field in ('annual_revenue_inr','npv_inr','annual_cashflows_inr','lost_existing_contribution_inr','roi_fraction','payback_years'):
                self.assertEqual(actual[field], expected[field])
            self.assertEqual(len(actual['dayparts']), 6)
            self.assertAlmostEqual(sum(p['opportunity_index'] for p in actual['dayparts']), 100.)
            self.assertEqual(actual['failfast']['status'], 'AT_RISK')

    def test_cache_restart_saved_results_and_idempotency(self):
        with patch.object(gateway.pipeline, 'prepare_evaluation', wraps=prepare_evaluation) as worker:
            first = self.evaluate(headers={'Idempotency-Key':'same'})
            self.assertEqual(first, self.evaluate(headers={'Idempotency-Key':'same'}))
            self.assertEqual(worker.call_count, 1)
        with TestClient(app) as fresh:
            fresh.cookies.update(self.client.cookies)
            self.assertEqual(fresh.get(BASE+'/evaluations/'+first['evaluation_id']).json()['data'], first)
        changed = self.scenario(assumptions={'rent_multiplier':.8})
        response = self.client.post(BASE+'/evaluate',json={'scenario_id':changed['scenario_id']},headers={'Idempotency-Key':'same'})
        self.assertEqual(response.status_code, 409)
        self.assertNotEqual(self.evaluate(changed['scenario_id'])['evaluation_id'], first['evaluation_id'])

    def test_source_or_engine_changes_block_reuse_but_preserve_saved_reports(self):
        evaluation = self.evaluate()
        for target, value in [('engine_identity','changed-engine'), ('snapshot_hashes',{'changed-source':'digest'})]:
            with patch.object(sources, target, return_value=value):
                self.assertEqual(self.client.post(BASE+'/portfolios',json={'evaluation_id':evaluation['evaluation_id']}).status_code,409)
                self.assertEqual(self.client.get(BASE+'/evaluations/'+evaluation['evaluation_id']).status_code,200)
                self.assertEqual(self.client.get(BASE+'/reports/'+evaluation['evaluation_id']+'?format=json').status_code,200)

    def test_unknown_ids_invalid_dates_and_unsupported_controls_fail_explicitly(self):
        self.assertEqual(self.client.get('/api/v1/projects/missing').status_code,404)
        self.assertEqual(self.client.post(BASE+'/evaluate',json={'feature_snapshot_id':'old'}).status_code,409)
        for assumptions in ({'demand_multiplier':-1}, {'opening_date':'2027-02-30'}, {'competition_multiplier':2}, {'site_overrides':{'site-01':{'gross_margin_fraction':.4}}}, {'site_overrides':{'missing':{'monthly_rent_inr':10}}}):
            self.assertEqual(self.client.post(BASE+'/scenarios',json={'name':'Invalid','assumptions':assumptions}).status_code,422)

    def test_portfolio_requires_explicit_risk_review_and_respects_budget(self):
        evaluation=self.evaluate(); eid=evaluation['evaluation_id']
        response=self.client.post(BASE+'/portfolios',json={'evaluation_id':eid})
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['data']['selected_site_ids'],[])
        risks=[a['site_id'] for a in evaluation['site_analyses']]
        response=self.client.post(BASE+'/portfolios',json={'evaluation_id':eid,'max_stores':2,'acknowledged_risk_site_ids':risks})
        self.assertEqual(response.status_code,200,response.text)
        plan=response.json()['data']
        self.assertEqual(plan['selected_site_ids'],['site-05','site-10'])
        self.assertEqual(plan['solver_status'],'OPTIMAL')
        self.assertEqual(plan['budget_used_inr']+plan['budget_unused_inr'],20_000_000)
        self.assertEqual(self.client.post(BASE+'/portfolios',json={'evaluation_id':eid,'acknowledged_risk_site_ids':[risks[0],risks[0]]}).status_code,422)
        zero=self.scenario(budget_inr=0)
        zero_eval=self.evaluate(zero['scenario_id'])
        self.assertEqual(zero_eval['rankings'],[])
        plan=self.client.post(BASE+'/portfolios',json={'evaluation_id':zero_eval['evaluation_id']}).json()['data']
        self.assertEqual((plan['budget_used_inr'],plan['full_network_npv_inr']), (0,0))

    def test_rent_and_sales_rescue_apply_canonical_verified_overrides(self):
        scenario=self.scenario(assumptions={'rent_multiplier':1.7,'site_overrides':{'site-01':{'sales_multiplier':.85}}})
        evaluation=self.evaluate(scenario['scenario_id'])
        for lever in ('rent','sales'):
            response=self.client.post(BASE+'/sites/site-01/rescue',json={'evaluation_id':evaluation['evaluation_id'],'lever':lever})
            self.assertEqual(response.status_code,200,response.text)
            result=response.json()['data']
            self.assertEqual(result['status'],'SOLVED')
            assumptions=copy.deepcopy(scenario['assumptions'])
            assumptions['site_overrides']['site-01'].update({k:v for k,v in result['actionable_site_override'].items() if v is not None})
            changed=self.scenario(base_scenario_id=scenario['scenario_id'],assumptions=assumptions)
            applied=next(a for a in self.evaluate(changed['scenario_id'])['site_analyses'] if a['site_id']=='site-01')
            self.assertEqual(applied['npv_inr'], result['npv_at_threshold'])
            self.assertEqual(self.client.get(BASE+'/scenarios/'+scenario['scenario_id']).json()['data'],scenario)
        self.assertEqual(result['threshold_coordinates'],'CANONICAL_SITE_OVERRIDE')

    def test_viable_bound_is_not_mislabelled_break_even_and_zero_controls_are_blocked(self):
        baseline=self.evaluate()
        result=self.client.post(BASE+'/sites/site-01/rescue',json={'evaluation_id':baseline['evaluation_id'],'upper_bound':1}).json()['data']
        self.assertEqual((result['threshold_kind'],result['threshold']),('VIABLE_BOUND',1.))
        self.assertGreater(result['npv_at_threshold'],1.)
        for assumptions,lever,blocked in [({'rent_multiplier':0},'rent','BLOCKED_ZERO_RENT_MULTIPLIER'),({'site_overrides':{'site-01':{'sales_multiplier':0}}},'sales','BLOCKED_ZERO_CURRENT_SALES_MULTIPLIER')]:
            scenario=self.scenario(assumptions=assumptions); evaluation=self.evaluate(scenario['scenario_id'])
            response=self.client.post(BASE+'/sites/site-01/rescue',json={'evaluation_id':evaluation['evaluation_id'],'lever':lever})
            self.assertEqual(response.status_code,200,response.text)
            self.assertEqual(response.json()['data']['application_status'],blocked)
            self.assertIsNone(response.json()['data']['actionable_site_override'])
        self.assertEqual(self.client.post(BASE+'/sites/site-01/rescue',json={'evaluation_id':baseline['evaluation_id'],'lower_bound':1,'upper_bound':2}).status_code,422)

    def test_infrastructure_uses_source_geometry_and_timing_changes_results(self):
        event=self.client.get(BASE+'/infrastructure').json()['data'][0]
        self.assertEqual(event['infra_project_id'],'metro-blue-2a')
        values=[]
        for state in ('current','opens','delayed'):
            scenario=self.scenario(assumptions={'infrastructure_state':state,'infrastructure_effect_fraction':event['assumed_effect_fraction']})
            value=self.evaluate(scenario['scenario_id']);values.append(sum(a['npv_inr'] for a in value['site_analyses']))
        self.assertGreater(values[1],values[2]);self.assertGreater(values[2],values[0])

    def test_geography_and_daypart_outputs_have_matching_saved_identity(self):
        evaluation=self.evaluate();eid=evaluation['evaluation_id']
        for resource in ('features','dayparts','rankings'):
            result=self.client.get(BASE+'/'+resource+'?evaluation_id='+eid)
            self.assertEqual(result.status_code,200,result.text)
            self.assertEqual(result.json()['data']['evaluation_id'],eid)
        geo=self.client.get(BASE+'/features?evaluation_id='+eid).json()['data']
        self.assertEqual(len(geo['cells']),100);self.assertGreater(len(geo['pois']),100)
        self.assertTrue(all(p['source_status']=='REAL' for p in geo['pois']))

    def test_workspace_is_persistent_and_refuses_cross_account_references(self):
        scenario=self.scenario();evaluation=self.evaluate(scenario['scenario_id'])
        plan=self.client.post(BASE+'/portfolios',json={'evaluation_id':evaluation['evaluation_id']}).json()['data']
        state=dict(scenario_id=scenario['scenario_id'],evaluation_id=evaluation['evaluation_id'],portfolio_run_id=plan['portfolio_run_id'])
        self.assertEqual(self.client.post(BASE+'/workspace',json=state).status_code,200)
        self.assertEqual(self.client.post(BASE+'/workspace',json={'scenario_id':'baseline'}).status_code,200)
        self.assertEqual(self.client.post(BASE+'/workspace',json=state).status_code,200)
        self.assertEqual(len(store.list_objects('workspace','demo')),1)
        with TestClient(app) as other:
            other.post('/api/v1/auth/register',json=dict(name='Another account',email='another@example.test',password='another-test-passphrase'))
            self.assertIsNone(other.get(BASE+'/workspace').json()['data']['evaluation_id'])
            for path in ('scenarios/'+scenario['scenario_id'],'evaluations/'+evaluation['evaluation_id'],'portfolios/'+plan['portfolio_run_id'],'reports/'+evaluation['evaluation_id']+'?format=json'):
                self.assertEqual(other.get(BASE+'/'+path).status_code,404)
            self.assertEqual(other.post(BASE+'/workspace',json=state).status_code,404)
        self.client.post('/api/v1/auth/logout')
        self.assertEqual(self.client.post('/api/v1/auth/login',json=dict(email='contract@example.test',password='contract-passphrase-2026')).status_code,200)
        restored=self.client.get(BASE+'/workspace').json()['data']
        self.assertEqual({k:restored[k] for k in state},state)
        self.assertTrue(restored['analysis_current'])
        with patch.object(sources,'engine_identity',return_value='new-code'):
            self.assertFalse(self.client.get(BASE+'/workspace').json()['data']['analysis_current'])

    def test_reports_are_frozen_escaped_and_require_matching_portfolios(self):
        scenario=self.scenario(name='<script>alert(1)</script>');evaluation=self.evaluate(scenario['scenario_id']);eid=evaluation['evaluation_id']
        run=self.client.post(BASE+'/portfolios',json={'evaluation_id':eid}).json()['data']
        report=self.client.get(BASE+'/reports/'+eid+'?format=html&portfolio_run_id='+run['portfolio_run_id'])
        self.assertEqual(report.status_code,200)
        self.assertNotIn('<script>alert(1)</script>',report.text);self.assertIn('&lt;script&gt;',report.text)
        value=self.client.get(BASE+'/reports/'+eid+'?format=json').json()['data']
        self.assertNotIn('inputs',value['project']);self.assertNotIn('prepared_network',value)
        other=self.evaluate()
        self.assertEqual(self.client.get(BASE+'/reports/'+other['evaluation_id']+'?portfolio_run_id='+run['portfolio_run_id']).status_code,409)

    def test_invalid_domain_output_and_timeout_never_save_partial_results(self):
        with patch.object(gateway.pipeline,'prepare_evaluation',return_value={'broken':True}):
            self.assertEqual(self.client.post(BASE+'/evaluate',json={}).status_code,502)
        self.assertEqual(store.list_objects('evaluation','demo'),[])
        release=threading.Event()
        def slow(*args):
            release.wait(2);return prepare_evaluation(*args)
        try:
            with patch.object(gateway.pipeline,'prepare_evaluation',side_effect=slow), patch.dict(os.environ,{'STORESCOUT_COMPUTE_TIMEOUT_SECONDS':'.01'}):
                response=self.client.post(BASE+'/evaluate',json={})
                self.assertEqual(response.status_code,503);self.assertEqual(response.json()['error']['code'],'ENGINE_TIMEOUT')
        finally:
            release.set()
        self.assertEqual(store.list_objects('evaluation','demo'),[])

    def test_atomic_rollback_and_concurrent_cache_publication(self):
        with self.assertRaises(sqlite3.IntegrityError):
            store.save_result('demo','evaluation','rollback',None,'r','x',[('evaluation','x',{'ok':1}),('evaluation','x',{'bad':1})])
        self.assertIsNone(store.get('evaluation','demo','x'))
        barrier=threading.Barrier(2);user_id=store.current_user.get()
        def publish(identity):
            context=store.current_user.set(user_id)
            try:
                barrier.wait()
                return store.save_result('demo','evaluation','same',None,'r',identity,[('evaluation',identity,{'identity':identity})])
            finally:store.current_user.reset(context)
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(publish,['a','b']))
        self.assertEqual(results[0],results[1]);self.assertEqual(len(store.list_objects('evaluation','demo')),1)

    def test_missing_or_modified_artifact_fails_closed(self):
        original_sha = sources.sha
        with patch.object(sources,'sha',side_effect=lambda path: '0'*64 if path.name == 'catboost.joblib' else original_sha(path)):
            self.assertEqual(self.client.get(BASE+'/model').status_code,503)
        with patch.object(sources,'ROOT',Path(self.tmp.name)):
            response=self.client.get(BASE+'/model')
            self.assertEqual(response.status_code,503)
            self.assertEqual(response.json()['error']['code'],'MODEL_UNAVAILABLE')

    def test_public_preview_is_computed_and_does_not_expose_account_data(self):
        with TestClient(app) as anonymous:
            response=anonymous.get('/api/v1/showcase')
        self.assertEqual(response.status_code,200,response.text)
        data=response.json()['data']
        self.assertEqual(data['model_artifact_id'],sources.model_bundle()['card']['model_artifact_id'])
        self.assertEqual(len(data['dayparts']),6)
        cases={s['state']:s for s in data['scenarios']}
        self.assertEqual(set(cases),{'current','opens','delayed'})
        for case in cases.values():
            self.assertEqual(case['delta_npv_inr'],case['npv_inr']-cases['current']['npv_inr'])
        self.assertGreater(cases['opens']['npv_inr'],cases['delayed']['npv_inr'])
        self.assertNotIn('contract@example.test',response.text)
        self.assertNotIn('password',response.text)


if __name__ == '__main__':
    unittest.main()
