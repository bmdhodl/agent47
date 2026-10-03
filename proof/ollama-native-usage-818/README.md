# Native Ollama usage: issue #818

Windows, 2026-10-02, unpublished AgentGuard 1.4.1 candidate. The existing
manual billing helpers now read native `prompt_eval_count` / `eval_count`
fields from dictionaries and attribute-based response objects. Cached prompt
counts remain a subset of input; they do not increase the total twice.

Fixtures use the documented [chat](https://docs.ollama.com/api/chat) and
[generate](https://docs.ollama.com/api/generate) response shapes. These are
offline fixtures, not newly captured inference or outside-user activation.

## Verification

- Previous #821 wheel: 15 expected regression failures, 3 passes, 0 errors or
  skips. The same 18 cases pass on the fixed wheel on Windows/Python 3.9.6
  and 3.13.2, with 0 skips or warnings. See each profile's installed-tests.txt
  and receipt.json. The crossing call records 2,500 tokens before raising on
  the 1,000-token cap; subsequent checks refuse another call.
- Tests cover chat/generate, dicts/attributes, zero and partial counts,
  nested OpenAI usage precedence, cached prompt subsets, paid unknown-model
  fallback, a stream chunk without usage, and explicit caller-owned JSONL.
  The trace retains 2,500 tokens and the CLI report counts one free result.
  `consume_billable` itself returns a record and logs consumption; it does
  not automatically write a trace.
- Both clean virtual environments install the candidate without dependencies,
  copy tests outside the checkout without its conftest, disable pytest plugin
  autoload and run isolated Python. Optional provider packages are absent.
  All 49 installed package files and metadata equal the exact wheel; archive
  CRC and all 49 candidate source files were also checked. Py3.9's bundled
  pip records an empty archive_info: its receipt explicitly says the installer
  did not record a digest. The archive SHA and installed-byte checks still ran.
- Full SDK: 1,438 passed, 3 existing optional Agents skips, 0 warnings,
  92.39% coverage. Ruff, Bandit, docs, CI-tools/review-readiness/release
  guards and generated PyPI README pass. MCP: 11 tests pass. Logs and exit
  results are retained under checks/; ruff-final.txt checks the final test file.

Candidate wheel SHA-256: `193d5d5cd5ff75222d89e6d29953d510608f44acd499b3e4a8ea96512eb38188`.
Previous #821 wheel SHA-256:
`24817796814f57b6d08ece52a27921b839a90e49bfbb6b9ee906741cbef2afdd`.
Executed Windows test-file bytes SHA-256: `3dbe16e5879eea7657dfab62358c69ea99880dee47bf747109bd62deafbe5f60`. Git archives
normalize this checkout's line endings, so archived test bytes can differ.
Public logs replace checkout/validation paths with neutral labels. Raw local
logs are retained privately. Showwork checks certify these saved artifacts;
they do not rerun the behavioral suite.

## Scope

No Ollama client interception, pricing inference, new public API, dependency,
workflow, or release tag is added. Manual `consume_billable` records usage
after a request; callers must check before the next request and account for
native streams once at their final usage payload. `free_local` remains an
explicit existing caller choice. Local patch configuration #817 is separate.
