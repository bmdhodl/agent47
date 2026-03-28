# SDK Roadmap - Now / Next / Later

SDK code changes only. No README, docs, blog, or marketing items.

Release note: feature freeze is in effect until the next PyPI cleanup release ships.

## Recently Completed

| Item | Status |
|------|--------|
| Eval assertion expansion | Done - `EvalSuite` now has >=12 built-in assertions |
| `estimate_cost` pricing refresh | Done - Anthropic and Google pricing refreshed on 2026-03-26; OpenAI entries retained pending direct re-verification from this environment |
| `RetryGuard` - cap retry attempts per tool | Done - configurable per-tool retry ceilings now raise `RetryLimitExceeded` |
| Offline demo | Done - `agentguard demo` proves budget, loop, and retry enforcement without API keys or network access |
| Incident reporting | Done - `agentguard incident` renders local Markdown/HTML summaries from trace files |
| Install doctor / local validation | Done - `agentguard doctor` verifies local setup, trace writing, and the next minimal integration step |

## Now (next 2 weeks)

| Item | Success Signal |
|------|---------------|
| Release hardening and code-scanning cleanup | No open SDK/example/workflow findings remain that block a clean PyPI release, and release metadata matches the shipped tag |

## Next (next month)

| Item | Success Signal |
|------|---------------|
| Streaming support in patches | `patch_openai` / `patch_anthropic` capture streamed responses without losing final token and cost totals |
| Framework quickstart generator | One local command prints the exact minimal snippet for the user's framework without any dashboard dependency |
| OpenTelemetry Collector sink improvements | `OtelTraceSink` supports custom resource attributes and span links |
| `ContentGuard` - detect PII/sensitive data in agent outputs | New guard class, raises `ContentViolation`, regex-based (no deps) |

## Later (ideas bucket)

| Item | Success Signal |
|------|---------------|
| TypeScript SDK | npm package with parity: LoopGuard, BudgetGuard, TimeoutGuard, Tracer |
| Repo-local `.agentguard.json` manifest | AI coding agents and humans can declare service name, trace path, and guard defaults without a hosted control plane |
| Cost model alias cleanup | Common provider aliases map cleanly onto canonical model pricing entries without warning spam |
| Policy bundle import/export | Guard and sink settings can be serialized and applied across environments without a hosted control plane |

Each "Later" item stays here until it earns a "Now" or "Next" slot. Items can be deleted without ceremony.
