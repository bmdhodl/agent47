"""Reproduce a scoped installed-wheel Windows framework check for issue #736."""
from __future__ import annotations

import argparse
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import zipfile


CASES = (
    "test_langchain_dispatch_propagates_budget_stop",
    "test_langgraph_node_budget_stops_the_graph",
    "test_otel_sink_exports_guard_spans",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, data: object) -> None:
    path.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--source", required=True, help="Full source commit SHA")
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--wheel-sha256", required=True)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=("floor", "current"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    environment = {
        name: value for name, value in os.environ.items()
        if not name.upper().startswith(("PYTHON", "PIP_", "UV_"))
        and not any(part in name.upper() for part in (
            "TOKEN", "KEY", "SECRET", "PASSWORD", "PATRIX", "AGENTGUARD",
            "OPENAI", "ANTHROPIC", "LANGSMITH", "LANGCHAIN", "OTEL",
        ))
    }
    environment.update(
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", AGENTGUARD_REQUIRE_REAL_DEPS="1",
        OPENAI_AGENTS_DISABLE_TRACING="1",
    )
    hidden = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

    def git(*argv: str) -> bytes:
        return subprocess.run(
            ["git", *argv], cwd=repo, env=environment, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=hidden,
        ).stdout

    assert git("rev-parse", args.source).decode().strip() == args.source
    wheel = args.wheel.resolve()
    assert digest(wheel.read_bytes()) == args.wheel_sha256
    package_sources = {}
    with zipfile.ZipFile(wheel) as archive:
        modules = [name for name in archive.namelist()
                   if name.startswith("agentguard/")
                   and (name.endswith(".py") or name.endswith("py.typed"))]
        tracked = git("ls-tree", "-r", "--name-only", args.source,
                      "sdk/agentguard").decode().splitlines()
        expected = {path.removeprefix("sdk/") for path in tracked
                    if path.endswith(".py") or path.endswith("py.typed")}
        assert set(modules) == expected
        for name in modules:
            data = git("show", f"{args.source}:sdk/{name}")
            assert archive.read(name).replace(b"\r\n", b"\n") == data.replace(b"\r\n", b"\n"), name
            package_sources[name] = digest(data)
        metadata_names = [name for name in archive.namelist()
                          if name.endswith(".dist-info/METADATA")]
        assert len(metadata_names) == 1
        metadata_bytes = archive.read(metadata_names[0])
        metadata = BytesParser().parsebytes(metadata_bytes)
        assert metadata["Name"] == "agentguard47" and metadata["Version"] == "1.4.1"
        assert metadata["Requires-Python"] == ">=3.9"
        assert all("extra ==" in value for value in metadata.get_all("Requires-Dist", []))

    inputs = ("sdk/tests/test_real_dispatch.py", ".github/requirements/ci-tools.txt",
              ".github/requirements/compat-floor.txt" if args.profile == "floor"
              else ".github/requirements/compat-latest.txt", "sdk/pyproject.toml")
    input_hashes = {}
    for path in inputs:
        data = git("show", f"{args.source}:{path}")
        name = "test_installed_dispatch.py" if path.endswith("test_real_dispatch.py") else Path(path).name
        (output / name).write_bytes(data)
        input_hashes[path] = digest(data)

    if args.profile == "current":
        supplement = Path(__file__).with_name("windows-platform.lock")
        (output / supplement.name).write_bytes(supplement.read_bytes())
        input_hashes["proof/windows-frameworks-736/windows-platform.lock"] = digest(supplement.read_bytes())

    commands = []

    def run(argv: list[str], log: str) -> str:
        with (output / log).open("w", encoding="utf-8") as stream:
            result = subprocess.run(argv, cwd=output, env=environment, stdout=stream,
                                    stderr=subprocess.STDOUT, creationflags=hidden)
        commands.append({"argv": argv, "cwd": str(output), "log": log, "exit": result.returncode})
        write_json(output / "commands.json", commands)
        assert result.returncode == 0, (log, result.returncode)
        return (output / log).read_text(encoding="utf-8")

    run([str(args.python), "-X", "utf8", "-m", "venv", str(output / "venv")], "venv.log")
    python = str(output / "venv/Scripts/python.exe")
    for lock in ("ci-tools.txt", "compat-floor.txt" if args.profile == "floor" else "compat-latest.txt"):
        argv = [python, "-X", "utf8", "-I", "-m", "pip", "--isolated", "install",
             "--index-url", "https://pypi.org/simple", "--only-binary=:all:",
             "--require-hashes", "-r", str(output / lock)]
        if lock == "compat-latest.txt":
            argv += ["-r", str(output / "windows-platform.lock")]
        run(argv, lock.replace(".txt", "-install.log"))
    run([python, "-I", "-c", "import importlib.metadata as m; assert not any(d.metadata['Name'].lower() == 'agentguard47' for d in m.distributions())"],
        "absent-before-install.log")
    run([python, "-X", "utf8", "-I", "-m", "pip", "--isolated", "install", "--no-deps", str(wheel)],
        "wheel-install.log")
    run([python, "-X", "utf8", "-I", "-m", "pip", "--isolated", "check"], "pip-check.log")
    probe = '''
import agentguard, importlib.metadata as m, json, pathlib, platform, sys, zipfile
d = m.distribution('agentguard47')
with zipfile.ZipFile(sys.argv[1]) as z:
    names = [n for n in z.namelist() if n.startswith('agentguard/') and (n.endswith('.py') or n.endswith('py.typed'))]
    for name in names:
        assert pathlib.Path(d.locate_file(name)).read_bytes() == z.read(name), name
    meta = next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))
    assert pathlib.Path(d.locate_file(meta)).read_bytes() == z.read(meta)
origin = pathlib.Path(agentguard.__file__).resolve()
assert origin.is_relative_to(pathlib.Path(sys.prefix).resolve())
direct = json.loads(d.read_text('direct_url.json'))
assert direct['url'] == pathlib.Path(sys.argv[1]).as_uri()
provenance_hash = direct['archive_info'].get('hashes', {}).get('sha256')
if provenance_hash is not None:
    assert provenance_hash == sys.argv[2]
assert all('extra ==' in value for value in d.requires or [])
packages = ('langchain-core', 'langgraph', 'langgraph-checkpoint', 'langgraph-sdk', 'opentelemetry-api', 'opentelemetry-sdk', 'pytest')
print(json.dumps({'python': platform.python_version(), 'platform': platform.platform(),
    'sdk': d.version, 'requires_python': d.metadata['Requires-Python'], 'installed_files_equal_wheel': len(names),
    'installed_metadata_equal_wheel': True, 'mandatory_runtime_dependencies': 0,
    'import_inside_venv': True, 'origin': str(origin), 'direct_url_verified': True,
    'pip_provenance_hash_present': provenance_hash is not None,
    'versions': {name: m.version(name) for name in packages},
    'all_distributions': {d.metadata['Name']: d.version for d in m.distributions()}}))
'''
    identity = json.loads(run([python, "-X", "utf8", "-I", "-c", probe, str(wheel), args.wheel_sha256],
                              "identity.json"))
    major_minor = ".".join(identity["python"].split(".")[:2])
    assert major_minor == ("3.10" if args.profile == "floor" else "3.13")
    assert identity["platform"].startswith("Windows")
    copied_test = output / "test_installed_dispatch.py"
    argv = [python, "-X", "utf8", "-I", "-m", "pytest"]
    argv += [f"{copied_test}::{name}" for name in CASES]
    argv += ["-q", "--confcutdir", str(output), "--junitxml", str(output / "tests.xml"),
             "--basetemp", str(output / "pytest")]
    test_output = run(argv, "tests.log")
    suites = ET.parse(output / "tests.xml").getroot().findall("testsuite")
    counts = {key: sum(int(s.attrib.get(key, "0")) for s in suites)
              for key in ("tests", "failures", "errors", "skipped")}
    assert counts == {"tests": 3, "failures": 0, "errors": 0, "skipped": 0}, counts
    assert sorted(case.attrib["name"] for s in suites for case in s.findall("testcase")) == sorted(CASES)
    assert "warnings summary" not in test_output
    write_json(output / "receipt.json", {
        "profile": args.profile, "source_commit": args.source, "wheel": wheel.name,
        "wheel_sha256": args.wheel_sha256, "wheel_metadata_sha256": digest(metadata_bytes),
        "source_files": package_sources, "input_sha256": input_hashes, "installed": identity,
        "cases": list(CASES), "counts": counts, "pip_check_exit": 0,
        "fresh_venv": True, "hash_enforced_unmodified_locks": True,
        "agentguard_absent_before_install": True, "no_repository_conftest": True,
        "test_file_copied_from_git_blob": True, "environment_scrubbed": True,
        "network": "PyPI installs only; framework tests use local graph/callback/exporter",
    })
    print(f"{args.profile}: Windows/Python {identity['python']}; three installed framework cases passed, zero skips", flush=True)


if __name__ == "__main__":
    main()
