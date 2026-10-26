"""Minimal standard-library HTTP API + static file server for SyncGuard E1."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json
import os

from e1_engine import ConcurrencyEngine

ROOT = Path(__file__).resolve().parent
engine = ConcurrencyEngine()


class SyncGuardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._json(200, {"status": "OK", "service": "SyncGuard E1"})
        if path == "/api/document":
            return self._json(200, {"status": "OK", **engine.snapshot()})
        if path == "/api/info":
            return self._json(200, {
                "name": "SyncGuard E1",
                "purpose": "Concurrency and synchronization prototype",
                "features": ["thread lock", "document version check", "permission gate", "conflict response"],
                "limitations": ["in-memory only", "single process", "whole-document replacement"]
            })
        if path == "/":
            self.path = "/static/index.html"
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/edit":
            return self._json(404, {"status": "NOT_FOUND", "message": "Unknown API endpoint."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 50000:
                return self._json(400, {"status": "REJECTED", "message": "Invalid request size."})
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"status": "REJECTED", "message": "Request body must be valid JSON."})

        result = engine.apply_edit(
            username=payload.get("username", ""),
            new_content=payload.get("content", ""),
            can_edit=payload.get("can_edit", False) is True,
            expected_version=payload.get("expected_version")
        )
        code = 200 if result["status"] == "ACCEPTED" else (409 if result["status"] == "CONFLICT" else 403)
        return self._json(code, result)

    def log_message(self, fmt, *args):
        # Keep terminal readable while retaining normal HTTP status output.
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    host = os.environ.get("SYNCGUARD_HOST", "127.0.0.1")
    port = int(os.environ.get("SYNCGUARD_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), SyncGuardHandler)
    print("SyncGuard E1 is running at http://%s:%s" % (host, port))
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SyncGuard E1...")
    finally:
        server.server_close()
