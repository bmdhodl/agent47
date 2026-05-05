from __future__ import annotations

from typing import Any, Dict, Optional

DEFAULT_PROFILE = "default"
CODING_AGENT_PROFILE = "coding-agent"
DEPLOYED_AGENT_PROFILE = "deployed-agent"

# The ``deployed-agent`` profile tightens guard defaults for agents that run
# unattended in production. Motivated by arxiv:2605.00055, which documents a
# deployed agent that installed 107 unauthorized components and overrode its
# own oversight gate under ambient persuasion. Tighter loop/retry caps and an
# earlier budget warning give operators a chance to intervene before drift
# compounds. This preset uses only the guard primitives AgentGuard already
# enforces; it does not add install-count, registry-write, or oversight
# immutability guards (those would require new guard classes).
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
    DEPLOYED_AGENT_PROFILE: {
        "loop_max": 2,
        "retry_max": 1,
        "warn_pct": 0.5,
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
