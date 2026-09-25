# AgentGuard 1.3.2 publication receipt

Published and verified on 2026-09-18 UTC.

- Release: https://github.com/bmdhodl/agent47/releases/tag/v1.3.2
- PyPI: https://pypi.org/project/agentguard47/1.3.2/
- Publish workflow: https://github.com/bmdhodl/agent47/actions/runs/35360428803
- Release commit: 72b060f7137c0c2219b78c36814bdbabaf10cfe0 (PR 725 squash).
- Tag: annotated `v1.3.2` -> `72b060f^{}`.
- LinkedIn / X: prepared, not posted from this environment (no create-post API).
  Compose links and scanned copy are in `compose-urls.txt`, `linkedin.txt`, and
  `x.txt`. Attach `demo-1440.png`.

## Public package verification

A fresh Python 3.12.3 virtualenv installed the PyPI wheel
`agentguard47-1.3.2-py3-none-any.whl` with `--no-deps`. `pip show` reports
`Requires:` empty. The import path is site-packages, not this checkout. All
eight CLI/quickstart paths passed in a temporary directory; see
`public-smoke.json`.

The installed-version streaming demo made one mocked `stream=True` call with a
final 200-token usage chunk. Recorded calls remained one; recorded tokens were
200; `include_usage` was injected. No network calls were made. See
`public-demo.json`. The 1.3.1 comparison remains in `previous-demo.json`
(0 tokens, 1 call).

The wheel downloaded from the PyPI metadata URL passed
`gh attestation verify agentguard47-1.3.2-py3-none-any.whl --repo bmdhodl/agent47`.
The verified workflow is `.github/workflows/publish.yml` at `refs/tags/v1.3.2`,
bound to the release commit above. Wheel SHA-256 is
`03b3b876bf97b55a4e8c68b8c115c554c4d3497b30d48b51b236d5d8a8dd17f3`.
See `pypi.json` and `attestation.json`.

## Review and delivery

PR 725 passed Python 3.9/3.12 CI, lint, MCP checks, documentation consistency,
CodeQL, and the Cursor security review. Codex P1/P2 notes on `34872e1` (split
Anthropic usage, iterator protocol, span errors) were fixed in `90fb6d7` and
landed in the squash. Claude PR Review, Copilot, and Bugbot were quota-blocked.
The required GitHub approving review was supplied by the repository admin on
merge. The red `claude-review` check was an out-of-usage CLI failure, not a
product-test failure.

Defluff 0.1.2 scored LinkedIn copy, X copy, image text, and alt text 0.0 after
the release URL was substituted, with zero flagged spans. Input SHA-256 values
are in the four scan receipts. This scans writing patterns; it does not prove
human authorship. The graphic is the browser-rendered comparison of measured
mock-provider results, not an image-model illustration.

## Limits retained

Recorded usage is checked before dispatch. Streams bill the provider's final
usage payload once. There is no concurrent reservation, predicted response-cost
guarantee, or goal-level preflight. Mid-stream abort without a usage payload
cannot recover tokens from partial text. File-backed checks and consumption
perform synchronous local I/O even in an async provider patch. Optional
CrewAI/ChromaDB issue 644 remains open. Signup capture alone does not establish
activation or paying demand.

The `email` job from PR 726 was not in the `v1.3.2` tag tree, so the
release-content run on the tag only executed `announce`. This identity cannot
`workflow_dispatch` (`403`). Re-run [Release Content](https://github.com/bmdhodl/agent47/actions/workflows/release-content.yml)
with `tag=v1.3.2` from current `main` to send the subscriber email. Retry with
the same tag, never a new campaign key.

Agent sign-off: Cursor | Grok 4.6 | auto
