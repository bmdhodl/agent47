# Metadata tool upgrade review

Fresh Windows Python3.11 hash installation, pip check, actual metadata/plugin discovery and missing-metadata behavior, complete source suite, required Ruff/security/floor/release checks and candidate wheel build are retained. Only importlib-metadata changes among19 hash-pinned tool packages; the other18 packages and fixed provider floors are preserved. Official PyPI artifact hashes match.

The full Makefile lint target also exposed31 findings in the review-readiness script, which hosted CI omits. Modern annotations and equivalent empty-list conditions preserve existing checks;25 guard/preflight cases and final full lint pass. Original failing lint and an invalid build-harness attempt using obsolete venv setuptools remain explicit historical failures; corrected declared build isolation and final checks pass. Commands, timestamps, working directory, exits and source hashes are retained with optional-provider limits. Four prior merged dependency PRs and their actual successful main CI readbacks are historical handoff evidence.

Run `python proof/dependency-review-839/verify.py` to verify retained evidence. Current-head hosted CI and merge remain separate gates. No SDK runtime/API change or release.
