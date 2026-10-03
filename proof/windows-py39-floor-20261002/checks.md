# Validation

- Windows/Python 3.9.6 installed Chat/Anthropic floor: 12 passed, 16 deselected, zero skips/warnings.
- Windows/Python 3.9.6 installed Responses/Agents floor: 13 passed, 15 deselected, zero skips/warnings.
- Both profiles: ZIP CRC, 49 wheel-to-checkout files, 49 installed-file hashes and installed metadata equal; no mandatory SDK requirements; AgentGuard absent before install; copied test bytes equal checkout; owner credentials removed; `python -I`; pytest plugins disabled.
- Full current-source SDK suite on Python 3.13.2: 1404 passed, three optional Agents skips, zero warnings, 92.33% coverage; raw portable output in sdk-tests.txt. The architecture tests are included in this full suite.
- Configured Ruff file list passed via `python -m ruff`; the standalone command was not on PATH.
- Configured Bandit exclusions (B101/B110/B112/B311) passed; no exclusions changed.
- Documentation links/alt text, CI-tool pins, review readiness, release metadata, generated PyPI README and `git diff --check` passed.
- MCP build and all 11 MCP tests passed.
- Public proof privacy scan passed, including absolute/relative checkout and environment path forms.

The initial proof driver stopped before tests because pip 21.1.3 did not record a local archive hash. Installed-byte verification supplied the artifact identity for both completed runs. No product bug, provider request, new runtime dependency, workflow edit, tag or publication is claimed.
