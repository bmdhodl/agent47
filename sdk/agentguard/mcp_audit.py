"""Audit-log primitive for MCP (Model Context Protocol) tool calls.

This module records one parseable JSONL row per MCP tool call. It is an
observability extension of AgentGuard's existing decision/audit surface — it
does **not** enforce policy. The ``decision`` field is a free-form label that
the caller supplies and this module records verbatim; nothing here allows,
denies, rate-limits, or short-circuits a tool call.

Raw tool arguments are never stored. Payloads are reduced to a deterministic
digest so an audit log can be kept without leaking arguments.

Usage::

    from agentguard import MCPAuditLogger

    audit = MCPAuditLogger("mcp_audit.jsonl")
    audit.record(
        server="github",
        tool="create_issue",
        payload={"repo": "acme/app", "title": "Bug"},
        decision="allow",
        reason="within session scope",
        agent_id="planner",
    )

The recorded row is a flat JSON object. An MCP wrapper calls ``record`` after it
has decided what to do with a tool call; this module only writes the row down.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .tracing import JsonlFileSink, TraceSink, _coerce_json_value

__all__ = [
    "MCPAuditLogger",
    "build_mcp_audit_row",
    "digest_payload",
]

# Schema marker so downstream parsers can branch on row type without guessing.
MCP_AUDIT_KIND = "mcp.tool_call.audit"

_SUPPORTED_ALGORITHMS = frozenset({"sha256", "sha1", "md5"})


def _require_non_empty(name: str, value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _timestamp_now() -> str:
    """Return an ISO-8601 UTC timestamp with a trailing ``Z``."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def digest_payload(payload: Any, *, algorithm: str = "sha256") -> str:
    """Return a deterministic hex digest of an MCP tool-call payload.

    The payload is coerced into a JSON-serializable structure and serialized
    with sorted keys so the digest is stable regardless of dict ordering. The
    raw payload is never returned or stored — only this digest.

    Args:
        payload: Any tool-call argument structure. Non-serializable values are
            coerced via the same path the tracing sinks use.
        algorithm: Hash algorithm name. One of ``sha256``, ``sha1``, ``md5``.

    Returns:
        A ``"<algorithm>:<hexdigest>"`` string, e.g. ``"sha256:ab12..."``.
    """
    if algorithm not in _SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"algorithm must be one of {sorted(_SUPPORTED_ALGORITHMS)}, got {algorithm!r}"
        )
    coerced = _coerce_json_value(payload)
    canonical = json.dumps(coerced, sort_keys=True, ensure_ascii=True)
    hexdigest = hashlib.new(algorithm, canonical.encode("utf-8")).hexdigest()
    return f"{algorithm}:{hexdigest}"


def build_mcp_audit_row(
    *,
    server: str,
    tool: str,
    payload: Any,
    decision: str,
    reason: Optional[str] = None,
    agent_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    payload_digest: Optional[str] = None,
    digest_algorithm: str = "sha256",
) -> Dict[str, Any]:
    """Build one normalized, JSON-serializable MCP tool-call audit row.

    The row records a *decision label* — it does not enforce it. Raw ``payload``
    is digested, never copied into the row.

    Args:
        server: MCP server name the tool belongs to.
        tool: Tool name being called.
        payload: Tool-call arguments. Digested, not stored raw.
        decision: Free-form decision label, e.g. ``"allow"``, ``"deny"``,
            ``"observed"``. Recorded verbatim; no enforcement happens here.
        reason: Optional human-readable rationale for the decision.
        agent_id: Optional identifier of the agent making the call.
        timestamp: Optional ISO-8601 timestamp. Generated (UTC) if omitted.
        payload_digest: Optional precomputed digest. Computed from ``payload``
            if omitted.
        digest_algorithm: Algorithm used when computing the digest.

    Returns:
        A flat dict suitable for a single JSONL line.
    """
    row = {
        "kind": MCP_AUDIT_KIND,
        "timestamp": timestamp or _timestamp_now(),
        "server": _require_non_empty("server", server),
        "tool": _require_non_empty("tool", tool),
        "payload_digest": payload_digest
        or digest_payload(payload, algorithm=digest_algorithm),
        "decision": _require_non_empty("decision", decision),
        "reason": reason,
        "agent_id": agent_id,
    }
    return row


class MCPAuditLogger:
    """Writes MCP tool-call audit rows to a JSONL sink.

    This logger is audit-only. It records the ``decision`` label supplied by the
    caller and never enforces a policy. It holds no mutable state of its own;
    thread safety comes from the underlying sink (``JsonlFileSink`` is
    thread-safe).

    Usage::

        audit = MCPAuditLogger("mcp_audit.jsonl")
        audit.record(server="github", tool="create_issue",
                      payload={"repo": "acme/app"}, decision="allow")

    Args:
        sink: Either a path string (wrapped in a :class:`JsonlFileSink`) or any
            :class:`~agentguard.TraceSink` instance.
        digest_algorithm: Hash algorithm used for payload digests.
    """

    def __init__(
        self,
        sink: Any,
        *,
        digest_algorithm: str = "sha256",
    ) -> None:
        if isinstance(sink, (str, os.PathLike)):
            self._sink: TraceSink = JsonlFileSink(os.fspath(sink))
        elif isinstance(sink, TraceSink):
            self._sink = sink
        else:
            raise TypeError(
                "sink must be a file path, path-like object, or a TraceSink instance"
            )
        if digest_algorithm not in _SUPPORTED_ALGORITHMS:
            raise ValueError(
                f"digest_algorithm must be one of {sorted(_SUPPORTED_ALGORITHMS)}, "
                f"got {digest_algorithm!r}"
            )
        self._digest_algorithm = digest_algorithm

    def record(
        self,
        *,
        server: str,
        tool: str,
        payload: Any,
        decision: str,
        reason: Optional[str] = None,
        agent_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        payload_digest: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build an audit row and write it to the sink as one JSONL line.

        Returns the row that was written so callers can assert on or forward it.
        This does not enforce ``decision`` — it only records it.
        """
        row = build_mcp_audit_row(
            server=server,
            tool=tool,
            payload=payload,
            decision=decision,
            reason=reason,
            agent_id=agent_id,
            timestamp=timestamp,
            payload_digest=payload_digest,
            digest_algorithm=self._digest_algorithm,
        )
        self._sink.emit(row)
        return row

    def __repr__(self) -> str:
        return f"MCPAuditLogger(sink={self._sink!r})"
