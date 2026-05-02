# AgentGuard Examples

Working examples showing AgentGuard integrated with popular AI agent frameworks.

## Coding-Agent Starter Flow

Start here if you want the smallest repo-local onboarding loop:

```bash
pip install agentguard47
agentguard doctor
python examples/starters/agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
```

The starter files under `examples/starters/` are the executable counterparts to
`agentguard quickstart`. They live in this repo for copy-paste onboarding and
coding-agent setup; they are not included in the installed PyPI wheel.

## Framework Examples

| File | Framework | What it shows |
|------|-----------|---------------|
| `budget_aware_escalation.py` | Raw AgentGuard | Advisor-style escalation from a cheaper local model to a stronger model on hard turns |
| `coding_agent_review_loop.py` | Raw AgentGuard | Local coding-agent review loop proof: repeated review/edit retries trip `BudgetGuard` and `RetryGuard` without network calls |
| `disposable_harness_session.py` | Raw AgentGuard | Two tracer instances sharing one `session_id` to simulate a managed-agent session across disposable harnesses |
| `per_token_budget_spike.py` | Raw AgentGuard | Local token-metered pricing proof: one oversized turn triggers `BudgetGuard` without any API key |
| **`cost_guardrail.py`** | **OpenAI** | **Full cost guardrail pipeline: auto-budget enforcement, warning/exceeded events, dashboard sync** |
| `decision_trace_workflow.py` | Raw AgentGuard | Agent proposal, human edit, approval, and binding outcome captured through the normal event pipeline |
| `langchain_rag_with_guards.py` | LangChain | RAG pipeline with loop detection + budget enforcement via callback handler |
| `crewai_with_guards.py` | CrewAI | Multi-agent crew with auto-traced OpenAI calls and budget limits |
| `openai_agents_with_guards.py` | OpenAI | Function-calling agent with LoopGuard, BudgetGuard, and structured tracing |

## Quick Start

```bash
pip install agentguard47
agentguard doctor
python examples/starters/agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl

# Then print or run the starter for your real stack
agentguard quickstart --framework openai
agentguard quickstart --framework langchain
python examples/starters/agentguard_openai_quickstart.py

# Cost guardrail demo (recommended first networked example)
export OPENAI_API_KEY=sk-...
python examples/cost_guardrail.py

# Decision-trace demo (local-only)
python examples/decision_trace_workflow.py

# Disposable harness / managed-session demo (local-only)
python examples/disposable_harness_session.py

# Per-token budget spike demo (local-only)
python examples/per_token_budget_spike.py

# Coding-agent review loop demo (local-only)
python examples/coding_agent_review_loop.py
agentguard incident coding_agent_review_loop_traces.jsonl

# Advisor-style escalation demo (local-only)
python examples/budget_aware_escalation.py

# Or with dashboard integration
export AGENTGUARD_API_KEY=ag_...
python examples/cost_guardrail.py

# Run any other example
python examples/openai_agents_with_guards.py
```

Sample incident output from a clean coding-agent review-loop run:
[`docs/examples/coding-agent-review-loop-incident.md`](../docs/examples/coding-agent-review-loop-incident.md)

Each example writes traces to a local JSONL file. To send traces to the hosted dashboard instead, replace `JsonlFileSink` with `HttpSink`:

```python
from agentguard.sinks.http import HttpSink

sink = HttpSink(
    url="https://app.agentguard47.com/api/ingest",
    api_key="ag_your_key_here",
)
```

`HttpSink` mirrors trace and decision events. It does not poll or execute
dashboard remote kill signals by itself.

If a run trips a guard locally, generate an incident summary:

```bash
agentguard incident cost_guardrail_traces.jsonl
```
