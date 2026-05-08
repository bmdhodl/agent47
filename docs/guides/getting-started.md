# Getting Started with AgentGuard

Get from zero to your first traced agent run in under 5 minutes.

## Install

```bash
pip install agentguard47
```

Zero dependencies. Python 3.9+.

## Fastest safe activation path

Copy-paste this when you want the shortest local proof before touching a real
agent or provider key:

```bash
agentguard doctor
agentguard demo
agentguard quickstart --framework raw --write
python agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
```

This path proves local trace writing, budget stops, loop stops, retry stops,
and a runnable starter file without any network calls.

## Verify the install

Start with a local verification pass:

```bash
agentguard doctor
```

This stays fully local:
- no dashboard
- no network calls
- no hosted control-plane dependency

It verifies that AgentGuard can initialize in local-only mode, write a local
trace, and recommend the smallest correct next step for the current
environment.

## Generate the right starter

Once the SDK is verified locally, print the starter for the stack you actually
use:

```bash
agentguard quickstart --framework raw
agentguard quickstart --framework openai
agentguard quickstart --framework langchain --json
```

This is intentionally high-signal:
- no framework auto-detection
- no dashboard dependency
- no hidden file writes

It gives you the install command, the starter file contents, and the next
commands to run.

## Optional repo-local defaults

If you want a repo to carry safe local defaults, create `.agentguard.json`:

```json
{
  "profile": "coding-agent",
  "service": "support-agent",
  "trace_file": ".agentguard/traces.jsonl",
  "budget_usd": 5.0
}
```

This stays intentionally narrow:
- safe local defaults only
- no secrets
- no API keys
- no hosted control-plane behavior

After that, `agentguard.init()` can stay minimal:

```python
import agentguard

agentguard.init(local_only=True)
```

For coding-agent and repo-automation setups, follow
[`coding-agents.md`](coding-agents.md) after `doctor`, then use
[`coding-agent-safety-pack.md`](coding-agent-safety-pack.md) for copy-paste
repo instructions.

If you want AgentGuard to generate those repo-local instruction files instead
of copying snippets by hand:

```bash
agentguard skillpack --write
```

That writes `.agentguard.json` plus agent-specific instruction files into
`agentguard_skillpack/` for review before you copy or merge them into a real
repo.

## Offline demo

Before wiring a real agent, prove the SDK locally:

```bash
agentguard demo
```

This is fully offline:
- no API keys
- no dashboard
- no network calls

It writes a local trace file, demonstrates budget enforcement, loop detection,
and retry protection, then shows how to inspect the trace with `agentguard report`
and `agentguard incident`.

For a more realistic coding-agent failure mode, run the local review-loop proof:

```bash
python examples/coding_agent_review_loop.py
agentguard incident coding_agent_review_loop_traces.jsonl
```

This simulates repeated review/edit attempts and a stuck patch retry storm. It
uses `BudgetGuard` and `RetryGuard`, writes a local JSONL trace, and still makes
no network calls. A checked-in sample incident is available at
[`../examples/coding-agent-review-loop-incident.md`](../examples/coding-agent-review-loop-incident.md).

If your agent runtime uses disposable workers or managed-agent harnesses, add a
runtime `session_id` to correlate those short-lived traces:

```python
import agentguard

agentguard.init(
    service="managed-harness-a",
    session_id="support-session-001",
    local_only=True,
)
```

Guide: [`managed-agent-sessions.md`](managed-agent-sessions.md)

## 1. Trace an agent run

```python
from agentguard import Tracer, JsonlFileSink

tracer = Tracer(sink=JsonlFileSink(".agentguard/traces.jsonl"), service="my-agent")

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search for docs"})

    with span.span("tool.search", data={"query": "python asyncio"}) as tool:
        result = "found 3 results"  # your tool call here
        tool.event("tool.result", data={"result": result})

    span.event("reasoning.step", data={"thought": "summarize results"})
```

This writes every step to `.agentguard/traces.jsonl` — reasoning, tool calls,
timing, everything. The parent directory is created automatically.

## 2. View the trace

```bash
agentguard report .agentguard/traces.jsonl
```

```
AgentGuard report
  Total events: 6
  Spans: 2  Events: 4
  Approx run time: 0.3 ms
  Savings ledger: exact 0 tokens / $0.0000, estimated 0 tokens / $0.0000
```

Render an incident report:

```bash
agentguard incident .agentguard/traces.jsonl
```

## 3. Add a loop guard

Stop agents that repeat themselves. Guards auto-check on every `span.event()` call:

```python
from agentguard import Tracer, LoopGuard, LoopDetected, JsonlFileSink

tracer = Tracer(
    sink=JsonlFileSink(".agentguard/traces.jsonl"),
    service="my-agent",
    guards=[LoopGuard(max_repeats=3)],
)

with tracer.trace("agent.run") as span:
    for step in range(10):
        try:
            # LoopGuard checks fire on event(), not on span()
            span.event("tool.call", data={"tool": "search", "query": "test"})
        except LoopDetected as e:
            print(f"Loop caught: {e}")
            break
```

## 4. Add a budget guard

Cap spend per agent run:

```python
from agentguard import Tracer, BudgetGuard, JsonlFileSink

budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)
tracer = Tracer(
    sink=JsonlFileSink(".agentguard/traces.jsonl"),
    service="my-agent",
)

# Record usage where model calls happen.
budget.consume(calls=1, cost_usd=0.02)

# Raises BudgetExceeded when the limit is hit.
# Fires BudgetWarning at 80% of the limit.
```

If you want a local proof that token-based pricing can spike on one oversized
turn, run:

```bash
python examples/per_token_budget_spike.py
agentguard report per_token_budget_spike_traces.jsonl
```

That example prices each turn from token counts, then shows `BudgetGuard`
catching a single high-context spike before the run drifts further.

## 5. Auto-instrument OpenAI

Skip manual tracing — let AgentGuard patch the OpenAI client:

```python
from agentguard import BudgetGuard, Tracer, JsonlFileSink, patch_openai

budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)
tracer = Tracer(sink=JsonlFileSink(".agentguard/traces.jsonl"), service="my-agent")
patch_openai(tracer, budget_guard=budget)

# OpenAI chat completions are now traced with token counts, cost estimates, and budget checks.
# Works with openai>=1.0 client instances.
```

Same for Anthropic:

```python
from agentguard import patch_anthropic
patch_anthropic(tracer, budget_guard=budget)
```

## 6. Use with LangChain

```bash
pip install agentguard47[langchain]
```

```python
from agentguard import LoopGuard, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

handler = AgentGuardCallbackHandler(
    loop_guard=LoopGuard(max_repeats=3),
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)

# Pass to any LangChain LLM or agent:
result = agent.invoke(
    {"input": "your question"},
    config={"callbacks": [handler]},
)
```

## 7. Create an incident report

When a run blows through budget or hits a loop, render a shareable report:

```bash
agentguard incident .agentguard/traces.jsonl
agentguard incident .agentguard/traces.jsonl --format html > incident.html
```

The incident report highlights guard events, the exact-vs-estimated savings
ledger, and the upgrade path to retained alerts, team visibility, and remote
kill signal management.

## 8. Send traces to the dashboard

Swap the file sink for an HTTP sink when you need retained incidents, alerts,
team visibility, or hosted decision history:

```python
from agentguard import Tracer, HttpSink

sink = HttpSink(
    url="https://app.agentguard47.com/api/ingest",
    api_key="ag_...",
)
tracer = Tracer(sink=sink, service="my-agent")
```

Sign up at [app.agentguard47.com](https://app.agentguard47.com) to get an API key.

`HttpSink` mirrors trace and decision events to the dashboard. It does not poll
or execute dashboard remote kill signals by itself; local guards remain the
authoritative runtime stop path.

Hosted contract details: [`dashboard-contract.md`](dashboard-contract.md)

## Next steps

- [Examples](https://github.com/bmdhodl/agent47/tree/main/examples) — LangChain, CrewAI, OpenAI integration examples
- [Coding agents](https://github.com/bmdhodl/agent47/blob/main/docs/guides/coding-agents.md) — repo-local onboarding for Codex, Claude Code, Cursor, and similar tools
- [Guards reference](https://github.com/bmdhodl/agent47#guards) — LoopGuard, FuzzyLoopGuard, BudgetGuard, TimeoutGuard, RateLimitGuard, RetryGuard
- [Evaluation](https://github.com/bmdhodl/agent47#evaluation) — assertion-based trace analysis for CI
- [Incident Reports](https://github.com/bmdhodl/agent47#incident-reports) — local postmortem-style summaries for guard trips
- [Dashboard Contract](dashboard-contract.md) - hosted ingest, decision history, and remote-kill boundaries
- [Async support](https://github.com/bmdhodl/agent47#async) — AsyncTracer, async decorators
