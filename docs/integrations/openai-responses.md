# OpenAI Responses and Agents SDK

Status: owner-approved AG-06 architecture, 2026-10-03. This path is new in
**AgentGuard 2.0.0**, which requires Python 3.11+. 1.4.0 does not provide
this support.

The adapter uses the existing `init()`, `patch_openai()` and
`patch_openai_async()` entry points. It adds no core dependency, public export,
or second agent orchestrator. OpenAI and the Agents SDK remain optional.

## Install

Install AgentGuard 2.0.0 in a clean environment. The minimum Responses pair is
OpenAI 1.66.3
and OpenAI Agents 0.0.3; it does not change Chat Completions' 1.40.0 floor.

```bash
python -m pip install "agentguard47==2.0.0" \
  "openai==1.66.3" "openai-agents==0.0.3"
```

The supported version pairs and installed tests are recorded in
[AG-06 acceptance proof](../../proof/approved-responses-735/README.md).

## Activate before dispatch

```python
import agentguard

agentguard.init(budget_usd=0.05, trace_file="agents_traces.jsonl")
# Run the standard OpenAIResponsesModel after activation.
```

[`openai_agents_sdk_budget.py`](../../examples/openai_agents_sdk_budget.py)
composes that path with the Agents SDK's `max_turns`. It makes real provider
calls when run with a provider key. The acceptance tests instead use real SDK
objects with a counting fake transport and disable vendor tracing.

Activate before model dispatch and before constructing stream helpers.
Standard OpenAI clients created earlier are covered. A previously saved bound
callable, custom resource override, or custom model transport can bypass the
patch. A second call after an exhausted recorded budget is refused before it
reaches the supported transport.

## Tested boundary

| Path | Behavior | Proof |
|---|---|---|
| Sync/async `responses.create` and `parse` | Preserve SDK results/errors, record usage once, refuse the next prohibited dispatch | Responses cases in `sdk/tests/test_real_dispatch.py` |
| Stream helpers and raw/streaming response wrappers | Preserve context managers; final reported usage is counted once, including unread wrapper exit | Stream and wrapper cases in the same suite |
| `Runner.run` and `Runner.run_streamed` with `OpenAIResponsesModel` | Stop a repeated tool loop before the next model request; the tested three-call budget sends exactly three requests | `test_agents_sdk_run_stops_a_tool_loop_before_the_next_model_call` |
| Native `max_turns` | Remains effective when it is tighter than the AgentGuard call budget | `test_agents_sdk_native_max_turns_still_applies` |

The budget covers instrumented model calls. Tool invocations and handoffs are
not guard points; subsequent supported model requests are. Hosted tools execute
inside a response and cannot be interrupted by this adapter. Their separate
fees are absent from model token usage. This is not an invoice cap.

`background=True` returns before final usage is available: the current path
records one call and zero tokens. Retrieve, cancel, compact, stream resumption
by response ID, Realtime and WebSocket transports are unsupported. In-flight
calls can overshoot a recorded token or dollar budget. Async non-stream calls
do not reserve; store-backed sync calls and streams have the narrower
[reservation contract](../guides/reservation-contract.md).

The full [enforcement map](../enforcement-boundary.md) owns these bounds.
Installed-wheel evidence does not establish external adoption. Outside
activation and repeat use remain tracked in #737; later adapters retain their
own decisions.
