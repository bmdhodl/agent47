# SDK Decisions

- 2026-10-03: Patrick approved the prepared #736 Responses/Agents minimum CI
  job and required-result inventory update. Use the separate hash-pinned
  OpenAI 1.66.3 / Agents 0.0.3 lock on Ubuntu/Python 3.12, preserving Chat's
  OpenAI 1.40.0 floor. Real floor tests must run without skips, including the
  approved #817 free-client cases. This does not authorize a release, CrewAI
  advisory exception, new runtime API, or broader held adapter work.

**Last Updated:** 2026-10-03

## Python support policy (owner approved 2026-10-03, #831)

- Patrick accepted Python 3.11 as the new SDK minimum after the earlier 3.10
  recommendation was corrected: Python 3.10 reached EOL on 2026-10-01.
  Python 3.11 security support is scheduled through October 2027.
  Source: [Python supported versions](https://devguide.python.org/versions/).
- This intentionally retires Python 3.9/3.10. Prepare 2.0.0 as the next
  candidate, align metadata, CI and migration docs, and merge #831 only with
  green checks. Published 1.4.0 remains available; no tag/publication is authorized.
- Compile the CI-tools lock with the configured Python 3.11; keep authentic
  compiler provenance and all retained tool versions/hashes. The compiler
  removes exceptiongroup, tomli and typing-extensions backports that the
  new interpreter no longer needs. Retire the old
  Dependabot version ignores that existed solely for the Python 3.9 floor.
- Tradeoff: users of older interpreters must recreate their environment with
  Python 3.11+ or pin 1.4.0. Revisit the supported floor by 2027-07-01, before
  Python 3.11's scheduled end of security support.

## Previous CI compiler and SDK interpreter decision (superseded by #831)

- Preserve #662's separate interpreters: compile the CI-tool lock with the
  configured Python 3.10; install and test those tools and the SDK on 3.9.
  Dependabot selects the actual pip-compile header before `.python-version`.
  Retain the explicit `importlib-metadata` pin for build's Python 3.9 dependency.
  #827 regenerates the lock, preserves all existing pins/hashes, and retains
  the compiler's Windows `colorama` dependency. Do not relabel compiler provenance
  or raise the SDK floor to repair dependency submission.

## Owner-approved local billing correction (2026-10-03)

- #817 may add the runtime-only `free_local_clients` keyword to OpenAI sync/async
  patches and `init()`. The owner approved the narrow per-client proposal.
- Declare exact clients free; keep paid defaults, token/call limits, existing
  reservation boundaries and lifecycle restoration. No URL/model inference,
  new export, dependency, saved configuration, or release is authorized here.
- This exception does not remove the external-adoption gate for broader SDK
  feature work in `ops/FOLLOWUP.md` or the held adapter issues.

## Locked
- SDK stays free, MIT, and zero-dependency.
- Distribution > features until directory/community traction improves.
- Product focus is runtime enforcement + coding-agent safety.
- AgentGuard SDK owns local enforcement, local proof, local reports, and local
  setup.
- AgentGuard Dashboard owns retained history, alerts, remote controls, and team
  operations. The public repo does not resurrect a hosted dashboard.
- Public copy describes tested bounds. Do not promise invoice caps,
  host-wide interception, or guaranteed bill prevention. Concurrent
  reservation is the store-backed sync OpenAI non-stream path and
  store-backed streams.
  Canonical map: [docs/enforcement-boundary.md](../docs/enforcement-boundary.md).
- Landing-page navigation never counts as install or activation. Demo
  feedback is voluntary, local, and limited to version, adapter, result, and
  reproduction. No default SDK telemetry.
- Local reservation is shipped for store-backed sync non-streaming OpenAI
  and for store-backed OpenAI/Anthropic streams. Unknown provider outcomes
  cannot silently free funds. A stream that stops early keeps a token or
  dollar hold; partial usage is not a settlement. Call holds can be exact;
  token/dollar holds need an explicit request bound and are still not an
  invoice cap. Canonical
  contract: [docs/guides/reservation-contract.md](../docs/guides/reservation-contract.md).
  `BudgetGuard.check()` / `consume()` stay recorded-budget preflight.
  In-memory streams, async non-stream calls, and Anthropic non-stream calls
  do not reserve.
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
