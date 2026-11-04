# Accessibility and legibility audit: Playmaker playtest table

**Standard:** WCAG 2.1 AA | **Date:** 4 Nov 2026 | **Build:** server and link versions (same page)

**How it was tested:** axe-core 4.10.2 (WCAG 2.0/2.1 A and AA plus best-practice rules) on twelve
screens, laptop (1440 × 900) and phone (412 × 915): start screen, table, a pass being chosen, the roll
dialog, the contest decision, the end dialog with feedback, placement, and the Coach's Call target. Plus
keyboard-only navigation, a focus-trap test on dialogs, 200% zoom (720 px), and contrast computed for
every text and graphic colour pair, including SVG court text that axe does not check.
`tests/test_accessibility.py` repeats the key checks on every test run.

## Summary

| | Before | After |
|---|---|---|
| axe violations per screen | 2 to 4 (1 to 2 serious) | **0 on all 12 screens** |
| Colour pairs below the WCAG minimum | 13 | **0** |
| Focus kept inside dialogs | no (escaped after 1 Tab) | yes |
| Escape closes dialogs | no | yes (when the dialog has a cancel) |
| Screen reader name for a piece | "O1" | "O1, Pass-First Point Guard, on I11 (plain wood), has the ball, 68 legal actions" |
| 200% zoom | no sideways scroll | no sideways scroll |

## Findings and fixes

### Perceivable

| # | Issue | WCAG | Severity | Fix |
|---|---|---|---|---|
| 1 | Zone labels on the court (black at 35%) reached only 2.0 to 2.4:1 on every zone colour | 1.4.3 Contrast | 🔴 Critical | Solid ink `#1d1b18`, 10 px: 4.9 to 12:1 |
| 2 | The ball marker (orange) was 1.0 to 2.1:1 against the zones | 1.4.11 Non-text contrast | 🔴 Critical | Larger disc with a 2.5 px dark brown outline (4.4 to 10.8:1) and seams, so it is a shape, not just a colour |
| 3 | Move highlights (light blue) were 1.5:1 on long-two and 1.7:1 on rim squares | 1.4.11 | 🟡 Major | Navy `#0b2a5b` 3 px outline (4.0 to 9.8:1) on a light tile; targets on a piece become a dashed ring so its number stays readable |
| 4 | Lock badges and chips: white on grey at 3.5:1, text 8 px "LK" | 1.4.3 | 🟡 Major | Dark grey `#4a4a4a` (8.9:1), the word LOCK at 9.5 px |
| 5 | Small type: cards 10.5 px (headers 9 px), trackers 11 px, log 11 px | Legibility | 🟡 Major | Body 14 px; cards 12 to 12.5 px (headers 10 px); trackers and log 12.5 px |
| 6 | Whose turn was shown in words only, in the middle of a sentence | Legibility | 🟢 Minor | "OFFENCE TO ACT" / "DEFENCE TO ACT" first, with a white or black side bar |
| 7 | Roll results and moves were not announced to screen readers | 4.1.3 Status messages | 🟡 Major | A polite live region announces each action, roll ("Offence rolls: … rolled 3: success") and the final score |

### Operable

| # | Issue | WCAG | Severity | Fix |
|---|---|---|---|---|
| 8 | Dialogs did not keep focus: Tab escaped to the page behind | 2.4.3 Focus order | 🔴 Critical | Focus is trapped in the dialog; the page behind is hidden from assistive tech; focus returns where it was on close |
| 9 | Escape did not close dialogs | 2.1.1 Keyboard | 🟡 Major | Escape cancels the roll dialog, continues after a roll, closes the end screen; decisions that must be made (Coach's Call target) stay open |
| 10 | Focus on a court piece was a faint ring colour change | 2.4.7 Focus visible | 🟡 Major | A dashed navy halo for keyboard focus, a solid navy halo for the selected piece |
| 11 | After choosing a piece, keyboard users had to Tab past all ten pieces to reach its actions | 2.4.3 | 🟢 Minor | Focus jumps to the piece's first action; after each action focus goes to the actions panel; a "Skip to the actions" link |
| 12 | Phone court squares are about 22 px (under 44 px) | 2.5.5 Target size | 🟢 Minor | Already mitigated: every court choice is also a full-size button on phones |

### Understandable

| # | Issue | WCAG | Severity | Fix |
|---|---|---|---|---|
| 13 | The log repeated "Offence rolls" twice on each roll line | Legibility | 🟢 Minor | The side chip says it once |
| 14 | The browser tab title never changed | 2.4.2 Page titled | 🟢 Minor | "<game or scenario> · Playmaker playtest" |

### Robust

| # | Issue | WCAG | Severity | Fix |
|---|---|---|---|---|
| 15 | The court was `role="img"` with clickable pieces inside, so screen readers could not use them | 4.1.2 Name, role, value | 🔴 Critical | `role="group"` with a description; pieces are buttons with full names, position, zone, ball, screen, arrow, lock, selected state (`aria-pressed`) and the number of legal actions |
| 16 | Dialogs had no accessible name | 4.1.2 | 🟡 Major | Named by their heading |
| 17 | No main landmark on the start screen, no h1 on the table, unnamed and duplicate side landmarks, content outside landmarks | 1.3.1 Info and relationships | 🟢 Minor | `main` on both views, the game title is the h1, "Offence: cards and tracker" / "Defence: cards and tracker", rolls and log in a named region |

Also added: `prefers-reduced-motion` turns off the dice animation; `forced-colors` (Windows high
contrast) keeps highlights visible.

## Colour contrast after the fixes

| Element | Foreground | Background | Ratio | Needed |
|---|---|---|---|---|
| Body text | `#1d1b18` | paper `#f6f1e7` | 15.3:1 | 4.5 |
| Secondary text | `#6b6357` | paper | 5.3:1 | 4.5 |
| Zone labels | `#1d1b18` | long-two `#c8724f` (worst zone) | 4.9:1 | 4.5 |
| Move highlight | `#0b2a5b` | long-two (worst zone) | 4.0:1 | 3.0 |
| Ball outline | `#3a1d00` | long-two (worst zone) | 4.4:1 | 3.0 |
| Lock badge | `#ffffff` | `#4a4a4a` | 8.9:1 | 4.5 |
| ▲ value | `#1d1b18` | `#dfeedd` | 14.3:1 | 4.5 |
| ▼ value | `#1d1b18` | `#f6dcd6` | 13.2:1 | 4.5 |
| Band "Poor" (lowest) | `#1d1b18` | `#d0693b` | 4.7:1 | 4.5 |
| Band "Excellent" | `#ffffff` | `#3d7a4c` | 5.1:1 | 4.5 |
| Focus ring | `#0b2a5b` | white | 14.0:1 | 3.0 |

Colour is never the only signal: zones carry text labels (rim, mid, L2, 3), ratings carry ▲ / ▼,
turn-enders carry "(ends turn)" as well as a dashed border, the side to act is written out, and the
contest options say "clean" or "foul roll" in words.

## Still open (needs people, not code)

1. **Real screen-reader passes** (NVDA on Windows, TalkBack on the Samsung): the names and live
   announcements are in place, but only a real reader shows whether the flow makes sense.
2. **Court overview for screen readers:** a piece-by-piece list is there; a one-line "who is open"
   summary would be a design decision (it would add help, which touches Neutrality).
3. **Why a square is missing** (screen geometry, arrow lines) is still not explained in words
   (open question 44).
