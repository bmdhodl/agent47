---
name: next-ticket
description: >
  Pull and ship the next AgentGuard weekly ticket when the owner says
  "next ticket", "work the next ticket", "pull the next ticket", or
  "you are my lead". Open a ready PR, get Bugbot and Copilot to QA it,
  use a different model if those two are out of usage, fix real review
  issues, merge, then explain what shipped and why in a few words with
  one scenario and a few lines of code.
---

# Next ticket

You are the lead senior engineer. Do this once, then stop. Do not start another ticket in the same turn.

The owner saying "next ticket" is the selection. The `planning-only` label does not block that.

## 1. Pull the next ticket

Planning authority is [GitHub #729](https://github.com/bmdhodl/agent47/issues/729) and [Project 4](https://github.com/users/bmdhodl/projects/4). `ops/03-ROADMAP_NOW_NEXT_LATER.md` is a view, not a second queue.

```bash
gh issue list --repo bmdhodl/agent47 --state open --label roadmap:2026-weekly --limit 50
```

Take the first open ticket in the newest ordered sequence table in #729 (for example "Adoption sequence updated September 24"). Only if #729 has no such table, take the lowest open `AG-` issue. Skip any ticket that #729, the ticket, or a linked issue marks held, conditional, or blocked on an unmet gate; AG-06 (#735) stays held per #767. Read that issue before coding.

If the next ticket's acceptance needs outside people (testers, posts, replies) that an agent cannot produce, ship only the repo-side slice the ticket names and tell the owner what is still theirs. Also read `memory/`, `ops/00-NORTHSTAR.md`, `ops/03-ROADMAP_NOW_NEXT_LATER.md`, `ops/04-DEFINITION_OF_DONE.md`, and `ops/FOLLOWUP.md`.

Stay inside the ticket. The SDK stays MIT and zero-dependency. No paid features, no dashboard work, no new public export, and no release tag unless the ticket says so.

## 2. Ship it

Work on a branch off `main`. Open the PR ready for review. Never open a draft.

Follow the repo's existing proof rules: tests, `showwork` claims, and a short PR body with the command output.

## 3. QA

Ask Bugbot and Copilot to review the open PR. Wait until each one has either a real review or an explicit skip.

A usage-limit, quota, or "couldn't run" comment is a skip, not a code defect. Do not reply to each repeat of that skip.

If both Bugbot and Copilot skipped, send the diff to a model other than the one that wrote the PR. Ask that model only for bugs, security problems, and broken behavior. Do not review your own diff with the same model.

For every real review comment:

- Fix it when it is a real bug or a misleading contract.
- Reply with the file and the reason when it is already handled.
- Resolve GitHub review threads after the fix is on the branch.
- Do not push an empty change just to retrigger a comment that is already answered.

## 4. Merge

Merge after the checks that ran are green and the review comments are answered.

If GitHub still requires an approving review and this login cannot override it, stop and give the owner the PR link. Say that the merge button is theirs. Do not claim the PR merged.

## 5. Tell the owner

After the merge, use a few words. Include all four:

1. What it did.
2. Why, as one scenario a person can picture.
3. A few lines of the code that do the important part, with one sentence each.
4. What it still does not do, if that would mislead someone.

Example shape:

```text
What: Two workers that share one saved budget can no longer both spend the last OpenAI call.
Why: One call is left. Both workers look at the same moment. Both would have sent. Now the first claims the call, and the second stops.
Code: reserve_for_dispatch(...) writes the hold before the provider is called.
Still open: streaming, Anthropic, and in-memory budgets do not reserve.
```

Then stop.
