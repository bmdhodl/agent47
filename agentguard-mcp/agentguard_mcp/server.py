"""FastMCP server entry point for AgentGuard MCP budgets."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from agentguard_mcp.storage import BudgetStore
from agentguard_mcp.sync import SyncHook


def create_server(
    store: BudgetStore | None = None,
    sync_hook: SyncHook | None = None,
) -> FastMCP:
    """Create an AgentGuard MCP server without import-time local state writes."""
    app = FastMCP("AgentGuard MCP", json_response=True)
    budget_store = store if store is not None else BudgetStore()
    usage_sync = sync_hook if sync_hook is not None else SyncHook()

    @app.tool()
    def set_budget(
        scope: str,
        limit_tokens: int | None = None,
        limit_usd: float | None = None,
        period: str = "day",
    ) -> dict:
        """Set a local token or dollar budget for a scope."""
        return dict(budget_store.set_budget(scope, limit_tokens, limit_usd, period))

    @app.tool()
    def check_remaining(scope: str) -> dict:
        """Return current usage and limits for a scope."""
        return dict(budget_store.check_remaining(scope))

    @app.tool()
    def record_call(
        server: str,
        tool: str,
        tokens_in: int,
        tokens_out: int,
        cost_usd: float,
        session_id: str | None = None,
    ) -> dict:
        """Record one MCP tool call if matching budgets still allow it."""
        result = budget_store.record_call(server, tool, tokens_in, tokens_out, cost_usd, session_id)
        usage_sync.record(
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

    @app.tool()
    def kill_switch(scope: str, enable: bool = True) -> dict:
        """Block or unblock calls matching a scope."""
        return dict(budget_store.kill_switch(scope, enable))

    @app.tool()
    def list_budgets() -> dict:
        """List configured budgets and current local usage."""
        return {"budgets": [dict(item) for item in budget_store.list_budgets()]}

    return app


def main() -> None:
    mcp = create_server()
    mcp.run(transport="stdio")
