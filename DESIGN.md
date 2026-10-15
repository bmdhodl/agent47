---
name: BMD
design_version: "1.0.0"
description: One human-first design family for websites, apps, email, reports and media.
colors:
  background: "#0a0a0a"
  surface: "#161616"
  raised: "#222222"
  border: "#525252"
  control-border: "#737373"
  text-primary: "#f5f5f5"
  text-secondary: "#b8b8b8"
  accent: "#FF8200"
  on-accent: "#111827"
  success: "#34d399"
  warning: "#fbbf24"
  danger: "#f87171"
  light-background: "#ffffff"
  light-surface: "#f8fafc"
  light-border: "#cbd5e1"
  light-control-border: "#64748b"
  light-text: "#111827"
  light-secondary: "#475569"
  light-link: "#B45309"
typography:
  display:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "3rem"
    fontWeight: "600"
    lineHeight: "1.15"
  h1:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "2rem"
    fontWeight: "600"
    lineHeight: "1.2"
  h2:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: "600"
    lineHeight: "1.3"
  h3:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "1.125rem"
    fontWeight: "600"
    lineHeight: "1.4"
  body:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "1rem"
    fontWeight: "400"
    lineHeight: "1.6"
  secondary:
    fontFamily: "ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif"
    fontSize: "0.875rem"
    fontWeight: "400"
    lineHeight: "1.5"
  mono:
    fontFamily: "'JetBrains Mono', ui-monospace, 'SFMono-Regular', Consolas, monospace"
    fontSize: "0.875rem"
    fontWeight: "400"
    lineHeight: "1.6"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  2xl: "48px"
  3xl: "64px"
rounded:
  none: "0px"
  sm: "4px"
  md: "8px"
motion:
  feedback: "150ms"
  transition: "220ms"
  easing: "cubic-bezier(0.2, 0, 0, 1)"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.on-accent}"
    rounded: "{rounded.sm}"
    padding: "12px 20px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "{spacing.lg}"
  email:
    backgroundColor: "{colors.light-background}"
    textColor: "{colors.light-text}"
    padding: "{spacing.lg}"
---

# BMD design system

## Overview

Design for the person who must understand, decide and act. A person should
recognize the purpose, current state and next action without an explanation.
Human comprehension is the acceptance standard. AI can use the same interface;
accessible semantics support both people and automation.

One BMD family shares this rubric and its tokens. Websites, desktop apps,
emails, reports, graphics and videos adapt to their medium. A matching palette
alone is not compliance. Keep the interface simple, clear and calm, with orange
as the recognizable BMD accent.

This is the canonical current standard, adopted 2026-10-15. Local product
documents describe implementation and medium constraints, not competing rules.
Versioned copies and generated tokens must match this source. An exported copy
does not certify the rendered product. Historical releases keep their history.

## Colors

Websites and apps default to dark neutrals; email defaults to a light surface.
Use the named tokens above, not independently maintained palettes.

- Separate canvas, surface and raised content visibly. Use the stronger control
  border when a boundary is needed to identify an input or control.
- Orange emphasizes the primary action and selected state. Do not color every
  heading, label or link alike. Body text remains neutral.
- Orange buttons use dark text. Light-surface text links use `light-link` and an
  underline. Brand orange on white and white on brand orange fail normal-text
  contrast and must not be used for that purpose.
- Status combines a label or icon with color. Success, warning, error and unknown
  must remain distinguishable without color. Unknown never becomes zero or success.
- Meet WCAG 2.2 AA: normal text at least 4.5:1, large text 3:1, and essential
  control boundaries and state indicators 3:1 against adjacent colors.

## Typography

System sans-serif is the default across prose, headings, labels and controls.
Use 16px body text and 14px secondary text at default zoom. Email uses equivalent
inline pixel values with Arial/sans-serif fallbacks. Do not shrink text to fit.
Responsive headings may scale down while keeping the hierarchy clear.

Reserve monospace for code, commands and technical values. Use sentence case;
remove decorative `$` prefixes, tracked uppercase labels and redundant eyebrows.
The brand wordmark may retain its established treatment. A static renderer may
use its bundled readable sans-serif when a system font is unavailable.

Keep paragraphs short, left aligned, and generally within 45-75 characters per
line on wide screens (66ch default). Narrow screens reflow naturally. Lists and
data tables follow the task; do not force them into prose dimensions.

## Layout

Lead with purpose, the useful result or state, and one clear primary action.
Show the information needed for a decision before optional background. Use
progressive disclosure for methods, logs and advanced options. Never collapse
essential warnings, failures, consent or the consequences of an action.

Group by task and relationship. Space between groups must exceed space within
them. Use headings, distinct surfaces and visible separators to make boundaries
clear. Avoid nested panels and turning every paragraph into a card.

Default to 24px panel padding, 16px on narrow screens, and 32-64px between major
sections. A content region generally caps at 1200px; email caps at 600px. Keep
body copy at a reading width even within a wider application.

Navigation names the user's tasks. Preserve useful direct paths and product
behavior. Secondary actions should not compete with the primary action.
Do not add dashboards, settings or layers to explain implementation internals.

## Elevation & Depth

Use space and a clearly brighter surface for raised content. Borders distinguish
regions where whitespace alone is insufficient. A restrained shadow is allowed
for an overlay when it makes layering understandable; decorative glow is not a
substitute for grouping. Keep text and essential controls clear in every state.

## Shapes

Use 4px rounding on controls and 8px on panels by default. Square data tables and
media frames remain valid. Use one treatment per role. Icons may aid recognition;
give actionable icons accessible names and visible labels where meaning is unclear.
Do not require a new icon library to use a useful existing icon.

## Components

**Actions and inputs:** use clear verbs and visible labels. Give controls visible
keyboard focus, a usable hit area (44px default), loading feedback, and clear error
recovery. Explain a relevant unavailable action rather than making it disappear.
Hide actions that do not apply. Preserve values when validation fails.

**Results and reports:** show the outcome, what needs attention and next action
first. Details remain available. Tables support actual comparison; cards group
related content. Avoid repeated summaries of the same fact.

**Motion:** use the short duration tokens for feedback and state transitions.
Animate only when it explains a change or helps orientation. Honor reduced motion,
provide controls for persistent movement, and keep content usable with motion off.
Avoid scroll hijacking, pointer tilt, flashing and automatic repeated entrances.

**Video and diagrams:** show an actual task and result. Prefer real product
footage with concise callouts; animated explanations may clarify invisible steps.
Never imply simulated footage is a captured product run. Make the outcome apparent
in the first five seconds. Use user-initiated playback, a useful poster, controls
and deferred loading. Keep an equivalent explanation available without playback.
Use captions/transcripts for speech and describe important visual-only information.
SDR is the default; HDR and code-built scenes are optional production methods.

**Email:** readable sans-serif, 16px body, 14px supporting text, light background,
clear sections, one primary action, inline styles and meaningful text when images
are blocked. Links remain links, including button-styled anchors. Use a linked
video poster rather than an embedded player. Transactional mail need not carry
newsletter branding or an unrelated reply question. Preserve consent, unsubscribe
and delivery behavior.

**Static graphics:** labels must be readable at the actual embed size, including
phone width. Offer a narrow layout or accompanying text if a wide diagram cannot
remain readable. Retain factual-claims and geometry checks. Do not treat a minimum
font size in the source canvas as proof of legibility after scaling.

## Do's and Don'ts

- Reduce compulsory reading. Remove duplication before adding decoration.
- Use a visual when it communicates better than prose, not to meet a media quota.
- Preserve real product behavior, truthful status and evidence behind claims.
- Test full flows and default, loading, empty, success and error states.
- Check 375/768/1440 widths, keyboard use, zoom, focus, contrast and reduced motion.
- Review email in Gmail, Outlook and Apple Mail with images on and blocked. Browser
  screenshots are preliminary evidence, not inbox-client proof.
- Keep public copy direct, factual and free of em dashes. Follow the publication's
  separate voice and approval rules.
- Record visual review and human comprehension separately from automated checks.
  Missing evidence remains untested; token parity alone is never a visual PASS.
- Apply to all new and changed human-facing work. Track remaining maintained
  surfaces in existing project queues. Do not silently reactivate retired work.

## Evidence and acceptance

Review related reference surfaces together before broad component propagation:
homepage, one tool/result flow, Queues/Status, newsletter, transactional email and
one real product demo. A human reviewer must be able to identify purpose, state
and next action without coaching. Record who reviewed what and the actual result.
Automated checks, agent critique and human review are distinct forms of evidence.

This standard supersedes earlier blanket square-corner, monospace-prose,
near-invisible-boundary, icon, layout-count and hover-motion bans. It also replaces
mandatory code-only, silent, fixed-aspect and HDR demo production. Accessibility,
truthful demonstrations, privacy, factual QA and release gates continue to apply.

Research checked 2026-10-15:

- [Google DESIGN.md format](https://github.com/google-labs-code/design.md): tokens
  plus rationale; format validation does not measure usability.
- [Google expressive design research](https://design.google/library/expressive-material-design-google-research):
  hierarchy and containment should help people find and understand important content.
- [Google typography guidance](https://web.dev/learn/design/typography) and
  [W3C clear page structure](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o2p03-page-structure/).
- [Video performance](https://web.dev/learn/performance/video-performance),
  [motion controls](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html),
  and [email video constraints](https://mailchimp.com/help/add-video-to-an-email/).
