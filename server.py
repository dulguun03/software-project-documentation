"""Local documentation sandbox. No Google calls, real OAuth, AI inference or persistence."""
import argparse
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import default
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
TOKEN = "sprint05-local-sandbox"
LIMIT = 2 * 1024 * 1024


class SandboxServer(ThreadingHTTPServer):
    def __init__(self, address):
        super().__init__(address, Handler)
        self.actions = {}
        self.history = {}
        self.sequence = 0
        self.provider_calls = 0
        self.lock = threading.Lock()


class RequestError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def fields(payload, names):
    if not isinstance(payload, dict) or set(payload) != set(names):
        raise RequestError(400, "Provide exactly these fields: " + ", ".join(names))


def text_fields(payload, names):
    for name in names:
        if not isinstance(payload[name], str) or not payload[name].strip():
            raise RequestError(400, name + " must be a nonempty string.")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / "public"), **kwargs)

    def log_message(self, format, *args):
        pass  # Never log authorization headers or command bodies.

    def send_json(self, code, body):
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def envelope(self, status, message):
        return {"status": status, "user_message": message, "correlation_id": self.correlation}

    def parse_body(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise RequestError(400, "Invalid Content-Length.")
        if size <= 0:
            raise RequestError(400, "A request body is required.")
        if size > LIMIT:
            raise RequestError(413, "Request exceeds 2 MiB.")
        self.connection.settimeout(10)
        raw = self.request_bytes
        content_type = self.headers.get("Content-Type", "")
        if self.path in ("/v1/pets/upload-photo", "/v1/audio/translate-bark"):
            if not content_type.startswith("multipart/form-data;"):
                raise RequestError(415, "Use multipart/form-data with a boundary.")
            message = BytesParser(policy=default).parsebytes(
                ("Content-Type: " + content_type + "\r\nMIME-Version: 1.0\r\n\r\n").encode() + raw)
            if not message.is_multipart():
                raise RequestError(400, "Malformed multipart body.")
            payload = {}
            for part in message.iter_parts():
                name = part.get_param("name", header="Content-Disposition")
                if name in payload:
                    raise RequestError(400, "Duplicate multipart field.")
                data = part.get_payload(decode=True)
                if part.get_filename():
                    payload[name] = {"filename": Path(part.get_filename()).name,
                                     "content_type": part.get_content_type(), "data": data}
                else:
                    payload[name] = data.decode("utf-8")
            return payload
        if content_type.split(";")[0] != "application/json":
            raise RequestError(415, "Use application/json.")
        try:
            return json.loads(raw)
        except (ValueError, UnicodeError):
            raise RequestError(400, "Malformed JSON body.")

    def do_POST(self):
        with self.server.lock:
            self.server.sequence += 1
            self.correlation = f"corr_sandbox_{self.server.sequence:04d}"
            try:
                # Consume ordinary request bodies before early error responses on Windows.
                # Cap the read so oversized uploads never allocate unbounded memory.
                self.connection.settimeout(10)
                size = int(self.headers.get("Content-Length", "0"))
                if size < 0:
                    raise RequestError(400, "Invalid Content-Length.")
                self.request_bytes = self.rfile.read(min(size, LIMIT + 1))
                if self.headers.get("Authorization") != "Bearer " + TOKEN:
                    raise RequestError(401, "Missing or invalid sandbox bearer token.")
                failure = self.headers.get("X-Sandbox-Failure")
                if failure in ("403", "500", "503"):
                    raise RequestError(int(failure), {"403": "Sandbox provider permission is unavailable.",
                        "500": "Unexpected internal sandbox error.", "503": "Sandbox dependency unavailable."}[failure])
                payload = self.parse_body()
                code, result = self.dispatch(payload)
                self.send_json(code, result)
            except RequestError as error:
                self.send_json(error.status, {**self.envelope("error", error.message),
                    "error": {"code": "http_" + str(error.status), "message": error.message}})
            except (UnicodeError, ValueError, KeyError, TypeError):
                self.send_json(400, {**self.envelope("error", "Review the request field types and values."),
                    "error": {"code": "http_400", "message": "Review the request field types and values."}})
            except Exception:
                self.send_json(500, {**self.envelope("error", "Unexpected internal sandbox error."),
                    "error": {"code": "http_500", "message": "Unexpected internal sandbox error."}})

    def dispatch(self, payload):
        path = self.path
        if path == "/v1/commands":
            fields(payload, ["session_id", "transcript", "intent", "event"])
            text_fields(payload, ["session_id", "transcript", "intent"])
            if payload["intent"] != "calendar.create":
                raise RequestError(400, "This sandbox supports calendar.create only.")
            event = payload["event"]
            fields(event, ["title", "start", "end", "timezone"])
            text_fields(event, ["title", "start", "end", "timezone"])
            start, end = [datetime.fromisoformat(event[key].replace("Z", "+00:00")) for key in ["start", "end"]]
            if start.tzinfo is None or end.tzinfo is None or end <= start or event["timezone"] != "Asia/Ulaanbaatar":
                raise RequestError(400, "Use timezone-aware start/end, end after start, and Asia/Ulaanbaatar.")
            action_id = f"action_{len(self.server.actions)+1:04d}"
            self.server.actions[action_id] = {**payload, "payload_version": 1, "status": "proposed"}
            return 200, {**self.envelope("proposed", "Review this action before confirming."),
                "transcript": payload["transcript"], "intent": payload["intent"], "action_id": action_id,
                "payload_version": 1, "required_fields": [], "event": event}
        match = re.fullmatch(r"/v1/actions/([a-zA-Z0-9_]+)/(?P<verb>confirm|execute)", path)
        if match:
            fields(payload, ["session_id", "payload_version"])
            text_fields(payload, ["session_id"])
            if type(payload["payload_version"]) is not int or payload["payload_version"] < 1:
                raise RequestError(400, "payload_version must be a positive integer.")
            action_id, verb = match.group(1), match.group("verb")
            action = self.server.actions.get(action_id)
            if not action or action["session_id"] != payload["session_id"]:
                raise RequestError(404, "Resource or session action not found.")
            if action["payload_version"] != payload["payload_version"]:
                raise RequestError(409, "Action version or confirmation conflicts.")
            if verb == "confirm":
                if action["status"] not in ("proposed", "confirmed"):
                    raise RequestError(409, "Completed actions cannot be reconfirmed.")
                action["status"] = "confirmed"
            else:
                if action["status"] not in ("confirmed", "succeeded"):
                    raise RequestError(409, "Confirm the exact action before execution.")
                if action["status"] == "confirmed":
                    self.server.provider_calls += 1  # Simulated provider write count, no network.
                    action["status"] = "succeeded"
                    self.server.history.setdefault(action["session_id"], []).append({"action_id": action_id,
                        "type": action["intent"], "status": "succeeded",
                        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})
            return 200, {**self.envelope(action["status"], "Sandbox action " + action["status"] + "."),
                "action_id": action_id, "payload_version": 1,
                "provider_resource_id": "sandbox_event_" + action_id if action["status"] == "succeeded" else ""}
        if path == "/v1/contacts/search":
            fields(payload, ["query"]); text_fields(payload, ["query"])
            contacts = [{"name": "Anu", "email": "anu@example.org"}] if "anu" in payload["query"].lower() else []
            return 200, {**self.envelope("succeeded", "Sandbox contacts searched."), "contacts": contacts}
        if path == "/v1/sessions/history":
            fields(payload, ["session_id"]); text_fields(payload, ["session_id"])
            return 200, {**self.envelope("succeeded", "Sandbox session history retrieved."),
                "items": self.server.history.get(payload["session_id"], [])}
        if path in ("/v1/pets/upload-photo", "/v1/audio/translate-bark"):
            file_field = "photo" if path.endswith("upload-photo") else "audio"
            fields(payload, ["pet_id", file_field]); text_fields(payload, ["pet_id"])
            if payload["pet_id"] != "corgi_98231":
                raise RequestError(404, "Pet not found in sandbox fixtures.")
            upload = payload[file_field]
            if not isinstance(upload, dict) or not upload.get("data"):
                raise RequestError(400, "A nonempty file is required.")
            if file_field == "photo":
                if upload["content_type"] != "image/png" or not upload["data"].startswith(b"\x89PNG\r\n\x1a\n"):
                    raise RequestError(415, "Upload an image/png fixture.")
                return 200, {"pet_id": payload["pet_id"], "photo_id": "photo_0001",
                    "filename": upload["filename"], "bytes_received": len(upload["data"])}
            if upload["content_type"] != "audio/wav" or not (upload["data"].startswith(b"RIFF") and upload["data"][8:12] == b"WAVE"):
                raise RequestError(415, "Upload an audio/wav fixture.")
            return 200, {"pet_id": payload["pet_id"], "meaning": "I want to play.", "confidence": 0.92, "simulated": True}
        if path == "/v1/webhooks/subscribe":
            fields(payload, ["pet_id", "callback_url", "events"])
            text_fields(payload, ["pet_id", "callback_url"])
            callback = urlsplit(payload["callback_url"])
            if callback.scheme != "https" or not callback.hostname or callback.username or callback.password:
                raise RequestError(400, "callback_url must be HTTPS with a hostname and no credentials.")
            if payload["pet_id"] != "corgi_98231":
                raise RequestError(404, "Pet not found in sandbox fixtures.")
            if payload["events"] != ["pet.activity.detected"]:
                raise RequestError(400, "Choose the supported pet.activity.detected event.")
            return 201, {"subscription_id": "subscription_0001", **payload, "status": "active"}
        raise RequestError(404, "Endpoint not found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8080, type=int)
    args = parser.parse_args()
    server = SandboxServer((args.host, args.port))
    print(f"Sandbox ready at http://{args.host}:{args.port}/swagger/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
