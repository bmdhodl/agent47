# Claude Code hook

`agentguard hook claude-code` runs as a Claude Code command hook. It refuses
four kinds of tool call before they run:

| Stop | Default | Set with |
| --- | --- | --- |
| The same call, with the same input, again and again in a row | third in a row is refused | `loop_max` in `.agentguard.json` |
| A call that already failed, tried again unchanged | refused after 2 failures | `retry_max` in `.agentguard.json` |
| One tool that keeps coming back empty, or with the same error, while the input is reworded | off | `no_progress_max` in `.agentguard.json`; set an integer of at least `2` to opt in, `0` to turn it off |
| Any call past a per-session count | off | `--max-calls N` |

`loop_max` and `retry_max` come from the `coding-agent` profile. Edit, test,
edit, test is not a loop: only calls with nothing between them count.

"The same input" ignores JSON key order and Bash's descriptive label. Case
and whitespace in values stay exact: paths, code indentation, search patterns,
and quoted shell literals can change meaning when those characters change.

The opt-in empty-or-same-error rule counts results rather than repeated inputs.
For example, `{"no_progress_max": 5}` enables it after five matching results:

- Empty means no matches, such as Grep or Glob reporting zero files, or an
  empty list or string. A command that succeeds quietly, like `mkdir`, is
  progress, not empty.
- Two errors are the same after case, whitespace, digits, and the words of the
  call's own input are masked. `cat: a.log: No such file` and
  `cat: b.log: No such file` match.
- Any other result in between, from any tool, starts the count over. So does
  a user interrupt. After a refusal, the agent can use another tool, and the
  next result from that tool resets the count.

When a call is refused, the hook exits 2. Claude Code blocks the call and shows
the reason to the model, for example:

```text
AgentGuard refused Bash: the same call just ran 2 times in a row
(limit 2). Change the input or the approach.
```

```text
AgentGuard refused Grep: Grep came back empty the last 5 times in a
row, even with changed input (limit 5). Rewording the call is not working; try
a different approach or report to the user.
```

## Install

Installation requires **Claude Code 2.1.295 or later**. The installer checks
`claude --version` before either a preview or a write. An old, missing, or
unrecognized version stops installation without changing settings. Run the
installed hooks with that same supported Claude Code installation; the check
does not protect against a later host downgrade or a different executable.

Preview the settings, then write them:

```bash
agentguard hook claude-code --install
agentguard hook claude-code --install --write
```

This adds one handler to `PreToolUse`, `PostToolUse`, and `PostToolUseFailure`
in `.claude/settings.local.json`. Existing hooks and settings are kept. The
handler runs the Python interpreter that installed AgentGuard, so the file is
per-machine. Keep it out of git: add `.claude/settings.local.json` to
`.gitignore` if your repo does not already ignore it.

Add `--max-calls 300` to the install command to also cap tool calls per
session.

Remove it with:

```bash
agentguard hook claude-code --uninstall --write
```

Only AgentGuard's handlers are removed.
Removal does not require Claude Code to be installed.

## Hook failures

The generated synchronous `PreToolUse` command handler sets
`"onFailure": "block"`. On a supported Claude Code host, a missing executable,
crash, timeout, or rejected JSON output blocks the pending tool call. An
intentional guard refusal still exits 2. A normal allow exits 0.
The post-tool handlers record results after the action and do not get this
setting. AgentGuard does not install background policy handlers.
Plain-text stdout is not a host failure. For example, an incomplete `{invalid`
line is treated as text; `onFailure` cannot turn arbitrary stdout into a deny.

Reinstall to update an existing AgentGuard hook. Existing installations do not
gain failure blocking merely from an SDK upgrade. Review the preview before
`--write`; unrelated settings and hook handlers are preserved.
See the [official Claude Code failure behavior](https://code.claude.com/docs/en/hooks#block-the-action-when-a-hook-fails).

## What it writes

- `.agentguard/claude-code/sessions/<session id>.json`: counts for one Claude
  Code session. Each hook call reads only its own session file, and a lock
  keeps parallel tool calls from losing counts.
- `.agentguard/claude-code/trace.jsonl`: one event per allowed call and per
  refusal. Refusals record the tool name, rule and counts. Raw input keys and
  values are omitted from receipts and labels, since commands, URLs, paths
  and nested values can contain credentials. Original arguments are used
  in memory for matching, not copied into the trace.
- `.agentguard/claude-code/.gitignore`: ignores the directory, so none of this
  is committed by accident.

Print what it refused:

```bash
agentguard receipt .agentguard/claude-code/trace.jsonl
```

## Limits

- The no-progress rule is off by default. When enabled, it may refuse a
  different recovery command from the same tool after repeated failures.
  Choose a threshold for your workflow and keep it off for unrestricted
  diagnostic work. SDK `LoopGuard(max_no_progress=N)` is also opt-in.
- It checks tool calls that fire `PreToolUse`. It does not see model tokens,
  work inside a subagent's own process, or your subscription quota.
- It counts per session. A new session starts at zero.
- Legacy handlers without `onFailure: "block"`, unsupported hosts, and disabled
  hooks can let a call proceed after a hook failure. Only the generated
  synchronous pre-tool handler on a supported host requests failure blocking.
- A user can remove or edit the hook. It is a guardrail, not a sandbox.
- Native Claude Code 2.1.296 on Windows passed an offline scripted-model
  check with five actual Bash failure payloads: the default allowed a recovery
  command; opt-in `no_progress_max: 5` refused it. The payloads and marker
  evidence are in `proof/pr869-maintenance-20261015/native/`. Actual empty
  Grep/Glob payloads, live provider use and macOS remain untested. Earlier
  Linux host proof used Claude Code 2.1.283.
- Native Claude Code 2.1.296 on Windows was exercised with a loopback scripted
  model fixture: allow, intentional refusal, missing executable, crash,
  timeout, malformed JSON object, and schema-invalid JSON. The first tool ran;
  all six blocked cases left its marker absent. Evidence:
  [offline host acceptance](../../proof/hook-failure-20261015/README.md).
  This did not test a paid provider, an active user profile, or macOS/Linux.

Where this sits among the other paths:
[enforcement boundary](../enforcement-boundary.md).
