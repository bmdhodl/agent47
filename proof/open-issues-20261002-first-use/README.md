# Open issue pass, 2026-10-02

This dated receipt does not replace GitHub #729 or claim completion of the 25 open issues. The owner selected the full backlog. Evidence, architecture, personal-post and release activation gates remain explicit.

## First-use correction

The README recommended `receipt`, `hook` and `run` after installing published 1.4.0. Those commands, plus `--version`, exit 2 in that wheel (`before-unreleased-commands.json`). The README and generated PyPI source description now mark them as 1.4.1 candidate-only. Published PyPI metadata is unchanged.

`powershell-walkthrough.txt` records the exact first PowerShell block from `docs/guides/try-release.md`, executed with Windows PowerShell, fresh Python 3.11 and `agentguard47==1.4.0`: exit 0. Doctor, demo, two reports and the raw starter completed. All three demo stop events and the starter trace were checked. The local script's 15.85 seconds do not measure an outside user's first-use time. No activation script, security policy change, provider key, optional dependency or paid call was needed.

Checks after the documentation fix:

- `python -m pytest sdk/tests/test_documentation.py sdk/tests/test_release_example.py sdk/tests/test_pypi_readme_sync.py -q`: exit 0, 39 passed.
- `python -m pytest -p pytest_cov <checkout>/sdk/tests -q --cov=agentguard --cov-fail-under=80 --basetemp <isolated-test-directory>/pytest`: exit 0, 1392 passed, 3 optional Agents SDK skips, 3 runtime warnings, **92.40% coverage**. Windows/Python 3.13.2; raw output in `sdk-tests.txt`. Structural tests are part of this full suite.
- Ruff, `sdk_release_guard.py`, `check_docs.py --repository agent47`, generated README checks and `git diff --check`: exit 0.
- The repository's configured Bandit command, `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`: exit 0. Its existing exclusions were unchanged.

All evidence above was regenerated after the documentation fix. The earlier PR review proof explains this checkout's Windows junction; logical and physical paths can differ in unedited output. These artifact receipts do not certify external adoption.

## Upstream readback

`upstream.json` captures PyPI metadata and OSV on October 2. CrewAI 1.15.23 still requires `chromadb~=1.1.0`. Latest ChromaDB is 1.5.9; PYSEC-2026-311 lists affected releases from 1.0.0 through 1.5.9. No compatible fixed release was found. #644 stays open; a future resolved-tree audit is still necessary. Sources: [CrewAI](https://pypi.org/pypi/crewai/json), [ChromaDB](https://pypi.org/pypi/chromadb/json), [OSV](https://osv.dev/vulnerability/PYSEC-2026-311).

## All-issue audit

`issue-inventory.json` retains the 25 issue identities and readback timestamps. Each issue body was read for scope, acceptance and dependencies.

| Issue | Current finding and next evidence |
|---|---|
| #644 | Upstream fixed, CrewAI-compatible ChromaDB release and fresh tree audit needed. |
| #729 | Parent remains open while child requirements and dated decisions remain incomplete. |
| #735 | #786 implemented Experimental Responses/Agents paths. Real supported floor/current proof is still needed before promotion; no new exports are needed. |
| #736 | Matrix exists; Responses support and clean CrewAI resolution or an owner exception remain incomplete. Extras currently have Ubuntu evidence only. |
| #737 | October 16 gate needs three consented outside workflow activations and a later-day repeat. Missing inputs must produce narrow/hold at the checkpoint. |
| #738 | Candidate Claude hook exists; actual host/OS proof, doctor probe, failure cases and demand gate remain incomplete. |
| #739 | Needs approved Cursor translation and real host allow/deny, failure and reversible-configuration proof. |
| #740 | Needs the local MCP package/authority design. Default tools must not raise limits or clear stops; hosted read-only tools stay separate. |
| #741 | Needs approved host/MCP interception, zero downstream dispatch on denial, and spoofing/replay/restart/concurrency proof. |
| #742 | Reports/receipts are partial. Needs the accepted stop contract, scope/unknown fields and redacted denial fixtures. |
| #743 | Needs an optional versioned reference contract and offline examples with separate runtime and showwork results. |
| #744 | Needs owner-reviewed AgentGuard-side BMD contract and fake-worker proof; no BMD source/storage changes. |
| #745 | November 13 gate needs three repeat users across two stacks over 14 days, plus completion/false-stop denominators. |
| #746 | This pass fixes candidate command confusion and tests PowerShell first use. Three outside tester observations remain unverified. |
| #747 | Needs the 5-8 scenario corpus, native/no-guard controls, false-stop cases, versions and raw performance/dispatch results. |
| #748 | Repo fixture and release example already shipped. Post analytics and two outside actionable reports remain unverified; no posting occurred. |
| #749 | Needs tested Claude/Cursor packaging and fresh-profile install/upgrade/uninstall proof after adapters. Registry submission stays owner-reviewed. |
| #750 | Needs owner-reviewed candidate workflow, no-op/blocked cases and three exact-artifact rehearsals. No production schedule/publication enabled. |
| #751 | Needs fake failure/retry/delivery rehearsals and recovery runbook; no subscriber blast or destructive rollback. |
| #752 | Needs candidate/recovery rehearsals, repeat-use evidence and explicit owner activation. Unattended publication stays disabled. |
| #753 | December 11 gate needs five repeat users, two actionable reports/contributions and three consented examples; expansion needs approval. |
| #754 | Conditional: three outside JavaScript workflows and an alternatives/capacity decision before a TypeScript port. |
| #755 | Conditional: two outside multi-host deployments and gateway comparison before a new owner-approved store/protocol. |
| #756 | Conditional: consented real loop/success patterns, held-out replay results and overhead measurement before a loop change. |
| #757 | Conditional: three users unable to use supported hooks, alternatives review and mandatory-interception threat model before expansion. |

No issue is closed by this partial pass. External usage remains unverified. No package release, personal post, subscriber send, new API, workflow or cross-product authority was introduced.

Sign-off: OpenAI | GPT-6 | auto
