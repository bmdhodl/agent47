# Owner-approved AG-06 acceptance

The accepted architecture uses the existing init/patch APIs and the standard
OpenAIResponsesModel. The candidate is 2.0.0 and remains unpublished; stable
PyPI 1.4.0 does not provide this path. Fresh installed Windows/Python 3.11
minimum/current OpenAI and Agents SDK pairs run outside the checkout with real
SDK objects, fake counting transport, disabled vendor tracing and no paid calls.
Native max_turns remains effective; unsupported boundaries are documented in
docs/integrations/openai-responses.md and the enforcement map.

Both installed profiles passed 21 Responses/Agents cases without skips:
OpenAI 1.66.3 / Agents 0.0.3 and OpenAI 3.22.1 / Agents 0.22.3.
The actual example also ran outside the checkout against a loopback fake server
on each pair. Five requests recorded $0.06, tripping its $0.05 recorded-cost
budget; no sixth dispatch reached the server. This demonstrates the documented
in-flight overshoot rather than an invoice cap. No provider credentials or
paid calls were used.

Full source validation passed 1,480 tests with 91.30% coverage. Its 114 optional
provider skips are separate from the two no-skip installed acceptance suites.
Lint, security scanning, docs and release/tool/review guards passed. Initial
failed attempts are retained: the identity probe normalized only the checkout's
CRLF bytes, and the example had stale import-order/noqa lint defects. The probe
now compares exact installed/wheel/checkout bytes, and the example imports are
sorted before activation. Successful commands retain their own output.

receipt.json binds commands, actual version pairs, installed package/metadata
identity, zero mandatory runtime dependencies and exact source/test snapshots.
The private installation resolves allowed transitives normally; it does not
claim that the Linux CI locks are generic Windows locks. Gzipped logs and the
candidate wheel retain exact bytes. Hosted exact-head CI and independent PR
review remain separate merge gates. Internal dogfood and outside adoption are
separate; no Fluarmn or external-user success is inferred from these tests.

Run python proof/approved-responses-735/verify.py for artifact verification.
Its optional `traces.jsonl` argument verifies the retained source-test scratch
snapshot, not a file in the reviewer's checkout. The earlier scratch-file
existence claim is retracted and replaced by this portable artifact check.
OpenAI | GPT-6 | auto.
