# SDK Roadmap - Now / Next / Later

SDK repo work only. Distribution-facing docs and package metadata count when
they directly strengthen coding-agent adoption.

**Last reviewed:** 2026-06-05

## Success Metric & Gate

- **The metric is human signal, not volume.** Track GitHub stars, external
  issues/PRs, unique viewers, and referral sources. Download/clone counts are
  reported but labelled machine volume and are not a goal (see
  `memory/state.md` Adoption Reality). Baseline on 2026-06-05: 3 stars, 0
  external issues, ~72 unique viewers/14d.
- **Gate for any `Now` item:** it must move a tracked human signal or create a
  distribution event with a referrer we can watch lift on `make stats`.
  Pure feature work without an adoption tie does not enter `Now`.

## Current Focus Notes

- `v1.2.13` is the shipped public PyPI latest (published 2026-05-30 with a
  matching GitHub Release marked Latest). The dead `v1.2.11` and `v1.2.12` tags
  were deleted on 2026-05-30; do not recreate them without owner approval.
- Official MCP Registry listing is live as `io.github.bmdhodl/agentguard47` and
  the public API now serves `0.2.2` (`isLatest: true`). Republish is scripted
  via `gh workflow run publish-mcp-registry.yml` after each npm publish.
- Glama is live at `https://glama.ai/mcp/servers/bmdhodl/agent47`; all seven
  MCP tools are indexed and graded A. Only "no recent usage" remains (seed via
  "Try in Browser" with the read key or let real traffic clear it).
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

## Now (next 2 weeks)

| Item | Success Signal |
|------|---------------|
| Activation proof polish | A fresh local flow from `pip install` to `agentguard doctor`, `agentguard demo`, and `agentguard quickstart` stays deterministic; repo-only examples and starters remain offline and easy to copy into real repos |
| Release proof hygiene | The tag publish path verifies the tag matches `sdk/pyproject.toml`, publishes to PyPI first, then creates the GitHub Release |
| MCP distribution hygiene | Official MCP Registry metadata is refreshed to `0.2.2`; Glama tool catalog indexes the seven MCP tools; `awesome-mcp-servers` receives the Glama URL without building unrelated features |
| Dashboard contract drift checks | Hosted ingest, decision-trace event names, required fields, and remote-kill boundaries remain documented and covered by tests before any release |
| Ops/doc freshness | `ops/02-ARCHITECTURE.md`, this roadmap, `ops/FOLLOWUP.md`, and memory files stay concise and current enough that agents do not start from stale assumptions |

## Next (next month)

| Item | Success Signal |
|------|---------------|
| Streaming support in patches | `patch_openai` / `patch_anthropic` capture streamed responses without losing final token and cost totals |
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
