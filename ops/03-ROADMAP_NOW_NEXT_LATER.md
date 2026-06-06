# SDK Roadmap - Now / Next / Later

SDK repo work only. Distribution-facing docs and package metadata count when
they directly strengthen coding-agent adoption.

**Last reviewed:** 2026-06-06

## Current Focus Notes

- Current SDK release candidate is `v1.2.13` from `main`; public PyPI latest
  remains `v1.2.10` until the next tag publish succeeds. The stale `v1.2.11`
  tag failed before PyPI publish, and the stale `v1.2.12` tag points at a
  `1.2.10` checkout. Do not reuse either tag without explicit owner approval.
- Distribution-signal baseline: read PyPI published-package downloads and human
  GitHub signals (stars, referrers), not raw clone counts. CI never installs the
  published `agentguard47` wheel (it tests the local checkout), so published-
  download counts are real signal. Clone counts are partly self-inflicted by
  scheduled checkout workflows, so discount them as a popularity metric.
- Official MCP Registry listing is live as `io.github.bmdhodl/agentguard47` at
  package version `0.2.2`. The `awesome-mcp-servers` listing PR is open. Refresh
  registry metadata only; do not touch SDK runtime code for distribution work.
- Glama release is live at `https://glama.ai/mcp/servers/bmdhodl/agent47` with
  the MCP tools now indexed (profile completeness ~92%).
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
| Dashboard contract alignment for v1.2.10 | Done - hosted ingest shape and decision-trace defaults are documented and covered by tests; remote-kill boundaries are documented |
| Coding-agent review-loop proof | Done - `examples/coding_agent_review_loop.py` demonstrates local budget and retry stops for review/refinement loops without API keys or network calls |
| Follow-up handoff | Done - `ops/FOLLOWUP.md` records next hygiene and activation-metrics work without burying it in PR notes |
| Opt-in activation metrics design | Done - `docs/guides/activation-metrics-design.md` defines allowed questions, consent boundaries, forbidden fields, and local-first non-goals without adding telemetry |
| Release tag version guard | Done - the publish path now verifies the git tag matches `sdk/pyproject.toml` and gates announcements on a published release, closing the `v1.2.11`/`v1.2.12` mismatch class |
| MCP Registry refresh to 0.2.2 | Done - official registry listing now reports `0.2.2` and Glama indexes the MCP tools; OIDC automates the registry publish |
| BudgetGuard persistent cross-process state | Done - `BudgetGuard` can persist spend across processes so disposable workers and multi-process runs share one budget ceiling |
| Positioning vs WorkOS and Manifest | Done - README and docs clarify the runtime budget plus kill-switch wedge against identity-time (WorkOS) and LLM-router (Manifest) tools |

## Now (next 2 weeks)

| Item | Success Signal |
|------|---------------|
| Activation proof polish | A fresh local flow from `pip install` to `agentguard doctor`, `agentguard demo`, and `agentguard quickstart` stays deterministic; repo-only examples and starters remain offline and easy to copy into real repos |
| Distribution-signal hygiene | Distribution reporting reads PyPI published-package downloads and human GitHub signals, not raw clone counts; clone-count spikes are discounted as self-inflicted scheduled-CI checkouts |
| Next tag publish | The next tag matches `sdk/pyproject.toml`, publishes to PyPI first, then creates the GitHub Release, so public PyPI moves past `v1.2.10` cleanly |
| Dashboard contract drift checks | Hosted ingest, decision-trace event names, required fields, and remote-kill boundaries remain documented and covered by tests before any release |
| Ops/doc freshness | `ops/02-ARCHITECTURE.md`, this roadmap, `ops/FOLLOWUP.md`, and memory files stay concise and current enough that agents do not start from stale assumptions |

## Next (next month)

| Item | Success Signal |
|------|---------------|
| Streaming support in patches | `patch_openai` / `patch_anthropic` capture streamed responses without losing final token and cost totals |
| Coding-agent profile v2 | Built-in coding-agent defaults cover streamed calls, fuzzy loop patterns, and stronger repo-local safety without increasing setup complexity |
| Cost model alias cleanup | Common provider aliases map cleanly onto canonical model pricing entries without warning spam |
| Persistent budget guard docs | The new cross-process `BudgetGuard` state has a short guide and example so multi-process and disposable-worker runs adopt a shared budget ceiling without guessing |

## Later (ideas bucket)

| Item | Success Signal |
|------|---------------|
| TypeScript SDK | npm package with parity: LoopGuard, BudgetGuard, TimeoutGuard, Tracer |
| Savings Ledger heuristics / token efficiency audit | The SDK can attribute conservative exact-vs-estimated token savings beyond cache hits, loops, and retry prevention without drifting into generic prompt optimization |
| OpenTelemetry Collector sink improvements | `OtelTraceSink` supports custom resource attributes and span links without pulling the SDK toward generic observability positioning |
| `ContentGuard` - detect PII/sensitive data in agent outputs | New guard class, raises `ContentViolation`, regex-based (no deps) |
| Policy bundle import/export | Guard and sink settings can be serialized and applied across environments without a hosted control plane |

Each "Later" item stays here until it earns a "Now" or "Next" slot. Items can be deleted without ceremony.
