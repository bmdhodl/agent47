# Existing OpenAI clients: issue #816

**Initial candidate, superseded by [review revision](review-r2/README.md).**
These isolated runs passed, but full compatibility-floor CI subsequently failed
six cases after SDK module replacement in earlier tests. The revision retains
the cached-export regression and proof for the final reconciled implementation.

This is a Windows spot-check of the unpublished `agentguard47` 1.4.1 candidate,
checked on 2026-10-02. The fix patches standard shared OpenAI resource methods,
so ordinary clients and resources created before activation trace usage and
refuse the next request once the recorded budget is exhausted.

The real provider SDKs use mocked HTTP transports. No provider request, local
model inference, or billable model call runs. This is repository-side evidence,
not outside-user adoption or a published-release result.

The regressions cover sync/async Chat Completions and Responses, public `init`,
patch idempotency, shared budgets across earlier/later clients, and restoration
by `unpatch`. Previously saved bound methods, raw/streaming helpers, and custom
instance overrides remain outside the shared-method contract; recreate saved
references after activation. Anthropic activation order is unchanged.

The same copied test file ran outside the checkout with isolated Python, no
repository `conftest.py`, pytest plugin autoload disabled, and owner provider
credentials removed from the child environment. The baseline wheel produced
12 expected failures (zero errors/skips); the new installed wheel passes them.

| Installed profile (Python 3.11.9) | Versions | Result |
| --- | --- | --- |
| Chat/Anthropic floor | OpenAI 1.40.0, Anthropic 0.34.0 | 18 passed, 22 deselected, zero skips/warnings |
| Responses/Agents floor | OpenAI 1.66.3, Anthropic 0.34.0, Agents 0.0.3 | 37 passed, 3 deselected, zero skips/warnings |
| Current | OpenAI 3.19.2, Anthropic 1.8.0, Agents 0.22.3 | 37 passed, 3 deselected, zero skips/warnings |

Floor selection excludes APIs absent from OpenAI 1.40.0 and the three unrelated
framework cases. The other profiles exclude only those framework cases. The
full provider selection also reruns Responses parsing, raw/streaming helpers,
stream settlement, provider errors, the CLI runner, and the Agents tool loop.

Candidate wheel SHA-256:
`4ae7716e6570c04202b151c03ee3027d4a065d41e1403a1b97abde2a88bcf0af`.
Baseline candidate SHA-256:
`04b111624f9e91a4047f9932dc3c277ba7ddf015f7588414d5b3d3036869ef8d`.
Executed test bytes SHA-256:
`ca7e241f6c7653047dc7dc6ef956c9370b6473a86f4bb9a50bd1de94b9c282e4`.

Each new profile verifies ZIP integrity, all 49 package files against the
checkout, absence before wheel installation, all 49 installed files and
installed metadata against the archive, installed provenance/hash, and zero
mandatory runtime dependencies. The receipt records exact versions and JUnit
counts; `versions.txt` retains the resolved optional environment.

Raw outputs are retained locally. Public copies replace machine paths with
`[REVIEW_CHECKOUT]`, `[PROFILE_ENV]`, or `[CANDIDATE_WHEEL]`; test names, failures,
counts, timings and hashes remain intact. See the per-profile receipts/logs
and [configured checks](checks.md).

These results do not prove live model billing, every custom client, captured
callables before activation, outside-user demand, or a released fix. The
Responses/Agents rows remain Experimental until recurring floor CI is approved
and executed. Existing historical proof folders describe their earlier wheel.
