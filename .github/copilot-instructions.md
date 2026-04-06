# AgentGuard Copilot Review Instructions

Review this repo as a public SDK + MCP project, not as the private dashboard.

Priorities:
- Preserve the SDK/dashboard boundary. Do not suggest dashboard, billing, or
  private control-plane changes in this repo.
- Keep the SDK free, MIT, zero-dependency, and local-first.
- Favor coding-agent safety and runtime enforcement over generic observability,
  analytics, or prompt tooling.
- Keep MCP scope narrow: read access to traces, alerts, usage, costs, and
  budget health.

When reviewing changes, prioritize:
- runtime correctness and regression risk
- schema/contract drift between SDK output and hosted ingest expectations
- local-first onboarding: `doctor`, `demo`, `quickstart`, starter files
- package metadata and docs consistency across README, PyPI, npm, and MCP
  registry metadata
- architectural invariants in `sdk/tests/test_architecture.py`
- release-gate and proof quality for user-visible or release-facing changes

Push back on:
- new hard dependencies in `sdk/agentguard`
- broad "AI agent platform" wording that weakens the coding-agent wedge
- speculative abstractions, framework sprawl, or generic observability drift
- changes that move hosted-only behavior into the public SDK path without
  evidence

Assume the best PRs in this repo are:
- small, composable, and evidence-backed
- explicit about scope and non-goals
- validated with targeted tests, lint, and release/doc sync checks
