from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from .contracts import Decision, TraceEvent
from .graph import attack_path
from .reconcile import reconcile
from .sample_data import credentials_map, firewall_rules, hospital_assets, scan_findings


def run_sample(log_path: str | Path | None = None) -> dict[str, object]:
    run_id = str(uuid4())
    events: list[TraceEvent] = []
    assets = hospital_assets()
    scans = scan_findings()
    findings = reconcile(scans)
    events.append(TraceEvent(run_id, "reconcile", "reconciler", "findings_reconciled",
                             tuple(evidence for finding in findings for evidence in finding.evidence_ids),
                             details={"findings": len(findings)}))
    decisions: list[Decision] = []
    paths = []
    for finding in findings:
        path = attack_path(finding, assets, firewall_rules(), credentials_map())
        if path:
            paths.append(path)
            lane = "Act now" if finding.kev and path.impact_score >= 5 else "Plan"
            rationale = "KEV vulnerability has an internet-to-patient-critical path."
            decisions.append(Decision(finding.id, lane, rationale, path.evidence_ids))
        else:
            decisions.append(Decision(
                finding.id, "Plan" if finding.kev else "Closed",
                "No internet path was established; retain as a planned review.",
                finding.evidence_ids, ("reachability",) if finding.kev else (),
            ))
    events.append(TraceEvent(run_id, "decision-gate", "gate", "decisions_created",
                             tuple(evidence for decision in decisions for evidence in decision.evidence_ids),
                             details={"lanes": {lane: sum(d.lane == lane for d in decisions) for lane in ("Act now", "Plan", "Closed")}}))
    result = {
        "run_id": run_id,
        "findings": findings,
        "paths": paths,
        "decisions": decisions,
        "events": events,
    }
    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as stream:
            for event in events:
                stream.write(json.dumps(event.__dict__, sort_keys=True) + "\n")
    return result

