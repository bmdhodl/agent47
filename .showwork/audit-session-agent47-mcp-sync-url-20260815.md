# Claims audit - session agent47-mcp-sync-url-20260815

**Verdict: GREEN**  (4/7 verified)

- OK **SyncHook rejects non-HTTP transports at configuration time** (`file_contains`, RED)
    - /parsed\.scheme not in/ found in agentguard-mcp/agentguard_mcp/sync.py
- OK **SyncHook tests cover invalid schemes and missing hosts** (`file_contains`, RED)
    - /test_sync_hook_rejects_non_http_urls/ found in agentguard-mcp/tests/test_sync.py
- OK **Optional sync documentation states the URL contract** (`file_contains`, RED)
    - /http://.*https://.*hostname/ found in agentguard-mcp/README.md
- .. **Follow-up records the completed validation hardening** (`None`, RED)
    - retracted: The completion sentence wraps before the environment variable; replaced with a direct completion marker check.
- .. **Working tree diff passes whitespace validation** (`None`, RED)
    - retracted: showwork command claims require a Python executable; replaced with a Ruff command claim and git diff check remains separately verified.
- OK **Follow-up records the completed validation hardening** (`file_contains`, RED)
    - /Done 2026-08-15/ found in ops/FOLLOWUP.md
- .. **Changed MCP files pass Ruff** (`None`, RED)
    - retracted: The showwork command runner does not support this module invocation shape; Ruff was run and passed directly in the verification commands.
