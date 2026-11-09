# Step 10 report: rebuild the boards, and measure positions against the average

## 1. Changes to the printed game

None. `leaf_mode` stays `floor`, so the game plays exactly as before.

## The exam, floor against relative

The JavaScript search (the app's own), All-Star, under today's rules. P = pass, F = fail.

| Board | On the clock: floor | On the clock: relative | 3 ahead: floor | 3 ahead: relative |
|---|---|---|---|---|
| 1 Straight lane (rebuilt) | F | F | F | F |
| 2 Sag by shooting | P | P | P | **F** |
| 3 Help the helper (rebuilt) | F | F | F | F |
| 4 Two jobs, one defender (rebuilt) | P | P | F | P |
| 5 Closeout (judge restated) | F | F | F | F |
| 6 Catch window (judged by D-94) | F | F | F | F |
| 7 Clock (B rebuilt) | P | P | P | P |
| 8 Backdoor (rebuilt) | F | F | F | F |
| 9 Corner | F | F | F | F |
| 10 Steal | F | F | F | P |
| 11 Contested pass (rebuilt) | F | F | F | F |
| 12 Strong-side corner | P | P | P | P |
| 13 Spacing | F | F | F | F |
| 14 Variety (judge restated) | F | **P** | F | **P** |
| 15 Goal consistency | P | P | P | P |
| 16 Wearing out one defender | F | **P** | F | **P** |
| 17 Turn economy | P | P | P | P |
| C1 Deny the shooter's catch | P | P | P | P |
| C2 Clean pass (rebuilt) | P | P | P | P |
| **Passes (of 19)** | **8** | **10** | **7** | **10** |

**Made worse by relative:** board 2, at 3 moves ahead only:
- Under floor, X2 quick-steps to D7 and the board passes.
- Under relative, X3 sprints to N7 and X2 doesn't sag.
- On the clock both modes pass.

**Missing terms:** a crowded or clear driving lane (board 13). O1's straight drive reads 8 with O5 in the lane and 8
with O5 cleared to any of 20 squares, so neither mode can see the spacing. Not added.

## 2. What changed

- **Step 9 merged** (pull request 53). Branch `step-10-position-value` from `main`.
- **Shaun's marks** are in `DECISIONS.md`. They settle D-96, D-97, D-108, D-109 and D-111; D-112 and D-113 stay open
  until the goals step.
- **Boards rebuilt** (`playmaker_engine/exam.py`). The facts that show each intent are in
  `docs/runs/step10/board_facts.json` and on the book pages.
  - **1:** O1 at I8, X1 trailing at K11. Before the defence acts, the drive is worth 32 against 22 for the best other
    option.
  - **3:** X1 has used his Move and Quick Step, so he has no movement left. Only X4 can get next to O1 (H4, H5 or I4).
  - **4:** X5 sits at J5, off the passing line, so the pass to O5 is legal; it arrives half the time.
    - The judge is met if the offence attacks X5, or if its choice rates above every attacking turn its own search
      weighs.
    - The part that judged the computer's own reading is dropped.
  - **5 (judge restated):**
    - A: the drive must end closer to the rim.
    - B: a shot now, or a move to a square where no defender can Contest.
  - **6 (judge restated):** by D-94. The open look (33) beats the possession (24.9), so O4 must act himself.
  - **7 B:** the offence's final turn: the last phase, 2 tokens left.
  - **8:** X1 and X2 have used their Move and Quick Step, so no one can step into the backdoor pass. A cut arrives for
    sure; after a cut to F7, O2's look is 32.
  - **11:** X2 moves to C6, off the line, so the pass to O2 is legal. X5 is in the lane, and the pass arrives half the
    time. B is the final turn.
  - **14 (judge restated):** met when the top first move leads by more than the variety margin (2). Otherwise no first
    move above 70%.
  - **C2** (`exam.c2`): two equal shooters, each catch worth 39.
    - The pass to O2 is clean: X2 sags to B4, out of the lane, and no one can step into it.
    - The pass to O3 is contested: X3 can step into it, and it arrives 55% of the time.
    - Judged: no contested pass, and the clean pass rated above it.
- **`leaf_mode`** (`floor` by default; `relative`) in `decide.py` and `engine.js`, read from `ai_profiles.json`
  (`eval.leaf_mode`).
  - **relative:** the position is worth the phase table **plus** its continuation read **minus** the average
    continuation read at that phase.
    - The continuation read is the engine's own: each attacker's look after the defence's best cover, which carries
      the pass's chance of arriving, the contest and the defenders' remaining Moves and Quick Steps.
    - A shot now and a look released this turn stay as they are.
  - **The averages:** `tools/relative_average.py` reads the step 3n seed positions (and Senior Pro's aggregate run) at
    the first offence turn of each phase, under today's rules. They are stored as `eval.relative_average`.
    - Senior Pro: 15.6, 18.1, 20.3, 20.5, 19.1, 19.7 for phases 1 to 6, from 160 down to 41 positions.
    - The other age and standard tables rest on 1 to 16 positions a phase.
  - No new weights.
- **Tools:**
  - `tools/js_equivalence.py --leaf-mode` and `tools/js_probe.js` set the mode in both engines.
  - `engine.js` exports `setLeafMode`.
  - `tools/exam_10.py` runs the exam, the gap values and the depth measure.
  - `tools/exam_evidence.*` take the mode.
- **The exam book** has the rebuilt pictures and words, and a "Step 10: the exam both ways" table on each page. On
  rebuilt boards, the step 6 and step 9 sections are labelled as the board before the rebuild.

## 3. What it proves

- **Equivalence** (`tools/js_equivalence.py --n 200`): 0 mismatches in both modes. Files:
  `docs/runs/step10/js_equivalence_floor_200.json` and `_relative_200.json`.
- **The tests for the changed files:**
  - `test_rules_current` (18 pass), `test_static`, `test_step3n`, `test_step3m`: 77 pass, 15 expected failures, 0 fail.
  - With `floor`, no test outside the exam boards changed outcome against `main` (section 5).
- **What still works:** boards 12, 15, 17 and C1 pass in all four runs.
  - Board 9 fails in all four, and board 10 fails on the clock in both modes. Both fail under floor too, so the new
    reading isn't the cause.
  - They passed in step 6, when the Python search looked 1 move ahead; the app's search looks 2.
- **The real-gap boards, 3 moves ahead** (`docs/runs/step10/gaps_*.json`): the computer's choice against the move the
  board expects.

| Board | Floor | Relative |
|---|---|---|
| 2 A / B | level (18.8 v 18.7; 18.7 v 18.7) | read differently: choice ahead 2.6 and 2.4 (X3's sprint 19.0 v X2's sag 21.6) |
| 3 | choice ahead 5.7 (24.9 v 30.6) | read differently: choice ahead 11.9 (28.0 v 39.9) |
| 6 | choice ahead 6.0 (39 v 33) | choice ahead 5.1 (42.5 v 37.4) |
| 13 | level (24.9 v 24.9) | read differently: choice ahead 2.6 (22.1 v 19.5) |
| 16 | level (24.9 v 24.9) | **the expected move ahead by 10.2** (29.7 v 19.5): the board passes |

  On boards 2, 3 and 6 the values are from the defence's side: lower is better for it.
- **How far the app looks on the clock** (`docs/runs/step10/app_depth.json`, the JavaScript search, 21 positions):

| Level | Here: median (lowest) | Phone speed: median (lowest) |
|---|---|---|
| Rookie | 2 (1, board 2 A) | 1 |
| Starter | 2 (2) | 1 |
| All-Star | 2 (2, board 6 slowest) | 2 (1, board 10 B) |

- **Timings:**
  - The four exam runs took 2 to 8 minutes each, run side by side.
  - The clock runs shared four cores with the others, so their timing is a little pessimistic.

## 4. For Shaun to decide

- **Switch `relative` on?**
  - For: it lifts the exam from 8 to 10 passes on the clock and from 7 to 10 at 3 moves ahead. Boards 14 and 16 now
    pass, and board 4 passes at 3 moves ahead. The positions that floor read as the same 24.9 now read differently.
  - Against: board 2 fails at 3 moves ahead. On boards 2, 3, 6 and 13 the new readings still prefer the computer's
    choice to the board's move.
  - Option: switch it on and treat boards 2, 3, 6 and 13 as valuation questions for phase 4; or keep floor until the
    missing term is decided.
- **My choices inside "relative"**, for your sign-off:
  - Only the continuation is read against the average; a shot now and a look released this turn stay absolute.
  - Every age and standard uses its own average, but only Senior Pro rests on more than 16 positions a phase.
- **The missing term:** a crowded or clear driving lane (board 13).
- **Rebuilt boards that still fail in both modes:**
  - **1:** the defence pauses, and the drive is still worth 32 against 22.
  - **3:** X4 helping reads worse for the defence.
  - **5 A:** O2 steps up the wing instead of driving.
  - **6:** the screen and pass back read higher.
  - **8:** O2 lifts away instead of cutting.
  - **11:** no pass on the final turn.

  The values are on each page.

## 5. Noticed, not touched

- **Boards 9 and 10 now fail under floor** with the app's search (2 moves ahead on the clock). They passed with the
  Python search at 1 move in step 6.
- **The `floor` comparison with `main`** (the same four test files, the same order, on each branch):
  - `main`: 74 pass, 16 expected failures, 2 fail.
  - This branch: 77 pass, 15 expected failures, 0 fail, run in a different file order.
  - Outside the exam boards, no test changed outcome. The exam-board differences:
    - board 1 now fails, as rebuilt;
    - board 4 now passes, as rebuilt;
    - board 9 and board 15 move with the clock, as before.
- **The static test about the browser bundle** fails on `main` and on this branch alike whenever another test has
  already loaded `exam.py` or `selfplay.py`. It depends on test order; I didn't change it.
- The test runs rewrite two screenshots in `docs/`; I restored them.
