# Playmaker: UX, legibility and accessibility audit pack

Everything needed to audit the app's interface and write an improvement plan, without running anything. Built 17 Nov 2026 from the step 18s branch (PR 80), the latest build.

## Start here

1. **`01_screens/`**: 59 full-page screenshots of every screen the app has, on a laptop (1440 by 900) and a phone (Galaxy S9+), plus 200% zoom, dark-mode request and forced colours. File names follow the player's path through the app.
2. **`02_measures/measures_summary.md`**: one row per screen, covering automated accessibility issues (axe-core 4.10.2, WCAG 2.0, 2.1 and 2.2 AA plus best practice), words on screen, share of text under 14 px, small touch targets and sideways scroll.
3. **What the capture found** (below): the facts to start the plan from.
4. **`05_prior_work/ACCESSIBILITY_AUDIT.md`**: the last audit (4 Nov 2026) and what it fixed. A lot has been added since: levels, rosters, the draft, the digital match, the trainer, the scout report and the coverage view.

## What the capture found

The automated rules are mostly clean. Legibility and touch size are where the work is.

- **Automated issues: 0 on 51 of 59 screens.** The other 8:
  - Heading order on 6 phone screens (an `h3` with no `h2` above it, `.cmp-head`).
  - Contrast on the shot-clock labels under forced colours (1.5 to 1, 5 places).
- **In play, most text is small.** On the table, 60 to 87% of visible characters are under 14 px. The court labels are 9 to 11 px, and so are the card stat rows. Set-up screens are fine (2 to 5% under 14 px).
- **Court pieces are 20 by 20 px on a phone,** where 44 px is the target. The "Pick a player" buttons below the court are the full-size way to select one, so a phone player has two ways to select a piece, one of them hard to hit.
- **The table is long on a phone.** At tip-off it is 1,428 px tall (about 1.7 screens). The end-of-scenario screen is 1,961 px.
- **The court pieces have no visible focus outline** by the browser's measure when tabbed to (they are SVG; check by eye in `screens/laptop_14_piece_selected.png`). Every other control in the tab order shows focus.
- **The "Skip to the actions" link is on the start screen,** where there are no actions to skip to.
- **Escape doesn't close the end-of-scenario dialog.** Focus stays inside it correctly.
- **"Coverage: shown" does nothing in the server version.** The coverage map runs only in the link version (the browser engine). The button still appears in the server version and toggles with no map. The two screenshots of the working view come from the link version: `01_screens/link_version_coverage_stop1.png` and `_stop2.png`.
- **The handwriting font (Kalam) loads from Google Fonts.** Offline, headings fall back to a system font. It loaded for this capture. It is used for headings, card titles and the court, and the long end-of-turn line in `laptop_21_end_dialog.png` shows how it reads at length.
- **Piece names for screen readers are full:** "O1, number 1, Pass-First Point Guard, on I11 (plain wood), has the ball, 60 legal actions". The keyboard order is in `measures.json` (`keyboard_start`, `keyboard_table`).

## What's in the pack

| Folder | Contents |
|---|---|
| `01_screens/` | The 59 new screenshots, plus `earlier_screens/` (the screenshots kept in `docs/` from past steps, useful for seeing what changed) and the two coverage-view screenshots. |
| `02_measures/` | `measures_summary.md`; `measures.json` (every axe finding with the element and the fix axe suggests, the text-size spread, every small target by name, keyboard order, piece names, dialog focus). |
| `03_source/` | The interface source: `index.html`, `style.css`, `app.js` (the table and set-up), `coach.js` (the course and Coach Vision), `notation.js`, `trainer.js`, `records.js`, `pyodide-adapter.js`. Server-side words: `view.py`, `game.py`, `api.py`, `trainer.py`, and `plain.py` (the banned-words list the words are checked against). |
| `04_runnable/` | `playmaker.html`, the one-file link version: open it in a browser. It fetches Pyodide and the fonts from the internet on first load. |
| `05_prior_work/` | The 4 Nov audit; the interface history (`README_history.md`, "The coach's clipboard" and "Legibility and access"); the step 3n and step 5 reports (legibility and the interface clean-up); `STEP18S_REPORT.md` (the coverage view and the phase scores). |
| `06_design_rules/` | What any plan has to respect: `CLAUDE.md` (plain basketball words, the banned terms), `SHAUN_PRINCIPLES.md`, `DECISIONS.md`, `RULES_CURRENT.md`, `README.md`. |
| `07_tests/` | `test_accessibility.py` (the axe and focus checks run on every test run), `test_static.py` (link version, phone layout, coverage view), `test_web.py`. Any change the plan proposes has to keep these passing. |
| `08_strings/ui_strings.txt` | 494 pieces of on-screen text with file and line, for a wording and reading-level review. Pulled out by pattern, so text built from pieces appears in pieces. |
| `09_rerun/` | `capture.js`, the script that made the screenshots and measures, to run again after changes and compare. |

## Running it yourself

- **Server version** (all features except the coverage map): `python -m playmaker_web` in `playmaker/`, then open the address it prints.
- **Link version**: open `04_runnable/playmaker.html`, or `playmaker/site/index.html` served over http.
- **Run the capture again**: start the server, install `axe-core@4.10.2` with npm, then `node 09_rerun/capture.js <server address> <path to axe.min.js> <output folder>`.
