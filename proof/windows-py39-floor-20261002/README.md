# Windows/Python 3.9 provider-floor check

Checked October 2, 2026 for [AG-07 (#736)](https://github.com/bmdhodl/agent47/issues/736).
The SDK advertises Python 3.9 as its minimum. Earlier real-provider artifact
checks used Windows/Python 3.11, and compatibility CI uses Ubuntu/Python 3.12.
This adds a local installed-artifact check at the SDK's minimum Python version.

| Fresh Windows/Python 3.9.6 environment | Selected existing tests | Result |
|---|---|---|
| OpenAI 1.40.0 / Anthropic 0.34.0 | Sync Chat/Messages, stream helpers, async create/streams, and `agentguard run` | 12 passed, 16 deselected; zero skips/warnings |
| OpenAI 1.66.3 / Agents 0.0.3 | Responses create/parse/stream, async/raw responses, provider errors, store holds, looping Runner and native max turns | 13 passed, 15 deselected; zero skips/warnings |

Each environment installed providers from PyPI using binary wheels and
`pytest==8.4.2`, confirmed AgentGuard was absent, then installed the same
unpublished `agentguard47-1.4.1-py3-none-any.whl` with `--no-deps`.
The source test file was copied byte for byte outside the checkout, without
`conftest.py`. Tests ran with `python -I`, pytest plugin autoload disabled,
`AGENTGUARD_REQUIRE_REAL_DEPS=1`, and owner provider/telemetry credentials
removed from the child environment. All HTTP/SSE provider calls used the
existing mocked transports; no live provider request or billing is verified.

Artifact identity:

- Candidate wheel SHA-256: `04b111624f9e91a4047f9932dc3c277ba7ddf015f7588414d5b3d3036869ef8d`.
- ZIP CRC passed; all 49 package files match the checkout's SDK bytes.
- All 49 installed package files and installed wheel metadata match the archive.
- The wheel has zero mandatory runtime requirements.
- Copied test SHA-256: `2c43797afbb10d617f2b4a1b47ffe0a01f242af61c00a50fb6a1e0a35566bff5`.

The original driver expected `direct_url.json` to contain an archive hash.
These fresh environments use pip 21.1.3, which recorded an empty `archive_info`
for the local wheel. That driver stopped before executing tests. The completed
check compares installed package and metadata bytes against the wheel instead;
receipts retain `direct_url_archive_sha256_recorded: false`. No pip or SDK
upgrade was needed. Initial private setup/origin logs were retained.

Commands after installation and copying the existing
[`test_real_dispatch.py`](../../sdk/tests/test_real_dispatch.py) to
`test_installed_dispatch.py` outside the checkout:

```text
python -I -m pytest test_installed_dispatch.py -k "not responses and not agents_sdk and not langchain and not langgraph and not otel" -q --basetemp pytest
python -I -m pytest test_installed_dispatch.py -k "responses or agents_sdk" -q --basetemp pytest
```

Each command ran in its own environment. Deselected tests are outside that
profile; none of the selected cases skipped. Version lists, provider-install,
absence-before-install, wheel-install and raw test logs accompany both receipts.
Public copies replace machine paths with placeholders and omit credential values.

Current OpenAI 3.19.2, Anthropic 1.8.0 and Agents 0.22.3 package metadata
declares Python 3.10+. The [version-specific registry metadata](provider-python-metadata.json)
records the official source URLs and each floor/current requirement. This is
an upstream installability boundary, not a current-provider runtime test on
Python 3.9 or advice to pin an old provider silently.

Responses/Agents remain Experimental because recurring floor CI is missing.
The prepared workflow proposal remains unapplied pending owner authorization.
CrewAI stays subject to [#644](https://github.com/bmdhodl/agent47/issues/644).
The other optional extras and macOS were not checked here. The candidate is
unpublished; published 1.4.0 lacks these Responses patches. This does not prove
outside-user activation or complete #736.

Repository validation also passed: the current-source suite on Python 3.13.2
had 1404 passes, three optional Agents skips, no warnings and 92.33% coverage.
Configured lint/security/docs/metadata checks and all 11 MCP tests passed.
See [validation](checks.md) and the [source-suite output](sdk-tests.txt).

Sign-off: OpenAI | GPT-6 | auto
