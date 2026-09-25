# Claims audit - session v141-version-flag

**Check verdict: RED**  (4/8 checks passed)

**Outcome: UNVERIFIED**. Some acceptance checks or session checks did not pass.

Claim descriptions are author supplied. Results establish only the stated check.

- OK Check for claim: **CLI defines a version flag** (`file_contains`)
    - /action="version"/ found in sdk/agentguard/cli.py
- XX Check for claim: **Package version is 1.4.1** (`file_contains`, RED)
    - /^version = "1.4.1"/ NOT in sdk/pyproject.toml
- XX Check for claim: **Changelog has a 1.4.1 section** (`file_contains`, RED)
    - /^## 1.4.1/ NOT in CHANGELOG.md
- OK Check for claim: **Release guard passes for 1.4.1** (`command`)
    - exit 0, stdout has 'passed'
- OK Check for claim: **CLI defines a version flag** (`file_contains`)
    - /action="version"/ found in sdk/agentguard/cli.py
- XX Check for claim: **Package version is 1.4.1** (`file_contains`, RED)
    - /^version = "1.4.1"/ NOT in sdk/pyproject.toml
- XX Check for claim: **Changelog has a 1.4.1 section** (`file_contains`, RED)
    - /^## 1.4.1/ NOT in CHANGELOG.md
- OK Check for claim: **Release guard passes for 1.4.1** (`command`)
    - exit 0, stdout has 'passed'

## 4 gap(s) - a claimed 'done' is not real

- [RED/fail] Package version is 1.4.1 - /^version = "1.4.1"/ NOT in sdk/pyproject.toml
- [RED/fail] Changelog has a 1.4.1 section - /^## 1.4.1/ NOT in CHANGELOG.md
- [RED/fail] Package version is 1.4.1 - /^version = "1.4.1"/ NOT in sdk/pyproject.toml
- [RED/fail] Changelog has a 1.4.1 section - /^## 1.4.1/ NOT in CHANGELOG.md

## Explanation

Observation: current_rerun. Historical finish: absent.
Check verdict: RED. Outcome: UNVERIFIED. Integrity: unknown.
Limitations: undeclared requirements: unknown; test adequacy: not assessed; formatting does not change the verdict.
Recovery: Repair the failed check, then rerun verify. This text does not authorize a merge or a clean close.
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:0 revision:absent
       /action="version"/ found in sdk/agentguard/cli.py
  requirement:absent check:file_contains scope:individual_check result:fail evidence:claim:1 revision:absent
       /^version = "1.4.1"/ NOT in sdk/pyproject.toml
  requirement:absent check:file_contains scope:individual_check result:fail evidence:claim:2 revision:absent
       /^## 1.4.1/ NOT in CHANGELOG.md
  requirement:absent check:command scope:individual_check result:pass evidence:claim:3 revision:absent
       exit 0, stdout has 'passed'
  requirement:CLI defines a version flag check:file_contains scope:artifact result:pass evidence:requirement:flag revision:absent
       /action="version"/ found in sdk/agentguard/cli.py
  requirement:Package version is 1.4.1 check:file_contains scope:artifact result:fail evidence:requirement:bump revision:absent
       /^version = "1.4.1"/ NOT in sdk/pyproject.toml
  requirement:Changelog has a 1.4.1 section check:file_contains scope:artifact result:fail evidence:requirement:changelog revision:absent
       /^## 1.4.1/ NOT in CHANGELOG.md
  requirement:Release guard passes for 1.4.1 check:command scope:behavior result:pass evidence:requirement:guard revision:0c6bc4b2cc96
       exit 0, stdout has 'passed'
