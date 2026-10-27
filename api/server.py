from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Add parent directory to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.app import CordonApplication


class CordonRequestHandler(BaseHTTPRequestHandler):
    application = CordonApplication()

    def _send(self, status: int, body: dict) -> None:
        encoded = json.dumps(body, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_html(self) -> None:
        encoded = (Path(__file__).with_name("index.html")).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send(400, {"error": "request body must be valid JSON"})
            return
        parsed = urlparse(self.path)
        if parsed.path == "/run":
            response = self.application.create_run(payload)
        else:
            parts = parsed.path.strip("/").split("/")
            if len(parts) == 5 and parts[0] == "runs" and parts[2] == "actions" and parts[4] == "approve":
                response = self.application.approve_action(parts[1], parts[3], bool(payload.get("approved", True)))
            else:
                response = type("Response", (), {"status": 404, "body": {"error": "not found"}})()
        self._send(response.status, response.body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send_html()
            return
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "runs":
            run_id = parts[1]
            response = {
                "board": self.application.get_board,
                "paths": self.application.get_paths,
                "trace": self.application.get_trace,
            }.get(parts[2], lambda _: type("Response", (), {"status": 404, "body": {"error": "not found"}})())(run_id)
        else:
            response = type("Response", (), {"status": 404, "body": {"error": "not found"}})()
        self._send(response.status, response.body)

    def log_message(self, *_args: object) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), CordonRequestHandler)
    print(f"Cordon API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
