from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    expected_lanes: dict[str, str]
    required_events: tuple[str, ...] = ()
    implemented: bool = False


SCENARIOS: dict[str, Scenario] = {
    "S1": Scenario(
        "S1",
        "Trivy and Grype disagree and are reconciled into one finding.",
        {},
        ("findings_reconciled",),
    ),
    "S2": Scenario(
        "S2",
        "A KEV Log4Shell finding is reachable from the internet through the patient portal.",
        {"patient-portal": "Act now"},
        ("decisions_created",),
        implemented=True,
    ),
    "S3": Scenario(
        "S3",
        "The same KEV CVE exists on an internal lab service without an internet path.",
        {"lab-reporting": "Plan"},
        ("decisions_created",),
        implemented=True,
    ),
    "S4": Scenario(
        "S4",
        "Synthetic exploitation telemetry causes an escalation and containment draft.",
        {"patient-portal": "Act now"},
        ("incident_escalated",),
        implemented=True,
    ),
    "S5": Scenario(
        "S5",
        "Missing imaging telemetry is treated as a coverage gap, not as safety.",
        {"imaging-server": "Plan"},
        ("coverage_gap_created",),
        implemented=True,
    ),
    "S6": Scenario(
        "S6",
        "Prompt-injection text inside a log field is treated as untrusted data.",
        {},
        ("poisoned_data_ignored",),
        implemented=True,
    ),
    "S7": Scenario(
        "S7",
        "An expired pharmacy risk acceptance is raised for review again.",
        {"pharmacy-api": "Plan"},
        ("expired_acceptance_raised",),
        implemented=True,
    ),
}


def get_scenario(name: str) -> Scenario:
    try:
        return SCENARIOS[name.upper()]
    except KeyError as error:
        raise ValueError(f"unknown scenario: {name}") from error

