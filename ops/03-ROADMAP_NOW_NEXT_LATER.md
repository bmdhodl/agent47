# SDK Roadmap - Now / Next / Later

SDK repo work only. Distribution-facing docs and package metadata count when
they directly strengthen coding-agent adoption.

**Last reviewed:** 2026-05-02

## Current Focus Notes

- Latest shipped SDK release is `v1.2.9`; current work is post-release
  hardening and activation, not a new feature push.
- Official MCP Registry listing is live as `io.github.bmdhodl/agentguard47`;
  keep MCP narrow and read-only while Glama remains blocked.
- Dashboard alignment is current for hosted ingest and decision traces. The
  remote-kill boundary is documented: the SDK emits events and enforces local
  guards, while the dashboard owns retained history, alerts, and team
  operations.
- The strongest package-installed proof path is `doctor` -> `demo` ->
  `quickstart`; repo checkouts also have starters and the coding-agent
  review-loop proof.

## Recently Completed

| Item | Status |
|------|--------|
| Eval assertion expansion | Done - `EvalSuite` now has >=12 built-in assertions |
| `estimate_cost` pricing refresh | Done - Anthropic and Google pricing refreshed on 2026-03-26; OpenAI entries retained pending direct re-verification from this environment |
| `RetryGuard` - cap retry attempts per tool | Done - configurable per-tool retry ceilings now raise `RetryLimitExceeded` |
| Offline demo | Done - `agentguard demo` proves budget, loop, and retry enforcement without API keys or network access |
| Incident reporting | Done - `agentguard incident` renders local Markdown/HTML summaries from trace files |
| Install doctor / local validation | Done - `agentguard doctor` verifies local setup, trace writing, and the next minimal integration step |
| Framework quickstart generator | Done - `agentguard quickstart --framework <stack>` prints the smallest credible starter snippet for raw, OpenAI, Anthropic, LangChain, LangGraph, and CrewAI |
| Savings Ledger foundation | Done - normalized usage capture and local exact-vs-estimated savings summaries now flow through SDK reports |
| Coding-agent local profile | Done - `profile=\"coding-agent\"` ships tighter loop and retry defaults for repo automation and coding agents |
| Repo-local `.agentguard.json` manifest | Done - humans and coding agents can share static local SDK defaults without dashboard coupling |
| Executable framework starters | Done - each supported stack now has a minimal runnable starter file in `examples/starters/` |
| Release stabilization for coding-agent onboarding | Done - docs, release metadata, package artifacts, and publish checks were aligned for `v1.2.4` |
| Decision query surfaces and MCP validation | Done - normalized decision extraction now works locally via `agentguard decisions`, via MCP through `get_trace_decisions`, and through repo CI/preflight coverage for the MCP server |
| Decision-trace instrumentation for human review workflows | Done - `decision.*` events, helper APIs, docs, and a local example now capture proposals, edits, approvals, and binding outcomes through the normal SDK event path |
| Coding-agent skillpack generation | Done - `agentguard skillpack` now generates `.agentguard.json` plus repo-local instructions for Codex, Claude Code, Copilot, and Cursor so coding-agent onboarding no longer depends on manual snippet copying |
| Managed-agent session correlation | Done - `session_id` now lets disposable harnesses or short-lived workers emit separate traces that still roll up under one higher-level local session for coding-agent and managed-agent runtimes |
| Budget-aware escalation guard | Done - `BudgetAwareEscalation` now lets apps keep a cheaper default model and escalate hard turns using token, confidence, tool-depth, or custom-rule signals without provider-specific SDK routing |
| Dashboard contract alignment for v1.2.9 | Done - hosted ingest shape and decision-trace defaults are documented and covered by tests; remote-kill boundaries are documented |
| Coding-agent review-loop proof | Done - `examples/coding_agent_review_loop.py` demonstrates local budget and retry stops for review/refinement loops without API keys or network calls |
| Follow-up handoff | Done - `FOLLOWUP.md` records next hygiene and activation-metrics work without burying it in PR notes |

## Now (next 2 weeks)

| Item | Success Signal |
|------|---------------|
| Activation proof polish | A fresh local flow from `pip install` to `agentguard doctor`, `agentguard demo`, and `agentguard quickstart` stays deterministic; repo-only examples and starters remain offline and easy to copy into real repos |
| MCP distribution hygiene | Official MCP Registry metadata remains current; Glama and `awesome-mcp-servers` stay tracked without building unrelated features to route around the blocker |
| Dashboard contract drift checks | Hosted ingest, decision-trace event names, required fields, and remote-kill boundaries remain documented and covered by tests before any release |
| Ops/doc freshness | `ops/02-ARCHITECTURE.md`, this roadmap, `FOLLOWUP.md`, and memory files stay concise and current enough that agents do not start from stale assumptions |

## Next (next month)

| Item | Success Signal |
|------|---------------|
| Streaming support in patches | `patch_openai` / `patch_anthropic` capture streamed responses without losing final token and cost totals |
| Coding-agent profile v2 | Built-in coding-agent defaults cover streamed calls, fuzzy loop patterns, and stronger repo-local safety without increasing setup complexity |
| Cost model alias cleanup | Common provider aliases map cleanly onto canonical model pricing entries without warning spam |
| Opt-in activation metrics design | A short design explains what, if anything, could be measured without default telemetry, payload capture, or local-only privacy drift |

## Later (ideas bucket)

| Item | Success Signal |
|------|---------------|
| TypeScript SDK | npm package with parity: LoopGuard, BudgetGuard, TimeoutGuard, Tracer |
| Savings Ledger heuristics / token efficiency audit | The SDK can attribute conservative exact-vs-estimated token savings beyond cache hits, loops, and retry prevention without drifting into generic prompt optimization |
| OpenTelemetry Collector sink improvements | `OtelTraceSink` supports custom resource attributes and span links without pulling the SDK toward generic observability positioning |
| `ContentGuard` - detect PII/sensitive data in agent outputs | New guard class, raises `ContentViolation`, regex-based (no deps) |
| Policy bundle import/export | Guard and sink settings can be serialized and applied across environments without a hosted control plane |

Each "Later" item stays here until it earns a "Now" or "Next" slot. Items can be deleted without ceremony.
