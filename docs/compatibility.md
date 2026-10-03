# Compatibility

Checked 2026-10-02 against AgentGuard `1.4.1` source. A row is **Supported**
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
| OpenAI Responses API, sync, async, and streamed (`patch_openai`, `patch_openai_async`) | Experimental | openai 1.66.3 (local spot-check) | `compat (latest)` runs the real client over a mocked transport: `create`, `stream()`, `with_streaming_response`, provider errors, and a store-backed `max_output_tokens` hold. [Installed candidate-wheel proof](../proof/responses-floor-20261002/README.md) exercises the same paths on Windows/Python 3.11 at 1.66.3 and 3.19.2. Not Supported yet: the automated floor, openai 1.40.0, predates Responses, so `compat (floor)` skips these tests. |
| OpenAI Agents SDK (`Runner.run`, `Runner.run_streamed`) | Experimental | openai-agents 0.0.3 (local spot-check) | `compat (latest)`: a real `Runner` with a looping function tool stops before the fourth model call, streamed and not, and `max_turns` still applies. The installed-wheel spot-check covers 0.0.3 and 0.22.3 with an explicit mocked model provider. Not in the automated floor lock. |
| Async and streamed Chat Completions and Anthropic calls | Supported | openai 1.40.0, anthropic 0.34.0 | `compat` runs eight real-client cases in `test_real_dispatch.py` at floor/current: sync streams, async create/streams and Anthropic `messages.stream`. Final usage bills once, completed holds settle and the second call is refused before HTTP dispatch. [Installed candidate-wheel proof](../proof/real-chat-stream-20261002/README.md) covers both pairs on Windows/Python 3.11. |
| CrewAI (`[crewai]`) | Experimental | crewai 1.15.21 | Not in the `compat` job. The extra resolves ChromaDB with unresolved advisories; see [#644](https://github.com/bmdhodl/agent47/issues/644) and the [CrewAI guide](integrations/crewai.md). |

The `compat` job runs on Ubuntu with Python 3.12 only. Optional extras are not
tested on Windows or macOS.
The dated Responses/Agents spot-check above is additional local Windows
evidence. It does not cover the other optional extras or satisfy the automated
floor/current support policy. The tested wheel is an unpublished 1.4.1 candidate;
published 1.4.0 does not include these Responses patches.

The published 1.4.0 wheel also has a dated [Windows reservation spot-check](../proof/windows-reservation-20261002/README.md)
on Python 3.11.9. Copied non-stream, stream and public-patch examples each ran
twice with two spawned processes sharing one local key: one simulated call
dispatched, one was refused, and no hold remained after normal completion.
The in-memory example still overshoots. These stand-ins verify local locking;
they do not add real-provider compatibility or promote the matrix rows.

The dated [real Chat/Anthropic stream and async check](../proof/real-chat-stream-20261002/README.md)
adds local Windows/Python 3.11 evidence using the same unpublished 1.4.1
candidate artifact. The existing compatibility jobs automatically run those
tests on Ubuntu/Python 3.12. This does not verify live provider billing or other
optional extras on Windows/macOS. Async non-stream calls still do not reserve.

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
