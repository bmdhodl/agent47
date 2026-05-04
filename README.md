# AgentGuard

**Stop runaway Python agents before they burn money.**

AgentGuard47 is a zero-dependency runtime control SDK for Python agents. Add
hard budget caps, loop detection, retry limits, timeouts, local traces, and
incident reports without changing agent frameworks or sending data anywhere by
default.

Use it when an agent can call tools, retry work, review code, or run long
enough to create surprise spend.

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

## Why AgentGuard

Most agent tooling tells you what happened after the run. AgentGuard stops the
bad run while it is happening.

| Problem | What AgentGuard does |
|---|---|
| Agent loops on the same tool | Raises `LoopDetected` |
| Flaky tool retries forever | Raises `RetryLimitExceeded` |
| Run spends too much | Raises `BudgetExceeded` |
| Run hangs | Raises `TimeoutExceeded` |
| Team needs proof | Writes local JSONL traces and incident reports |
| Dashboard comes later | `HttpSink` mirrors events only when you opt in |

Design constraints:

- zero runtime dependencies
- MIT licensed
- local-first by default
- no API key required for local proof
- no network calls unless you configure `HttpSink`
- guards raise exceptions inside the running process

## Local Proof In 60 Seconds

```bash
agentguard doctor
agentguard demo
agentguard quickstart --framework raw
```

`doctor` verifies the install and local trace writing.
`demo` proves budget, loop, and retry stops offline.
`quickstart` prints the smallest starter for your stack.

Expected first value moment:

```text
BudgetGuard stops simulated spend.
LoopGuard stops repeated tool calls.
RetryGuard stops a retry storm.
No API keys. No dashboard. No network calls.
```

Notebook version:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bmdhodl/agent47/blob/main/examples/quickstart.ipynb)

## Copy-Paste Repo Setup

Use this when you want a coding agent or teammate to add AgentGuard safely:

```bash
pip install agentguard47
agentguard doctor
agentguard quickstart --framework raw --write
python agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
```

Optional shared local defaults, saved as `.agentguard.json` in the repo root:

```json
{
  "profile": "coding-agent",
  "service": "my-agent",
  "trace_file": ".agentguard/traces.jsonl",
  "budget_usd": 5.0
}
```

Keep the first PR local-only. Add hosted ingest later only when retained
incidents, alerts, or team visibility matter.

## Quickstart: Guard One Agent Run

```python
from agentguard import BudgetGuard, JsonlFileSink, LoopGuard, Tracer

budget = BudgetGuard(max_cost_usd=5.00, max_calls=50, warn_at_pct=0.8)
loop = LoopGuard(max_repeats=3)
tracer = Tracer(
    sink=JsonlFileSink(".agentguard/traces.jsonl"),
    service="support-agent",
    guards=[loop],
)

with tracer.trace("agent.run") as span:
    budget.consume(calls=1, cost_usd=0.02)
    loop.check("search", {"query": "refund policy"})
    span.event("tool.call", data={"tool": "search", "query": "refund policy"})
    # Call your agent or tool here.
```

Inspect the local proof:

```bash
agentguard report .agentguard/traces.jsonl
agentguard incident .agentguard/traces.jsonl
```

## Auto-Patch Provider SDKs

If you already call OpenAI or Anthropic directly, patch once and keep using the
provider normally:

```python
from agentguard import BudgetGuard, Tracer, patch_openai

budget = BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)
tracer = Tracer(service="support-agent")
patch_openai(tracer, budget_guard=budget)

# OpenAI chat completions are now traced and budget-enforced.
```

When accumulated cost crosses the hard limit, `BudgetExceeded` is raised and
the agent stops.

## Guards

| Guard | Stops | Example |
|---|---|---|
| `BudgetGuard` | dollar, token, or call overruns | `BudgetGuard(max_cost_usd=5.00)` |
| `LoopGuard` | exact repeated tool calls | `LoopGuard(max_repeats=3)` |
| `FuzzyLoopGuard` | similar calls and A-B-A-B loops | `FuzzyLoopGuard(max_tool_repeats=5)` |
| `RetryGuard` | retry storms on the same tool | `RetryGuard(max_retries=3)` |
| `TimeoutGuard` | long-running jobs | `TimeoutGuard(max_seconds=300)` |
| `RateLimitGuard` | calls per minute | `RateLimitGuard(max_calls_per_minute=60)` |
| `BudgetAwareEscalation` | hard turns that need a stronger model | `BudgetAwareEscalation(...)` |

Guards are static runtime checks. They do not ask another model whether a run is
safe. They raise exceptions.

## Examples

All examples are local-first. No API key is required unless the example says so.

| Example | What it proves |
|---|---|
| [`examples/try_it_now.py`](examples/try_it_now.py) | budget, loop, and retry stops |
| [`examples/coding_agent_review_loop.py`](examples/coding_agent_review_loop.py) | review/refinement loop stopped by budget and retry guards |
| [`examples/per_token_budget_spike.py`](examples/per_token_budget_spike.py) | one oversized token-heavy turn can blow a run budget |
| [`examples/budget_aware_escalation.py`](examples/budget_aware_escalation.py) | when to escalate from a cheap model to a stronger one |
| [`examples/decision_trace_workflow.py`](examples/decision_trace_workflow.py) | proposal, edit, approval, and binding decision events |

Sample incident:
[`docs/examples/coding-agent-review-loop-incident.md`](docs/examples/coding-agent-review-loop-incident.md)

Proof gallery:
[`docs/examples/proof-gallery.md`](docs/examples/proof-gallery.md)

Starter files:
[`examples/starters/`](examples/starters/)

## Framework Integrations

AgentGuard can wrap raw Python code or integrate with common agent stacks.

```bash
agentguard quickstart --framework raw
agentguard quickstart --framework openai
agentguard quickstart --framework anthropic
agentguard quickstart --framework langchain
agentguard quickstart --framework langgraph
agentguard quickstart --framework crewai
```

Optional integration extras are opt-in. The core SDK stays stdlib-only.

```bash
pip install "agentguard47[langchain]"
pip install "agentguard47[langgraph]"
pip install "agentguard47[crewai]"
pip install "agentguard47[otel]"
```

## Runtime Control vs Observability

AgentGuard is not a generic tracing platform. It is the local runtime stop
layer.

| Capability | AgentGuard |
|---|---|
| In-process hard budget caps | Yes |
| Kill a bad run by raising an exception | Yes |
| Loop and retry-storm detection | Yes |
| Local JSONL traces | Yes |
| Local incident reports | Yes |
| Hosted ingest | Optional |
| Required dashboard | No |
| Runtime dependencies | None |

Competitive notes:

- [AgentGuard vs Vercel AI Gateway](docs/competitive/vercel-ai-gateway.md)
- [Where AgentGuard fits in the agent security stack](docs/competitive/agent-security-stack.md)

## Decision Traces

Capture proposal, human edit, approval, override, and binding events through the
same event pipeline:

```python
from agentguard import JsonlFileSink, Tracer, decision_flow

tracer = Tracer(sink=JsonlFileSink(".agentguard/traces.jsonl"))

with tracer.trace("agent.run") as run:
    with decision_flow(
        run,
        workflow_id="deploy-review",
        object_type="pull_request",
        object_id="123",
        actor_type="human",
        actor_id="pat",
    ) as decision:
        decision.proposed({"action": "merge"})
        decision.approved(comment="Looks safe")
        decision.bound(binding_state="merged", outcome="success")
```

Supported event types:

- `decision.proposed`
- `decision.edited`
- `decision.overridden`
- `decision.approved`
- `decision.bound`

Guide: [`docs/guides/decision-tracing.md`](docs/guides/decision-tracing.md)

## MCP Server

AgentGuard also ships a read-only MCP server for coding-agent workflows:

```bash
npx -y @agentguard47/mcp-server
```

Use the SDK to enforce local safety where the agent runs. Use MCP when a client
like Codex, Claude Code, or Cursor needs read access to traces, decisions,
costs, usage, and budget health.

## Hosted Dashboard Boundary

The SDK is the free local proof path. The hosted dashboard is for retained
history, alerts, team visibility, hosted decision history, and remote-control
operations.

| Use local SDK when | Use hosted dashboard when |
| --- | --- |
| You are proving AgentGuard in one repo | Multiple people need the same incident history |
| You need hard stops for loops, retries, timeouts, or budget burn | Runs need retained alerts and follow-up outside the terminal |
| You want JSONL traces and reports without an API key | You need spend trends across traces, services, or teammates |
| You are testing an agent before production | Operators need dashboard-managed remote kill signals |

Start local. Add hosted ingest when the work becomes shared, expensive, or
risky enough that local files are no longer enough.

```python
from agentguard import HttpSink, Tracer

tracer = Tracer(
    sink=HttpSink(
        url="https://app.agentguard47.com/api/ingest",
        api_key="ag_...",
    )
)
```

`HttpSink` mirrors trace and decision events to the dashboard. It does not
execute remote kill signals by itself.

Dashboard contract:
[`docs/guides/dashboard-contract.md`](docs/guides/dashboard-contract.md)

## Reports And CI Gates

Generate a local incident report:

```bash
agentguard incident .agentguard/traces.jsonl --format markdown
agentguard incident .agentguard/traces.jsonl --format html
```

Fail CI when a trace violates safety expectations:

```python
from agentguard import EvalSuite

result = (
    EvalSuite(".agentguard/traces.jsonl")
    .assert_no_loops()
    .assert_budget_under(tokens=50_000)
    .assert_no_errors()
    .run()
)

assert result.passed
```

## Package Facts

- Package: [`agentguard47`](https://pypi.org/project/agentguard47/)
- Python: 3.9+
- License: MIT
- Core runtime dependencies: zero
- Trace format: JSONL
- Local commands: `doctor`, `demo`, `quickstart`, `report`, `incident`, `eval`
- MCP package: [`@agentguard47/mcp-server`](mcp-server/)

## Docs

| Topic | Link |
|---|---|
| Getting started | [`docs/guides/getting-started.md`](docs/guides/getting-started.md) |
| Coding-agent setup | [`docs/guides/coding-agents.md`](docs/guides/coding-agents.md) |
| Safety pack | [`docs/guides/coding-agent-safety-pack.md`](docs/guides/coding-agent-safety-pack.md) |
| Dashboard contract | [`docs/guides/dashboard-contract.md`](docs/guides/dashboard-contract.md) |
| Decision traces | [`docs/guides/decision-tracing.md`](docs/guides/decision-tracing.md) |
| Managed sessions | [`docs/guides/managed-agent-sessions.md`](docs/guides/managed-agent-sessions.md) |
| Activation metrics design | [`docs/guides/activation-metrics-design.md`](docs/guides/activation-metrics-design.md) |
| Proof gallery | [`docs/examples/proof-gallery.md`](docs/examples/proof-gallery.md) |
| PyPI Trusted Publishing | [`docs/release/trusted-publishing.md`](docs/release/trusted-publishing.md) |

## Architecture

```text
agent code
   |
   v
Tracer
   |
   +-- guards raise exceptions locally
   |
   +-- sinks write traces locally or mirror to hosted ingest
```

Repository layout:

```text
sdk/          Python SDK package
mcp-server/   read-only MCP server
docs/         guides and competitive notes
examples/     runnable local examples
ops/          repo operating docs
memory/       SDK-only state and decisions
```

## Security

- No secrets are required for local mode.
- Do not put API keys in `.agentguard.json`.
- Hosted ingest API keys should be stored in environment variables.
- Local guards remain authoritative even when hosted ingest is configured.

Report security issues through GitHub Security Advisories or by email:
`pat@bmdpat.com`.

## Contributing

Contributions are welcome when they keep the SDK small, local-first, and
zero-dependency.

Before opening a PR:

```bash
python -m pytest sdk/tests/ -v
python -m ruff check sdk/agentguard/
python scripts/sdk_release_guard.py
```

Useful links:

- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`GOLDEN_PRINCIPLES.md`](GOLDEN_PRINCIPLES.md)
- [good first issues](https://github.com/bmdhodl/agent47/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22)

## License

MIT. See [`LICENSE`](LICENSE).
