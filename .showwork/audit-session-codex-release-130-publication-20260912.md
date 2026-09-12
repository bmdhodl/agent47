# Claims audit - session codex-release-130-publication-20260912

**Verdict: GREEN**  (5/5 verified)

- OK **Repository state now records the verified public 1.3.0 release** (`file_contains`)
    - /published 2026-09-12/ found in memory/state.md
- OK **Roadmap now records the published 1.3.0 release** (`file_contains`)
    - /published to PyPI on 2026-09-12/ found in ops/03-ROADMAP_NOW_NEXT_LATER.md
- OK **Release report records published social permalinks and exact PyPI trace readback** (`file_contains`)
    - /16ab935e6a714e5a82dd1c7135dce49c/ found in proof/v1.3.0/README.md
- OK **Raw public package smoke reports all seven hosted checks passed** (`file_contains`)
    - /RESULTS: 7/7 passed, 0 failed/ found in proof/v1.3.0/pypi-hosted.txt
- OK **Future test artifacts use directories excluded by the installed snapshotter while old evidence remains unchanged** (`file_contains`)
    - /Preserve existing session snapshots unchanged/ found in CLAUDE.md
