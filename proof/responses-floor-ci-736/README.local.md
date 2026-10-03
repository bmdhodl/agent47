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

Actual Linux execution is pending hosted PR CI; merge requires that job and
the existing current-version job to pass. No Linux success is claimed before
that run. Later hosted receipts will be appended here, preserving these local
results. All provider/model calls in the selected tests use offline transports.

The matrix describes the 1.4.1 source candidate, which remains unpublished;
published 1.4.0 lacks the Responses patches. #736 remains open for CrewAI/#644
and parent release/adoption gates. Artifact verification does not certify test
adequacy or external adoption.
Sign-off: OpenAI | GPT-6 | auto.
