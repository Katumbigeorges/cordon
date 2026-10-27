from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import os

from cordon.execution import ExecutionGateway, HttpExecutionGateway
from cordon.runtime import run


@dataclass
class ApiResponse:
    status: int
    body: dict[str, Any]


class CordonApplication:
    """Small API-first application used by the HTTP server and tests."""

    def __init__(self, execution: ExecutionGateway | None = None) -> None:
        self.runs: dict[str, dict[str, Any]] = {}
        self.approvals: dict[str, str] = {}
        self.execution = execution or (
            HttpExecutionGateway(os.environ["EXECUTION_SERVICE_URL"])
            if os.getenv("EXECUTION_SERVICE_URL")
            else ExecutionGateway()
        )

    def create_run(self, payload: dict[str, Any] | None = None) -> ApiResponse:
        payload = payload or {}
        if payload.get("mode", "sample") != "sample":
            return ApiResponse(400, {"error": "only sample mode is available"})
        try:
            result = run(scenario=payload.get("scenario", "composite-sample"))
            self.runs[result["run_id"]] = result
            return ApiResponse(201, self._public_result(result))
        except Exception as e:
            import traceback
            error_details = {
                "error": "Analysis failed",
                "message": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
            print(f"Error in create_run: {error_details}")
            return ApiResponse(500, error_details)

    def get_board(self, run_id: str) -> ApiResponse:
        result = self.runs.get(run_id)
        if result is None:
            return ApiResponse(404, {"error": "run not found"})
        lanes = {"Act now": [], "Plan": [], "Closed": []}
        for decision in result["decisions"]:
            lanes[decision["lane"]].append(decision)
        return ApiResponse(200, {"run_id": run_id, "lanes": lanes})

    def get_paths(self, run_id: str) -> ApiResponse:
        result = self.runs.get(run_id)
        if result is None:
            return ApiResponse(404, {"error": "run not found"})
        return ApiResponse(200, {"run_id": run_id, "paths": result["paths"]})

    def get_trace(self, run_id: str) -> ApiResponse:
        result = self.runs.get(run_id)
        if result is None:
            return ApiResponse(404, {"error": "run not found"})
        return ApiResponse(200, {"run_id": run_id, "events": result["events"]})

    def approve_action(self, run_id: str, action_id: str, approved: bool) -> ApiResponse:
        if run_id not in self.runs:
            return ApiResponse(404, {"error": "run not found"})
        state = "approved" if approved else "rejected"
        approval_id = str(uuid4())
        self.approvals[approval_id] = state
        action = next(
            (
                item for item in (
                    *self.runs[run_id].get("actions", []),
                    *self.runs[run_id].get("coverage_gaps", []),
                )
                if item["id"] == action_id
            ),
            None,
        )
        execution = (
            self.execution.execute(action, state)
            if action is not None
            else None
        )
        if action is not None:
            action["approval_state"] = state
            action["execution_state"] = "executed" if execution and execution.executed else "recorded"
        self.runs[run_id]["events"].append({
            "run_id": run_id,
            "step_id": f"approval-{approval_id}",
            "actor": "human-approval",
            "event": "action_approved" if approved else "action_rejected",
            "evidence_ids": action.get("evidence_ids", []) if action else [],
            "status": "ok",
            "details": {
                "action_id": action_id,
                "approval_state": state,
                "executed": execution.executed if execution else False,
            },
        })
        return ApiResponse(200, {
            "run_id": run_id,
            "action_id": action_id,
            "approval_id": approval_id,
            "approval_state": state,
            "executed": execution.executed if execution else False,
            "execution_reason": execution.reason if execution else "action not found",
            "execution_details": execution.details if execution else {},
        })

    @staticmethod
    def _public_result(result: dict[str, Any]) -> dict[str, Any]:
        return {
            "run_id": result["run_id"],
            "context": result["context"],
            "findings": result["findings"],
            "paths": result["paths"],
            "decisions": result["decisions"],
            "actions": result["actions"],
            "coverage_gaps": result["coverage_gaps"],
            "expired_acceptances": result["expired_acceptances"],
            "approval_state": "pending",
        }

