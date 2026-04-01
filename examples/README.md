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
| **`cost_guardrail.py`** | **OpenAI** | **Full cost guardrail pipeline: auto-budget enforcement, warning/exceeded events, dashboard sync** |
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
