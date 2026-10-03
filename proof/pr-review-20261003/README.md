# AgentGuard review and main readbacks (2026-10-03)

- #830 merged at bb96510: actual Python 3.10 tool-lock regeneration retains
  Python 3.9 support. Final PR CI and all main code/scanner workflows pass.
  Actual generated graph run 37136759166 submits all six CI manifests with
  HTTP 204 on the merge revision. See ../graph-runtime-lock-827/README.md.
  #827 is closed after that actual readback.
- #828 merged at d67c060: verified CodeQL SARIF uploader 4.38.2. Updated-head
  PR checks and main checks pass. Run 37137236385 actually executes the new
  SHA and reports `Successfully uploaded results`.
- #829 merged at 0376b58: verified Trustabl action 0.4.3, including 0.4.2.
  Source/bundle installer URLs follow the same upstream repository's rename.
  Engine v0.1.6, rules v0.2.0, permissions, telemetry and completion checks
  remain. Updated-head PR checks and main checks pass. Run 37137439731 executes
  the new SHA; scan findings are advisory and the completion wrapper passes.
- #831 remains open at 9b39701: pytest 9.0.3 requires Python >=3.10 and breaks
  the required 3.9 runner. The direct-pin guard and a fresh Python 3.9.6 pip
  install both reject it, exit 1; hosted test/lint/aggregate fail. Formal review
  requests changes. No patched pytest 8.x release exists on live PyPI today;
  latest 8.x remains 8.4.2. The upstream advisory's first patched version is
  9.0.3. No support-floor change or advisory dismissal was authorized or made.
  Copilot independently confirms the same P1 blocker; other compatibility
  jobs on Python 3.12 do not repair the failed shared 3.9 tools install.

Both dependency action tags were resolved through their annotated tag objects
to the exact commit pins. Copilot reported no blockers for #828/#829 and the
final #830 source/proof; Bugbot explicitly skipped. All real comments on the
merged PRs were fixed or answered, with zero unresolved inline threads. Original
Codex proof findings were reproduced, corrected and resolved. All 28 original
manifest entries match exact Git blobs; the original final export verifies
35/35 artifact checks. Hosted evidence is subsequently added under its own gate.

`merged-prs.json` binds final PR heads, main commits and actual workflow runs.
Complete changed-action and failed pytest CI logs are gzip retained.
`pytest831-held.json` binds actual metadata, advisory, candidate source, local
rejections and hosted failures. `source.json` binds committed source hashes.
Hashes establish retained-output integrity; quiet success logs are not tests
by themselves. No SDK release or outside-user/adoption claim is made.

Sources: [pytest advisory](https://github.com/advisories/GHSA-6w46-j5rx-g56g),
[pytest 9.0.3](https://pypi.org/project/pytest/9.0.3/),
[CodeQL release](https://github.com/github/codeql-action/releases/tag/v4.38.2),
[Trustabl tag](https://github.com/trustabl/trustabl-action/tree/v0.4.3).

Sign-off: OpenAI | GPT-6 | auto.
