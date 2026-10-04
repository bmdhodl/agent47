"""Verify dated Python-support, compiler, source-suite and installed-wheel receipts."""

import email
import gzip
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

root = Path(__file__).resolve().parent
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
for name, expected in manifest.items():
    data = (root / name).read_bytes()
    if Path(name).suffix in (".md", ".py", ".json"):
        data = data.decode("utf-8").replace("\r\n", "\n").encode("utf-8")
    assert hashlib.sha256(data).hexdigest() == expected, name


def packed_json(name):
    return json.loads(gzip.decompress((root / name).read_bytes()))


def check_commands(name, prefix=""):
    commands = packed_json(name)
    for item in commands:
        log = item.get("log", item["name"] + ".log")
        raw = gzip.decompress((root / (prefix + log + ".gz")).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == item["log_sha256"], log
    return commands


red = check_commands("red-commands.json.gz")
assert red[-1]["exit"] == 1
assert b"2 failed" in gzip.decompress((root / "red-regression.log.gz").read_bytes())
initial = check_commands("green-commands.json.gz")
assert initial[-1]["name"] == "suite" and initial[-1]["exit"] == 1
positive = check_commands("green-r2-commands.json.gz")
assert all(item["exit"] == item["expected_exit"] == 0 for item in positive[:-1])
# The misleading cross-version simulation is retained, never used as rejection proof.
assert positive[-1]["name"] == "reject-3.9" and positive[-1]["exit"] == 0
negative = check_commands("negative-commands.json.gz", "negative-")
assert len(negative) == 6
for item in negative:
    assert item["exit"] == item["expected_exit"]
    if item["name"].endswith("install"):
        raw = gzip.decompress((root / ("negative-" + item["log"] + ".gz")).read_bytes())
        assert item["exit"] == 1 and b"requires a different Python" in raw and b">=3.11" in raw
assert all(item["exit"] == 0 for item in check_commands("compiler-commands.json.gz", "compiler-"))
compiler = packed_json("compiler-receipt.json.gz")
assert compiler["compiler"] == {"python": "3.11.9", "pip_tools": "7.6.1"}


def pins(name, expected_sha):
    raw = gzip.decompress((root / name).read_bytes()).replace(b"\r\n", b"\n")
    assert hashlib.sha256(raw).hexdigest() == expected_sha
    result = {}
    for block in re.split(rb"(?=^[A-Za-z0-9][A-Za-z0-9_.\[\]-]*==)", raw, flags=re.M):
        match = re.match(rb"([A-Za-z0-9_.\[\]-]+)==([^\s]+)", block)
        if match:
            result[match[1].decode()] = (match[2], sorted(re.findall(rb"--hash=sha256:([a-f0-9]{64})", block)))
    return result


old = pins("compiler-previous.lock.gz", compiler["before_sha256"])
new = pins("compiler-compiled.lock.gz", compiler["after_sha256"])
assert len(old) == 22 and len(new) == 19 and all(old[name] == value for name, value in new.items())
assert set(old) - set(new) == {"exceptiongroup", "tomli", "typing-extensions"}
assert new["pytest"][0] == b"9.0.3" and new["colorama"][0] == b"0.4.6"
cases = ET.fromstring(gzip.decompress((root / "suite.xml.gz").read_bytes())).findall(".//testcase")
assert len(cases) == 1589 and sum(case.find("skipped") is not None for case in cases) == 114
assert all(case.find("failure") is None and case.find("error") is None for case in cases)
summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
assert summary["tests_passed"] == 1475 and summary["tests_skipped"] == 114
assert summary["coverage_percent"] == 91.36 and summary["pytest_warning_count"] == 0
assert summary["identity"]["python"] == "3.11.9" and summary["identity"]["pytest"] == "9.0.3"
with zipfile.ZipFile(root / "agentguard47-2.0.0-py3-none-any.whl") as wheel:
    metadata = email.message_from_bytes(wheel.read("agentguard47-2.0.0.dist-info/METADATA"))
assert metadata["Version"] == "2.0.0" and metadata["Requires-Python"] == ">=3.11"
assert all("extra ==" in requirement for requirement in metadata.get_all("Requires-Dist", []))
browser = json.loads((root / "browser-checks.json").read_text(encoding="utf-8"))
assert len(browser) == 12 and {item["viewport"] for item in browser} == {375, 768, 1440}
assert all(item["passed"] and item["dimensions"]["scroll"] == item["viewport"] for item in browser)
assert browser == json.loads(packed_json("browser-check.log.gz")["result"])
assert all(item["exit"] == 0 for item in packed_json("browser-commands.json.gz"))
print(f"Verified {len(manifest)} artifact hashes; Python 3.11 floor, 1475 source passes, 114 optional-provider skips, old-interpreter rejection and 12 browser checks.")
