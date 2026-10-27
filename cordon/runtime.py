from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .agents import run_agent_loop
from .contracts import TraceEvent
from .memory import HMemStore, HttpHMemStore
from .providers import ModelProvider, provider_from_environment


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def run(
    *,
    log_path: str | Path = "logs/sample-run.jsonl",
    provider: ModelProvider | None = None,
    memory: HMemStore | None = None,
    scenario: str = "composite-sample",
) -> dict[str, Any]:
    """Run the bounded sample multi-agent loop."""
    events: list[TraceEvent] = []
    run_id = str(uuid4())
    selected_memory = memory or (
        HttpHMemStore(os.environ["HMEM_SERVICE_URL"])
        if os.getenv("HMEM_SERVICE_URL")
        else HMemStore()
    )
    result = run_agent_loop(
        run_id,
        events.append,
        provider or provider_from_environment(),
        selected_memory,
    )
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for event in events:
            stream.write(json.dumps(_jsonable(event), sort_keys=True) + "\n")
    zetaris = result["data"]["zetaris"]
    return _jsonable({
        "run_id": run_id,
        "context": {
            "scenario": scenario,
            "mode": (
                "live-zetaris"
                if zetaris["live"] and zetaris.get("threat_data_via_zetaris")
                else "live-zetaris-partial"
                if zetaris["live"]
                else "sample"
            ),
            "scope": "28 synthetic hospital assets, 3 canonical findings, network paths, telemetry, and risk acceptances",
            "risk_focus": "patient-impacting exposure, exploitation signals, missing telemetry, poisoned logs, and expired exceptions",
            "data_sources": [
                "synthetic asset inventory",
                "synthetic firewall and credential edges",
                "synthetic Trivy/Grype findings",
                "synthetic telemetry",
                "synthetic risk acceptances",
            ],
            "live_zetaris": zetaris["live"] and zetaris.get("threat_data_via_zetaris", False),
            "live_zetaris_note": (
                f"Live Zetaris source discovery returned {zetaris['source_count']} rows and supplied KEV/EPSS enrichment."
                if zetaris["live"] and zetaris.get("threat_data_via_zetaris")
                else (
                    f"Zetaris source discovery is live, but threat enrichment is unavailable: {zetaris['threat_error']}"
                    if zetaris["live"] and zetaris.get("threat_error")
                    else "This run uses deterministic fixtures; set ZETARIS_LIVE=true to query Zetaris source discovery."
                )
            ),
            "zetaris_source_count": zetaris["source_count"],
            "hospital_data_via_zetaris": zetaris.get("hospital_data_via_zetaris", False),
            "synthetic_hospital_inputs": True,
        },
        "findings": result["data"]["findings"],
        "paths": result["paths"],
        "decisions": result["decisions"],
        "actions": result["actions"],
        "coverage_gaps": result["coverage_gaps"],
        "poisoned_data": result["poisoned_data"],
        "expired_acceptances": result["expired_acceptances"],
        "memory_context": result["memory_context"],
        "events": events,
    })


def write_result(result: dict[str, Any], output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
