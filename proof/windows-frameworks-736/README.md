# Installed Windows framework evidence for #736

Checked 2026-10-03 against source commit
`9a57ba03950229ed2d970d852a08cc2e966e51b1`. This is a local compatibility
spot-check of existing integrations, with no SDK, CI, dependency-manifest,
public API, release or support-classification change.

Two fresh venvs each ran the same three tests copied directly from that Git
commit's `sdk/tests/test_real_dispatch.py`, outside the checkout. Python ran
with `-I`, plugin autoload was disabled, and `--confcutdir` prevented loading
repository fixtures. `AGENTGUARD_REQUIRE_REAL_DEPS=1` made missing frameworks
fail instead of skip. No provider credentials or model requests were used.

| Profile | Windows Python | LangChain core | LangGraph / checkpoint / SDK | OpenTelemetry API / SDK | Result |
|---|---|---|---|---|---|
| Minimum | 3.10.11 | 1.6.3 | 1.2.11 / 4.2.0 / 0.4.4 | 1.44.0 / 1.44.0 | 3 passed, 0 skipped, 0 warnings |
| Current locked | 3.13.2 | 1.6.5 | 1.2.12 / 4.2.0 / 0.4.5 | 1.45.0 / 1.45.0 | 3 passed, 0 skipped, 0 warnings |

Both profiles ran on the same Windows x64 host, build 26200. Python 3.10
reports it as Windows 10; Python 3.13 reports it as Windows 11. The raw
identity records retain each interpreter's report, not evidence of two hosts.

The named cases prove these behaviors:

- A real LangChain `CallbackManager` propagates `BudgetExceeded` before a tool starts.
- A real LangGraph `StateGraph` invokes a guarded node twice and refuses its next invocation.
- A real OpenTelemetry in-memory exporter receives the expected span and event.

## Installed artifact and dependencies

Both profiles installed the unchanged unpublished candidate wheel retained
here as `agentguard47-1.4.1-py3-none-any.whl`, SHA-256
`b6059abc35fa0892a1dee999b67557c83c2d18986d600c78509ebdd244787684`.
It was reused from the #817 proof, not rebuilt for this check.

All 50 Python modules and `py.typed` matched the source commit's direct Git
blobs after explicit CRLF/LF normalization. All 51 installed package files
and `METADATA` matched the wheel byte for byte. Imports resolved inside the
fresh venv; `direct_url.json` identified the exact local wheel. Python 3.10's
bundled pip 23.0.1 omits an archive hash for local wheels, so the harness checks
the wheel hash independently and verifies every installed package file.
The distribution still declares Python 3.9+ and zero mandatory dependencies.
These framework tests require Python 3.10+; they do not raise the base floor.

Both installs used the unchanged hash-pinned `ci-tools.txt` and the corresponding
compatibility lock from the bound commit. The current lock was compiled for
Ubuntu and omits MCP 2.2.0's Windows-only `pywin32>=311` dependency. Installing
that lock alone on Windows failed with hashes enforced; the original failure
is retained as `current-lock-windows-failure.log.gz` and its command record.

The successful fresh retry additionally used the proof-only
[`windows-platform.lock`](windows-platform.lock), pinning pywin32 312 to the
PyPI hash for its CPython 3.13 Windows x64 wheel. Package metadata and the
artifact hash are retained in `windows-platform-source.json`, from the
[MCP metadata](https://pypi.org/pypi/mcp/2.2.0/json) and
[pywin32 metadata](https://pypi.org/pypi/pywin32/312/json).
The original CI locks were unchanged and hash enforcement stayed enabled.
This supplement is scoped to this profile; it is not a general Windows lock.
Both successful environments passed `pip check`.

## Reproduce

Use a fresh output directory outside the checkout and an existing matching
Windows interpreter. The retained wheel supplies the exact tested artifact.
For the minimum profile:

```powershell
python proof/windows-frameworks-736/run.py --repo . `
  --source 9a57ba03950229ed2d970d852a08cc2e966e51b1 `
  --wheel proof/windows-frameworks-736/agentguard47-1.4.1-py3-none-any.whl `
  --wheel-sha256 b6059abc35fa0892a1dee999b67557c83c2d18986d600c78509ebdd244787684 `
  --python <Python-3.10-executable> --profile floor --output <fresh-scratch-directory>
```

For the current profile, substitute an existing Python 3.13 interpreter,
`--profile current`, and another fresh output directory. The harness retains
commands, exit codes, versions, install logs, source hashes and named JUnit
results. Background subprocesses do not open console windows.

The source SDK suite passed 1,584 tests with three existing optional Agents
skips, zero warnings and 92.56% coverage. Its log and JUnit are retained here
as gzip files; compression preserves their raw bytes while keeping the
independent review diff below its size cap. `verify.py` checks the hashes,
named installed-case results, source-suite counts and recorded check exits
before printing success.
The two installed framework profiles each reject skips, failures, errors,
empty results or a different set of case names. `manifest.json` binds committed
LF text bytes and raw binary proof files; it excludes itself. The verifier
explicitly normalizes Git's LF/CRLF conversion for UTF-8 text only. Compressed
logs and the wheel still require exact binary bytes; installed wheel files also
remain byte-exact. Runtime evidence was generated before
independent review; regenerate it if review changes the harness or tested behavior.

The post-merge checkout regression is retained in `checkout-regression.json`
and its five logs: the original normal Windows checkout failed on a converted
JSON file; the corrected verifier passes both LF and CRLF copies. Altered
README content and altered wheel bytes are still refused. The runtime runner
and original six installed-framework results are unchanged.

`checkout-regression-review-r2.json` and its logs retain the fresh post-review
rerun against the verifier's exact content hash. The LF/CRLF cases record
different raw input hashes and CRLF counts, command paths and UTC times; their
success stdout is intentionally identical. Both corruptions still exit 1.

## Limits

This checks three existing framework dispatch paths on one Windows x64 host
at the stated interpreter/version pairs. It does not establish all optional
extras, every framework API, Windows CI, macOS, live-provider billing, host/MCP
interception or outside adoption. The SDK's base install still needs no extras.
The wheel remains an unpublished 1.4.1 candidate; PyPI remains 1.4.0.

#736 remains open for its remaining compatibility and parent gates. CrewAI
stays experimental under [#644](https://github.com/bmdhodl/agent47/issues/644);
this proof supplies no advisory exception or promotion. Broader adapter work
remains held by the existing owner and adoption decisions.

Sign-off: OpenAI | GPT-6 | auto
