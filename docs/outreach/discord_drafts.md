# Discord Community Drafts

Strategy: Post #help answers FIRST to build trust, then #showcase later.

---

## LangChain Discord

### #help: "My agent keeps calling the same tool over and over"

If your LangChain agent is calling the same tool repeatedly, you likely have a loop in your ReAct prompt or the tool is returning unhelpful results.

Quick debug: add loop detection before it burns your budget:

```python
from agentguard import LoopGuard, LoopDetected

guard = LoopGuard(max_repeats=3)

# In your tool wrapper:
try:
    guard.check(tool_name="search", tool_args={"query": query})
except LoopDetected as e:
    return f"Loop detected: {e}"
```

This catches identical tool calls on the 3rd repeat. You can also use the LangChain callback handler to get full trace visibility:

```python
from agentguard.integrations.langchain import AgentGuardCallbackHandler
from agentguard import Tracer

tracer = Tracer()
handler = AgentGuardCallbackHandler(tracer=tracer)
agent.run("your query", callbacks=[handler])
```

Then run `agentguard report traces.jsonl` to see where the loop happens.

---

### #showcase: AgentGuard — Loop Detection for LangChain Agents

Built an observability SDK that catches tool loops before they burn your budget. Zero dependencies, MIT licensed.

LangChain agents can loop silently when tools return unhelpful results. AgentGuard catches this with built-in loop detection and gives you full reasoning traces.

```python
from agentguard.integrations.langchain import AgentGuardCallbackHandler
from agentguard import Tracer, LoopGuard

tracer = Tracer()
handler = AgentGuardCallbackHandler(
    tracer=tracer,
    loop_guard=LoopGuard(max_repeats=3),
)

# Use with any LangChain agent
agent.run("question", callbacks=[handler])
```

See every step your agent took, not just the final output. Catch loops, track budgets, replay runs for tests.

Repo: https://github.com/bmdhodl/agent47
Install: `pip install agentguard47[langchain]`

---

## CrewAI Discord

### #help: "How do I track token usage across my agent's run?"

CrewAI makes it easy to coordinate agents, but tracking cumulative token usage across all agents and retries can be tricky.

You can wrap your LLM calls with a budget guard:

```python
from agentguard import BudgetGuard, BudgetExceeded

budget = BudgetGuard(max_tokens=50000, max_calls=100)

# After each LLM call:
try:
    budget.consume(tokens=response.usage.total_tokens, calls=1)
except BudgetExceeded as e:
    print(f"Budget hit: {e}")
    # stop the crew
```

This gives you hard limits so runaway agents don't blow your budget. You can also use the tracer to see token usage per agent:

```python
from agentguard import Tracer

tracer = Tracer()
with tracer.trace("crew.run") as span:
    span.event("llm.response", data={"tokens": tokens, "agent": "researcher"})
```

Then `agentguard report traces.jsonl` shows you which agent used the most tokens.

---

### #showcase: AgentGuard — Retry Visibility for CrewAI

Shipped a lightweight observability SDK for multi-agent systems. Solves the "why did this crew cost $30" problem.

CrewAI agents retry tasks automatically, but you don't always see how many retries happened or which agent burned through your budget. AgentGuard gives you full visibility with zero config.

```python
from agentguard import Tracer, BudgetGuard

tracer = Tracer()
budget = BudgetGuard(max_tokens=50000)

with tracer.trace("crew.task") as span:
    # your CrewAI task here
    budget.consume(tokens=response.usage.total_tokens)
```

Track token usage per agent. Catch budget overruns. See retry counts. Replay runs deterministically for regression tests.

Model-agnostic. Zero deps. MIT licensed.

Repo: https://github.com/bmdhodl/agent47
Install: `pip install agentguard47`

---

## Hugging Face Discord

### #help: "My agent costs are out of control"

If you're running agents with Hugging Face models (or any model) and costs are climbing, the usual culprit is silent loops or untracked retry logic.

Add hard budget limits before your next run:

```python
from agentguard import BudgetGuard, TimeoutGuard

budget = BudgetGuard(max_tokens=100000, max_calls=200)
timeout = TimeoutGuard(max_seconds=60)

timeout.start()
for step in agent_loop():
    budget.consume(tokens=output.tokens, calls=1)
    timeout.check()  # raises TimeoutExceeded if over limit
```

This kills the run if it exceeds token or time limits. No surprises on your bill.

You can also trace the run to see where tokens are going:

```python
from agentguard import Tracer

with Tracer().trace("agent.run") as span:
    span.event("model.call", data={"model": "meta-llama/Llama-3", "tokens": 150})
```

Run `agentguard report traces.jsonl` to see the breakdown.

---

### #showcase: AgentGuard — Model-Agnostic Tracing for Any Agent

Built an observability SDK that works with ANY model (OpenAI, Hugging Face, Anthropic, local models). Zero vendor lock-in.

Most agent tracing tools only work with specific providers. AgentGuard is pure Python and model-agnostic. Use it with Hugging Face Transformers, Inference API, TGI, or any other backend.

```python
from agentguard import Tracer, BudgetGuard

tracer = Tracer()
budget = BudgetGuard(max_tokens=50000)

with tracer.trace("agent.run") as span:
    # your Hugging Face model call
    span.event("model.response", data={"tokens": tokens})
    budget.consume(tokens=tokens)
```

Catch loops. Guard budgets. Replay runs. See reasoning traces in your browser.

MIT licensed. Zero dependencies.

Repo: https://github.com/bmdhodl/agent47
Install: `pip install agentguard47`

---

## AutoGen Discord

### #help: "How do I debug what my agent is thinking?"

AutoGen's multi-agent conversations can get complex fast. If you need to see what each agent is thinking (not just what they output), add reasoning traces:

```python
from agentguard import Tracer

tracer = Tracer()

# Wrap your agent loop:
with tracer.trace("autogen.conversation") as span:
    for message in conversation:
        span.event("agent.message", data={
            "agent": message.sender,
            "content": message.content,
            "recipient": message.recipient
        })
```

Then run `agentguard report traces.jsonl` to see the full conversation timeline. You can also open it in the browser with `agentguard view traces.jsonl` to see the event tree.

For multi-agent coordination issues, this makes it obvious when agents are talking past each other or repeating themselves.

---

### #showcase: AgentGuard — Multi-Agent Coordination Debugging

Built observability for multi-agent systems. Solves the "which agent broke the conversation" problem.

AutoGen makes it easy to orchestrate agents, but debugging coordination failures is hard. AgentGuard gives you full visibility into agent conversations with nested traces.

```python
from agentguard import Tracer

tracer = Tracer()
with tracer.trace("autogen.run") as span:
    with span.span("agent.alice") as s:
        s.event("reasoning", data={"thought": "..."})
    with span.span("agent.bob") as s:
        s.event("reasoning", data={"thought": "..."})
```

See which agent failed. Track conversation depth. Catch loops between agents. Replay conversations deterministically.

Model-agnostic. Zero deps. MIT licensed.

Repo: https://github.com/bmdhodl/agent47
Install: `pip install agentguard47`

---

## LlamaIndex Discord

### #help: "How do I debug what my agent is thinking?"

LlamaIndex agents (especially ReAct agents) can make a lot of tool calls, and it's not always clear why they chose one tool over another. The logs show the final answer but not the reasoning.

Add reasoning traces to see the full decision tree:

```python
from agentguard import Tracer

tracer = Tracer()

with tracer.trace("agent.query") as span:
    # Before each tool call:
    span.event("reasoning.step", data={
        "step": step_num,
        "thought": agent_thought,
        "action": tool_name
    })

    # Wrap the tool call:
    with span.span("tool.call", data={"tool": tool_name}):
        result = tool.run(args)

    span.event("tool.result", data={"output": result})
```

Then run `agentguard view traces.jsonl` to open the trace viewer in your browser. You'll see the full reasoning timeline with nested tool calls.

This is especially useful for RAG agents where you need to debug query retrieval and tool selection together.

---

### #showcase: AgentGuard — RAG Agent Tracing for LlamaIndex

Shipped an observability SDK for LlamaIndex agents. Solves the "why didn't my agent use the right tool" problem.

RAG agents have two failure modes: bad retrieval and bad tool selection. LlamaIndex handles the RAG, but debugging multi-step reasoning is still hard. AgentGuard gives you full visibility.

```python
from agentguard import Tracer, LoopGuard

tracer = Tracer()
guard = LoopGuard(max_repeats=3)

with tracer.trace("llamaindex.agent") as span:
    span.event("query", data={"query": user_query})
    guard.check("retrieval", {"query": user_query})
    # your LlamaIndex agent code
```

See every reasoning step. Catch tool loops. Track token usage. Replay runs for tests.

Model-agnostic. Zero deps. MIT licensed.

Repo: https://github.com/bmdhodl/agent47
Install: `pip install agentguard47`

---

## Posting Strategy

1. **Week 1**: Post #help answers (all 5 servers)
2. **Week 2**: Post #showcase messages (all 5 servers)
3. **Timing**: Post #help during peak hours (9am-12pm PT weekdays)
4. **Timing**: Post #showcase during lower traffic (2-5pm PT weekdays) to avoid spam detection
5. **Follow-up**: Reply to questions on #help posts to build credibility before #showcase
6. **Avoid**: Don't post all 5 #showcase messages on the same day (spread over 3-5 days)
