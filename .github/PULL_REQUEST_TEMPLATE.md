## Summary

<!-- What does this PR do? 1-3 bullet points. -->

## Related Issues

<!-- Link to GitHub issues: Closes #XX -->

## Proof

<!-- Paste validation commands and results. Link proof artifacts when useful. -->

## Review Readiness

Use these only when the PR touches the matching risk area. Leave a short note or
`N/A` so reviewers know it was considered.

- [ ] Public positioning claims have a source/fact ledger.
- [ ] State, lock, file, or process-concurrency changes include cross-platform failure proof.
- [ ] External API collectors include response-shape, pagination, null, and partial-failure tests.
- [ ] Proof artifacts include command, exit code, platform, and regenerated-after-review status.
- [ ] Workflow changes explain trigger scope, timeouts, concurrency, artifacts, and spend impact.

## Risk And Rollback

<!-- What could break? How would we revert or disable it? -->

## Scope

- **Related ops/doc(s):** <!-- NORTHSTAR | SDK_SCOPE | ARCHITECTURE | ROADMAP | DEFINITION_OF_DONE | N/A -->
- **Does this change the public API?** <!-- Yes / No. If yes, update ops/02-ARCHITECTURE.md. -->
- **Does this shift roadmap priority?** <!-- Yes / No. If yes, update ops/03-ROADMAP_NOW_NEXT_LATER.md. -->

## Checklist

- [ ] `make check` passes (pytest + ruff, coverage >= 80%)
- [ ] `make structural` passes (10 Golden Principles)
- [ ] `make security` passes (bandit)
- [ ] New functionality has tests
- [ ] No new hard dependencies in core SDK
- [ ] No hardcoded absolute paths
- [ ] If `__init__.py` exports changed, `ops/02-ARCHITECTURE.md` updated
