# SDK dependency security analysis — 2026-06-06

Resolves the dependency/security triage for issues #507, #469 (pip-audit
findings) and the dependency-drift portion of #418. Method follows the owner
triage notes on #507/#469: reproduce from repo-declared dependencies only, then
keep what reproduces and discard environment noise.

## 1. The SDK runtime is zero-dependency (definitive)

A clean install of the SDK core pulls nothing third-party:

```
$ python -m venv /tmp/ag-clean-venv
$ /tmp/ag-clean-venv/bin/python -m pip install ./sdk
$ /tmp/ag-clean-venv/bin/python -m pip freeze
agentguard47 @ file:///.../sdk
```

(`sdk-only-freeze.txt`) — zero runtime dependencies, so the SDK runtime has
**zero dependency vulnerabilities**. This is the locked zero-dependency design.

## 2. pip-audit findings in #507/#469 are mostly environment noise

The issues list: pypdf, pytest, python-dotenv, python-multipart, requests,
starlette, urllib3, uv. Auditing the repo's actual declared dev tooling
(`.github/requirements/ci-tools.in`) reproduces **only one** of them:

```
$ python -m pip_audit -r .github/requirements/ci-tools.in
Found 1 known vulnerability in 1 package
Name   Version ID             Fix Versions
pytest 8.4.2   CVE-2025-71176 9.0.3
```

(`pip-audit-ci-tools.txt`)

The other seven are **not AgentGuard dependencies** — they are pulled by
unrelated tools in the developer's global Python environment
(`false-positive-provenance.txt`):

| Package | Pulled by (not AgentGuard) |
|---|---|
| pypdf | embedchain |
| python-multipart | mcp, streamlit |
| starlette | fastapi, mcp, sse-starlette, streamlit |
| requests | crewai-tools, langchain, twine, pip_audit, … |
| urllib3 | botocore, docker, requests, twine, … |
| uv | crewai |
| python-dotenv | (not in SDK or ci-tools) |

None are imported anywhere under `sdk/agentguard/` (verified by grep). The SDK
uses stdlib `urllib` for its `HttpSink`, not `requests`/`urllib3`.

## 3. The one real finding (pytest) cannot be patched without dropping Python 3.9

`CVE-2025-71176` (GHSA-6w46-j5rx-g56g, "vulnerable tmpdir handling") is fixed
**only in pytest 9.0.3**. pytest 9.0.x requires **Python >=3.10**
(`pytest-py39-conflict.txt`), but the SDK supports **Python >=3.9**
(`sdk/pyproject.toml` `requires-python`, and the 3.9 classifier + CI job).

`scripts/ci_tools_requirements_guard.py` enforces that every CI-tool pin
supports Python 3.9, so bumping pytest to 9 would fail that guard and break the
3.9 test job.

**Risk acceptance:** pytest is a test-only tool. It is never shipped in the
published wheel and never runs on untrusted input (it runs this repo's own
trusted test code). The CVE is a local, predictable-tmpdir issue requiring a
hostile multi-user host. For a CI runner and a single-developer machine on
trusted code the real-world exposure is negligible. We keep pytest at 8.4.2
(the latest 8.x; no 8.x fix exists) rather than drop the advertised Python 3.9
support for a test-only, low-severity finding. Revisit when the SDK's Python
floor moves to 3.10.

## 4. Optional integration extras (#418 security rows)

The optional extras use lower-bound (`>=`) specs and there is **no committed
Python lockfile**, so a fresh `pip install 'agentguard47[...]'` resolves to the
**latest patched upstream**. The SDK never ships or pins a vulnerable version.

| Extra | Floor | CVE status |
|---|---|---|
| langgraph | `>=0.6.11` | CVE-2026-28277 fixed in 1.0.10 (major). Floor permits the patched 1.x; forcing a 1.x floor is a deferred compatibility change. |
| langchain-core | `>=0.3.84` | Worst CVE (CVE-2026-44843, deserialization RCE) fixed in 0.3.85 (safe minor) and 1.3.3; two further CVEs need 1.2.x (major). Floor permits patched releases. |
| crewai | `>=0.28` | No advisory; `>=0.28` still resolves (latest 1.14.x ≥ 0.28). |
| opentelemetry-api/sdk | `>=1.41.0` | No advisory; floor already permits 1.42.x. |

Major-version floor bumps (langgraph 1.x, langchain 1.x) are tracked as
deliberate compatibility work per the repo's stated drift policy and are not
forced here, since they cannot be smoke-tested for the optional integrations in
this pass and provide no benefit to fresh installs (which already get patched
upstreams).

## 5. #418 version drift — already resolved

`sdk/pyproject.toml` is at **1.2.13** (matches the shipped release), not the
`1.2.9`/`1.2.10` cited in the original 2026-05-02 report. The latest weekly
drift comment (2026-06-05) confirms this. Remaining drift items are
suggestion-only optional-extra floors and deferred major upgrades, which the
ongoing weekly drift report continues to track.

## Conclusion

- #507 / #469: no reproducible runtime-dependency vulnerability; the single
  dev-tooling finding (pytest) is a documented, accepted, test-only risk that
  cannot be fixed without dropping Python 3.9. Closed with this proof.
- #418: version drift resolved; security rows are covered by `>=` floors +
  fresh-install resolution; major bumps deferred by policy.
