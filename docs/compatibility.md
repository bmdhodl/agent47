# Compatibility

Checked 2026-09-26 against AgentGuard `1.4.1` source. A row is **Supported**
only when a CI job runs the real package, not a stand-in. Enforcement
semantics for each path are in the [enforcement boundary](enforcement-boundary.md).

## Matrix

| Surface | Status | Oldest tested | Evidence |
|---|---|---|---|
| Base SDK, no extras | Supported | Python 3.9 | `ci.yml` `test` on Python 3.9 and 3.12 (3.9–3.12 on `main`). `published-wheel.yml` installs the PyPI wheel on Windows, macOS, and Linux and checks that it requires no packages. |
| OpenAI Chat Completions, sync (`patch_openai`) | Supported | openai 1.40.0 | `ci.yml` `compat` runs `sdk/tests/test_real_dispatch.py` with the real SDK client over a mocked HTTP transport. The second call is refused before dispatch, and a store-backed guard dispatches once. |
| Anthropic Messages, sync (`patch_anthropic`) | Supported | anthropic 0.34.0 | Same job and file. The second call is refused before dispatch. |
| LangChain callbacks (`[langchain]`) | Supported, Python 3.10+ | langchain-core 1.6.3 | `compat` job: a real `CallbackManager` propagates `BudgetExceeded`. |
| LangGraph nodes (`[langgraph]`) | Supported, Python 3.10+ | langgraph 1.2.11, langgraph-checkpoint 4.2.0, langgraph-sdk 0.4.4 | `compat` job: a real `StateGraph` stops at the node budget. |
| OpenTelemetry sink (`[otel]`) | Supported | opentelemetry-api 1.44.0, opentelemetry-sdk 1.44.0 | `compat` job: spans and events reach a real in-memory exporter. |
| OpenAI Responses API, sync, async, and streamed (`patch_openai`, `patch_openai_async`) | Experimental | openai 3.19.2 | `compat (latest)` runs the real client over a mocked transport: `create`, `stream()`, `with_streaming_response`, provider errors, and a store-backed `max_output_tokens` hold. Not Supported yet: the floor, openai 1.40.0, predates the Responses API (1.66), so `compat (floor)` skips these tests. |
| OpenAI Agents SDK (`Runner.run`, `Runner.run_streamed`) | Experimental | openai-agents 0.22.3 | `compat (latest)`: a real `Runner` with a looping function tool stops before the fourth model call, streamed and not, and `max_turns` still applies. Not in the floor lock. |
| Async and streamed Chat Completions and Anthropic calls | Tested with stand-ins only | n/a | Unit tests in `test_instrument_stream.py`, `test_async_patches.py`, and `test_reservation_stream.py` use stand-in clients, not the real SDK request pipeline. |
| CrewAI (`[crewai]`) | Experimental | crewai 1.15.21 | Not in the `compat` job. The extra resolves ChromaDB with unresolved advisories; see [#644](https://github.com/bmdhodl/agent47/issues/644) and the [CrewAI guide](integrations/crewai.md). |

The `compat` job runs on Ubuntu with Python 3.12 only. Optional extras are not
tested on Windows or macOS.

## How versions are chosen

- **Oldest tested** comes from
  [`compat-floor.in`](../.github/requirements/compat-floor.in). Framework floors
  must equal the extras in [`sdk/pyproject.toml`](../sdk/pyproject.toml); a CI
  guardrail test fails if they drift. Provider floors are the oldest releases
  verified against the real patch path.
- **Current** comes from
  [`compat-latest.txt`](../.github/requirements/compat-latest.txt), a
  hash-pinned lock that Dependabot refreshes weekly. A red `compat (latest)`
  job on that pull request means an upstream release broke a supported path.
  Fix it, or move the row down, before merging.

## Support policy

- A row stays **Supported** while its `compat` job is green at both the floor
  and current versions.
- If an upstream release breaks a row and no fix ships within one AgentGuard
  release, the row moves to **Experimental** here and in the changelog. It is
  never kept Supported by pinning users to an old version silently.
- A new framework or provider enters as **Experimental** until it has a
  real-package test in `test_real_dispatch.py` and a row in both locks.
- Raising a floor is a changelog entry. Base installs never gain a runtime
  dependency.
