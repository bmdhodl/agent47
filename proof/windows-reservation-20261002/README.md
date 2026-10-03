# Published 1.4.0 Windows reservation check, 2026-10-02

The existing reservation examples ran on Windows with Python 3.11.9 and the
published `agentguard47==1.4.0` wheel. Two spawned processes shared one local
`JsonFileStateStore` key and `max_calls=1`: one simulated call dispatched and
the other was refused before dispatch. Both processes exited 0. Completed
calls left one settled call, zero reserved calls and zero unresolved calls.

| Copied example | Repeats | Result per run |
|---|---|---|
| `reserved_one_dispatch.py` | 2 | 1 dispatch, 1 blocked, spawn |
| `reserved_stream_dispatch.py` | 2 | 1 stream dispatch, 1 blocked, spawn |
| `shared_call_limit.py` | 2 | 1 dispatch, 1 stopped through public `patch_openai`, spawn |
| `two_worker_overshoot.py` | 2 | 2 dispatches, 2 recorded calls, 1 consume refusal |

The in-memory `check()` / `consume()` example still overshoots. It uses two
threads, not the process-shared reservation path. That control confirms the
proof does not imply all budget paths reserve before send.

## Artifact and execution

`receipt.json` records the installed origin, wheel hash, operating system,
Python version, example checkout-byte hashes, parsed results and public stdout
hashes. Installation started in a fresh environment where AgentGuard was
absent. The wheel SHA-256 equals the official PyPI 1.4.0 JSON metadata digest.
The installed `direct_url.json` archive hash equals that same wheel digest;
the module origin was asserted to be inside that environment's `site-packages`.
Every requirement was marked for an optional extra: no runtime dependency
was installed with the base wheel.

The four examples were copied byte-for-byte from main
`b4d0b61a4601b7ce372016f09cd3c7127df12b29` to a directory outside the checkout.
Each execution used that environment's `python -I`, with provider and owner
credential variables removed. No repository conftest or source path was used.
The three reservation examples create a fresh temporary store on each run.

To repeat on a fresh Windows/Python 3.11 environment, copy the four named
examples outside the checkout and use the environment's Python:

```powershell
python -I -m pip --isolated install --index-url https://pypi.org/simple --no-deps --only-binary=:all: "agentguard47==1.4.0"
python -I reserved_one_dispatch.py
python -I reserved_stream_dispatch.py
python -I shared_call_limit.py
python -I two_worker_overshoot.py
```

Run the last four commands twice. `before-install.txt`, `download.txt`,
`install.txt`, `versions.txt` and the eight example logs retain the completed
execution output. Public copies normalize line endings to LF, strip terminal
trailing whitespace and replace local installation paths with `[PROOF_ENV]`.
Their hashes in the receipt refer to those public copies. Raw local output is
retained separately.

The public source-suite log also replaces absolute and relative pytest
checkout prefixes with `[REVIEW_CHECKOUT]`. Its relative node paths were
redacted after Codex review; test output and counts were unchanged. The proof
bundle was checked again for user paths and the local checkout basename.

## Limits

These providers are simulated. The stream example invokes the existing
instrumentation wrapper directly; the shared-call example exercises the
public patch function with an OpenAI stand-in. No real provider request or
paid call occurred. This checks local Windows locking and dispatch behavior,
not real provider-version compatibility, cross-machine coordination, an
invoice cap, or every Windows/Python/filesystem combination. Two repeats are
a spot-check, not a contention stress test or crash-recovery proof.

The earlier Linux proofs remain historical evidence. This adds the Windows
slice from `ops/FOLLOWUP.md`; it does not close #736, promote optional surfaces,
publish a release, or supply outside-user observations for #746/#737.

The current-source SDK suite ran separately on Windows/Python 3.13.2: 1396
tests passed with three optional Agents skips, zero warnings and 92.27%
coverage (`sdk-tests.txt`). The published-wheel examples above used Python
3.11.9. Configured lint,
security, docs, release checks and all 11 MCP tests passed (`checks.md`).

Sign-off: OpenAI | GPT-6 | auto
