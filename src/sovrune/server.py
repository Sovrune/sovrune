"""Zero-dependency HTTP server for the alpha command center."""

from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from urllib.parse import urlparse

from . import __version__
from .offices import run_operating_loop
from .providers import configured_provider
from .sdk import load_adapter


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

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/healthz":
            return self._json({"status": "ok", "version": __version__})
        state = load_adapter().build_state()
        state.validate()
        if path == "/api/state":
            return self._json(state.to_dict())
        if path == "/api/loop":
            return self._json({"company": state.company, "steps": run_operating_loop(state)})
        if path == "/api/provider":
            provider = configured_provider()
            return self._json({"configured": bool(provider and provider.configured()),
                               "provider": provider.name if provider else "none",
                               "model": getattr(provider, "model", None)})
        if path.startswith("/api/"):
            return self._json({"error": "not found"}, 404)
        return super().do_GET()

    def log_message(self, fmt: str, *args: object) -> None:
        # Access logs contain paths only. Request bodies and credentials are never logged.
        super().log_message(fmt, *args)


def serve(host: str = "127.0.0.1", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Sovrune command center: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve(os.getenv("SOVRUNE_HOST", "127.0.0.1"), int(os.getenv("SOVRUNE_PORT", "8787")))
