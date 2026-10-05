# Claims audit - session qw-20261004-activation-exclude-published-wheel-ci

**Check verdict: GREEN**  (6/6 checks passed)

**Outcome: UNVERIFIED**. No acceptance requirements declared. Only individual checks were evaluated.

Claim descriptions are author supplied. Results establish only the stated check.

- OK Check for claim: **The refresh script subtracts our own published-wheel CI from the off-publish-day real-interpreter figure** (`file_contains`)
    - /net_of_own_ci/ found in scripts/refresh_activation_snapshot.py
- OK Check for claim: **A fresh snapshot dated the run day is committed** (`file_exists`)
    - docs/guides/activation-snapshot-2026-10-05.json exists
- OK Check for claim: **The written snapshot carries the named published-wheel exclusion with its run dates and job counts** (`file_contains`)
    - /published_wheel_ci_runs/ found in docs/guides/activation-snapshot-2026-10-05.json
- OK Check for claim: **A test beside the script asserts the net figure is strictly lower than the raw figure** (`file_contains`)
    - /test_own_ci_net_figure_is_lower_than_the_raw_figure/ found in sdk/tests/test_activation_evidence.py
- OK Check for claim: **The classifier reports the net-of-own-CI real-interpreter figure beside the raw one** (`file_contains`)
    - /net_of_own_ci/ found in scripts/activation_weekly_report.py
- OK Check for claim: **The documented method names the published-wheel exclusion** (`file_contains`)
    - /published-wheel/ found in docs/guides/activation-metrics-design.md

## Explanation

Observation: current_rerun. Historical finish: absent.
Check verdict: GREEN. Outcome: UNVERIFIED. Integrity: unknown.
Limitations: undeclared requirements: unknown; test adequacy: not assessed; formatting does not change the verdict.
Recovery: Repair the failed check, then rerun verify. This text does not authorize a merge or a clean close.
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:0 revision:absent
       /net_of_own_ci/ found in scripts/refresh_activation_snapshot.py
  requirement:absent check:file_exists scope:individual_check result:pass evidence:claim:1 revision:absent
       docs/guides/activation-snapshot-2026-10-05.json exists
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:2 revision:absent
       /published_wheel_ci_runs/ found in docs/guides/activation-snapshot-2026-10-05.json
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:3 revision:absent
       /test_own_ci_net_figure_is_lower_than_the_raw_figure/ found in sdk/tests/test_activation_evidence.py
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:4 revision:absent
       /net_of_own_ci/ found in scripts/activation_weekly_report.py
  requirement:absent check:file_contains scope:individual_check result:pass evidence:claim:5 revision:absent
       /published-wheel/ found in docs/guides/activation-metrics-design.md
