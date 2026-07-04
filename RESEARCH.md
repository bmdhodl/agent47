# RESEARCH — Anthropic per-tool max_tokens positioning update

## Sources

- Vault source card: `Knowledge/sources/2026-06-03-anthropic-advisor-max-tokens-cost-cap.md`
  - Claim: "The advisor tool now supports a max_tokens parameter to cap the advisor model's output per call, reducing latency and output token cost for workloads that don't need full-length advisor responses. Set tools[].max_tokens on the advisor tool definition."
  - Claim: "On the Claude API, you are no longer billed for a request when it returns stop_reason: 'refusal' without Claude having generated any output."
- Anthropic release notes URL of record (in queue task frontmatter): https://platform.claude.com/docs/en/release-notes/overview#june-2-2026
- Queue task: `Queue/agent47/anthropic-advisor-max-tokens-update-positioning.md`

## Verified current README state (before edit)

`README.md:1-13` — Headline is "Stop runaway Python agents before they burn money." `AgentGuard47 is a zero-dependency runtime control SDK for Python agents.` Lead value prop is in-process safety, not specifically per-call vs cross-call distinction.

`README.md:44-72` — `## Why AgentGuard` section has the "Problem -> What AgentGuard does" table. Includes "Run spends too much | Raises BudgetExceeded". The framing does not contrast against provider-native caps.

`README.md:293-313` — `## Runtime Control vs Observability` table has 8 rows comparing AgentGuard to "generic tracing platforms." It does NOT yet have a row about provider-native per-call token caps.

`README.md:218-219` — Auto-patch section mentions Anthropic by name in passing ("If you already call OpenAI or Anthropic directly"). No discussion of per-tool max_tokens.

## Verified competitive notes in repo

- `docs/competitive/vercel-ai-gateway.md` — referenced from README
- `docs/competitive/manifest.md` — referenced from README
- `docs/competitive/agent-security-stack.md` — referenced from README

None of these cover per-tool / per-call provider caps. The new contrast belongs in the README itself (as a row + short paragraph), not as a fourth competitive-notes file, since the task is positioning-paragraph reframing.

## What is in scope for this PR

Per queue task and queue-worker invocation:

- agent47 README positioning update (this PR).
- NOT in scope: bmdpat landing-page edit, PYPI_README, ARCHITECTURE, AGENTS, docs/competitive/*. The bmdpat half is held for Patrick per the queue-sweep instructions.

## Voice constraints from vault AGENTS.md

Forbidden: harness, leverage, streamline, delve, landscape, cutting-edge, game-changer, revolutionary, seamless, robust, holistic, synergy, ecosystem, engagement, retainer, governance audit, book a call, schedule a call, discovery call, SOW, compliance package. No em dashes. Use periods, commas, parens.

## Honest scope of Anthropic's change

- Per-tool `max_tokens` is an **output-token cap per single tool call** on the advisor tool definition.
- It does NOT cover: cross-tool budgets, cross-call accumulation, multi-provider abstraction (OpenAI + Anthropic in one app), retry storms, loop detection, in-process exception-based kill, rate limits per minute, time-window caps, or anything OpenAI-native.
- These are exactly the layers AgentGuard already covers. The positioning update simply states this contrast plainly.
