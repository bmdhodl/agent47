# Coding-Agent Smoke Test

Use this when you want a short, local-first proof that AgentGuard is wired
correctly before touching real provider credentials or hosted settings.

## Goal

Prove four things:
- the SDK installs cleanly
- local trace writing works
- guards can stop a runaway run
- incident reporting works from the generated trace

## 1. Install and verify

```bash
pip install agentguard47
agentguard doctor
```

This should succeed without API keys or network calls.

## 2. Prove the starter path

```bash
python examples/starters/agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
```

This proves the repo-local starter path works and writes a trace.

## 3. Run the stronger local demo

```bash
agentguard demo
python examples/demo_budget_kill.py
```

What this proves:
- `agentguard demo` shows budget, loop, and retry protection offline
- `examples/demo_budget_kill.py` shows a simulated runaway research agent get
  killed by `BudgetGuard`

## 4. Inspect the incident

```bash
agentguard incident demo_traces.jsonl
agentguard incident demo_traces.jsonl --format html > incident.html
```

That gives you a local postmortem-style summary with guard events and savings
data from the trace.

## 5. Only then move to real integrations

After the local smoke path works:
- use `agentguard quickstart --framework <stack>`
- wire the real coding agent
- keep `local_only=True` until you explicitly want hosted follow-through
