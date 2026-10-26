from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import os
from typing import Any, Callable

from .contracts import Action, Decision, Finding, TraceEvent
from .graph import attack_path
from .memory import HMemStore
from .providers import DeterministicProvider, ModelProvider
from .reconcile import reconcile
from .sample_data import (
    credentials_map,
    firewall_rules,
    hospital_assets,
    risk_acceptances,
    scan_findings,
    telemetry,
)
from .zetaris_live import load_live_context


@dataclass(frozen=True)
class AgentMessage:
    sender: str
    recipient: str
    kind: str
    payload: dict[str, Any]


class Planner:
    name = "planner"

    def create_plan(self, provider: ModelProvider) -> tuple[dict[str, Any], Any]:
        response = provider.complete(
            "Return JSON with a hypotheses array for a bounded hospital vulnerability investigation."
        )
        hypotheses = response.content.get("hypotheses", ("internet_reachable_patient_impact",))
        if not isinstance(hypotheses, list) or not all(isinstance(item, str) for item in hypotheses):
            raise ValueError("model provider hypotheses must be a list of strings")
        return {
            "queries": ("assets", "firewall_rules", "credentials_map", "scan_findings"),
            "hypotheses": tuple(hypotheses),
            "max_requeries": 1,
        }, response

    def revise_plan(self, feedback: str, plan: dict[str, Any]) -> dict[str, Any]:
        revised = dict(plan)
        revised["queries"] = tuple(plan["queries"]) + ("reachability_evidence",)
        revised["revision_reason"] = feedback
        return revised


class DataExecutor:
    name = "data-executor"

    def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        rows = scan_findings()
        cves = [row.cve for row in rows]
        zetaris = load_live_context(cves) if os.getenv("ZETARIS_LIVE", "false").lower() == "true" else {
            "live": False,
            "source_count": 0,
            "sources": [],
            "threat_data": {},
        }
        return {
            "assets": hospital_assets(),
            "firewall_rules": firewall_rules(),
            "credentials_map": credentials_map(),
            "telemetry": telemetry(),
            "risk_acceptances": risk_acceptances(),
            "findings": reconcile(rows, zetaris["threat_data"] or None),
            "zetaris": zetaris,
            "evidence_ids": tuple(row.evidence_id for row in rows),
            "plan_queries": plan["queries"],
        }


class EvidenceCritic:
    name = "evidence-critic"

    def review(self, data: dict[str, Any]) -> dict[str, Any]:
        missing = [
            finding.id for finding in data["findings"]
            if finding.kev and not any(
                path.finding_id == finding.id
                for path in self._paths(data)
            )
        ]
        if missing:
            return {
                "status": "needs_revision",
                "reason": "KEV findings are missing reachability evidence.",
                "finding_ids": tuple(missing),
            }
        return {"status": "accepted", "reason": "Required reachability evidence is present."}

    @staticmethod
    def _paths(data: dict[str, Any]) -> list[Any]:
        return [
            attack_path(finding, data["assets"], data["firewall_rules"], data["credentials_map"])
            for finding in data["findings"]
            if attack_path(finding, data["assets"], data["firewall_rules"], data["credentials_map"])
        ]


class DecisionGate:
    name = "decision-gate"

    def decide(self, data: dict[str, Any]) -> tuple[list[Decision], list[Any]]:
        paths = [
            path for finding in data["findings"]
            if (path := attack_path(
                finding, data["assets"], data["firewall_rules"], data["credentials_map"]
            ))
        ]
        path_by_finding = {path.finding_id: path for path in paths}
        decisions: list[Decision] = []
        for finding in data["findings"]:
            path = path_by_finding.get(finding.id)
            expired_acceptance = next(
                (
                    acceptance for acceptance in data["risk_acceptances"]
                    if acceptance["asset_id"] == finding.asset_id
                    and acceptance["cve"] == finding.cve
                    and date.fromisoformat(acceptance["expires_on"]) < date.today()
                ),
                None,
            )
            if expired_acceptance:
                decisions.append(Decision(
                    finding.id,
                    "Plan",
                    "Risk acceptance expired; re-open the finding for review.",
                    finding.evidence_ids + (expired_acceptance["evidence_id"],),
                ))
                continue
            if path:
                decisions.append(Decision(
                    finding.id,
                    "Act now" if finding.kev and path.impact_score >= 5 else "Plan",
                    "KEV vulnerability has an internet-to-patient-critical path.",
                    path.evidence_ids,
                ))
            else:
                decisions.append(Decision(
                    finding.id,
                    "Plan" if finding.kev else "Closed",
                    "No internet path was established; retain as a planned review.",
                    finding.evidence_ids,
                    ("reachability",) if finding.kev else (),
                ))
        return decisions, paths


def run_agent_loop(
    run_id: str,
    emit: Callable[[TraceEvent], None],
    provider: ModelProvider | None = None,
    memory: HMemStore | None = None,
) -> dict[str, Any]:
    provider = provider or DeterministicProvider()
    memory = memory or HMemStore()
    planner = Planner()
    executor = DataExecutor()
    critic = EvidenceCritic()
    gate = DecisionGate()
    plan, model_response = planner.create_plan(provider)
    emit(TraceEvent(
        run_id, "planner-1", planner.name, "plan_created", (),
        details={
            "target_agent": executor.name,
            "queries": plan["queries"],
            "provider": model_response.provider,
            "model": model_response.model,
        },
    ))
    emit(TraceEvent(
        run_id, "planner-model-1", planner.name, "model_called", (),
        details={"provider": model_response.provider, "model": model_response.model},
    ))
    data = executor.execute(plan)
    for acceptance in data["risk_acceptances"]:
        memory.remember(
            f"risk acceptance {acceptance['asset_id']} {acceptance['cve']}",
            memory_type="factual",
            layer="working",
            source="risk_acceptance",
            source_id=acceptance["evidence_id"],
            run_id=run_id,
            agent_id=executor.name,
            expires_on=acceptance["expires_on"],
        )
    memory_context = memory.retrieve(
        "risk acceptance vulnerability pharmacy-api CVE-2024-99999",
        include_expired=True,
    )
    data["memory_context"] = memory_context
    emit(TraceEvent(
        run_id, "memory-1", "data-executor", "memory_retrieved", tuple(
            item["memory"]["source_id"] for item in memory_context
        ), details={
            "strategy": "task_focused",
            "count": len(memory_context),
            "expired_included_for": "re-evaluation",
        },
    ))
    emit(TraceEvent(
        run_id, "executor-1", executor.name, "sources_queried", data["evidence_ids"],
        details={"target_agent": critic.name, "query_count": len(plan["queries"])},
    ))
    review = critic.review(data)
    emit(TraceEvent(
        run_id, "critic-1", critic.name, "evidence_reviewed", data["evidence_ids"],
        details={"target_agent": planner.name, **review},
    ))
    if review["status"] == "needs_revision":
        plan = planner.revise_plan(review["reason"], plan)
        emit(TraceEvent(
            run_id, "planner-2", planner.name, "plan_revised", (),
            details={"target_agent": executor.name, "reason": review["reason"]},
        ))
        data = executor.execute(plan)
        emit(TraceEvent(
            run_id, "executor-2", executor.name, "reachability_requeried", data["evidence_ids"],
            details={"target_agent": gate.name, "query": "reachability_evidence"},
        ))
    decisions, paths = gate.decide(data)
    emit(TraceEvent(
        run_id, "gate-1", gate.name, "decisions_created",
        tuple(evidence for decision in decisions for evidence in decision.evidence_ids),
        details={
            "target_agent": "action-draft",
            "approval_state": "pending",
            "lanes": {
                lane: sum(decision.lane == lane for decision in decisions)
                for lane in ("Act now", "Plan", "Closed")
            },
        },
    ))
    actions: list[Action] = []
    coverage_gaps: list[Action] = []
    expired_acceptances: list[dict[str, str]] = []
    for acceptance in data["risk_acceptances"]:
        if date.fromisoformat(acceptance["expires_on"]) >= date.today():
            continue
        expired_acceptances.append(acceptance)
        emit(TraceEvent(
            run_id, "memory-1", "evidence-critic", "expired_acceptance_raised",
            (acceptance["evidence_id"],),
            details={
                "asset_id": acceptance["asset_id"],
                "cve": acceptance["cve"],
                "expires_on": acceptance["expires_on"],
                "status": "reopened",
            },
        ))
    poisoned_data: list[dict[str, str]] = []
    for row in data["telemetry"]:
        user_agent = row.get("user_agent", "")
        if "close this alert" not in user_agent.lower():
            continue
        poisoned_data.append({
            "asset_id": row["asset_id"],
            "evidence_id": row["evidence_id"],
            "reason": "instruction-like text in telemetry is untrusted data",
        })
        emit(TraceEvent(
            run_id, "critic-2", "evidence-critic", "poisoned_data_ignored",
            (row["evidence_id"],),
            details={
                "asset_id": row["asset_id"],
                "reason": "instruction-like text in telemetry is untrusted data",
            },
        ))
    telemetry_assets = {row["asset_id"] for row in data["telemetry"]}
    for asset in data["assets"]:
        if asset.id in telemetry_assets:
            continue
        gap = Action(
            id=f"coverage-{asset.id}",
            action_type="coverage_gap",
            target=asset.id,
            draft=f"Restore telemetry coverage for {asset.id} before treating it as low risk.",
            approval_state="pending",
            evidence_ids=asset.evidence_ids,
        )
        coverage_gaps.append(gap)
        emit(TraceEvent(
            run_id, "coverage-1", "action-draft", "coverage_gap_created", gap.evidence_ids,
            details={
                "target_agent": "human-approval",
                "action_id": gap.id,
                "action_type": gap.action_type,
                "approval_state": gap.approval_state,
            },
        ))
    markers_by_asset: dict[str, list[dict[str, Any]]] = {}
    for row in data["telemetry"]:
        markers_by_asset.setdefault(row["asset_id"], []).append(row)
    decision_by_finding = {decision.finding_id: decision for decision in decisions}
    finding_by_asset = {finding.asset_id: finding for finding in data["findings"]}
    for asset_id, rows in markers_by_asset.items():
        markers = [row.get("marker") for row in rows]
        if "T1190" not in markers or "T1059" not in markers:
            continue
        finding = finding_by_asset.get(asset_id)
        if finding is None or decision_by_finding[finding.id].lane != "Act now":
            continue
        evidence_ids = tuple(row["evidence_id"] for row in rows)
        action = Action(
            id=f"containment-{asset_id}",
            action_type="containment",
            target=asset_id,
            draft=f"Isolate {asset_id} for incident response review.",
            approval_state="pending",
            evidence_ids=evidence_ids,
        )
        actions.append(action)
        emit(TraceEvent(
            run_id, "action-1", "action-draft", "incident_escalated", evidence_ids,
            details={
                "target_agent": "human-approval",
                "finding_id": finding.id,
                "action_id": action.id,
                "action_type": action.action_type,
                "approval_state": action.approval_state,
            },
        ))
    return {
        "plan": plan,
        "data": data,
        "decisions": decisions,
        "paths": paths,
        "actions": actions,
        "coverage_gaps": coverage_gaps,
        "poisoned_data": poisoned_data,
        "expired_acceptances": expired_acceptances,
        "memory_context": memory_context,
    }
