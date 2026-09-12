# SDK security and runtime audit, 2026-09-12

Scope: the Python SDK, optional integration boundaries, HTTP transport, package metadata, both MCP surfaces, and release automation. This is a source and behavioral audit, not a claim that every possible vulnerability has been eliminated.

## Findings fixed

- Non-finite/negative budget caps could disable comparisons. Constructors now reject them, including timeout and payment limits.
- Corrupt persisted budget counters could poison totals. Invalid state now raises before rewriting the store.
- Budget warning callbacks could deadlock on re-entry. Callbacks execute after releasing the lock; zero caps no longer divide by zero.
- A failed old payment could refund unrelated spend after a UTC rollover or explicit reset. Reservations now carry a generation.
- HTTP redirects could forward bearer credentials to a different origin. Cross-origin redirects are refused.
- IPv4-mapped IPv6 bypassed private-range checks. Connection-time validation also rejects non-global destinations and mixed DNS answers, and connects to the checked address without resolving it again. TLS retains the original hostname. Environment proxies are deliberately disabled on this sink.
- A malicious Retry-After value could request an unbounded or invalid sleep. Delays are finite, non-negative, and capped at 30 seconds.
- LangChain's real callback manager swallowed BudgetExceeded. The adapter now sets raise_error and run_inline. The regression failed through the installed callback manager before the fix.
- Old optional dependency floors allowed known vulnerable versions. LangChain, LangGraph and OpenTelemetry floors now match audited versions; CrewAI's floor advances while its unresolved upstream risk remains documented.
- The MCP npm dependency graph now audits with zero findings. CodeQL actions are updated to the reviewed pinned revision from the pending dependency PRs.

## Evidence

- Base SDK suite: 969 passed, one optional LangChain test skipped, 28 subtests, 91.50% coverage. `pytest-full.txt`.
- Installed LangChain 1.6.3, LangGraph 1.2.11 and OpenTelemetry 1.44.0: 107 integration/regression tests passed. CrewAI callback shape tests run without installing CrewAI. `extras-tests.txt`.
- HTTP hosted smoke: 7/7, including exact trace ID returned by the real dashboard. Provider response is mocked; HTTP ingest and retrieval are live. `hosted-smoke.txt`.
- TypeScript MCP: 10/10 tests; npm audit zero. Python local-budget MCP: 19/19 tests.
- Regression-before files preserve the reproduced failures. Windows default pytest temp cleanup failed on an existing host temp path; final runs use a dedicated worktree temp directory.

## Audited boundaries and limits

- Guard limits are in-process. BudgetGuard.consume accounts for reported usage, so the call crossing a cap is recorded; it does not undo provider charges. X402SpendGuard checks before its payment callback.
- Goal metering, tracing/async tracing, provider patches, serialization/reporting, generated onboarding, and persistence are covered by the full suite. Tests include concurrency, malformed inputs, cost/usage accounting, and offline CLI paths.
- SDK code uses the standard library. Optional extras have independent trees. Audit JSON files retain exact resolved versions.
- CrewAI 1.15.21 resolves ChromaDB 1.1.1. Four distinct upstream advisories remain with no fixed release: CVE-2026-45829, CVE-2026-45830, CVE-2026-45831, CVE-2026-45833 (one is duplicated by the scanner). Base SDK installs are unaffected. Avoid the extra without reviewing that exposure; this audit does not label it clean.
- Static model prices retain their actual last-verification date, 2026-05-19. We did not fabricate a new verification date. Prefer provider-reported cost or strict resolution for unlisted/changed prices.
- Local JSONL is an operational record, not cryptographic proof of execution. Signing alone would establish who signed bytes, not whether the claimed work happened.
- Persistence uses a local filesystem lock with stale-lock recovery; it is not distributed consensus. A network filesystem is not an audited deployment here.

Sign-off: OpenAI | GPT-6 | auto
