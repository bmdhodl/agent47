# LangChain Integration Example

This is a minimal example showing how to wire AgentGuard tracing into LangChain
without adding hard dependencies to the SDK.

## Example
```python
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

from agentguard.integrations.langchain import AgentGuardCallbackHandler
from agentguard.tracing import JsonlFileSink, Tracer

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"), service="demo")
handler = AgentGuardCallbackHandler(tracer=tracer)

llm = ChatOpenAI(temperature=0.0, callbacks=[handler])
response = llm([HumanMessage(content="Explain agent loops in one paragraph.")])
print(response)
```

## Expected output
- `traces.jsonl` with `llm.start`, `llm.end`, and `chain.*` events
- Use the CLI to summarize:
```bash
agentguard summarize traces.jsonl
```

## Notes
- This is a stub. It captures high-level events and can be expanded to include token usage or tool metadata.
- The SDK remains dependency-free; integrations live in this folder.
