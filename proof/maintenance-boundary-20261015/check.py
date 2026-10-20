"""Repeat the two boundary checks through showwork's project-script contract."""
from pathlib import Path
import sys
import tempfile

import pytest


root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "sdk"))
with tempfile.TemporaryDirectory(prefix="agentguard-boundary-check-") as scratch:
    result = pytest.main([
        str(root / "sdk/tests/test_background_boundary.py"),
        str(root / "sdk/tests/test_enforcement_boundary.py")
        + "::test_enforcement_map_classes_and_tests_exist",
        "-q", "-p", "no:cacheprovider", "-o", "addopts=",
        "--basetemp", str(Path(scratch) / "pytest"),
    ])
raise SystemExit(result)
