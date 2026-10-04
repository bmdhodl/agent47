# Compatibility

Checked 2026-10-03 against AgentGuard `2.0.0` candidate source. A row is **Supported**
only when a CI job runs the real package, not a stand-in. Enforcement
semantics for each path are in the [enforcement boundary](enforcement-boundary.md).

The candidate retires Python 3.9/3.10 and moves the SDK to a major release.
Published 1.4.0 and the dated 1.4.1 candidate receipts below keep their original
support and artifact identity. See [migration](guides/python-311-migration.md).

## Matrix

| Surface | Status | Oldest tested | Evidence |
|---|---|---|---|
| Base SDK, no extras | Supported | Python 3.11 | `ci.yml` `test` on Python 3.11 and 3.12 on PRs and `main`. `published-wheel.yml` installs the PyPI wheel on Windows, macOS, and Linux and checks that it requires no packages. |
| OpenAI Chat Completions, sync (`patch_openai`) | Supported | openai 1.40.0 | `ci.yml` `compat` runs `sdk/tests/test_real_dispatch.py` with the real SDK client over a mocked HTTP transport. The second call is refused before dispatch, and a store-backed guard dispatches once. |
| Anthropic Messages, sync (`patch_anthropic`) | Supported | anthropic 0.34.0 | Same job and file. The second call is refused before dispatch. |
| LangChain callbacks (`[langchain]`) | Supported, Python 3.11+ | langchain-core 1.6.3 | `compat` job: a real `CallbackManager` propagates `BudgetExceeded`. |
| LangGraph nodes (`[langgraph]`) | Supported, Python 3.11+ | langgraph 1.2.11, langgraph-checkpoint 4.2.0, langgraph-sdk 0.4.4 | `compat` job: a real `StateGraph` stops at the node budget. |
| OpenTelemetry sink (`[otel]`) | Supported | opentelemetry-api 1.44.0, opentelemetry-sdk 1.44.0 | `compat` job: spans and events reach a real in-memory exporter. |
| OpenAI Responses API, sync, async, and streamed (`patch_openai`, `patch_openai_async`) | Supported in the 2.0.0 candidate | openai 1.66.3 | `responses-floor` and `compat (latest)` run the real client over a mocked transport: `create`, `stream()`, `with_streaming_response`, provider errors, and a store-backed `max_output_tokens` hold. The floor job rejects skips and also runs the explicit free-client tests. [CI proof](../proof/responses-floor-ci-736/README.md); [additional installed Windows proof](../proof/responses-floor-20261002/README.md). Chat's separate 1.40.0 floor remains unchanged. |
| OpenAI Agents SDK (`Runner.run`, `Runner.run_streamed`) | Supported in the 2.0.0 candidate | openai-agents 0.0.3 | `responses-floor` and `compat (latest)`: a real `Runner` with a looping function tool stops before the fourth model call, streamed and not, and `max_turns` still applies. The floor job rejects skips. [CI proof](../proof/responses-floor-ci-736/README.md); installed-wheel spot-check covers 0.0.3 and 0.22.3 with an explicit mocked model provider. |
| Async and streamed Chat Completions and Anthropic calls | Supported | openai 1.40.0, anthropic 0.34.0 | `compat` runs eight real-client cases in `test_real_dispatch.py` at floor/current: sync streams, async create/streams and Anthropic `messages.stream`. Final usage bills once, completed holds settle and the second call is refused before HTTP dispatch. [Installed candidate-wheel proof](../proof/real-chat-stream-20261002/README.md) covers both pairs on Windows/Python 3.11. |
| CrewAI (`[crewai]`) | Experimental | crewai 1.15.21 | Not in the `compat` job. The extra resolves ChromaDB with unresolved advisories; see [#644](https://github.com/bmdhodl/agent47/issues/644) and the [CrewAI guide](integrations/crewai.md). |

The `compat` and `responses-floor` jobs run on Ubuntu with Python 3.12 only.
Other optional extras have no Windows or macOS CI coverage.
The dated Responses/Agents spot-check above is additional local Windows
evidence. A separate [installed-framework check](../proof/windows-frameworks-736/README.md)
on 2026-10-03 adds three cases each for LangChain, LangGraph, and OpenTelemetry
at the minimum versions on Windows/Python 3.10.11 and current locked versions
on Windows/Python 3.13.2. Each profile passed all three cases without skips or
warnings using the unchanged 1.4.1 candidate wheel. The current Ubuntu lock
needed a proof-only hash-pinned `pywin32` supplement for MCP's Windows dependency;
it is not a standalone Windows lock. These local results do not add macOS or
Windows CI coverage. The separate required
`responses-floor` job supplies automated minimum-version evidence; `compat
(latest)` supplies current-version evidence. The tested wheel is an unpublished 1.4.1 candidate;
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

An additional [Windows/Python 3.9.6 floor check](../proof/windows-py39-floor-20261002/README.md)
uses the same installed candidate wheel: 12 Chat/Anthropic cases at OpenAI
1.40.0 / Anthropic 0.34.0 and 13 Responses/Agents cases at OpenAI 1.66.3 /
Agents 0.0.3 passed without skips or warnings. This remains local floor evidence;
automated floor evidence now comes from `responses-floor`. That earlier candidate's base SDK support for
Python 3.9 did not establish current-provider installability: OpenAI 3.19.2,
Anthropic 1.8.0 and Agents 0.22.3 declare Python 3.10+ in their package metadata.
Current-provider CI remains on Python 3.12.

The [existing-client regression check](../proof/early-openai-clients-816/review-r2/README.md)
uses a new candidate wheel containing the #816 fix. On Windows/Python 3.11,
20 provider cases passed at the Chat/Anthropic floor, and 41 passed at both the
Responses/Agents floor and current versions. This includes activation after
client construction, cached resource exports, and restoration by `unpatch`. Saved callables/helpers
remain outside the activation contract. These are local results; the existing
CI jobs run the added regressions without changing the support classifications.

## How versions are chosen

- **Oldest tested** comes from
  [`compat-floor.in`](../.github/requirements/compat-floor.in). Framework floors
  must equal the extras in [`sdk/pyproject.toml`](../sdk/pyproject.toml); a CI
  guardrail test fails if they drift. Provider floors are the oldest releases
  verified against the real patch path. Responses/Agents use the separate
  [`compat-responses-floor.in`](../.github/requirements/compat-responses-floor.in)
  lock so their minimum does not raise Chat's 1.40.0 floor.
- **Current** comes from
  [`compat-latest.txt`](../.github/requirements/compat-latest.txt), a
  hash-pinned lock that Dependabot refreshes weekly. A red `compat (latest)`
  job on that pull request means an upstream release broke a supported path.
  Fix it, or move the row down, before merging.

## Support policy

- A row stays **Supported** while its real-package minimum job (`compat
  (floor)` or `responses-floor`) and `compat (latest)` are green. The required
  aggregate rejects failed, cancelled, skipped or missing job groups. The
  Responses floor separately rejects skipped, empty or failing test results.
- If an upstream release breaks a row and no fix ships within one AgentGuard
  release, the row moves to **Experimental** here and in the changelog. It is
  never kept Supported by pinning users to an old version silently.
- A new framework or provider enters as **Experimental** until it has a
  real-package test in `test_real_dispatch.py` and a row in its minimum and
  current locks.
- Raising a floor is a changelog entry. Base installs never gain a runtime
  dependency.
