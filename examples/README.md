# AgentGuard Examples

Working examples showing AgentGuard integrated with popular AI agent frameworks.

## Examples

| File | Framework | What it shows |
|------|-----------|---------------|
| `langchain_rag_with_guards.py` | LangChain | RAG pipeline with loop detection + budget enforcement via callback handler |
| `crewai_with_guards.py` | CrewAI | Multi-agent crew with auto-traced OpenAI calls and budget limits |
| `openai_agents_with_guards.py` | OpenAI | Function-calling agent with LoopGuard, BudgetGuard, and structured tracing |

## Quick Start

```bash
pip install agentguard47
export OPENAI_API_KEY=sk-...

# Run any example
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
