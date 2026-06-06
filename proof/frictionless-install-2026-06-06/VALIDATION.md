# Frictionless install + badge network effect — proof

**Date:** 2026-06-06

## Goal

Make SDK installation as frictionless as possible (already zero-dependency) and
add a low-friction network-effect loop that converts installs into visible
proof / new installs. Directly targets the documented gap: 3 GitHub stars
against thousands of PyPI downloads.

## What changed (SDK only, zero new dependencies)

1. **Bare `agentguard` now welcomes instead of dumping argparse help.**
   `cli.main()` routes the no-args path to `first_run.render_welcome`, which
   shows the 60-second local path (`doctor` -> `demo` -> `quickstart`) and the
   star CTA. The most-typed first command after `pip install` now guides the
   user to a win.

2. **`python -m agentguard` works.** Added `sdk/agentguard/__main__.py` mirroring
   the console script, so the CLI runs without the `agentguard` script on PATH.
   The older `python -m agentguard.cli` fallback still works and stays in the
   doctor/demo/quickstart hints.

3. **`agentguard badge` network-effect surface.** Prints a paste-able
   "Guarded by AgentGuard" README badge (markdown / rst / html). Every adopting
   repo becomes a backlink and social proof. Surfaced in the welcome, the demo
   close ("Show your repo is guarded"), and a dedicated README section.

4. **`agentguard welcome` subcommand** for re-showing the tour on demand.

## Files

- `sdk/agentguard/__main__.py` (new)
- `sdk/agentguard/first_run.py` (welcome + badge renderers)
- `sdk/agentguard/cli.py` (welcome/badge subcommands + bare-command routing)
- `sdk/agentguard/demo.py` (badge nudge at the success moment)
- `sdk/tests/test_first_run.py` (welcome, badge, CLI dispatch, end-to-end
  `python -m agentguard` subprocess test)
- README.md / CHANGELOG.md / sdk/PYPI_README.md (regenerated)
- ARCHITECTURE.md, ops/03-ROADMAP, memory/state.md, memory/distribution.md

## Verification (see checks.txt and cli-behavior.txt)

- ruff: All checks passed
- bandit: clean (exit 0)
- structural (test_architecture.py): 9 passed
- release-guard: passed
- full suite: 795 passed, total coverage ~92.5% (>= 80 gate)
- `first_run.py` coverage: 100%
- `__main__.py` coverage: 100% (import-level wiring test + end-to-end subprocess test)
- `python -m agentguard` end-to-end subprocess test: passing

Note: `checks.txt` was regenerated after the review-fix commit (8baa888). The
first capture predated the fix and showed `__main__.py` at 0% / 794 passed; the
current `checks.txt` is the source of truth and shows 100% / 795 passed.

## Automated review follow-ups (PR #584, claude-review: no blocking issues)

Applied the three minor nits the first review raised:
- Closed the `__main__.py` import-coverage gap with a wiring test (now 100%).
- Refreshed the stale `test_first_run.py` module docstring.
- Strengthened the badge assertions to match the full linked-image markdown
  (`[![Guarded by AgentGuard](`) instead of an incidental substring.

Second review raised one item — the proof artifacts contradicted each other
because `checks.txt` predated the fix. Resolved by regenerating `checks.txt`
above; it now shows `__main__.py` at 100% and 795 passing, matching this file.
