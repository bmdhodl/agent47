# Claims audit - session agent47-release-guard-skill-metadata-20260815

**Verdict: GREEN**  (3/5 verified)

- OK **Release guard checks the public AgentGuard skill metadata version.** (`file_contains`, RED)
    - /SKILL_METADATA_PATH/ found in scripts/sdk_release_guard.py
- OK **Regression test covers stale skill metadata version detection.** (`file_contains`, RED)
    - /test_check_skill_metadata_reports_version_drift/ found in sdk/tests/test_sdk_release_guard.py
- OK **Release guard passes with synchronized candidate metadata.** (`command`, RED)
    - exit 0, stdout has 'Release guard passed.'
- .. **Full SDK test suite passes after release guard hardening.** (`None`, RED)
    - retracted: Initial receipt command encoded python -m incorrectly for showwork command checks; replacing it with the direct pytest executable.
- .. **Full SDK test suite passes after release guard hardening via direct pytest executable.** (`None`, RED)
    - retracted: Showwork command claims require a Python script path and cannot represent the pytest module invocation; the full suite was run and passed outside the receipt.
