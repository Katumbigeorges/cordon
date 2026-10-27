#!/usr/bin/env python3
"""
Meterless H-MEM Mock Service for Cordon Demo

This is a lightweight HTTP service that simulates the Meterless H-MEM API
for hierarchical memory storage and retrieval. In production, this would
connect to the real Meterless platform.

Run with: python meterless_hmem_service.py
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from cordon.memory import HMemStore


class HMemServiceHandler(BaseHTTPRequestHandler):
    """HTTP handler for Meterless H-MEM-compatible API."""
    
    # Shared memory store across requests
    store = HMemStore(path="logs/hmem-service.jsonl")
    
    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        """Send JSON response."""
        encoded = json.dumps(body, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(encoded)
    
    def do_OPTIONS(self) -> None:
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_POST(self) -> None:
        """Handle memory operations."""
        content_length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(content_length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return
        
        if self.path == "/memory/remember":
            self._handle_remember(payload)
        elif self.path == "/memory/retrieve":
            self._handle_retrieve(payload)
        elif self.path == "/health":
            self._send_json(200, {
                "status": "healthy",
                "service": "Meterless H-MEM Mock",
                "records": len(self.store.records)
            })
        else:
            self._send_json(404, {"error": "Not found"})
    
    def do_GET(self) -> None:
        """Handle health check."""
        if self.path in ["/health", "/"]:
            self._send_json(200, {
                "status": "healthy",
                "service": "Meterless H-MEM Mock Service",
                "version": "1.0.0-demo",
                "architecture": "hierarchical-memory",
                "records": len(self.store.records),
                "layers": ["executive", "tactical", "operational"],
                "description": "Hierarchical memory for multi-agent risk tracking"
            })
        else:
            self._send_json(404, {"error": "Not found"})
    
    def _handle_remember(self, payload: dict[str, Any]) -> None:
        """Store a memory record."""
        try:
            record = self.store.remember(
                content=payload["content"],
                memory_type=payload.get("memory_type", "fact"),
                layer=payload.get("layer", "operational"),
                source=payload.get("source", "unknown"),
                source_id=payload.get("source_id", "unknown"),
                run_id=payload.get("run_id", "unknown"),
                agent_id=payload.get("agent_id", "unknown"),
                expires_on=payload.get("expires_on"),
                derived_from=tuple(payload.get("derived_from", [])),
            )
            self._send_json(201, {
                "memory": {
                    "id": record.id,
                    "content": record.content,
                    "layer": record.layer,
                    "created_at": record.created_at,
                },
                "status": "remembered"
            })
        except KeyError as e:
            self._send_json(400, {"error": f"Missing required field: {e}"})
    
    def _handle_retrieve(self, payload: dict[str, Any]) -> None:
        """Retrieve memory records by query."""
        query = payload.get("query", "")
        limit = payload.get("limit", 5)
        include_expired = payload.get("include_expired", False)
        
        memories = self.store.retrieve(
            query=query,
            limit=limit,
            include_expired=include_expired
        )
        
        self._send_json(200, {
            "memories": memories,
            "query": query,
            "count": len(memories),
            "strategy": "hierarchical_semantic_search"
        })
    
    def log_message(self, format: str, *args: Any) -> None:
        """Custom logging."""
        print(f"[H-MEM] {format % args}")


def serve(host: str = "127.0.0.1", port: int = 9000) -> None:
    """Start the H-MEM service."""
    server = HTTPServer((host, port), HMemServiceHandler)
    print(f"""
========================================================================
  Meterless H-MEM Mock Service
  Hierarchical Memory for Multi-Agent Coordination
========================================================================
  Status:   Running
  Address:  http://{host}:{port}
  Storage:  logs/hmem-service.jsonl
  Records:  {len(HMemServiceHandler.store.records)}
------------------------------------------------------------------------
  API Endpoints:
    GET  /health              - Service health check
    POST /memory/remember     - Store memory record
    POST /memory/retrieve     - Query memory by content
------------------------------------------------------------------------
  Architecture: Executive -> Tactical -> Operational layers
  Use Case: Cross-run risk acceptance tracking and agent memory
========================================================================
    """)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[H-MEM] Shutting down gracefully...")
        server.shutdown()


if __name__ == "__main__":
    serve()
