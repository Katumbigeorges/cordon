from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ExecutionResult:
    action_id: str
    approval_state: str
    executed: bool
    reason: str
    details: dict[str, Any]


class ExecutionGateway:
    """Approval boundary for action execution; no handler means dry-run mode."""

    def __init__(self, handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> None:
        self.handler = handler

    def execute(self, action: dict[str, Any], approval_state: str) -> ExecutionResult:
        action_id = action["id"]
        if approval_state != "approved":
            return ExecutionResult(
                action_id, approval_state, False, "human approval is required", {}
            )
        if self.handler is None:
            return ExecutionResult(
                action_id, approval_state, False, "no execution handler configured; dry-run only", {}
            )
        details = self.handler(action)
        return ExecutionResult(action_id, approval_state, True, "approved handler completed", details)


class HttpExecutionGateway:
    """HTTP client for the live, record-only execution service."""

    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def execute(self, action: dict[str, Any], approval_state: str) -> ExecutionResult:
        request = Request(
            f"{self.base_url}/execute",
            data=json.dumps({"action": action, "approval_state": approval_state}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        return ExecutionResult(
            body["action_id"], body["approval_state"], body["executed"], body["reason"], body["details"]
        )
