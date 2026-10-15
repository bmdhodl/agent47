# Maintenance capability and background-process evidence

Checked 2026-10-15 on Windows / Python 3.13.2. This is boundary evidence,
not a process supervisor, account quota cap, or package release.

## Behavior

`python examples/enforcement_boundary/background_child.py` starts a Python
parent through the actual `agentguard run --budget-usd 0.01` runner. The parent
starts a separate uninstrumented interpreter and exits without joining it.
Only after observing that parent's exit does the controller release the child.
The child then writes two simulated dispatches and exits. There are no provider
or network calls. Explicit inherited pipes let the controller drain the child
before removing its own temporary directory; a bounded child wait and stop
marker also cover a failed controller path. No unrelated process is stopped.

The new regression failed before the reproduction existed (`background-red.txt`).
It then passed. An initial local implementation did not explicitly pass the
Windows output handles to the child and failed cleanup; the final version does.
Independent review also found inherited AgentGuard sink settings could escape
the scratch directory or initialize remote ingest. A poisoned trace-destination
regression failed (`env-regression-red.txt`); the example now strips all
`AGENTGUARD_*` variables and explicitly puts its trace inside the owned scratch.
A synthetic-key regression blocks DNS and socket connections before they can
reach the network and confirms remote ingest is never initialized.
This does not reproduce a provider bill or independently verify the reported
Bedrock incident. It establishes that a parent guard does not supervise children.

## Validation

- Focused boundary, daily persistence, shared-store preflight and reservation
  tests: 78 passed, exit 0. This includes restart persistence and concurrent
  admission on the existing covered store-backed paths.
- Initial full SDK: 1612 passed, 3 optional skips, 92.54% coverage, exit 0.
  Raw output: `sdk-suite.txt`.
- After the independent environment-isolation repair: **1614 passed, 3 optional
  skips, 92.54% coverage**, exit 0 (`sdk-final.txt`). The replayable boundary
  checks pass 4/4, including both poisoned-environment regressions.
- Structural: 9 passed, exit 0 (`structural.txt`).
- Ruff and Bandit: exit 0 (`lint.txt`, `security.txt`).
- Release metadata guard: exit 0 (`release-guard.txt`). No version bump or tag.
- MCP TypeScript build/tests: 11 passed, exit 0 (`mcp.txt`).
- Review-readiness and CI-tools requirements guards: exit 0.

The capability matrix corrects the single-run-only claim: SDK daily persistence
and configurable 80% warnings already exist. Monthly SDK budgets and automatic
tree inheritance remain deferred. The unpublished Python MCP sibling's monthly
budget is cooperative. Generic Codex tools and subscription quotas are outside
the current interception boundary.

`agentguard receipt` remains stable. A stop receipt records a covered refusal
and trace hash; it does not sign or attest that record. Anthropic's `/receipts`
summarizes historical work. Google documents a project-level spend cap.

CI, independent review, merge, production state, and any future package release
remain separate checks. No active user hook settings were changed.

Sign-off: OpenAI | GPT-6 | auto.
