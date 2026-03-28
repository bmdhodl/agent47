# SDK Roadmap - Now / Next / Later

SDK code changes only. No README, docs, blog, or marketing items.

## Recently Completed

| Item | Status |
|------|--------|
| Eval assertion expansion | Done - `EvalSuite` now has >=12 built-in assertions |
| `estimate_cost` pricing refresh | Done - Anthropic and Google pricing refreshed on 2026-03-26; OpenAI entries retained pending direct re-verification from this environment |
| `RetryGuard` - cap retry attempts per tool | Done - configurable per-tool retry ceilings now raise `RetryLimitExceeded` |
| Offline demo | Done - `agentguard demo` proves budget, loop, and retry enforcement without API keys or network access |
| Incident reporting | Done - `agentguard incident` renders local Markdown/HTML summaries from trace files |
| Install doctor / local validation | Done - `agentguard doctor` verifies local setup, trace writing, and the next minimal integration step |
| Framework quickstart generator | Done in PR - `agentguard quickstart --framework <stack>` prints the smallest credible starter snippet for raw, OpenAI, Anthropic, LangChain, LangGraph, and CrewAI |

## Now (next 2 weeks)

| Item | Success Signal |
|------|---------------|
| Repo-local `.agentguard.json` manifest | Agents and humans can declare local SDK defaults in a tiny static config file without dashboard coupling |
| Executable framework starters | Each supported stack has a minimal runnable example that proves the integration path with AgentGuard |

## Next (next month)

| Item | Success Signal |
|------|---------------|
| Streaming support in patches | `patch_openai` / `patch_anthropic` capture streamed responses without losing final token and cost totals |
| OpenTelemetry Collector sink improvements | `OtelTraceSink` supports custom resource attributes and span links |
| `ContentGuard` - detect PII/sensitive data in agent outputs | New guard class, raises `ContentViolation`, regex-based (no deps) |

## Later (ideas bucket)

| Item | Success Signal |
|------|---------------|
| TypeScript SDK | npm package with parity: LoopGuard, BudgetGuard, TimeoutGuard, Tracer |
| Release hardening and code-scanning cleanup | No open SDK/example/workflow findings remain that block the next PyPI release, and release metadata stays aligned with the shipped tag |
| Repo-local `.agentguard.json` manifest | AI coding agents and humans can declare service name, trace path, and guard defaults without a hosted control plane |
| Cost model alias cleanup | Common provider aliases map cleanly onto canonical model pricing entries without warning spam |
| Policy bundle import/export | Guard and sink settings can be serialized and applied across environments without a hosted control plane |

Each "Later" item stays here until it earns a "Now" or "Next" slot. Items can be deleted without ceremony.
