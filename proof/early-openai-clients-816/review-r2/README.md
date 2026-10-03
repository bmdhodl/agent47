# Review revision: cached resource exports

The initial isolated candidate profiles passed, but the full Linux compatibility
floor CI run failed six existing-client cases. Earlier stand-in tests removed
the OpenAI root module while resource submodules stayed cached. OpenAI 1.40.0
then re-imported without its `resources` re-export, and activation fell back to
constructor wrapping. This revision imports the canonical Chat resource module
when the export is absent, preserving coverage for existing clients.

The regression file now includes 16 cases, with explicit sync/async tests for
both present and absent resource exports. This folder supersedes the initial
candidate as the completed #816 proof; the parent logs retain that earlier
artifact and its narrower results. Copilot independently implemented the same
module-lookup fix in `d17a16e`; that commit is preserved in the branch history.
The final implementation has one lookup path and also permits a genuinely
absent legacy `openai.resources` namespace, while dependency errors propagate.

| Installed profile on Windows/Python 3.11.9 | Result |
| --- | --- |
| OpenAI 1.40.0 / Anthropic 0.34.0 | 20 passed, 24 deselected, zero skips/warnings |
| OpenAI 1.66.3 / Anthropic 0.34.0 / Agents 0.0.3 | 41 passed, 3 deselected, zero skips/warnings |
| OpenAI 3.19.2 / Anthropic 1.8.0 / Agents 0.22.3 | 41 passed, 3 deselected, zero skips/warnings |

The previous installed candidate produces **16 expected failures**, with zero
errors/skips, on the same regression file. A focused order repro produced six
failures before the fix and **121 passed** afterward. That focused run used the
local floor environment; full Linux floor CI is a separate required check on
the final PR head before merge.

Final candidate SHA-256:
`24817796814f57b6d08ece52a27921b839a90e49bfbb6b9ee906741cbef2afdd`.
Baseline SHA-256:
`04b111624f9e91a4047f9932dc3c277ba7ddf015f7588414d5b3d3036869ef8d`.
Executed Windows test bytes SHA-256:
`3e7a670967737d9c70872ef662630853ac2c64546955b9c35270b26b196130a2`.

Each profile starts without AgentGuard, installs this wheel without dependency
resolution, then verifies its origin/hash, ZIP integrity, all 49 package files
against the checkout and installed archive bytes, installed metadata bytes,
and zero mandatory runtime requirements. JUnit checks reject failures, errors,
skips and an unexpected case count. The copied tests run outside the checkout,
without repository `conftest.py`, with isolated Python, pytest plugin autoload
disabled, and owner provider credentials scrubbed. Real SDKs use mock HTTP;
no model request, local inference or billing runs.

Reproduction commands in a throwaway environment with the profile's exact
provider versions (see each `versions.txt`):

```text
python -m pip wheel ./sdk --no-deps --wheel-dir <artifact-dir>
python -I -m pip --isolated install --no-deps <candidate-wheel>
python -I -m pytest test_installed_dispatch.py -q --junitxml installed-tests.xml -k "not langchain and not langgraph and not otel"
```

The Chat/Anthropic floor additionally selects `and not responses and not
agents_sdk`. The baseline selects `existing_client or existing_async_client
or existing_openai_client` against the previous wheel. `sdk-tests.txt` and
[configured checks](checks.md) retain the full source validation. Public copies
replace machine paths with placeholders while preserving test names, counts,
failures, timings and hashes; raw originals remain local.

Saved bound methods/raw/streaming helpers and custom instance overrides remain
outside the contract; recreate saved references after activation. Anthropic
activation order is unchanged. This is an unpublished candidate and local
repository evidence, not live billing or outside-user adoption. Responses and
Agents remain Experimental.
