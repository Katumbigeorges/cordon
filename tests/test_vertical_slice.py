import json
import unittest
from pathlib import Path

from cordon.pipeline import run_sample


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
        from tempfile import TemporaryDirectory

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


if __name__ == "__main__":
    unittest.main()
