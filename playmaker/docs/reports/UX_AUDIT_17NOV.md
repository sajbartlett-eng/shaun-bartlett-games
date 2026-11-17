# UX, legibility and accessibility audit (17 Nov 2026)

**Built from:** the audit pack (`docs/reports/ux_audit_pack/`), a fresh baseline capture of this branch before any change (`docs/runs/step19/baseline/`, 59 screens, laptop and phone), the running app (server and link versions), a keyboard-only pass, the browser's accessibility tree on the table, 200% zoom, a dark-mode request, forced colours, and Shaun's requests (`docs/reference/SHAUN_UX_REQUESTS_17NOV.md`).

**Severity:** critical (stops someone playing, or misleads them about the game); major (slows or confuses most players in that group); minor (polish).

**Who:** **new** (a first-time player), **phone** (a phone player), **keyboard** (keyboard only), **reader** (screen reader), **all**.

**Stage:** where step 19 fixes it (1 moving and acting, 2 advantages, 3 diagrams and reports, 4 home screen, 5 learning, 6 watching the computer, 7 the rest).

## 1. Usability: from opening the app to finishing a possession

| # | What's wrong | Who | Severity | Fix | Stage |
|---|---|---|---|---|---|
| U1 | **Moving a player takes three choices in three places.** Tap the player, pick Move, Quick Step or Sprint from the buttons under the board, then tap a square. A defender's new arrow is a fourth button. The board and the buttons are far apart on a laptop and a whole screen apart on a phone. | all | major | Tap a player and every square he can reach lights up at once, marked by the movement it takes. Tap a square for a ghost with its arrow, then confirm beside the board or tap the square again. | 1 |
| U2 | **Choosing a pass pushes the board off a phone screen.** Each pass option is three lines of rule text, so the four passes fill 1.5 screens (`phone_15_pass_choice.png`). | phone | major | Turn-ending actions open in a short list under the board, one line each with its chance. The detail is one tap away. | 1, 2 |
| U3 | **The turn-ending actions sit in the same row as the movements,** marked only by "(ends turn)" and a dashed red border. | new | minor | A separate actions list that opens from the player (double-tap, long-press, an Actions button or the A key). | 1 |
| U4 | **The roll dialog is a second confirm** after choosing an action that goes to the dice. | all | minor | The confirm step shows the dice and the chance. The result dialog stays. | 1 |
| U5 | **The first screen asks for 484 words of set-up** before a game: format, possessions, age, standard, teams, level, scouting, seat. Defaults exist but aren't marked as safe to skip. | new | major | Four choices, each with good defaults and one Start button. The rest goes under Advanced settings. | 4 |
| U6 | **"Learn the rules" is a separate ten-minute course** before the first game. | new | major | The first game is the course: one tip at the moment each idea first matters. | 5 |
| U7 | **The computer can't be watched playing itself from the home screen.** "The computer by side" sits deep in the options, and nothing lets you pause, step or change speed. | Shaun | major | "Watch the computer", with play, pause, step and speed. | 6 |
| U8 | **"Coverage: shown" does nothing in the server version.** The map runs in the browser engine only. | all on the server | major | The server runs the same engine for the coverage view. | 6 |
| U9 | **The whiteboard shows a whole phase at once,** with only "the best look this phase" as comment. There is no turn-by-turn story, no assessment of each side and no report to keep. | all | major | Turn-by-turn diagrams, a line for each team each turn, the coach's assessment at each phase end and the possession's end, and a downloadable report. | 3 |
| U10 | **The end of a possession is a long dialog** (1,961 px on a phone) mixing the score, the trainer, ratings, the review, feedback for the designer and the log. | all | minor | The coach's assessment leads. Review, feedback and the log stay folded. | 3, 7 |
| U11 | **The skip link on the start screen goes nowhere** (there are no actions there). | keyboard | minor | Show the skip link only on the table. | 7 |
| U12 | **The rule reminders are long paragraphs** in the tracker (six to nine rules in one fold). | new | minor | Left as they are. The tips in the first game teach them one at a time. | 5 |

## 2. Legibility

| # | What's wrong | Who | Severity | Fix | Stage |
|---|---|---|---|---|---|
| L1 | **60 to 87% of the text in play is under 14 px.** Card stat rows are 12 to 12.5 px, the tracker 13 px, chips 12 px, court labels 8.5 to 11 px. | all, phone | major | Reading text at least 14 px; court labels and dense card rows at least 12 px. | 7 |
| L2 | **Every option speaks in numbers:** "Pass 18▲ v Intercept 6 (X2)", "Dribble 17▲ v Agility 8▲", "3 × (11 − 0) = 33". Shaun wants advantages first and numbers on tap. | all, new | major | Each option shows its chance as a percentage and one short "why" in advantage words, using the scout report's own phrases (`scout_phrases.json`). A "Show the numbers" switch brings today's view back. | 2 |
| L3 | **The cards lead with numbers** ("▲ Mid 12, L2 11, 3PT 11, FT 18") when folded. | all | major | Folded cards read as words: "Is dangerous from three. Knocks down the pull-up." Ratings open on tap. | 2 |
| L4 | **Coach Vision is in numbers and only at Learn level:** "O2's three 11▲ against X2's contest 5: a clean look behind the arc is worth 3 × 6 = 18". | all | major | Advantage words for both sides: "Get O2 the ball: dangerous from three, and X2 is slow to close out." | 2 |
| L5 | **The coverage view's line of strength is hard to read:** "The most the offence can force by next phase: 26 (lower is a stronger defence), by 2 separate ways." | all | major | "The offence's best look rose from 21 to 26: the defence got weaker." The number always means what the offence can get. | 7 |
| L6 | **Coverage reds and the shot-zone colours mix on the board** (pink long-two against red coverage). | all, colour-blind | major | Zone colours switch off while the coverage view shows; a legend under the board. | 7 |
| L7 | **Abbreviations on the cards** (Act, QS, Drb, Chl, F·S, F·C) are explained only to screen readers. | new | minor | Ratings open on tap with full names; the folded card has no abbreviations. | 2 |
| L8 | **The status line under the top bar packs three ideas** ("OFFENCE TO ACT · Offence turn: 2 actions left · a turn-ender ends it now · Hesitate: 1 a phase"). It already shortens after six turns. | new | minor | One idea a line: who acts and how many actions are left. The reminders move into the first-game tips. | 5 |
| L9 | **The handwriting font loads from Google Fonts.** Offline, the marker headings fall back to the system's handwriting font, or Comic Sans. | all offline | minor | Self-host Kalam with the app. | 7 |

## 3. Accessibility (WCAG 2.2 AA)

| # | What's wrong | WCAG | Who | Severity | Fix | Stage |
|---|---|---|---|---|---|---|
| A1 | **Court pieces and squares are 19 to 20 px on a phone.** The "Pick a player" buttons are full size but sit below the board and are needed to play reliably. | 2.5.8 Target size (minimum) | phone | critical | A tap on the court snaps to the nearest legal target within a finger's reach; the ghost and confirm catch a wrong snap. | 1 |
| A2 | **No single-pointer path for the arrow** once a drag rotate exists. | 2.5.7 Dragging movements | phone, motor | major (once built) | A rotate control: 45° a tap, both ways. | 1 |
| A3 | **Double-tap zooms the page on phones** and is hard to find. | 2.5.1 Pointer gestures | phone, motor | major (once built) | An Actions button and a long-press; the court stops the page zooming. | 1 |
| A4 | **Court pieces show no visible focus by the browser's measure** when tabbed to (an SVG halo is drawn on `:focus-visible`, but nothing marks a square). | 2.4.7 Focus visible; 2.4.11 Focus not obscured | keyboard | major | A clear focus ring on pieces and on squares, kept for the arrow-key cursor. | 1 |
| A5 | **No keyboard way to move between squares.** Each target is its own Tab stop: a defender with 25 squares is 25 Tabs. | 2.1.1 Keyboard | keyboard | major | Arrow keys move between a player's legal squares, Enter places, Enter confirms, A opens his actions, Escape backs out. | 1 |
| A6 | **The screen reader hears "Move to I12" with no next step.** Nothing announces the ghost or how to confirm. | 4.1.3 Status messages | reader | major | "O1 to J9, arrow north. Press Enter to confirm, Escape to cancel." | 1 |
| A7 | **Escape doesn't close the end-of-possession dialog** (its cancel is empty). Focus does stay inside it. | 2.1.2 No keyboard trap (best practice) | keyboard | minor | Escape closes it, as Close does. | 7 |
| A8 | **Heading order is wrong on six phone screens** (the matchup card's `h3` with no `h2` above it). | 1.3.1 Info and relationships | reader | minor | Fix the level. | 7 |
| A9 | **The shot-clock labels fail contrast in forced colours** (1.5 to 1). | 1.4.3 Contrast (minimum) | low vision | minor | System colours in forced-colours mode. | 7 |
| A10 | **The table is 1.7 phone screens tall at tip-off,** so the board scrolls away while choosing. | 1.4.10 Reflow (usability) | phone | major | The board stays in view; the side panels become tabs or drawers. | 7 |
| A11 | **Animations** (the dice roll, smooth scroll) respect `prefers-reduced-motion`; new ones (ghosts, replay speed) must too. | 2.3.3 Animation from interactions | motion-sensitive | minor | Covered in the new code. | 7 |
| A12 | **The defenders are buttons for the offence** when it is the offence's turn, and choosing one says "no legal action for this player now". | 4.1.2 Name, role, value | reader | minor | Kept as buttons (they open the matchup card), with a name that says they're the other side's. | 1 |

**Kept from the 4 Nov audit:** 0 axe issues on 51 of 59 screens; zone labels and the ball in solid ink; focus kept inside dialogs; full names for pieces; 200% zoom with no sideways scroll. All stay.

## The ten changes that matter most

1. **Tap a player, tap a square, confirm.** Every square he can reach lights at once; no movement menu (U1, Stage 1).
2. **Turn-ending actions in a short list beside the board,** one line each, never over it, opened by double-tap, long-press, an Actions button or A (U2, U3, A3, Stage 1).
3. **A tap on a phone court snaps to the nearest legal target,** so 20 px pieces stop being a problem (A1, Stage 1).
4. **Keyboard and screen reader play the board directly:** arrow keys between squares, Enter, A, Escape, and every step announced (A4, A5, A6, Stage 1).
5. **Advantages first, numbers on tap:** a percentage and one plain "why" on every option, words on the cards, and a "Show the numbers" switch (L2, L3, L4, L7, Stage 2).
6. **The whiteboard turn by turn,** with the coach's assessment at each phase and at the end, and a report to download (U9, Stage 3).
7. **A home screen with four choices and one Start button;** everything else under Advanced settings (U5, Stage 4).
8. **Learn by playing the first game,** with one tip at a time (U6, Stage 5).
9. **Watch the computer play itself,** and the coverage view working on the server too (U7, U8, Stage 6).
10. **Bigger text in play and a phone table that fits one screen,** with the coverage view clear of the zone colours (L1, L5, L6, A10, Stage 7).
