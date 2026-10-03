# Responses/Agents minimum CI proof (#736)

Patrick approved the prepared separate minimum-version job on 2026-10-03.
It uses hash-pinned OpenAI 1.66.3 and Agents 0.0.3 on Ubuntu/Python 3.12,
preserves Chat's 1.40.0 floor/current matrix, and makes `responses-floor`
part of the required CI result inventory. The real Responses/Agents group
and all free-client tests must execute without skips. No mandatory SDK
dependency, runtime API or release change.

- Required-result regression: 32 failed / 17 passed against the old gate.
  Updated inventory: 49 passed, zero skips/errors/failures.
- Full SDK: 1583 passed, 3 existing optional Agents skips, zero warnings,
  92.56% coverage. Full output/JUnit are gzip-retained with roundtrips.
- The actual workflow's extracted JUnit validator passes 16 cases covering
  both result positions: success, skip, failure, error, empty, malformed,
  invalid count and missing file. Both test groups must contain clean tests.
- YAML parses; existing triggers, permissions and compat job stay identical;
  required group names match the aggregate inventory. Floor installs enforce
  the committed hashes. All eight configured checks pass, including 11 MCP
  tests. Source hashes come directly from committed Git blobs.
- Packaged SDK modules remain identical to main; prior installed-wheel
  evidence at free-local-clients-817/review-r3 still binds that runtime.

Actual hosted CI passed at c3985a4: Ubuntu/Python 3.12.14 ran 21 real
Responses/Agents tests and 71 free-client tests, both with zero skips, failures,
errors or warnings. All nine CI jobs, including floor/current compatibility
and the required aggregate, passed. hosted-ci.json binds the actual run to
identical committed source; hosted-floor.log.gz retains exact test-step output.
The original local-only receipt is preserved in README.local.md. Final-head
checks must still pass before merge. Provider/model calls use offline transports.

The matrix describes the 1.4.1 source candidate, which remains unpublished;
published 1.4.0 lacks the Responses patches. #736 remains open for CrewAI/#644
and parent release/adoption gates. Artifact verification does not certify test
adequacy or external adoption.
Sign-off: OpenAI | GPT-6 | auto.
