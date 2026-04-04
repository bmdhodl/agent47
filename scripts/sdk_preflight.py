"""Run a fast local preflight for the SDK based on changed files."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Set

REPO_ROOT = Path(__file__).resolve().parents[1]
README_SYNC_INPUTS = {
    "README.md",
    "CHANGELOG.md",
    "sdk/PYPI_README.md",
    "scripts/generate_pypi_readme.py",
}
SDK_CODE_PREFIXES = (
    "sdk/agentguard/",
)
PYTHON_LINT_PREFIXES = (
    "sdk/agentguard/",
    "sdk/tests/",
    "scripts/",
)
TEST_MAP = {
    "sdk/agentguard/__init__.py": [
        "sdk/tests/test_exports.py",
        "sdk/tests/test_first_run.py",
        "sdk/tests/test_smoke.py",
    ],
    "sdk/agentguard/atracing.py": [
        "sdk/tests/test_atracing.py",
    ],
    "sdk/agentguard/cli.py": [
        "sdk/tests/test_cli_report.py",
    ],
    "sdk/agentguard/cost.py": [
        "sdk/tests/test_cost.py",
    ],
    "sdk/agentguard/demo.py": [
        "sdk/tests/test_demo.py",
    ],
    "sdk/agentguard/doctor.py": [
        "sdk/tests/test_doctor.py",
    ],
    "sdk/agentguard/evaluation.py": [
        "sdk/tests/test_evaluation.py",
    ],
    "sdk/agentguard/guards.py": [
        "sdk/tests/test_concurrency.py",
        "sdk/tests/test_guards.py",
    ],
    "sdk/agentguard/instrument.py": [
        "sdk/tests/test_instrument.py",
        "sdk/tests/test_instrument_patch.py",
    ],
    "sdk/agentguard/integrations/crewai.py": [
        "sdk/tests/test_crewai_integration.py",
    ],
    "sdk/agentguard/integrations/langchain.py": [
        "sdk/tests/test_langchain_integration.py",
    ],
    "sdk/agentguard/integrations/langgraph.py": [
        "sdk/tests/test_langgraph_integration.py",
    ],
    "sdk/agentguard/quickstart.py": [
        "sdk/tests/test_quickstart.py",
    ],
    "sdk/agentguard/reporting.py": [
        "sdk/tests/test_cli_report.py",
        "sdk/tests/test_reporting.py",
    ],
    "sdk/agentguard/savings.py": [
        "sdk/tests/test_cli_report.py",
        "sdk/tests/test_reporting.py",
        "sdk/tests/test_savings.py",
    ],
    "sdk/agentguard/setup.py": [
        "sdk/tests/test_doctor.py",
        "sdk/tests/test_init.py",
    ],
    "sdk/agentguard/sinks/http.py": [
        "sdk/tests/test_http_sink.py",
        "sdk/tests/test_hosted_ingest_contract.py",
        "sdk/tests/test_integration_cost_guardrail.py",
        "sdk/tests/test_e2e_pipeline.py",
    ],
    "sdk/agentguard/sinks/otel.py": [
        "sdk/tests/test_otel_sink.py",
    ],
    "sdk/agentguard/tracing.py": [
        "sdk/tests/test_tracing.py",
    ],
    "sdk/agentguard/usage.py": [
        "sdk/tests/test_instrument.py",
        "sdk/tests/test_langchain_integration.py",
        "sdk/tests/test_savings.py",
    ],
    "scripts/sdk_preflight.py": [
        "sdk/tests/test_sdk_preflight.py",
    ],
    "sdk/tests/conftest.py": [
        "sdk/tests/test_hosted_ingest_contract.py",
        "sdk/tests/test_integration_cost_guardrail.py",
        "sdk/tests/test_e2e_pipeline.py",
    ],
    "sdk/tests/integration_dashboard.py": [
        "sdk/tests/test_integration_dashboard_script.py",
    ],
}
BANDIT_ARGS = ["-m", "bandit", "-r", "sdk/agentguard/", "-s", "B101,B110,B112,B311", "-q"]


@dataclass(frozen=True)
class Step:
    label: str
    reason: str
    command: List[str]


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _existing(paths: Iterable[str]) -> List[str]:
    return sorted(path for path in {_normalize_path(value) for value in paths} if (REPO_ROOT / path).exists())


def discover_changed_files() -> List[str]:
    """Discover tracked and untracked local changes."""
    git_commands = (
        ["git", "diff", "--name-only", "--cached"],
        ["git", "diff", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    )
    changed: Set[str] = set()
    for command in git_commands:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            normalized = _normalize_path(line.strip())
            if normalized:
                changed.add(normalized)
    return sorted(changed)


def build_plan(changed_files: Sequence[str]) -> List[Step]:
    """Build a fast preflight plan from a set of changed files."""
    normalized = {_normalize_path(path) for path in changed_files if _normalize_path(path)}
    steps: List[Step] = []

    lint_targets = _existing(
        path
        for path in normalized
        if path.endswith(".py") and path.startswith(PYTHON_LINT_PREFIXES)
    )
    if lint_targets:
        steps.append(
            Step(
                label="ruff",
                reason="lint only the Python files touched in this branch",
                command=[sys.executable, "-m", "ruff", "check", *lint_targets],
            )
        )

    pytest_targets: Set[str] = set()
    for path in normalized:
        if (
            path.startswith("sdk/tests/")
            and path.endswith(".py")
            and Path(path).name.startswith("test_")
            and (REPO_ROOT / path).exists()
        ):
            pytest_targets.add(path)
        pytest_targets.update(TEST_MAP.get(path, ()))

        if path.startswith("sdk/agentguard/") and path.endswith(".py"):
            fallback = f"sdk/tests/test_{Path(path).stem}.py"
            if (REPO_ROOT / fallback).exists():
                pytest_targets.add(fallback)

    if pytest_targets:
        steps.append(
            Step(
                label="targeted-pytest",
                reason="run only the test files most directly tied to the touched SDK paths",
                command=[sys.executable, "-m", "pytest", *sorted(pytest_targets), "-v"],
            )
        )

    if any(path.startswith(SDK_CODE_PREFIXES) for path in normalized):
        steps.append(
            Step(
                label="structural",
                reason="SDK module edits must keep the architectural invariants green",
                command=[sys.executable, "-m", "pytest", "sdk/tests/test_architecture.py", "-v"],
            )
        )
        steps.append(
            Step(
                label="security",
                reason="SDK module edits should get a fast security scan before the full gate",
                command=[sys.executable, *BANDIT_ARGS],
            )
        )

    if normalized & README_SYNC_INPUTS:
        steps.append(
            Step(
                label="pypi-readme-sync",
                reason="README/changelog metadata must stay in sync with the generated PyPI description",
                command=[sys.executable, "scripts/generate_pypi_readme.py", "--check"],
            )
        )
        steps.append(
            Step(
                label="pypi-readme-test",
                reason="the committed PyPI README snapshot should still match the generator output",
                command=[sys.executable, "-m", "pytest", "sdk/tests/test_pypi_readme_sync.py", "-v"],
            )
        )

    return steps


def run_plan(steps: Sequence[Step]) -> int:
    """Execute the planned preflight steps."""
    if not steps:
        print("No SDK-relevant changes detected; preflight has nothing to run.")
        return 0

    for step in steps:
        print(f"==> {step.label}: {step.reason}")
        print(" ".join(step.command))
        result = subprocess.run(step.command, cwd=REPO_ROOT, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Treat this repo-relative path as changed. Can be passed multiple times.",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Print the planned steps as JSON instead of running them.",
    )
    args = parser.parse_args(argv)

    changed_files = args.changed_file or discover_changed_files()
    plan = build_plan(changed_files)
    if args.plan:
        print(json.dumps([asdict(step) for step in plan], indent=2))
        return 0
    return run_plan(plan)


if __name__ == "__main__":
    raise SystemExit(main())
