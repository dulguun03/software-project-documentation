"""Exercise real HTTP requests and runnable samples against a fresh local server."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from server import SandboxServer, TOKEN


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = SandboxServer(("127.0.0.1", 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)
        cls.spec = json.loads((ROOT / "docs/openapi/openapi.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def setUp(self):
        self.server.actions.clear(); self.server.history.clear(); self.server.provider_calls = 0

    def post(self, path, payload, token=TOKEN, extra=None, raw=None):
        headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json", **(extra or {})}
        request = Request(self.base + "/v1" + path, data=raw if raw is not None else json.dumps(payload).encode(), headers=headers)
        try:
            response = urlopen(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def proposal(self):
        payload = self.spec["paths"]["/commands"]["post"]["requestBody"]["content"]["application/json"]["example"]
        status, body = self.post("/commands", payload)
        self.assertEqual(status, 200)
        return body["action_id"]

    def test_01_all_four_samples_run_and_return_expected_statuses(self):
        evidence = {}
        for sample, statuses in [("assistant_workflow.py", [200]*5), ("upload_photo.py", [200]),
                                 ("translate_bark.py", [200]), ("subscribe_webhook.py", [201])]:
            result = subprocess.run([sys.executable, str(ROOT/"samples"/sample)], capture_output=True, text=True,
                encoding="utf-8", env={**os.environ, "API_BASE_URL": self.base + "/v1", "PYTHONIOENCODING": "utf-8"}, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            records = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual([item["http_status"] for item in records], statuses)
            evidence[sample] = records
        self.assertEqual(evidence["upload_photo.py"][0]["body"]["bytes_received"], (ROOT/"assets/einstein.png").stat().st_size)
        self.assertTrue(evidence["translate_bark.py"][0]["body"]["simulated"])
        self.assertEqual(len(evidence["assistant_workflow.py"][-1]["body"]["items"]), 1)
        (ROOT/"evidence").mkdir(exist_ok=True)
        (ROOT/"evidence/sample-responses.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_02_missing_or_wrong_token_is_401(self):
        code, body = self.post("/contacts/search", {"query": "Anu"}, token="")
        self.assertEqual(code, 401); self.assertEqual(body["error"]["code"], "http_401")

    def test_03_execute_without_confirmation_makes_zero_writes(self):
        action = self.proposal()
        code, _ = self.post(f"/actions/{action}/execute", {"session_id": "session_anu_01", "payload_version": 1})
        self.assertEqual(code, 409); self.assertEqual(self.server.provider_calls, 0)

    def test_04_wrong_version_and_session_cannot_confirm(self):
        action = self.proposal()
        for payload, expected in [({"session_id":"session_anu_01","payload_version":2},409),
                                  ({"session_id":"session_other","payload_version":1},404)]:
            self.assertEqual(self.post(f"/actions/{action}/confirm",payload)[0],expected)
        self.assertEqual(self.server.actions[action]["status"], "proposed")

    def test_05_thirty_retries_create_one_simulated_write(self):
        action = self.proposal(); payload = {"session_id":"session_anu_01","payload_version":1}
        self.assertEqual(self.post(f"/actions/{action}/confirm", payload)[0], 200)
        ids = {self.post(f"/actions/{action}/execute",payload)[1]["provider_resource_id"] for _ in range(30)}
        self.assertEqual(len(ids), 1); self.assertEqual(self.server.provider_calls, 1)
        self.assertEqual(len(self.server.history["session_anu_01"]), 1)

    def test_06_history_is_session_filtered(self):
        self.assertEqual(self.post("/sessions/history", {"session_id":"session_other"})[1]["items"], [])

    def test_07_missing_fields_and_malformed_json_are_400(self):
        self.assertEqual(self.post("/commands", {})[0], 400)
        self.assertEqual(self.post("/commands", {}, raw=b'{broken')[0], 400)
        self.assertEqual(self.post("/contacts/search", {"query": 3})[0], 400)

    def test_08_failure_simulation_blocks_writes(self):
        action = self.proposal()
        for status in (403,500,503):
            code, body = self.post(f"/actions/{action}/execute", {"session_id":"session_anu_01","payload_version":1},extra={"X-Sandbox-Failure":str(status)})
            self.assertEqual(code,status); self.assertIn("correlation_id",body)
        self.assertEqual(self.server.provider_calls,0)

    def test_09_webhook_rejects_non_https_and_unknown_events(self):
        payload={"pet_id":"corgi_98231","callback_url":"http://example.org/corgly/pet-activity","events":["pet.activity.detected"]}
        self.assertEqual(self.post("/webhooks/subscribe",payload)[0],400)
        payload.update(callback_url="https://example.org/corgly/pet-activity",events=["pet.deleted"])
        self.assertEqual(self.post("/webhooks/subscribe",payload)[0],400)

    def test_10_unknown_action_and_empty_search(self):
        self.assertEqual(self.post("/actions/action_missing/confirm",{"session_id":"session_anu_01","payload_version":1})[0],404)
        self.assertEqual(self.post("/contacts/search",{"query":"Temuulen"})[1]["contacts"],[])

    def test_11_invalid_media_type_and_oversized_body(self):
        self.assertEqual(self.post("/pets/upload-photo",{})[0],415)
        self.assertEqual(self.post("/contacts/search",{},raw=b' '*(2*1024*1024+1))[0],413)

    def test_12_calendar_time_validation(self):
        payload=json.loads(json.dumps(self.spec["paths"]["/commands"]["post"]["requestBody"]["content"]["application/json"]["example"]))
        payload["event"]["end"]="2026-10-06T09:00:00+08:00"
        self.assertEqual(self.post("/commands",payload)[0],400)
        self.assertEqual(len(self.server.actions),0)


if __name__ == "__main__":
    unittest.main()
