# Windows tool lock repair

Original zipp 4.1.0 lock fails an actual Python 3.11.9 Windows hash-checked install because colorama was omitted. After an explicit cross-platform pin and genuine pip-tools 7.6.1 regeneration, the same environment installs successfully and pip check passes. Full source suite: 1477 passed, 114 optional-provider skips, 91.36% coverage. CI lint scope plus the changed test and the live direct-pin floor guard pass. The broader diagnostic lint failure in existing tests is retained and explicitly outside acceptance; no tests or CI gates were skipped. All 18 original lock pins/hashes are preserved; only colorama is restored.

Verify with `python proof/dependency-review-835/verify.py`. Hosted CI and merge readback are separate.

Review clarification: `ruff-ci` and `floor-guard` ran from `C:\Users\patri\Documents\GitHub\agent47-review-20261002`, the same repository working directory as the source suite. Their original receipt entries omitted `cwd`; those historical entries and their hashes are preserved. The broader test-file lint failure is disclosed above and was not included in the CI lint target before or after this PR.
