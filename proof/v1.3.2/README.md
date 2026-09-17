# AgentGuard 1.3.2: streamed usage billed once

Selected after 1.3.1 left streaming totals uncounted. The patches already
stopped exhausted-budget retries before dispatch. Streamed OpenAI and
Anthropic calls still billed from the stream object, which has no usage
until the last chunk. Closing that hole protects the existing budget
promise. It is not a new guard family.

## Behavior and scope

OpenAI and Anthropic sync/async patches wrap `stream=True` responses and
bill the final usage payload once. Anthropic `messages.stream()` is
included. OpenAI streaming requests set `stream_options.include_usage=True`
when the caller did not set `include_usage`. An explicit `False` is left
unchanged. A stream that ends without usage counts as one dispatched call
with zero tokens and zero cost. Exhausted budgets still refuse the request
before dispatch.

This does not reserve concurrent capacity, predict a response's cost, or
preflight goal-level caps. Mid-stream abort without a usage payload cannot
recover tokens from partial text. Provider-internal retries remain inside
the provider library.

## Evidence

- Same mocked stream, three chunks, 200 tokens of final usage:
  1.3.1 recorded 0 tokens. 1.3.2 recorded 200 tokens and one consume.
  See previous-demo.json and candidate-demo.json. Command:
  `PYTHONPATH=sdk python examples/streaming_usage_demo.py`.
- Full suite: 1019 passed, one optional skip, 90.55% coverage. Command:
  `PYTHONPATH=sdk python -m pytest sdk/tests/ -q --tb=short --cov=agentguard --cov-report=term --cov-fail-under=80`.
  Exit 0. See pytest.txt.
- Stream tests cover OpenAI/Anthropic sync and async create(stream=True),
  Anthropic messages.stream(), include_usage injection, empty streams, and
  exhausted-budget preflight. See sdk/tests/test_instrument_stream.py.
- Pinned Ruff and Bandit pass. Release guard passes. MCP npm test: 10
  passed. See lint.txt, bandit.json, release-guard.txt, mcp-test.txt.
- The image's visible text matches image-copy.txt after whitespace
  normalization. Browser overflow checks passed at 375, 768, and 1440
  pixels: document scrollWidth equals clientWidth. See browser-checks.json
  and demo-375.png / demo-768.png / demo-1440.png.
- The HDR plate is a generated atmosphere still with no labels. Measured
  numbers are browser-rendered on top of that plate in demo.html.
- Defluff 0.1.2 scanned LinkedIn, X, image text, and alt text separately:
  all scored 0.0. Adjacent receipts include exact input hashes. This
  detects writing patterns, not authorship or image provenance.

The tag, PyPI publish, and live LinkedIn/X posts are outside this
candidate. Do not treat these files as a publication receipt.

Agent sign-off (provider | model | reasoning tier): Cursor | Grok 4.6 | auto
