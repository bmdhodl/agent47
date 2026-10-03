# Current review proof for #817 / PR #825

This supersedes the parent initial proof and review-r2 for current source. Copilot follow-up found inconsistent cost provenance: six completed/interrupted capped stream cases failed the added zero-source assertion before the fix. They now label known free model cost zero while retaining unresolved usage and holds.
Claude review found missing zero-cost accounting for completed stored streams
without usage, plus unsupported SDK owner layouts. Eight regressions failed
before the fix; all now pass. Codex review found that stored zero-cost holds
could bypass an already exhausted dollar budget. Six dispatch regressions
failed before the atomic settled-exhaustion check; all now refuse before HTTP.

- Focused real-SDK tests: 71 passed.
- Full source SDK: 1552 passed, 3 existing optional Agents skips, zero warnings,
  92.54% coverage. Full raw output and JUnit retained.
- Eight configured checks all pass, including bandit and 11 MCP tests.
- Reinstalled current wheel in previously verified fresh Windows profiles:
  Python 3.9.6 / OpenAI 1.40.0: 49 Chat-compatible passes;
  Python 3.9.6 / OpenAI 1.66.3: 71 passes;
  Python 3.13.2 / OpenAI 3.24.0: 71 passes.
  All have zero skips, failures, errors or warnings. The 1.40 profile explicitly
  deselects Responses/raw cases. The 3.13 profile was freshly recreated during
  review after its earlier environment executable was missing; these results
  come from the verified replacement, then current-wheel reinstallation.
- All 51 installed modules and METADATA equal the single saved wheel.
  Each wheel module matches the source commit's direct Git blob after explicit
  Windows checkout line-ending normalization. No mandatory SDK dependency.

The fix rejects new reservations after settled dollar exhaustion inside the
existing store transaction; existing reservation retry identity stays intact.
Free requests may still reserve zero dollars while budget remains. Missing
usage stays unknown and retains existing unresolved token/call holds, with
known zero model cost in the event. Unsupported client ownership fails before
activation. No live provider/model requests or outside-user adoption evidence.

The 1.4.1 candidate remains unpublished. Paid clients keep existing estimates;
token/call caps are needed to bound a free loop. No invoice/hardware-cost claim.
Artifact checks and saved hashes bind evidence; they do not certify adequacy.
Sign-off: OpenAI | GPT-6 | auto.
