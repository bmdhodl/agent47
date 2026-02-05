# LangChain Integration

Wire AgentGuard tracing and guards into any LangChain chain or agent.

## Install

```bash
pip install agentguard47[langchain]
```

## Basic usage

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from agentguard.tracing import JsonlFileSink, Tracer
from agentguard.guards import LoopGuard, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

tracer = Tracer(sink=JsonlFileSink("traces.jsonl"), service="demo")
handler = AgentGuardCallbackHandler(
    tracer=tracer,
    loop_guard=LoopGuard(max_repeats=3),
    budget_guard=BudgetGuard(max_tokens=50000),
)

llm = ChatOpenAI(temperature=0.0, callbacks=[handler])
response = llm.invoke([HumanMessage(content="Explain agent loops in one paragraph.")])
print(response)
```

## What gets captured

- `chain.*` spans for each chain/agent invocation
- `llm.call` spans with prompts and token usage
- `tool.*` spans for each tool invocation
- Guard checks on every tool call (loop detection + budget tracking)

## View traces

```bash
agentguard report traces.jsonl
agentguard view traces.jsonl
```

## Notes

- The handler tracks nested spans via a stack, so nested chains and tools are properly correlated.
- Guards raise `LoopDetected` or `BudgetExceeded` when limits are hit, stopping the agent.
- The SDK has zero required dependencies. LangChain is an optional extra.
