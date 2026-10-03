# Responses and Agents compatibility spot-check, 2026-10-02

Related work: #736 and the existing Experimental paths from #786. This fixes compatibility-test selection and isolation; no SDK runtime, public export, dependency floor, workflow, release tag or support promotion changed.

## Reproduction and correction

At main `2258413bc2ce6d63ea249ea2673a925c81b6b00e`, the Responses fixture checked `OpenAI.responses` on the class. OpenAI 1.66.3 creates this resource on each instance. The baseline selected 12 tests and skipped all 12 (`floor-baseline.txt`); exit 0 was no compatibility proof.

The fixture now uses a small capability probe that closes an instance with a fake key and an explicit SDK HTTP client. Two regression cases verify both an instance-only resource and an absent resource. Before the fix: 1 failed, 1 skipped. After the fix: 2 passed. The regression calls the capability probe directly, without pytest fixture internals, and fails if the resource is misreported.

Once that skip was removed, early Agents 0.0.3 eagerly created its default provider even when the agent had an explicit model. With owner credentials removed, three tests failed at provider construction. Both Runner variants and the native-turn test now receive an explicit `RunConfig` backed by the same mock HTTP client. No default provider credential or network connection is required.

## Installed artifact results

Both fresh Windows/Python 3.11 environments installed the **same** unpublished `agentguard47-1.4.1-py3-none-any.whl`. SHA-256: `04b111624f9e91a4047f9932dc3c277ba7ddf015f7588414d5b3d3036869ef8d`.

`candidate-wheel-check.json` confirms archive CRC integrity, byte-for-byte equality of all 49 package source/type files against the checkout, version 1.4.1, and zero mandatory runtime requirements.

Review required a clean repeat because the original version lists came from before a forced wheel reinstall. The final environments assert that AgentGuard is absent before installing the wheel. Tests run outside the repository with `python -I`, without its source-inserting conftest. The installed `direct_url.json` must name the wheel and its archive SHA-256 must equal the recorded artifact hash. The import origin must be in the environment's `site-packages`. The receipts also retain the executed test-copy hash (Windows checkout bytes), counts and exit status. The original 12-case logs remain as earlier-run evidence; they are superseded by the clean logs below.

| Pair | Result | Evidence |
|---|---|---|
| openai 1.66.3 / openai-agents 0.0.3 | 13 passed, 0 skipped, exit 0 | `floor-clean-installed.txt`, `floor-receipt.json`, `floor-clean-versions.txt` |
| openai 3.19.2 / openai-agents 0.22.3 | 13 passed, 0 skipped, exit 0 | `current-clean-installed.txt`, `current-receipt.json`, `current-clean-versions.txt` |

Executed shape in each environment:

```text
python -I -m pip --isolated install --no-deps <candidate-wheel>
python -I -m pytest <outside-checkout>/test_installed_dispatch.py -k "responses or agents_sdk" -q --basetemp <fresh-test-directory>
```

Real SDKs used fake HTTP transports; Agents tracing was disabled. Provider and owner credential variables were removed from child environments. No real provider request or paid call occurred. Local user/checkout paths in captured text were replaced with placeholders; terminal trailing spaces were stripped. The raw local logs remain separate from these public copies.

The wheel was built once for the completed checks and reused. An initial concurrent attempt to build two wheels in the same source tree collided in setuptools' build directory; that failed local attempt is not a compatibility failure. The completed installed tests use the single recorded artifact.

The extra case uses a real `AsyncTracer` and `JsonlFileSink`: one async Responses call writes one `llm.result` event with the expected cost and accounts for 15 tokens. No unawaited-coroutine warning occurs in either isolated run. `AsyncTraceContext.event` is synchronous by design. This verifies the production tracer/file-sink path, not arbitrary custom tracers.

The full-suite warning was reproduced as test pollution: the "provider not installed" unit tests removed modules from the cache, then reimported installed providers and patched their real constructors with mock tracers. Two new assertions failed before the correction. `patch.dict(sys.modules, {"openai": None})` and its Anthropic equivalent now simulate missing dependencies without importing or patching installed clients. The final full suite has zero warnings; no warning filter or timeout change was applied.

## Existing checks and limits

- Final full SDK suite: **1396 passed, 3 optional Agents skips, zero warnings, 92.33% coverage**, exit 0 (`sdk-tests-clean.txt`). The original pre-review run remains in `sdk-tests.txt`. The two clean artifact environments cover the three optional Agents cases.
- Final dispatch/isolation group: 29 passed, 3 optional Agents skips, zero warnings. All three changed test files passed Ruff. Configured SDK security scan, docs/generated-README checks and release guard passed.
- This is a local spot-check, not a supported-floor promise, OS-wide optional-extra certification, published release or external-user evidence. Both rows stay **Experimental** until automatic floor/current checks cover them. The Chat Completions floor remains 1.40.0.
- CrewAI remains subject to #644; no advisory exception or support promotion was applied.

Sign-off: OpenAI | GPT-6 | auto
