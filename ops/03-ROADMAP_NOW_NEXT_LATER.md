# SDK Roadmap - Now / Next / Later

SDK repo work only. Distribution-facing docs and package metadata count when
they directly strengthen coding-agent adoption.

**Last reviewed:** 2026-09-18

## Current Focus Notes

- Planning authority for 2026 weekly work is
  [GitHub #729](https://github.com/bmdhodl/agent47/issues/729) and
  [Project 4](https://github.com/users/bmdhodl/projects/4). This file is the
  SDK-now view. Do not treat the tables below as a second execution queue.
- Honest enforcement claims (AG-01): recorded-budget preflight vs remaining
  exposure. Canonical map:
  [enforcement boundary](../docs/enforcement-boundary.md).
- Stable SDK releases automatically email active AgentGuard subscribers.
  The release email is owner-authorized (2026-09-18) and uses the existing
  subscriber service. See [release email](../docs/guides/release-email.md).

- Provider patches record final streamed usage once and reject exhausted
  recorded budgets before dispatch.
  See [release state](../memory/state.md) for publication evidence and
  [package metadata](../sdk/pyproject.toml) for the branch version.

- September security pass: repair budget and transport boundaries, test real framework dispatch, then publish a verified SDK release.

- **Human-signal baseline for distribution metrics.** Separate PyPI package
  downloads from scheduled checkout clones. Clone counts can be self-inflicted
  by internal CI workflows; downloads are a directional activation signal, not
  proof of distinct users or production adoption.
- Published release status lives in [release state](../memory/state.md).
  The optional CrewAI advisory remains tracked in #644.
- Official MCP Registry listing is live as `io.github.bmdhodl/agentguard47` at
  `0.2.2` with `isLatest: true`; the older `0.2.1` result is historical
  metadata, not a current release blocker.
- Glama is live at `https://glama.ai/mcp/servers/bmdhodl/agent47`, but its
  public API returned an empty `tools` array on 2026-08-15. Treat that as an
  external directory indexing issue until the rendered listing and API agree.
- The live adoption baseline on 2026-08-15 was 4 GitHub stars and 5/18/106
  PyPI downloads for the last day/week/month. Downloads are a directional
  activation signal, not evidence of distinct users or production adoption.
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
| Provider patches record final streamed usage once | Done - 2026-09-17; OpenAI and Anthropic sync/async `stream=True` calls, plus Anthropic `messages.stream()`, bill the final usage payload once. OpenAI injects `include_usage` when unset. Exhausted-budget preflight is unchanged |
| Clean-wheel activation proof | Done - 2026-08-15; an isolated venv installed the locally built candidate wheel and completed `python -m agentguard`, `doctor`, `demo`, raw `quickstart --write`, generated-starter execution, `report`, and `badge` without API keys or network |
| Competitor Wedge Map consolidation | Done - README wedge map (WorkOS, Uber, Anthropic) refreshed on 2026-06-17 |
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
| Frictionless first-run + badge network effect | Done - bare `agentguard` prints a guided welcome instead of argparse help, `python -m agentguard` works without PATH setup, and `agentguard badge` prints a paste-able "Guarded by AgentGuard" README badge (the lowest-friction install→backlink surface) |
| Ops and release-state freshness | Done - architecture, roadmap, follow-up, and affected SDK memory files were reconciled against the 2026-08-15 mainline and public artifact checks |

## Now (next 2 weeks)

| Item | Success Signal |
|------|---------------|
| Honest enforcement boundary (AG-01 / #730) | A first-time reader can state the protected path and remaining exposure; no invented invoice caps. Map: [enforcement-boundary.md](../docs/enforcement-boundary.md) |
| Activation evidence (AG-02 / #731) | Owner-selected measurement of first value; do not self-select this card after AG-01 |
| Release proof hygiene | The tag publish path verifies the tag matches `sdk/pyproject.toml`, publishes to PyPI first, then creates the GitHub Release |
| MCP distribution hygiene | Official MCP Registry metadata is current at `0.2.2` and `awesome-mcp-servers` PR `#7164` is merged; Glama's empty public `tools` response remains an external listing check, not SDK work |
| Dashboard contract drift checks | Hosted ingest, decision-trace event names, required fields, and remote-kill boundaries remain documented and covered by tests before any release |
| Ops/doc freshness | Reconciled 2026-09-18 with #729. Older dashboard-era hard-cap copy is replaced by the enforcement map |

## Next (next month)

| Item | Success Signal |
|------|---------------|
| Coding-agent profile v2 | Built-in coding-agent defaults cover streamed calls, fuzzy loop patterns, and stronger repo-local safety without increasing setup complexity |
| Cost model alias cleanup | Common provider aliases map cleanly onto canonical model pricing entries without warning spam |
| Release announcement reliability | Release-content automation handles missing GitHub Discussions categories without failing the package release path |

## Later (ideas bucket)

| Item | Success Signal |
|------|---------------|
| TypeScript SDK | npm package with parity: LoopGuard, BudgetGuard, TimeoutGuard, Tracer |
| Savings Ledger heuristics / token efficiency audit | The SDK can attribute conservative exact-vs-estimated token savings beyond cache hits, loops, and retry prevention without drifting into generic prompt optimization |
| OpenTelemetry Collector sink improvements | `OtelTraceSink` supports custom resource attributes and span links without pulling the SDK toward generic observability positioning |
| `ContentGuard` - detect PII/sensitive data in agent outputs | New guard class, raises `ContentViolation`, regex-based (no deps) |
| Policy bundle import/export | Guard and sink settings can be serialized and applied across environments without a hosted control plane |

Each "Later" item stays here until it earns a "Now" or "Next" slot. Items can be deleted without ceremony.
