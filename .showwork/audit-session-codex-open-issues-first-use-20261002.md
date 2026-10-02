# Claims audit - session codex-open-issues-first-use-20261002

**Check verdict: GREEN**  (10/10 checks passed)

**Outcome: VERIFIED**. Declared acceptance checks passed; requirement coverage and test adequacy need review.

Claim descriptions are author supplied. Results establish only the stated check.

- OK Check for claim: **README labels unpublished command examples as candidate-only** (`file_contains`)
    - /1.4.1 candidate/ found in README.md
- OK Check for claim: **Generated PyPI source description carries the candidate command labels** (`file_contains`)
    - /1.4.1 candidate/ found in sdk/PYPI_README.md
- OK Check for claim: **The release guide includes the directly tested PowerShell walkthrough** (`file_contains`)
    - /Windows PowerShell/ found in docs/guides/try-release.md
- OK Check for claim: **The dated before-proof records rejected candidate commands in published 1.4.0** (`file_contains`)
    - /"exit_code": 2/ found in proof/open-issues-20261002-first-use/before-unreleased-commands.json
- OK Check for claim: **The raw installed-wheel PowerShell walkthrough output is retained** (`file_contains`)
    - /Exit code: 0/ found in proof/open-issues-20261002-first-use/powershell-walkthrough.txt
- OK Check for claim: **Raw final SDK test output is retained** (`file_contains`)
    - /1392 passed, 3 skipped, 3 warnings/ found in proof/open-issues-20261002-first-use/sdk-tests.txt
- OK Check for claim: **Current upstream CrewAI and advisory metadata are retained as dated evidence** (`file_contains`)
    - /1.15.23/ found in proof/open-issues-20261002-first-use/upstream.json
- OK Check for claim: **All-issue identity readback includes the conditional MCP issue** (`file_contains`)
    - /AG-28/ found in proof/open-issues-20261002-first-use/issue-inventory.json
- OK Check for claim: **The dated audit records actual verification and remaining requirements for all issues** (`file_contains`)
    - /92.40%/ found in proof/open-issues-20261002-first-use/README.md
- OK Check for claim: **The first-use guide gives tested commands for published 1.4.0 and labels candidate-only commands** (`file_contains`)
    - /1.4.1 candidate/ found in README.md

## Explanation

Observation: current_rerun. Historical finish: absent.
Check verdict: GREEN. Outcome: VERIFIED. Integrity: unknown.
Limitations: undeclared requirements: unknown; test adequacy: not assessed; formatting does not change the verdict.
Recovery: Repair the failed check, then rerun verify. This text does not authorize a merge or a clean close.
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:0 revision:absent
       /1.4.1 candidate/ found in README.md
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:1 revision:absent
       /1.4.1 candidate/ found in sdk/PYPI_README.md
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:2 revision:absent
       /Windows PowerShell/ found in docs/guides/try-release.md
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:3 revision:absent
       /"exit_code": 2/ found in proof/open-issues-20261002-first-use/before-unreleased-commands.json
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:4 revision:absent
       /Exit code: 0/ found in proof/open-issues-20261002-first-use/powershell-walkthrough.txt
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:5 revision:absent
       /1392 passed, 3 skipped, 3 warnings/ found in proof/open-issues-20261002-first-use/sdk-tests.txt
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:6 revision:absent
       /1.15.23/ found in proof/open-issues-20261002-first-use/upstream.json
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:7 revision:absent
       /AG-28/ found in proof/open-issues-20261002-first-use/issue-inventory.json
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:8 revision:absent
       /92.40%/ found in proof/open-issues-20261002-first-use/README.md
  requirement:The first-use guide gives tested commands for published 1.4.0 and labels candidate-only commands check:file_contains scope:artifact result:pass evidence:requirement:released-first-use revision:absent
       /1.4.1 candidate/ found in README.md
