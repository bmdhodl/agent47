# Local-cost documentation correction for #817

The former comparison example activated a patch without recording a local call.
Its copy promised equal dollar enforcement for paid and free endpoints. The new
offline example uses existing manual `consume_billable(..., free_local=True)`;
no SDK runtime or public signature changes. #817 remains open for patch configuration.

- Valid regression: old guide **1 failed, 1 passed**; corrected guide **2 passed**.
- Clean installed 1.4.1 candidate: Windows/Python 3.9.6 and 3.13.2, **2 cases each**,
  zero skips/errors/warnings. All 49 package files and metadata equal the wheel;
  wheel bytes equal unchanged SDK source. SHA-256 `3671cd33312a4c8dcffec8db8a4459a175ebe5cc9b16c0074c23d1c1aa3ba009`.
- Clean published 1.4.0: Windows/Python 3.13.2, **2 cases**, zero skips/errors/warnings.
  PyPI's wheel digest and every installed package file and metadata were verified.
- All three profiles run actual `report` and `incident`: one 2,500-token call,
  zero model cost. The next manual preflight refuses dispatch at the call cap.
  Paid/unknown-provider pricing remains conservative. No model request runs.
- Full SDK **1481 passed, 3 existing optional Agents skips, zero warnings, 92.36% coverage**.
  A test import-spacing fix happened during that run; final installed tests use
  the formatted test. Initial lint failure and final successful rerun are retained.
  Other configured checks pass, including 11 MCP tests. `source-suite.txt.gz`
  retains the full path-normalized output; gzip roundtrip verified.
- Vercel's official overview, budgets, BYOK and pricing pages were read on
  2026-10-03. Corrected local-hosting, soft-cap and BYOK claims link to those
  sources in the guide. Removed unsupported zero-overhead and deployment-stat claims.

Validation uses isolated Python with pytest plugin autoload disabled, provider
environment removed, tests/docs copied outside the checkout, and no optional
provider SDKs. Raw private logs are retained; committed paths are normalized.
This proves the documented manual path, not the unfixed local patch's billing,
real provider inference, outside adoption, or a PyPI release. Native Ollama
token-field support is explicitly labeled as the unpublished 1.4.1 candidate.
Sign-off: OpenAI | GPT-6 | auto.
