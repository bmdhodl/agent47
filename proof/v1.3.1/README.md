# AgentGuard 1.3.1: exhausted-budget preflight

Selected on 2026-09-14 after reviewing current main, release 1.3.0, the roadmap,
and the sole open issue (#644, an upstream optional CrewAI/ChromaDB exposure).
The broad September audit was already shipped. Fixing a reproduced provider
dispatch bypass directly protects existing users and the package's core promise.
It has higher immediate value than another guard, a dashboard expansion, or
repeating registry work. A signup alone is not adoption evidence.

## Behavior and scope

Previously the OpenAI/Anthropic patches charged usage only after dispatch. A
caller that caught BudgetExceeded could keep issuing requests on an exhausted
budget. All four sync/async patches now call BudgetGuard.check() first, emit a
budget stop with request_sent=false, and never dispatch that rejected request.
Successful responses retain exactly-once usage accounting.

The new check is non-consuming and reads the current persisted daily bucket.
Reset and rollover reopen the budget. It does not reserve concurrent capacity,
predict response cost, account streaming totals, or preflight goal-level caps.
Provider-internal retries remain inside the provider library. This is not a
guarantee that every in-flight response fits under a token or dollar cap.

## Evidence

- Initial regression run: 18 failed before the fix. Two retries crossed the
  mocked provider boundary despite exhausted budgets.
- Final Windows Python 3.12.13 suite: 992 passed, one optional LangChain test
  skipped, 91.41% coverage. Command: PYTHONPATH=sdk python -m pytest sdk/tests/
  -q --tb=short --cov=agentguard --cov-report=term --cov-fail-under=80. Exit 0.
- The suite includes architecture invariants and 23 dedicated preflight tests:
  all four patches, call/token/cost and zero caps, accounting, reset, shared
  persisted usage, daily rollover, and corrupt state refusal.
- Pinned Ruff 0.15.13 and Bandit 1.8.6 pass. An earlier local Ruff 0.16.7 run
  flagged unchanged scripts under its newer defaults; it was not the CI version.
- CI toolchain compatibility and review-readiness guards pass. MCP npm test:
  10 passed; npm ci audit: zero vulnerabilities in the resolved MCP lockfile.
- Built wheel and sdist. Installed 1.3.0 from PyPI and the 1.3.1 wheel in
  separate environments. Same demo: 3 attempts, 1-call cap, 3 mocked dispatches
  before and 1 after. Both versions raised 2 exceptions, proving exceptions
  alone were insufficient. See previous-demo.json and candidate-demo.json.
- Real OpenAI 3.14.0 and Anthropic 1.5.0 clients, sync and async, passed with
  HTTP MockTransport: one dispatch, two blocked retries, five tokens recorded.
  No paid provider requests. See provider_smoke.py and provider-smoke.json.
  Reproduce with openai==3.14.0, anthropic==1.5.0, httpx2==2.13.0. These
  provider versions depend on httpx2 (OpenAI requires httpx2>=2.7.0,<3).
  The import is the real package name, not an alias for httpx.
- The image's visible text matches image-copy.txt after whitespace normalization.
  Browser overflow assertions passed at 375, 768, and 1440 pixels. The saved
  screenshot was visually inspected for readable text and correct results.
- Defluff 0.1.2 scanned LinkedIn, X, image text, and alt text separately: all
  scored 0.0. Adjacent receipts include exact input hashes. This detects writing
  patterns, not authorship or image provenance.

Public installation, release provenance, PR review outcomes, and social
permalinks must be added after publication. No candidate result proves those.

Agent sign-off (provider | model | reasoning tier): OpenAI | GPT-6 | auto
