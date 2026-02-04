# AgentGuard SDK (Python)

This is a minimal, framework-agnostic SDK for tracing, guarding, and replaying multi-agent runs.

## Install (editable)
```bash
python3 -m pip install -e .
```

## Basic tracing
```python
from agentguard.tracing import Tracer

tracer = Tracer()

with tracer.trace("agent.run", data={"user_id": "u123"}) as span:
    span.event("reasoning.step", data={"step": 1, "thought": "search docs"})
    with span.span("tool.call", data={"tool": "search", "query": "agent loops"}):
        # call your tool here
        pass
```

## Loop guard
```python
from agentguard.guards import LoopGuard

guard = LoopGuard(max_repeats=3)

# call when you invoke a tool
guard.check(tool_name="search", tool_args={"query": "agent loops"})
```

## Replay
```python
from agentguard.recording import Recorder, Replayer

recorder = Recorder("runs.jsonl")
recorder.record_call("llm", {"prompt": "hi"}, {"text": "hello"})

replayer = Replayer("runs.jsonl")
resp = replayer.replay_call("llm", {"prompt": "hi"})
```

## Integrations
- LangChain stub in `agentguard.integrations.langchain`
