# Claude Code hook

`agentguard hook claude-code` runs as a Claude Code command hook. It refuses
three kinds of tool call before they run:

| Stop | Default | Set with |
| --- | --- | --- |
| The same call, with the same input, again and again in a row | third in a row is refused | `loop_max` in `.agentguard.json` |
| A call that already failed, tried again unchanged | refused after 2 failures | `retry_max` in `.agentguard.json` |
| Any call past a per-session count | off | `--max-calls N` |

Defaults come from the `coding-agent` profile. Edit, test, edit, test is not a
loop: only identical calls with nothing between them count.

When a call is refused, the hook exits 2. Claude Code blocks the call and shows
the reason to the model, for example:

```text
AgentGuard refused Bash(npm test): the same call just ran 2 times in a row
(limit 2). Change the input or the approach.
```

## Install

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

## What it writes

- `.agentguard/claude-code/state.json`: per-session counts, keyed by Claude
  Code's session id. A lock keeps parallel tool calls from losing counts.
- `.agentguard/claude-code/trace.jsonl`: one event per allowed call and per
  refusal. A refusal includes up to 60 characters of the command, path, or URL.
- `.agentguard/claude-code/.gitignore`: ignores the directory, so none of this
  is committed by accident.

Print what it refused:

```bash
agentguard receipt .agentguard/claude-code/trace.jsonl
```

## Limits

- It checks tool calls that fire `PreToolUse`. It does not see model tokens,
  work inside a subagent's own process, or your subscription quota.
- It counts per session. A new session starts at zero.
- Hook input it cannot read is reported as a hook error and the call
  proceeds. It does not fail closed.
- A user can remove or edit the hook. It is a guardrail, not a sandbox.
- Run against Claude Code 2.1.283 on Linux. Windows and macOS were not
  executed.

Where this sits among the other paths:
[enforcement boundary](../enforcement-boundary.md).
