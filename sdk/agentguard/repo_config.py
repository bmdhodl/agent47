from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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

    with open(config_path, encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        raise ValueError(f"{CONFIG_FILE_NAME} must contain a JSON object")

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
        if not isinstance(budget_usd, (int, float)) or budget_usd < 0:
            raise ValueError("budget_usd in .agentguard.json must be a non-negative number")
        parsed["budget_usd"] = float(budget_usd)

    return config_path, parsed
