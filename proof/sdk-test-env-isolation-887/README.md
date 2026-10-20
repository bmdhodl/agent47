# SDK test environment isolation (#887)

Each SDK test now starts without ambient `AGENTGUARD_*` runtime settings.
The CI harness sentinel `AGENTGUARD_REQUIRE_REAL_DEPS` is preserved so absent
provider dependencies cannot become silent skips. Tests can still set explicit
values, and pytest's monkeypatch fixture restores the original environment
afterward. Production SDK code is unchanged.

## Reproduction

Before the fixture changed, synthetic service/key/trace settings reproduced
the reported failures in `test_init.py` and `test_runner.py`: **9 failed,
59 passed**. The new subprocess regression also failed before the change:
its child suite reported two failed isolation probes and one passed explicit
setting probe.

The subprocess regression loads the actual shared conftest source in a scratch
suite. It checks that inherited and unknown future `AGENTGUARD_*` settings
are absent, `AGENTGUARDIAN` remains intact, an explicit per-test setting works,
and the next test starts clean. It uses synthetic values and a 30-second
timeout. Existing SDK environment-behavior tests remain in the full suite.

## Validation

Both full runs used the checkout SDK on Python 3.13.2, the native 80% coverage
floor, and separate absolute scratch directories:

| Environment | Command | Result |
|---|---|---|
| No ambient AgentGuard settings | `python -m pytest sdk/tests/ -q -p pytest_cov --cov=agentguard --cov-report=term-missing --cov-fail-under=80` | 1689 passed / 3 skipped; 92.70% coverage |
| Synthetic service, key, trace file, URL and unknown future setting | Same command | 1689 passed / 3 skipped; 92.65% coverage |

The three skips require the optional Agents package, absent in this local
environment. Focused synthetic-environment run, including real dispatch:
**111 passed / 3 optional skips**. Structural:
**9 passed**. MCP TypeScript build and tests: **11 passed**. Native Ruff,
Bandit, CI-tool pins, review-readiness, release guard, PyPI README sync and
`git diff --check` pass.

Two separate local QA sessions returned correctness/security PASS and
house-style PASS, with no findings. Each recorded a verdict before the work
plan and retained it after. These are local reviews, not merge approval.

## Review correction

Initial head `7164824` passed both full runs at 1688 passed / 3 skipped and
92.70% coverage, but the remote Codex review found that its broad cleanup
also removed the CI dependency sentinel. That head is superseded. A new
regression calls the actual `test_real_dispatch._require()` with a deliberately
absent package and the sentinel set. Before the fix, the child skipped and
the regression failed. After the literal sentinel exception, the child proves
`ModuleNotFoundError` is raised. Both original QA lenses re-reviewed this
correction and passed it. The corrected full-run results are in the table
above. The final correction receipt is `qw-20261020-sdk-env-sentinel-review`;
the initial receipt remains unchanged as historical evidence.

## Scope and limits

Only test infrastructure and its regression change. No runtime SDK,
authentication, dependencies, workflows, package versions or publication.
The existing npm dependency advisories remain under #878 and their upgrade
PRs; this change does not remediate them. No rendered surface changes.
The roadmap and architecture were reviewed; no structural docs need updates.
Final-head CI, independent QA/merge and accepted-source readback remain
separate gates.

Sign-off: OpenAI | gpt-6.1-sol | xhigh. These are the actual executor model
and reasoning values from the local turn context; Codex is the agent surface.
