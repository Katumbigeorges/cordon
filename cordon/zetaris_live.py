from __future__ import annotations

from typing import Any

from tools.zetaris import run_sql


def _rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        if all(isinstance(row, dict) for row in payload):
            return payload
        return []
    if isinstance(payload, dict):
        headers = payload.get("headers")
        values = payload.get("data")
        if isinstance(headers, list) and isinstance(values, list):
            return [
                dict(zip(headers, row))
                for row in values
                if isinstance(row, list)
            ]
        for key in ("data", "rows", "results", "result"):
            if key in payload:
                return _rows(payload[key])
    return []


def load_live_context(cves: list[str]) -> dict[str, Any]:
    """Load scenario threat enrichment through named Zetaris templates."""
    sources = load_live_sources()["sources"]
    threat_data: dict[str, dict[str, Any]] = {}
    for cve in sorted(set(cves)):
        kev_rows = _rows(run_sql("kev_by_cve", {"cve": cve}))
        epss_rows = _rows(run_sql("epss_by_cve", {"cve": cve}))
        kev = kev_rows[0] if kev_rows else {}
        epss = epss_rows[0] if epss_rows else {}
        threat_data[cve] = {
            "kev": bool(kev.get("kev", False)),
            "kev_due_date": kev.get("kev_due_date"),
            "epss": epss.get("epss"),
            "epss_percentile": epss.get("epss_percentile"),
            "evidence_id": f"ev-zetaris-threat-{cve.lower()}",
        }
    return {
        "live": True,
        "source_count": len(sources),
        "sources": sources,
        "threat_data": threat_data,
    }


def load_live_sources() -> dict[str, Any]:
    sources = _rows(run_sql("discover_sources"))
    return {"live": True, "source_count": len(sources), "sources": sources}


