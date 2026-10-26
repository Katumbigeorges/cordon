"""Run the existing suite offline, keeping generated traces outside the checkout."""
from __future__ import annotations

import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root))
    original_directory = Path.cwd()
    environment = dict(os.environ)
    environment.pop("MODEL_PROVIDER_URL", None)
    environment.pop("MODEL_PROVIDER_API_KEY", None)
    environment["SAMPLE_MODE"] = "true"
    with TemporaryDirectory(prefix="cordon-check-") as directory:
        try:
            os.chdir(directory)
            with patch.dict(os.environ, environment, clear=True), patch(
                "socket.socket.connect", side_effect=RuntimeError("Network disabled in offline checks")
            ), patch(
                "socket.socket.connect_ex", side_effect=RuntimeError("Network disabled in offline checks")
            ):
                suite = unittest.defaultTestLoader.discover(str(root / "tests"))
                if suite.countTestCases() == 0:
                    print("FAIL: no tests discovered", file=sys.stderr)
                    return 1
                result = unittest.TextTestRunner(verbosity=2).run(suite)
                return 0 if result.wasSuccessful() else 1
        finally:
            # Windows cannot remove a directory while it is the process cwd.
            os.chdir(original_directory)


if __name__ == "__main__":
    raise SystemExit(main())
