# RESEARCH — competitor wedge map README batch (2026-06-12)

## Sources

- Vault batch card: `Queue/agent47/competitor-wedge-map-readme-batch.md`
  (supersedes workos-positioning-update, agentguard-uber-validation-readme,
  thinking-tokens-breakdown-agentguard; holds mem0-contamination-positioning).
- Batching rule: `Queue/agent47/_README.md` § Competitor-positioning batching
  rule (2026-06-07), incl. fact-gating clause.
- WorkOS: vault `Knowledge/sources/2026-06-04-workos-scoped-agent-credentials.md`.
  Claim used: WorkOS productizes scoped agent credentials (agent-specific
  identity, per-agent RBAC, audit logs). Identity-time vs run-time framing;
  "different wedges, same buyer"; composable, not adversarial. Confidence
  marked medium in the source (marketing-layer copy), so README copy describes
  the category axis, not WorkOS internals.
- Uber: vault `Knowledge/sources/2026-06-03-uber-caps-claude-code-1500.md`,
  confidence high, verified 2026-06-04. URL of record:
  https://simonwillison.net/2026/Jun/3/uber-caps-usage/ (Bloomberg report).
  Exact claim: Uber limits all employees to $1,500/month in token spending on
  EACH AI coding tool. Per-tool, per-employee. The task card's shorthand
  "$1,500/developer Claude Code cap" is imprecise; README uses the accurate
  per-employee-per-tool form. The per-tool blindspot (one dev across Claude
  Code + Cursor + Copilot can spend 3x before policy fires) is itself the
  wedge argument for a cross-tool runtime envelope.
- Anthropic per-tool `max_tokens`: already cited in README.md:62-64 with the
  2026-06-02 release-notes URL. Wedge map reuses the existing fact; adds no
  new claim.
- Routers/gateways: existing README.md:53-58 (Manifest, Vercel AI Gateway) and
  docs/competitive/manifest.md, docs/competitive/vercel-ai-gateway.md. Reused.

## Verified current README state (before edit)

- README.md:48-98 "Why AgentGuard": in-process vs router framing (Manifest,
  Vercel AI Gateway), cross-call cross-provider envelope, per-tool
  `max_tokens` comparison table. No WorkOS, no Uber, no unified wedge section.
- README.md:351-377 "Runtime Control vs Observability": capability table +
  competitive notes links. Insertion point: new section goes directly after
  this one (before "Decision Traces", README.md:379).
- `grep -i mem0 README.md` -> no match (must stay that way).
- `grep -i "WorkOS|Uber|1,500" README.md` -> no match before edit.

## Build/CI constraints verified

- `sdk/PYPI_README.md` is GENERATED from README.md by
  `scripts/generate_pypi_readme.py` (README_PATH = Path("README.md"), line 11).
  `sdk/tests/test_pypi_readme_sync.py::test_committed_pypi_readme_is_in_sync`
  diffs the committed file against the generator output. Any README edit
  requires `python scripts/generate_pypi_readme.py --write` + committing
  sdk/PYPI_README.md.
- Repo CLAUDE.md: "do not add one-off reports ... to the repo root" — WORK_PLAN,
  RESEARCH, QA_REPORT already exist at root on main from prior worker runs;
  this run refreshes them in place, adds no new root files.
- Anchor-style internal links (`#runtime-control-vs-observability`) are already
  used at README.md:58, so an anchor link in the new section is safe for the
  PyPI link rewriter.

## Decisions

- Thinking-token accounting NOT mentioned even in prose: the parsing of
  `usage.output_tokens_details.thinking_tokens` is a deferred feature
  (cannon-paused). A README differentiator claim for an unshipped capability
  would be false. The card's "may mention" is permissive, not required.
- mem0 excluded entirely per fact-gating (false 57-71% stat, open Request
  2026-06-04-2330). No memory-layer bullet ships in this batch.
