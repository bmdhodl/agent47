"""Tests for the MCP tool-call audit-log primitive.

These cover audit-only behavior: row schema, payload digesting, no raw-argument
leakage, and that ``decision`` is recorded as a label without enforcement.
"""
import json

import pytest

from agentguard import MCPAuditLogger, build_mcp_audit_row, digest_payload
from agentguard.mcp_audit import MCP_AUDIT_KIND
from agentguard.tracing import TraceSink

_REQUIRED_FIELDS = {
    "kind",
    "timestamp",
    "server",
    "tool",
    "payload_digest",
    "decision",
    "reason",
    "agent_id",
}


class _CaptureSink(TraceSink):
    """Sink that keeps emitted rows in memory for assertions."""

    def __init__(self):
        self.rows = []

    def emit(self, event):
        # Round-trip through JSON to prove rows are parseable.
        self.rows.append(json.loads(json.dumps(event, sort_keys=True)))


# ---------------------------------------------------------------------------
# build_mcp_audit_row — schema
# ---------------------------------------------------------------------------

def test_build_row_has_full_schema_for_allow_decision():
    row = build_mcp_audit_row(
        server="github",
        tool="create_issue",
        payload={"repo": "acme/app", "title": "Bug"},
        decision="allow",
        reason="within session scope",
        agent_id="planner",
    )
    assert set(row) == _REQUIRED_FIELDS
    assert row["kind"] == MCP_AUDIT_KIND
    assert row["server"] == "github"
    assert row["tool"] == "create_issue"
    assert row["decision"] == "allow"
    assert row["reason"] == "within session scope"
    assert row["agent_id"] == "planner"
    assert row["payload_digest"].startswith("sha256:")
    assert row["timestamp"].endswith("Z")


def test_build_row_has_full_schema_for_deny_decision():
    row = build_mcp_audit_row(
        server="filesystem",
        tool="delete_file",
        payload={"path": "/etc/passwd"},
        decision="deny",
        reason="path outside workspace",
        agent_id="worker-7",
    )
    assert set(row) == _REQUIRED_FIELDS
    assert row["decision"] == "deny"
    assert row["reason"] == "path outside workspace"


def test_build_row_optional_fields_default_to_none():
    row = build_mcp_audit_row(
        server="github",
        tool="list_repos",
        payload={},
        decision="observed",
    )
    assert row["reason"] is None
    assert row["agent_id"] is None


def test_build_row_is_json_serializable():
    row = build_mcp_audit_row(
        server="github", tool="x", payload={"a": 1}, decision="allow"
    )
    parsed = json.loads(json.dumps(row, sort_keys=True))
    assert parsed == row


@pytest.mark.parametrize("bad", ["", "  ", None, 123])
def test_build_row_rejects_empty_required_strings(bad):
    with pytest.raises((ValueError, TypeError)):
        build_mcp_audit_row(server=bad, tool="x", payload={}, decision="allow")
    with pytest.raises((ValueError, TypeError)):
        build_mcp_audit_row(server="s", tool=bad, payload={}, decision="allow")
    with pytest.raises((ValueError, TypeError)):
        build_mcp_audit_row(server="s", tool="x", payload={}, decision=bad)


# ---------------------------------------------------------------------------
# digest_payload — digest behavior
# ---------------------------------------------------------------------------

def test_digest_is_deterministic_regardless_of_key_order():
    a = digest_payload({"a": 1, "b": 2})
    b = digest_payload({"b": 2, "a": 1})
    assert a == b


def test_digest_differs_for_different_payloads():
    assert digest_payload({"a": 1}) != digest_payload({"a": 2})


def test_digest_carries_algorithm_prefix():
    assert digest_payload({"x": 1}, algorithm="sha1").startswith("sha1:")
    assert digest_payload({"x": 1}, algorithm="sha256").startswith("sha256:")


def test_digest_rejects_unknown_algorithm():
    with pytest.raises(ValueError):
        digest_payload({"x": 1}, algorithm="rot13")


def test_digest_handles_non_serializable_payload():
    # Sets and other non-JSON values are coerced, not raised on.
    digest = digest_payload({"tags": {"b", "a"}})
    assert digest.startswith("sha256:")


# ---------------------------------------------------------------------------
# No raw-argument leakage
# ---------------------------------------------------------------------------

def test_row_does_not_leak_raw_arguments():
    secret = "super-secret-token-value"
    row = build_mcp_audit_row(
        server="api",
        tool="call",
        payload={"token": secret, "body": "sensitive payload text"},
        decision="allow",
    )
    serialized = json.dumps(row)
    assert secret not in serialized
    assert "sensitive payload text" not in serialized
    # Only the digest represents the payload.
    assert "payload" not in row
    assert row["payload_digest"].startswith("sha256:")


def test_logger_does_not_leak_raw_arguments():
    sink = _CaptureSink()
    audit = MCPAuditLogger(sink)
    secret = "another-secret-99"
    audit.record(
        server="api", tool="call", payload={"key": secret}, decision="deny"
    )
    serialized = json.dumps(sink.rows)
    assert secret not in serialized


# ---------------------------------------------------------------------------
# MCPAuditLogger — writes one parseable JSONL row per call
# ---------------------------------------------------------------------------

def test_logger_writes_one_jsonl_row_per_call_to_file(tmp_path):
    path = tmp_path / "mcp_audit.jsonl"
    audit = MCPAuditLogger(str(path))
    audit.record(
        server="github", tool="create_issue", payload={"repo": "a/b"},
        decision="allow", agent_id="planner",
    )
    audit.record(
        server="filesystem", tool="delete_file", payload={"path": "x"},
        decision="deny", reason="out of scope",
    )

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    rows = [json.loads(line) for line in lines]
    assert rows[0]["decision"] == "allow"
    assert rows[1]["decision"] == "deny"
    assert all(r["kind"] == MCP_AUDIT_KIND for r in rows)


def test_logger_accepts_pathlike_sink(tmp_path):
    path = tmp_path / "mcp_audit.jsonl"
    audit = MCPAuditLogger(path)
    audit.record(server="github", tool="create_issue", payload={}, decision="allow")

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 1
    assert rows[0]["tool"] == "create_issue"


def test_logger_record_returns_written_row():
    sink = _CaptureSink()
    audit = MCPAuditLogger(sink)
    returned = audit.record(
        server="github", tool="x", payload={"a": 1}, decision="observed"
    )
    assert returned == sink.rows[0]


def test_logger_records_decision_label_without_enforcing():
    # A "deny" decision must still produce a written row — the logger never
    # raises or short-circuits based on the decision value.
    sink = _CaptureSink()
    audit = MCPAuditLogger(sink)
    row = audit.record(
        server="api", tool="dangerous_tool", payload={}, decision="deny"
    )
    assert row["decision"] == "deny"
    assert len(sink.rows) == 1


def test_logger_rejects_invalid_sink_type():
    with pytest.raises(TypeError):
        MCPAuditLogger(12345)


def test_logger_honors_digest_algorithm():
    sink = _CaptureSink()
    audit = MCPAuditLogger(sink, digest_algorithm="sha1")
    row = audit.record(server="s", tool="t", payload={"a": 1}, decision="allow")
    assert row["payload_digest"].startswith("sha1:")
