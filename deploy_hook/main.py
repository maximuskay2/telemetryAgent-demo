"""Signed deploy webhook for TelemetryAgent's Hosting step.

TelemetryAgent POSTs {"action": "rollback" | "restart" | "ping", ...} with
X-Telemetry-Signature: sha256=<HMAC-SHA256(WEBHOOK_SECRET, raw body)>.
Anything unsigned, mis-signed, or older than MAX_SKEW_S is refused.

This demo target has no real deployment to roll back, so accepted actions
are recorded and shown at GET /. Replace `perform()` with your own
rollback/restart call for a real service.
"""

import hashlib
import hmac
import json
import os
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SECRET = os.environ.get("WEBHOOK_SECRET", "")
MAX_SKEW_S = 300
ALLOWED = {"ping", "rollback", "restart"}
history = deque(maxlen=50)


def perform(action: str, body: dict) -> str:
    if action == "ping":
        return "pong"
    return f"{action} acknowledged (demo target: nothing to redeploy)"


class Handler(BaseHTTPRequestHandler):
    def _reply(self, code: int, payload: dict) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.rstrip("/") in ("", "/health"):
            self._reply(200, {
                "ok": True,
                "configured": bool(SECRET),
                "recent": list(history),
            })
            return
        self._reply(404, {"error": "not found"})

    def do_POST(self):
        if self.path.rstrip("/") != "/deploy":
            self._reply(404, {"error": "not found"})
            return
        if not SECRET:
            self._reply(503, {"error": "WEBHOOK_SECRET not set"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        want = "sha256=" + hmac.new(
            SECRET.encode(), raw, hashlib.sha256
        ).hexdigest()
        got = self.headers.get("X-Telemetry-Signature", "")
        if not hmac.compare_digest(want, got):
            self._reply(401, {"error": "bad signature"})
            return
        try:
            body = json.loads(raw)
        except ValueError:
            self._reply(400, {"error": "invalid json"})
            return
        action = body.get("action")
        if action not in ALLOWED:
            self._reply(400, {"error": f"action not allowed: {action}"})
            return
        try:
            ts = float(body.get("ts") or 0)
        except (TypeError, ValueError):
            ts = 0.0
        if abs(time.time() - ts) > MAX_SKEW_S:
            self._reply(401, {"error": "stale request"})
            return
        detail = perform(action, body)
        history.appendleft({
            "at": time.time(),
            "action": action,
            "system_id": body.get("system_id"),
            "run_id": body.get("run_id"),
            "detail": detail,
        })
        self._reply(200, {"ok": True, "detail": detail})

    def log_message(self, fmt, *args):
        print("%s %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"deploy hook on :{port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
