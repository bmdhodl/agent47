# Claims audit - session v132-publish

**Check verdict: GREEN**  (24/24 checks passed)

**Outcome: VERIFIED**. Declared acceptance checks passed; requirement coverage and test adequacy need review.

Claim descriptions are author supplied. Results establish only the stated check.

- OK Check for claim: **verify_publication.py passes against 1.3.2 receipts** (`command`)
    - exit 0, stdout has 'passed'
- OK Check for claim: **PUBLICATION.md records PyPI 1.3.2** (`file_contains`)
    - /pypi.org/project/agentguard47/1.3.2/ found in proof/v1.3.2/PUBLICATION.md
- OK Check for claim: **memory/state.md records published 1.3.2** (`file_contains`)
    - /Latest verified published SDK release: 1.3.2/ found in memory/state.md
- OK Check for claim: **inbox records merged 725 and tag v1.3.2** (`file_contains`)
    - /tagged `v1.3.2`/ found in inbox/log.md
- OK Check for claim: **public-demo recorded 200 tokens once** (`file_contains`)
    - /"recorded_tokens": 200/ found in proof/v1.3.2/public-demo.json
- OK Check for claim: **public-smoke is site-packages 1.3.2** (`file_contains`)
    - /site-packages/ found in proof/v1.3.2/public-smoke.json
- OK Check for claim: **attestation receipt exists** (`file_exists`)
    - proof/v1.3.2/attestation.json exists
- OK Check for claim: **pypi metadata receipt exists** (`file_exists`)
    - proof/v1.3.2/pypi.json exists
- OK Check for claim: **compose URLs exist** (`file_exists`)
    - proof/v1.3.2/compose-urls.txt exists
- OK Check for claim: **LinkedIn copy uses the release URL** (`file_contains`)
    - /releases/tag/v1.3.2/ found in proof/v1.3.2/linkedin.txt
- OK Check for claim: **X copy uses the release URL** (`file_contains`)
    - /releases/tag/v1.3.2/ found in proof/v1.3.2/x.txt
- OK Check for claim: **LinkedIn slop is zero** (`file_contains`)
    - /"slop_score": 0.0/ found in proof/v1.3.2/linkedin-slop.json
- OK Check for claim: **X slop is zero** (`file_contains`)
    - /"slop_score": 0.0/ found in proof/v1.3.2/x-slop.json
- OK Check for claim: **proof README points at PUBLICATION.md** (`file_contains`)
    - /PUBLICATION.md/ found in proof/v1.3.2/README.md
- OK Check for claim: **installed smoke helper exists** (`file_exists`)
    - proof/v1.3.2/installed_smoke.py exists
- OK Check for claim: **pip-show receipt exists** (`file_exists`)
    - proof/v1.3.2/pip-show.txt exists
- OK Check for claim: **verify script exists** (`file_exists`)
    - proof/v1.3.2/verify_publication.py exists
- OK Check for claim: **publish session ledger exists** (`file_exists`)
    - .showwork/sessions/v132-publish.jsonl exists
- OK Check for claim: **release-content.yml now has the email job from 726** (`file_contains`)
    - /python scripts/send_release_email.py/ found in .github/workflows/release-content.yml
- .. Check for claim: **roadmap records the release email job** (`None`)
    - retracted: pattern did not match the roadmap sentence
- .. Check for claim: **DoD requires the release-content email job** (`None`)
    - retracted: pattern did not match the DoD checkbox wording
- OK Check for claim: **roadmap records the release email job** (`file_contains`)
    - /automatically email active AgentGuard subscribers/ found in ops/03-ROADMAP_NOW_NEXT_LATER.md
- OK Check for claim: **DoD requires the release-content email job** (`file_contains`)
    - /emails active AgentGuard/ found in ops/04-DEFINITION_OF_DONE.md
- OK Check for claim: **PyPI 1.3.2 smoke and streaming demo receipts match** (`command`)
    - exit 0, stdout has 'passed'
- OK Check for claim: **PUBLICATION.md records PyPI 1.3.2** (`file_contains`)
    - /pypi.org/project/agentguard47/1.3.2/ found in proof/v1.3.2/PUBLICATION.md
- OK Check for claim: **memory/state.md records published 1.3.2** (`file_contains`)
    - /Latest verified published SDK release: 1.3.2/ found in memory/state.md
