# Local reservation and reconciliation contract

Design date: **2026-09-20**. Closes the design slice of
[AG-03 / #732](https://github.com/bmdhodl/agent47/issues/732). Parent plan:
[#729](https://github.com/bmdhodl/agent47/issues/729). Implementation is
[AG-04 / #733](https://github.com/bmdhodl/agent47/issues/733), not this document.

This is an architecture contract. It does **not** change `BudgetGuard.check()`
or `consume()`. Those still overshoot when two workers both pass `check()`
before either `consume()`. Reproduce with
`examples/enforcement_boundary/two_worker_overshoot.py`.

No public SDK API is added by this contract. The executable model is the
private module `sdk/agentguard/_reservation_contract.py`. AG-04 wires one
provider path to that model: sync, non-streaming OpenAI Chat Completions
when `BudgetGuard` has a `StateStore`. `ReservationLedger` stays private.
`BudgetGuard.reservation_totals()` reports settled, reserved, and unresolved
amounts. `check()` and `consume()` still do not reserve.

## Native-first alternative (smaller)

Refresh read 2026-09-20. Prefer the native control when it already covers the
workflow. AgentGuard reservation is only for **local workers that share a
`StateStore` key** and still need an in-process stop plus a JSONL record.

| Need | Smaller native path | Why not AgentGuard first |
| --- | --- | --- |
| One Claude managed session dollar cap | [Session budget](https://platform.claude.com/docs/en/managed-agents/sessions): `max_list_cost` enforced **between** model requests. The crossing request can finish past the cap. | Provider list-cost cap, not a Python dispatch reservation. |
| One OpenAI Agents run | [Runner `max_turns`](https://openai.github.io/openai-agents-python/running_agents/) and local function-tool concurrency. | Turn limits are not token/dollar holds. |
| Multi-tenant proxy with concurrent spend | [LiteLLM budget reservation](https://docs.litellm.ai/docs/proxy/users): estimate, reserve, replace with actual; disable reservation to get recorded-spend overshoot; `fail_closed_budget_enforcement` when Redis is degraded. | AgentGuard is not a proxy and has no Redis lease. |
| Cursor / Claude Code / Copilot / Codex host tools | Host hooks and native caps. | Package install is not a host interceptor. |

If LiteLLM (or a provider session cap) already bounds the traffic, document
that path and skip AG-04 for that workflow.

## What this ledger can and cannot guarantee

After AG-04 implements this contract on one patched dispatch path sharing one
store key:

**Can**

- Call count: `settled_calls + held_calls` never exceeds `max_calls` for
  workers that go through `reserve` on that store key.
- A local exception **before send** can `cancel` and free the call slot.
- Timeout, crash, or unknown provider outcome keeps the hold
  (`unresolved`). Unknown provider outcome cannot silently free funds.

**Cannot**

- A provider invoice or subscription quota. `can_claim_invoice_cap()` is
  always false. There is no invoice cap without a valid request-cost bound,
  and even then the bound is our estimate, not the bill.
- Token or dollar stops when the caller omits an upper bound. Missing bound
  refuses the reserve rather than pretending to cap spend.
- Hosts, SDKs, or processes that never call `reserve`.
- Mixed-version processes: an old `check()`/`consume()` worker can still
  overshoot a store that a new worker is reserving.
- UTC day rollover for in-flight holds. Unresolved reservations stay on the
  **reserve-day** bucket. The next UTC day is a new key and starts empty.
- Estimate overrun: if actual tokens/cost exceed the reserved bound, commit
  still records the truth. That leftover is remaining exposure, not a silent
  write-down.

## Ledger shape (existing StateStore)

Reuse `JsonFileStateStore` period buckets (`key` or `key:YYYY-MM-DD`). Do not
add a database, a distributed lease, or a payment rail.

```json
{
  "tokens_used": 0,
  "calls_used": 0,
  "cost_used": 0.0,
  "reservations": {
    "res_1": {
      "status": "reserved",
      "calls": 1,
      "tokens_bound": 128000,
      "cost_bound": 0.05,
      "price_table_version": "2026.07.15",
      "period_bucket": "fleet:2026-09-20",
      "tokens_settled": null,
      "cost_settled": null,
      "calls_settled": null
    }
  }
}
```

`tokens_used` / `calls_used` / `cost_used` stay **settled** totals so current
`consume()` files remain readable. Holds live only under `reservations`.
Missing `reservations` means `{}` (old state).

**Authoritative vs estimated**

| Dimension | At reserve | At commit | Authority |
| --- | --- | --- | --- |
| Calls | integer `calls` (usually 1) | same integer | exact |
| Tokens | optional `tokens_bound` | provider usage | bound is an estimate |
| Cost | optional `cost_bound` plus `price_table_version` | provider usage or the **same** table version | bound is an estimate, not an invoice |

A cost cap without `cost_bound` is `MissingBound`. Record the price-table
version used for the estimate. Commit leftover-release math uses that
version; it does not silently switch tables.

## Identifiers and lock order

- `reservation_id`: caller-supplied opaque string (AG-04 should use `uuid4`).
- Store key: existing `_period_bucket()` (`key` or `key:YYYY-MM-DD` UTC).
- Lock order: `BudgetGuard._lock`, then `StateStore.update` (already how
  `_consume_persistent` works). Never take the store lock first.

## Transition table

| From | Action | Evidence required | To | Funds |
| --- | --- | --- | --- | --- |
| (absent) | `reserve` | remaining capacity; cost/token bound if that cap exists | `reserved` | hold bound |
| `reserved` | `reserve` same id+bounds | none | `reserved` | unchanged (idempotent) |
| `reserved` | `reserve` same id, different bounds | — | error | unchanged |
| `reserved` | `commit` | provider usage (may be zero tokens on a missing-usage stream) | `committed` | hold → settled actual |
| `reserved` | `cancel` | `dispatch_never_sent=True` | `cancelled` | hold released |
| `reserved` | `cancel` without evidence | — | error | unchanged |
| `reserved` | `mark_unresolved` / crash / timeout | reason string | `unresolved` | hold kept |
| `unresolved` | `commit` | operator or late usage | `committed` | hold → settled actual |
| `unresolved` | `cancel` | `operator_attests_never_dispatched=True` | `cancelled` | hold released |
| `unresolved` | `cancel` without attestation | — | error | unchanged |
| `committed` | `commit` same usage | none | `committed` | unchanged (idempotent) |
| `committed` | `commit` different usage | — | error | unchanged |
| `committed` | `cancel` | — | error | unchanged |
| `cancelled` | `commit` | — | error | unchanged |
| `cancelled` | `cancel` | none | `cancelled` | unchanged (idempotent) |
| corrupt / non-object / NaN | any | — | `StateStoreError` | no silent reset to zero |

## Scenario model (acceptance)

| Scenario | Required result |
| --- | --- |
| Concurrent first use, `max_calls=1`, two workers | exactly one `reserve` succeeds |
| Zero budget (`max_calls=0`) | `reserve` raises `BudgetExceeded`; no record |
| Exactly-at-limit after one settled call | next `reserve` raises `BudgetExceeded` |
| Process death after `reserve` | `recover_crash` → `unresolved`; hold kept |
| Dispatch timeout | `mark_unresolved(reason="timeout")`; hold kept |
| Old state (no `reservations` key) | treated as empty holds; settled counters kept |
| Corrupt state | `StateStoreError`; refuse to zero the ledger |
| Actual cost above `cost_bound` | commit records actual; `estimate_overrun=true`; no silent shrink |

## Period rollover

Existing UTC day buckets stay. A reservation is charged to the bucket it was
**reserved** against. Unresolved rows are not copied into the next day.
Operator resolution writes the original bucket. This is remaining uncertainty
for requests in flight across midnight, not a new database.

## Compatibility and migration

- `check()` and `consume()` stay. Default installs keep today's overshoot
  until AG-04 opts a path into `reserve`.
- First `reserve` may add a `reservations` object. Do not rewrite files for
  idle keys.
- AG-04 must keep existing unit/persistence fixtures readable.
- Windows and Linux multiprocessing stay on `JsonFileStateStore`'s lock file.
  No new backend.

## Unsupported paths (unchanged)

OpenAI Responses, unpatched clients, host tools, provider invoices, and
HttpSink remote kill stay unsupported. See
[enforcement-boundary.md](../enforcement-boundary.md).

No new MCP tools. No new rendered site page. Viewport and host allow/deny
tests are N/A for this design PR.

## AG-04 slice

Implemented for **one** local store plus **one** patched dispatch:
sync OpenAI Chat Completions **without** `stream=True`, and only when
`BudgetGuard` is constructed with a `StateStore`.

`sdk/tests/test_reservation_path.py` and
`examples/enforcement_boundary/reserved_one_dispatch.py` are the proof.
Spawn is the multiprocessing start method used for the two-process race.
Windows was not executed in the environment that added this slice; the
lock file is the same `JsonFileStateStore` path the persistence tests
already use.

### What that path does

- `reserve_for_dispatch` runs inside `StateStore.update` before the mock
  or provider function is called.
- `commit_reservation` writes provider usage. The same usage twice does
  not add the call again.
- `cancel_reservation(..., dispatch_never_sent=True)` frees a hold only
  when this process has not called the provider.
- A provider exception or a failed settlement calls
  `mark_reservation_unresolved`. The hold stays.
- `recover_reservation` is the process-death path. It does not free funds.
- Call holds are exact. A token cap requires `max_tokens` or
  `max_completion_tokens` on the request. A dollar cap estimates an upper
  bound from that token cap and the owned high-water price
  (`price_table` version `2026.07.15`). Missing either bound refuses the
  send. The estimate is not an invoice.

### Still unsupported

- In-memory `BudgetGuard`, `check()`, and `consume()`.
- OpenAI streaming, OpenAI async, and every Anthropic patch.
- OpenAI Responses, unpatched clients, host tools, and `HttpSink` remote kill.
- Mixed processes: an old `check()`/`consume()` worker can still overshoot
  a store that a new worker is reserving. `check()` does not see holds.
- UTC day rollover. Unresolved rows stay on the reserve-day key.
- A provider invoice. `can_claim_invoice_cap()` stays false.
- Actual usage above the reserved bound is stored as `estimate_overrun`.
  It is not written down to the estimate.
