from __future__ import annotations

import importlib.util
import json
import os
import platform
import sys
from typing import Any, Dict, List, Optional, TextIO, Tuple

from agentguard.evaluation import _load_events
from agentguard.setup import get_tracer, init, shutdown

_OPTIONAL_MODULES: Tuple[Tuple[str, str, str], ...] = (
    ("openai", "openai", "init() can auto-patch installed OpenAI clients."),
    ("anthropic", "anthropic", "init() can auto-patch installed Anthropic clients."),
    (
        "langchain_core",
        "langchain",
        "Use agentguard.integrations.langchain.AgentGuardCallbackHandler for callback-based tracing.",
    ),
    (
        "langgraph",
        "langgraph",
        "Use agentguard.integrations.langgraph.guarded_node for node-level enforcement.",
    ),
    (
        "crewai",
        "crewai",
        "Use agentguard.integrations.crewai.AgentGuardCrewHandler for CrewAI callbacks.",
    ),
)


def run_doctor(
    trace_path: str = "agentguard_doctor_trace.jsonl",
    stream: Optional[TextIO] = None,
    json_output: bool = False,
) -> int:
    """Verify the local SDK install without touching the hosted dashboard.

    Intended for a fresh process before AgentGuard has already been initialized.
    """
    out = stream or sys.stdout

    try:
        result = _run_checks(trace_path)
    except Exception as exc:
        result = {
            "status": "error",
            "error": str(exc),
            "trace_file": trace_path,
            "python": platform.python_version(),
        }
        if json_output:
            out.write(json.dumps(result) + "\n")
        else:
            _print(out, "AgentGuard doctor")
            _print(out, "No dashboard. No network calls. Local verification only.")
            _print(out, "")
            _print(out, f"[fail] {exc}")
        return 1

    if json_output:
        out.write(json.dumps(result) + "\n")
        return 0

    _render_text(result, out)
    return 0


def _run_checks(trace_path: str) -> Dict[str, Any]:
    if get_tracer() is not None:
        raise RuntimeError(
            "agentguard doctor must run before agentguard.init() or in a separate process."
        )

    detected, hints = _detect_optional_integrations()
    normalized_path = _prepare_trace_path(trace_path)
    events_written = _verify_local_init(normalized_path)

    return {
        "status": "ok",
        "python": platform.python_version(),
        "package_version": _package_version(),
        "trace_file": normalized_path,
        "events_written": events_written,
        "detected_integrations": detected,
        "integration_hints": hints,
        "next_commands": [
            "agentguard demo",
            f"agentguard report {normalized_path}",
        ],
        "recommended_snippet": _recommended_snippet(),
    }


def _detect_optional_integrations() -> Tuple[List[str], List[str]]:
    detected: List[str] = []
    hints: List[str] = []

    for module_name, label, hint in _OPTIONAL_MODULES:
        if importlib.util.find_spec(module_name) is not None:
            detected.append(label)
            hints.append(f"{label}: {hint}")

    return detected, hints


def _prepare_trace_path(trace_path: str) -> str:
    directory = os.path.dirname(trace_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    if os.path.exists(trace_path):
        os.remove(trace_path)
    return trace_path


def _verify_local_init(trace_path: str) -> int:
    saved_env = {
        "AGENTGUARD_API_KEY": os.environ.get("AGENTGUARD_API_KEY"),
        "AGENTGUARD_SERVICE": os.environ.get("AGENTGUARD_SERVICE"),
        "AGENTGUARD_TRACE_FILE": os.environ.get("AGENTGUARD_TRACE_FILE"),
        "AGENTGUARD_BUDGET_USD": os.environ.get("AGENTGUARD_BUDGET_USD"),
    }

    try:
        for key in saved_env:
            os.environ.pop(key, None)

        shutdown()
        tracer = init(
            service="agentguard-doctor",
            trace_file=trace_path,
            budget_usd=5.0,
            auto_patch=False,
            watermark=False,
            local_only=True,
        )
        with tracer.trace("doctor.verify") as span:
            span.event("reasoning.step", data={"thought": "verifying local SDK path"})
            span.event("tool.check", data={"tool": "doctor", "result": "ok"})
    finally:
        shutdown()
        for key, value in saved_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    events = _load_events(trace_path)
    if len(events) < 4:
        raise RuntimeError(
            f"Local trace verification wrote too few events to {trace_path} ({len(events)} found)"
        )
    return len(events)


def _package_version() -> str:
    try:
        from importlib.metadata import version

        return version("agentguard47")
    except Exception:
        return "0.0.0-dev"


def _recommended_snippet() -> str:
    return "\n".join(
        [
            "import agentguard",
            "",
            "agentguard.init(",
            '    service="my-agent",',
            "    budget_usd=5.00,",
            "    local_only=True,",
            ")",
        ]
    )


def _render_text(result: Dict[str, Any], out: TextIO) -> None:
    detected = result["detected_integrations"]
    hints = result["integration_hints"]

    _print(out, "AgentGuard doctor")
    _print(out, "No dashboard. No network calls. Local verification only.")
    _print(out, "")
    _print(out, f"[ok] Python: {result['python']}")
    _print(out, f"[ok] agentguard47: {result['package_version']}")
    _print(
        out,
        f"[ok] init(local_only=True): wrote {result['events_written']} events to {result['trace_file']}",
    )
    if detected:
        _print(out, f"[ok] Optional integrations detected: {', '.join(detected)}")
    else:
        _print(out, "[ok] Optional integrations detected: none")

    _print(out, "")
    _print(out, "Suggested next step:")
    _print(out, result["recommended_snippet"])
    _print(out, "")
    _print(out, "Helpful commands:")
    for command in result["next_commands"]:
        _print(out, f"  {command}")

    if hints:
        _print(out, "")
        _print(out, "Integration hints:")
        for hint in hints:
            _print(out, f"  - {hint}")


def _print(stream: TextIO, line: str) -> None:
    stream.write(line + "\n")
