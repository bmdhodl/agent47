"""Verify the retained proof bytes and the two named installed test groups."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def main() -> None:
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
    cases = sorted((
        "test_langchain_dispatch_propagates_budget_stop",
        "test_langgraph_node_budget_stops_the_graph",
        "test_otel_sink_exports_guard_spans",
    ))
    for profile, python in (("floor", "3.10.11"), ("current", "3.13.2")):
        receipt = json.loads((root / f"{profile}-receipt.json").read_text(encoding="utf-8"))
        assert receipt["installed"]["python"] == python
        assert receipt["counts"] == {"tests": 3, "errors": 0, "failures": 0, "skipped": 0}
        assert receipt["installed"]["installed_files_equal_wheel"] == 51
        assert receipt["installed"]["mandatory_runtime_dependencies"] == 0
        assert receipt["installed"]["import_inside_venv"]
        assert receipt["installed"]["installed_metadata_equal_wheel"]
        assert receipt["hash_enforced_unmodified_locks"] and receipt["no_repository_conftest"]
        assert receipt["wheel_sha256"] == manifest[receipt["wheel"]]
        suites = ET.parse(root / f"{profile}-tests.xml").getroot().findall("testsuite")
        observed = sorted(case.attrib["name"] for suite in suites for case in suite.findall("testcase"))
        assert observed == cases
        counts = {key: sum(int(s.attrib.get(key, "0")) for s in suites)
                  for key in ("tests", "errors", "failures", "skipped")}
        assert counts == receipt["counts"]
        tests = gzip.decompress((root / f"{profile}-tests.log.gz").read_bytes()).decode("utf-8")
        assert "3 passed" in tests and "warnings summary" not in tests
        pip_check = gzip.decompress((root / f"{profile}-pip-check.log.gz").read_bytes()).decode("utf-8")
        assert "No broken requirements found." in pip_check
        commands = json.loads((root / f"{profile}-commands.json").read_text(encoding="utf-8"))
        assert commands and all(command["exit"] == 0 for command in commands)
    failure = gzip.decompress((root / "current-lock-windows-failure.log.gz").read_bytes()).decode("utf-8")
    assert "pywin32>=311" in failure and "ERROR: In --require-hashes mode" in failure
    checks = json.loads((root / "checks.json").read_text(encoding="utf-8"))
    assert len(checks) == 8 and all(check["exit"] == 0 for check in checks)
    source_xml = gzip.decompress((root / "source-suite.xml.gz").read_bytes())
    suites = ET.fromstring(source_xml).findall("testsuite")
    counts = {key: sum(int(s.attrib.get(key, "0")) for s in suites)
              for key in ("tests", "errors", "failures", "skipped")}
    assert counts == {"tests": 1587, "errors": 0, "failures": 0, "skipped": 3}
    source_log = gzip.decompress((root / "source-suite.log.gz").read_bytes()).decode("utf-8")
    assert "1584 passed, 3 skipped" in source_log and "warnings summary" not in source_log
    assert "Total coverage: 92.56%" in source_log
    print(f"{len(manifest)} retained artifact hashes verified; six installed framework cases passed; original Windows lock failure retained.")


if __name__ == "__main__":
    main()
