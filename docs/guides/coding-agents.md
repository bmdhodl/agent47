# Coding Agents

Use this flow when Codex, Claude Code, Cursor, or another coding agent needs to
wire AgentGuard into a repo without hidden network behavior or dashboard setup.

AgentGuard's job in this flow is narrow and deliberate: stop coding agents from
looping, retrying forever, and burning budget. Keep the first integration local
and auditable, then add the hosted dashboard later only if you need operational
visibility.

If you want ready-to-copy repo instructions for specific coding agents, start
with [`coding-agent-safety-pack.md`](coding-agent-safety-pack.md).

If you want AgentGuard to materialize those files for you:

```bash
agentguard skillpack --write
```

That writes `.agentguard.json` plus the instruction files into
`agentguard_skillpack/` so you can review the pack before applying it to a real
repo.

## Goal

Keep the first integration:
- local-only
- zero-dependency in the core SDK
- deterministic
- auditable from checked-in files

## 1. Check in repo-local defaults

Create `.agentguard.json` at the repo root:

```json
{
  "profile": "coding-agent",
  "service": "support-agent",
  "trace_file": ".agentguard/traces.jsonl",
  "budget_usd": 5.0
}
```

What this does:
- `profile: "coding-agent"` tightens the default `LoopGuard` and adds `RetryGuard`
- `.agentguard/traces.jsonl` keeps local traces out of the project root
- `budget_usd` gives the agent a safe default ceiling without dashboard coupling

What this does not do:
- no API keys
- no hosted control-plane settings
- no secrets

If you want AgentGuard to generate this file together with coding-agent
instructions:

```bash
agentguard skillpack --target codex --write
agentguard skillpack --target claude-code --write
```

## 2. Verify the local path

Run:

```bash
agentguard doctor
```

This:
- makes no network calls
- writes a small local trace
- checks for optional integrations already installed
- prints the smallest safe next-step snippet

## 3. Start from the raw starter

Run:

```bash
python examples/starters/agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
```

That proves:
- local trace writing works
- the checked-in defaults are usable
- the repo can run AgentGuard without provider credentials

## 4. Move to the real stack

Once the raw path works, either:

```bash
agentguard quickstart --framework openai
agentguard quickstart --framework langchain
agentguard quickstart --framework langgraph
```

or run the matching checked-in starter under `examples/starters/`.

If you want the SDK to create a starter file in-place for the repo or coding
agent:

```bash
agentguard quickstart --framework raw --write
agentguard quickstart --framework openai --write --output agentguard_openai_quickstart.py
```

`--write` keeps the first-run flow local and auditable. It writes the exact
starter shown by `quickstart`, then prints the next commands to run. It will
not overwrite an existing file unless you add `--force`.

Those starter files live in the repo for onboarding and copy-paste setup. They
are not part of the installed PyPI wheel.

## 5. Keep the boundary clean

For coding-agent onboarding, prefer:

```python
import agentguard

agentguard.init(local_only=True)
```

That keeps the first run local even if an `AGENTGUARD_API_KEY` is present in the
environment.

Use the dashboard later for:
- retained history
- team visibility
- alerts
- remote kill
- governance

The SDK should prove local enforcement first. The dashboard remains the control
plane.

If the coding agent already supports MCP, add `@agentguard47/mcp-server` only
after the local SDK path is proven. That MCP bridge is for retained traces and
alerts, not the first-run safety proof.

Once the repo-local path works, run the fuller walkthrough in
[`coding-agent-smoke-test.md`](coding-agent-smoke-test.md) to step through the
starter path, the offline demo, and the local budget-kill example.
