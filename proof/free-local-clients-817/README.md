Historical initial proof. Current source and review corrections: [review-r2](review-r2/README.md).

# Explicit free-client billing proof (#817)

The owner approved the prepared narrow per-client proposal on 2026-10-03.
The API adds runtime-only `free_local_clients` to sync/async OpenAI patches
and `init`. Exact named clients record local/zero cost; unnamed clients retain
paid estimates. No URL/model inference, new export, saved configuration,
mandatory dependency, provider request or package publication.

- Baseline: 1481 passed, 3 existing optional skips; 92.38% coverage.
- Initial API regression: 24 failed, 5 passed because the option was absent.
  Later cases expanded coverage; the initial raw result remains in red.txt.gz.
- Final focused: 47 passed. Real SDK transports cover mixed paid/local clients,
  sync/async Chat and Responses, streams, parse, raw responses, zero local
  JSONL/report/incident cost, retained paid estimates and refusal before send.
  Token/call caps, validation, weak lifetimes, idempotency, shutdown/repatch,
  zero-dollar reservations and interrupted token holds are covered.
- Full source: 1528 passed, 3 existing optional Agents skips, zero warnings,
  92.55% coverage. Complete source/baseline/regression logs are gzip-retained
  with checked roundtrips. No new optional skip belongs to the changed path.
- Fresh installed-wheel profiles: Windows/Python 3.9.6 with OpenAI 1.40.0
  (33 Chat-compatible cases; Responses explicitly deselected), Python 3.9.6
  with OpenAI 1.66.3 (47 cases), Python 3.13.2 with OpenAI 3.24.0 (47 cases).
  All profiles have zero skipped/error/failed cases or warnings. Every one of
  51 installed package files and METADATA equals the same wheel. Fresh venvs
  had no AgentGuard before installation; isolated Python and scrubbed provider
  environment exclude checkout/owner-provider leakage.
- All eight configured checks pass: ruff, bandit, docs, CI-tools, review
  readiness, release guard, PyPI README consistency, and MCP build/tests.
- New guide snippet parses; existing manual-example contract passes in the
  source suite. The candidate remains unpublished; published 1.4.0 needs its
  documented manual workaround.

The built wheel matches the staged Windows package bytes. source-binding.json
also compares each wheel module with the committed Git blob after Windows
checkout line-ending normalization; the source revision and hashes are saved.
Manifests hash Git-normalized UTF-8 LF text or exact gzip bytes. Showwork checks
saved artifacts; it does not by itself prove test adequacy or outside adoption.

In-memory and async non-stream calls retain recorded-budget preflight.
Store-backed sync non-stream calls and streams retain their existing boundaries.
Explicit free billing does not bypass exhausted recorded budgets or release an
interrupted stream's token/call hold. Token/call limits are needed to bound a
free loop; no provider invoice or hardware/electricity promise is made.
Sign-off: OpenAI | GPT-6 | auto.
