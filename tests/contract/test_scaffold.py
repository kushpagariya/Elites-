"""Check real scaffold boundaries; analytics are intentionally unavailable."""
import os
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app


class ScaffoldContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get("STORESCOUT_DB_PATH")
        os.environ["STORESCOUT_DB_PATH"] = str(Path(self.tmp.name) / "state.sqlite3")
        self.client = TestClient(app)

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("STORESCOUT_DB_PATH", None)
        else:
            os.environ["STORESCOUT_DB_PATH"] = self.previous
        self.tmp.cleanup()

    def test_real_health_and_fixture(self):
        self.assertEqual(self.client.get("/api/v1/health").json()["data"]["status"], "ok")
        value = self.client.get("/api/v1/projects/demo").json()["data"]
        self.assertEqual((len(value["sites"]), len(value["stores"])), (10, 4))
        self.assertEqual(value["source_status"], "SYNTHETIC")

    def test_scenario_save_is_immutable_and_persists(self):
        body = {"name": "Rent case", "assumptions": {"rent_multiplier": 0.8}}
        response = self.client.post("/api/v1/projects/demo/scenarios", json=body)
        self.assertEqual(response.status_code, 201)
        fresh_client = TestClient(app)
        values = fresh_client.get("/api/v1/projects/demo/scenarios").json()["data"]
        self.assertEqual(len(values), 2)
        self.assertEqual(values[0]["assumptions"]["rent_multiplier"], 1)
        self.assertEqual(values[1]["assumptions"]["rent_multiplier"], 0.8)

    def test_unimplemented_is_not_fake_success(self):
        response = self.client.post("/api/v1/projects/demo/evaluate", json={"scenario_id": "baseline"})
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()["error"]["code"], "NOT_IMPLEMENTED")

    def test_unknown_project_and_invalid_input(self):
        self.assertEqual(self.client.get("/api/v1/projects/another").status_code, 404)
        self.assertEqual(self.client.post("/api/v1/projects/demo/scenarios", json={"name": "bad", "assumptions": {"demand_multiplier": -1}}).status_code, 422)
        self.assertEqual(self.client.post("/api/v1/projects/demo/scenarios", json={"name": "bad", "assumptions": {"site_overrides": {"missing": {"monthly_rent_inr": 1}}}}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
