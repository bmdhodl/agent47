# Coding-Agent Smoke Test

This is the first end-to-end proof path for A.SDK when you want to watch a real
coding-agent-style flow do useful work, trip runtime guards, and optionally
mirror the same traces to the hosted dashboard.

## Goal

Prove all of this from scratch:
- the SDK installs cleanly
- local traces work
- a coding-agent-style task can complete successfully
- loop and retry enforcement both fire on realistic bad behavior
- the same trace stream can be mirrored to AgentGuard with an API key

## 1. Install the SDK

```bash
pip install agentguard47
```

## 2. Add repo-local defaults

Create `.agentguard.json`:

```json
{
  "profile": "coding-agent",
  "service": "smoke-coding-agent",
  "trace_file": ".agentguard/smoke_coding_agent_traces.jsonl",
  "budget_usd": 5.0
}
```

Keep this file narrow:
- no secrets
- no API keys
- no hosted settings

## 3. Verify the local path first

```bash
agentguard doctor
agentguard demo
```

Both commands stay local. No network calls, no dashboard dependency.

## 4. Run the scratch coding-agent smoke example

```bash
python examples/coding_agent_smoke.py
```

What it does:
- answers a realistic user request about local AgentGuard setup
- writes a local trace
- trips `LoopGuard` on repeated repo lookups
- trips `RetryGuard` on repeated flaky tool failures

Inspect the trace:

```bash
agentguard report .agentguard/smoke_coding_agent_traces.jsonl
agentguard incident .agentguard/smoke_coding_agent_traces.jsonl
```

## 5. Mirror the same run to the hosted dashboard

Only do this explicitly:

```bash
export AGENTGUARD_API_KEY=ag_...
python examples/coding_agent_smoke.py --dashboard
```

This keeps the boundary clean:
- local trace remains the source of truth for SDK proof
- hosted ingest is opt-in
- the dashboard remains the operational layer

## 6. What to verify

Local SDK side:
- the script prints a healthy answer for the user request
- `LoopGuard` triggered is `True`
- `RetryGuard` triggered is `True`
- `agentguard report` renders a summary
- `agentguard incident` renders an incident report with guard events

Hosted side:
- recent traces exist for the `smoke-coding-agent` service
- loop and retry incidents are visible
- trace counts and timestamps match the local run

Use the dashboard handoff prompt for the hosted verification pass.
