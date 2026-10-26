from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.zetaris import ZetarisError, run_sql


REQUIRED = ("ZETARIS_REST_URL", "ZETARIS_API_KEY", "ZETARIS_ORG_ID", "ZETARIS_USER_AGENT")


def load_env_names() -> dict[str, str]:
    values: dict[str, str] = {}
    path = Path(".env")
    if path.exists():
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                values.setdefault(name.strip(), value.strip().strip('"').strip("'"))
    return values


def main() -> int:
    file_values = load_env_names()
    missing = [name for name in REQUIRED if not (os.getenv(name) or file_values.get(name))]
    if missing:
        print(f"FAIL configuration missing: {', '.join(missing)}")
        return 1
    try:
        select_one = run_sql("select_one")
        sources = run_sql("discover_sources")
        kev = run_sql("kev_by_cve", {"cve": "CVE-2021-44228"})
        epss = run_sql("epss_by_cve", {"cve": "CVE-2021-44228"})
    except ZetarisError as error:
        print(f"FAIL Zetaris read-only preflight: {error}")
        return 1
    print("PASS configuration: .env")
    print(f"PASS SELECT 1: {select_one}")
    print(f"PASS source discovery: {len(sources)} source rows")
    print(f"PASS KEV lookup: {len(kev)} rows")
    print(f"PASS EPSS lookup: {len(epss)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
