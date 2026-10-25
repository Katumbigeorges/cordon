from __future__ import annotations

import argparse
import json
from pathlib import Path

from cordon.runtime import run, write_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Cordon in deterministic sample mode.")
    parser.add_argument(
        "--log-path",
        default="logs/sample-run.jsonl",
        help="JSONL trace destination.",
    )
    parser.add_argument(
        "--output",
        help="Optional JSON result destination. stdout is used when omitted.",
    )
    args = parser.parse_args()

    result = run(log_path=args.log_path)
    if args.output:
        write_result(result, args.output)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

