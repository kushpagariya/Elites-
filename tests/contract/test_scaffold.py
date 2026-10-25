"""Targeted API contracts and persistence; final E2E acceptance is deferred."""
import os
import tempfile
import unittest
from unittest.mock import patch
from backend.app.repositories import store
from backend.app.services import sources
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app


class ScaffoldContractTests(unittest.TestCase):
    def test_local_frontend_cors_and_report_header_exposure(self):
        headers={"Origin":"http://127.0.0.1:3001", "Access-Control-Request-Method":"POST", "Access-Control-Request-Headers":"Content-Type, Idempotency-Key"}
        response=self.client.options("/api/v1/projects/demo/evaluate",headers=headers)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.headers["access-control-allow-origin"],headers["Origin"])
        response=self.client.get("/api/v1/health",headers={"Origin":headers["Origin"]})
        self.assertIn("Content-Disposition",response.headers["access-control-expose-headers"])
        response=self.client.options("/api/v1/projects/demo/evaluate",headers={**headers,"Origin":"https://unapproved.example"})
        self.assertEqual(response.status_code,400)
        self.assertNotIn("access-control-allow-origin",response.headers)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get("STORESCOUT_DB_PATH")
        os.environ["STORESCOUT_DB_PATH"] = str(Path(self.tmp.name) / "state.sqlite3")
        self.client = TestClient(app)
        account = self.client.post("/api/v1/auth/register", json={"name": "Contract account", "email": "contract@example.test", "password": "contract-passphrase-2026"})
        self.assertEqual(account.status_code, 201, account.text)
        self.user_context = store.current_user.set(account.json()["data"]["id"])

    def tearDown(self):
        store.current_user.reset(self.user_context)
        if self.previous is None:
            os.environ.pop("STORESCOUT_DB_PATH", None)
        else:
            os.environ["STORESCOUT_DB_PATH"] = self.previous
        self.tmp.cleanup()

    def test_real_health_and_fixture(self):
        self.assertEqual(self.client.get("/api/v1/health").json()["data"]["status"], "ok")
        value = self.client.get("/api/v1/projects/demo").json()["data"]
        self.assertEqual((len(value["sites"]), len(value["stores"])), (10, 4))
        self.assertEqual(value["source_status"], "ASSUMED")

    def test_scenario_save_is_immutable_and_persists(self):
        body = {"name": "Rent case", "assumptions": {"rent_multiplier": 0.8}}
        response = self.client.post("/api/v1/projects/demo/scenarios", json=body)
        self.assertEqual(response.status_code, 201)
        fresh_client = TestClient(app)
        fresh_client.cookies.update(self.client.cookies)
        values = fresh_client.get("/api/v1/projects/demo/scenarios").json()["data"]
        self.assertEqual(len(values), 2)
        self.assertEqual(values[0]["assumptions"]["rent_multiplier"], 1)
        self.assertEqual(values[1]["assumptions"]["rent_multiplier"], 0.8)

    def test_saved_evaluation_is_explicit_synthetic_trained_mode(self):
        response = self.client.post("/api/v1/projects/demo/evaluate", json={"scenario_id": "baseline"})
        self.assertEqual(response.status_code, 200, response.text[:300])
        value=response.json()["data"]
        self.assertEqual(value["method_mode"],"model_simulated")
        self.assertTrue(value["model_artifact_id"])
        self.assertEqual(len(value["site_analyses"]),10)
        for resource in ["features","dayparts","rankings"]:
            result=self.client.get(f"/api/v1/projects/demo/{resource}?evaluation_id={value['evaluation_id']}")
            self.assertEqual(result.status_code,200,result.text[:150])
            self.assertEqual(result.json()["data"]["evaluation_id"],value["evaluation_id"])
        model=self.client.get("/api/v1/projects/demo/model").json()["data"]
        self.assertTrue(model["trained_model_available"]);self.assertIsNone(model["metrics"])
        self.assertEqual(self.client.get("/api/v1/projects/demo/evaluations/"+value["evaluation_id"]).json()["data"],value)

    def test_atomic_snapshot_rollback(self):
        with self.assertRaises(ValueError):
            store.save_result("demo", "evaluation", "atomic", None, "atomic", "atomic", [("evaluation","atomic",{"ok":True}),("evaluation_context","atomic",{"bad":float("nan")})])
        self.assertIsNone(store.get("evaluation","demo","atomic"))

    def test_idempotency_and_report_snapshot(self):
        response=self.client.post("/api/v1/projects/demo/evaluate",json={},headers={"Idempotency-Key":"unit-request"})
        self.assertEqual(response.status_code,200,response.text[:100]);evaluation=response.json()["data"]
        repeated=self.client.post("/api/v1/projects/demo/evaluate",json={},headers={"Idempotency-Key":"unit-request"})
        self.assertEqual(repeated.json()["data"],evaluation)
        scenario=self.client.post("/api/v1/projects/demo/scenarios",json={"name":"Different","assumptions":{"demand_multiplier":1.1}}).json()["data"]
        conflict=self.client.post("/api/v1/projects/demo/evaluate",json={"scenario_id":scenario["scenario_id"]},headers={"Idempotency-Key":"unit-request"})
        self.assertEqual(conflict.status_code,409)
        run_response = self.client.post("/api/v1/projects/demo/portfolios", json={"evaluation_id": evaluation["evaluation_id"]})
        self.assertEqual(run_response.status_code, 200, run_response.text)
        run_id = run_response.json()["data"]["portfolio_run_id"]
        report=self.client.get(f"/api/v1/projects/demo/reports/{evaluation['evaluation_id']}?portfolio_run_id={run_id}")
        self.assertEqual(report.status_code,200)
        for label in ["SYNTHETIC","ASSUMED",evaluation["evaluation_id"],run_id,evaluation["evidence"]["source_snapshot_id"]]: self.assertIn(label,report.text)
        self.assertEqual(self.client.get(f"/api/v1/projects/demo/reports/missing?portfolio_run_id={run_id}").status_code,404)
        with patch.object(sources, "engine_identity", return_value="future-incompatible-version"):
            self.assertEqual(self.client.post("/api/v1/projects/demo/sites/site-01/rescue",json={"evaluation_id":evaluation["evaluation_id"]}).status_code,409)
            self.assertEqual(self.client.get(f"/api/v1/projects/demo/reports/{evaluation['evaluation_id']}?portfolio_run_id={run_id}").status_code,200)

    def test_snapshot_conflict_and_bad_date(self):
        self.assertEqual(self.client.post("/api/v1/projects/demo/evaluate",json={"feature_snapshot_id":"old"}).status_code,409)
        self.assertEqual(self.client.post("/api/v1/projects/demo/scenarios",json={"name":"bad date","assumptions":{"opening_date":"2027-02-30"}}).status_code,422)

    def test_unknown_project_and_invalid_input(self):
        self.assertEqual(self.client.get("/api/v1/projects/another").status_code, 404)
        self.assertEqual(self.client.post("/api/v1/projects/demo/scenarios", json={"name": "bad", "assumptions": {"demand_multiplier": -1}}).status_code, 422)
        self.assertEqual(self.client.post("/api/v1/projects/demo/scenarios", json={"name": "bad", "assumptions": {"site_overrides": {"missing": {"monthly_rent_inr": 1}}}}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
