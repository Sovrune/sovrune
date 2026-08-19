import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from sovrune.accountability import execute_run
from sovrune.core import BusinessState, Evidence, Metric
from sovrune.demo import AcmeAdapter
from sovrune.offices import run_operating_loop
from sovrune.server import Handler
from sovrune.store import AccountabilityStore, StoreError


class AccountabilityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.temp.name, "accountability.db")
        self.store = AccountabilityStore(self.db)

    def tearDown(self):
        self.temp.cleanup()

    def test_run_persists_complete_accountability_chain(self):
        run = execute_run(AcmeAdapter().build_state(), self.store)
        self.assertEqual(run["status"], "awaiting_approval")
        self.assertEqual(len(run["artifacts"]), 7)
        self.assertEqual(run["decision"]["status"], "proposed")
        self.assertEqual(run["approval"]["status"], "pending")
        self.assertEqual(run["prediction"]["status"], "pending_approval")
        reopened = AccountabilityStore(self.db).get_run(run["id"])
        self.assertEqual(reopened["decision"]["evidence"][0]["source"], "acme-demo-generated")

    def test_approval_is_single_use_and_opens_prediction(self):
        run = execute_run(AcmeAdapter().build_state(), self.store)
        resolved = self.store.resolve_approval(run["approval"]["id"], "approve", "founder", "ship experiment")
        self.assertEqual(resolved["status"], "approved")
        self.assertEqual(resolved["decision"]["status"], "approved")
        self.assertEqual(resolved["prediction"]["status"], "open")
        with self.assertRaises(StoreError):
            self.store.resolve_approval(run["approval"]["id"], "reject", "founder")

    def test_rejection_cancels_prediction(self):
        run = execute_run(AcmeAdapter().build_state(), self.store)
        rejected = self.store.resolve_approval(run["approval"]["id"], "reject", "operator")
        self.assertEqual(rejected["status"], "rejected")
        self.assertEqual(rejected["prediction"]["status"], "cancelled")

    def test_generic_company_metric_can_operate(self):
        evidence = Evidence("aggregate-test", "2026-08-19", 0.9)
        state = BusinessState("Generic Co", Metric("Weekly revenue", 80, "usd", 100, evidence),
                              [Metric("Activation", 40, "percent", 50, evidence)])
        steps = run_operating_loop(state)
        self.assertIn("Activation", next(x for x in steps if x["office"] == "Strategy")["summary"])
        self.assertEqual(execute_run(state, self.store)["company"], "Generic Co")


class HttpGateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous = {key: os.environ.get(key) for key in ("SOVRUNE_DB", "SOVRUNE_APPROVAL_TOKEN")}
        os.environ["SOVRUNE_DB"] = os.path.join(self.temp.name, "http.db")
        os.environ.pop("SOVRUNE_APPROVAL_TOKEN", None)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        for key, value in self.previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp.cleanup()

    def request(self, path, payload=None, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Sovrune-Approval-Token"] = token
        request = Request(self.base + path, json.dumps(payload or {}).encode(), headers, method="POST")
        with urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())

    def test_http_mutations_are_disabled_without_explicit_token(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/runs")
        self.assertEqual(caught.exception.code, 503)
        with self.assertRaises(HTTPError) as read_caught:
            urlopen(self.base + "/api/runs", timeout=3)
        self.assertEqual(read_caught.exception.code, 503)

    def test_token_protects_run_and_approval_mutations(self):
        os.environ["SOVRUNE_APPROVAL_TOKEN"] = "test-token-with-enough-entropy"
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/runs", token="wrong")
        self.assertEqual(caught.exception.code, 401)
        status, run = self.request("/api/runs", token="test-token-with-enough-entropy")
        self.assertEqual(status, 201)
        read = Request(self.base + "/api/runs", headers={"X-Sovrune-Approval-Token": "test-token-with-enough-entropy"})
        with urlopen(read, timeout=3) as response:
            self.assertEqual(json.loads(response.read())["runs"][0]["id"], run["id"])
        _, resolved = self.request(f"/api/approvals/{run['approval']['id']}",
                                   {"action": "approve", "actor": "test-approver"},
                                   "test-token-with-enough-entropy")
        self.assertEqual(resolved["prediction"]["status"], "open")


if __name__ == "__main__":
    unittest.main()
