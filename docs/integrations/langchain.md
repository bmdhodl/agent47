# LangChain Integration

AgentGuard integrates with LangChain via a callback handler that traces chains, LLM calls, and tool invocations — with optional loop and budget guards.

## Install

```bash
pip install agentguard47[langchain]
```

## Quick Start

```python
from langchain_openai import ChatOpenAI
from agentguard import Tracer, JsonlFileSink, LoopGuard, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="my-agent",
)

handler = AgentGuardCallbackHandler(
    tracer=tracer,
    loop_guard=LoopGuard(max_repeats=5),
    budget_guard=BudgetGuard(max_tokens=100_000, max_cost_usd=1.00),
)

llm = ChatOpenAI(model="gpt-4o", callbacks=[handler])
result = llm.invoke("What is AgentGuard?")
```

## What Gets Traced

| LangChain Event | AgentGuard Span/Event |
|---|---|
| Chain start/end | `chain.<name>` span |
| LLM start/end | `llm.call` span + `llm.end` event |
| Tool start/end | `tool.<name>` span + `tool.result` event |

## Guards

**LoopGuard** fires `LoopDetected` if the same tool is called with the same args repeatedly.

**BudgetGuard** tracks token usage from LLM responses and fires `BudgetExceeded` when limits are hit. Cost estimation is automatic for supported models.

## With LangChain Agents

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([...])
agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, callbacks=[handler])
result = executor.invoke({"input": "research task"})
```

## Viewing Traces

```bash
agentguard report traces.jsonl
```
