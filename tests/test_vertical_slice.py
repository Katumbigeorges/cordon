import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from cordon.pipeline import run_sample
from cordon.runtime import run
from api.app import CordonApplication
from scenarios.runner import run_scenario
from tools.zetaris import ZetarisError, run_sql
from cordon.providers import ModelResponse
from cordon.execution import ExecutionGateway
from cordon.memory import HMemStore


class VerticalSliceTests(unittest.TestCase):
    def test_sample_slice_separates_reachable_and_unreachable_log4shell(self):
        result = run_sample()
        log4shell = [item for item in result["findings"] if item.cve == "CVE-2021-44228"]
        decisions = {item.finding_id: item.lane for item in result["decisions"]}
        portal = next(item for item in log4shell if item.asset_id == "patient-portal")
        lab = next(item for item in log4shell if item.asset_id == "lab-reporting")

        self.assertEqual(decisions[portal.id], "Act now")
        self.assertEqual(decisions[lab.id], "Plan")
        self.assertTrue(portal.kev)
        self.assertIn("id", portal.conflicts)

    def test_sample_slice_emits_jsonl_trace(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "run.jsonl"
            result = run_sample(output)
            lines = output.read_text(encoding="utf-8").splitlines()

        self.assertTrue(lines)
        self.assertTrue(all(json.loads(line)["run_id"] == result["run_id"] for line in lines))
        self.assertEqual(
            {event["event"] for event in map(json.loads, lines)},
            {"findings_reconciled", "decisions_created"},
        )

    def test_runtime_returns_json_serializable_result(self):
        with TemporaryDirectory() as directory:
            result = run(log_path=Path(directory) / "run.jsonl")

        serialized = json.dumps(result)
        self.assertIn('"decisions"', serialized)
        self.assertIn('"paths"', serialized)

    def test_runtime_shows_critic_requery_and_pending_approval(self):
        with TemporaryDirectory() as directory:
            result = run(log_path=Path(directory) / "run.jsonl")

        events = result["events"]
        event_names = {event["event"] for event in events}
        self.assertIn("plan_revised", event_names)
        self.assertIn("reachability_requeried", event_names)
        gate = next(event for event in events if event["event"] == "decisions_created")
        self.assertEqual(gate["details"]["approval_state"], "pending")

    def test_runtime_uses_injected_model_provider(self):
        class TestProvider:
            def complete(self, prompt):
                return ModelResponse(
                    {"hypotheses": ["injected_hypothesis"]}, "test", "test-model"
                )

        result = run(provider=TestProvider())
        planned = next(event for event in result["events"] if event["event"] == "plan_created")
        self.assertEqual(planned["details"]["provider"], "test")
        self.assertEqual(planned["details"]["model"], "test-model")

    def test_runtime_retrieves_expiry_aware_memory_context(self):
        result = run()

        memory_event = next(event for event in result["events"] if event["event"] == "memory_retrieved")
        self.assertEqual(memory_event["details"]["expired_included_for"], "re-evaluation")
        self.assertEqual(result["memory_context"][0]["memory"]["source_id"], "ev-risk-pharmacy")

    def test_runtime_accepts_injected_memory_store(self):
        memory = HMemStore()
        result = run(memory=memory)
        self.assertTrue(memory.records)
        self.assertEqual(
            result["memory_context"][0]["memory"]["source_id"],
            "ev-risk-pharmacy",
        )

    def test_zetaris_sample_mode_uses_named_template(self):
        with patch.dict(os.environ, {"SAMPLE_MODE": "true"}, clear=False):
            self.assertEqual(run_sql("select_one"), [{"value": 1}])
            self.assertEqual(run_sql("discover_sources")[0]["name"], "sample.cmdb")

    def test_zetaris_rejects_unknown_template_before_network_call(self):
        with self.assertRaisesRegex(ZetarisError, "unknown Zetaris template"):
            run_sql("not_a_real_template")

    def test_api_exposes_board_paths_trace_and_non_executing_approval(self):
        application = CordonApplication()
        created = application.create_run({"mode": "sample"})
        run_id = created.body["run_id"]

        self.assertEqual(created.status, 201)
        self.assertTrue(created.body["actions"])
        self.assertTrue(created.body["coverage_gaps"])
        self.assertEqual(application.get_board(run_id).status, 200)
        self.assertEqual(application.get_paths(run_id).status, 200)
        self.assertEqual(application.get_trace(run_id).status, 200)
        approval = application.approve_action(run_id, "finding-001", True)
        self.assertEqual(approval.body["approval_state"], "approved")
        self.assertFalse(approval.body["executed"])

    def test_approved_action_uses_injected_executor_only_after_approval(self):
        executed: list[str] = []
        application = CordonApplication(
            execution=ExecutionGateway(
                lambda action: executed.append(action["id"]) or {"mode": "test"}
            )
        )
        created = application.create_run({"mode": "sample"})
        action_id = created.body["run_id"]
        stored = application.runs[action_id]
        action = stored["actions"][0]

        rejected = application.approve_action(action_id, action["id"], False)
        self.assertFalse(rejected.body["executed"])
        self.assertEqual(executed, [])
        approved = application.approve_action(action_id, action["id"], True)
        self.assertTrue(approved.body["executed"])
        self.assertEqual(executed, [action["id"]])

    def test_s2_and_s3_scenarios_pass(self):
        self.assertEqual(run_scenario("S2")["status"], "passed")
        self.assertEqual(run_scenario("S3")["status"], "passed")

    def test_s4_escalates_exploitation_with_pending_containment(self):
        result = run()

        escalation = next(event for event in result["events"] if event["event"] == "incident_escalated")
        action = result["actions"][0]
        self.assertEqual(action["action_type"], "containment")
        self.assertEqual(action["target"], "patient-portal")
        self.assertEqual(action["approval_state"], "pending")
        self.assertEqual(escalation["details"]["action_id"], action["id"])
        self.assertEqual(set(escalation["evidence_ids"]), {"ev-log-001", "ev-log-002"})

    def test_s4_scenario_is_ready(self):
        result = run_scenario("S4")
        self.assertEqual(result["status"], "passed")

    def test_s5_missing_telemetry_creates_a_plan_coverage_gap(self):
        result = run()

        gap = next(item for item in result["coverage_gaps"] if item["target"] == "imaging-server")
        event = next(
            item for item in result["events"]
            if item["event"] == "coverage_gap_created"
            and item["details"]["action_id"] == gap["id"]
        )
        self.assertEqual(gap["action_type"], "coverage_gap")
        self.assertEqual(gap["approval_state"], "pending")
        self.assertEqual(event["details"]["action_id"], gap["id"])
        self.assertEqual(run_scenario("S5")["status"], "passed")

    def test_s6_prompt_injection_is_ignored_as_untrusted_data(self):
        result = run()

        poisoned = result["poisoned_data"]
        event = next(item for item in result["events"] if item["event"] == "poisoned_data_ignored")
        decisions = {item["finding_id"]: item["lane"] for item in result["decisions"]}
        self.assertEqual(poisoned[0]["asset_id"], "staff-vpn")
        self.assertEqual(event["evidence_ids"], ["ev-log-003"])
        self.assertIn("patient-portal", {
            next(finding["asset_id"] for finding in result["findings"] if finding["id"] == finding_id)
            for finding_id, lane in decisions.items() if lane == "Act now"
        })
        self.assertEqual(run_scenario("S6")["status"], "passed")

    def test_s7_expired_acceptance_reopens_pharmacy_finding(self):
        result = run()

        pharmacy = next(
            finding for finding in result["findings"]
            if finding["asset_id"] == "pharmacy-api"
        )
        decision = next(
            decision for decision in result["decisions"]
            if decision["finding_id"] == pharmacy["id"]
        )
        event = next(item for item in result["events"] if item["event"] == "expired_acceptance_raised")
        self.assertEqual(decision["lane"], "Plan")
        self.assertIn("ev-risk-pharmacy", decision["evidence_ids"])
        self.assertEqual(event["details"]["status"], "reopened")
        self.assertEqual(run_scenario("S7")["status"], "passed")


if __name__ == "__main__":
    unittest.main()
