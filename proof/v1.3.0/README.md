# AgentGuard 1.3.0 release validation

Candidate and public release checked on 2026-09-12. Published as 1.3.0.

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


## Publication and downstream readback

- Trusted PyPI publish and GitHub release workflow succeeded: run 34712412922, tag v1.3.0 at 9f0492ea96f3f3e23f195884a5ff4d1853afc50a.
- Fresh `pip install --no-cache-dir --index-url https://pypi.org/simple agentguard47==1.3.0` installed the public package with no base dependencies. `pypi-metadata.txt` shows the isolated environment import path.
- Doctor, demo, report, incident, and raw quickstart passed again from that environment. Hosted smoke passed 7/7 and read back exact trace ID `16ab935e6a714e5a82dd1c7135dce49c`. Provider response mocked; transport and persistence live.
- Installing LangChain Core 1.6.3 alongside the public package and running `budget_demo.py` produced zero tool executions with the zero-call budget. The same demo on 1.2.13 produced one. The image is rendered from captured Python output; it is not generated concept art. Responsive screenshot assertions passed at 375/768/1440 with no horizontal overflow.
- LinkedIn published and read back: https://www.linkedin.com/feed/update/urn:li:ugcPost:7504283081680297985/
- X published and read back with the image and alt text: https://x.com/phughes9000/status/2098847583556845686
- Both exact post texts passed defluff 0.1.2, score 0.0. LinkedIn also returned 0% likely AI on QuillBot model 7.1.0. This is detector output, not an authorship guarantee. X was scanned with defluff; no QuillBot authorship result is claimed for it.
- LinkedIn's alt-text editor crashed. The recovered photo flow published the correct image; its post body explains the image. An unrelated pre-existing GolfFly video draft was kept open unchanged in a separate tab.
- All nine default-branch Dependabot alerts resolved. Issues 709, 685, 698 and 642 closed; 686 closed as not planned. Nine superseded PRs closed. Issue 644 remains open because the CrewAI/ChromaDB finding is unresolved.
- Secret scan initially flagged 70 SHA-256 values in showwork snapshots as generic API keys. Snapshot values were validated as hashes; scanning the rest of the staged diff found no leaks. No global scanner exclusion was added.

OpenAI | GPT-6 | auto
