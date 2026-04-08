"""Structured decision-trace helpers built on top of TraceContext events.

These helpers let applications capture agent proposals, human edits or
overrides, approvals, and binding outcomes without hand-building event payloads
for every workflow.
"""
from __future__ import annotations

import json
import uuid
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from difflib import unified_diff
from typing import Any, Dict, Iterator, Optional, Union

from .tracing import (
    TraceContext,
    Tracer,
    _coerce_json_value,
    _json_size,
    _truncate_text,
    _truncation_marker,
)

DECISION_PROPOSED = "decision.proposed"
DECISION_EDITED = "decision.edited"
DECISION_OVERRIDDEN = "decision.overridden"
DECISION_APPROVED = "decision.approved"
DECISION_BOUND = "decision.bound"

_DECISION_EVENT_TYPES = {
    DECISION_PROPOSED,
    DECISION_EDITED,
    DECISION_OVERRIDDEN,
    DECISION_APPROVED,
    DECISION_BOUND,
}
_DECISION_RESERVED_SPAN_KEYS = {
    "decision_id",
    "workflow_id",
    "object_type",
    "object_id",
    "actor_type",
    "actor_id",
}
_MAX_DECISION_DATA_BYTES = 65_536
_DECISION_FIELDS = (
    "decision_id",
    "workflow_id",
    "trace_id",
    "object_type",
    "object_id",
    "actor_type",
    "actor_id",
    "event_type",
    "proposal",
    "final",
    "diff",
    "reason",
    "comment",
    "timestamp",
    "binding_state",
    "outcome",
)


def _require_non_empty(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_value(name: str, value: Any) -> Any:
    if value is None:
        raise ValueError(f"{name} must not be None")
    return value


def _snapshot(value: Any) -> Any:
    if value is None:
        return None
    try:
        return deepcopy(value)
    except TypeError:
        return value


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_diff_value(value: Any) -> str:
    if value is None:
        return "null\n"
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True)
        except (TypeError, ValueError):
            text = repr(value)
    if not text.endswith("\n"):
        text += "\n"
    return text


def _compute_diff(proposal: Any, final: Any) -> Optional[str]:
    if proposal is None or final is None:
        return None
    if proposal == final:
        return ""
    diff = unified_diff(
        _normalize_diff_value(proposal).splitlines(keepends=True),
        _normalize_diff_value(final).splitlines(keepends=True),
        fromfile="proposal",
        tofile="final",
        lineterm="\n",
    )
    rendered = "".join(diff)
    return rendered or ""


def _fit_decision_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {key: _coerce_json_value(value) for key, value in payload.items()}
    if _json_size(sanitized) <= _MAX_DECISION_DATA_BYTES:
        return sanitized

    for field, budget in (("diff", 4096), ("comment", 2048), ("reason", 2048)):
        value = sanitized.get(field)
        if isinstance(value, str):
            sanitized[field] = _truncate_text(value, budget)
            if _json_size(sanitized) <= _MAX_DECISION_DATA_BYTES:
                return sanitized

    for field in ("proposal", "final"):
        sanitized[field] = _truncation_marker(sanitized[field])
        if _json_size(sanitized) <= _MAX_DECISION_DATA_BYTES:
            return sanitized

    for field, budget in (("diff", 512), ("comment", 512), ("reason", 512)):
        value = sanitized.get(field)
        if isinstance(value, str):
            sanitized[field] = _truncate_text(value, budget)

    return sanitized


def is_decision_event(event: Dict[str, Any]) -> bool:
    """Return True when a raw trace event carries a decision.* payload."""
    if not isinstance(event, dict):
        return False
    if event.get("kind") != "event":
        return False
    name = event.get("name")
    payload = event.get("data")
    if name in _DECISION_EVENT_TYPES:
        return isinstance(payload, dict)
    return isinstance(payload, dict) and payload.get("event_type") in _DECISION_EVENT_TYPES


def extract_decision_payload(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize a raw trace event into the stable decision payload shape."""
    if not is_decision_event(event):
        return None
    payload = event.get("data")
    if not isinstance(payload, dict):
        payload = {}
    normalized = {field: payload.get(field) for field in _DECISION_FIELDS}
    normalized["trace_id"] = normalized["trace_id"] or event.get("trace_id")
    normalized["event_type"] = normalized["event_type"] or event.get("name")
    return normalized


def extract_decision_events(
    events: Iterator[Dict[str, Any]] | list[Dict[str, Any]],
    *,
    trace_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    decision_id: Optional[str] = None,
) -> list[Dict[str, Any]]:
    """Extract normalized decision payloads from a trace event stream."""
    extracted: list[Dict[str, Any]] = []
    for event in events:
        payload = extract_decision_payload(event)
        if payload is None:
            continue
        if trace_id is not None and payload.get("trace_id") != trace_id:
            continue
        if workflow_id is not None and payload.get("workflow_id") != workflow_id:
            continue
        if decision_id is not None and payload.get("decision_id") != decision_id:
            continue
        extracted.append(payload)
    return extracted


def _build_decision_payload(
    context: TraceContext,
    *,
    decision_id: str,
    workflow_id: str,
    object_type: str,
    object_id: str,
    actor_type: str,
    actor_id: str,
    event_type: str,
    proposal: Any,
    final: Any,
    diff: Optional[str],
    reason: Optional[str],
    comment: Optional[str],
    timestamp: Optional[str],
    binding_state: Optional[str],
    outcome: Optional[str],
) -> Dict[str, Any]:
    if event_type not in _DECISION_EVENT_TYPES:
        raise ValueError(f"Unsupported decision event type: {event_type}")

    payload = {
        "decision_id": _require_non_empty("decision_id", decision_id),
        "workflow_id": _require_non_empty("workflow_id", workflow_id),
        "trace_id": context.trace_id,
        "object_type": _require_non_empty("object_type", object_type),
        "object_id": _require_non_empty("object_id", object_id),
        "actor_type": _require_non_empty("actor_type", actor_type),
        "actor_id": _require_non_empty("actor_id", actor_id),
        "event_type": event_type,
        "proposal": _require_value("proposal", proposal),
        "final": final,
        "diff": diff,
        "reason": reason,
        "comment": comment,
        "timestamp": timestamp or _timestamp_now(),
        "binding_state": binding_state,
        "outcome": outcome,
    }
    return _fit_decision_payload(payload)


def _emit_decision_event(
    context: TraceContext,
    *,
    decision_id: str,
    workflow_id: str,
    object_type: str,
    object_id: str,
    actor_type: str,
    actor_id: str,
    event_type: str,
    proposal: Any,
    final: Any,
    diff: Optional[str],
    reason: Optional[str],
    comment: Optional[str],
    timestamp: Optional[str],
    binding_state: Optional[str],
    outcome: Optional[str],
) -> Dict[str, Any]:
    payload = _build_decision_payload(
        context,
        decision_id=decision_id,
        workflow_id=workflow_id,
        object_type=object_type,
        object_id=object_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=event_type,
        proposal=proposal,
        final=final,
        diff=diff,
        reason=reason,
        comment=comment,
        timestamp=timestamp,
        binding_state=binding_state,
        outcome=outcome,
    )
    context.event(event_type, data=payload)
    return payload


def log_decision_proposed(
    context: TraceContext,
    *,
    workflow_id: str,
    object_type: str,
    object_id: str,
    actor_type: str,
    actor_id: str,
    proposal: Any,
    decision_id: Optional[str] = None,
    reason: Optional[str] = None,
    comment: Optional[str] = None,
    timestamp: Optional[str] = None,
    binding_state: Optional[str] = None,
    outcome: Optional[str] = "proposed",
) -> Dict[str, Any]:
    """Emit a `decision.proposed` event through the normal tracing pipeline."""
    return _emit_decision_event(
        context,
        decision_id=decision_id or uuid.uuid4().hex,
        workflow_id=workflow_id,
        object_type=object_type,
        object_id=object_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=DECISION_PROPOSED,
        proposal=_require_value("proposal", proposal),
        final=proposal,
        diff="",
        reason=reason,
        comment=comment,
        timestamp=timestamp,
        binding_state=binding_state,
        outcome=outcome,
    )


def log_decision_edited(
    context: TraceContext,
    *,
    decision_id: str,
    workflow_id: str,
    object_type: str,
    object_id: str,
    actor_type: str,
    actor_id: str,
    proposal: Any,
    final: Any,
    reason: Optional[str] = None,
    comment: Optional[str] = None,
    timestamp: Optional[str] = None,
    diff: Optional[str] = None,
    binding_state: Optional[str] = None,
    outcome: Optional[str] = "edited",
) -> Dict[str, Any]:
    """Emit a `decision.edited` event with original proposal, final form, and diff."""
    resolved_proposal = _require_value("proposal", proposal)
    resolved_final = _require_value("final", final)
    return _emit_decision_event(
        context,
        decision_id=decision_id,
        workflow_id=workflow_id,
        object_type=object_type,
        object_id=object_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=DECISION_EDITED,
        proposal=resolved_proposal,
        final=resolved_final,
        diff=_compute_diff(resolved_proposal, resolved_final) if diff is None else diff,
        reason=reason,
        comment=comment,
        timestamp=timestamp,
        binding_state=binding_state,
        outcome=outcome,
    )


def log_decision_overridden(
    context: TraceContext,
    *,
    decision_id: str,
    workflow_id: str,
    object_type: str,
    object_id: str,
    actor_type: str,
    actor_id: str,
    proposal: Any,
    final: Any,
    reason: Optional[str] = None,
    comment: Optional[str] = None,
    timestamp: Optional[str] = None,
    diff: Optional[str] = None,
    binding_state: Optional[str] = None,
    outcome: Optional[str] = "overridden",
) -> Dict[str, Any]:
    """Emit a `decision.overridden` event with preserved proposal and reviewer rationale."""
    resolved_proposal = _require_value("proposal", proposal)
    resolved_final = _require_value("final", final)
    return _emit_decision_event(
        context,
        decision_id=decision_id,
        workflow_id=workflow_id,
        object_type=object_type,
        object_id=object_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=DECISION_OVERRIDDEN,
        proposal=resolved_proposal,
        final=resolved_final,
        diff=_compute_diff(resolved_proposal, resolved_final) if diff is None else diff,
        reason=reason,
        comment=comment,
        timestamp=timestamp,
        binding_state=binding_state,
        outcome=outcome,
    )


def log_decision_approved(
    context: TraceContext,
    *,
    decision_id: str,
    workflow_id: str,
    object_type: str,
    object_id: str,
    actor_type: str,
    actor_id: str,
    proposal: Any,
    final: Any = None,
    reason: Optional[str] = None,
    comment: Optional[str] = None,
    timestamp: Optional[str] = None,
    diff: Optional[str] = None,
    binding_state: Optional[str] = None,
    outcome: Optional[str] = "approved",
) -> Dict[str, Any]:
    """Emit a `decision.approved` event for a reviewed proposal or final form."""
    resolved_proposal = _require_value("proposal", proposal)
    resolved_final = resolved_proposal if final is None else _require_value("final", final)
    return _emit_decision_event(
        context,
        decision_id=decision_id,
        workflow_id=workflow_id,
        object_type=object_type,
        object_id=object_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=DECISION_APPROVED,
        proposal=resolved_proposal,
        final=resolved_final,
        diff=_compute_diff(resolved_proposal, resolved_final) if diff is None else diff,
        reason=reason,
        comment=comment,
        timestamp=timestamp,
        binding_state=binding_state,
        outcome=outcome,
    )


def log_decision_bound(
    context: TraceContext,
    *,
    decision_id: str,
    workflow_id: str,
    object_type: str,
    object_id: str,
    actor_type: str,
    actor_id: str,
    proposal: Any,
    binding_state: str,
    outcome: str,
    final: Any = None,
    reason: Optional[str] = None,
    comment: Optional[str] = None,
    timestamp: Optional[str] = None,
    diff: Optional[str] = None,
) -> Dict[str, Any]:
    """Emit a `decision.bound` event for the binding result of an approved decision."""
    resolved_proposal = _require_value("proposal", proposal)
    resolved_final = resolved_proposal if final is None else _require_value("final", final)
    return _emit_decision_event(
        context,
        decision_id=decision_id,
        workflow_id=workflow_id,
        object_type=object_type,
        object_id=object_id,
        actor_type=actor_type,
        actor_id=actor_id,
        event_type=DECISION_BOUND,
        proposal=resolved_proposal,
        final=resolved_final,
        diff=_compute_diff(resolved_proposal, resolved_final) if diff is None else diff,
        reason=reason,
        comment=comment,
        timestamp=timestamp,
        binding_state=_require_non_empty("binding_state", binding_state),
        outcome=_require_non_empty("outcome", outcome),
    )


class DecisionTrace:
    """Stateful helper for logging a full decision review flow on one trace span."""

    def __init__(
        self,
        context: TraceContext,
        *,
        workflow_id: str,
        object_type: str,
        object_id: str,
        actor_type: str,
        actor_id: str,
        decision_id: Optional[str] = None,
    ) -> None:
        self._context = context
        self.workflow_id = _require_non_empty("workflow_id", workflow_id)
        self.object_type = _require_non_empty("object_type", object_type)
        self.object_id = _require_non_empty("object_id", object_id)
        self.actor_type = _require_non_empty("actor_type", actor_type)
        self.actor_id = _require_non_empty("actor_id", actor_id)
        self.decision_id = decision_id or uuid.uuid4().hex
        self._proposal = None
        self._final = None

    @property
    def trace_id(self) -> str:
        """Return the enclosing trace id used for all emitted decision events."""
        return self._context.trace_id

    def _resolve_actor(
        self,
        actor_type: Optional[str],
        actor_id: Optional[str],
    ) -> tuple[str, str]:
        return (
            self.actor_type if actor_type is None else _require_non_empty("actor_type", actor_type),
            self.actor_id if actor_id is None else _require_non_empty("actor_id", actor_id),
        )

    def _resolve_proposal(self, proposal: Any = None) -> Any:
        if proposal is not None:
            self._proposal = _snapshot(proposal)
            if self._final is None:
                self._final = _snapshot(proposal)
        if self._proposal is None:
            raise ValueError("proposal is required before logging this decision event")
        return _snapshot(self._proposal)

    def _resolve_final(self, final: Any = None) -> Any:
        if final is not None:
            self._final = _snapshot(final)
        if self._final is None:
            self._final = _snapshot(self._proposal)
        return _snapshot(self._final)

    def proposed(
        self,
        proposal: Any,
        *,
        actor_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
        timestamp: Optional[str] = None,
        binding_state: Optional[str] = None,
        outcome: Optional[str] = "proposed",
    ) -> Dict[str, Any]:
        """Record the agent's original proposed action."""
        resolved_actor_type, resolved_actor_id = self._resolve_actor(actor_type, actor_id)
        self._proposal = _snapshot(proposal)
        self._final = _snapshot(proposal)
        return log_decision_proposed(
            self._context,
            workflow_id=self.workflow_id,
            object_type=self.object_type,
            object_id=self.object_id,
            actor_type=resolved_actor_type,
            actor_id=resolved_actor_id,
            proposal=self._proposal,
            decision_id=self.decision_id,
            reason=reason,
            comment=comment,
            timestamp=timestamp,
            binding_state=binding_state,
            outcome=outcome,
        )

    def edited(
        self,
        final: Any,
        *,
        actor_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        proposal: Any = None,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
        timestamp: Optional[str] = None,
        diff: Optional[str] = None,
        binding_state: Optional[str] = None,
        outcome: Optional[str] = "edited",
    ) -> Dict[str, Any]:
        """Record a human edit to the original proposal with exact diff when practical."""
        resolved_actor_type, resolved_actor_id = self._resolve_actor(actor_type, actor_id)
        resolved_proposal = self._resolve_proposal(proposal)
        self._final = _snapshot(final)
        return log_decision_edited(
            self._context,
            decision_id=self.decision_id,
            workflow_id=self.workflow_id,
            object_type=self.object_type,
            object_id=self.object_id,
            actor_type=resolved_actor_type,
            actor_id=resolved_actor_id,
            proposal=resolved_proposal,
            final=self._final,
            reason=reason,
            comment=comment,
            timestamp=timestamp,
            diff=diff,
            binding_state=binding_state,
            outcome=outcome,
        )

    def overridden(
        self,
        final: Any,
        *,
        actor_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        proposal: Any = None,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
        timestamp: Optional[str] = None,
        diff: Optional[str] = None,
        binding_state: Optional[str] = None,
        outcome: Optional[str] = "overridden",
    ) -> Dict[str, Any]:
        """Record a human override of the original proposal."""
        resolved_actor_type, resolved_actor_id = self._resolve_actor(actor_type, actor_id)
        resolved_proposal = self._resolve_proposal(proposal)
        self._final = _snapshot(final)
        return log_decision_overridden(
            self._context,
            decision_id=self.decision_id,
            workflow_id=self.workflow_id,
            object_type=self.object_type,
            object_id=self.object_id,
            actor_type=resolved_actor_type,
            actor_id=resolved_actor_id,
            proposal=resolved_proposal,
            final=self._final,
            reason=reason,
            comment=comment,
            timestamp=timestamp,
            diff=diff,
            binding_state=binding_state,
            outcome=outcome,
        )

    def approved(
        self,
        *,
        actor_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        proposal: Any = None,
        final: Any = None,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
        timestamp: Optional[str] = None,
        diff: Optional[str] = None,
        binding_state: Optional[str] = None,
        outcome: Optional[str] = "approved",
    ) -> Dict[str, Any]:
        """Record approval of the current proposal or final reviewed form."""
        resolved_actor_type, resolved_actor_id = self._resolve_actor(actor_type, actor_id)
        resolved_proposal = self._resolve_proposal(proposal)
        resolved_final = self._resolve_final(final)
        return log_decision_approved(
            self._context,
            decision_id=self.decision_id,
            workflow_id=self.workflow_id,
            object_type=self.object_type,
            object_id=self.object_id,
            actor_type=resolved_actor_type,
            actor_id=resolved_actor_id,
            proposal=resolved_proposal,
            final=resolved_final,
            reason=reason,
            comment=comment,
            timestamp=timestamp,
            diff=diff,
            binding_state=binding_state,
            outcome=outcome,
        )

    def bound(
        self,
        *,
        binding_state: str,
        outcome: str,
        actor_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        proposal: Any = None,
        final: Any = None,
        reason: Optional[str] = None,
        comment: Optional[str] = None,
        timestamp: Optional[str] = None,
        diff: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record the binding result of the current approved decision."""
        resolved_actor_type, resolved_actor_id = self._resolve_actor(actor_type, actor_id)
        resolved_proposal = self._resolve_proposal(proposal)
        resolved_final = self._resolve_final(final)
        return log_decision_bound(
            self._context,
            decision_id=self.decision_id,
            workflow_id=self.workflow_id,
            object_type=self.object_type,
            object_id=self.object_id,
            actor_type=resolved_actor_type,
            actor_id=resolved_actor_id,
            proposal=resolved_proposal,
            final=resolved_final,
            binding_state=binding_state,
            outcome=outcome,
            reason=reason,
            comment=comment,
            timestamp=timestamp,
            diff=diff,
        )


@contextmanager
def decision_flow(
    target: Union[TraceContext, Tracer],
    *,
    workflow_id: str,
    object_type: str,
    object_id: str,
    actor_type: str,
    actor_id: str,
    decision_id: Optional[str] = None,
    span_name: str = "decision.flow",
    span_data: Optional[Dict[str, Any]] = None,
) -> Iterator[DecisionTrace]:
    """Wrap an agent decision workflow in a dedicated span and decision helper.

    Args:
        target: Existing `TraceContext` for nested decision spans or a `Tracer`
            for a top-level decision workflow trace.
        workflow_id: Stable workflow identifier shared across related decisions.
        object_type: Type of object under review, such as `ticket` or `deploy`.
        object_id: Stable object identifier under review.
        actor_type: Default actor type for emitted decision events.
        actor_id: Default actor identifier for emitted decision events.
        decision_id: Optional stable decision identifier. Generated if omitted.
        span_name: Span name used to wrap the workflow.
        span_data: Optional extra metadata attached to the decision-flow span.
    """
    span_payload = {
        "decision_id": decision_id or uuid.uuid4().hex,
        "workflow_id": workflow_id,
        "object_type": object_type,
        "object_id": object_id,
        "actor_type": actor_type,
        "actor_id": actor_id,
    }
    if span_data:
        conflicting_keys = sorted(_DECISION_RESERVED_SPAN_KEYS.intersection(span_data))
        if conflicting_keys:
            raise ValueError(
                "span_data cannot override reserved decision-flow keys: "
                + ", ".join(conflicting_keys)
            )
        span_payload.update(span_data)

    if isinstance(target, Tracer):
        span_cm = target.trace(span_name, data=span_payload)
    elif isinstance(target, TraceContext):
        span_cm = target.span(span_name, data=span_payload)
    else:
        raise TypeError("target must be a Tracer or TraceContext")

    with span_cm as context:
        yield DecisionTrace(
            context,
            workflow_id=workflow_id,
            object_type=object_type,
            object_id=object_id,
            actor_type=actor_type,
            actor_id=actor_id,
            decision_id=span_payload["decision_id"],
        )
