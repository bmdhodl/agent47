# Budget-Aware Escalation

`BudgetAwareEscalation` gives AgentGuard users a portable version of the "cheap executor, strong advisor" pattern without baking provider-specific routing into the SDK.

The shape is simple:

- keep a cheaper default model for routine work
- escalate only when the current turn looks hard
- wire the returned model choice into your own client call

This stays consistent with AgentGuard's core boundary: the SDK decides when a run is risky or expensive; your app still owns the actual model invocation.

## Why this exists

Anthropic's official advisor-tool docs describe the same high-level pattern: pair a faster, lower-cost executor with a stronger advisor for hard long-horizon tasks, especially coding and agentic workflows. The queue item that triggered this work called out the durable pattern, not a vendor-specific API, and that is the right way to bring it into AgentGuard.

Source:
- [Anthropic advisor tool docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/advisor-tool)

## What the guard does

`BudgetAwareEscalation` supports four trigger types in v1:

1. token count over a threshold
2. normalized confidence below a threshold
3. tool-call depth over a threshold
4. a custom rule that inspects the turn context

When a configured signal trips, the guard can:

- raise `EscalationRequired` so you switch to the stronger model explicitly, or
- arm the next call through the normal `auto_check(...)` path and let `select_model()` choose the stronger model on the next turn

## Minimal example

```python
from agentguard import BudgetAwareEscalation, EscalationRequired, EscalationSignal

guard = BudgetAwareEscalation(
    primary_model="ollama/llama3.1:8b",
    escalate_model="claude-opus-4-6",
    escalate_on=(
        EscalationSignal.TOKEN_COUNT(threshold=2000),
        EscalationSignal.CONFIDENCE_BELOW(threshold=0.45),
    ),
)

model = guard.select_model()

# ... run the cheaper model first ...
guard.auto_check(
    "llm.result",
    {
        "model": model,
        "usage": {"total_tokens": 2430},
        "confidence": 0.39,
    },
)

try:
    guard.check()
    next_model = guard.primary_model
except EscalationRequired as exc:
    next_model = exc.target_model
    print(exc.reason)
```

## Worked example: local Llama to Claude

This repo includes a local-only example that simulates a local Llama turn, arms the escalation guard from the result, and then routes the next call to Claude:

```bash
PYTHONPATH=sdk python examples/budget_aware_escalation.py
```

Expected output:

```text
Turn 1 model: ollama/llama3.1:8b
Turn 2 model: claude-opus-4-6
Escalation reason: token_count 2430 exceeded 2000
Wrote budget_aware_escalation_traces.jsonl
```

The example also writes a local trace file so the escalation path is inspectable.

## Signal semantics

### Token count

Use when a turn is getting too expensive or too context-heavy for the cheaper model:

```python
EscalationSignal.TOKEN_COUNT(threshold=2000)
```

The guard looks for:

- `token_count`
- `total_tokens`
- `usage.total_tokens`

### Confidence below

Use when your runtime already exposes a normalized confidence score:

```python
EscalationSignal.CONFIDENCE_BELOW(threshold=0.45)
```

The SDK does not invent confidence for you. If your provider exposes logprobs or another score, normalize it in your app and pass `confidence=...` or put `confidence` in the traced event payload.

### Tool-call depth

Use when a turn is spiraling into too many tool hops:

```python
EscalationSignal.TOOL_CALL_DEPTH(threshold=3)
```

The guard looks for:

- `tool_call_depth`
- `depth`
- `tool_calls` list length

### Custom rule

Use when your own heuristics are stronger than any single built-in signal:

```python
EscalationSignal.CUSTOM(
    lambda ctx: (ctx.get("token_count") or 0) > 1500 and (ctx.get("confidence") or 1.0) < 0.5,
    name="hard_turn",
)
```

The custom rule receives a context dict with:

- `event_name`
- `event_data`
- `primary_model`
- `escalate_model`
- `current_model`
- `token_count`
- `confidence`
- `tool_call_depth`

## Design boundary

This is intentionally not "transparent provider switching" inside AgentGuard's patchers.

Why:

- AgentGuard guards are runtime enforcement primitives, not provider adapters
- the SDK must stay zero-dependency
- routing policy is portable only if your app remains in control of the actual client call

So the contract is:

- AgentGuard tells you when escalation is needed
- your application decides how to invoke the stronger model

That keeps the feature compatible with local Ollama, raw HTTP clients, OpenAI-compatible endpoints, Anthropic, and future provider adapters without locking the SDK to one stack.
