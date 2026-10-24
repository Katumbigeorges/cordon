from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    kind: str
    value: dict[str, Any]


@dataclass(frozen=True)
class Asset:
    id: str
    name: str
    clinical_service: str
    criticality: int
    internet_facing: bool = False
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class FirewallRule:
    source: str
    destination: str
    protocol: str
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScanFinding:
    id: str
    scanner: str
    asset_id: str
    package: str
    version: str
    cve: str
    severity: str
    evidence_id: str


@dataclass(frozen=True)
class Finding:
    id: str
    asset_id: str
    package: str
    version: str
    cve: str
    severity: str
    scanners: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    conflicts: tuple[str, ...] = ()
    kev: bool = False
    kev_due_date: str | None = None
    epss: float | None = None
    epss_percentile: float | None = None


@dataclass(frozen=True)
class PathEdge:
    source: str
    destination: str
    edge_type: str
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AttackPath:
    finding_id: str
    nodes: tuple[str, ...]
    clinical_service: str
    impact_score: int
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class Decision:
    finding_id: str
    lane: str
    rationale: str
    evidence_ids: tuple[str, ...]
    missing_evidence: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class TraceEvent:
    run_id: str
    step_id: str
    actor: str
    event: str
    evidence_ids: tuple[str, ...]
    status: str = "ok"
    details: dict[str, Any] = field(default_factory=dict)
