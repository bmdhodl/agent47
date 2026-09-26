# AgentGuard

Stop runaway agents with runtime checks in Python.

[![PyPI version](https://img.shields.io/pypi/v/agentguard47)](https://pypi.org/project/agentguard47/)
[![Python versions](https://img.shields.io/pypi/pyversions/agentguard47)](https://pypi.org/project/agentguard47/)
[![CI](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/bmdhodl/agent47/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/bmdhodl/agent47)](LICENSE)

AgentGuard checks budgets, repeated tool calls, retries, and elapsed time in
instrumented Python code. Guards raise exceptions so your application can stop
the next operation. The base SDK has no runtime dependencies and needs no account.

**Names:** this repository is `agent47`, the PyPI package is `agentguard47`,
and the Python import is `agentguard`. Requires Python 3.9 or newer.

## Getting started

Install in a virtual environment, then run the offline checks:

```bash
python -m pip install agentguard47
agentguard doctor
agentguard demo
```

`doctor` checks the installation and local trace writing. `demo` exercises
budget, loop, and retry stops without provider keys or network access. Follow
the trace path printed by the command to inspect its output.
`agentguard demo --feedback` prints a local redacted report; nothing is sent.

`agentguard receipt agentguard_demo_traces.jsonl` prints a receipt of each stop
with the trace's SHA-256 drawn as a barcode. Add `--format markdown` to paste it
into a PR or issue. The hash identifies the trace file; it is not a signature.

### Guard a Claude Code session

```bash
agentguard hook claude-code --install --write
```

This installs a Claude Code hook that refuses the third identical tool call in
a row and a call that already failed twice. Refusals go to
`.agentguard/claude-code/trace.jsonl`. It checks tool calls, not tokens or
subscription quota. See the [Claude Code hook guide](docs/guides/claude-code-hook.md).

### Guard a script without editing it

```bash
agentguard run --budget-usd 5 agent.py
```

This patches the OpenAI and Anthropic clients, then runs `agent.py` in the same
interpreter. Settings come from flags, then environment variables, then
`.agentguard.json`. A guard stop exits 1. Every run ends with the trace path on
stderr, ready for `agentguard receipt`. `agentguard run python -m mypkg` works too. The bounds are
the same as patching the client yourself; see
[enforcement boundary](docs/enforcement-boundary.md).

### Stop before a third call

Save this as `budget_demo.py` and run `python budget_demo.py`. It makes no
network requests.

```python
from agentguard import BudgetExceeded, BudgetGuard

budget = BudgetGuard(max_calls=2)
completed = 0

for _ in range(3):
    try:
        budget.check()  # Check before the operation.
        # Put your provider or tool call here.
        completed += 1
        budget.consume(calls=1)  # Record the completed operation.
    except BudgetExceeded:
        print(f"Stopped before call {completed + 1}")

assert completed == 2
```

Expected output: `Stopped before call 3`.

### Connect a provider

Install the provider's client separately. For OpenAI:

```bash
python -m pip install openai
```

```python
from agentguard import BudgetGuard, JsonlFileSink, Tracer, patch_openai

budget = BudgetGuard(max_cost_usd=5.00)
tracer = Tracer(
    service="my-agent",
    sink=JsonlFileSink(".agentguard/traces.jsonl"),
)
patch_openai(tracer, budget_guard=budget)
# Make your OpenAI chat.completions.create calls after this setup.
```

The patch checks recorded usage before dispatch and records response usage
afterward, including streamed calls once the final usage arrives. A response
can exceed the remaining cost or token allowance. Concurrent requests do not
reserve capacity. OpenAI streams request `include_usage` unless the caller
already set it. See the [getting started guide](docs/guides/getting-started.md)
for setup, traces, and framework starters.

## How enforcement works

```mermaid
flowchart TD
    accTitle: AgentGuard operation checks
    accDescr: Check a limit before an operation, then record usage.
    A[Instrumented operation] --> B{Guard check}
    B -->|Limit reached| C[Raise exception]
    B -->|Allowed| D[Run operation]
    D --> E[Record usage and trace]
    E --> A
```

Text equivalent: check before an operation, run it if allowed, then record
usage. A guard exception returns control to your application's error handler.

| Guard | Checks | Raises |
| --- | --- | --- |
| `BudgetGuard` | Recorded calls, tokens, or estimated cost | `BudgetExceeded` |
| `LoopGuard` | Repeated tool calls | `LoopDetected` |
| `FuzzyLoopGuard` | Tool frequency and alternating patterns | `LoopDetected` |
| `RetryGuard` | Retries per tool | `RetryLimitExceeded` |
| `TimeoutGuard` | Elapsed time when checked | `TimeoutExceeded` |
| `RateLimitGuard` | Calls within a sliding minute | `BudgetExceeded` |
| `X402SpendGuard` | Payment amounts before the payment callback | `BudgetExceeded` |

For task budgets, use `BudgetGuard.goal(...)`. For signatures and defaults,
read the [guard source](sdk/agentguard/guards.py) and
[public exports](sdk/agentguard/__init__.py).

## Limits and security

- Guards cover operations you instrument. Installing the package does not
  intercept every action in Cursor, Claude Code, or another agent.
- A guard is not a sandbox or permission system. A permitted operation can
  still be destructive.
- Timeout checks do not interrupt an already blocked function or cancel an
  agent running on a provider's server.
- Cost estimates are not invoices. Supply reported cost or use strict cost
  resolution when an estimate is insufficient.
- Recorded-budget preflight refuses the next instrumented call when stored
  usage is already at a cap. It does not reserve concurrent in-flight
  requests, predict the next response, or cap a provider subscription.
  See the [enforcement boundary](docs/enforcement-boundary.md).
- The base SDK uses the standard library. Optional framework extras install
  third-party dependencies and need their own security review.
- The optional `[crewai]` extra pulls ChromaDB. The
  [2026-09-12 audit](proof/audit-20260912/README.md) found four unresolved
  advisories, including [PYSEC-2026-311 / CVE-2026-45829](https://github.com/advisories/GHSA-f4j7-r4q5-qw2c).
  Review that exposure before installing the extra. Base SDK installs do not
  include ChromaDB.
- Trace content can contain application data. Review it before sharing or
  configuring a remote sink.

See [security reporting](SECURITY.md), the
[dated dependency audit](proof/audit-20260912/README.md), and
[release notes](CHANGELOG.md). Audit results describe their recorded date,
not a permanent clean bill of health.

## Local traces and optional hosted ingest

The SDK is the free local proof path. Start local. Add hosted ingest only
when you need retained history, alerts, team visibility, spend trends,
hosted decision history, or dashboard-managed remote kill signals.

Local guards remain authoritative. `HttpSink` mirrors trace and decision events;
it does not execute remote kill signals by itself. See the
[dashboard contract](docs/guides/dashboard-contract.md) before configuring it.

Local use has no hosted event quota, retention period, or API-key allocation.
Network egress requires an integration you configure, such as `HttpSink` or
an OpenTelemetry exporter.

Nothing in the local SDK phones home. The
[AgentGuard website](https://bmdpat.com/tools/agentguard?utm_source=agentguard47&utm_medium=readme&utm_campaign=touchpoints)
describes the optional hosted service.

## Documentation

| You want to | Start here |
| --- | --- |
| See which paths actually stop a call | [Enforcement boundary](docs/enforcement-boundary.md) |
| Install and trace a first run | [Getting started](docs/guides/getting-started.md) |
| Find guides and source references | [Documentation index](docs/README.md) |
| Try a runnable example | [Examples](examples/) |
| Connect LangChain, LangGraph, or CrewAI | [Integration guides](docs/integrations/) |
| Inspect hosted data through MCP | [Read-only TypeScript MCP server](mcp-server/) |
| Use local budget tools through MCP | [Python budget MCP server](agentguard-mcp/) |
| Navigate with an AI assistant | [AI documentation index](llms.txt) |
| Contribute a fix | [Contributing](CONTRIBUTING.md) |
| Check what changed | [Changelog](CHANGELOG.md) |

## Help and maintenance

Maintained by [Patrick Hughes](https://github.com/bmdhodl).
[Report a bug](https://github.com/bmdhodl/agent47/issues) with the package
version, a minimal reproduction, and the expected result. Report vulnerabilities
through [SECURITY.md](SECURITY.md).

The source metadata defines the branch version. The PyPI badge links to the
published version. Documentation examples and local links are tested in CI.
The PyPI README is generated from this README and the changelog.

[MIT license](LICENSE).
