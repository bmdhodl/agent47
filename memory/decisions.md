# SDK Decisions

**Last Updated:** 2026-09-20

## Locked
- SDK stays free, MIT, and zero-dependency.
- Distribution > features until directory/community traction improves.
- Product focus is runtime enforcement + coding-agent safety.
- AgentGuard SDK owns local enforcement, local proof, local reports, and local
  setup.
- AgentGuard Dashboard owns retained history, alerts, remote controls, and team
  operations. The public repo does not resurrect a hosted dashboard.
- Public copy describes tested bounds. Do not promise invoice caps, concurrent
  reservations, host-wide interception, or guaranteed bill prevention.
  Canonical map: [docs/enforcement-boundary.md](../docs/enforcement-boundary.md).
- Landing-page navigation never counts as install or activation. Demo
  feedback is voluntary, local, and limited to version, adapter, result, and
  reproduction. No default SDK telemetry.
- GitHub issue #729 / Project 4 is the 2026 planning authority. `ops/03` is
  the SDK-now view and must link that plan instead of drifting into a second
  queue.
- Do not drift into generic observability, prompt optimization, or broad AI
  analytics.
- Keep MCP scope narrow: the published npm server is read-only hosted data;
  local `agentguard-mcp` budgets apply only when a client calls that server.

## Repo Hygiene
- Do not store business-sensitive planning data in this repository.
- Use `memory/` for SDK-only long-term memory.
