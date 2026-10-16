# Claims audit - session v200-review-fixes-2

**Check verdict: GREEN**  (5/5 checks passed)

**Outcome: VERIFIED**. Declared acceptance checks passed; requirement coverage and test adequacy need review.

Claim descriptions are author supplied. Results establish only the stated check.

- OK Check for claim: **clean_install.sh stops outside Windows Git Bash before it touches the work dir** (`file_contains`)
    - /msys\*\|cygwin\*\) ;;/ found in proof/v2.0.0/clean_install.sh
- .. Check for claim: **verify.py accepts any Python 3.10 patch release in the wheel refusal check** (`None`)
    - retracted: Claim pattern was mis-escaped by the shell and could not match the code; re-recorded with a pattern that matches the new regex call.
- OK Check for claim: **proof README explains why the local sdist hash changes per build** (`file_contains`)
    - /sdist hash changes with each build/ found in proof/v2.0.0/README.md
- OK Check for claim: **verify.py checks the Python 3.10 refusal with a regex instead of the fixed 3.10.11 string** (`file_contains`)
    - /re\.search\(r"requires a different Python: 3/ found in proof/v2.0.0/verify.py
- OK Check for claim: **verify.py no longer pins the 3.10.11 patch version** (`file_contains`)
    - /3\.10\.11/ absent as claimed
- OK Check for claim: **clean_install.sh refuses to run outside Windows Git Bash, verify.py accepts any Python 3.10 patch release in the refusal check, and the release prep verifier passes** (`command`)
    - exit 0, stdout has 'Verified v2.0.0 release prep'

## Explanation

Observation: current_rerun. Historical finish: absent.
Check verdict: GREEN. Outcome: VERIFIED. Integrity: unknown.
Limitations: undeclared requirements: unknown; test adequacy: not assessed; formatting does not change the verdict.
Recovery: Repair the failed check, then rerun verify. This text does not authorize a merge or a clean close.
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:0 revision:absent
       /msys\*\|cygwin\*\) ;;/ found in proof/v2.0.0/clean_install.sh
  requirement:absent check:absent scope:individual_check result:skipped evidence:claim:1 revision:absent
       retracted: Claim pattern was mis-escaped by the shell and could not match the code; re-recorded with a pattern that matches the new regex call.
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:2 revision:absent
       /sdist hash changes with each build/ found in proof/v2.0.0/README.md
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:3 revision:absent
       /re\.search\(r"requires a different Python: 3/ found in proof/v2.0.0/verify.py
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:4 revision:absent
       /3\.10\.11/ absent as claimed
  requirement:clean_install.sh refuses to run outside Windows Git Bash, verify.py accepts any Python 3.10 patch release in the refusal check, and the release prep verifier passes check:command scope:artifact result:pass evidence:requirement:review-fixes-2 revision:563c68a87735
       exit 0, stdout has 'Verified v2.0.0 release prep'
