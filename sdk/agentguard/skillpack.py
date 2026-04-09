from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, TextIO, Tuple

TARGET_CHOICES: Tuple[str, ...] = (
    "all",
    "codex",
    "claude-code",
    "copilot",
    "cursor",
)

_TARGET_PATHS: Dict[str, str] = {
    "codex": "AGENTS.md",
    "claude-code": "CLAUDE.md",
    "copilot": ".github/copilot-instructions.md",
    "cursor": ".cursor/rules/agentguard.mdc",
}

_TARGET_LABELS: Dict[str, str] = {
    "codex": "Codex / AGENTS",
    "claude-code": "Claude Code / CLAUDE",
    "copilot": "GitHub Copilot / copilot-instructions",
    "cursor": "Cursor rule",
}


def run_skillpack(
    target: str = "all",
    service: str = "my-agent",
    budget_usd: float = 5.0,
    trace_file: str = ".agentguard/traces.jsonl",
    stream: Optional[TextIO] = None,
    json_output: bool = False,
    write_files: bool = False,
    output_dir: Optional[str] = None,
    force: bool = False,
) -> int:
    """Render or write repo-local coding-agent instruction files."""
    out = stream or sys.stdout
    normalized = target.strip().lower()

    try:
        payload = _build_skillpack_payload(
            target=normalized,
            service=service,
            budget_usd=budget_usd,
            trace_file=trace_file,
        )
    except ValueError as exc:
        error = {
            "status": "error",
            "error": str(exc),
            "targets": list(TARGET_CHOICES),
        }
        if json_output:
            out.write(json.dumps(error) + "\n")
        else:
            _print(out, "AgentGuard skillpack")
            _print(out, f"[fail] {exc}")
            _print(out, f"Available targets: {', '.join(TARGET_CHOICES)}")
        return 1

    if write_files:
        try:
            written_files = _write_skillpack_files(
                payload["files"],
                output_dir=output_dir,
                force=force,
            )
        except (ValueError, OSError) as exc:
            error = {
                "status": "error",
                "error": str(exc),
                "target": normalized,
            }
            if json_output:
                out.write(json.dumps(error) + "\n")
            else:
                _print(out, "AgentGuard skillpack")
                _print(out, f"[fail] {exc}")
            return 1
        payload["written_files"] = written_files
        payload["output_dir"] = (output_dir or "agentguard_skillpack").replace("\\", "/")

    if json_output:
        out.write(json.dumps(payload) + "\n")
        return 0

    if write_files:
        _render_written_text(payload, out)
    else:
        _render_text(payload, out)
    return 0


def _build_skillpack_payload(
    *,
    target: str,
    service: str,
    budget_usd: float,
    trace_file: str,
) -> Dict[str, Any]:
    service = _validate_service(service)
    budget_usd = _validate_budget_usd(budget_usd)
    trace_file = _validate_trace_file(trace_file)
    selected_targets = _selected_targets(target)
    files = [_repo_config_entry(service, budget_usd, trace_file)]
    files.extend(_target_entry(name, trace_file) for name in selected_targets)
    return {
        "status": "ok",
        "target": target,
        "targets": selected_targets,
        "service": service,
        "budget_usd": round(budget_usd, 2),
        "trace_file": trace_file,
        "files": files,
        "summary": (
            "Repo-local instruction pack for coding agents. Keep the first AgentGuard "
            "integration local, auditable, and free of hosted settings."
        ),
        "notes": [
            "The generated .agentguard.json stays local-first: no API keys, no dashboard URL, no secrets.",
            "Each instruction file points agents at agentguard doctor, quickstart --write, and a local report run.",
            "Use --output-dir . only if you intentionally want to materialize these files directly into a repo.",
        ],
        "next_commands": [
            "agentguard doctor",
            "agentguard quickstart --framework raw --write",
            "python agentguard_raw_quickstart.py",
            f"agentguard report {trace_file}",
        ],
    }


def _selected_targets(target: str) -> List[str]:
    if target not in TARGET_CHOICES:
        raise ValueError(f"Unknown target '{target}'")
    if target == "all":
        return [name for name in TARGET_CHOICES if name != "all"]
    return [target]


def _validate_service(service: str) -> str:
    if not isinstance(service, str) or not service.strip():
        raise ValueError("service must be a non-empty string")
    return service.strip()


def _validate_budget_usd(budget_usd: float) -> float:
    if isinstance(budget_usd, bool) or not isinstance(budget_usd, (int, float)) or budget_usd < 0:
        raise ValueError("budget_usd must be a non-negative number")
    return float(budget_usd)


def _validate_trace_file(trace_file: str) -> str:
    if not isinstance(trace_file, str) or not trace_file.strip():
        raise ValueError("trace_file must be a non-empty string")
    return trace_file.strip()


def _repo_config_entry(service: str, budget_usd: float, trace_file: str) -> Dict[str, str]:
    config = {
        "profile": "coding-agent",
        "service": service,
        "trace_file": trace_file,
        "budget_usd": round(budget_usd, 2),
    }
    content = json.dumps(config, indent=2) + "\n"
    return {
        "target": "repo-config",
        "label": "Repo-local defaults",
        "path": ".agentguard.json",
        "description": "Shared local defaults for humans and coding agents.",
        "content": content,
    }


def _target_entry(target: str, trace_file: str) -> Dict[str, str]:
    return {
        "target": target,
        "label": _TARGET_LABELS[target],
        "path": _TARGET_PATHS[target],
        "description": "Agent-specific instructions for a local-first AgentGuard rollout.",
        "content": _target_content(target, trace_file),
    }


def _target_content(target: str, trace_file: str) -> str:
    if target == "codex":
        content = f"""
        Use AgentGuard in local-only mode first.

        - Respect the repo's `.agentguard.json`
        - Keep traces in `{trace_file}`
        - Prefer `agentguard.init(local_only=True)` for the first integration
        - Do not add API keys or hosted dashboard settings in the first PR
        - Verify with:
          1. `agentguard doctor`
          2. `agentguard quickstart --framework raw --write`
          3. `python agentguard_raw_quickstart.py`
          4. `agentguard report {trace_file}`
        """
    elif target == "claude-code":
        content = f"""
        When integrating AgentGuard:

        - start local-only
        - respect the repo's `.agentguard.json`
        - keep traces in `{trace_file}`
        - prefer `agentguard.init(local_only=True)` on the first pass
        - do not add API keys or dashboard settings in the first PR
        - prove the wiring with:
          1. `agentguard doctor`
          2. `agentguard quickstart --framework raw --write`
          3. `python agentguard_raw_quickstart.py`
          4. `agentguard report {trace_file}`
        """
    elif target == "copilot":
        content = f"""
        If you touch AI-agent code, keep AgentGuard local-first:

        - use the repo's `.agentguard.json` if present
        - keep traces in `{trace_file}`
        - prefer `agentguard.init(local_only=True)` during first integration
        - avoid adding secrets, API keys, or hosted settings in the first PR
        - verify with `agentguard doctor`, `agentguard quickstart --framework raw --write`, and `agentguard report {trace_file}`
        """
    elif target == "cursor":
        content = f"""
        ---
        description: AgentGuard local-first safety
        globs:
          - "**/*.py"
        alwaysApply: false
        ---

        When integrating AgentGuard:
        - keep the first run local
        - honor the repo's `.agentguard.json`
        - keep traces in `{trace_file}`
        - prefer `agentguard.init(local_only=True)`
        - do not add API keys or hosted settings in the first PR
        - verify with:
          1. `agentguard doctor`
          2. `agentguard quickstart --framework raw --write`
          3. `python agentguard_raw_quickstart.py`
          4. `agentguard report {trace_file}`
        """
    else:  # pragma: no cover
        raise ValueError(f"Unknown target '{target}'")

    return dedent(content).strip() + "\n"


def _write_skillpack_files(
    files: List[Dict[str, str]],
    *,
    output_dir: Optional[str],
    force: bool,
) -> List[str]:
    base_dir = Path(output_dir or "agentguard_skillpack")
    written: List[str] = []
    for file_payload in files:
        destination = base_dir / Path(file_payload["path"])
        if destination.exists() and not force:
            raise ValueError(
                f"Refusing to overwrite existing file: {destination.as_posix()}. Re-run with --force."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(file_payload["content"], encoding="utf-8")
        written.append(destination.as_posix())
    return written


def _render_text(payload: Dict[str, Any], out: TextIO) -> None:
    _print(out, "AgentGuard skillpack")
    _print(out, f"Target: {payload['target']}")
    _print(out, "")
    _print(out, payload["summary"])
    _print(out, "")
    for file_payload in payload["files"]:
        _print(out, f"{file_payload['label']}")
        _print(out, f"Suggested path: {file_payload['path']}")
        _print(out, "")
        _print(out, file_payload["content"].rstrip())
        _print(out, "")
    _print(out, "Next commands:")
    for command in payload["next_commands"]:
        _print(out, f"  {command}")


def _render_written_text(payload: Dict[str, Any], out: TextIO) -> None:
    _print(out, "AgentGuard skillpack")
    _print(out, f"Target: {payload['target']}")
    _print(out, f"Output dir: {payload['output_dir']}")
    _print(out, "")
    _print(out, "Wrote files:")
    for path in payload["written_files"]:
        _print(out, f"  {path}")
    _print(out, "")
    _print(out, "Next commands:")
    for command in payload["next_commands"]:
        _print(out, f"  {command}")
    _print(out, "")
    _print(out, "Notes:")
    for note in payload["notes"]:
        _print(out, f"  - {note}")


def _print(stream: TextIO, line: str) -> None:
    stream.write(line + "\n")
