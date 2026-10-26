from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from cordon.memory import HMemStore


class ServiceHandler(BaseHTTPRequestHandler):
    memory = HMemStore(os.getenv("HMEM_STORE_PATH"))

    def _send(self, status: int, body: dict[str, Any]) -> None:
        encoded = json.dumps(body, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        if self.path in ("/", "/health"):
            self._send(200, {"status": "ok", "service": os.getenv("SERVICE_ROLE", "all")})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        try:
            body = self._body()
            if self.path == "/model/complete":
                self._send(200, {
                    "content": {"hypotheses": ["internet_reachable_patient_impact"]},
                    "provider": "local-service",
                    "model": body.get("model", "cordon-local"),
                })
                return
            if self.path == "/memory/remember":
                record = self.memory.remember(**body)
                self._send(201, {"memory": record.__dict__})
                return
            if self.path == "/memory/retrieve":
                self._send(200, {
                    "memories": self.memory.retrieve(
                        body["query"],
                        limit=body.get("limit", 5),
                        include_expired=body.get("include_expired", False),
                    )
                })
                return
            if self.path == "/execute":
                approved = body.get("approval_state") == "approved"
                self._send(200, {
                    "action_id": body.get("action", {}).get("id"),
                    "approval_state": body.get("approval_state"),
                    "executed": False,
                    "reason": "live service records approved work; remediation handler is not configured" if approved else "human approval is required",
                    "details": {"mode": "record-only"},
                })
                return
        except (KeyError, TypeError, ValueError) as error:
            self._send(400, {"error": str(error)})
            return
        self._send(404, {"error": "not found"})

    def log_message(self, *_args: object) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8100) -> None:
    server = ThreadingHTTPServer((host, port), ServiceHandler)
    print(f"Cordon local services listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Cordon's local live service stack.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8100)
    args = parser.parse_args()
    serve(args.host, args.port)
