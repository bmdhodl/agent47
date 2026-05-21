"""Audit-log an MCP tool call with AgentGuard.

This shows how an MCP wrapper records one JSONL audit row per tool call. The
logger is audit-only: it writes down the ``decision`` label the wrapper has
already made. It does not allow, deny, or rate-limit anything.

Raw tool arguments are never written — only a digest of the payload.

Usage:
    PYTHONPATH=sdk python examples/mcp_audit_example.py
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from agentguard import MCPAuditLogger


def handle_mcp_tool_call(audit: MCPAuditLogger, server: str, tool: str, args: dict):
    """Stand-in for an MCP wrapper handling one tool call.

    The wrapper decides what to do with the call (here, a trivial label) and
    then records that decision. AgentGuard only writes the audit row.
    """
    # The wrapper's own logic decides the label — AgentGuard does not.
    decision = "deny" if tool == "delete_everything" else "allow"
    reason = "destructive tool" if decision == "deny" else "within session scope"

    audit.record(
        server=server,
        tool=tool,
        payload=args,
        decision=decision,
        reason=reason,
        agent_id="example-agent",
    )
    return decision


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "mcp_audit.jsonl"
        audit = MCPAuditLogger(str(log_path))

        # Two stub MCP tool calls — one allowed, one denied.
        handle_mcp_tool_call(
            audit, "github", "create_issue", {"repo": "acme/app", "title": "Bug"}
        )
        handle_mcp_tool_call(
            audit, "filesystem", "delete_everything", {"path": "/"}
        )

        print(f"Audit log written to {log_path}:")
        for line in log_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            print(
                f"  {row['timestamp']} {row['server']}.{row['tool']} "
                f"-> {row['decision']} ({row['payload_digest'][:23]}...)"
            )


if __name__ == "__main__":
    main()
