from __future__ import annotations

import json
import os
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from agentguard.profiles import normalize_profile

CONFIG_FILE_NAME = ".agentguard.json"


def find_repo_config(start_path: Optional[str] = None) -> Optional[str]:
    """Find the nearest repo-local AgentGuard config file."""
    current = Path(start_path or os.getcwd()).resolve()
    if current.is_file():
        current = current.parent

    for directory in (current, *current.parents):
        candidate = directory / CONFIG_FILE_NAME
        if candidate.is_file():
            return str(candidate)
    return None


def load_repo_config(start_path: Optional[str] = None) -> Tuple[Optional[str], Dict[str, Any]]:
    """Load supported AgentGuard defaults from the nearest repo config file."""
    config_path = find_repo_config(start_path)
    if not config_path:
        return None, {}

    try:
        with open(config_path, encoding="utf-8") as handle:
            raw = json.load(handle)
    except JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {config_path}: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"Could not read {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"{config_path} must contain a JSON object")

    config_dir = os.path.dirname(config_path)
    parsed: Dict[str, Any] = {}

    service = raw.get("service")
    if service is not None:
        if not isinstance(service, str) or not service.strip():
            raise ValueError("service in .agentguard.json must be a non-empty string")
        parsed["service"] = service.strip()

    trace_file = raw.get("trace_file")
    if trace_file is not None:
        if not isinstance(trace_file, str) or not trace_file.strip():
            raise ValueError("trace_file in .agentguard.json must be a non-empty string")
        normalized_trace = trace_file.strip()
        if not os.path.isabs(normalized_trace):
            normalized_trace = os.path.normpath(os.path.join(config_dir, normalized_trace))
        parsed["trace_file"] = normalized_trace

    budget_usd = raw.get("budget_usd")
    if budget_usd is not None:
        if isinstance(budget_usd, bool) or not isinstance(budget_usd, (int, float)) or budget_usd < 0:
            raise ValueError("budget_usd in .agentguard.json must be a non-negative number")
        parsed["budget_usd"] = float(budget_usd)

    profile = raw.get("profile")
    if profile is not None:
        if not isinstance(profile, str) or not profile.strip():
            raise ValueError("profile in .agentguard.json must be a non-empty string")
        parsed["profile"] = normalize_profile(profile)

    warn_pct = raw.get("warn_pct")
    if warn_pct is not None:
        if (
            isinstance(warn_pct, bool)
            or not isinstance(warn_pct, (int, float))
            or not (0.0 <= float(warn_pct) <= 1.0)
        ):
            raise ValueError("warn_pct in .agentguard.json must be between 0.0 and 1.0")
        parsed["warn_pct"] = float(warn_pct)

    loop_max = raw.get("loop_max")
    if loop_max is not None:
        if isinstance(loop_max, bool) or not isinstance(loop_max, int) or loop_max < 2:
            raise ValueError("loop_max in .agentguard.json must be an integer >= 2")
        parsed["loop_max"] = loop_max

    retry_max = raw.get("retry_max")
    if retry_max is not None:
        if isinstance(retry_max, bool) or not isinstance(retry_max, int) or retry_max < 1:
            raise ValueError("retry_max in .agentguard.json must be an integer >= 1")
        parsed["retry_max"] = retry_max

    return config_path, parsed


def load_repo_config_safely(
    start_path: Optional[str] = None,
) -> Tuple[Optional[str], Dict[str, Any], Optional[str]]:
    """Load repo config without raising for malformed local defaults."""
    config_path = find_repo_config(start_path)
    if not config_path:
        return None, {}, None

    try:
        _, parsed = load_repo_config(start_path)
        return config_path, parsed, None
    except ValueError as exc:
        return config_path, {}, str(exc)
