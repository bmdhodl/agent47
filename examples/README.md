# AgentGuard Examples

Working examples showing AgentGuard integrated with popular AI agent frameworks.

## Start Here

If you want the smallest runnable file for a given stack, start in
[`examples/starters/`](./starters):

```bash
python examples/starters/agentguard_raw_quickstart.py
python examples/starters/agentguard_langgraph_quickstart.py
```

These starter files match the output from `agentguard quickstart` and are meant
for first-run onboarding by both humans and coding agents.

## Examples

| File | Framework | What it shows |
|------|-----------|---------------|
| **`cost_guardrail.py`** | **OpenAI** | **Full cost guardrail pipeline: auto-budget enforcement, warning/exceeded events, dashboard sync** |
| `langchain_rag_with_guards.py` | LangChain | RAG pipeline with loop detection + budget enforcement via callback handler |
| `crewai_with_guards.py` | CrewAI | Multi-agent crew with auto-traced OpenAI calls and budget limits |
| `openai_agents_with_guards.py` | OpenAI | Function-calling agent with LoopGuard, BudgetGuard, and structured tracing |

## Quick Start

```bash
pip install agentguard47
agentguard doctor
agentguard quickstart --framework raw
python examples/starters/agentguard_raw_quickstart.py

# Then print the starter for your real stack
agentguard quickstart --framework openai
agentguard quickstart --framework langchain

# Cost guardrail demo (recommended first networked example)
export OPENAI_API_KEY=sk-...
python examples/cost_guardrail.py

# Or with dashboard integration
export AGENTGUARD_API_KEY=ag_...
python examples/cost_guardrail.py

# Run any other example
python examples/openai_agents_with_guards.py
```

Each example writes traces to a local JSONL file. To send traces to the hosted dashboard instead, replace `JsonlFileSink` with `HttpSink`:

```python
from agentguard.sinks.http import HttpSink

sink = HttpSink(
    url="https://app.agentguard47.com/api/ingest",
    api_key="ag_your_key_here",
)
```

If a run trips a guard locally, generate an incident summary:

```bash
agentguard incident cost_guardrail_traces.jsonl
```
