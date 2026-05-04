"""FastMCP server entry point for AgentGuard MCP budgets."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from agentguard_mcp.storage import BudgetStore
from agentguard_mcp.sync import SyncHook

mcp = FastMCP("AgentGuard MCP", json_response=True)
store = BudgetStore()
sync_hook = SyncHook()


@mcp.tool()
def set_budget(
    scope: str,
    limit_tokens: int | None = None,
    limit_usd: float | None = None,
    period: str = "day",
) -> dict:
    """Set a local token or dollar budget for a scope."""
    return dict(store.set_budget(scope, limit_tokens, limit_usd, period))


@mcp.tool()
def check_remaining(scope: str) -> dict:
    """Return current usage and limits for a scope."""
    return dict(store.check_remaining(scope))


@mcp.tool()
def record_call(
    server: str,
    tool: str,
    tokens_in: int,
    tokens_out: int,
    cost_usd: float,
    session_id: str | None = None,
) -> dict:
    """Record one MCP tool call and return whether matching budgets still allow it."""
    result = store.record_call(server, tool, tokens_in, tokens_out, cost_usd, session_id)
    sync_hook.record(
        {
            "server": server,
            "tool": tool,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost_usd,
            "session_id": session_id,
            "result": result,
        }
    )
    return dict(result)


@mcp.tool()
def kill_switch(scope: str, enable: bool = True) -> dict:
    """Block or unblock calls matching a scope."""
    return dict(store.kill_switch(scope, enable))


@mcp.tool()
def list_budgets() -> dict:
    """List configured budgets and current local usage."""
    return {"budgets": [dict(item) for item in store.list_budgets()]}


def main() -> None:
    mcp.run(transport="stdio")
