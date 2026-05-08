# QA Report — deployed-agent preset

Verdict: PASS

## Scope match

The diff matches `WORK_PLAN.md` exactly. No scope creep beyond the four files
listed in the plan (profiles, setup docstring, test, CHANGELOG).

## What was checked

- `sdk/agentguard/profiles.py` — new `DEPLOYED_AGENT_PROFILE` constant and
  dict entry follow the existing pattern. Comment block explains the
  motivation and what was deliberately left out (install/registry/oversight
  guards). Values (loop_max=2, retry_max=1, warn_pct=0.5) are strictly
  tighter than `coding-agent` as expected for a deployed-agent preset.
- `sdk/agentguard/setup.py` — docstring updated to list new profile.
  `normalize_profile` already uses `_PROFILE_DEFAULTS` keys for error
  messages, so no other update needed.
- `sdk/tests/test_init.py` — new test mirrors the existing
  `test_coding_agent_profile_tightens_guard_defaults` and additionally
  covers `warn_pct` via `get_budget_guard()._warn_at_pct`. Idiomatic.
- `CHANGELOG.md` — one Unreleased entry citing the arxiv paper.

## Test result

`pytest sdk/tests/ -x` — 708 passed, 0 failed.

## Safety checks

- No secrets or credentials added.
- No denylist paths touched (`.github/workflows/`, `.env*`,
  `supabase/migrations/`, `security/`, Stripe/Clerk).
- No new dependencies.
- No network calls.
- No test coverage regressions — net +1 test.

## Repo pattern adherence

- Naming: hyphenated `deployed-agent` matches `coding-agent`.
- Constant: `DEPLOYED_AGENT_PROFILE` matches `CODING_AGENT_PROFILE`.
- Test method name pattern matches the precedent.
- Comment voice matches surrounding code (terse, no fluff).

## Known gap (intentional, called out in WORK_PLAN.md)

The task body asked for `max_install_count`, `registry_write: deny`,
`oversight_decision_immutable`, `approval_threshold`. These primitives don't
exist in the SDK today. This PR ships the preset registration + the security
narrative; a follow-up task can land the new guard classes.
