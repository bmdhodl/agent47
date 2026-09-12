# Claims audit - session codex-release-130-final-20260912

**Verdict: GREEN**  (14/14 verified)

- OK **SDK developer instructions identify the 1.3.0 candidate** (`file_contains`)
    - /v1.3.0/ found in .claude/agents/sdk-dev.md
- OK **Shared instructions identify the 1.3.0 candidate** (`file_contains`)
    - /release candidate: v1.3.0/ found in AGENTS.md
- OK **Claude instructions identify the 1.3.0 candidate** (`file_contains`)
    - /Current release candidate: v1.3.0/ found in CLAUDE.md
- OK **Package metadata selects 1.3.0** (`file_contains`)
    - /version = "1.3.0"/ found in sdk/pyproject.toml
- OK **Bundled skill version matches 1.3.0** (`file_contains`)
    - /version: "1.3.0"/ found in skills/agentguard/SKILL.md
- OK **Release notes disclose the unresolved dependency advisories** (`file_contains`)
    - /four distinct unresolved/ found in CHANGELOG.md
- OK **Generated PyPI description includes the 1.3.0 notes** (`file_contains`)
    - /1.3.0/ found in sdk/PYPI_README.md
- OK **Repository state does not claim publication before it happens** (`file_contains`)
    - /1.3.0 release candidate, not yet published/ found in memory/state.md
- OK **Social queue dispatch requires explicit opt-in** (`file_contains`)
    - /inputs.queue_social == true/ found in .github/workflows/release-content.yml
- OK **SDK tests append mocked local OpenAI traces; not a provider-delivery claim** (`file_contains`)
    - /llm.openai.gpt-4o-mini/ found in traces.jsonl
- OK **Saved release suite reports 969 passes and one optional skip** (`file_contains`)
    - /969 passed, 1 skipped/ found in proof/v1.3.0/pytest.txt
- OK **Installed-wheel hosted smoke reports all seven checks passed** (`file_contains`)
    - /RESULTS: 7/7 passed, 0 failed/ found in proof/v1.3.0/wheel-hosted.txt
- OK **Release proof preserves the unresolved security limitation** (`file_contains`)
    - /CrewAI extra carries four unresolved/ found in proof/v1.3.0/README.md
- OK **Roadmap now targets the 1.3.0 candidate and preserves publication gates** (`file_contains`)
    - /release-prep branch targets/ found in ops/03-ROADMAP_NOW_NEXT_LATER.md
