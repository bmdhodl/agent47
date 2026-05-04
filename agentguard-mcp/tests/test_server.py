from __future__ import annotations

import importlib


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
