# PR #869 maintenance repair proof

Windows, CPython 3.13.2. No provider API calls, package release, active Claude
settings changes or real credentials were used. The argument markers in the
regressions are synthetic. Supported-version CI remains a separate gate.

- `regressions-before.txt`: 12 failing behavior regressions and one passing
  budget privacy control before production changes. This supersedes the
  original near-duplicate acceptance examples that folded string values.
- `focused-after.txt`: deterministic focused acceptance, rerunnable with
  `python proof/pr869-maintenance-20261015/verify.py`.
- `full-suite.txt`: initial complete SDK run, 1,652 passed, three optional
  dependency skips and one failure; coverage 92.67%. The failure was the old
  DX expectation that a loop error contains raw input. That expectation was
  changed to require omission; `dx-after.txt` records all 45 DX tests passing.
  This initial run is not claimed as a final full-suite pass.
- `lint.txt`, `structural.txt`, `security.txt`: Ruff passes, nine architecture
  checks pass, Bandit returns zero. An empty Bandit log means no findings.
- `mcp-tests.txt`: TypeScript build and all 11 MCP tests pass. The initial
  install hit a shared global npm cache collision. A task-specific cache
  resolved it, with both install outputs retained.
- `showwork.txt` and `showwork-final.txt`: earlier refusals are retained. One
  lacked declarations for files inherited from main; another detected the
  live full-suite log changing during verification. Neither was bypassed.
  `showwork-closed.txt` records the later stable close.
- `native/summary.json`: actual Claude Code 2.1.296 executed five varied
  failing Bash commands with captured `PostToolUseFailure` payloads, then a
  distinct recovery command. Default `0` allowed it and wrote the marker;
  explicit `5` refused it and the marker stayed absent. Both native-host
  cases pass against a loopback scripted provider. This is not evidence of
  live provider use, real empty Grep/Glob payloads, or active-profile setup.

The fixes retain semantic argument strings, send structured results and raw
invocation arguments to guards only in memory, omit raw argument data from
refusal traces/messages, hash persisted hook error outcomes, and set the
hook's no-progress default to zero. The guard-data override is private and
does not change the public event or persisted trace schema.

Sign-off: OpenAI | GPT-6 | auto
