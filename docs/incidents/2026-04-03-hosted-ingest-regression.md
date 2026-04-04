# Hosted Ingest Regression RCA

Date: 2026-04-03

## Summary

The SDK shipped a hosted-ingest incompatibility that surfaced as `400 No valid events`
responses from `https://app.agentguard47.com/api/ingest` while some traces still
appeared in the dashboard live stream.

The hotfix in `v1.2.6` corrected the runtime behavior. This incident write-up captures
why the regression shipped and what now prevents a repeat.

## What Happened

- `Tracer` emits a local watermark as the first event in a new trace with `kind="meta"`.
- Hosted ingest only accepts trace records with `kind/type` of `span` or `event`.
- The pre-hotfix `HttpSink` forwarded trace events verbatim, so hosted ingest could see:
  - a first-line watermark record with `kind="meta"`, and/or
  - a payload missing the hosted `type` alias that the validator expects.
- That produced first-batch `400` responses even though later valid trace events could
  still show up in the dashboard, which made the failure mode look inconsistent from the
  outside.

## Root Cause

The real root cause was contract drift between the public SDK and hosted ingest.

1. The SDK treated the HTTP sink as a raw transport and did not normalize events for the
   hosted ingest contract.
2. The local ingest test harness did not faithfully model hosted ingest behavior:
   - it did not require the hosted `type` alias
   - it returned `200` even when a batch contained zero valid events
   - it therefore did not fail on the exact first-batch behavior that production rejected
3. The manual dashboard smoke test only checked whether `/api/v1/traces` returned
   anything, not whether the exact trace written by the current run was present.

## Why We Missed It

### 1. Mock drift hid the contract break

The repo's local ingest server validated a simplified schema. It was close enough for
happy-path coverage, but not close enough to catch the production break.

### 2. Release proof was too weak

The smoke script asked "does the traces endpoint return data?" instead of
"did the exact trace from this run survive ingest validation?" That allowed false
confidence if old traces existed or if only later batches succeeded.

### 3. Tag publish could outrun release validation

The tag-based publish workflow built and uploaded to PyPI without rerunning SDK tests.
CI ran separately, which meant a direct tag push could publish before a regression was
fully revalidated.

### 4. Local test runs were vulnerable to import shadowing

This machine had an editable `agentguard47` install from another checkout. Without
forcing pytest to import the SDK from the current repo, ad hoc local verification could
accidentally exercise the wrong code.

## Corrective Actions Shipped

- `sdk/agentguard/sinks/http.py`
  - drops non-ingest records like the watermark before POSTing
  - mirrors supported trace kinds into both `kind` and `type`
- `sdk/tests/conftest.py`
  - now mirrors hosted ingest more closely
  - returns `400` on zero-valid-event batches
  - records request-level failures for assertions
  - forces pytest imports to resolve from this checkout
- `sdk/tests/test_hosted_ingest_contract.py`
  - adds a direct hosted-contract regression suite
  - proves watermark-only batches fail
  - proves `HttpSink` only posts hosted-compatible trace records
- `sdk/tests/test_integration_cost_guardrail.py`
  - now verifies a specific trace id through `/api/v1/traces?trace_id=...`
  - fails if any ingest request is rejected
- `sdk/tests/integration_dashboard.py`
  - now writes a deterministic probe trace and verifies that exact trace id against the
    hosted API
- `.github/workflows/publish.yml`
  - now reruns SDK lint, bandit, and the full test suite before publishing to PyPI
- `ops/04-DEFINITION_OF_DONE.md`
  - now requires trace-id-scoped hosted smoke proof when the SDK/dashboard ingest
    contract changes

## Preventive Standard Going Forward

For any future `HttpSink`, tracing, or ingest-contract change:

1. The mock contract in `sdk/tests/conftest.py` must be updated first.
2. A regression test must fail against the old behavior before the fix is accepted.
3. Release proof must include a trace-id-scoped hosted lookup, not a broad endpoint
   health check.
4. Tag-based publish must remain blocked on SDK test success.

## Remaining Risk

The hosted dashboard is private, so the public repo still cannot enforce the server-side
schema directly. The mitigation is to keep the local contract harness aligned with the
real ingest validator and to preserve the real hosted smoke step in release proof.
