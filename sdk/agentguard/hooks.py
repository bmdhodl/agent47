"""Claude Code hook: refuse repeated tool calls, retry storms, and runs past a call cap.

Claude Code runs this as a command hook on PreToolUse, PostToolUse, and
PostToolUseFailure. Each invocation is a fresh process, so per-session counts
live in a JsonFileStateStore under ``.agentguard/`` in the project. A refused
PreToolUse exits 2; Claude Code blocks the call and shows the reason to the
model. Refusals are written to a JSONL trace that ``agentguard receipt`` reads.

Bounds: only tool calls that fire PreToolUse are checked. Model tokens,
subagent internals, and subscription quota are not.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

from agentguard.profiles import CODING_AGENT_PROFILE, get_profile_defaults
from agentguard.repo_config import load_repo_config
from agentguard.state import JsonFileStateStore
from agentguard.tracing import JsonlFileSink, Tracer

STATE_FILE = "claude-code-state.json"
TRACE_FILE = "claude-code.jsonl"
SETTINGS_FILE = Path(".claude") / "settings.local.json"
EVENTS = ("PreToolUse", "PostToolUse", "PostToolUseFailure")
HOOK_ARGS = ["-m", "agentguard.cli", "hook", "claude-code"]
# Bash sends a free-text description that changes between otherwise identical calls.
_IGNORED_INPUT_KEYS = {"description"}
_SESSION_RE = re.compile(r"[^A-Za-z0-9_.-]")


class Refusal(Exception):
    """A tool call the hook refuses. The message is shown to the model."""

    def __init__(self, kind: str, message: str, data: Dict[str, Any]) -> None:
        super().__init__(message)
        self.kind = kind
        self.data = data


def signature(tool_name: str, tool_input: Any) -> str:
    if isinstance(tool_input, dict):
        tool_input = {k: v for k, v in tool_input.items() if k not in _IGNORED_INPUT_KEYS}
    raw = json.dumps([tool_name, tool_input], sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def preview(tool_name: str, tool_input: Any) -> str:
    if isinstance(tool_input, dict):
        for key in ("command", "file_path", "pattern", "url", "prompt"):
            if key in tool_input:
                return f"{tool_name}({str(tool_input[key])[:60]})"
    return tool_name


def limits(project_dir: str, max_calls: Optional[int]) -> Dict[str, Any]:
    """Loop and retry caps from .agentguard.json, else the coding-agent profile."""
    _, config = load_repo_config(project_dir)
    defaults = get_profile_defaults(config.get("profile", CODING_AGENT_PROFILE))
    return {
        "loop_max": config.get("loop_max", defaults["loop_max"]),
        "retry_max": config.get("retry_max", defaults["retry_max"]),
        "max_calls": max_calls,
    }


def check_and_record(state: Optional[Dict[str, Any]], sig: str, label: str,
                     caps: Dict[str, Any]) -> Dict[str, Any]:
    """PreToolUse: raise Refusal, or return the state with this call recorded."""
    state = state or {"calls": 0, "last": None, "streak": 0, "failures": {}}
    if caps["max_calls"] is not None and state["calls"] >= caps["max_calls"]:
        raise Refusal("budget", f"AgentGuard refused {label}: this session already made "
                      f"{state['calls']} tool calls (limit {caps['max_calls']}). Stop and "
                      "report progress to the user.",
                      {"calls_used": state["calls"], "limit_calls": caps["max_calls"]})
    streak = state["streak"] + 1 if state["last"] == sig else 1
    if caps["loop_max"] and streak >= caps["loop_max"]:
        raise Refusal("loop", f"AgentGuard refused {label}: the same call just ran "
                      f"{streak - 1} times in a row (limit {caps['loop_max'] - 1}). Change the "
                      "input or the approach.",
                      {"tool_name": label, "repeats": streak - 1, "limit": caps["loop_max"] - 1})
    failures = state["failures"].get(sig, 0)
    if caps["retry_max"] and failures >= caps["retry_max"]:
        raise Refusal("retry", f"AgentGuard refused {label}: the same call already failed "
                      f"{failures} times (limit {caps['retry_max']}). Diagnose the failure "
                      "before trying again.",
                      {"tool_name": label, "failures": failures, "limit": caps["retry_max"]})
    state.update(calls=state["calls"] + 1, last=sig, streak=streak)
    return state


def record_result(state: Optional[Dict[str, Any]], sig: str, failed: bool) -> Dict[str, Any]:
    """PostToolUse / PostToolUseFailure: count failures per call signature."""
    state = state or {"calls": 0, "last": None, "streak": 0, "failures": {}}
    if failed:
        state["failures"][sig] = state["failures"].get(sig, 0) + 1
    else:
        state["failures"].pop(sig, None)
    return state


_GUARD_EVENTS = {
    "budget": "guard.budget_exceeded",
    "loop": "guard.loop_detected",
    "retry": "guard.retry_limit_exceeded",
}


def run(stdin: TextIO, stderr: TextIO, max_calls: Optional[int] = None) -> int:
    """Handle one hook event. Returns the process exit code."""
    try:
        event = json.load(stdin)
        name = event["hook_event_name"]
        tool_name = event["tool_name"]
        session = _SESSION_RE.sub("_", str(event["session_id"])) or "unknown"
    except (ValueError, KeyError, TypeError) as exc:
        # Any exit other than 0 or 2 is a non-blocking error: the call proceeds and
        # Claude Code shows a hook error.
        stderr.write(f"agentguard hook: unreadable hook input ({exc})\n")
        return 1
    if name not in EVENTS:
        return 0
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    root = Path(project_dir) / ".agentguard"
    store = JsonFileStateStore(root / STATE_FILE)
    tool_input = event.get("tool_input")
    sig = signature(tool_name, tool_input)
    if name != "PreToolUse":
        store.update(session, lambda s: record_result(s, sig, name == "PostToolUseFailure"))
        return 0
    label = preview(tool_name, tool_input)
    caps = limits(project_dir, max_calls)
    tracer = Tracer(sink=JsonlFileSink(str(root / TRACE_FILE)), service="claude-code",
                    watermark=False)
    try:
        store.update(session, lambda s: check_and_record(s, sig, label, caps))
    except Refusal as refusal:
        with tracer.trace("claude_code.tool_call", data={"session": session}) as ctx:
            ctx.event(_GUARD_EVENTS[refusal.kind], data={**refusal.data, "message": str(refusal)})
        stderr.write(f"{refusal}\n")
        return 2
    with tracer.trace("claude_code.tool_call", data={"session": session}) as ctx:
        ctx.event("tool.call", data={"tool_name": tool_name})
    return 0


def _handler(entry: Dict[str, Any]) -> bool:
    args = entry.get("args", [])
    return "agentguard.cli" in args and "claude-code" in args


def install_settings(settings: Dict[str, Any], python: str, max_calls: Optional[int]) -> Dict[str, Any]:
    """Return settings with the AgentGuard handler on each event, keeping other hooks."""
    settings = uninstall_settings(settings)
    args = HOOK_ARGS + ([] if max_calls is None else ["--max-calls", str(max_calls)])
    hooks = settings.setdefault("hooks", {})
    for name in EVENTS:
        hooks.setdefault(name, []).append({
            "matcher": "*",
            "hooks": [{"type": "command", "command": python, "args": args, "timeout": 10}],
        })
    return settings


def uninstall_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Remove only AgentGuard handlers; drop groups and events left empty."""
    hooks = settings.get("hooks", {})
    for name in list(hooks):
        groups: List[Dict[str, Any]] = []
        for group in hooks[name]:
            kept = [h for h in group.get("hooks", []) if not _handler(h)]
            if kept:
                groups.append({**group, "hooks": kept})
        if groups:
            hooks[name] = groups
        else:
            del hooks[name]
    if "hooks" in settings and not hooks:
        del settings["hooks"]
    return settings


def configure(project_dir: str, write: bool, remove: bool, max_calls: Optional[int],
              out: TextIO) -> int:
    path = Path(project_dir) / SETTINGS_FILE
    current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    updated = (uninstall_settings(current) if remove
               else install_settings(current, sys.executable, max_calls))
    text = json.dumps(updated, indent=2) + "\n"
    if not write:
        out.write(f"# Preview of {path}. Add --write to save it.\n{text}")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    action = "Removed AgentGuard hooks from" if remove else "Wrote AgentGuard hooks to"
    out.write(f"{action} {path}\n")
    if not remove:
        out.write(f"Refusals are logged to {Path(project_dir) / '.agentguard' / TRACE_FILE}\n")
    return 0
