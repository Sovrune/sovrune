"""Zero-dependency HTTP server for the alpha command center."""

from __future__ import annotations

import json
import os
import secrets
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import urlparse

from . import __version__
from .accountability import execute_run
from .offices import run_operating_loop
from .providers import configured_provider
from .sdk import load_adapter
from .store import AccountabilityStore, StoreError


class Handler(SimpleHTTPRequestHandler):
    static = files("sovrune").joinpath("static")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.static), **kwargs)

    def _json(self, payload: object, code: int = 200) -> None:
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _control_authorized(self) -> bool:
        token = os.getenv("SOVRUNE_APPROVAL_TOKEN", "")
        supplied = self.headers.get("X-Sovrune-Approval-Token", "")
        if len(token) < 24:
            self._json({"error": "accountability HTTP API is disabled; configure a SOVRUNE_APPROVAL_TOKEN of at least 24 characters"}, 503)
            return False
        if not secrets.compare_digest(token, supplied):
            self._json({"error": "unauthorized"}, 401)
            return False
        return True

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/healthz":
            return self._json({"status": "ok", "version": __version__})
        if path == "/api/runs" or path.startswith("/api/runs/") or path == "/api/approvals":
            if not self._control_authorized():
                return None
            store = AccountabilityStore()
            if path == "/api/runs":
                return self._json({"runs": store.list_runs()})
            if path.startswith("/api/runs/"):
                run = store.get_run(path.removeprefix("/api/runs/"))
                return self._json(run if run else {"error": "run not found"}, 200 if run else 404)
            return self._json({"approvals": store.list_approvals()})
        if path == "/api/state":
            state = load_adapter().build_state()
            state.validate()
            return self._json(state.to_dict())
        if path == "/api/loop":
            state = load_adapter().build_state()
            state.validate()
            return self._json({"company": state.company, "steps": run_operating_loop(state)})
        if path == "/api/provider":
            provider = configured_provider()
            return self._json({"configured": bool(provider and provider.configured()),
                               "provider": provider.name if provider else "none",
                               "model": getattr(provider, "model", None)})
        if path.startswith("/api/"):
            return self._json({"error": "not found"}, 404)
        return super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if not self._control_authorized():
            return None
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._json({"error": "invalid content length"}, 400)
        if length > 65536:
            return self._json({"error": "request too large"}, 413)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "invalid JSON"}, 400)
        store = AccountabilityStore()
        try:
            if path == "/api/runs":
                state = load_adapter().build_state()
                return self._json(execute_run(state, store), 201)
            if path.startswith("/api/approvals/"):
                approval_id = path.removeprefix("/api/approvals/")
                return self._json(store.resolve_approval(approval_id, payload.get("action", ""),
                                                         payload.get("actor", ""), payload.get("note", "")))
        except (StoreError, ValueError) as error:
            return self._json({"error": str(error)}, 409)
        return self._json({"error": "not found"}, 404)

    def log_message(self, fmt: str, *args: object) -> None:
        # Access logs contain paths only. Request bodies and credentials are never logged.
        super().log_message(fmt, *args)


def serve(host: str = "127.0.0.1", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Sovrune command center: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve(os.getenv("SOVRUNE_HOST", "127.0.0.1"), int(os.getenv("SOVRUNE_PORT", "8787")))
