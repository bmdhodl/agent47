# Validation

- `python -m pytest sdk/tests/test_example_starters.py sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_mcp_registry_metadata.py -q` -> 35 passed in 1.69s.
- `python scripts/sdk_release_guard.py --check-mcp-npm` -> Release guard passed.
- `git diff --check` -> passed.
- Proof artifact UTF-8/BOM/NUL/local-path scan -> passed after rewriting generated text files as UTF-8 without BOM.
- JSON artifact parse check -> passed.