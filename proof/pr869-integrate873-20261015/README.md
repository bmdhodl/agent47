# PR #869 integration with merged #873

Merged `origin/main` at `ff21dea510f0c8442002c658cf380e07275ecc3b` into the
existing loop-repair branch. Hook source and tests merged automatically.
The guide and canonical enforcement row were resolved to retain both contracts:
version-gated synchronous failure blocking and opt-in no-progress detection
with default zero, exact argument values and private guard input.

Windows / CPython 3.13.2 validation:

- `verify.py`: **317 passed**, including installer, loop, tracing, privacy,
  architecture and documentation checks. Raw output: `focused.txt`.
- Ruff and Bandit pass. An empty `security.txt` is a successful zero-finding scan.
- Actual Windows npm-wrapper installer preview reports Claude Code **2.1.296**
  and creates no settings: `preview.json`.
- Native Claude Code **2.1.296**: both loop/recovery cases and all seven failure
  cases pass against the combined source. Raw payloads, actual host tool results,
  marker state and summaries are under `native-loop/` and `native-failures/`.
  `native-summary.json` binds all nine cases to the hook source SHA-256.
- `child-cleanup.json` records zero matching task-native or timeout processes.
  No process was stopped, and no provider or active profile was used.
- Release, CI-tools and review-readiness guards pass. Final-commit CI and
  independent review remain separate gates; no package release is authorized.

The single `inbox/log.md` entry records the actual #873 merge. This merge of
main does not claim that #869 has itself merged.

Sign-off: OpenAI | GPT-6 | auto
