# Repository checks

Executed in the isolated review checkout, 2026-10-02. Every command below
exited 0. This file summarizes the captured command output; it is not a raw
terminal transcript.

- `python scripts/check_docs.py --repository agent47`: documentation links
  and image alt text passed.
- `python scripts/sdk_release_guard.py`: release guard passed.
- `python scripts/review_readiness_guard.py`: review readiness guard passed.
- `python scripts/generate_pypi_readme.py --check`: generated metadata matched.
- `python scripts/ci_tools_requirements_guard.py`: direct pins support Python 3.9.
- The exact Ruff file list in `make lint`: all checks passed.
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`: configured
  SDK scan passed; no exclusions changed.
- `npm --prefix mcp-server test`: TypeScript build and all 11 tests passed.
- The proof receipt's eight public stdout hashes and parsed payloads matched
  their files; example byte hashes matched the unchanged Windows checkout.
- Public proof copies contained no local user or checkout paths.

Codex review found relative checkout node paths in the initial SDK log.
The public copy was regenerated from retained raw output with those prefixes
redacted. All proof files were then checked again for local user paths and the
checkout basename; the example stdout hashes still matched. No runtime or
test behavior changed, so the same completed suite output remains the evidence.

The full SDK suite and architecture assertions are recorded separately in
`sdk-tests.txt` (Windows/Python 3.13.2). Published 1.4.0 example results are in the eight named example
logs and `receipt.json`; the SDK suite tests the current 1.4.1 source candidate.
Those published-wheel examples used Windows/Python 3.11.9.
