# OpenAI update review

Restored the two fixed compatibility floors and updated OpenAI to 3.22.1 in the current-version locks. A new regression first failed before Dependabot version-update exclusions were added. Focused tests and Ruff output are retained. Security updates remain enabled according to the official version-only option documentation linked in receipt.json. Hosted CI is a separate merge gate.

Verify: `python proof/dependency-review-834-r2/verify.py`.
