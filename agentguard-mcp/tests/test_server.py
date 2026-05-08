from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def _tool_payload(result):
    assert result.isError is False
    assert result.content
    return json.loads(result.content[0].text)


def test_importing_server_does_not_create_state_db(tmp_path, monkeypatch):
    db_path = tmp_path / "state.db"
    monkeypatch.setenv("AGENTGUARD_DB_PATH", str(db_path))

    import agentguard_mcp.server as server

    importlib.reload(server)

    assert not db_path.exists()


def test_create_server_initializes_store_when_called(tmp_path, monkeypatch):
    db_path = tmp_path / "state.db"
    monkeypatch.setenv("AGENTGUARD_DB_PATH", str(db_path))

    from agentguard_mcp.server import create_server

    app = create_server()

    assert app is not None
    assert db_path.exists()


def test_module_entrypoint_serves_budget_tools_over_stdio(tmp_path):
    async def run_smoke() -> None:
        env = os.environ.copy()
        env["AGENTGUARD_DB_PATH"] = str(tmp_path / "state.db")
        package_root = Path(__file__).resolve().parents[1]
        env["PYTHONPATH"] = (
            f"{package_root}{os.pathsep}{env['PYTHONPATH']}"
            if env.get("PYTHONPATH")
            else str(package_root)
        )
        env.pop("AGENTGUARD_SYNC_URL", None)
        env.pop("AGENTGUARD_SYNC_TOKEN", None)

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "agentguard_mcp"],
            env=env,
        )

        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            assert {
                "set_budget",
                "record_call",
                "check_remaining",
                "kill_switch",
                "list_budgets",
            } <= tool_names

            scope = "session:release-operator-dogfood"
            set_budget = _tool_payload(
                await session.call_tool(
                    "set_budget",
                    {"scope": scope, "limit_tokens": 100, "period": "session"},
                )
            )
            assert set_budget["scope"] == scope
            assert set_budget["tokens_limit"] == 100

            record_call = _tool_payload(
                await session.call_tool(
                    "record_call",
                    {
                        "server": "github",
                        "tool": "create_issue",
                        "tokens_in": 10,
                        "tokens_out": 5,
                        "cost_usd": 0.01,
                        "session_id": "release-operator-dogfood",
                    },
                )
            )
            assert record_call["allowed"] is True

            remaining = _tool_payload(await session.call_tool("check_remaining", {"scope": scope}))
            assert remaining["tokens_used"] == 15
            assert remaining["usd_used"] == 0.01

            enabled = _tool_payload(
                await session.call_tool("kill_switch", {"scope": scope, "enable": True})
            )
            assert enabled["kill_switch"] is True

            disabled = _tool_payload(
                await session.call_tool("kill_switch", {"scope": scope, "enable": False})
            )
            assert disabled["kill_switch"] is False

            budgets = _tool_payload(await session.call_tool("list_budgets", {}))
            assert budgets["budgets"]
            assert budgets["budgets"][0]["scope"] == scope

    asyncio.run(asyncio.wait_for(run_smoke(), timeout=10))
