from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from .agents import run_agent_loop
from .contracts import TraceEvent
from .memory import HMemStore
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
) -> dict[str, Any]:
    """Run the bounded sample multi-agent loop."""
    events: list[TraceEvent] = []
    run_id = str(uuid4())
    result = run_agent_loop(
        run_id,
        events.append,
        provider or provider_from_environment(),
        memory,
    )
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for event in events:
            stream.write(json.dumps(_jsonable(event), sort_keys=True) + "\n")
    return _jsonable({
        "run_id": run_id,
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
