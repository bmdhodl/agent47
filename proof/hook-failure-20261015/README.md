# Hook failure blocking: issue #871

## Result

On Windows, native Claude Code **2.1.296** executed the allowed Bash action.
Intentional AgentGuard refusal, missing executable, nonzero crash, timeout,
malformed JSON object, and schema-invalid JSON all blocked it. Each blocked
case returned a real host tool-result error and left the tool marker absent.
Seven cases passed. See [native/summary.json](native/summary.json), the exact
argv/settings/request/tool-result receipt for each case, and raw native stdout.

This is offline native-host integration, with a loopback-only scripted model,
a synthetic API key, new per-case config directories and projects, no copied
credentials, no active user settings, no MCP servers, and no session persistence.
All provider/proxy environment variables were excluded from child environments.
Native usage/cost fields reflect scripted fixture token values, not a provider
charge. No real provider call or account-setting change occurred.

## Commands and exit status

From the repository root, with `PYTHONPATH=sdk`:

- `python -m pytest sdk/tests/test_hook_install_failure.py -q -p no:cacheprovider`:
  before fix **18 failed**, exit 1. Raw: `regression-before.txt`.
- Final focused hook, installer and architectural tests: **51 passed**, exit 0.
  Raw: `focused-after.txt`. Includes two later empty-settings regressions;
  their initial failing result is in `empty-settings-before.txt`.
- Full SDK suite before the later Windows wrapper follow-up, with pytest-cov,
  cache disabled and a unique disposable basetemp:
  **1631 passed, 3 skipped**, **92.53% coverage**, exit 0. Raw: `sdk-suite.txt`.
  The three skips need the optional `agents` package, absent in this interpreter.
  This Windows run used Python 3.13.2; supported Python 3.11/3.12 remain CI gates.
- `python -m ruff check sdk/agentguard/ scripts/claude_hook_failure_acceptance.py
  sdk/tests/test_hook_install_failure.py sdk/tests/test_hooks.py`: exit 0.
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`: exit 0.
  The fixed local `claude --version` probe has narrowly scoped B404/B603
  annotations: no shell, no event/config-controlled command or arguments.
- CI-tools requirements and review-readiness guards: exit 0.
- `python scripts/claude_hook_failure_acceptance.py --output <fresh-output>
  --claude <native-claude-executable>`: **7/7 passed**, exit 0, native-final.txt.
  Each native invocation has a 45-second timeout; each server binds 127.0.0.1.

## Contract and limits

Install/preview now verifies `claude --version` is stable Claude Code 2.1.295
or later before settings mutation. Unsupported/unknown/missing/failed/timed-out
probes stop clearly. Only synchronous PreToolUse gets `onFailure: block`.
Reinstallation and removal preserve unrelated hooks, mixed groups and settings;
removal remains available without Claude Code. Existing handlers require an
explicit reinstall to gain the setting. A later host downgrade is not prevented.

An initial incomplete line `{invalid json` was treated by the host as plain
text and allowed the action (`native-failures.txt` retains that diagnostic).
This matches the official plain-stdout exception. A complete but malformed
JSON object was then blocked; the exact final fixture and native proof are
retained. Arbitrary stdout is not a deny, and no broader claim is made.

Official minimum and failure contract, checked 2026-10-15:
[Claude Code hooks reference](https://code.claude.com/docs/en/hooks#block-the-action-when-a-hook-fails).
No paid-model, production-profile, macOS or Linux native acceptance is claimed.
`child-cleanup.json` records zero remaining owned native/timeout-helper processes.
No package release or merge is authorized by these receipts. Final-head CI and
independent review remain separate gates. Proof predates automated PR review;
rerun affected checks after any review-driven code change. The initial hosted
review found a missing repository showwork receipt and a stale canonical hook
row. The row now distinguishes candidate from legacy behavior. A new isolated
showwork session explicitly records its late start and rechecks the proof;
it does not claim that the initial code work had an earlier repository ledger.

A later independent review found that bare `claude` lookup fails for npm's
Windows `.CMD` wrapper. The installer now resolves the executable with
`shutil.which` and passes that absolute path plus the fixed `--version` argument,
without `shell=True`. Two new regressions failed before this repair; all
73 hook/map/architecture checks then passed. `windows-real-preview.txt` records
the actual installed npm wrapper returning 2.1.296 through the real CLI preview;
no `.claude` directory or settings file was created. This repair changes host
discovery, not the already-exercised native hook policy.
The final post-wrapper SDK suite passed **1633 tests**, with **3 optional
`agents` dependency skips** and **92.66% coverage**, exit 0. Its separate raw
receipt is `windows-wrapper-sdk-suite.txt`; the earlier `sdk-suite.txt` remains
the historical run bound by the initial review receipt.

Sign-off: OpenAI | GPT-6 | auto.
