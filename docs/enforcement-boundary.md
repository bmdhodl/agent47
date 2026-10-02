# Enforcement boundary

Checked 2026-09-26 against AgentGuard `1.4.1` source. This is the tested
promise. It is not an invoice cap, a host-wide kill switch, or a savings
guarantee.

Parent plan: [GitHub #729](https://github.com/bmdhodl/agent47/issues/729).
This document closes [AG-01 / #730](https://github.com/bmdhodl/agent47/issues/730).

## What a first-time reader should remember

On **OpenAI Chat Completions**, **OpenAI Responses**, and **Anthropic Messages**
patches, an exhausted
**recorded** budget refuses the **next** dispatch. That check reads usage
already stored on `BudgetGuard`. It does **not** reserve concurrent in-flight
calls, predict the next response's tokens or dollars, intercept a direct SDK
client you never patched, or cap a provider subscription quota.

Installing `agentguard47` does nothing to Cursor, Claude Code, Copilot, or
Codex until your code (or a generated starter) calls the SDK.

## Classes

| Class | Meaning |
| --- | --- |
| `advisory` | Reports, instructs, or records after the fact. Does not refuse the action that just ran. |
| `recorded-budget preflight` | Refuses the next instrumented action when recorded token/call/cost usage is already at or above a cap. `check()` does not reserve concurrent in-flight requests. `consume()` at entry serializes call accounting on the guard lock; that is still not token or dollar reservation. |
| `recorded-event preflight` | Refuses the next instrumented action when recorded loop, retry, timeout, or rate state is already at a cap. This is not a token, call, or dollar budget. |
| `reservation-backed` | Holds capacity before in-flight work so concurrent callers cannot both spend the last unit. |
| `unsupported` | Not intercepted. Do not advertise a stop here. |

## Surface map

Every advertised supported path lists a test and a limitation. Unsupported
paths are marked `unsupported`.

| Surface | Class | Test | Limitations |
| --- | --- | --- | --- |
| `BudgetGuard.check()` | recorded-budget preflight | `sdk/tests/test_budget_preflight.py::test_check_does_not_charge_or_warn_and_reset_reopens` | Refuses a new request at equality. Does not charge. Does not reserve concurrent in-flight requests. |
| `BudgetGuard.consume()` | advisory | `sdk/tests/test_guards.py` | Records usage for a call that already ran, then raises if the new total exceeds the cap. The billed provider call is not undone. |
| OpenAI Chat Completions patch (sync, async, stream) | recorded-budget preflight | `sdk/tests/test_budget_preflight.py::test_exhausted_budget_never_dispatches` | Chat Completions only. In-flight responses can exceed remaining tokens or cost. An in-memory stream without usage counts as one call and zero tokens. In-memory and async non-stream calls do not reserve. Store-backed rows below do. |
| OpenAI Chat Completions sync, non-stream, with `StateStore` | reservation-backed | `sdk/tests/test_reservation_path.py::test_barrier_threads_dispatch_once` | Holds one call before send for workers that share that store key. Token and dollar holds need `max_tokens` on the request; the dollar figure is a high-water estimate, not an invoice. Unknown provider outcome keeps the hold. In-memory guards and async non-stream calls stay on recorded-budget preflight. |
| OpenAI and Anthropic streams with `StateStore` | reservation-backed | `sdk/tests/test_reservation_stream.py::test_two_store_streams_dispatch_once` | Holds one call before the stream is sent. Missing usage, an early stop, or a partial usage chunk under a token or dollar cap stays unresolved. An exception while entering the stream context stays unresolved. A calls-only cap settles one call and zero tokens. Unknown model cost is an overestimate, not free. Not an invoice cap. |
| Anthropic Messages patch (sync, async, stream, `messages.stream`) | recorded-budget preflight | `sdk/tests/test_budget_preflight.py::test_exhausted_budget_never_dispatches` | In-memory and non-stream calls use recorded-budget preflight. Store-backed streams are the reservation row above. |
| Exhausted budget vs next dispatch (repro) | recorded-budget preflight | `examples/enforcement_boundary/exhausted_budget_blocks_dispatch.py` | Mock provider; real patch and `BudgetGuard`. No network. |
| Concurrent `check()` overshoot (repro) | unsupported | `examples/enforcement_boundary/two_worker_overshoot.py` | Two workers can both pass `check()` and both dispatch. This characterizes in-memory overshoot. The store-backed sync OpenAI path is the separate reservation row. |
| Store-backed one-call race (repro) | reservation-backed | `examples/enforcement_boundary/reserved_one_dispatch.py` | Two spawned processes share one `JsonFileStateStore` and `max_calls=1`. Exactly one mock dispatch runs. Not an invoice cap. Windows was not executed for this repro. |
| Store-backed streamed one-call race (repro) | reservation-backed | `examples/enforcement_boundary/reserved_stream_dispatch.py` | Same race with `stream=True`. Exactly one mock stream runs. Windows was not executed for this repro. |
| LangChain LLM callbacks | advisory | `sdk/tests/test_langchain_integration.py::test_llm_start_does_not_preflight_exhausted_budget` | `consume` runs on `on_llm_end` after the LLM returns. An exhausted token budget does not block `on_llm_start`. Cost uses the same resolver and price table as the patched clients; an unknown model is overestimated, not free. |
| LangChain tool callbacks | recorded-budget preflight | `sdk/tests/test_langchain_integration.py::test_tool_start_blocks_exhausted_call_budget` | `consume(calls=1)` runs at `on_tool_start`. An exhausted call budget raises before the tool span. The guard lock serializes that call increment, so two threads cannot both take the last call slot. This is not token or dollar preflight for the LLM. |
| LangGraph `guarded_node` / `guard_node` | recorded-budget preflight | `sdk/tests/test_langgraph_integration.py::test_budget_guard_fires` | `consume(calls=1)` runs at node entry. A `max_cost_usd`-only guard does not fire here. Inner provider clients are not patched unless you patch them separately. |
| CrewAI `AgentGuardCrewHandler` | advisory | `sdk/tests/test_crewai_integration.py::test_budget_guard_fires` | `step_callback` runs after the step. The step that exhausts the call budget already ran. |
| `LoopGuard` / `FuzzyLoopGuard` / `RetryGuard` / `TimeoutGuard` / `RateLimitGuard` | recorded-event preflight | `sdk/tests/test_guards.py` | Runtime event checks at `check()`. Not a token/call/cost budget. `TimeoutGuard` does not interrupt a blocked call or a provider-side job. `RateLimitGuard` raises `BudgetExceeded`. |
| `X402SpendGuard.charge()` | reservation-backed | `sdk/tests/test_x402.py::test_concurrent_charges_do_not_overshoot` | Reserves the payment amount before `pay()`. Failed `pay` rolls back. This is not LLM spend. |
| CLI `doctor` | advisory | `sdk/tests/test_doctor.py::test_run_doctor_writes_local_trace_and_snippet` | Verifies install and local traces. Does not wrap host tools. |
| CLI `demo` | advisory | `sdk/tests/test_enforcement_boundary.py::test_cli_demo_budget_path_is_advisory` | Budget demo emits `llm.result` then `consume()`. Loop/retry demos fire Tracer event guards. Not host interception. |
| CLI `skillpack` / `skills/agentguard` | advisory | `sdk/tests/test_skillpack.py::test_skillpack_notes_are_onboarding_not_host_enforcement` | Generated instructions. Not Cursor, Claude Code, Copilot, or Codex enforcement. |
| CLI `hook claude-code` loop and retry checks | recorded-event preflight | `sdk/tests/test_hooks.py::test_run_refuses_with_exit_2_and_logs_a_receipt` | Claude Code tool calls that fire `PreToolUse`, in a project where the hook is installed. Refuses the `loop_max`-th identical call in a row and a call that already failed `retry_max` times. Checks tool calls, not model tokens, subagent-internal work, or subscription quota. Unreadable hook input is a non-blocking error; the call proceeds. A user can remove the hook. Run against Claude Code 2.1.283 on Linux; Windows and macOS were not executed. |
| CLI `hook claude-code --max-calls` | recorded-budget preflight | `sdk/tests/test_hooks.py::test_parallel_hook_processes_do_not_lose_counts` | Per-session tool-call count in a locked `JsonFileStateStore`; parallel hook processes do not lose counts. A call count, not a token or dollar budget. |
| CLI `run` | recorded-budget preflight | `sdk/tests/test_real_dispatch.py::test_agentguard_run_stops_an_unmodified_openai_script` | Calls `init()`, which patches OpenAI Chat Completions, OpenAI Responses, and Anthropic Messages, then runs the script in the same interpreter. Same bounds as those patch rows: the call that crosses a dollar cap is already sent. Subprocesses the script starts are not patched. |
| npm `@agentguard47/mcp-server` | advisory | `mcp-server/src/__tests__/tools.test.ts` | Read-only hosted traces, alerts, usage, costs, and event-quota health. `check_budget` is hosted event quota, not `BudgetGuard` and not a provider invoice. Mutating budget tools are denied. |
| Python `agentguard-mcp` `record_call` | reservation-backed | `agentguard-mcp/tests/test_storage.py::test_concurrent_record_call_never_exceeds_budget` | SQLite `BEGIN IMMEDIATE` for clients that call this server. Does not intercept other MCP servers. Unpublished checkout package. |
| OpenAI Responses API patch (`responses.create`, `responses.parse`, `responses.stream()`; sync, async, stream) | recorded-budget preflight | `sdk/tests/test_real_dispatch.py::test_responses_create_counts_once_and_blocks_before_dispatch` | Needs openai 1.66 or later. Bills `response.usage`, or the usage on the `response.completed` stream event. `with_raw_response` and `with_streaming_response` count when the response is parsed. Store-backed sync non-stream calls and store-backed streams reserve like Chat Completions; token and dollar holds need `max_output_tokens`. In-flight responses can exceed remaining tokens or cost. |
| OpenAI Agents SDK (`Runner.run`, `Runner.run_streamed`) on `OpenAIResponsesModel` | recorded-budget preflight | `sdk/tests/test_real_dispatch.py::test_agents_sdk_run_stops_a_tool_loop_before_the_next_model_call` | Refuses the next model call and `BudgetExceeded` leaves `Runner.run`. Tool calls and handoffs are not guard points; each model call they lead to is. Patch before the SDK builds its client (`agentguard.init()` at startup). Native `max_turns` still applies. `OpenAIChatCompletionsModel` follows the Chat Completions row. |
| OpenAI Responses paths outside the patch | unsupported | `sdk/tests/test_enforcement_boundary.py::test_openai_responses_unpatched_paths_are_named` | Hosted tool calls (web search, file search, code interpreter, computer use) run inside one response: AgentGuard cannot stop one mid-response, and per-call tool fees are not in `usage`. `background=True` returns before usage exists: it counts as one call and zero tokens, and the spend that follows is not recorded. Resuming a stream by `response_id`, `responses.retrieve`, `cancel`, `compact`, and the Realtime and WebSocket transports are not patched. |
| Host tools in Cursor, Claude Code, Copilot, Codex | unsupported | `sdk/tests/test_enforcement_boundary.py::test_skillpack_is_not_host_enforcement` | Package install is not a hook. Prefer native host caps when they already cover the workflow. |
| Provider subscription quota / invoice cap | unsupported | `sdk/tests/test_enforcement_boundary.py::test_product_docs_reject_invoice_guarantees` | Native billing limits stay with the provider. AgentGuard estimates are not invoices. |
| `HttpSink` remote kill | unsupported | `sdk/tests/test_enforcement_boundary.py::test_httpsink_does_not_claim_remote_kill` | Local guards are authoritative. `HttpSink` mirrors events; it does not execute dashboard kill signals. |

## Remaining exposure

- **Direct SDK bypass.** Any client you do not patch or wrap can spend.
- **In-flight spend.** A request that passed `check()` can still return more
  tokens or dollars than remain.
- **Missing usage.** An in-memory stream or response without usage still
  counts as a dispatched call with zero tokens and zero cost. A store-backed
  stream with a token or dollar cap keeps that hold unresolved instead,
  including when the stream stops early after a partial usage chunk.
- **Subscription quota.** AgentGuard does not read or enforce OpenAI,
  Anthropic, or cloud-account billing quotas.
- **Concurrent recorded-budget paths.** Two threads can both pass `check()`
  before either `consume()`. Reproduce with
  `examples/enforcement_boundary/two_worker_overshoot.py`. Store-backed
  sync non-streaming OpenAI calls, and store-backed OpenAI or Anthropic
  streams, reserve before send. Contract:
  [reservation-contract.md](guides/reservation-contract.md).
  `examples/enforcement_boundary/reserved_one_dispatch.py` and
  `reserved_stream_dispatch.py` are those races. In-memory, async non-stream,
  and Anthropic non-stream calls still use recorded-budget preflight.
- **Framework adapters.** LangChain LLM and CrewAI steps record after the
  model or step ran. LangGraph charges a call at node entry, not per inner
  LLM, and does not increment token or dollar totals.

Native provider or host caps are the right default when they already cover
the workflow. Use AgentGuard when you need an in-process stop at a specific
Python dispatch boundary plus a local JSONL record of why work stopped.

## Competitive check (documentation only)

Read 2026-09-20. These are vendor docs, not a benchmark:

- [Claude managed-session budgets](https://platform.claude.com/docs/en/managed-agents/sessions)
  are session-level provider controls. Prefer them when one Claude session cap
  is enough.
- [LiteLLM user budgets](https://docs.litellm.ai/docs/proxy/users) document
  reservations on a proxy. AgentGuard is not a proxy. The local contract
  is [reservation-contract.md](guides/reservation-contract.md). It reserves
  store-backed OpenAI calls and store-backed streams that share a
  `StateStore`. It does not reserve the other recorded-budget paths.

## History

Older dashboard-era copy in `ops/00-NORTHSTAR.md`, `memory/distribution.md`,
and `docs/cost-guardrails.md` promised hard dollar stops that the public SDK
does not implement. This file is the replacement. The private dashboard repo
still owns retained history, alerts, and remote controls. This public repo
stays local-first: MIT, zero-dependency runtime checks, local proof.

The 2026 weekly plan in [#729](https://github.com/bmdhodl/agent47/issues/729)
is the planning authority. `ops/03-ROADMAP_NOW_NEXT_LATER.md` is the SDK-now
view and must not contradict that plan.
