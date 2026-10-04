# Ruff upgrade review

Ruff 0.16.9 reproduced 37 CI-script lint findings. Safe type/import updates plus a narrowed optional-import fallback and timezone-aware local-calendar clock fix now pass required lint. A regression using the committed pre-change script confirms that unexpected installed-package import errors were previously swallowed; the new guard propagates them while retaining the missing-package fallback. A UTC-midnight test protects the release guard's existing local-date boundary. Full source, lint, security, live pin-floor and release metadata checks are retained with actual commands/cwd/exit codes. Genuine Python3.11 compilation and actual Windows hash installation preserve the other pins and colorama fix. SDK runtime/API remain unchanged.

Verify with `python proof/dependency-review-838/verify.py`. Hosted CI and merge are separate gates.
