# Final named-example proof for #817 documentation

Current example: `examples/local_cost_manual.py`. The guide's marked Python
block must match this file exactly. Tests execute the named Python file with
`runpy`; Markdown text is never executed. Other guide snippets cannot change
selection. The SDK runtime, public signatures and accounting policy are unchanged.

- Final full SDK: **1481 passed, 3 existing optional Agents skips, zero warnings,
  92.38% coverage**, 117.64 seconds. Complete normalized output is retained in
  `source-suite.txt.gz`; gzip roundtrip verified. This final run removes the
  earlier whitespace-only timing limit in the parent receipt.
- Final focused guide/file parity and accounting: **2 passed**. All three
  previously clean installed profiles pass both final tests again, zero
  skips/errors/warnings. Test, guide and example hashes bind each rerun.
- Candidate Windows/Python 3.9.6 and 3.13.2: all 49 installed package files and
  metadata still match the candidate wheel. Published 1.4.0/Python 3.13.2:
  every installed package file and metadata still match the verified PyPI wheel.
  These are rechecks of the earlier isolated installations, not fresh installs.
- One explicitly free response records 2,500 tokens and one call, writes
  zero model cost to JSONL/report/incident, and refuses the next preflight.
  The paired paid/unknown-provider case retains conservative cost. No model runs.
- Final ruff (including the example), docs, README and release checks pass;
  SDK code is unchanged from the earlier passing bandit/CI-tools/readiness/MCP
  checks in the parent folder. Historical logs and receipts remain intact.

The original guide's failed regression is in the parent folder. Earlier
review-r2 evidence is historical. Manifests hash Git-normalized text bytes
or the exact gzip bytes. Showwork verifies saved artifacts, not behavioral
test adequacy. #817 patch configuration and the owner API exception remain
open; this is no release, inference or outside-adoption claim.
Sign-off: OpenAI | GPT-6 | auto.
