# AgentGuard 1.3.0 release validation

Candidate checked on 2026-09-12. Publication and social readback will be appended after they happen.

- Built wheel and source archive from `sdk/` with Python 3.13.2.
- Full SDK suite: 969 passed, 1 optional LangChain test skipped, 91.43% coverage. See `pytest.txt`.
- Installed the built wheel with `--no-deps` into a new environment. Metadata confirms 1.3.0 and imports from that environment, not the checkout.
- Doctor, offline demo, trace report, incident report, and raw quickstart generation all exit zero. See `wheel-*.txt`.
- The installed wheel sent a trace through the real hosted endpoint and read back exact trace ID `ef3120e3375e4c63b7f31743c1aeeb85`: 7/7 checks passed. OpenAI is mocked; no paid model call was made. `installed_hosted_smoke.py` deliberately removes the original script's checkout import insertion.
- Ruff, Bandit, release metadata synchronization, and diff whitespace checks pass. The preceding audit passed CI on Python 3.9 and 3.12, 107 optional integration/regression tests, both MCP suites, and npm audit.
- Quota prevented Copilot and Cursor Bugbot reviews of the audit. Codex completed with no inline findings. Claude's receipt findings were corrected with append-only retractions and a regenerated final report. Old ledger history is retained, not rewritten.
- This release changes the default announcement workflow to require an explicit opt-in before queuing text-only social drafts. This release's manually reviewed posts include a real demo image.

Known limitation: the CrewAI extra carries four unresolved ChromaDB advisories; see the September audit and changelog. This is not a clean bill of health for that optional dependency tree.

OpenAI | GPT-6 | auto
