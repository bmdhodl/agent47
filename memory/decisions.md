# SDK Decisions

**Last Updated:** 2026-04-02

## Locked
- SDK stays free, MIT, and zero-dependency.
- Distribution > features until directory/community traction improves.
- Product focus is runtime enforcement + coding-agent safety.
- A.SDK owns local enforcement, local proof, local reports, and local setup.
- A.D owns retained history, alerts, remote controls, and team operations.
- Do not drift into generic observability, prompt optimization, or broad AI
  analytics.
- Keep MCP scope narrow: read access to traces, alerts, usage, costs, and
  budget health.

## Repo Hygiene
- Do not store business-sensitive planning data in this repository.
- Use `memory/` for SDK-only long-term memory.
