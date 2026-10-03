# Repository validation

Completed on 2026-10-02, all commands exit 0. This summarizes command output;
the full SDK output is retained separately in `sdk-tests.txt`.

- Current source on Windows/Python 3.13.2: **1404 passed, 3 optional Agents
  skips, zero warnings, 92.35% coverage**. Includes architecture assertions.
- Eight selected real-client cases in each clean installed-wheel profile on
  Windows/Python 3.11.9: no skips or warnings, exit 0.
- Changed test file and the exact `make lint` Ruff inventory passed.
- Configured SDK Bandit scan passed; no exclusions changed.
- Docs, generated PyPI README, release metadata, CI tool pins and review
  readiness checks passed.
- TypeScript build and all 11 MCP tests passed.
- Both receipt test-copy hashes matched the executed checkout bytes. Both
  installed archive hashes match the same candidate wheel; its 49 package
  files still equal current SDK source bytes and its ZIP CRC is valid.
- Entire public proof bundle was scanned for local user/checkout paths,
  including relative pytest node prefixes. Captured public text normalizes LF,
  removes terminal trailing whitespace and substitutes local paths.

Hosted floor/current CI is the merge gate for the supported matrix row. Local
spot-checks alone do not establish Ubuntu or all-platform support. No workflow
change, runtime change, release or outside-user evidence is included.
