# bmdpat measurement contract (AG-02 follow-up)

Status: specification for the bmdpat site-event store. This public SDK repo
does not implement bmdpat. Do not add SDK telemetry to satisfy this contract.

## Problem

On 2026-09-18 the read-only site-event query counted two events named
`install_intent`. Both targets were the AgentGuard landing page, so **zero of
those events proved a package-install action**. Landing-page navigation never
counts as install or activation.

## Allowed event classes

| Class | Counts as | Allowed targets |
|---|---|---|
| `page_navigation` | View, unique viewer, or CTA click on marketing HTML | `/`, `/index.html`, `/quickstart.html`, `/compare.html`, `/enforcement.html`, `/activation.html`, `/trust.html`, blog posts |
| `install_intent` | Intent to install the package | `https://pypi.org/project/agentguard47/`, copy of `pip install agentguard47` |
| `outbound_docs` | Docs click | GitHub blob/tree URLs under `bmdhodl/agent47` |
| `bot` / `ai_crawl` | Noise | Any; exclude from human totals |

A CTA click on "Run proof in 60 seconds" is `page_navigation`, not install.
Copying the install command **may** be `install_intent` only when the event
payload says the copied text was `pip install agentguard47`.

## Required payload fields

- `event_name`
- `target` (URL or copied text)
- `occurred_at` (UTC)
- `classification` (`human`, `bot`, `ai_crawl`, `unknown`)
- `window` (the calendar query used to retrieve it)

Forbidden: names, emails, IPs, repo paths, trace bodies, subscriber lists.

## Query windows

Use **calendar dates in UTC**, not rolling 24-hour buckets. Label publication
and CI bursts on the same window (GitHub Release days, PyPI publish days,
Actions checkout clones). Report unknowns instead of filling gaps.

## Implementation lane

Change the bmdpat classifier. Keep this document as the source of the rule.
Until that classifier ships, treat every landing-page `install_intent` as
`page_navigation` in the weekly activation report.
