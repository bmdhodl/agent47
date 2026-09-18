# Enforcement boundary

Checked 2026-09-18 against AgentGuard `1.3.2` source. This is the tested
promise. It is not an invoice cap, a host-wide kill switch, or a savings
guarantee.

Parent plan: [GitHub #729](https://github.com/bmdhodl/agent47/issues/729).
This document closes [AG-01 / #730](https://github.com/bmdhodl/agent47/issues/730).

## What a first-time reader should remember

On **OpenAI Chat Completions** and **Anthropic Messages** patches, an exhausted
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
| OpenAI Chat Completions patch (sync, async, stream) | recorded-budget preflight | `sdk/tests/test_budget_preflight.py::test_exhausted_budget_never_dispatches` | Chat Completions only. In-flight responses can exceed remaining tokens or cost. A stream without usage counts as one call and zero tokens. Concurrent requests do not reserve capacity. |
| Anthropic Messages patch (sync, async, stream, `messages.stream`) | recorded-budget preflight | `sdk/tests/test_budget_preflight.py::test_exhausted_budget_never_dispatches` | Same in-flight, missing-usage, and concurrency bounds as the OpenAI patch. |
| Exhausted budget vs next dispatch (repro) | recorded-budget preflight | `examples/enforcement_boundary/exhausted_budget_blocks_dispatch.py` | Mock provider; real patch and `BudgetGuard`. No network. |
| Concurrent `check()` overshoot (repro) | unsupported | `examples/enforcement_boundary/two_worker_overshoot.py` | Two workers can both pass `check()` and both dispatch. This characterizes current overshoot; it is not a fix. Reservation is later work (AG-03/AG-04). |
| LangChain LLM callbacks | advisory | `sdk/tests/test_langchain_integration.py::test_llm_start_does_not_preflight_exhausted_budget` | `consume` runs on `on_llm_end` after the LLM returns. An exhausted token budget does not block `on_llm_start`. |
| LangChain tool callbacks | recorded-budget preflight | `sdk/tests/test_langchain_integration.py::test_tool_start_blocks_exhausted_call_budget` | `consume(calls=1)` runs at `on_tool_start`. An exhausted call budget raises before the tool span. The guard lock serializes that call increment, so two threads cannot both take the last call slot. This is not token or dollar preflight for the LLM. |
| LangGraph `guarded_node` / `guard_node` | recorded-budget preflight | `sdk/tests/test_langgraph_integration.py::test_budget_guard_fires` | `consume(calls=1)` runs at node entry. A `max_cost_usd`-only guard does not fire here. Inner provider clients are not patched unless you patch them separately. |
| CrewAI `AgentGuardCrewHandler` | advisory | `sdk/tests/test_crewai_integration.py::test_budget_guard_fires` | `step_callback` runs after the step. The step that exhausts the call budget already ran. |
| `LoopGuard` / `FuzzyLoopGuard` / `RetryGuard` / `TimeoutGuard` / `RateLimitGuard` | recorded-event preflight | `sdk/tests/test_guards.py` | Runtime event checks at `check()`. Not a token/call/cost budget. `TimeoutGuard` does not interrupt a blocked call or a provider-side job. `RateLimitGuard` raises `BudgetExceeded`. |
| `X402SpendGuard.charge()` | reservation-backed | `sdk/tests/test_x402.py::test_concurrent_charges_do_not_overshoot` | Reserves the payment amount before `pay()`. Failed `pay` rolls back. This is not LLM spend. |
| CLI `doctor` | advisory | `sdk/tests/test_doctor.py::test_run_doctor_writes_local_trace_and_snippet` | Verifies install and local traces. Does not wrap host tools. |
| CLI `demo` | advisory | `sdk/tests/test_enforcement_boundary.py::test_cli_demo_budget_path_is_advisory` | Budget demo emits `llm.result` then `consume()`. Loop/retry demos fire Tracer event guards. Not host interception. |
| CLI `skillpack` / `skills/agentguard` | advisory | `sdk/tests/test_skillpack.py::test_skillpack_notes_are_onboarding_not_host_enforcement` | Generated instructions. Not Cursor, Claude Code, Copilot, or Codex enforcement. |
| npm `@agentguard47/mcp-server` | advisory | `mcp-server/src/__tests__/tools.test.ts` | Read-only hosted traces, alerts, usage, costs, and event-quota health. `check_budget` is hosted event quota, not `BudgetGuard` and not a provider invoice. Mutating budget tools are denied. |
| Python `agentguard-mcp` `record_call` | reservation-backed | `agentguard-mcp/tests/test_storage.py::test_concurrent_record_call_never_exceeds_budget` | SQLite `BEGIN IMMEDIATE` for clients that call this server. Does not intercept other MCP servers. Unpublished checkout package. |
| OpenAI Responses API | unsupported | `sdk/tests/test_enforcement_boundary.py::test_openai_responses_is_unsupported` | Not patched. Use Chat Completions or wrap the call yourself with `check()` / `consume()`. |
| Host tools in Cursor, Claude Code, Copilot, Codex | unsupported | `sdk/tests/test_enforcement_boundary.py::test_skillpack_is_not_host_enforcement` | Package install is not a hook. Prefer native host caps when they already cover the workflow. |
| Provider subscription quota / invoice cap | unsupported | `sdk/tests/test_enforcement_boundary.py::test_product_docs_reject_invoice_guarantees` | Native billing limits stay with the provider. AgentGuard estimates are not invoices. |
| `HttpSink` remote kill | unsupported | `sdk/tests/test_enforcement_boundary.py::test_httpsink_does_not_claim_remote_kill` | Local guards are authoritative. `HttpSink` mirrors events; it does not execute dashboard kill signals. |

## Remaining exposure

- **Direct SDK bypass.** Any client you do not patch or wrap can spend.
- **In-flight spend.** A request that passed `check()` can still return more
  tokens or dollars than remain.
- **Missing usage.** A stream or response without usage still counts as a
  dispatched call with zero tokens and zero cost on the provider patches.
- **Subscription quota.** AgentGuard does not read or enforce OpenAI,
  Anthropic, or cloud-account billing quotas.
- **Concurrent recorded-budget paths.** Two threads can both pass `check()`
  before either `consume()`. Reproduce with
  `examples/enforcement_boundary/two_worker_overshoot.py`.
- **Framework adapters.** LangChain LLM and CrewAI steps record after the
  model or step ran. LangGraph charges a call at node entry, not per inner
  LLM, and does not increment token or dollar totals.

Native provider or host caps are the right default when they already cover
the workflow. Use AgentGuard when you need an in-process stop at a specific
Python dispatch boundary plus a local JSONL record of why work stopped.

## Competitive check (documentation only)

Read 2026-09-18. These are vendor docs, not a benchmark:

- [Claude managed-session budgets](https://platform.claude.com/docs/en/managed-agents/sessions)
  are session-level provider controls. Prefer them when one Claude session cap
  is enough.
- [LiteLLM user budgets](https://docs.litellm.ai/docs/proxy/users) document
  reservations on a proxy. AgentGuard is not a proxy. Recorded-budget
  preflight here is in-process and does not reserve.

## History

Older dashboard-era copy in `ops/00-NORTHSTAR.md`, `memory/distribution.md`,
and `docs/cost-guardrails.md` promised hard dollar stops that the public SDK
does not implement. This file is the replacement. The private dashboard repo
still owns retained history, alerts, and remote controls. This public repo
stays local-first: MIT, zero-dependency runtime checks, local proof.

The 2026 weekly plan in [#729](https://github.com/bmdhodl/agent47/issues/729)
is the planning authority. `ops/03-ROADMAP_NOW_NEXT_LATER.md` is the SDK-now
view and must not contradict that plan.
