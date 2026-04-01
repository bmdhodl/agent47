# Coding Agents

Use this flow when Codex, Claude Code, Cursor, or another coding agent needs to
wire AgentGuard into a repo without hidden network behavior or dashboard setup.

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
