# Python support closeout (2026-10-04 UTC)

PR #831 merged as `26c4ebc` after the owner-approved Python 3.11 minimum.
All nine main CI jobs passed at that exact merge. Actionlint, CodeQL, docs,
scanner and Scorecard also passed. Ordinary canonical Windows checkout
verified all 56 retained artifacts and 39 source hashes; unrelated tmp/ is preserved.

Copilot reviewed d37e9cc with no blockers, Claude findings were answered with
normalization/publication-gate evidence, Bugbot explicitly skipped for account
mismatch, and the original review thread was resolved. The optional Trustabl
app check is recorded with its actual state in receipt.json; it is not required.

The SDK candidate is 2.0.0, requiring Python >=3.11. Published PyPI/GitHub
release remains 1.4.0. No tag or publication was performed. Dependabot then
opened #834/#835/#836; these are separate review work, not part of this receipt.

Sign-off: OpenAI | GPT-6 | auto.
