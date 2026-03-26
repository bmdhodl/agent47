# SDK Roadmap - Now / Next / Later

SDK code changes only. No README, docs, blog, or marketing items.

## Recently Completed

| Item | Status |
|------|--------|
| Eval assertion expansion | Done - `EvalSuite` now has >=12 built-in assertions |
| `estimate_cost` pricing refresh | Done - Anthropic and Google pricing refreshed on 2026-03-26; OpenAI entries retained pending direct re-verification from this environment |

## Now (next 2 weeks)

| Item | Success Signal |
|------|---------------|
| `RetryGuard` - cap retry attempts per tool | New guard class, raises `RetryLimitExceeded` after a configurable per-tool retry ceiling |

## Next (next month)

| Item | Success Signal |
|------|---------------|
| Streaming support in patches | `patch_openai` traces streaming responses with incremental token counts |
| OpenTelemetry Collector sink improvements | `OtelTraceSink` supports custom resource attributes and span links |

## Later (ideas bucket)

| Item | Success Signal |
|------|---------------|
| `ContentGuard` - detect PII/sensitive data in agent outputs | New guard class, raises `ContentViolation`, regex-based (no deps) |
| TypeScript SDK | npm package with parity: LoopGuard, BudgetGuard, TimeoutGuard, Tracer |
| Cost model alias cleanup | Common provider aliases map cleanly onto canonical model pricing entries without warning spam |

Each "Later" item stays here until it earns a "Now" or "Next" slot. Items can be deleted without ceremony.
