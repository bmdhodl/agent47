# Site design: the handler

Design rules for agentguard47.com. The landing page follows all of them; the
other pages share the tokens and components.

## Premise

Every agent gets a handler. AgentGuard is a quiet professional assigned to a
runaway agent: it watches the tool calls, it steps in on the exact call that
crosses the line, and it leaves a receipt. The page reads like a case file on
that job, not a product brochure.

Three words for every decision: **silent, precise, accountable.**

- Silent: black, lots of space, few words, nothing moves unless it means
  something.
- Precise: numbers, exact commands, exact exception names, hairline rules.
- Accountable: every claim has a receipt, a test, or a stated limit.

## Voice

- Short declarative sentences. Second person. Present tense.
- Labels may be in character: "Case file", "Rules of engagement", "Evidence".
  Claims may not. A claim says exactly what the code does:
  "the next call raises `BudgetExceeded`", never "eliminates runaway costs".
- Verbs for what AgentGuard does: stop, refuse, raise, record. Never kill,
  eliminate, terminate, destroy.
- No hype: no "powerful", "seamless", "blazing", "revolutionary",
  "game-changing", "supercharge", "unlock". The slop scan must score 0.000.
- State limits in the same voice as features. "Rules of engagement" is where
  the page says what AgentGuard will not do.

## Palette

| Token | Value | Use |
| --- | --- | --- |
| `--suit` | `#0b0b0c` | Page background. |
| `--suit-2` | `#141315` | Code blocks, raised surfaces. |
| `--shirt` | `#f2eee6` | Body text and headlines. |
| `--paper` | `#ebe5d8` | Receipts and dossier paper. |
| `--ink` | `#1a1718` | Text on paper. |
| `--tie` | `#b3121d` | The one accent: stops, the primary action, the rule under a kicker. |
| `--tie-bright` | `#ea4049` | Red text on black: 5.0:1 on `--suit`, 4.7:1 on `--suit-2`. |
| `--steel` / `--steel-dark` | `#a39c95` / `#8a827c` | Secondary text, metadata. Both pass 4.5:1 on black. |

Red is rationed. On any screen, red marks at most: the stop, the action, and
one headline accent. If everything is red, nothing is a stop.

## Type

- Headlines: Archivo, condensed (`wdth` 62-72), weight 850-900, uppercase,
  tight leading (0.88-0.92). Large enough to feel like a stencil on a crate.
- Body: IBM Plex Sans 17px / 1.6.
- Data, labels, commands: IBM Plex Mono. Labels are 11-12px uppercase with
  0.14em tracking.
- Numbers that matter (a limit, a count) are set in the mono face, large.

## Motifs

1. **Barcode.** The mark, the section divider, and the receipt's hash. Bars
   are generated from a real SHA-256, never random.
2. **Crosshair.** A thin ring and tick marks placed over the one thing that
   was stopped. Used once per page.
3. **Stamp.** "STOPPED" in red, rotated a few degrees, heavy border. Applied
   only to things that were actually refused.
4. **Redaction bar.** A black bar over text that the reader does not need,
   used to show a trace's private fields are not collected. Decorative text
   only; never hide something the reader needs to read.
5. **Case file.** Paper cards with a mono header row (`FILE 01 · LOOP`), a
   one-line profile, and the evidence underneath.

## Components

- `.kicker`: red 28px rule, then a mono uppercase label.
- `.dossier`: paper card, ink text, mono header row, 1px ink rule.
- `.stamp`: red, 3px border, rotated -6deg, mono uppercase.
- `.crosshair`: CSS-only ring with four ticks, absolutely positioned.
- `.barcode`: inline SVG from a hash; `aria-hidden`.
- `.receipt`: the real output of `agentguard receipt`, set in mono on paper
  with a torn bottom edge.
- `.rules`: numbered list of limits, each with a plain-language consequence.

## Landing page order

1. **Top bar.** Barcode mark, wordmark, five links.
2. **Hero.** Kicker, headline, one-line lead, install line, the receipt.
3. **Case file.** Four targets (budget, loop, retry, time), each a dossier
   card with the exception name and a one-line example.
4. **Three ways in.** Claude Code hook, `agentguard run`, patch the client.
   One command each. Commands that ship after the current PyPI release are
   labeled with their version.
5. **Evidence.** The receipt explained: stops, recorded cost, trace hash.
6. **Rules of engagement.** What it does not do, linked to the tested limits.
7. **For teams.** Hosted dashboard, one line, two buttons.
8. **Footer.**

## Motion

- One entrance: the stamp lands on the receipt (scale 1.4 to 1, 180ms) when
  the hero loads.
- Nothing loops. Nothing parallaxes.
- `prefers-reduced-motion: reduce` removes all of it.

## Layout

- 1120px max content width, 20px side gutters, 12-column thinking but mostly
  two columns: a narrow label column and a wide content column.
- Hairline rules (`--rule`) between sections instead of cards and shadows.
- Works at 375px with no horizontal scroll. Checked at 375, 768, 1440.

## Do not

- Use any game studio's names, logos, characters, weapons, or screenshots.
  The references are black suit, white shirt, red tie, barcode. That is all.
- Use gradients, glass, glows, emoji, pill badges, stat cards, testimonial
  carousels, or stock photos.
- Show a number the product did not produce. Receipts on the page are real
  command output with the version printed on them.
- Claim invoice caps or host-wide interception. See
  [enforcement boundary](enforcement-boundary.md).

## Accessibility

- Text contrast 4.5:1 minimum, including red and grey on black.
- Every decorative SVG is `aria-hidden`; the receipt figure has an
  `aria-label` that says what it shows.
- Focus ring: 2px `--tie-bright`, 3px offset.
- Visible, real text for every command so it can be selected and copied.
