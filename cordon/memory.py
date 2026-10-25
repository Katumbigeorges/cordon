from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    content: str
    memory_type: str
    layer: str
    source: str
    source_id: str
    run_id: str
    agent_id: str
    expires_on: str | None = None
    derived_from: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def expired(self, today: date | None = None) -> bool:
        return bool(self.expires_on and self.expires_on < (today or date.today()).isoformat())


class HMemStore:
    """Small auditable H-MEM-compatible store for sample and local runs."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self.records: dict[str, MemoryRecord] = {}
        if self.path and self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line:
                    record = MemoryRecord(**json.loads(line))
                    self.records[record.id] = record

    def remember(
        self,
        content: str,
        *,
        memory_type: str,
        layer: str,
        source: str,
        source_id: str,
        run_id: str,
        agent_id: str,
        expires_on: str | None = None,
        derived_from: tuple[str, ...] = (),
    ) -> MemoryRecord:
        record = MemoryRecord(
            id=f"memory-{uuid4()}",
            content=content,
            memory_type=memory_type,
            layer=layer,
            source=source,
            source_id=source_id,
            run_id=run_id,
            agent_id=agent_id,
            expires_on=expires_on,
            derived_from=derived_from,
        )
        self.records[record.id] = record
        self._append(record)
        return record

    def retrieve(self, query: str, *, limit: int = 5, include_expired: bool = False) -> list[dict[str, Any]]:
        terms = set(query.lower().split())
        ranked: list[tuple[int, MemoryRecord]] = []
        for record in self.records.values():
            if not include_expired and record.expired():
                continue
            score = len(terms & set(record.content.lower().split()))
            if score:
                ranked.append((score, record))
        ranked.sort(key=lambda item: (-item[0], item[1].created_at))
        return [
            {
                "memory": asdict(record),
                "score": score,
                "retrieval_reason": "keyword_overlap",
                "strategy": "task_focused",
            }
            for score, record in ranked[:limit]
        ]

    def _append(self, record: MemoryRecord) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(record), sort_keys=True) + "\n")
