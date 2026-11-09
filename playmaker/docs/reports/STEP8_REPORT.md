# Step 8 report: the new print, the 9 November rulings, the exam book

## 1. Changes to the printed game

None by me. Today's print is filed: the eight PDFs are in `reference/` and the old copies are in
`archive/reference/` with the suffix `_pre9nov`.

**The rules check** (`tests/test_rules_current.py`): 14 pass, 4 fail. In all four the numbers agree; only the wording
moved. Neither the print nor the register is changed.

| Check | Printed today | Register |
|---|---|---|
| Turnover points, rulebook | "Intercept or steal −5, lose 2 seconds, play on. A stolen shot is cancelled. Last phase: 0, or the score so far if lower" (the check looks for "−5 and lose 2 seconds") | −5 |
| Turnover points, offence tracker | "Intercepted: −5." (the check looks for "Picked off: −5") | −5 |
| Steal foul, rulebook | "Foul on a steal +5, play on / Second foul on a steal +5 and free throws, possession ends / Foul on a shot, a Steal's too: free throws or the open shot, whichever is higher" (the check looks for "First foul on a steal +5") | +5 |
| Steal foul, defence tracker | "Foul: +5 to them; 2nd also free throws, over" and "Any foul now, a Steal's too: free throws or the open shot if higher, no +5" (the check looks for "1st +5") | +5 |

## 2. What changed

- **Step 7 merged** (pull request 51). Branch `step-08-exam-book` from `main` after the site rebuild.
- **The print:** the rulebook, both trackers, the A3 court, both first-game guides, the playing levels sheet and the
  scenarios, replacing the old copies.
- **`DECISIONS.md`**, all with "Source: Shaun, 9 Nov 2026":
  - D-62 to D-69 and D-80 move to Ruled as "provisional, phase 4". Phase 4 tunes them against the exam; any change
    needs evidence and Shaun's approval.
  - D-81 is closed: the cost stands as built, with the paired read and D-13.
  - D-91 is accepted for now; it comes back in step 14.
  - D-92 is settled in step 13, with exam evidence.
  - D-93 is re-measured in phase 4 under the 9 November rules.
  - D-94 is ruled, with Shaun's principle in his words. The six advantage states stay. It carries the trainer note:
    never call a shot an advantage in player-facing text.
  - D-95 is ruled, not built: responsibility comes from coverage shares, not fixed matchups. It is built in phase 4,
    with the trainer's flags in step 16.
- **The exam book:** `docs/reports/EXAM_BOOK.html`, with `docs/reports/EXAM_BOOK_index.md` as the tick list. It has
  21 pages:
  - the 17 exam boards (board 6 is D-111);
  - two candidate boards built from the archived tests' positions (D-108, D-109);
  - the two trainer tests (D-112, D-113).

  The pictures are drawn by the app's own drawing code. `tools/exam_book.py` and `tools/exam_book_draw.js` rebuild the
  book.
- **`docs/runs/step6/exam_results.json`**: the exam rows from the step 6 full run, saved so the book reads results
  already on file.

## 3. What it proves

- **The rules check:** run as above.
- **The exam book:**
  - It opens in a browser with the network blocked: 0 outside requests, no errors, 21 pages, 25 pictures. It is
    1.2 MB in one file. It fits a phone screen with no sideways scroll.
  - Its words pass the banned-terms check.
- **Today's results:**
  - 6 of 17 pass: boards 1, 9, 10, 12, 15 and 17. That is the All-Star on the clock under the 9 November rules.
  - Not measured under the current rules:
    - searching four moves ahead (its only run was before 9 November);
    - the two candidate boards (their tests checked the retired computer).
  - The two trainer tests fail.
- The exam was not run.

## 4. For Shaun to decide

- **D-94, "the six advantage states stay":** those six states live in the step 3g module archived in step 5
  (`archive/engine/advantage.py`). The live computer doesn't use them. Options: keep them as the trainer's vocabulary
  for phase 4; or restate D-94 without them.
- **D-77** (scenario 10 is played with the card's numbers) is a number, but I left it awaiting sign-off: it is a
  card's setup, not one of the engine's settings. Options: move it with the provisional settings; or leave it.
- **Boards I wasn't sure of:**
  - **Board 5:** the "drive" half counts any movement by O2, even a sprint up the wing away from the rim, so today half
    of the board passes on a move that isn't a drive.
  - **Board 1** passes easily: the drive is weak before the defence acts (10 against 26).
  - **D-108** is copied from the archived test: Five Out v High-Low on the tabletop starting setup, not the app format
    the other boards use.
  - **D-109** is scenario card 1 with players placed by hand. O5 stands out of bounds as the inbounder, as stored.
  - **D-112:** the test checks that the trainer offers a legal reorder, but not which one. The page says that in
    general terms.
  - **Left and right** on every page mean as you look at the picture (rim at the bottom).
  - **Board 17** has no picture: it checks the other boards.

## 5. Noticed, not touched

- The app serves its own copy of the playing levels sheet (`playmaker_web/static/docs/Playmaker_Playing_Levels.pdf`),
  which is still the old one.
- `docs/runs/3n/3n_exam_timed.json` judged board 1 by the old line check, so its Starter and Rookie rows don't match
  today's reading. The book says so.
