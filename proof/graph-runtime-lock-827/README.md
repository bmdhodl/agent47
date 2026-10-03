# CI lock compiler proof (#827)

The CI-tool lock was actually regenerated with Python 3.10.11 and pip-tools
7.6.1, following the existing #662 maintenance-interpreter policy. All 21
existing package versions and their hashes remain identical. The Windows
compiler adds colorama 0.4.6; both hashes match PyPI. Mandatory SDK dependencies
remain zero and its Python 3.9 floor remains unchanged.

The exact failed updater revision is
`d9801668064b8f4214778175ee5bb5df6e5246d2`. Its
[parser](https://github.com/dependabot/dependabot-core/blob/d9801668064b8f4214778175ee5bb5df6e5246d2/python/lib/dependabot/python/file_parser/python_requirement_parser.rb#L27-L35)
places the actual compiler header before `.python-version`. Its
[version manager](https://github.com/dependabot/dependabot-core/blob/d9801668064b8f4214778175ee5bb5df6e5246d2/python/lib/dependabot/python/language_version_manager.rb#L117-L118)
chooses the first requirement. Consequently the old 3.9 header overrode the
repo's existing 3.10 configuration. The regression failed before regeneration
(1 failed / 10 passed) and passes afterward (11 passed).

`compiler.json` records the executed command and actual interpreter. The
supported `CUSTOM_COMPILE_COMMAND` override preserves that exact command;
pip-tools otherwise printed a false `--no-index` flag. The compiler generated
the Python header normally. No manual provenance relabeling was performed.
The explicit importlib-metadata pin retains build's Python 3.9 dependency.

Fresh Windows/Python 3.9.6 proof: hash-enforced installation of all CI tools,
`pip check`, 18 guard tests and the direct-pin compatibility guard pass. The
previously built candidate wheel also installs without dependencies and passes
`pip check`, `doctor` and `demo`. All 50 wheel Python modules match the unchanged
committed SDK source after explicitly normalizing CRLF/LF. The candidate stays
1.4.1 and unpublished; this is not a new release or a rebuilt-wheel claim.

Full SDK: 1584 passed, 3 existing optional Agents skips, zero warnings and
92.56% coverage. All eight configured checks pass, including 11 MCP tests.
Complete logs/JUnit are gzip retained with roundtrip checks; private local paths
are replaced. `validation.json` binds source Git blobs, results and log hashes.
The manifest binds the retained files; artifact verification does not certify
test adequacy or a successful hosted submission.

GitHub's actual generated Dependency Graph submission remains pending until
the manifest reaches main. The issue stays open for that verification. The
[original failure](https://github.com/bmdhodl/agent47/actions/runs/37109111613)
cannot be retried; successful SDK-directory scans do not validate this directory.
Workflow files, repository security settings and provider locks are unchanged.

Sign-off: OpenAI | GPT-6 | auto.
