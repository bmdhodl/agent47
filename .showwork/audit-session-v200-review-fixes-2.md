# Claims audit - session v200-review-fixes-2

**Check verdict: RED**  (3/4 checks passed)

**Outcome: UNVERIFIED**. Some acceptance checks or session checks did not pass.

Claim descriptions are author supplied. Results establish only the stated check.

- OK Check for claim: **clean_install.sh stops outside Windows Git Bash before it touches the work dir** (`file_contains`)
    - /msys\*\|cygwin\*\) ;;/ found in proof/v2.0.0/clean_install.sh
- XX Check for claim: **verify.py accepts any Python 3.10 patch release in the wheel refusal check** (`file_contains`, RED)
    - /3\\.10\\.\d\+/ NOT in proof/v2.0.0/verify.py
- OK Check for claim: **proof README explains why the local sdist hash changes per build** (`file_contains`)
    - /sdist hash changes with each build/ found in proof/v2.0.0/README.md
- OK Check for claim: **clean_install.sh refuses to run outside Windows Git Bash, verify.py accepts any Python 3.10 patch release in the refusal check, and the release prep verifier passes** (`command`)
    - exit 0, stdout has 'Verified v2.0.0 release prep'

## 1 gap(s) - a claimed 'done' is not real

- [RED/fail] verify.py accepts any Python 3.10 patch release in the wheel refusal check - /3\\.10\\.\d\+/ NOT in proof/v2.0.0/verify.py

## Explanation

Observation: current_rerun. Historical finish: absent.
Check verdict: RED. Outcome: UNVERIFIED. Integrity: unknown.
Limitations: undeclared requirements: unknown; test adequacy: not assessed; formatting does not change the verdict.
Recovery: Repair the failed check, then rerun verify. This text does not authorize a merge or a clean close.
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:0 revision:absent
       /msys\*\|cygwin\*\) ;;/ found in proof/v2.0.0/clean_install.sh
  requirement:absent check:file_contains scope:individual_check result:fail evidence:claim:1 revision:absent
       /3\\.10\\.\d\+/ NOT in proof/v2.0.0/verify.py
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:2 revision:absent
       /sdist hash changes with each build/ found in proof/v2.0.0/README.md
  requirement:clean_install.sh refuses to run outside Windows Git Bash, verify.py accepts any Python 3.10 patch release in the refusal check, and the release prep verifier passes check:command scope:artifact result:pass evidence:requirement:review-fixes-2 revision:3d2e718dc920
       exit 0, stdout has 'Verified v2.0.0 release prep'
