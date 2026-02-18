---
title: "How to Add Cost Gates to Your AI Agent CI Pipeline"
published: true
tags: [ai, python, cicd, devops]
description: "Fail CI if your AI agent exceeds a dollar budget. A GitHub Actions workflow for cost-controlled agent testing."
canonical_url: https://github.com/bmdhodl/agent47/blob/main/docs/blog/003-ci-cost-gates-devto.md
---

Your AI agent passes all your tests. Great. But did you check how much it *cost*?

Most CI pipelines test for correctness — they don't test for cost. A single agent run can burn $5, $50, or $500 depending on model choice, tool loops, and context window size. In CI, this adds up fast: 10 PRs × 3 test runs × $5/run = $150/day in API costs.

**AgentGuard adds cost gates to your CI pipeline.** If an agent run exceeds a dollar threshold, CI fails. No surprises on your OpenAI invoice.

## The Problem

AI agent tests are fundamentally different from unit tests:

1. **Non-deterministic** — the same input can produce different (and differently priced) outputs
2. **Expensive** — each run costs real money in API calls
3. **Unbounded** — an agent can make 3 tool calls or 300, and you won't know until the bill arrives

Traditional test assertions don't catch these issues. `assert result == expected` doesn't tell you the test cost $12.

## The Solution: Cost Gates in CI

Here's a GitHub Actions workflow that runs your agent with a budget guard and fails if costs exceed a threshold:

```yaml
name: Cost Gate

on:
  pull_request:
    branches: [main]

jobs:
  cost-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install agentguard47

      - name: Run agent with budget guard
        run: |
          python3 -c "
          from agentguard import Tracer, BudgetGuard, JsonlFileSink

          tracer = Tracer(
              sink=JsonlFileSink('ci_traces.jsonl'),
              service='ci-agent-test',
              guards=[BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)],
          )

          with tracer.trace('ci.agent_run') as span:
              # Your agent code here
              pass
          "

      - name: Evaluate traces
        if: always()
        uses: bmdhodl/agent47/.github/actions/agentguard-eval@main
        with:
          trace-file: ci_traces.jsonl
          assertions: "no_errors,max_cost:5.00"
```

## What This Does

1. **BudgetGuard** tracks cost during the agent run. If the agent exceeds $5, it raises `BudgetExceeded` and the run stops immediately.
2. **JsonlFileSink** writes structured traces to a file for post-run analysis.
3. **agentguard-eval** action reads the trace file and asserts:
   - No errors occurred
   - Total cost stayed under $5.00
4. If any assertion fails, **CI fails**. The eval action posts results as a PR comment.

## Auto-Tracking Cost with OpenAI

If your agent uses OpenAI, AgentGuard can auto-track cost per API call:

```python
from agentguard import Tracer, BudgetGuard, JsonlFileSink, patch_openai

tracer = Tracer(
    sink=JsonlFileSink("ci_traces.jsonl"),
    service="ci-agent-test",
    guards=[BudgetGuard(max_cost_usd=5.00)],
)
patch_openai(tracer)  # auto-tracks cost for every ChatCompletion call

# Now run your agent normally — costs are tracked automatically
```

No manual `consume()` calls needed. AgentGuard intercepts OpenAI responses, extracts token counts, and estimates cost using published pricing.

## Multiple Assertions

The eval action supports several assertion types:

```yaml
assertions: "no_errors,max_cost:5.00,max_duration:30,max_events:100"
```

- `no_errors` — no error events in the trace
- `max_cost:X` — total cost under $X
- `max_duration:X` — no span longer than X seconds
- `max_events:X` — total event count under X (catches runaway loops)

## Why This Matters

Every other agent observability tool (LangSmith, Langfuse, Portkey) shows you cost *after* the run. AgentGuard is the only tool that:

1. **Kills the agent mid-run** when the budget is exceeded
2. **Fails CI** if cost thresholds are breached
3. **Does it with zero dependencies** — stdlib Python only

## Try It

```bash
pip install agentguard47
```

Full workflow file: [docs/ci/cost-gate-workflow.yml](https://github.com/bmdhodl/agent47/blob/main/docs/ci/cost-gate-workflow.yml)

Repo: [github.com/bmdhodl/agent47](https://github.com/bmdhodl/agent47)
