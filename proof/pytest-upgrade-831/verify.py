"""Verify the retained PR831 Windows lock repair and source-suite receipts."""

import gzip
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
for name, expected in manifest.items():
    data = (root / name).read_bytes()
    if Path(name).suffix in (".md", ".py", ".json", ".lock"):
        data.decode("utf-8")
        data = data.replace(b"\r\n", b"\n")
    assert hashlib.sha256(data).hexdigest() == expected, name


def entries(name):
    result = {}
    raw = (root / name).read_bytes()
    for block in re.split(rb"(?=^[A-Za-z0-9][A-Za-z0-9_.\[\]-]*==)", raw, flags=re.M):
        match = re.match(rb"([A-Za-z0-9_.\[\]-]+)==([^\s]+)", block)
        if match:
            result[match[1].decode()] = (
                match[2].decode(),
                sorted(re.findall(rb"--hash=sha256:([a-f0-9]{64})", block)),
            )
    return result


old, new = entries("original.lock"), entries("repaired.lock")
assert len(old) == 21 and all(new[name] == value for name, value in old.items())
assert set(new) - set(old) == {"colorama"}
assert new["colorama"][0] == "0.4.6" and len(new["colorama"][1]) == 2
assert new["pytest"][0] == "9.0.3"
compiler = json.loads((root / "compiler-receipt.json").read_text())
assert compiler["compiler"] == {"python": "3.10.11", "pip_tools": "7.6.1"}
assert hashlib.sha256((root / "repaired.lock").read_bytes().replace(b"\r\n", b"\n")).hexdigest() == compiler["after_sha256"]
original_commands = json.loads((root / "original-commands.json").read_text())
assert original_commands[-1]["name"] == "install" and original_commands[-1]["exit_code"] == 1
original_log = gzip.decompress((root / "original-install.log.gz").read_bytes())
assert b"ERROR: In --require-hashes mode" in original_log and b"colorama>=0.3.9" in original_log
commands = json.loads((root / "retry-commands.json").read_text())
assert len(commands) == 5 and all(item["exit_code"] == 0 for item in commands)
for item in commands:
    log = gzip.decompress((root / (item["name"] + ".log.gz")).read_bytes())
    assert hashlib.sha256(log).hexdigest() == item["log_sha256"]
checks = json.loads((root / "checks.json").read_text())
assert len(checks) == 9
assert all(item["exit"] == (1 if item["name"] == "ci-tools-current-python39-policy" else 0) for item in checks)
cases = ET.fromstring(gzip.decompress((root / "suite.xml.gz").read_bytes())).findall(".//testcase")
skips = sum(case.find("skipped") is not None for case in cases)
assert len(cases) - skips == 1473 and skips == 114
assert all(case.find("failure") is None and case.find("error") is None for case in cases)
summary = json.loads((root / "summary.json").read_text())
assert summary["tests_passed"] == 1473 and summary["tests_skipped"] == 114
assert summary["sdk_tree_matches_main_45c4d54"] is True
assert summary["coverage_percent"] == 91.30 and summary["pytest_warning_count"] == 0
assert summary["identity"]["pytest"] == "9.0.3"
print(f"Verified {len(manifest)} artifact hashes, 21 preserved pins, Windows hash install and 1473 source tests; 114 optional-provider skips. Python 3.9 policy remains unresolved.")
