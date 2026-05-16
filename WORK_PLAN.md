# WORK_PLAN — Narrow OtelTraceSink enhancement

## Problem statement
The roadmap Later bucket sanctions enhancing the existing `OtelTraceSink` so it
supports custom resource attributes and span links, without pulling AgentGuard
toward a broad observability product. This task adds those two capabilities
inside the existing sink only — no new exporter module, no new dependency.

## Approach
- `OtelTraceSink.__init__` gains an optional `resource_attributes` dict. Entries
  are coerced to strings and stamped onto every span this sink emits, prefixed
  `agentguard.resource.*`. Per-span attribute prefixing is the API-compatible
  way to surface resource-level context without owning the TracerProvider's
  OTel `Resource` (which would push the sink into provider-setup territory).
- Span links: a span-start event may carry a `links` list of
  `{"span_id": ..., "attributes": {...}}` entries. On span start, links that
  reference an already-tracked AgentGuard span are converted to OTel `Link`
  objects via the span's `get_span_context()` and passed to `start_span(links=)`.
  Links to unknown/malformed entries are skipped.

## Files touched
- `sdk/agentguard/sinks/otel.py` — implementation + docstrings.
- `sdk/tests/test_otel_sink.py` — fake OTel `Link`, fake span context, new tests.

## What "done" looks like
- [x] `resource_attributes` constructor arg, backward-compatible (defaults None).
- [x] Resource attrs stamped on every span; non-string values coerced.
- [x] `links` on span-start produce OTel `Link` objects to tracked spans.
- [x] Malformed/unknown links skipped without crashing.
- [x] All 9 original tests still pass; new tests cover both features.
- [x] No new dependencies; core SDK stays zero-dep.

## Risks / assumptions
- Assumes OTel `Link` is importable from `opentelemetry.trace` (it is, since
  opentelemetry-api 1.x) — guarded behind the existing `_HAS_OTEL` try/except.
- Assumes `start_span` accepts a `links` kwarg (it does in opentelemetry-api).
- Span links only resolve to spans this sink currently tracks; cross-process
  links are out of scope (and out of the narrow mandate).
