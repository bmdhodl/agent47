# QA_REPORT.md - anthropic-advisor-max-tokens-update-positioning (agent47)

**Verdict:** OK

## What was checked

1. Diff scope: only `README.md` and the auto-generated `sdk/PYPI_README.md`. No code in `sdk/`. No `.github/workflows/`. No `.env*`. No `security/`. No `supabase/`. No secrets.
2. Banned-word scan (grep -i over README.md): no matches for harness / leverage / streamline / delve / landscape / cutting-edge / game-changer / revolutionary / seamless / robust / holistic / synergy / ecosystem.
3. `pytest sdk/tests/test_pypi_readme_sync.py` -- 5/5 pass. The PYPI_README sync test is the gate on this README change; it is green.
4. Full SDK test suite (`pytest sdk/tests/`) revealed ONE failure: `test_init.py::TestInit::test_init_default_local_sink`. Confirmed pre-existing by re-running on stock `main` with my changes stashed -- same failure. Cause: local environment has `AGENTGUARD_API_KEY` + `AGENTGUARD_SERVICE` env vars set (vault config) that override the default sink. Unrelated to this PR.
5. Scope match: WORK_PLAN.md said README lead-paragraph reframe + new comparison section + PYPI_README regen. Diff does exactly that.
6. Voice rules: builder-to-builder, short sentences, numbers (the 2026-06-02 date and the concrete table), no fluff, no em dashes in new content. Existing em-dash on the lead paragraph was replaced with `--` as part of the rewrite.
7. README total diff: ~50 LOC added, well under the 400-LOC merge ceiling.

## What was NOT changed

- No code under `sdk/`.
- No tests added or modified.
- No new dependencies.
- No claims about Anthropic API beyond what the 2026-06-03 source page documents (per-tool `max_tokens` on the advisor tool, refusal-not-billed).

## Independent verifier note

Task `signal_type: vendor-announcement`, not `security-threat`. CVE-Bench second-verifier requirement does not apply.
