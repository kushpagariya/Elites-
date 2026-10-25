"""Deployment boundaries: clean artifact restore, honest readiness, independent maps."""
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services import sources
from backend.app.services.errors import ServiceError
from ml.decision_engine import package
from tests.contract import test_integration as integration
BASE = integration.BASE


class DeploymentTests(unittest.TestCase):
    setUp = integration.IntegrationTests.setUp
    tearDown = integration.IntegrationTests.tearDown
    evaluate = integration.IntegrationTests.evaluate
    def test_packaged_restore_into_clean_release_and_refuse_differing_files(self):
        destination = Path(self.tmp.name) / 'release/ml/artifacts/reference_sales_v2'
        record_dir = Path(self.tmp.name) / 'release/ml/evaluation/decision_engine_v1'
        record_dir.mkdir(parents=True)
        (record_dir/'artifact_bundle_manifest.json').write_bytes((package.OUT/'artifact_bundle_manifest.json').read_bytes())
        with patch.object(package, 'ARTIFACTS', destination), patch.object(sources, 'ROOT', Path(self.tmp.name)/'release'):
            result = sources.restore_packaged_model()
            self.assertEqual(result['card']['model_artifact_id'], 'reference-sales-sim-v2-438774e0a585')
            self.assertEqual(result['artifact_sha256'], '438774e0a585de6ae4ed8a80cd3b1cf396d698bb811f1079a37c68f627bf4998')
            (destination/'catboost.joblib').write_bytes(b'tampered')
            (destination/'support.json').unlink()
            with self.assertRaises(ValueError): sources.restore_packaged_model()
            self.assertEqual((destination/'catboost.joblib').read_bytes(), b'tampered')

    def test_geography_and_infrastructure_do_not_load_model(self):
        with patch.object(sources, 'model_bundle', side_effect=ServiceError(503,'MODEL_UNAVAILABLE','Unavailable')):
            response = self.client.get(BASE+'/features')
            self.assertEqual(response.status_code,200,response.text)
            data=response.json()['data']
            self.assertEqual(len([p for p in data['pois'] if p['category']=='competitor']),219)
            self.assertEqual(len(data['catchments']),10)
            self.assertEqual(self.client.get(BASE+'/infrastructure').status_code,200)

    def test_readiness_fails_when_startup_cannot_verify_model_and_errors_are_safe(self):
        with patch.object(sources, 'restore_packaged_model', side_effect=ValueError('private internal failure')):
            with TestClient(app) as client:
                self.assertEqual(client.get('/api/v1/health').json()['data']['analytics_status'],'unavailable')
                response=client.get('/api/v1/ready')
                self.assertEqual(response.status_code,503)
                self.assertNotIn('private internal failure',response.text)
        with patch.object(sources, 'ROOT', Path(self.tmp.name)):
            response=self.client.get(BASE+'/model')
            self.assertEqual(response.status_code,503)
            self.assertNotIn('python',response.text)
            self.assertNotIn('--install',response.text)

    def test_daypart_categories_trace_to_delivered_domain_and_zero_is_preserved(self):
        result=self.evaluate()
        for site in result['site_analyses']:
            self.assertEqual(len(site['dayparts']),6)
            for profile in site['dayparts']:
                self.assertTrue(profile['categories'])
                self.assertAlmostEqual(sum(c['weighted_opportunity'] for c in profile['categories']),profile['raw_opportunity'],places=8)
                self.assertEqual(sum(c['count'] for c in profile['categories']),profile['support_count'])
                self.assertTrue(profile['source_ids'])
