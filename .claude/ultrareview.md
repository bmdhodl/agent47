# Ultrareview Prompt — AgentGuard (`agent47`)

This is the repo-specific brief for `/ultrareview`. Every review agent
spawned by ultrareview should load this file first and treat it as the
ground truth for what "good" looks like in this repository.

Do not review in the abstract. Review against the constraints and
non-negotiables below. If a change violates one of the **hard rules**,
call it out at the top of your report — those block the PR regardless
of how clean the rest of the diff is.

---

## 1. What this repo is

AgentGuard is the **public SDK wedge** for BMD PAT LLC.

- `sdk/agentguard/` — zero-dependency Python runtime guardrails SDK
  (PyPI `agentguard47`, MIT, Python 3.9+). Core is stdlib-only.
- `mcp-server/` — narrow read-only TypeScript MCP surface
  (`@agentguard47/mcp-server`).
- `site/` — static public landing page (Vercel).
- `docs/`, `examples/`, `examples/starters/` — onboarding and proof.

The hosted dashboard, billing, team policy, and remote control plane
live in a **separate private repo** (`agent47-dashboard`). They are
out of scope here.

Core product message to preserve:

> AgentGuard stops coding agents from looping, retrying forever, and
> burning budget.

Latest shipped SDK release: see `memory/state.md` (ground truth).

---

## 2. Load before reviewing

Every review agent must read, in this order, before forming opinions:

1. `memory/state.md`
2. `memory/blockers.md`
3. `memory/decisions.md`
4. `memory/distribution.md`
5. `ops/00-NORTHSTAR.md`
6. `ops/03-ROADMAP_NOW_NEXT_LATER.md`
7. `ops/04-DEFINITION_OF_DONE.md`
8. `ARCHITECTURE.md`
9. `GOLDEN_PRINCIPLES.md`
10. `CLAUDE.md` and `AGENTS.md`

If `memory/` conflicts with older docs, **`memory/` wins**.

Also skim, for the files the PR actually touches:

- `sdk/agentguard/__init__.py` (public API surface + `__all__`)
- `sdk/tests/test_architecture.py` (structural invariants)
- `sdk/tests/test_exports.py` (public-export contract)
- `sdk/pyproject.toml`, `CHANGELOG.md`, `sdk/PYPI_README.md` for any
  release-metadata-adjacent change
- `Makefile` to understand `make preflight / check / structural /
  security / release-guard`
- `PR_DRAFT.md` and `proof/<task-name>/` for the proof the author
  saved

---

## 3. Hard rules — auto-fail the review if any are broken

Flag these at the **top** of the review with severity = blocker. Do
not bury them in a list.

1. **No new hard dependency in core SDK.** Anything under
   `sdk/agentguard/` except `integrations/` and `sinks/otel.py` must
   be stdlib-only. Optional deps in `integrations/` and `sinks/otel.py`
   must be guarded with `try/except ImportError` and listed under
   `[project.optional-dependencies]` in `sdk/pyproject.toml`.
2. **One-way import direction.** Core modules must not import from
   `integrations/` or `sinks/otel.py`. Reverse is fine. Enforced by
   `test_core_does_not_import_integrations`.
3. **Guards raise exceptions, never return bool.** `check()` and
   `auto_check()` raise `LoopDetected`, `BudgetExceeded`,
   `TimeoutExceeded`, `RetryLimitExceeded`,
   `EscalationRequired`, etc. Enforced by
   `test_guard_check_methods_raise_not_return`.
4. **Public API stability.** Removing or renaming a symbol in
   `sdk/agentguard/__init__.py` `__all__` is a breaking change and
   requires an intentional call-out. New exports must have
   docstrings (`test_all_public_exports_have_docstrings`).
5. **Thread-safe mutable state.** Any class with shared mutable
   state needs `self._lock = threading.Lock()` and must be listed in
   `THREAD_SAFE_CLASSES` in `test_architecture.py`.
6. **SDK stays free, MIT, zero-dependency.** No paid-only features,
   no dashboard-only logic, no hosted-product coupling in this repo.
   `memory/decisions.md` is locked on this.
7. **No hardcoded absolute paths** in `.py` files under `sdk/`.
8. **Module size ≤ 800 lines.** Split if exceeded.
9. **Release metadata must stay aligned.** If `sdk/pyproject.toml`
   version, `CHANGELOG.md`, or `sdk/PYPI_README.md` changed — or if
   the PR claims release prep — `make release-guard` must pass and
   the PR must show evidence it was run.
10. **No secrets, no `.env`, no business-sensitive planning.**
    `memory/decisions.md` bans business/outreach data in this repo.
11. **HttpSink must preserve SSRF protection.** Any change under
    `sdk/agentguard/sinks/http.py` that touches URL handling,
    redirects, retry, or gzip gets a dedicated second look.

---

## 4. Review axes (parallelize across agents)

Spawn one agent per axis. Each agent owns its axis end-to-end and
returns a short, structured report. **Do not duplicate work across
axes** — if something is better covered by another axis, reference it
and move on.

### A. Architecture & boundary
- Does the change respect the `sdk/` / `mcp-server/` / `site/` /
  `docs/` boundary described in `ARCHITECTURE.md` §3 and §6?
- Any drift toward dashboard work, prompt optimization, generic
  observability, or broad AI analytics? (`memory/decisions.md`
  forbids this.)
- Import direction: core → integrations is banned. Any new cycles?
- Does the change belong in this repo at all, or is it dashboard
  work masquerading as SDK work?

### B. Golden Principles & structural invariants
Walk all 10 rules in `GOLDEN_PRINCIPLES.md`. For each: state
pass/fail, point at the enforcing test, and cite the diff hunk that
caused any fail. If `test_architecture.py` was edited, explain
whether the invariant itself weakened or just the allow-list grew.

### C. Public API & backwards compatibility
- Diff `sdk/agentguard/__init__.py` and every `__all__` touched.
- For each added/removed/renamed symbol: is it intentional? Is the
  docstring present? Does `test_exports.py` still pass?
- Any public signature change (guard params, sink `emit`, Tracer
  surface, CLI flags)? Call out migration impact.
- CLI: did any `agentguard <subcommand>` change its flags, exit
  codes, or output format? That's user-visible.

### D. Guard & sink semantics
- New/changed guards: inherits `BaseGuard`, `check()` raises,
  `auto_check(event_name, event_data)` present, `_lock` on mutable
  state, exported, added to `THREAD_SAFE_CLASSES`.
- New/changed sinks: inherits `TraceSink`, implements
  `emit(event: Dict[str, Any]) -> None`, optional deps guarded,
  exported from `sinks/__init__.py` and top-level `__init__.py`.
- Trace event shape preserved:
  `{service, kind, phase, trace_id, span_id, parent_id, name, ts,
  duration_ms, data, error, cost_usd}`.

### E. Tests, coverage, and proof
- `make check` evidence in the PR (or equivalent direct commands).
- Coverage ≥ 80% (`--cov-fail-under=80`). Current baseline is ~93%;
  any meaningful drop needs justification.
- New functionality has targeted tests, not just smoke coverage.
- No persistent pytest config warnings introduced.
- `proof/<task-name>/` exists and contains real artifacts (command
  output, JSONL traces, example runs) — not just placeholder text.
- `PR_DRAFT.md` updated with title, scope, non-goals, proof, and
  saved artifacts.

### F. Release readiness (only if the PR is release-adjacent)
- `sdk/pyproject.toml` version matches the intended tag.
- `CHANGELOG.md` entry exists for that version and accurately
  reflects the diff.
- `sdk/PYPI_README.md` was regenerated from `README.md` +
  `CHANGELOG.md` (`scripts/generate_pypi_readme.py --write`).
- `make release-guard` passes.
- If `HttpSink`, tracing, or the hosted-ingest contract changed,
  `sdk/tests/integration_dashboard.py` was run with a real key and
  the probe `trace_id` appears in the hosted response.

### G. Security & supply chain
- `make security` (bandit) passes with the allow-list in
  `Makefile` (`-s B101,B110,B112,B311`). Any new suppression must be
  justified.
- No secrets, tokens, or API keys in diff, tests, fixtures, or
  proof artifacts. Check `.gitleaksignore` was not silently
  expanded.
- `HttpSink`: SSRF guard, redirect handling, gzip, retry, and
  timeout behavior all intact.
- No new network calls from core or from CLI default paths
  (`doctor`, `demo`, `quickstart` must stay local-first, no API
  keys required).
- Any new subprocess, `eval`, `exec`, `pickle`, or shell call is a
  red flag in this SDK.

### H. Docs, examples, and distribution
- `README.md`, `llms.txt`, `docs/`, `examples/`, and
  `examples/starters/` stay consistent with the diff.
- Coding-agent onboarding path is still credible end-to-end:
  `pip install agentguard47` → `agentguard doctor` →
  `agentguard demo` → `agentguard quickstart --framework <stack>` →
  starter file runs.
- Claims in docs match actual behavior (versions, flags, guard
  params in `AGENTS.md` §Guard Parameters table).
- `MORNING_REPORT.md` and `PR_DRAFT.md` reflect the current PR if
  they were touched.
- Package metadata (name, description, keywords, URLs) still
  positions the SDK as zero-dependency runtime guardrails for
  coding-agent safety.

### I. Scope hygiene & simplification
- Does the diff do more than the stated goal? Flag speculative
  abstractions, framework sprawl, and novelty features with weak
  adoption value (`CLAUDE.md` → "Avoid" list).
- Can any new helper be deleted in favor of an existing pattern
  (`TraceSink`, guard exceptions, `.agentguard.json`, existing CLI
  proof flows)?
- Are there half-finished TODOs, dead code, or commented-out
  blocks?
- Would a smaller, more boring diff ship the same user value?

---

## 5. Common anti-patterns in this repo

Reviewers should recognize and flag these on sight.

- A PR that adds a new guard "because it's cool" when the roadmap
  says distribution > features.
- Introducing `requests`, `httpx`, `pydantic`, `rich`, etc. into
  core. **Core is stdlib-only.** Use `urllib` / `json` /
  `dataclasses` / `argparse`.
- A guard whose `check()` returns `True`/`False` or `None`.
- Silently broadening `sdk/pyproject.toml` runtime deps instead of
  optional extras.
- Adding dashboard positioning, hosted pricing, or team-policy
  language to `site/`, `README.md`, or `docs/`.
- Touching `ops/02-ARCHITECTURE.md` without also reconciling
  `ARCHITECTURE.md` (they drift).
- Work that chases the Glama listing block from
  `memory/blockers.md` — don't route around it, don't build new
  guards just because it's blocked.
- CLI flag renames without a compatibility shim or changelog note.
- Tests that import private internals for convenience instead of
  going through the public API, unless explicitly hardening them.
- Proof artifacts that are fabricated or copy-pasted from earlier
  PRs.

---

## 6. Output format (per review agent)

Return a single Markdown block:

```
## Ultrareview — <axis name>

### Blockers
- <one line each, cite file:line, reference hard rule #>

### Must-fix before merge
- <one line each, cite file:line>

### Nice-to-have
- <one line each, cite file:line>

### Verified clean
- <what you explicitly checked and found good>

### Open questions for the author
- <one line each>
```

Rules:
- Cite `file:line` for every finding so the author can jump to it.
- If an axis has nothing to say, return the section with empty
  bullets — don't invent findings to look thorough.
- Do not restate the diff. Reviewers read the diff themselves.
- Do not rewrite the author's code; describe the change you want.
- Keep each bullet to one sentence. If it needs a paragraph, link
  to a file/line and summarize.

---

## 7. Meta-reviewer (aggregator) instructions

When aggregating across axis agents:

1. Lead with **all blockers**, deduplicated, sorted by hard-rule
   number then by file.
2. Then must-fix, then nice-to-have, then open questions.
3. Collapse duplicate findings that multiple axes surfaced — keep
   the most specific one and attribute the others.
4. End with a one-line merge recommendation:
   `merge` / `merge after must-fix` / `do not merge`.
5. If the PR is release-adjacent and axis F found any gap, the
   recommendation is at best `merge after must-fix` — release
   metadata drift is never "nice-to-have" here.

Keep the aggregated report under ~400 lines. If it's longer, the
diff is probably too large and that itself is a finding.
