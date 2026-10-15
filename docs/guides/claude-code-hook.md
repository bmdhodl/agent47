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
- Legacy handlers without `onFailure: "block"`, unsupported hosts, and disabled
  hooks can let a call proceed after a hook failure. Only the generated
  synchronous pre-tool handler on a supported host requests failure blocking.
- A user can remove or edit the hook. It is a guardrail, not a sandbox.
- Native Claude Code 2.1.296 on Windows was exercised with a loopback scripted
  model fixture: allow, intentional refusal, missing executable, crash,
  timeout, malformed JSON object, and schema-invalid JSON. The first tool ran;
  all six blocked cases left its marker absent. Evidence:
  [offline host acceptance](../../proof/hook-failure-20261015/README.md).
  This did not test a paid provider, an active user profile, or macOS/Linux.

Where this sits among the other paths:
[enforcement boundary](../enforcement-boundary.md).
