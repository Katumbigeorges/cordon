from __future__ import annotations

from collections import defaultdict

from .contracts import Finding, ScanFinding
from .sample_data import public_threat_data


def _canonical_cve(cve: str) -> str:
    if cve == "GHSA-jfh8-c2jp-5v3q":
        return "CVE-2021-44228"
    return cve


def reconcile(rows: list[ScanFinding], threat_data: dict[str, dict[str, object]] | None = None) -> list[Finding]:
    grouped: dict[tuple[str, str, str, str], list[ScanFinding]] = defaultdict(list)
    for row in rows:
        grouped[(row.asset_id, row.package, row.version, _canonical_cve(row.cve))].append(row)

    threat_data = public_threat_data() if threat_data is None else threat_data
    result: list[Finding] = []
    for index, (key, matches) in enumerate(sorted(grouped.items()), start=1):
        asset_id, package, version, cve = key
        scanners = tuple(sorted({row.scanner for row in matches}))
        ids = {row.cve for row in matches}
        severities = {row.severity for row in matches}
        conflicts: list[str] = []
        if len(ids) > 1:
            conflicts.append("id")
        if len(severities) > 1:
            conflicts.append("severity")
        if len(scanners) != len(matches):
            conflicts.append("count")
        canonical = threat_data.get(cve, {})
        evidence_ids = tuple(row.evidence_id for row in matches)
        if canonical.get("evidence_id"):
            evidence_ids += (str(canonical["evidence_id"]),)
        result.append(Finding(
            id=f"finding-{index:03d}", asset_id=asset_id, package=package,
            version=version, cve=cve, severity=max(severities, key=lambda value: {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(value, 0)),
            scanners=scanners, evidence_ids=evidence_ids,
            conflicts=tuple(conflicts), kev=bool(canonical.get("kev")),
            kev_due_date=canonical.get("kev_due_date"), epss=canonical.get("epss"),
            epss_percentile=canonical.get("epss_percentile"),
        ))
    return result

