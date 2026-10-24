from __future__ import annotations

from .contracts import Asset, AttackPath, Finding, FirewallRule


def attack_path(finding: Finding, assets: list[Asset], rules: list[FirewallRule],
                credentials: list[dict[str, str]]) -> AttackPath | None:
    by_id = {asset.id: asset for asset in assets}
    asset = by_id[finding.asset_id]
    nodes = [asset.id]
    evidence_ids = list(asset.evidence_ids) + list(finding.evidence_ids)
    if any(rule.source == "internet" and rule.destination == asset.id for rule in rules):
        nodes.insert(0, "internet")
    else:
        return None
    for credential in credentials:
        if credential["source_asset"] == asset.id:
            nodes.append(credential["target_asset"])
            evidence_ids.append(credential["evidence_id"])
    return AttackPath(
        finding_id=finding.id, nodes=tuple(nodes), clinical_service=by_id[nodes[-1]].clinical_service,
        impact_score=by_id[nodes[-1]].criticality, evidence_ids=tuple(evidence_ids),
    )

