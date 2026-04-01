import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MCP_PACKAGE = REPO_ROOT / "mcp-server" / "package.json"
MCP_SERVER = REPO_ROOT / "mcp-server" / "server.json"


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_mcp_registry_metadata_matches_package():
    package = _load_json(MCP_PACKAGE)
    server = _load_json(MCP_SERVER)

    assert package["name"] == "@agentguard47/mcp-server"
    assert package["version"] == server["version"]
    assert package["mcpName"] == server["name"]

    published_package = server["packages"][0]
    assert published_package["registryType"] == "npm"
    assert published_package["identifier"] == package["name"]
    assert published_package["version"] == package["version"]
    assert published_package["transport"]["type"] == "stdio"


def test_mcp_registry_metadata_declares_required_env_vars():
    server = _load_json(MCP_SERVER)
    env_vars = {entry["name"]: entry for entry in server["packages"][0]["environmentVariables"]}

    assert "AGENTGUARD_API_KEY" in env_vars
    assert env_vars["AGENTGUARD_API_KEY"]["isRequired"] is True
    assert env_vars["AGENTGUARD_API_KEY"]["isSecret"] is True

    assert "AGENTGUARD_URL" in env_vars
    assert env_vars["AGENTGUARD_URL"]["isRequired"] is False
    assert env_vars["AGENTGUARD_URL"]["isSecret"] is False
