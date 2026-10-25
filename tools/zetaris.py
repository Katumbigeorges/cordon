from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4


class ZetarisError(RuntimeError):
    """Raised when a Zetaris query cannot be completed."""


_TEMPLATE_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_TEMPLATE_ROOT = Path(__file__).resolve().parent.parent / "zetaris" / "templates"


def request_id() -> str:
    return str(uuid4())


def _load_environment() -> dict[str, str]:
    values: dict[str, str] = {}
    for filename in (".env.local", ".env"):
        path = Path(filename)
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            values.setdefault(name.strip(), value.strip().strip('"').strip("'"))
    return values


def _setting(name: str) -> str:
    return os.getenv(name) or _load_environment().get(name, "")


def _template_sql(template: str, params: dict[str, Any]) -> str:
    if not _TEMPLATE_NAME.fullmatch(template):
        raise ZetarisError(f"invalid template name: {template!r}")
    path = _TEMPLATE_ROOT / f"{template}.sql"
    if not path.is_file():
        raise ZetarisError(f"unknown Zetaris template: {template!r}")
    sql = path.read_text(encoding="utf-8").strip()
    unresolved = re.findall(r":([a-zA-Z_][a-zA-Z0-9_]*)", sql)
    missing = [name for name in unresolved if name not in params]
    if missing:
        raise ZetarisError(f"missing parameters for {template!r}: {', '.join(missing)}")
    for name in unresolved:
        sql = sql.replace(f":{name}", _quote_sql_value(params[name]))
    return sql


def _quote_sql_value(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if not isinstance(value, str):
        raise ZetarisError("SQL parameters must be strings, numbers, or booleans")
    return "'" + value.replace("'", "''") + "'"


def _sample_result(template: str, params: dict[str, Any]) -> Any:
    if template == "select_one":
        return [{"value": 1}]
    if template == "discover_sources":
        return [{"name": "sample.cmdb", "rows": 28, "freshness": "sample"}]
    if template == "kev_by_cve":
        cve = params.get("cve")
        return [{"cve": cve, "kev": cve == "CVE-2021-44228"}]
    if template == "epss_by_cve":
        return [{"cve": params.get("cve"), "epss": 0.98, "epss_percentile": 0.999}]
    raise ZetarisError(f"sample fixture not configured for template {template!r}")


def _request_payload(sql: str, query_id: str, limit: int) -> dict[str, Any]:
    return {"queryId": query_id, "sql": sql, "source": "SqlEditor", "limit": limit}


def _live_query(
    payload: dict[str, Any],
    *,
    base_url: str,
    api_key: str,
    org_id: str,
    timeout: float,
    opener: Callable[..., Any] = urlopen,
) -> Any:
    url = base_url.rstrip("/") + "/sql-editor/sqls/run"
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Org-ID": org_id,
            "X-Request-ID": request_id(),
        },
        method="POST",
    )
    try:
        with opener(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise ZetarisError(f"Zetaris returned HTTP {error.code}") from error
    except (URLError, TimeoutError, ValueError) as error:
        raise ZetarisError("Zetaris request failed") from error


def run_sql(
    template: str,
    params: dict[str, Any] | None = None,
    *,
    timeout: float = 10.0,
    query_id: str | None = None,
    opener: Callable[..., Any] = urlopen,
) -> Any:
    """Run a named Zetaris query in sample mode or through the REST API."""
    params = params or {}
    sql = _template_sql(template, params)
    if _setting("SAMPLE_MODE").lower() == "true":
        return _sample_result(template, params)

    base_url = _setting("ZETARIS_REST_URL") or _setting("ZETARIS_BASE_URL")
    api_key = _setting("ZETARIS_API_KEY")
    org_id = _setting("ZETARIS_ORG_ID")
    missing = [
        name for name, value in (
            ("ZETARIS_REST_URL", base_url),
            ("ZETARIS_API_KEY", api_key),
            ("ZETARIS_ORG_ID", org_id),
        ) if not value
    ]
    if missing:
        raise ZetarisError(f"missing Zetaris configuration: {', '.join(missing)}")
    return _live_query(
        _request_payload(sql, query_id or template, int(_setting("ZETARIS_QUERY_LIMIT") or "1000")),
        base_url=base_url,
        api_key=api_key,
        org_id=org_id,
        timeout=timeout,
        opener=opener,
    )
