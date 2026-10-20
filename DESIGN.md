---
name: BMD
design_version: "1.2.0"
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

## Brand mark

Use the approved BMD loop mark everywhere BMD identifies itself: one unbroken
ring with three square stations. Build at the top is orange; Manage and Deploy
are neutral. The 2026-10-17 mark replaces PH, bp and node-triad logos. Keep
product names alongside the shared mark; do not invent a logo for each surface.

- For vector marks and generated app icons, reuse the existing two masters:
  the pixel-fitted 16-unit master at 16-63px and the optically centered 24-unit
  master at 64px and above. Email and raster media may scale the approved 512px
  tile; check its legibility at the actual display size. Do not redraw,
  distort, crop, rotate or animate the logo geometry. Orange background particles
  remain separate and retain their established motion.
- Default colors: ring `#e5e5e5`, Build `#FF8200`, other stations `#a3a3a3`,
  tile `#0a0a0a`. Use the approved paper palette or the dark tile on light
  surfaces. Keep clear space on each side equal to at least one sixth of the
  mark's box width (4 units on the standard master). The approved small favicon
  may fill its 16-unit tile to preserve legibility; don't add padding to it.
- Website: shared header/home link, favicon/app icons and social preview.
  Desktop: app chrome, launcher icon, About and startup/recovery screens.
  Email: one header or footer mark with readable sender text when images fail.
  Graphics: a consistent brand position outside the information area. Video:
  the same mark on the poster and a brief end card or unobtrusive signature;
  never delay the useful demonstration with a logo intro.
- Decorative marks next to the visible name have empty alternative text. A
  logo-only home link has a useful accessible name. At actual phone/embed size,
  keep the mark recognizable and all content clear; don't use a watermark over
  controls, data or captions.
- Pin copied assets or generated geometry in implementation tests. The approved
  512px dark tile is `bmd-loop-mark-512.png`, SHA-256
  `362d797dd2920fadda6ae91488143780ba6ca2951aefedda3d71061de3a3c1cc`.
  Existing product implementation notes own asset paths and generators. New
  and revised media use this mark; published historical assets stay historical.

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

### Reading budget

Use word budgets, not a text-to-image percentage. The guidance cited below does
not establish a universal percentage; viewport, page purpose and content change
what the ratio means. These are BMD editorial defaults, not research thresholds
or WCAG requirements. Less is welcome; never add copy to reach a target.

| Marketing surface | Default budget |
|---|---|
| Homepage or landing page | Aim for 250-400 default-visible words total |
| Hero, including heading, support and actions | At most 40 words |
| Supporting section introduction | At most 60 words, one main point |
| Card supporting copy | At most 20 words |

Lead with the customer benefit: time saved, cost avoided or a useful result.
Claims about savings or revenue need evidence. Show the working path with a
useful demo, diagram or comparison when it explains faster than prose. Keep the
established orange background motion; visuals do not need a percentage quota.

Count authored, default-visible main content, including headings, control labels
and captions. Exclude repeated site navigation/footer and dynamic data records;
record expanded content separately. The page total includes its sections and
cards. Never fit a budget by shrinking text, removing necessary labels, hiding
essential warnings or baking text into images. Keep paragraphs below 50 words
where practical and put their point first.

Apps and result flows lead with the outcome, state and next action; keep task
data and necessary instructions available. Documentation, articles, reports,
newsletters and legal content do not inherit the marketing-page cap. Use a short
summary and clear sections. Email must still make sense with images blocked.

When changing a surface, record its type, visible word count and counting method
in the existing task or PR. Explain any budget overrun by the user's task. Review
the rendered layout at 375/768/1440 and check comprehension separately: a word
count cannot prove that a page is clear, useful or visually engaging.

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
Preserve established brand motion, including the website's swirling orange-dot
background. Ambient animation can express the identity and make a surface feel
alive. Improve readability and grouping while retaining that visual character.
Keep moving artwork behind the content, with readable text, clear controls and
visible boundaries. Honor reduced motion, provide a pause control for persistent
movement, and keep content usable with motion off. Pause background rendering
when it is offscreen or the page is hidden. Avoid scroll hijacking, pointer tilt,
flashing and automatic repeated entrances. Background motion and user-controlled
product video serve different purposes; retain both where established.

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

The 2026-10-19 motion clarification preserves the established orange particle
background alongside the readable layout. A simpler interface keeps its approved
visual identity; it does not require a static, text-only presentation.

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

Reading-budget guidance checked 2026-10-19:

- [W3C succinct text](https://www.w3.org/WAI/WCAG2/supplemental/patterns/o3p05-succinct-text/):
  short, focused chunks; consider splitting English paragraphs over 50 words.
  This is supplemental accessibility guidance, not a mandatory WCAG word limit.
- [Google expressive design research](https://design.google/library/expressive-material-design-google-research):
  hierarchy, grouping and motion support comprehension; removing needed action
  labels can harm usability. BMD's page and component budgets are house defaults.
