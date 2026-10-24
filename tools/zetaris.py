from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4


class ZetarisError(RuntimeError):
    """Raised when a Zetaris query cannot be completed."""


def run_sql(template: str, params: dict[str, Any] | None = None, *, timeout: float = 10.0) -> Any:
    """Run a named query in sample mode or through Zetaris REST.

    Live SQL templates are intentionally not accepted from callers. The live
    adapter is added after the source registration contracts are verified.
    """
    params = params or {}
    if os.getenv("SAMPLE_MODE", "").lower() == "true":
        fixture = Path("data") / "sample" / f"{template}.json"
        if not fixture.exists():
            raise ZetarisError(f"sample fixture not found for template {template!r}")
        return json.loads(fixture.read_text(encoding="utf-8"))
    raise ZetarisError(
        f"live template {template!r} is not configured; use SAMPLE_MODE=true "
        "until Zetaris source registration is complete"
    )


def request_id() -> str:
    return str(uuid4())

