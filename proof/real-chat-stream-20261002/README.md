# Real Chat and Anthropic stream/async compatibility, 2026-10-02

Eight additional real-provider SDK cases verify existing patches. The SDKs
parse mocked HTTP responses and SSE events through their normal request
pipelines. Each case uses a shared-store `max_calls=1` guard, records one
`llm.result` event and 15 tokens, and refuses before a second HTTP dispatch.
Completed streams settle one call and leave no reserved or unresolved hold.

Covered paths:

- OpenAI sync Chat stream, including injected `stream_options.include_usage`.
- OpenAI async Chat create and stream with a real `AsyncTracer`/file sink.
- Anthropic sync streamed `messages.create` and `messages.stream`; the latter
  uses the SDK's `text_stream` and `get_final_message` APIs.
- Anthropic async create, streamed create and stream helper, with a real
  async tracer/file sink and the helper's async final-message API.

| Profile | Real package versions | Installed candidate-wheel result |
|---|---|---|
| floor | openai 1.40.0, anthropic 0.34.0 | 8 passed, 0 skipped, 0 warnings, exit 0 |
| current | openai 3.19.2, anthropic 1.8.0 | 8 passed, 0 skipped, 0 warnings, exit 0 |

Both rows installed the same unpublished `agentguard47-1.4.1-py3-none-any.whl`,
SHA-256 `04b111624f9e91a4047f9932dc3c277ba7ddf015f7588414d5b3d3036869ef8d`.
This is the previously built candidate artifact; no SDK runtime changed.
Before reuse, its ZIP CRC, all 49 package source/type files against the current
checkout, version metadata and zero mandatory runtime dependencies were
checked again. The real provider versions come from the existing CI floor
inputs/current lock; their dependencies were resolved in each fresh local
environment and are recorded in the profile version lists.

Each profile ran on Windows/Python 3.11.9 in a fresh venv where AgentGuard was
absent before wheel installation. `direct_url.json` binds the installed archive
to the recorded wheel hash; the import origin was asserted to be in that
venv's `site-packages`. The test file was copied byte-for-byte outside the
checkout, with no source-inserting conftest. Executed command shape:

```text
python -I -m pytest test_installed_dispatch.py -k "chat_stream or chat_async or anthropic_stream or anthropic_async" -q --basetemp <fresh-directory>
```

The two `*-receipt.json` files retain artifact identity, Windows checkout-byte
test hashes and results. The `*-installed-tests.txt` files retain completed
pytest output. Plugin autoload was disabled and provider/owner credential
variables were removed from child environments. Public log copies replace
local paths, normalize LF and remove terminal trailing whitespace; raw local
output is retained separately.

## Scope and limits

This adds tests and documentation. No SDK runtime, public API, dependency
floor, workflow or release changes. OpenAI and Anthropic use their own HTTP
client implementations, including Anthropic 1.8's httpx2 transport. SDK clients
and stream managers are closed explicitly; async patches are restored by the
provider fixtures after each case.

No real provider request or paid call occurred. These cases prove the mocked
normal completion and exhausted-budget paths, not live provider billing,
crash recovery, every Python/OS pair or a provider invoice cap. Async
non-stream calls remain recorded-budget preflight, without reservations.
Existing stand-in tests continue to cover error, cancellation and missing-usage
boundaries. Responses/Agents stay Experimental pending the separate automatic
floor check; CrewAI stays subject to #644. Outside adoption remains unknown.

The separately executed source suite on Windows/Python 3.13.2 passed 1404
tests, with three optional Agents skips, zero warnings and 92.35% coverage
(`sdk-tests.txt`). Configured lint/security/docs/release guards and all 11 MCP
tests passed (`checks.md`). The existing floor/current hosted compatibility
jobs must pass before merging the matrix update.

Sign-off: OpenAI | GPT-6 | auto
