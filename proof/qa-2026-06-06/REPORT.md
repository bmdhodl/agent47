# AgentGuard SDK — End-to-End QA Validation Report

**Date:** 2026-06-06
**Under test:** `agentguard47 1.2.13` (this worktree checkout, commit `15e7bc8`)
**Environment:** isolated venv (`.qa-venv`), Python 3.13.2, Windows 11. Tooling:
pytest 9.0.3, ruff 0.15.16, bandit 1.9.4, Node 22.14, npm 10.9.

> The globally-installed `agentguard` pointed at a *different* worktree
> (`.codex/worktrees/agent47-release-prep-1-2-11`, `0.0.0-dev`) and the global
> env had a broken `agentguard47` dist blocking editable install. A dedicated
> venv was created so every result below is against *this* checkout, not a stale
> install.

---

## Verdict

| Gate | Result |
|------|--------|
| Checkpoint 1 — full pytest + coverage | **PASS** — 784 passed, 92.48% coverage (>=80 gate) |
| Checkpoint 2 — lint / security / structural | **PASS** — ruff clean, bandit clean under policy, structural invariants pass |
| Checkpoint 3 — end-to-end CLI proof path | **PASS** — every proof surface runs offline |
| Checkpoint 4 — MCP surfaces | **PASS** — TS 10/10, Python 15/15 |
| Checkpoint 5 — architecture / page review | **PASS with findings** — site funnel has broken links + stale data (fixed in this PR) |

No High/Medium security issues. All findings are non-blocking and listed below.

---

## Checkpoint 1 — Test suite + coverage

`pytest sdk/tests/ --cov=agentguard --cov-fail-under=80`
- **784 passed**, 0 failed, in 17.3s.
- **Total coverage 92.48%.** Lowest modules: `state.py` 77%, `langchain.py` 73%
  (optional integration), `usage.py` 81%. All core guards >=98%.
- Artifact: `01-pytest-full.txt`

## Checkpoint 2 — Lint, security, structural

- **ruff:** `All checks passed!` (`02-ruff.txt`)
- **bandit (repo policy `-s B101,B110,B112,B311`):** clean (`03-bandit-policy.txt`)
- **bandit (no skips):** only 5 Low/justified findings (`04-bandit-full.txt`):
  - 2× `try/except/continue` in `integrations/langchain.py` — best-effort model/
    usage extraction; correct to swallow.
  - 1× `try/except/pass` in `sinks/otel.py` span end — correct.
  - 1× `random.random()` in `tracing.py` — used for **trace sampling**, not
    crypto. Not a vuln.
- **Structural / 10 Golden Principles:** pass (part of full run,
  `test_architecture.py`). Zero-dep core, one-way imports, exception-raising
  guards, thread-safety locks, <=800-line modules all hold.

### Focused security review (manual, beyond bandit)

| Surface | Finding |
|---------|---------|
| `sinks/http.py` `HttpSink` | **Strong.** SSRF blocklist incl. cloud metadata `169.254.169.254`, RFC1918, loopback, IPv6 ULA/link-local; IDNA/punycode normalization; redirect re-validation (`_SsrfSafeRedirectHandler`); header-injection check on `api_key`; rejects credentials in query string; warns on key-over-HTTP. |
| `sinks/http.py` (minor) | DNS-rebind TOCTOU: `_validate_url` resolves once, urllib resolves again at connect. **Low risk** — endpoint is operator-configured, not attacker input. |
| `state.py` `JsonFileStateStore` | JSON only (no pickle/eval). Atomic write (`mkstemp`+`fsync`+`os.replace`). Cross-process advisory lock with documented stale-break. Corrupt store raises instead of silently zeroing the budget. Sound. |
| `agentguard-mcp/storage.py` | All SQLite uses `?` placeholders — **no injection**. Input validation on tokens/cost; `BEGIN IMMEDIATE` for atomic record. |
| `agentguard-mcp/sync.py` (minor) | Posts to `AGENTGUARD_SYNC_URL` with **no** scheme/SSRF validation (unlike `HttpSink`). Opt-in operator env var, so low risk; flagged as a consistency gap, not a vuln. |
| whole SDK | grep confirms **no** `eval`/`exec`/`pickle`/`marshal`/`os.system`/`yaml.load`/`shell=True`. |
| `mcp-server` npm | `hono` moderate advisory present **transitively** via `@modelcontextprotocol/sdk`. All 4 CVEs are in hono's HTTP-server features (IP allowlist, cookies, JWT mw, route mount). This server is **stdio-only and never imports hono** → not reachable. Routine SDK bump recommended, not urgent. |

## Checkpoint 3 — End-to-end CLI proof path (offline, no API keys)

All run from a clean sandbox dir; artifacts under `e2e/`.

| Command | Result |
|---------|--------|
| `agentguard doctor` | OK, verifies install + writes probe trace + prints next step |
| `agentguard demo` | OK, trips budget/loop/retry guards, writes JSONL |
| `agentguard quickstart --framework {raw,openai,anthropic,langchain,langgraph,crewai}` | all 6 OK |
| `agentguard report <trace>` | OK, cost + guard-event summary + savings ledger |
| `agentguard incident <trace>` | OK, shareable incident |
| `agentguard eval <trace>` | OK, correctly reports `2/3 passed` (loop assertion fails by design) |
| `agentguard decisions <trace>` | OK (`0` decision events for demo trace) |
| `agentguard summarize <trace>` | OK |
| `agentguard skillpack` | OK |
| `examples/starters/*.py` | `raw` runs fully offline; framework starters fail **gracefully** with clear `pip install ...` messages (no tracebacks) |

**Site code snippets executed verbatim** (`05-site-snippets.txt`): both the
`index.html` (`agentguard.init(...)`) and `compare.html`
(`Tracer(guards=[BudgetGuard(max_cost_usd=5.00, warn_at_pct=0.8)])` + `patch_openai`)
examples import and run. The marketing code is real.

## Checkpoint 4 — MCP surfaces

- `mcp-server/` (TypeScript, read-only): `npm test` → **10/10 pass**.
- `agentguard-mcp/` (Python, local budgets): ruff clean, `pytest` → **15/15 pass**.

## Checkpoint 5 — Architecture / page review (`site/`)

Reviewed every page + rendered the homepage (graphics/data verified). Homepage
data is accurate (0 deps, MIT, **1.2.13**, 4 guards). `security.html` is an
intentional redirect to `trust.html`. Findings:

### Broken links / dead anchors (onboarding funnel)
1. `index.html` → `/quickstart` (nav + two primary CTAs "Open/Run quickstart"):
   **no `quickstart.html` exists** → 404. This is the #1 onboarding CTA.
2. `index.html` → `/pricing` (nav + footer): no `pricing.html` → 404.
3. `#pricing` anchor is referenced from `compare.html` (`/#pricing`) and
   `trust.html` (`/index.html#pricing`) but **no element has `id="pricing"`** on
   any page → dead anchors.

### Data accuracy (stale vs shipped SDK)
4. `trust.html` lists **gzip compression**, **retry-with-backoff + idempotency**,
   and **429/Retry-After backpressure** as *"Planned (v0.8.0)"* — but all three
   are **already shipped in `HttpSink`** (verified in `sinks/http.py`). The same
   section calls `HttpSink` "Current," so the page contradicts itself and
   understates the product.
5. `trust.html` "Last updated: February 2026 (v1.2.0)" — stale (current 1.2.13).

### Minor
6. `compare.html` / `security.html` are not linked from the main nav/footer
   (orphan except via sitemap/redirect).
7. CLI `quickstart` exposes `raw,openai,anthropic,langchain,langgraph,crewai`, but
   `examples/starters/` also ships `agentguard_pydantic_ai_quickstart.py` — a
   framework the CLI generator doesn't list. Cosmetic inconsistency.
8. Root-level `QA_REPORT.md` and `WORK_PLAN.md` (from an earlier README PR) sit in
   the repo root, which `CLAUDE.md` says to avoid ("do not add one-off reports/
   work plans to the repo root").

---

## Fixes applied (see `CHANGES.md` in this folder)

Findings 1–5 fixed (frictionless-onboarding + accuracy), plus 6 additional
broken blog links caught by the link checker. Findings 6–8 noted for follow-up.
`CHANGES.md` has the file-by-file rationale and re-run proof.
