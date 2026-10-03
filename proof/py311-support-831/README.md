# PR831: Python 3.11 support and pytest 9

The owner accepted Python 3.11 as the minimum on 2026-10-03 after Python 3.10
reached end of life. The next SDK candidate is 2.0.0 because dropping
Python 3.9/3.10 is breaking. Published 1.4.0 remains unchanged.

This packet supersedes the pending support decision in `proof/pytest-upgrade-831`.
That earlier packet is an immutable receipt from df3f7e3 before this decision.
It must not be read as the current support policy.

- Real Windows/Python 3.11.9 compiler, pip-tools 7.6.1: all 19 retained tool
  versions and hash sets preserved; three obsolete backports removed. Windows
  colorama remains hash-pinned. Original and compiled locks are retained.
- Two new regression tests first failed on the old floor/CI contract. The first
  full run exposed a separate old 3.9 assertion in the published-wheel test.
  After updating that contract assertion, 1,475 source tests passed, 114
  optional-provider cases skipped, zero failures/errors/warnings, 91.36% coverage.
- Ruff, Bandit, Python-floor guard, README/release sync, review-readiness, docs,
  and TypeScript MCP checks passed. Actual command arguments, exit codes,
  UTC bounds and untouched raw output are compressed with their receipts.
- The included 2.0.0 wheel requires Python >=3.11 and has no mandatory runtime
  dependencies. Its actual 3.11 install passes version, doctor, demo, report,
  raw quickstart and generated starter. Fresh real Python 3.9.6 and 3.10.11
  installs reject it. Pip 24's --python-version dry run did not reject a local
  wheel; that unsuccessful simulation is retained and excluded from this claim.
- Playwright CLI checked the four changed static pages at 375/768/1440: all
  12 version-label/overflow checks passed. The repository has no root pnpm
  test:e2e script; this was a localhost static preview. Screenshots and the
  raw browser result are retained. Historical receipt output keeps its 1.4.1 identity.

Run `python proof/py311-support-831/verify.py` from any checkout. Known UTF-8
text normalizes CRLF to LF; gzip, screenshots and the wheel remain byte-exact.
`source-hashes.json` binds the tested changes and is checked against committed
Git blobs during closeout. The verifier checks only retained dated artifacts,
so future source changes do not rewrite this proof.

This is candidate/source/installed-wheel proof. It is not publication,
real provider billing, external adoption or hosted CI proof. Hosted CI is
verified separately before merge. No release tag was created.
