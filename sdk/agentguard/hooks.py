"""Claude Code hook: refuse repeated tool calls, retry storms, and runs past a call cap.

Repeats preserve argument case and whitespace while ignoring JSON key order. A tool that
keeps coming back empty or with the same error is refused even when the agent
rewords each call.

Claude Code runs this as a command hook on PreToolUse, PostToolUse, and
PostToolUseFailure. Each invocation is a fresh process, so per-session counts
live in a JsonFileStateStore under ``.agentguard/claude-code/`` in the project,
a directory that ignores itself in git. A refused
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
import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

from agentguard._loop_match import (
    EMPTY,
    advance_streak,
    describe_outcome,
    normalize_args,
    outcome_of,
)
from agentguard.profiles import CODING_AGENT_PROFILE, get_profile_defaults
from agentguard.repo_config import load_repo_config
from agentguard.state import JsonFileStateStore
from agentguard.tracing import JsonlFileSink, Tracer

HOOK_DIR = Path(".agentguard") / "claude-code"
SESSIONS_DIR = "sessions"
TRACE_FILE = "trace.jsonl"
SETTINGS_FILE = Path(".claude") / "settings.local.json"
EVENTS = ("PreToolUse", "PostToolUse", "PostToolUseFailure")
HOOK_ARGS = ["-m", "agentguard.cli", "hook", "claude-code"]
# Bash sends a free-text description that changes between otherwise identical calls.
_IGNORED_INPUT_KEYS = {"description"}
_SESSION_RE = re.compile(r"[^A-Za-z0-9_.-]")
# Empty or same-error results in a row from one tool, with no other result between.
NO_PROGRESS_MAX = 0


class Refusal(Exception):
    """A tool call the hook refuses. The message is shown to the model."""

    def __init__(self, kind: str, message: str, data: Dict[str, Any]) -> None:
        super().__init__(message)
        self.kind = kind
        self.data = data


def _without_ignored(tool_input: Any) -> Any:
    if isinstance(tool_input, dict):
        return {k: v for k, v in tool_input.items() if k not in _IGNORED_INPUT_KEYS}
    return tool_input


def signature(tool_name: str, tool_input: Any) -> str:
    raw = json.dumps([tool_name, normalize_args(_without_ignored(tool_input))],
                     sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def preview(tool_name: str, tool_input: Any) -> str:
    # Refusal messages also persist in JSONL. Even a truncated input or an
    # arbitrary argument key can disclose credentials; keep the tool name only.
    return tool_name


def limits(project_dir: str, max_calls: Optional[int]) -> Dict[str, Any]:
    """Loop and retry caps from .agentguard.json, else the coding-agent profile."""
    _, config = load_repo_config(project_dir)
    defaults = get_profile_defaults(config.get("profile", CODING_AGENT_PROFILE))
    return {
        "loop_max": config.get("loop_max", defaults["loop_max"]),
        "retry_max": config.get("retry_max", defaults["retry_max"]),
        "no_progress_max": config.get("no_progress_max", NO_PROGRESS_MAX),
        "max_calls": max_calls,
    }


def check_and_record(state: Optional[Dict[str, Any]], sig: str, label: str,
                     caps: Dict[str, Any], tool: Optional[str] = None,
                     tool_input: Any = None) -> Dict[str, Any]:
    """PreToolUse: raise Refusal, or return the state with this call recorded."""
    state = state or {"calls": 0, "last": None, "streak": 0, "failures": {}}
    if caps["max_calls"] is not None and state["calls"] >= caps["max_calls"]:
        raise Refusal("budget", f"AgentGuard refused {label}: this session already made "
                      f"{state['calls']} tool calls (limit {caps['max_calls']}). Stop and "
                      "report progress to the user.",
                      {"calls_used": state["calls"], "calls_limit": caps["max_calls"]})
    call = {"tool_name": tool or label}
    streak = state["streak"] + 1 if state["last"] == sig else 1
    if caps["loop_max"] and streak >= caps["loop_max"]:
        raise Refusal("loop", f"AgentGuard refused {label}: the same call just ran "
                      f"{streak - 1} times in a row (limit {caps['loop_max'] - 1}). Change the "
                      "input or the approach.",
                      {**call, "repeats": streak - 1, "limit": caps["loop_max"] - 1})
    failures = state["failures"].get(sig, 0)
    if caps["retry_max"] and failures >= caps["retry_max"]:
        raise Refusal("retry", f"AgentGuard refused {label}: the same call already failed "
                      f"{failures} times (limit {caps['retry_max']}). Diagnose the failure "
                      "before trying again.",
                      {**call, "failures": failures, "limit": caps["retry_max"]})
    stall = state.get("stall")
    limit = caps.get("no_progress_max")
    if limit and tool and stall and stall["tool"] == tool and stall["count"] >= limit:
        raise Refusal("loop", f"AgentGuard refused {label}: {tool} "
                      f"{describe_outcome(stall['outcome'])} the last "
                      f"{stall['count']} times in a row, even with changed input (limit "
                      f"{limit}). Rewording the call is not working; try a different approach "
                      "or report to the user.",
                      {**call, "rule": "no_progress", "results": stall["count"], "limit": limit,
                       "outcome": "empty" if stall["outcome"] == EMPTY else "same error"})
    state.update(calls=state["calls"] + 1, last=sig, streak=streak)
    return state


def record_result(state: Optional[Dict[str, Any]], sig: str, failed: bool,
                  tool: Optional[str] = None, outcome: Optional[str] = None) -> Dict[str, Any]:
    """PostToolUse / PostToolUseFailure: count failures per call and the no-progress run."""
    state = state or {"calls": 0, "last": None, "streak": 0, "failures": {}}
    if failed:
        state["failures"][sig] = state["failures"].get(sig, 0) + 1
    else:
        state["failures"].pop(sig, None)
    if tool is not None:
        state["stall"] = advance_streak(state.get("stall"), tool, outcome)
    return state


def _outcome(event: Dict[str, Any]) -> Optional[str]:
    tool_input = _without_ignored(event.get("tool_input"))
    if event["hook_event_name"] == "PostToolUseFailure":
        # A user interrupt says nothing about whether the tool is stuck.
        if event.get("is_interrupt"):
            return None
        outcome = outcome_of(error=event.get("error") or "failed", args=tool_input)
        # Only equality is needed across hook processes. Error text can contain
        # private input even after normalization, so persist its digest only.
        return hashlib.sha256(outcome.encode("utf-8")).hexdigest() if outcome else None
    if "tool_response" not in event:
        return None
    return outcome_of(event["tool_response"], args=tool_input)


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
        # Installed PreToolUse handlers set onFailure=block on supported hosts,
        # so an unreadable event is a blocking hook failure rather than an allow.
        stderr.write(f"agentguard hook: unreadable hook input ({exc})\n")
        return 1
    if name not in EVENTS:
        return 0
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    root = Path(project_dir) / HOOK_DIR
    root.mkdir(parents=True, exist_ok=True)
    # Session state and command snippets are machine-local; keep them out of git.
    ignore = root / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")
    # One small file per session: a hook call reads only its own counts.
    store = JsonFileStateStore(root / SESSIONS_DIR / f"{session}.json")
    tool_input = event.get("tool_input")
    sig = signature(tool_name, tool_input)
    if name != "PreToolUse":
        outcome = _outcome(event)
        store.update(session, lambda s: record_result(s, sig, name == "PostToolUseFailure",
                                                      tool_name, outcome))
        return 0
    label = preview(tool_name, tool_input)
    caps = limits(project_dir, max_calls)
    tracer = Tracer(sink=JsonlFileSink(str(root / TRACE_FILE)), service="claude-code",
                    watermark=False)
    try:
        store.update(session, lambda s: check_and_record(s, sig, label, caps, tool_name, tool_input))
    except Refusal as refusal:
        with tracer.trace("claude_code.tool_call", data={"session": session}) as ctx:
            ctx.event(_GUARD_EVENTS[refusal.kind], data={**refusal.data, "message": str(refusal)})
        stderr.write(f"{refusal}\n")
        return 2
    with tracer.trace("claude_code.tool_call", data={"session": session}) as ctx:
        ctx.event("tool.call", data={"tool_name": tool_name})
    return 0


def _handler(entry: Dict[str, Any]) -> bool:
    # Ours start with exactly HOOK_ARGS; --max-calls may follow.
    return entry.get("args", [])[: len(HOOK_ARGS)] == HOOK_ARGS


def install_settings(settings: Dict[str, Any], python: str, max_calls: Optional[int]) -> Dict[str, Any]:
    """Add the AgentGuard handler to each event, keeping other hooks. Modifies and returns settings."""
    settings = uninstall_settings(settings)
    args = HOOK_ARGS + ([] if max_calls is None else ["--max-calls", str(max_calls)])
    hooks = settings.setdefault("hooks", {})
    for name in EVENTS:
        handler = {"type": "command", "command": python, "args": args, "timeout": 10}
        if name == "PreToolUse":
            handler["onFailure"] = "block"
        hooks.setdefault(name, []).append({
            "matcher": "*",
            "hooks": [handler],
        })
    return settings


def uninstall_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Remove only AgentGuard handlers; drop groups and events left empty. Modifies and returns settings."""
    hooks = settings.get("hooks", {})
    removed_any = False
    for name in list(hooks):
        groups: List[Dict[str, Any]] = []
        removed = False
        for group in hooks[name]:
            kept = [h for h in group.get("hooks", []) if not _handler(h)]
            if len(kept) == len(group.get("hooks", [])):
                groups.append(group)
                continue
            removed = True
            removed_any = True
            if kept:
                groups.append({**group, "hooks": kept})
        if groups:
            hooks[name] = groups
        elif removed:
            del hooks[name]
    if removed_any and not hooks:
        del settings["hooks"]
    return settings


def _require_supported_claude() -> str:
    """Fail before installation when the host cannot enforce onFailure=block."""
    requirement = ("AgentGuard hook installation requires Claude Code 2.1.295 or later "
                   "with onFailure support. No settings were changed.")
    executable = shutil.which("claude")
    if executable is None:
        raise SystemExit(f"{requirement} Could not find claude on PATH.")
    try:
        # Resolve the host exactly as its CLI invocation would; neither the
        # command name nor arguments come from hook payloads or project config.
        result = subprocess.run(  # nosec B603
            [executable, "--version"], capture_output=True, text=True, timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit(f"{requirement} Could not verify claude --version ({exc}).") from exc
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+) \(Claude Code\)", result.stdout.strip())
    if result.returncode != 0 or match is None:
        raise SystemExit(f"{requirement} claude --version did not return a supported version.")
    if tuple(int(part) for part in match.groups()) < (2, 1, 295):
        raise SystemExit(f"{requirement} Detected {result.stdout.strip()}.")
    return ".".join(match.groups())


def configure(project_dir: str, write: bool, remove: bool, max_calls: Optional[int],
              out: TextIO) -> int:
    path = Path(project_dir) / SETTINGS_FILE
    try:
        current = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path} is not valid JSON ({exc}). Fix it, then run this again.") from exc
    version = None if remove else _require_supported_claude()
    updated = (uninstall_settings(current) if remove
               else install_settings(current, sys.executable, max_calls))
    text = json.dumps(updated, indent=2) + "\n"
    if version is not None:
        out.write(f"# Verified Claude Code {version}; PreToolUse blocks hook failures.\n")
    if not write:
        out.write(f"# Preview of {path}. Add --write to save it.\n{text}")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    # Claude Code reads this file on every tool call; never leave it half-written.
    tmp = path.with_name(path.name + ".agentguard.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    action = "Removed AgentGuard hooks from" if remove else "Wrote AgentGuard hooks to"
    out.write(f"{action} {path}\n")
    if not remove:
        out.write(f"Refusals are logged to {Path(project_dir) / HOOK_DIR / TRACE_FILE}\n")
        out.write(f"{SETTINGS_FILE} holds this machine's Python path; keep it out of git.\n")
    return 0
