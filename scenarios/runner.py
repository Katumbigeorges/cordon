from __future__ import annotations

from typing import Any

from cordon.runtime import run
from cordon.trace_validation import validate_trace

from .definitions import Scenario, get_scenario


def _asset_lanes(result: dict[str, Any]) -> dict[str, str]:
    finding_assets = {
        finding["id"]: finding["asset_id"] for finding in result["findings"]
    }
    return {
        finding_assets[decision["finding_id"]]: decision["lane"]
        for decision in result["decisions"]
        if decision["finding_id"] in finding_assets
    }


def _coverage_lanes(result: dict[str, Any]) -> dict[str, str]:
    return {gap["target"]: "Plan" for gap in result.get("coverage_gaps", [])}


def run_scenario(name: str) -> dict[str, Any]:
    scenario = get_scenario(name)
    if not scenario.implemented:
        return {
            "scenario": scenario.name,
            "status": "not_ready",
            "reason": "The current orchestration does not yet accept this scenario's input data.",
        }

    result = run(log_path=f"logs/{scenario.name.lower()}.jsonl")
    trace_errors = validate_trace(result)
    lanes = {**_asset_lanes(result), **_coverage_lanes(result)}
    failures = [
        f"{asset}: expected {expected}, got {lanes.get(asset)}"
        for asset, expected in scenario.expected_lanes.items()
        if lanes.get(asset) != expected
    ]
    failures.extend(
        f"required event missing: {event}"
        for event in scenario.required_events
        if not any(item["event"] == event for item in result["events"])
    )
    failures.extend(trace_errors)
    return {
        "scenario": scenario.name,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "run_id": result["run_id"],
        "lanes": lanes,
    }

