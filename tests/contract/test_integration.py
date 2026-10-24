"""Transport tests with explicit test doubles, never production model evidence."""
import copy
import json
import os
import shutil
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

BASE = "/api/v1/projects/demo"


def test_engine(project, scenario):
    """Only a contract fixture. No claim of numerical/model validity."""
    rows = []
    for index, site in enumerate(project["sites"]):
        status = "AT_RISK" if index == 1 else "REJECTED" if index == 2 else "VIABLE"
        rows.append({"site_id": site["site_id"], "annual_revenue_inr": 100, "lost_existing_contribution_inr": 0, "annual_cashflows_inr": [1] * project["projection_years"], "npv_inr": 1000 - index, "roi_fraction": None, "payback_years": None, "failfast": {"status": status, "failed_rule_ids": [], "reasons": ["TEST FIXTURE ONLY"]}, "drivers": ["<script>alert('test')</script>"], "source_ids": ["synthetic-cells"]})
    return {"method_mode": "scenario_assumptions", "site_analyses": rows, "rankings": [r["site_id"] for r in rows if r["failfast"]["status"] in {"VIABLE", "AT_RISK"}], "model_artifact_id": None, "_context": {"test_only": True}}


def test_portfolio(project, context, max_stores, acknowledgements):
    """Contract output only; backend checks its budget, not its economics."""
    selected = [project["sites"][0]] if max_stores and project["budget_inr"] >= project["sites"][0]["capex_inr"] else []
    used = sum(site["capex_inr"] for site in selected)
    return {"selected_site_ids": [site["site_id"] for site in selected], "budget_used_inr": used, "budget_unused_inr": project["budget_inr"] - used, "full_network_npv_inr": 100 if selected else 0, "status": "FULL_NETWORK_EXACT", "evaluated_subsets": 1024, "total_subsets": 1024}


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name)
        self.data = self.directory / "data"
        shutil.copytree(sources.DATA_ROOT, self.data)
        self.env = patch.dict(os.environ, {"STORESCOUT_DB_PATH": str(self.directory / "state.sqlite3"), "STORESCOUT_MODEL_DIR": str(self.directory / "model")})
        self.env.start()
        self.source_patch = patch.object(sources, "DATA_ROOT", self.data)
        self.source_patch.start()
        self.engine = patch.object(gateway.pipeline, "run_evaluation", side_effect=test_engine)
        self.engine_mock = self.engine.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.engine.stop()
        self.source_patch.stop()
        self.env.stop()
        self.tmp.cleanup()

    def evaluate(self, scenario_id="baseline", **kwargs):
        result = self.client.post(BASE + "/evaluate", json={"scenario_id": scenario_id}, **kwargs)
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()["data"]

    def scenario(self, **kwargs):
        response = self.client.post(BASE + "/scenarios", json={"name": "Test case", "assumptions": {}, **kwargs})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["data"]

    def test_evaluation_cache_restart_and_saved_reads(self):
        first = self.evaluate()
        second = self.evaluate(headers={"Idempotency-Key": "eval-1"})
        self.assertEqual(first, second)
        self.assertEqual(self.engine_mock.call_count, 1)
        with TestClient(app) as fresh:
            self.assertEqual(fresh.get(BASE + "/evaluations/" + first["evaluation_id"]).json()["data"], first)
        identity = first["evaluation_id"]
        row = self.client.get(BASE + f"/sites/site-01/analysis?evaluation_id={identity}")
        self.assertEqual(row.json()["meta"]["evaluation_id"], identity)
        ranks = self.client.get(BASE + f"/rankings?evaluation_id={identity}").json()["data"]
        self.assertEqual(ranks["rankings"], first["rankings"])
        self.assertEqual(len(ranks["diagnoses"]), 10)
        self.assertEqual(len(store.list_objects("evaluation_context", "demo")), 1)

    def test_idempotency_conflict_and_changed_scenario(self):
        first = self.evaluate(headers={"Idempotency-Key": "same-key"})
        changed = self.scenario(assumptions={"rent_multiplier": 0.8})
        response = self.client.post(BASE + "/evaluate", headers={"Idempotency-Key": "same-key"}, json={"scenario_id": changed["scenario_id"]})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "IDEMPOTENCY_CONFLICT")
        self.assertNotEqual(first["evaluation_id"], self.evaluate(changed["scenario_id"])["evaluation_id"])
        self.assertEqual(self.engine_mock.call_count, 2)

    def test_source_change_invalidates_cache_and_old_report_is_frozen(self):
        first = self.evaluate()
        cells = json.loads((self.data / "cells.json").read_text())
        cells[0]["annual_wallet_inr"] += 1
        (self.data / "cells.json").write_text(json.dumps(cells))
        second = self.evaluate()
        self.assertNotEqual(first["evaluation_id"], second["evaluation_id"])
        report = self.client.get(BASE + f"/reports/{first['evaluation_id']}?format=json").json()["data"]
        self.assertNotEqual(report["snapshot"]["source_snapshot_hash"], sources.installed_snapshot()["snapshot_hash"])
        self.assertNotIn("prepared_network", report)
        self.assertNotIn("inputs", report["project"])

    def test_invalid_output_does_not_commit_partial_state(self):
        broken = test_engine(sources.installed_snapshot()["project"], {})
        broken["site_analyses"].pop()
        self.engine_mock.side_effect = None
        self.engine_mock.return_value = broken
        response = self.client.post(BASE + "/evaluate", json={})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(store.list_objects("evaluation", "demo"), [])
        self.assertEqual(store.list_objects("evaluation_context", "demo"), [])
        broken["_context"] = {"bad": float("nan")}
        broken["site_analyses"] = test_engine(sources.installed_snapshot()["project"], {})["site_analyses"]
        self.assertEqual(self.client.post(BASE + "/evaluate", json={}).status_code, 502)

    def test_model_claim_requires_actual_matching_bundle(self):
        broken = test_engine(sources.installed_snapshot()["project"], {})
        broken.update(method_mode="model_simulated", model_artifact_id="invented")
        self.engine_mock.side_effect = None
        self.engine_mock.return_value = broken
        self.assertEqual(self.client.post(BASE + "/evaluate", json={}).status_code, 502)
        self.assertEqual(self.client.get(BASE + "/model").status_code, 503)
        model_dir = self.directory / "model"
        model_dir.mkdir()
        (model_dir / "test.bin").write_bytes(b"TEST ARTIFACT: NOT A TRAINED MODEL")
        (model_dir / "model_card.json").write_text(json.dumps({"artifact_file": "test.bin", "model_artifact_id": "invented", "method_mode": "model_simulated"}))
        result = self.evaluate()
        self.assertEqual(result["method_mode"], "model_simulated")
        model = self.client.get(BASE + "/model").json()["data"]
        self.assertEqual(len(model["artifact_sha256"]), 64)
        self.assertNotIn("artifact_path", model)
        (model_dir / "test.bin").write_bytes(b"CHANGED TEST ARTIFACT")
        response = self.client.post(BASE + "/portfolios", json={"evaluation_id": result["evaluation_id"]})
        self.assertEqual(response.status_code, 409)

    def test_artifact_cannot_escape_bundle_directory(self):
        model_dir = self.directory / "model"
        model_dir.mkdir()
        (self.directory / "outside.bin").write_bytes(b"outside")
        (model_dir / "model_card.json").write_text(json.dumps({"artifact_file": "../outside.bin", "model_artifact_id": "x", "method_mode": "model_simulated"}))
        self.assertEqual(self.client.get(BASE + "/model").status_code, 503)

    def test_unknown_ids_dates_and_bounds(self):
        self.assertEqual(self.client.post(BASE + "/evaluate", json={"scenario_id": "missing"}).status_code, 404)
        self.assertEqual(self.client.post(BASE + "/evaluate", json={"feature_snapshot_id": "stale"}).status_code, 409)
        for value in ["2026-02-30", "20261024", "2026-10-24T00:00:00"]:
            response = self.client.post(BASE + "/scenarios", json={"name": "bad", "assumptions": {"opening_date": value}})
            self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.post(BASE + "/sites/site-01/rescue", json={"evaluation_id": "missing", "lower_bound": 10, "upper_bound": 1}).status_code, 422)
        self.assertEqual(self.client.get(BASE + "/evaluations/missing").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/projects/other/evaluations/anything").status_code, 404)

    def test_portfolio_budget_and_empty_plan_use_saved_scenario(self):
        scenario = self.scenario(budget_inr=0)
        evaluation = self.evaluate(scenario["scenario_id"])
        with patch.object(gateway.pipeline, "run_portfolio", side_effect=test_portfolio) as engine:
            first = self.client.post(BASE + "/portfolios", json={"evaluation_id": evaluation["evaluation_id"]})
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(first.json()["data"]["selected_site_ids"], [])
            self.assertEqual(engine.call_args.args[0]["budget_inr"], 0)
            second = self.client.post(BASE + "/portfolios", json={"evaluation_id": evaluation["evaluation_id"]})
            self.assertEqual(first.json(), second.json())
            self.assertEqual(engine.call_count, 1)

    def test_portfolio_rejects_unacknowledged_risk_and_false_exactness(self):
        evaluation = self.evaluate()
        output = test_portfolio(sources.installed_snapshot()["project"], {}, 2, [])
        output.update(selected_site_ids=["site-02"], budget_used_inr=6250000, budget_unused_inr=13750000)
        with patch.object(gateway.pipeline, "run_portfolio", return_value=output):
            response = self.client.post(BASE + "/portfolios", json={"evaluation_id": evaluation["evaluation_id"]})
            self.assertEqual(response.status_code, 502)
            good = self.client.post(BASE + "/portfolios", json={"evaluation_id": evaluation["evaluation_id"], "acknowledged_risk_site_ids": ["site-02"]})
            self.assertEqual(good.status_code, 200, good.text)
            output["evaluated_subsets"] = 10
            response = self.client.post(BASE + "/portfolios", json={"evaluation_id": evaluation["evaluation_id"], "max_stores": 3, "acknowledged_risk_site_ids": ["site-02"]})
            self.assertEqual(response.status_code, 502)
        self.assertEqual(len(store.list_objects("portfolio", "demo")), 1)

    def test_report_escapes_content_and_requires_matching_portfolio(self):
        first = self.evaluate()
        second = self.evaluate(self.scenario()["scenario_id"])
        with patch.object(gateway.pipeline, "run_portfolio", side_effect=test_portfolio):
            run = self.client.post(BASE + "/portfolios", json={"evaluation_id": first["evaluation_id"]}).json()["data"]
        url = BASE + f"/reports/{first['evaluation_id']}?portfolio_run_id={run['portfolio_run_id']}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("<script>", response.text)
        self.assertIn("&lt;script&gt;", response.text)
        self.assertIn("default-src 'none'", response.headers["content-security-policy"])
        self.assertEqual(self.client.get(BASE + f"/reports/{second['evaluation_id']}?portfolio_run_id={run['portfolio_run_id']}").status_code, 409)
        self.assertEqual(self.client.get(BASE + "/portfolios/" + run["portfolio_run_id"]).json()["data"], run)

    def test_rescue_is_a_saved_proposal_not_scenario_mutation(self):
        evaluation = self.evaluate()
        output = {"status": "SOLVED", "threshold": 100000, "verification_npv_inr": 0.5, "reasons": ["TEST ONLY"]}
        with patch.object(gateway.pipeline, "run_rescue", return_value=output, create=True):
            response = self.client.post(BASE + "/sites/site-01/rescue", json={"evaluation_id": evaluation["evaluation_id"]})
            self.assertEqual(response.status_code, 200, response.text)
            result = response.json()["data"]
            self.assertEqual(result["upper_bound"], 800000)
            self.assertEqual(self.client.get(BASE + "/rescues/" + result["rescue_id"]).json()["data"], result)
            output["threshold"] = 900000
            invalid = self.client.post(BASE + "/sites/site-01/rescue", json={"evaluation_id": evaluation["evaluation_id"], "upper_bound": 700000})
            self.assertEqual(invalid.status_code, 502)
        self.assertEqual(store.list_objects("scenario", "demo"), [])
        self.assertEqual(self.client.get(BASE + "/evaluations/" + evaluation["evaluation_id"]).json()["data"], evaluation)

    def test_source_and_daypart_results_are_not_confused(self):
        value = self.client.get(BASE + "/features").json()["data"]
        self.assertFalse(value["prepared"])
        self.assertEqual(len(value["cells"]), 100)
        evaluation = self.evaluate()
        url = BASE + "/dayparts?evaluation_id=" + evaluation["evaluation_id"]
        self.assertEqual(self.client.get(url + "&time_bin=weekday_lunch").status_code, 503)
        self.assertEqual(self.client.get(url + "&time_bin=imaginary").status_code, 422)

    def test_engine_change_blocks_recomputation_but_not_saved_reads(self):
        evaluation = self.evaluate()
        with patch.object(sources, "engine_identity", return_value="changed"):
            response = self.client.post(BASE + "/portfolios", json={"evaluation_id": evaluation["evaluation_id"]})
            self.assertEqual(response.status_code, 409)
            self.assertEqual(self.client.get(BASE + "/evaluations/" + evaluation["evaluation_id"]).status_code, 200)

    def test_timeout_does_not_publish_late_result(self):
        release = threading.Event()
        def slow(project, scenario):
            release.wait(2)
            return test_engine(project, scenario)
        self.engine_mock.side_effect = slow
        try:
            with patch.dict(os.environ, {"STORESCOUT_COMPUTE_TIMEOUT_SECONDS": "0.01"}):
                response = self.client.post(BASE + "/evaluate", json={})
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.json()["error"]["code"], "ENGINE_TIMEOUT")
        finally:
            release.set()
        self.assertEqual(store.list_objects("evaluation", "demo"), [])

    def test_atomic_rollback_and_concurrent_cache_publication(self):
        with self.assertRaises(sqlite3.IntegrityError):
            store.save_result("demo", "evaluation", "rollback", None, "r", "x", [("evaluation", "x", {"ok": 1}), ("evaluation", "x", {"bad": 1})])
        self.assertIsNone(store.get("evaluation", "demo", "x"))
        self.assertIsNone(store.cached_id("demo", "evaluation", "rollback", None, "r"))
        barrier = threading.Barrier(2)
        def publish(identity):
            barrier.wait()
            return store.save_result("demo", "evaluation", "same", None, "r", identity, [("evaluation", identity, {"identity": identity})])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(publish, ["a", "b"]))
        self.assertEqual(results[0], results[1])
        self.assertEqual(len(store.list_objects("evaluation", "demo")), 1)


if __name__ == "__main__":
    unittest.main()
