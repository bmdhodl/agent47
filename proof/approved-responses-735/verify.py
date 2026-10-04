"""Verify retained AG-06 acceptance evidence without provider or network calls."""
import gzip
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify():
    receipt = json.loads((HERE / "receipt.json").read_text(encoding="utf-8"))
    artifacts = receipt["artifacts"]
    require(len(artifacts) >= 75, "Incomplete artifact inventory")
    for name, expected in artifacts.items():
        require(Path(name).name == name, "Artifact path leaves proof directory")
        require(digest((HERE / name).read_bytes()) == expected, "Artifact differs: " + name)
    expected_commands = {"candidate-build"}
    for profile in ("floor", "current"):
        expected_commands.update(profile + "-" + suffix for suffix in (
            "venv", "providers", "wheel", "pip-check", "inventory", "responses", "free-local", "example"))
    expected_commands.update("source-" + suffix for suffix in (
        "full", "ruff", "bandit", "docs", "release", "tools", "review"))
    commands = receipt["commands"]
    require(len(commands) == len(expected_commands), "Unexpected command count")
    require({r["name"] for r in commands} == expected_commands, "Missing acceptance command")
    for row in commands:
        require(row["exit"] == 0, "Acceptance command failed: " + row["name"])
        name = row["name"] + ".log.gz"
        require(name in artifacts, "Command has no retained output")
        output = gzip.decompress((HERE / name).read_bytes())
        quiet = row["name"].endswith("-venv") or row["name"] == "source-bandit"
        require(bool(output) or quiet, "Unexpected empty command output: " + row["name"])
    pairs = [("1.66.3", "0.0.3"), ("3.22.1", "0.22.3")]
    for profile in ("floor", "current"):
        output = gzip.decompress((HERE / (profile + "-example.log.gz")).read_bytes())
        require(b"Recorded $0.0600 over 5 model calls" in output, "Example budget result differs")
        require(b"Fake local transport received 5 requests; no sixth dispatch." in output, "Example interception proof differs")
    require(len(receipt["profiles"]) == 2, "Both installed profiles are required")
    for profile, versions, row in zip(("floor", "current"), pairs, receipt["profiles"]):
        require((row["openai"], row["agents"]) == versions, "Provider versions differ")
        require(row["version"] == "2.0.0", "Wrong AgentGuard candidate")
        require(row["python"].startswith("3.11.") and row["system"] == "Windows", f"Wrong platform for {profile}")
        require(row["package_files_equal_wheel_and_source"] >= 40, "Incomplete installed identity proof")
        require(row["metadata_equal_wheel"] and row["mandatory_runtime_requirements"] == 0, "Core dependency contract differs")
        for suite in ("responses", "free-local"):
            name = profile + "-" + suite + ".xml.gz"
            require(name in artifacts, "Missing test XML")
            suites = list(ET.fromstring(gzip.decompress((HERE / name).read_bytes())).iter("testsuite"))
            counts = {k: sum(int(s.get(k, "0")) for s in suites) for k in ("tests", "skipped", "failures", "errors")}
            require(counts["tests"] >= (13 if suite == "responses" else 1), "Empty or incomplete installed test suite")
            require(all(counts[k] == 0 for k in ("skipped", "failures", "errors")), "Installed suite did not run cleanly")
            if suite == "responses":
                require(counts == row["responses_suite"], "Profile test counts differ from XML")
    sources = receipt["source_hashes"]
    require(len(sources) >= 50, "Incomplete source snapshot inventory")
    for index, (path, expected) in enumerate(sorted(sources.items())):
        local = (ROOT / path).resolve()
        require(ROOT.resolve() in local.parents, "Source path leaves repository")
        archived = gzip.decompress((HERE / f"source-{index:02d}.gz").read_bytes())
        require(digest(archived) == expected, "Source snapshot differs: " + path)
        require(digest(local.read_bytes().replace(b"\r\n", b"\n")) == expected, "Checkout source differs: " + path)
    wheel_name = "agentguard47-2.0.0-py3-none-any.whl"
    require(wheel_name in artifacts, "Candidate wheel missing")
    require(all(row["wheel_sha256"] == artifacts[wheel_name] for row in receipt["profiles"]), "Profile wheel identity differs")
    with zipfile.ZipFile(HERE / wheel_name) as wheel:
        require(wheel.testzip() is None, "Wheel CRC failure")
        names = [n for n in wheel.namelist() if n.startswith("agentguard/") and n.endswith(".py")]
        require(len(names) == receipt["profiles"][0]["package_files_equal_wheel_and_source"], "Wheel package inventory differs")
        for name in names:
            require(digest(wheel.read(name).replace(b"\r\n", b"\n")) == sources["sdk/" + name], "Wheel source differs: " + name)
    verifier = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    require(digest(verifier) == receipt["verifier_sha256"], "Verifier changed after evidence freeze")
    print("Verified installed AG-06 acceptance evidence: two profiles, no skipped acceptance tests")


if __name__ == "__main__":
    verify()
