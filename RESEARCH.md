# RESEARCH — OtelTraceSink enhancement

## Verified facts
- `opentelemetry.trace.Link` exists in opentelemetry-api 1.x and takes
  `(context: SpanContext, attributes: dict)`. Imported alongside the existing
  `SpanKind`/`StatusCode` import, guarded by `_HAS_OTEL`.
- `Tracer.start_span(...)` accepts a `links` kwarg (list of `Link`). The fake
  tracer in `tests/test_otel_sink.py` was extended to accept it.
- `Span.get_span_context()` returns the `SpanContext` a `Link` needs.
- Existing sink stores OTel spans by `span_id` in `self._spans` (otel.py:80).
  Span links reuse that same registry — link targets must already be tracked.
- The repo lint path targets production code, so the 4 pre-existing F401 unused
  imports in `test_otel_sink.py` are not CI-checked and are out of scope for
  this task. The production file `agentguard/sinks/otel.py` passes `ruff check`
  cleanly.
- Roadmap `ops/03-ROADMAP_NOW_NEXT_LATER.md:76` explicitly lists this exact
  Later item: "OtelTraceSink supports custom resource attributes and span links
  without pulling the SDK toward generic observability positioning."

## Decisions
- Resource attributes are stamped as per-span attributes (`agentguard.resource.*`)
  rather than constructing an OTel `Resource`, because the `Resource` belongs to
  the `TracerProvider` the caller owns — the sink does not create the provider.
- All values coerced to `str` to avoid OTel attribute-type validation failures
  when a caller passes ints/bools.

## Test evidence
- `python -m pytest tests/test_otel_sink.py -q` → 20 passed.
- `python -m pytest tests/ -q` → 752 passed (no regressions).
- `python -m ruff check agentguard/sinks/otel.py` → All checks passed.
