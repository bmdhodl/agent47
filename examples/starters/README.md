# Starter Files

These are the executable counterparts to `agentguard quickstart`.

Each file is intentionally small:
- one supported stack
- one obvious install command
- one obvious run command
- local traces by default

They live in this repo for copy-paste onboarding and coding-agent setup. They
are not included in the installed PyPI wheel.

## Files

| File | Stack | Local-first behavior |
|------|-------|----------------------|
| `agentguard_raw_quickstart.py` | Raw Python | Fully offline. No API keys or network calls. |
| `agentguard_openai_quickstart.py` | OpenAI | Local traces via `local_only=True`; OpenAI call still uses `OPENAI_API_KEY`. |
| `agentguard_anthropic_quickstart.py` | Anthropic | Local traces via `local_only=True`; Anthropic call still uses `ANTHROPIC_API_KEY`. |
| `agentguard_langchain_quickstart.py` | LangChain | Explicit callback wiring with local traces. |
| `agentguard_langgraph_quickstart.py` | LangGraph | Fully local graph example with node guards. |
| `agentguard_crewai_quickstart.py` | CrewAI | Explicit callback wiring with local traces. |

## Suggested flow

```bash
pip install agentguard47
agentguard doctor
python examples/starters/agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
```

Then move to the file that matches your real stack.
