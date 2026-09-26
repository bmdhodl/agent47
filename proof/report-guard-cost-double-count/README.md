# report: guard events double-counted the tripping call

Patched OpenAI/Anthropic calls emit `llm.result` (top-level `cost_usd`), then
`guard.budget_exceeded` with `data.cost_usd` = the same call's cost.
`_extract_cost` falls back to `data.cost_usd`, so every cost sum counted the
tripping call twice.

Fix: `evaluation._sum_cost` skips `guard.*` events. Used by `cli._report`,
`summarize_trace` (and therefore `incident`), and `assert_cost_under`.
`savings` no longer picks a guard event as a savings baseline.

| File | What |
|---|---|
| `repro.py` | Real `openai` client, `httpx.MockTransport`, $1.50/call, `BudgetGuard(max_cost_usd=5.0)` |
| `before.txt` | Guard $6.00, report $7.50 |
| `after.txt` | Guard $6.00, report $6.00 |
| `tests-before-fix.txt` | The 4 new regression tests fail against the unfixed SDK |
| `make-check-sdk.txt` | `ci-tools-guard review-readiness lint test`: 1214 passed, 91.55% coverage |
| `make-structural.txt`, `make-security.txt`, `make-preflight.txt`, `make-release-guard.txt` | Pass |
| `make-mcp-env-failure.txt` | `make mcp` fails here on missing `mcp-server/node_modules`; identical on the clean tree. No MCP files changed. |

Run: `PYTHONPATH=sdk python proof/report-guard-cost-double-count/repro.py` (needs `openai`).
