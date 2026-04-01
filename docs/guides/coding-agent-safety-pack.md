# Coding-Agent Safety Pack

Use this when you want a coding agent to onboard AgentGuard into a repo with
the fewest moving parts possible.

The goal is always the same:
- keep the first run local
- keep the config auditable
- stop loops, retries, and runaway spend
- avoid hidden network behavior

## 1. Repo-local defaults

Check in a tiny `.agentguard.json` file:

```json
{
  "profile": "coding-agent",
  "service": "support-agent",
  "trace_file": ".agentguard/traces.jsonl",
  "budget_usd": 5.0
}
```

This gives both humans and coding agents the same local defaults without
secrets or hosted coupling.

## 2. Codex / AGENTS.md snippet

Add this to the target repo's `AGENTS.md`:

```md
Use AgentGuard in local-only mode first.

- Keep traces in `.agentguard/traces.jsonl`
- Prefer `agentguard.init(local_only=True)`
- Respect the checked-in `.agentguard.json`
- Do not add API keys or hosted settings during first integration
- Verify with:
  1. `agentguard doctor`
  2. `agentguard quickstart --framework raw`
  3. `python examples/starters/agentguard_raw_quickstart.py`
  4. `agentguard report .agentguard/traces.jsonl`
```

## 3. Claude Code / CLAUDE.md snippet

Add this to the target repo's `CLAUDE.md`:

```md
When using AgentGuard:

- start local-only
- use the repo's `.agentguard.json`
- keep traces in `.agentguard/traces.jsonl`
- do not add dashboard or network settings in the first PR
- prove the integration by running `agentguard doctor` and a local starter
```

## 4. GitHub Copilot / .github/copilot-instructions.md snippet

Add this to `.github/copilot-instructions.md`:

```md
If you touch AI-agent code, keep AgentGuard local-first:

- prefer `agentguard.init(local_only=True)`
- use `.agentguard.json` if present
- avoid adding secrets or hosted settings
- verify changes with `agentguard doctor` and a local trace report
```

## 5. Cursor project rule snippet

Add a rule like `.cursor/rules/agentguard.mdc`:

```md
---
description: AgentGuard local-first safety
globs:
  - "**/*.py"
alwaysApply: false
---

When integrating AgentGuard:
- keep the first run local
- use `.agentguard/traces.jsonl`
- honor `.agentguard.json`
- avoid API keys and hosted settings in initial setup
- verify with `agentguard doctor` before wiring real providers
```

## 6. MCP-capable agent snippet

Only after the local SDK path is proven, MCP-capable coding agents can read
retained AgentGuard traces through the published MCP server:

```json
{
  "mcpServers": {
    "agentguard": {
      "command": "npx",
      "args": ["-y", "@agentguard47/mcp-server"],
      "env": {
        "AGENTGUARD_API_KEY": "ag_your_key_here"
      }
    }
  }
}
```

Keep this out of the first-run path. MCP is for retained trace access later,
not for proving local enforcement.

## 7. Verification sequence

The shortest credible flow is:

```bash
pip install agentguard47
agentguard doctor
agentguard quickstart --framework raw
python examples/starters/agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
```

For a stronger proof run:

```bash
agentguard demo
python examples/demo_budget_kill.py
agentguard incident demo_traces.jsonl --format json
```

## 8. Boundary reminder

Use the AgentGuard SDK for:
- local enforcement
- local traces
- local reports
- local savings summaries

Use the hosted dashboard later for:
- retained history
- alerts
- remote controls
- team visibility
- governance
