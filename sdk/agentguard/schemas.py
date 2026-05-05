"""Typed contracts for the agentguard47 public surface.

Per "AI rewards strict APIs" — these dataclasses give agents and humans a
single importable schema for the SDK's main configuration and policy shapes.
They use only the standard library (frozen dataclasses + typing) so they do
not violate AgentGuard's zero-dependency guarantee.

Public schemas:

- ``InitConfig``    — keyword arguments accepted by ``agentguard.init()``.
- ``RepoConfig``    — schema for ``.agentguard.json`` repo-local defaults.
- ``ProfileDefaults`` — guard policy shape for a built-in profile.

Each schema has a ``validate()`` method that raises ``ValueError`` on bad
input. Validation rules mirror the runtime checks already enforced by
``agentguard.init()`` and ``agentguard.repo_config`` — these classes simply
expose the contract so agents can introspect it without scraping prose.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Dict, Optional

# Import the canonical profile names so the schema stays in sync.
from agentguard.profiles import (
    _PROFILE_DEFAULTS,
    normalize_profile,
)

SUPPORTED_PROFILES = tuple(sorted(_PROFILE_DEFAULTS.keys()))


@dataclass(frozen=True)
class ProfileDefaults:
    """Guard policy shape for a built-in profile.

    Mirrors the dict returned by ``agentguard.profiles.get_profile_defaults``.
    """

    loop_max: int
    warn_pct: float
    retry_max: Optional[int] = None

    def validate(self) -> None:
        if not isinstance(self.loop_max, int) or self.loop_max < 1:
            raise ValueError(f"loop_max must be a positive int, got {self.loop_max!r}")
        if self.retry_max is not None and (
            not isinstance(self.retry_max, int) or self.retry_max < 0
        ):
            raise ValueError(f"retry_max must be a non-negative int or None, got {self.retry_max!r}")
        if not isinstance(self.warn_pct, (int, float)) or not (0.0 <= float(self.warn_pct) <= 1.0):
            raise ValueError(f"warn_pct must be in [0.0, 1.0], got {self.warn_pct!r}")


@dataclass(frozen=True)
class RepoConfig:
    """Schema for ``.agentguard.json`` repo-local defaults.

    Every field is optional. Unknown keys are tolerated by the runtime loader
    (``agentguard.repo_config.load_repo_config_safely``) but are not part of
    the typed contract.
    """

    service: Optional[str] = None
    trace_file: Optional[str] = None
    budget_usd: Optional[float] = None
    profile: Optional[str] = None
    warn_pct: Optional[float] = None
    loop_max: Optional[int] = None
    retry_max: Optional[int] = None

    def validate(self) -> None:
        if self.service is not None:
            if not isinstance(self.service, str) or not self.service.strip():
                raise ValueError("service must be a non-empty string")
        if self.trace_file is not None:
            if not isinstance(self.trace_file, str) or not self.trace_file.strip():
                raise ValueError("trace_file must be a non-empty string")
        if self.budget_usd is not None:
            if (
                isinstance(self.budget_usd, bool)
                or not isinstance(self.budget_usd, (int, float))
                or self.budget_usd < 0
            ):
                raise ValueError("budget_usd must be a non-negative number")
        if self.profile is not None:
            # normalize_profile raises ValueError for unknown values.
            normalize_profile(self.profile)
        if self.warn_pct is not None:
            if (
                isinstance(self.warn_pct, bool)
                or not isinstance(self.warn_pct, (int, float))
                or not (0.0 <= float(self.warn_pct) <= 1.0)
            ):
                raise ValueError("warn_pct must be in [0.0, 1.0]")
        if self.loop_max is not None:
            if (
                isinstance(self.loop_max, bool)
                or not isinstance(self.loop_max, int)
                or self.loop_max < 1
            ):
                raise ValueError("loop_max must be a positive int")
        if self.retry_max is not None:
            if (
                isinstance(self.retry_max, bool)
                or not isinstance(self.retry_max, int)
                or self.retry_max < 0
            ):
                raise ValueError("retry_max must be a non-negative int")

    def to_dict(self) -> Dict[str, Any]:
        """Return a dict of only the set (non-None) fields."""
        return {f.name: getattr(self, f.name) for f in fields(self) if getattr(self, f.name) is not None}


@dataclass(frozen=True)
class InitConfig:
    """Schema for keyword arguments accepted by ``agentguard.init()``.

    Mirrors the public signature of ``agentguard.init`` exactly. Use this to
    validate config payloads (e.g. from a control plane or a config file)
    before passing them through to ``init``.

    Example::

        from agentguard import InitConfig, init

        cfg = InitConfig(budget_usd=5.00, profile="coding-agent")
        cfg.validate()
        init(**cfg.to_dict())
    """

    api_key: Optional[str] = None
    budget_usd: Optional[float] = None
    service: Optional[str] = None
    session_id: Optional[str] = None
    trace_file: Optional[str] = None
    warn_pct: Optional[float] = None
    loop_max: Optional[int] = None
    retry_max: Optional[int] = None
    profile: Optional[str] = None
    auto_patch: bool = True
    watermark: bool = True
    local_only: bool = False

    def validate(self) -> None:
        if self.warn_pct is not None and not (0.0 <= float(self.warn_pct) <= 1.0):
            raise ValueError(f"warn_pct must be between 0.0 and 1.0, got {self.warn_pct!r}")
        if self.local_only and self.api_key:
            raise ValueError("local_only=True cannot be combined with api_key")
        if self.api_key and ("\n" in self.api_key or "\r" in self.api_key):
            raise ValueError(
                "api_key must not contain newline or carriage return characters "
                "(possible HTTP header injection)"
            )
        if self.budget_usd is not None:
            if (
                isinstance(self.budget_usd, bool)
                or not isinstance(self.budget_usd, (int, float))
                or self.budget_usd < 0
            ):
                raise ValueError("budget_usd must be a non-negative number")
        if self.profile is not None:
            normalize_profile(self.profile)
        if self.loop_max is not None:
            if (
                isinstance(self.loop_max, bool)
                or not isinstance(self.loop_max, int)
                or self.loop_max < 1
            ):
                raise ValueError("loop_max must be a positive int")
        if self.retry_max is not None:
            if (
                isinstance(self.retry_max, bool)
                or not isinstance(self.retry_max, int)
                or self.retry_max < 0
            ):
                raise ValueError("retry_max must be a non-negative int")
        for name in ("service", "session_id", "trace_file"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a non-empty string when set")

    def to_dict(self) -> Dict[str, Any]:
        """Return all fields as a dict suitable for ``init(**cfg.to_dict())``.

        Includes None values so callers can pass through unchanged. Use
        ``to_set_dict`` if you only want explicitly set fields.
        """
        return {f.name: getattr(self, f.name) for f in fields(self)}

    def to_set_dict(self) -> Dict[str, Any]:
        """Return only fields that differ from their defaults."""
        out: Dict[str, Any] = {}
        for f in fields(self):
            default = f.default if f.default is not field else None
            value = getattr(self, f.name)
            if value != default:
                out[f.name] = value
        return out


__all__ = [
    "SUPPORTED_PROFILES",
    "InitConfig",
    "ProfileDefaults",
    "RepoConfig",
]
