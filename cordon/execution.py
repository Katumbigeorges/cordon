from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


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
