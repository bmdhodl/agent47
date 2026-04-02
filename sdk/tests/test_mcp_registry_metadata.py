import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT_DOCKERFILE = REPO_ROOT / "Dockerfile"
ROOT_DOCKERIGNORE = REPO_ROOT / ".dockerignore"
ROOT_SMITHERY = REPO_ROOT / "smithery.yaml"
MCP_PACKAGE = REPO_ROOT / "mcp-server" / "package.json"
MCP_SERVER = REPO_ROOT / "mcp-server" / "server.json"
MCP_DOCKERFILE = REPO_ROOT / "mcp-server" / "Dockerfile"
MCP_DOCKERIGNORE = REPO_ROOT / "mcp-server" / ".dockerignore"
MCP_SMITHERY = REPO_ROOT / "mcp-server" / "smithery.yaml"


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


def test_mcp_glama_packaging_files_are_present():
    assert ROOT_DOCKERFILE.exists()
    assert ROOT_DOCKERIGNORE.exists()
    assert ROOT_SMITHERY.exists()
    assert MCP_DOCKERFILE.exists()
    assert MCP_DOCKERIGNORE.exists()
    assert MCP_SMITHERY.exists()


def test_mcp_smithery_config_matches_runtime_contract():
    root_smithery = ROOT_SMITHERY.read_text(encoding="utf-8")
    root_dockerfile = ROOT_DOCKERFILE.read_text(encoding="utf-8")
    smithery = MCP_SMITHERY.read_text(encoding="utf-8")
    dockerfile = MCP_DOCKERFILE.read_text(encoding="utf-8")

    assert "agentguardApiKey" in root_smithery
    assert "agentguardUrl" in root_smithery
    assert "AGENTGUARD_API_KEY" in root_smithery
    assert "AGENTGUARD_URL" in root_smithery
    assert "/app/mcp-server/dist/index.js" in root_smithery

    assert "COPY mcp-server/package*.json ./" in root_dockerfile
    assert "COPY mcp-server/src ./src" in root_dockerfile
    assert 'CMD ["node", "/app/mcp-server/dist/index.js"]' in root_dockerfile

    assert "agentguardApiKey" in smithery
    assert "agentguardUrl" in smithery
    assert "AGENTGUARD_API_KEY" in smithery
    assert "AGENTGUARD_URL" in smithery
    assert "/app/dist/index.js" in smithery

    assert "npm ci" in dockerfile
    assert "npm run build" in dockerfile
    assert 'CMD ["node", "/app/dist/index.js"]' in dockerfile

    dockerignore = MCP_DOCKERIGNORE.read_text(encoding="utf-8")
    assert "node_modules" in dockerignore
    assert ".mcpregistry_github_token" in dockerignore

    root_dockerignore = ROOT_DOCKERIGNORE.read_text(encoding="utf-8")
    assert "mcp-server/node_modules" in root_dockerignore
    assert ".codex-proof" in root_dockerignore
