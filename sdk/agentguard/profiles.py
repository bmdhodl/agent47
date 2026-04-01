from __future__ import annotations

from typing import Any, Dict, Optional

DEFAULT_PROFILE = "default"
CODING_AGENT_PROFILE = "coding-agent"

_PROFILE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    DEFAULT_PROFILE: {
        "loop_max": 5,
        "retry_max": None,
        "warn_pct": 0.8,
    },
    CODING_AGENT_PROFILE: {
        "loop_max": 3,
        "retry_max": 2,
        "warn_pct": 0.8,
    },
}


def normalize_profile(profile: Optional[str]) -> str:
    """Return a canonical profile name or raise for unknown values."""
    normalized = (profile or DEFAULT_PROFILE).strip().lower()
    if normalized not in _PROFILE_DEFAULTS:
        supported = ", ".join(sorted(_PROFILE_DEFAULTS))
        raise ValueError(f"Unknown AgentGuard profile '{profile}'. Supported profiles: {supported}")
    return normalized


def get_profile_defaults(profile: Optional[str]) -> Dict[str, Any]:
    """Return a copy of the defaults for a known profile."""
    normalized = normalize_profile(profile)
    return dict(_PROFILE_DEFAULTS[normalized])
