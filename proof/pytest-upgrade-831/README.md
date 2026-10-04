# PR #831: approved pytest upgrade, Windows lock repair

The owner approved original PR head `9b39701fadee4c30fc9cbd907fc7fb0a4537ef51`
on October 3, 2026 at 22:35:08 UTC. Its Python 3.9 install and required-result
checks still fail: pytest 9.0.3 requires Python 3.10 or newer. The existing
Python 3.9 support policy is unchanged while the owner chooses that policy.
This packet does not claim that the PR is ready to merge.

A fresh Windows/Python 3.10 check also found a separate lock defect: the PR
dropped `colorama`, which is required on Windows. The original hash-enforced
install refused that unpinned dependency. The failure and command are retained.

The existing Python 3.10.11 / pip-tools 7.6.1 compiler regenerated the lock
without upgrading packages. All 21 original package pins and hash sets remain;
the generated `colorama==0.4.6` entry restores its two official PyPI hashes.
Neither workflow nor SDK support floor changed in this repair.

A second fresh Windows/Python 3.10.11 environment installed the repaired lock
with hash enforcement. `pip check` passed. The unchanged SDK source suite,
using pytest 9.0.3, passed **1,473 tests**, with **114 optional-provider skips**,
zero failures/errors/warnings and **91.30% coverage**. Providers were absent
from this CI-tools-only environment; the skips are not framework compatibility
proof. This is source-suite evidence, not an installed SDK or publication claim.

The tested SDK Git tree equals main `45c4d54824319888abe67e3e437c38294c92a306`;
the test checkout included the PR plus that main's existing changes at
`27c31c11499fc49f2418dc8235561fd97971cd5e`.

Ruff, Bandit, docs, review-readiness, release metadata, PyPI README and MCP
checks passed. Direct pins pass the Python 3.10 guard. The current default
Python 3.9 guard still rejects pytest 9.0.3, as it should. Its exit 1 is
retained explicitly and is not represented as green CI.

The packet contains raw compressed output, actual commands, JUnit, compiler
receipt, original/repaired locks and [summary.json](summary.json). Run:

```powershell
python proof/pytest-upgrade-831/verify.py
py -3.10 -m venv .venv-pytest9
.venv-pytest9\Scripts\python.exe -m pip install --require-hashes -r .github/requirements/ci-tools.txt
.venv-pytest9\Scripts\python.exe -m pytest sdk/tests/ --cov=agentguard --cov-fail-under=80
```

The manifest binds committed LF text; the verifier also accepts the equivalent
UTF-8 CRLF checkout. Compressed log/XML bytes remain exact. Python optimization
is not used for this proof procedure.

Sign-off: OpenAI | GPT-6 | auto
