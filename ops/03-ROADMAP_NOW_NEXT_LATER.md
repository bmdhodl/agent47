# SDK Roadmap — Now / Next / Later

SDK code changes only. No README, docs, blog, or marketing items.

## Now (next 2 weeks)

| Item | Success Signal |
|------|---------------|
| — | No SDK code changes planned — current focus is README/launch prep in other tracks |

## Next (next month)

| Item | Success Signal |
|------|---------------|
| `estimate_cost` pricing refresh | Pricing dict matches current OpenAI/Anthropic/Google published rates |
| Eval assertion expansion | `EvalSuite` has >=12 built-in assertions (currently 8) |

## Later (ideas bucket)

| Item | Success Signal |
|------|---------------|
| `ContentGuard` — detect PII/sensitive data in agent outputs | New guard class, raises `ContentViolation`, regex-based (no deps) |
| OpenTelemetry Collector sink improvements | `OtelTraceSink` supports custom resource attributes and span links |
| TypeScript SDK | npm package with parity: LoopGuard, BudgetGuard, TimeoutGuard, Tracer |
| `RetryGuard` — cap retry attempts per tool | New guard, configurable per-tool retry limits |
| Streaming support in patches | `patch_openai` traces streaming responses with incremental token counts |

Each "Later" item stays here until it earns a "Now" or "Next" slot. Items can be deleted without ceremony.
