from __future__ import annotations

from typing import Any


KNOWN_ROLES = {"planner", "data-executor", "evidence-critic", "decision-gate"}


def validate_trace(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    run_id = result.get("run_id")
    events = result.get("events", [])
    roles = {event.get("actor") for event in events}
    if not run_id:
        errors.append("run_id is missing")
    if len(roles & KNOWN_ROLES) < 3:
        errors.append("trace does not show enough interacting agent roles")
    for event in events:
        if event.get("run_id") != run_id:
            errors.append(f"event {event.get('step_id')} has a different run_id")
        if not event.get("actor") or not event.get("event"):
            errors.append("trace event is missing actor or event")
    requery = [event for event in events if event.get("event") == "reachability_requeried"]
    critic = [event for event in events if event.get("actor") == "evidence-critic"]
    if requery and not any(event.get("details", {}).get("status") == "needs_revision" for event in critic):
        errors.append("re-query has no Critic needs_revision event")
    gates = [event for event in events if event.get("event") == "decisions_created"]
    if not gates or gates[-1].get("details", {}).get("approval_state") != "pending":
        errors.append("decision gate did not preserve pending approval")
    return errors

