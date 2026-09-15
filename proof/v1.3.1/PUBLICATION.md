# AgentGuard 1.3.1 publication receipt

Published and verified on 2026-09-14 America/Chicago (2026-09-15 UTC).

- Release: https://github.com/bmdhodl/agent47/releases/tag/v1.3.1
- PyPI: https://pypi.org/project/agentguard47/1.3.1/
- Publish workflow: https://github.com/bmdhodl/agent47/actions/runs/34921927131
- Release commit: 19a6761d94c23b2231f72483e92749251693c5d6 (PR 721).
- LinkedIn: https://www.linkedin.com/feed/update/urn:li:share:7505451968731987968/
- X: https://x.com/phughes9000/status/2099689675032056208

## Public package verification

A fresh Python 3.12.13 environment installed agentguard47==1.3.1 from PyPI
with uv --no-cache. It resolved one package, with no base runtime dependencies.
The installed module came from site-packages. All eight CLI/quickstart paths
passed in a temporary directory; see public-smoke.json.

The installed-version regression demo made three attempts against a mocked
provider with a one-call budget. Exactly one request reached the mock and both
retries raised BudgetExceeded before dispatch. Recorded calls remained one;
no network calls were made. See public-demo.json. The comparison against
PyPI 1.3.0 remains in previous-demo.json.

The wheel downloaded from the PyPI metadata URL passed `gh attestation verify
sdk/dist/agentguard47-1.3.1-py3-none-any.whl --repo bmdhodl/agent47`.
The verified workflow is .github/workflows/publish.yml at refs/tags/v1.3.1,
bound to the release commit above. Its SHA-256 is
1d68ca7e137781213839cb74cc204a84ea6b734c294ebfd9aca9fcbe562e3d0b.
See pypi.json and attestation.json for the metadata and verification result.

## Review and delivery

PR 721 passed Python 3.9/3.12 CI, lint, MCP checks, documentation consistency,
CodeQL, Bugbot, and the Cursor security review. Codex's source-version memory
finding was fixed. Claude's documentation/audit findings were addressed;
hypothetical silent store failures and future fields were declined with the
store contract and reset/rollover regressions cited. Copilot could not review
because its account quota was exhausted. The full review disposition is on
the PR. The regenerated implementation audit verified 17/17 claims.

The published LinkedIn body contains every scanned paragraph. X's published
body contains the scanned copy and its image has the scanned alt text. Both
permanent posts were opened and the attached graphic visually checked.
Published text receipts and screenshots are adjacent to this file.
LinkedIn's alt-text editor crashed; the image was published successfully
without custom alt text. No duplicate post was submitted.

Defluff 0.1.2 scored LinkedIn copy, X copy, image text, and alt text 0.0, with
zero flagged spans. Input SHA-256 values are in the four scan receipts. The
release notes also scored 0.0. This scans writing patterns; it does not prove
human authorship. The graphic is the browser-rendered comparison of measured
mock-provider results, not an image-model illustration.

## Limits retained

Recorded usage is checked before dispatch. There is no concurrent reservation,
predicted response-cost guarantee, streaming usage accounting, or goal-level
preflight. File-backed checks and consumption perform synchronous local I/O
even in an async provider patch. Optional CrewAI/ChromaDB issue 644 remains
open. Signup capture alone does not establish activation or paying demand.

Agent sign-off: OpenAI | GPT-6 | auto
