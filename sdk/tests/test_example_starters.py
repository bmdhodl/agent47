from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from agentguard.quickstart import FRAMEWORK_CHOICES, _build_quickstart_payload
from agentguard.reporting import render_incident_report

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTERS_ROOT = REPO_ROOT / "examples" / "starters"


def test_quickstart_payloads_have_matching_starter_files() -> None:
    for framework in FRAMEWORK_CHOICES:
        payload = _build_quickstart_payload(
            framework=framework,
            service="my-agent",
            budget_usd=5.0,
            trace_file=".agentguard/traces.jsonl",
        )
        starter_path = STARTERS_ROOT / payload["filename"]
        assert starter_path.exists(), f"Missing starter file for {framework}: {starter_path}"
        compile(
            starter_path.read_text(encoding="utf-8"),
            str(starter_path),
            "exec",
            flags=0,
            dont_inherit=True,
        )


def test_raw_starter_runs_and_writes_trace() -> None:
    starter_path = STARTERS_ROOT / "agentguard_raw_quickstart.py"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    sdk_path = str(REPO_ROOT / "sdk")
    env["PYTHONPATH"] = (
        sdk_path
        if not existing_pythonpath
        else os.pathsep.join([sdk_path, existing_pythonpath])
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [sys.executable, str(starter_path)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            raise AssertionError(
                "Starter timed out after 60 seconds.\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            ) from exc

        assert result.returncode == 0, result.stderr
        assert "Completed local raw starter run." in result.stdout
        assert Path(tmpdir, ".agentguard", "traces.jsonl").exists()


def test_pydantic_ai_starter_is_optional_and_local_first() -> None:
    starter_path = STARTERS_ROOT / "agentguard_pydantic_ai_quickstart.py"
    assert starter_path.exists(), f"Missing Pydantic AI starter: {starter_path}"
    source = starter_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    compile(source, str(starter_path), "exec", flags=0, dont_inherit=True)
    imports = {
        (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert ("pydantic_ai", "Agent") in imports
    assert ("pydantic_ai.models.test", "TestModel") in imports
    assert "pydantic-ai" in source

    init_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "agentguard"
        and node.func.attr == "init"
    ]
    assert init_calls, "Pydantic AI starter should initialize AgentGuard"
    init_keywords = {
        keyword.arg: keyword.value
        for keyword in init_calls[0].keywords
        if keyword.arg is not None
    }
    assert isinstance(init_keywords.get("local_only"), ast.Constant)
    assert init_keywords["local_only"].value is True
    assert isinstance(init_keywords.get("auto_patch"), ast.Constant)
    assert init_keywords["auto_patch"].value is False


def test_disposable_harness_example_links_session_id() -> None:
    example_path = REPO_ROOT / "examples" / "disposable_harness_session.py"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    sdk_path = str(REPO_ROOT / "sdk")
    env["PYTHONPATH"] = (
        sdk_path
        if not existing_pythonpath
        else os.pathsep.join([sdk_path, existing_pythonpath])
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [sys.executable, str(example_path)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            raise AssertionError(
                "Disposable harness example timed out after 60 seconds.\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            ) from exc

        assert result.returncode == 0, result.stderr
        assert "Shared session_id: support-session-001" in result.stdout
        assert Path(tmpdir, "managed_session_traces.jsonl").exists()


def test_per_token_budget_spike_example_runs() -> None:
    example_path = REPO_ROOT / "examples" / "per_token_budget_spike.py"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    sdk_path = str(REPO_ROOT / "sdk")
    env["PYTHONPATH"] = (
        sdk_path
        if not existing_pythonpath
        else os.pathsep.join([sdk_path, existing_pythonpath])
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [sys.executable, str(example_path)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            raise AssertionError(
                "Per-token budget spike example timed out after 60 seconds.\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            ) from exc

        assert result.returncode == 0, result.stderr
        assert "Budget spike caught on turn 3" in result.stdout
        assert Path(tmpdir, "per_token_budget_spike_traces.jsonl").exists()


def test_coding_agent_review_loop_example_runs_offline() -> None:
    example_path = REPO_ROOT / "examples" / "coding_agent_review_loop.py"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    sdk_path = str(REPO_ROOT / "sdk")
    env["PYTHONPATH"] = (
        sdk_path
        if not existing_pythonpath
        else os.pathsep.join([sdk_path, existing_pythonpath])
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [sys.executable, str(example_path)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            raise AssertionError(
                "Coding-agent review loop example timed out after 60 seconds.\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            ) from exc

        assert result.returncode == 0, result.stderr
        assert "No API keys. No dashboard. No network calls." in result.stdout
        assert "BudgetGuard stopped review loop on attempt 3" in result.stdout
        assert "RetryGuard stopped retry storm on attempt 4" in result.stdout

        trace_path = Path(tmpdir, "coding_agent_review_loop_traces.jsonl")
        assert trace_path.exists()
        names = []
        with trace_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    names.append(json.loads(line)["name"])
        assert "review.iteration" in names
        assert "guard.budget_exceeded" in names
        assert "guard.retry_limit_exceeded" in names


def test_coding_agent_review_loop_sample_incident_is_in_sync() -> None:
    example_path = REPO_ROOT / "examples" / "coding_agent_review_loop.py"
    sample_path = REPO_ROOT / "docs" / "examples" / "coding-agent-review-loop-incident.md"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    sdk_path = str(REPO_ROOT / "sdk")
    env["PYTHONPATH"] = (
        sdk_path
        if not existing_pythonpath
        else os.pathsep.join([sdk_path, existing_pythonpath])
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [sys.executable, str(example_path)],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=60,
        )

        assert result.returncode == 0, result.stderr
        trace_path = Path(tmpdir, "coding_agent_review_loop_traces.jsonl")
        expected = _normalize_incident_snapshot(
            render_incident_report(str(trace_path), output_format="markdown") + "\n"
        )
        actual = sample_path.read_text(encoding="utf-8")

        assert _normalize_incident_snapshot(actual) == expected


def _normalize_incident_snapshot(markdown: str) -> str:
    lines = markdown.lstrip("\ufeff").splitlines()
    return "\n".join(
        "- Duration: <runtime> ms" if line.startswith("- Duration: ") else line
        for line in lines
    ) + "\n"


def test_budget_aware_escalation_example_runs() -> None:
    example_path = REPO_ROOT / "examples" / "budget_aware_escalation.py"
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH")
    sdk_path = str(REPO_ROOT / "sdk")
    env["PYTHONPATH"] = (
        sdk_path
        if not existing_pythonpath
        else os.pathsep.join([sdk_path, existing_pythonpath])
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [sys.executable, str(example_path)],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            raise AssertionError(
                "Budget-aware escalation example timed out after 60 seconds.\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            ) from exc

        assert result.returncode == 0, result.stderr
        assert "Turn 1 model: ollama/llama3.1:8b" in result.stdout
        assert "Turn 2 model: claude-opus-4-6" in result.stdout
        trace_path = Path(tmpdir, "budget_aware_escalation_traces.jsonl")
        assert trace_path.exists()

        routes = []
        with trace_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                event = json.loads(line)
                if event.get("kind") == "event" and event.get("name") == "model.route":
                    routes.append(event.get("data", {}).get("route"))
        assert routes == ["primary", "escalated"]
