# Configured validation

Full source suite: 1416 passed, 3 optional Agents skips, zero warnings; coverage 92.41%. Installed profiles include the real Agents packages separately and have zero skips. Structural checks are included in the full suite. All 11 MCP tests passed.

These are retained results, not a claim that reading this file reruns the checks.

## ruff (exit 0)

```text
All checks passed!
```

## bandit (exit 0)

```text

```

## docs (exit 0)

```text
Documentation links and image alt text passed
```

## ci-tools (exit 0)

```text
[REVIEW_CHECKOUT]\.github\requirements\ci-tools.in direct pins support Python 3.9
```

## review-readiness (exit 0)

```text
Review readiness guard passed.
```

## release-guard (exit 0)

```text
Release guard passed.
```

## pypi-readme (exit 0)

```text

```

## mcp (exit 0)

```text

> @agentguard47/mcp-server@0.2.2 test
> npm run build && node --test dist/__tests__/*.test.js


> @agentguard47/mcp-server@0.2.2 build
> tsc

TAP version 13
# Subtest: client requires AGENTGUARD_API_KEY
ok 1 - client requires AGENTGUARD_API_KEY
  ---
  duration_ms: 1.0881
  ...
# Subtest: client trims base URL, encodes trace IDs, and sends bearer auth
ok 2 - client trims base URL, encodes trace IDs, and sends bearer auth
  ---
  duration_ms: 18.3625
  ...
# Subtest: isDecisionEvent recognizes decision lifecycle events
ok 3 - isDecisionEvent recognizes decision lifecycle events
  ---
  duration_ms: 0.6261
  ...
# Subtest: extractDecisionPayload normalizes trace and event fields
ok 4 - extractDecisionPayload normalizes trace and event fields
  ---
  duration_ms: 0.1259
  ...
# Subtest: extractDecisionEvents filters by workflow and trace
ok 5 - extractDecisionEvents filters by workflow and trace
  ---
  duration_ms: 0.2352
  ...
# Subtest: buildToolShape supports string, number, and boolean fields
ok 6 - buildToolShape supports string, number, and boolean fields
  ---
  duration_ms: 2.2002
  ...
# Subtest: query_traces exposes read-only annotations and agent-use guidance
ok 7 - query_traces exposes read-only annotations and agent-use guidance
  ---
  duration_ms: 1.4299
  ...
# Subtest: get_trace_decisions returns normalized decision payloads
ok 8 - get_trace_decisions returns normalized decision payloads
  ---
  duration_ms: 0.5455
  ...
# Subtest: check_budget returns warning status and cost summary
ok 9 - check_budget returns warning status and cost summary
  ---
  duration_ms: 0.4245
  ...
# Subtest: all tools expose object input schemas
ok 10 - all tools expose object input schemas
  ---
  duration_ms: 0.2503
  ...
# Subtest: published MCP tools are read-only and deny mutating budget names
ok 11 - published MCP tools are read-only and deny mutating budget names
  ---
  duration_ms: 0.7963
  ...
1..11
# tests 11
# suites 0
# pass 11
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 249.5563
```
