"""Advisor-style model escalation primitives for hard turns."""
from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

from .guards import AgentGuardError, BaseGuard


class EscalationRequired(AgentGuardError, RuntimeError):
    """Raised when a run should switch to a stronger model for the next call."""

    def __init__(
        self,
        target_model: str,
        reason: str,
        signal_name: str,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.target_model = target_model
        self.reason = reason
        self.signal_name = signal_name
        self.metrics = metrics or {}
        super().__init__(
            f"Escalation required: switch to {target_model} ({signal_name}: {reason})"
        )


@dataclass(frozen=True)
class EscalationSignal:
    """A declarative trigger that can arm or require model escalation.

    Use the constructor helpers to build supported signal types::

        EscalationSignal.TOKEN_COUNT(threshold=2000)
        EscalationSignal.CONFIDENCE_BELOW(threshold=0.45)
        EscalationSignal.TOOL_CALL_DEPTH(threshold=3)
        EscalationSignal.CUSTOM(lambda ctx: ctx["token_count"] > 1000, name="custom")
    """

    kind: str
    threshold: Optional[float] = None
    rule: Optional[Callable[[Dict[str, Any]], bool]] = None
    name: Optional[str] = None

    @classmethod
    def TOKEN_COUNT(cls, threshold: int) -> "EscalationSignal":
        """Trigger when the current turn uses more than ``threshold`` tokens."""
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        return cls(kind="token_count", threshold=float(threshold), name="token_count")

    @classmethod
    def token_count(cls, threshold: int) -> "EscalationSignal":
        """Alias for ``TOKEN_COUNT``."""
        return cls.TOKEN_COUNT(threshold)

    @classmethod
    def CONFIDENCE_BELOW(cls, threshold: float) -> "EscalationSignal":
        """Trigger when normalized confidence drops below ``threshold``."""
        if threshold < 0 or threshold > 1:
            raise ValueError("threshold must be between 0 and 1")
        return cls(kind="confidence_below", threshold=float(threshold), name="confidence_below")

    @classmethod
    def confidence_below(cls, threshold: float) -> "EscalationSignal":
        """Alias for ``CONFIDENCE_BELOW``."""
        return cls.CONFIDENCE_BELOW(threshold)

    @classmethod
    def TOOL_CALL_DEPTH(cls, threshold: int) -> "EscalationSignal":
        """Trigger when tool-call depth exceeds ``threshold``."""
        if threshold < 1:
            raise ValueError("threshold must be >= 1")
        return cls(kind="tool_call_depth", threshold=float(threshold), name="tool_call_depth")

    @classmethod
    def tool_call_depth(cls, threshold: int) -> "EscalationSignal":
        """Alias for ``TOOL_CALL_DEPTH``."""
        return cls.TOOL_CALL_DEPTH(threshold)

    @classmethod
    def CUSTOM(
        cls,
        rule: Callable[[Dict[str, Any]], bool],
        *,
        name: str = "custom_rule",
    ) -> "EscalationSignal":
        """Trigger when ``rule(context)`` returns ``True``."""
        if not callable(rule):
            raise TypeError("rule must be callable")
        if not name:
            raise ValueError("name must be a non-empty string")
        return cls(kind="custom", rule=rule, name=name)

    @classmethod
    def custom(
        cls,
        rule: Callable[[Dict[str, Any]], bool],
        *,
        name: str = "custom_rule",
    ) -> "EscalationSignal":
        """Alias for ``CUSTOM``."""
        return cls.CUSTOM(rule, name=name)


@dataclass(frozen=True)
class _EscalationMatch:
    signal_name: str
    reason: str
    metrics: Dict[str, Any]


class BudgetAwareEscalation(BaseGuard):
    """Route hard turns to a stronger model without baking provider logic into the SDK.

    The guard can be used in two ways:

    - call ``select_model(...)`` before the next model invocation
    - call ``check(...)`` and catch ``EscalationRequired`` to switch models

    It also supports the normal AgentGuard auto-check path. If an emitted event
    contains matching metrics, the guard arms an escalation for the next call.

    Usage::

        guard = BudgetAwareEscalation(
            primary_model="ollama/llama3.1:8b",
            escalate_model="claude-opus-4-6",
            escalate_on=EscalationSignal.TOKEN_COUNT(threshold=2000),
        )

        selected = guard.select_model(token_count=1800)
        assert selected == "ollama/llama3.1:8b"

        guard.auto_check(
            "llm.result",
            {"model": "ollama/llama3.1:8b", "usage": {"total_tokens": 2400}},
        )
        selected = guard.select_model()
        assert selected == "claude-opus-4-6"
    """

    def __init__(
        self,
        primary_model: str,
        escalate_model: str,
        escalate_on: "EscalationSignal | Tuple[EscalationSignal, ...] | list[EscalationSignal]",
    ) -> None:
        if not isinstance(primary_model, str) or not primary_model.strip():
            raise ValueError("primary_model must be a non-empty string")
        if not isinstance(escalate_model, str) or not escalate_model.strip():
            raise ValueError("escalate_model must be a non-empty string")
        if primary_model == escalate_model:
            raise ValueError("primary_model and escalate_model must differ")

        signals: Tuple[EscalationSignal, ...]
        if isinstance(escalate_on, EscalationSignal):
            signals = (escalate_on,)
        elif isinstance(escalate_on, (list, tuple)):
            signals = tuple(escalate_on)
        else:
            raise TypeError("escalate_on must be an EscalationSignal or a sequence of them")
        if not signals:
            raise ValueError("Provide at least one EscalationSignal")
        if not all(isinstance(signal, EscalationSignal) for signal in signals):
            raise TypeError("All escalate_on entries must be EscalationSignal instances")

        self._primary_model = primary_model
        self._escalate_model = escalate_model
        self._signals = signals
        self._lock = threading.Lock()
        self._pending_match: Optional[_EscalationMatch] = None
        self._last_reason: Optional[str] = None
        self._last_signal_name: Optional[str] = None

    @property
    def primary_model(self) -> str:
        """The default cheaper model used when no signal has triggered."""
        return self._primary_model

    @property
    def escalate_model(self) -> str:
        """The stronger model selected when escalation is required."""
        return self._escalate_model

    @property
    def last_reason(self) -> Optional[str]:
        """The most recent escalation reason, if any."""
        with self._lock:
            return self._last_reason

    @property
    def last_signal_name(self) -> Optional[str]:
        """The most recent triggering signal name, if any."""
        with self._lock:
            return self._last_signal_name

    def check(
        self,
        event_name: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        **overrides: Any,
    ) -> None:
        """Raise ``EscalationRequired`` when the next or current call should escalate."""
        match = self._consume_pending_match()
        if match is None:
            context = self._build_context(event_name, event_data, overrides)
            match = self._match_context(context)
        if match is None:
            self._record_last_match(None)
            return

        self._record_last_match(match)
        raise EscalationRequired(
            target_model=self._escalate_model,
            reason=match.reason,
            signal_name=match.signal_name,
            metrics=match.metrics,
        )

    def select_model(
        self,
        event_name: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        **overrides: Any,
    ) -> str:
        """Return the model to use for the next call."""
        try:
            self.check(event_name, event_data, **overrides)
        except EscalationRequired:
            return self._escalate_model
        return self._primary_model

    def auto_check(self, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Arm the next call when observed trace data crosses a configured signal."""
        context = self._build_context(event_name, event_data, {})
        current_model = context.get("current_model")
        if current_model == self._escalate_model:
            return
        match = self._match_context(context)
        if match is None:
            return
        with self._lock:
            self._pending_match = match

    def reset(self) -> None:
        """Clear pending and historical escalation state."""
        with self._lock:
            self._pending_match = None
            self._last_reason = None
            self._last_signal_name = None

    def __repr__(self) -> str:
        return (
            "BudgetAwareEscalation("
            f"primary_model={self._primary_model!r}, "
            f"escalate_model={self._escalate_model!r}, "
            f"signals={len(self._signals)})"
        )

    def _consume_pending_match(self) -> Optional[_EscalationMatch]:
        with self._lock:
            match = self._pending_match
            self._pending_match = None
            return match

    def _record_last_match(self, match: Optional[_EscalationMatch]) -> None:
        with self._lock:
            if match is None:
                self._last_reason = None
                self._last_signal_name = None
            else:
                self._last_reason = match.reason
                self._last_signal_name = match.signal_name

    def _build_context(
        self,
        event_name: Optional[str],
        event_data: Optional[Dict[str, Any]],
        overrides: Dict[str, Any],
    ) -> Dict[str, Any]:
        data = event_data or {}
        token_count = _extract_metric_number(overrides, "token_count")
        if token_count is None:
            token_count = _extract_metric_number(data, "token_count")
        if token_count is None:
            token_count = _extract_nested_metric_number(data, ("usage", "total_tokens"))
        if token_count is None:
            token_count = _extract_metric_number(data, "total_tokens")

        confidence = _extract_metric_number(overrides, "confidence")
        if confidence is None:
            confidence = _extract_metric_number(data, "confidence")
        if confidence is None:
            confidence = _extract_metric_number(data, "confidence_score")

        tool_call_depth = _extract_metric_number(overrides, "tool_call_depth")
        if tool_call_depth is None:
            tool_call_depth = _extract_metric_number(data, "tool_call_depth")
        if tool_call_depth is None:
            tool_call_depth = _extract_metric_number(data, "depth")
        if tool_call_depth is None:
            tool_calls = data.get("tool_calls")
            if isinstance(tool_calls, list):
                tool_call_depth = float(len(tool_calls))

        current_model = overrides.get("current_model")
        if not isinstance(current_model, str) or not current_model:
            model = data.get("model")
            current_model = model if isinstance(model, str) and model else None

        context = {
            "event_name": event_name,
            "event_data": data,
            "primary_model": self._primary_model,
            "escalate_model": self._escalate_model,
            "current_model": current_model,
            "token_count": token_count,
            "confidence": confidence,
            "tool_call_depth": tool_call_depth,
        }
        for key, value in overrides.items():
            if key in {"token_count", "confidence", "tool_call_depth", "current_model"} and value is None:
                continue
            context[key] = value
        return context

    def _match_context(self, context: Dict[str, Any]) -> Optional[_EscalationMatch]:
        for signal in self._signals:
            match = self._match_signal(signal, context)
            if match is not None:
                return match
        return None

    def _match_signal(
        self,
        signal: EscalationSignal,
        context: Dict[str, Any],
    ) -> Optional[_EscalationMatch]:
        if signal.kind == "token_count":
            token_count = context.get("token_count")
            threshold = signal.threshold
            if isinstance(token_count, (int, float)) and threshold is not None and token_count > threshold:
                return _EscalationMatch(
                    signal_name=signal.name or "token_count",
                    reason=f"token_count {int(token_count)} exceeded {int(threshold)}",
                    metrics={"token_count": int(token_count)},
                )
            return None

        if signal.kind == "confidence_below":
            confidence = context.get("confidence")
            threshold = signal.threshold
            if isinstance(confidence, (int, float)) and threshold is not None and confidence < threshold:
                return _EscalationMatch(
                    signal_name=signal.name or "confidence_below",
                    reason=f"confidence {confidence:.3f} fell below {threshold:.3f}",
                    metrics={"confidence": float(confidence)},
                )
            return None

        if signal.kind == "tool_call_depth":
            tool_call_depth = context.get("tool_call_depth")
            threshold = signal.threshold
            if (
                isinstance(tool_call_depth, (int, float))
                and threshold is not None
                and tool_call_depth > threshold
            ):
                return _EscalationMatch(
                    signal_name=signal.name or "tool_call_depth",
                    reason=f"tool_call_depth {int(tool_call_depth)} exceeded {int(threshold)}",
                    metrics={"tool_call_depth": int(tool_call_depth)},
                )
            return None

        if signal.kind == "custom" and signal.rule is not None:
            if signal.rule(context):
                metrics = {}
                for key in ("token_count", "confidence", "tool_call_depth", "current_model"):
                    if context.get(key) is not None:
                        metrics[key] = context[key]
                return _EscalationMatch(
                    signal_name=signal.name or "custom_rule",
                    reason=f"custom rule '{signal.name or 'custom_rule'}' triggered",
                    metrics=metrics,
                )
            return None

        return None


def _extract_metric_number(source: Dict[str, Any], key: str) -> Optional[float]:
    value = source.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _extract_nested_metric_number(source: Dict[str, Any], path: Tuple[str, ...]) -> Optional[float]:
    current: Any = source
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    if isinstance(current, bool):
        return None
    if isinstance(current, (int, float)):
        return float(current)
    return None
