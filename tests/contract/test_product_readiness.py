"""Saved decision journeys using actual fitted Bengaluru inference and isolated accounts."""
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch
from pypdf import PdfReader
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services import reports, sources
from backend.app.repositories import store
from tests.contract import test_integration as integration
BASE = integration.BASE


class ProductJourneys(unittest.TestCase):
    setUp = integration.IntegrationTests.setUp
    tearDown = integration.IntegrationTests.tearDown
    evaluate = integration.IntegrationTests.evaluate
    scenario = integration.IntegrationTests.scenario

    def plan(self, evaluation):
        response = self.client.post(BASE+'/portfolios', json=dict(evaluation_id=evaluation['evaluation_id'],
            max_stores=2, acknowledged_risk_site_ids=[a['site_id'] for a in evaluation['site_analyses'] if a['failfast']['status']=='AT_RISK']))
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['data']

    def test_map_context_before_analysis_is_contextual_and_does_not_raise_caps(self):
        geo = self.client.get(BASE+'/features').json()['data']
        self.assertIsNone(geo['evaluation_id'])
        shops = [p for p in geo['pois'] if p['category']=='competitor']
        self.assertEqual(len(shops), 219)
        self.assertEqual(len({p['poi_id'] for p in shops}),219)
        self.assertTrue(all('annual_revenue_inr' not in p and 'npv_inr' not in p and p['source_id'] for p in shops))
        project = self.client.get(BASE).json()['data']
        self.assertEqual((len(project['sites']),len(project['stores'])),(10,4))
        self.assertEqual(self.client.post(BASE+'/workspace',json=dict(selected_site_ids=[shops[0]['poi_id']])).status_code,422)
        self.assertEqual(self.client.post(BASE+'/portfolios',json=dict(evaluation_id='missing',max_stores=219)).status_code,422)

    def test_saved_scenario_views_and_comparison_survive_navigation_and_login(self):
        before = self.evaluate()
        changed = self.scenario(base_scenario_id='baseline', name='Deliberate zero effect', assumptions=dict(rent_multiplier=.8,infrastructure_state='delayed',infrastructure_effect_fraction=0,opening_date='2028-04-01'))
        after = self.evaluate(changed['scenario_id'])
        pair = dict(before_scenario_id='baseline',before_evaluation_id=before['evaluation_id'],after_scenario_id=changed['scenario_id'],after_evaluation_id=after['evaluation_id'])
        initial = dict(scenario_id='baseline',evaluation_id=before['evaluation_id'],portfolio_run_id=None)
        state = dict(scenario_id=changed['scenario_id'],evaluation_id=after['evaluation_id'],portfolio_run_id=None,comparison=pair,selected_site_ids=['site-02','site-04'])
        for value in (initial,state,initial,state):
            self.assertEqual(self.client.post(BASE+'/workspace',json=value).status_code,200)
        restored = self.client.get(BASE+'/workspace?scenario_id=baseline').json()['data']
        self.assertEqual(restored['evaluation_id'], before['evaluation_id'])
        self.client.post('/api/v1/auth/logout')
        self.client.post('/api/v1/auth/login',json=dict(email='contract@example.test',password='contract-passphrase-2026'))
        restored = self.client.get(BASE+'/workspace').json()['data']
        self.assertEqual(restored['comparison'],pair)
        self.assertEqual(restored['selected_site_ids'],state['selected_site_ids'])
        self.assertTrue(restored['analysis_current'])
        self.assertEqual(self.client.get(BASE+'/scenarios/'+changed['scenario_id']).json()['data']['assumptions']['infrastructure_effect_fraction'],0)
        invalid = {**state,'comparison':{**pair,'before_evaluation_id':after['evaluation_id']}}
        self.assertEqual(self.client.post(BASE+'/workspace',json=invalid).status_code,409)

    def test_pdf_is_paginated_readable_frozen_and_account_isolated(self):
        evaluation = self.evaluate()
        plan = self.plan(evaluation)
        path = BASE+'/reports/'+evaluation['evaluation_id']+'?portfolio_run_id='+plan['portfolio_run_id']
        # Report already exists in the same transaction as portfolio, before its first download.
        self.assertIsNotNone(store.get('report','demo',reports.report_key(evaluation['evaluation_id'],plan['portfolio_run_id'])))
        response = self.client.get(path)
        self.assertEqual(response.status_code,200,response.text[:80])
        self.assertTrue(response.headers['content-type'].startswith('application/pdf'))
        self.assertIn('.pdf',response.headers['content-disposition'])
        reader = PdfReader(BytesIO(response.content))
        text = '\n'.join(page.extract_text() for page in reader.pages)
        for word in ('Recommendation','Selected locations','Financial comparison','Risks','INR','%','Page 1 of','Synthetic'):
            self.assertIn(word,text)
        self.assertNotIn('"annual_revenue_inr":',text)
        self.assertNotIn('prepared_network',text)
        for i,page in enumerate(reader.pages):
            self.assertIn(f'Page {i+1} of {len(reader.pages)}',page.extract_text())
        self.assertGreaterEqual(len(reader.pages),3)
        with patch.object(reports,'render_pdf',side_effect=AssertionError('Must not render again')), patch.object(sources,'engine_identity',return_value='new-software'):
            self.assertEqual(self.client.get(path).content,response.content)
        with TestClient(app) as other:
            other.post('/api/v1/auth/register',json=dict(name='Isolated',email='isolation@example.test',password='isolated-passphrase-2026'))
            self.assertEqual(other.get(path).status_code,404)
        # Optional review artifact, always isolated from historical evidence.
        output=Path('.runtime/product-readiness'); output.mkdir(parents=True,exist_ok=True)
        (output/'decision-report.pdf').write_bytes(response.content)

    def test_pdf_failure_cannot_publish_partial_portfolio(self):
        evaluation = self.evaluate()
        with patch.object(reports,'render_pdf',side_effect=ValueError('Rendering failed')):
            with self.assertRaises(ValueError):
                self.client.post(BASE+'/portfolios',json=dict(evaluation_id=evaluation['evaluation_id']))
        self.assertEqual(store.list_objects('portfolio','demo'),[])
        self.assertEqual(store.list_objects('report','demo'),[])


if __name__=='__main__': unittest.main()
