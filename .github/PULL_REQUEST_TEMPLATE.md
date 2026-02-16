## Summary

<!-- What does this PR do? 1-3 bullet points. -->

## Related Issues

<!-- Link to GitHub issues: Closes #XX -->

## Scope

- **Related ops/ doc(s):** <!-- NORTHSTAR | SDK_SCOPE | ARCHITECTURE | ROADMAP | DEFINITION_OF_DONE | N/A -->
- **Does this change the public API?** <!-- Yes / No — if Yes, update ops/02-ARCHITECTURE.md -->
- **Does this shift roadmap priority?** <!-- Yes / No — if Yes, update ops/03-ROADMAP_NOW_NEXT_LATER.md -->

## Checklist

- [ ] `make check` passes (pytest + ruff, coverage >= 80%)
- [ ] `make structural` passes (10 Golden Principles)
- [ ] `make security` passes (bandit)
- [ ] New functionality has tests
- [ ] No new hard dependencies in core SDK
- [ ] No hardcoded absolute paths
- [ ] If `__init__.py` exports changed, `ops/02-ARCHITECTURE.md` updated
