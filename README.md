# AgentGuard

**Your coding agent just started looping through retries and shell calls. AgentGuard stops it before it burns budget.**

Local-first runtime guardrails for coding agents. Stop loops, retry storms, and budget burn with a zero-dependency Python SDK, then expose traces and incident context through MCP when your tooling needs read access.

[![PyPI](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)
[![Downloads](https://img.shields.io/pypi/dm/agentguard47)](https://pypi.org/project/agentguard47/)
[![Python](https://img.shields.io/pypi/pyversions/agentguard47)](https://pypi.org/project/agentguard47/)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-93%25-brightgreen)](https://github.com/bmdhodl/agent47)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/bmdhodl/agent47/badge)](https://scorecard.dev/viewer/?uri=github.com/bmdhodl/agent47)
[![GitHub stars](https://img.shields.io/github/stars/bmdhodl/agent47?style=social)](https://github.com/bmdhodl/agent47)

```bash
pip install agentguard47
```

## Verify your install

Before wiring a real agent, validate the local SDK path:

```bash
agentguard doctor
```

`doctor` makes no network calls. It verifies local trace writing, confirms the
SDK can initialize in local-only mode, detects optional integrations already
installed in your environment, and prints the smallest correct next-step snippet.

## Generate a starter

When you know the stack you want to wire, print the exact starter snippet:

```bash
agentguard quickstart --framework raw
agentguard quickstart --framework openai
agentguard quickstart --framework langgraph --json
```

`quickstart` is designed for both humans and coding agents. It prints the
install command, the smallest credible starter file, and the next commands to
run after you validate the SDK locally.

## Coding-Agent Defaults

If you want humans and coding agents to share the same safe local defaults, add
a tiny `.agentguard.json` file to the repo:

```json
{
  "profile": "coding-agent",
  "service": "support-agent",
  "trace_file": ".agentguard/traces.jsonl",
  "budget_usd": 5.0
}
```

`agentguard.init(local_only=True)` and `agentguard doctor` will pick this up
automatically. Keep it local and static: no secrets, no API keys, no dashboard
settings.

Every `agentguard quickstart --framework ...` payload also has a matching
runnable file under [`examples/starters/`](examples/starters/). Those starter
files live in the repo for copy-paste onboarding and coding-agent setup; they
are not shipped inside the PyPI wheel.

For the repo-first onboarding flow, see
[`docs/guides/coding-agents.md`](docs/guides/coding-agents.md).

For copy-paste setup snippets tailored to Codex, Claude Code, GitHub Copilot,
Cursor, and MCP-capable agents, see
[`docs/guides/coding-agent-safety-pack.md`](docs/guides/coding-agent-safety-pack.md).

## MCP Server for Coding-Agent Workflows

If your coding agent already uses MCP, AgentGuard also ships a published
read-only MCP server that exposes traces, alerts, usage, costs, and budget
health from the AgentGuard read API:

```bash
npx -y @agentguard47/mcp-server
```

The MCP server is intentionally narrow. Use the SDK to enforce safety where the
agent runs. Add MCP when you want Codex, Claude Code, Cursor, or another
MCP-compatible client to inspect traces and incidents without bespoke glue.

## Try it in 60 seconds

No API keys. No dashboard. No network calls. Just run it:

```bash
pip install agentguard47
agentguard demo
```

```
AgentGuard offline demo
No API keys. No dashboard. No network calls.

1. BudgetGuard: stopping runaway spend
  warning fired at $0.84
  stopped on call 9: cost $1.08 exceeded $1.00

2. LoopGuard: stopping repeated tool calls
  stopped on repeated tool call: Loop detected ...

3. RetryGuard: stopping retry storms
  stopped retry storm: Retry limit exceeded ...

Local proof complete.
```

Prefer the example script instead of the CLI? This does the same local demo:

```bash
python examples/try_it_now.py
```

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bmdhodl/agent47/blob/main/examples/quickstart.ipynb)

## Quickstart: Stop a Runaway Coding Agent in 4 Lines

```python
from agentguard import Tracer, BudgetGuard, patch_openai

tracer = Tracer(guards=[BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)])
patch_openai(tracer)  # auto-tracks every OpenAI call

# Use OpenAI normally - AgentGuard tracks cost and kills the agent at $5
```

That's it. Every `ChatCompletion` call is tracked. When accumulated cost hits $4 (80%), your warning fires. At $5, `BudgetExceeded` is raised and the agent stops.

No config files. No dashboard required. No dependencies.

For a deterministic local proof before wiring a real agent, run:

```bash
agentguard doctor
agentguard quickstart --framework raw
agentguard demo
```

`agentguard doctor` verifies the install path. `agentguard quickstart` prints
the copy-paste starter for your stack. `agentguard demo` then proves SDK-only
enforcement with a realistic local run. Keep the first integration local and
only add hosted pieces after you need retained incidents or team-visible
follow-through.

## The Problem

Coding agents are cheap to start and expensive to leave unattended:
- **Cost overruns average 340%** on autonomous agent tasks ([source](https://arxiv.org/abs/2401.15811))
- A single stuck retry or tool loop can burn through your budget in minutes
- Existing tracing tools show you what happened after the burn, not stop the run while it is still happening

**AgentGuard is built to stop a runaway coding agent mid-run, not just explain the damage later.**

| | AgentGuard | LangSmith | Langfuse | Portkey |
|---|---|---|---|---|
| Hard budget enforcement | **Yes** | No | No | No |
| Kill agent mid-run | **Yes** | No | No | No |
| Loop detection | **Yes** | No | No | No |
| Cost tracking | **Yes** | Yes | Yes | Yes |
| Zero dependencies | **Yes** | No | No | No |
| Self-hosted option | **Yes** | No | Yes | No |
| Price | **Free (MIT)** | $2.50/1k traces | $59/mo | $49/mo |

## Guards

Guards are runtime checks that raise exceptions when limits are hit. The agent stops immediately.

| Guard | What it stops | Example |
|-------|--------------|---------|
| `BudgetGuard` | Dollar/token/call overruns | `BudgetGuard(max_cost_usd=5.00)` |
| `LoopGuard` | Exact repeated tool calls | `LoopGuard(max_repeats=3)` |
| `FuzzyLoopGuard` | Similar tool calls, A-B-A-B patterns | `FuzzyLoopGuard(max_tool_repeats=5)` |
| `TimeoutGuard` | Wall-clock time limits | `TimeoutGuard(max_seconds=300)` |
| `RateLimitGuard` | Calls-per-minute throttling | `RateLimitGuard(max_calls_per_minute=60)` |
| `RetryGuard` | Retry storms on the same flaky tool | `RetryGuard(max_retries=3)` |

```python
from agentguard import BudgetGuard, BudgetExceeded

budget = BudgetGuard(
    max_cost_usd=10.00,
    warn_at_pct=0.8,
    on_warning=lambda msg: print(f"WARNING: {msg}"),
)

# In your agent loop:
budget.consume(tokens=1500, calls=1, cost_usd=0.03)
# At 80% → warning callback fires
# At 100% → BudgetExceeded raised, agent stops
```

```python
from agentguard import RetryGuard, RetryLimitExceeded, Tracer

retry_guard = RetryGuard(max_retries=3)
tracer = Tracer(guards=[retry_guard])

with tracer.trace("agent.run") as span:
    try:
        span.event("tool.retry", data={"tool_name": "search", "attempt": 1})
        span.event("tool.retry", data={"tool_name": "search", "attempt": 2})
        span.event("tool.retry", data={"tool_name": "search", "attempt": 3})
        span.event("tool.retry", data={"tool_name": "search", "attempt": 4})
    except RetryLimitExceeded:
        # Retry storm stopped
        pass
```

## Integrations

### LangChain

```bash
pip install agentguard47[langchain]
```

```python
from agentguard import Tracer, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

tracer = Tracer(guards=[BudgetGuard(max_cost_usd=5.00)])
handler = AgentGuardCallbackHandler(
    tracer=tracer,
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)

# Pass to any LangChain component
llm = ChatOpenAI(callbacks=[handler])
```

### LangGraph

```bash
pip install agentguard47[langgraph]
```

```python
from agentguard.integrations.langgraph import guarded_node

@guarded_node(tracer=tracer, budget_guard=BudgetGuard(max_cost_usd=5.00))
def research_node(state):
    return {"messages": state["messages"] + [result]}
```

### CrewAI

```bash
pip install agentguard47[crewai]
```

```python
from agentguard.integrations.crewai import AgentGuardCrewHandler

handler = AgentGuardCrewHandler(
    tracer=tracer,
    budget_guard=BudgetGuard(max_cost_usd=5.00),
)

agent = Agent(role="researcher", step_callback=handler.step_callback)
```

### OpenAI / Anthropic Auto-Instrumentation

```python
from agentguard import Tracer, BudgetGuard, patch_openai, patch_anthropic

tracer = Tracer(guards=[BudgetGuard(max_cost_usd=5.00)])
patch_openai(tracer)      # auto-tracks all ChatCompletion calls
patch_anthropic(tracer)   # auto-tracks all Messages calls
```

## Cost Tracking

Built-in pricing for OpenAI, Anthropic, Google, Mistral, and Meta models. Updated monthly.

```python
from agentguard import estimate_cost

# Single call estimate
cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
# → $0.00625

# Track across a trace — cost is auto-accumulated per span
with tracer.trace("agent.run") as span:
    span.cost.add("gpt-4o", input_tokens=1200, output_tokens=450)
    span.cost.add("claude-sonnet-4-5-20250929", input_tokens=800, output_tokens=300)
    # cost_usd included in trace end event
```

## Tracing

Full structured tracing with zero dependencies — JSONL output, spans, events, and cost data.

```python
from agentguard import Tracer, JsonlFileSink, BudgetGuard

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    guards=[BudgetGuard(max_cost_usd=5.00)],
)

with tracer.trace("agent.run") as span:
    span.event("reasoning", data={"thought": "search docs"})
    with span.span("tool.search", data={"query": "quantum computing"}):
        pass  # your tool logic
    span.cost.add("gpt-4o", input_tokens=1200, output_tokens=450)
```

```bash
$ agentguard report traces.jsonl

AgentGuard report
  Total events: 9
  Spans: 6  Events: 3
  Estimated cost: $0.01
  Savings ledger: exact 800 tokens / $0.0010, estimated 1500 tokens / $0.0075
```

When a run trips a guard or needs escalation, render a shareable incident report:

```bash
agentguard incident traces.jsonl
agentguard incident traces.jsonl --format html > incident.html
```

The incident report summarizes guard triggers, exact-vs-estimated savings, and
the dashboard upgrade path for retained alerts and remote kill switch.

## Decision Tracing

Capture agent proposals, human edits, overrides, approvals, and binding
outcomes through the normal AgentGuard event path.

```python
from agentguard import JsonlFileSink, Tracer, decision_flow

tracer = Tracer(
    sink=JsonlFileSink(".agentguard/traces.jsonl"),
    service="approval-flow",
)

with tracer.trace("agent.run") as run:
    with decision_flow(
        run,
        workflow_id="deploy-approval",
        object_type="deployment",
        object_id="deploy-042",
        actor_type="agent",
        actor_id="release-bot",
    ) as decision:
        decision.proposed({"action": "deploy", "environment": "staging"})
        decision.edited(
            {"action": "deploy", "environment": "production"},
            actor_type="human",
            actor_id="reviewer-123",
            reason="Customer approved direct rollout",
        )
        decision.approved(actor_type="human", actor_id="reviewer-123")
        decision.bound(
            actor_type="system",
            actor_id="deploy-api",
            binding_state="applied",
            outcome="success",
        )
```

Every decision event includes a stable schema in `event.data`:

- `decision_id`
- `workflow_id`
- `trace_id`
- `object_type`
- `object_id`
- `actor_type`
- `actor_id`
- `event_type`
- `proposal`
- `final`
- `diff`
- `reason`
- `comment`
- `timestamp`
- `binding_state`
- `outcome`

Guide: [`docs/guides/decision-tracing.md`](docs/guides/decision-tracing.md)

## Evaluation

Assert properties of your traces in tests or CI.

```python
from agentguard import EvalSuite

result = (
    EvalSuite("traces.jsonl")
    .assert_no_loops()
    .assert_budget_under(tokens=50_000)
    .assert_completes_within(seconds=30)
    .assert_total_events_under(500)
    .assert_no_budget_exceeded()
    .assert_no_errors()
    .run()
)
```

```bash
agentguard eval traces.jsonl --ci   # exits non-zero on failure
```

## CI Cost Gates

Fail your CI pipeline if an agent run exceeds a cost budget. No competitor offers this.

```yaml
# .github/workflows/cost-gate.yml (simplified)
- name: Run agent with budget guard
  run: |
    python3 -c "
    from agentguard import Tracer, BudgetGuard, JsonlFileSink
    tracer = Tracer(
        sink=JsonlFileSink('ci_traces.jsonl'),
        guards=[BudgetGuard(max_cost_usd=5.00)],
    )
    # ... your agent run here ...
    "

- name: Evaluate traces
  uses: bmdhodl/agent47/.github/actions/agentguard-eval@main
  with:
    trace-file: ci_traces.jsonl
    assertions: "no_errors,max_cost:5.00"
```

Full workflow: [`docs/ci/cost-gate-workflow.yml`](docs/ci/cost-gate-workflow.yml)

## Incident Reports

Turn a trace into a postmortem-style incident summary:

```bash
agentguard incident traces.jsonl --format markdown
agentguard incident traces.jsonl --format html > incident.html
```

Use this when a run hits `guard.budget_warning`, `guard.budget_exceeded`,
`guard.loop_detected`, or a fatal error. AgentGuard will summarize the run,
separate exact and estimated savings, and suggest the next control-plane step.

## Async Support

Full async API mirrors the sync API.

```python
from agentguard import AsyncTracer, BudgetGuard, patch_openai_async

tracer = AsyncTracer(guards=[BudgetGuard(max_cost_usd=5.00)])
patch_openai_async(tracer)

# All async OpenAI calls are now tracked and budget-enforced
```

## Optional Hosted Dashboard

For teams that need retained history, alerts, and remote controls, the SDK can
mirror traces to the hosted dashboard:

```python
from agentguard import Tracer, HttpSink, BudgetGuard

tracer = Tracer(
    sink=HttpSink(
        url="https://app.agentguard47.com/api/ingest",
        api_key="ag_...",
        batch_size=20,
        flush_interval=10.0,
        compress=True,
    ),
    guards=[BudgetGuard(max_cost_usd=50.00)],
    metadata={"env": "prod"},
    sampling_rate=0.1,  # 10% of traces
)
```

Keep the first integration local. Add `HttpSink` only when you need retained
incidents, alerts, or hosted follow-through.

## Architecture

```
Your Agent Code
    │
    ▼
┌─────────────────────────────────────┐
│           Tracer / AsyncTracer       │  ← trace(), span(), event()
│  ┌───────────┐  ┌────────────────┐  │
│  │  Guards    │  │  CostTracker   │  │  ← runtime intervention
│  └───────────┘  └────────────────┘  │
└──────────┬──────────────────────────┘
           │ emit(event)
    ┌──────┼──────────┬───────────┐
    ▼      ▼          ▼           ▼
 JsonlFile  HttpSink  OtelTrace  Stdout
  Sink      (gzip,    Sink       Sink
            retry)
```

## What's in this repo

| Directory | Description | License |
|-----------|-------------|---------|
| `sdk/` | Python SDK — guards, tracing, evaluation, integrations | MIT |
| `mcp-server/` | Read-only MCP surface for traces, alerts, usage, costs, and budget health | MIT |
| `site/` | Landing page | MIT |

> Dashboard is in a separate private repo ([agent47-dashboard](https://github.com/bmdhodl/agent47-dashboard)).

## Security

- **Zero runtime dependencies** — one package, nothing to audit, no supply chain risk
- **[OpenSSF Scorecard](https://scorecard.dev/viewer/?uri=github.com/bmdhodl/agent47)** — automated security analysis on every push
- **CodeQL scanning** — GitHub's semantic code analysis on every PR
- **Bandit security linting** — Python-specific security checks in CI

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup, test commands, and PR guidelines.

## Commercial Support

Need help rolling out coding-agent safety in production? BMD Pat LLC offers:

- **$500 Async Azure Audit** -- cost, reliability, and governance review. No meetings. Results in 5 business days.
- **Custom agent guardrails** -- production-grade cost controls, compliance tooling, kill switches.

[Start a project](https://bmdpat.com/start) | [See the research](https://bmdpat.com/research)

## License

MIT (BMD PAT LLC)
