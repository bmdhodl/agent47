# Responses and Agents compatibility spot-check, 2026-10-02

Related work: #736 and the existing Experimental paths from #786. This fixes compatibility-test selection and isolation; no SDK runtime, public export, dependency floor, workflow, release tag or support promotion changed.

## Reproduction and correction

At main `2258413bc2ce6d63ea249ea2673a925c81b6b00e`, the Responses fixture checked `OpenAI.responses` on the class. OpenAI 1.66.3 creates this resource on each instance. The baseline selected 12 tests and skipped all 12 (`floor-baseline.txt`); exit 0 was no compatibility proof.

The fixture now probes and closes an instance with a fake key and an explicit SDK HTTP client, as the dispatch tests do. Two regression cases verify both an instance-only resource and an absent resource. Before the fix: 1 failed, 1 skipped. After the fix: 2 passed. The successful case now explicitly fails if the fixture skips it.

Once that skip was removed, early Agents 0.0.3 eagerly created its default provider even when the agent had an explicit model. With owner credentials removed, three tests failed at provider construction. Both Runner variants and the native-turn test now receive an explicit `RunConfig` backed by the same mock HTTP client. No default provider credential or network connection is required.

## Installed artifact results

Both fresh Windows/Python 3.11 environments installed the **same** unpublished `agentguard47-1.4.1-py3-none-any.whl`. SHA-256: `04b111624f9e91a4047f9932dc3c277ba7ddf015f7588414d5b3d3036869ef8d`.

`candidate-wheel-check.json` confirms archive CRC integrity, byte-for-byte equality of all 49 package source/type files against the checkout, version 1.4.1, and zero mandatory runtime requirements.

The tests were copied outside the repository and run with `python -I`, without the repository conftest that inserts the source checkout. The import origin was asserted to be the virtual environment's `site-packages`. The receipts retain the SHA-256 of the executed test copy (Windows checkout bytes), artifact hash, import location, selected/pass/skip counts and exit status. Version files retain each resolved environment.

| Pair | Result | Evidence |
|---|---|---|
| openai 1.66.3 / openai-agents 0.0.3 | 12 passed, 0 skipped, exit 0 | `floor-installed.txt`, `floor-receipt.json`, `floor-versions.txt` |
| openai 3.19.2 / openai-agents 0.22.3 | 12 passed, 0 skipped, exit 0 | `current-installed.txt`, `current-receipt.json`, `current-versions.txt` |

Executed shape in each environment:

```text
python -I -m pip --isolated install --no-deps <candidate-wheel>
python -I -m pytest <outside-checkout>/test_installed_dispatch.py -k "responses or agents_sdk" -q --basetemp <fresh-test-directory>
```

Real SDKs used fake HTTP transports; Agents tracing was disabled. Provider and owner credential variables were removed from child environments. No real provider request or paid call occurred. Local user/checkout paths in captured text were replaced with placeholders; terminal trailing spaces were stripped. The raw local logs remain separate from these public copies.

The wheel was built once for the completed checks and reused. An initial concurrent attempt to build two wheels in the same source tree collided in setuptools' build directory; that failed local attempt is not a compatibility failure. The completed installed tests use the single recorded artifact.

## Existing checks and limits

- Full SDK suite: **1395 passed, 3 optional Agents skips, 3 existing async-mock warnings, 92.33% coverage**, exit 0 (`sdk-tests.txt`). The two fresh artifact environments cover the three optional Agents cases.
- Changed-file preflight: 18 passed, 3 optional Agents skips; both changed test files passed Ruff. Configured SDK security scan and release guard passed.
- This is a local spot-check, not a supported-floor promise, OS-wide optional-extra certification, published release or external-user evidence. Both rows stay **Experimental** until automatic floor/current checks cover them. The Chat Completions floor remains 1.40.0.
- CrewAI remains subject to #644; no advisory exception or support promotion was applied.

Sign-off: OpenAI | GPT-6 | auto
