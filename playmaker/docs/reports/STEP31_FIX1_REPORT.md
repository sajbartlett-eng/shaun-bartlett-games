# Step 31, fix 1 of 7: re-read only what an action touched. Report

**Built in both engines, on branch `step-31`. Not merged, as asked.** No decision changed: on every exam board, every choice, value and coach's line is the same before and after (239 readings, 0 different). Every reading ran with the engine held to 256 MB, so memory stays within a phone's browser. The exam was not run.

The speed-up is real but short of the 3 to 10 times the step 31C report estimated. Defence setups are now about 2.8 times faster, offence setups and turns about 1.8 times. Why, and what's left, is in section 4.

## 1. Changes to the printed game

None.

## 2. What was built

1. **The defence's answer inside the number (both engines).** For each defender movement the computer considers, it used to work out the worth of every look on the court again, often over 800 of them. Now it re-reads only the looks that movement touches: the ones the defender can contest from his new square, the ones he was contesting, the look on the square he steps onto, and the looks a block bears on.
   - That alone barely helped, because one defender touches about 40% of the court. So, for each defender, the computer now keeps a ceiling on every look: what it would be worth with his contest taken off. No move of his can make it worth more.
   - It reads looks highest ceiling first, and stops as soon as nothing left could change the answer. A movement now reads about 1 in 8 of the looks it used to.
2. **Setting up each board's reading (JavaScript).** Most looks are worth the same at every step of the value (no block line moves with the step), so they're worked out once, not once per step. The quick bound check that decides which movements get read in full reuses every look the movement doesn't touch.
3. **Contest values kept across boards (both engines).** How much one defender's contest takes off one look depends only on the cards, the look and the kinds of contest he can make there. So it's kept for the game, in a size-limited store, instead of being worked out again for every board.
4. **The old reset settlement (JavaScript).** Within one think, the same position now settles once, not once per search line that reaches it.
5. **A reference kept for the tests.** Each engine keeps the old read-every-look method, used only behind a test switch. The new test file `tests/test_fix1_difference.py` reads every candidate both ways and requires the same numbers to the last digit.
6. **The comparison tool.** `tools/step_31_same.py` records every board's choices, values and lines (the Coverage view's words, the defenders' lines, both engines), with the heap held to 256 MB, then compares two records field by field.
7. **The design.** The design PDF you sent replaces the design file's text where they differ. That adds A (what on-ball position is worth), B (two-step routes, and shot fakes read inside the number) and C (ties broken by the next-best line), each with its row in the rulings table. The audit is filed with it, in `docs/reference/step31/`. A, B and C are design text only; they come with fixes 3 to 5.

## 3. Times, before and after

**One at a time, nothing else running:**

| Thinking | Before | After | Times faster |
|---|---|---|---|
| A defence setup (E1, Five Out cards against Iron Wall) | 86.7 s | 27.9 s | 3.1 |
| A defence setup (E33) | 35.1 s | 14.4 s | 2.4 |
| An offence setup (E15b, Shoot and Protect) | 60.6 s | 33.8 s | 1.8 |
| A turn with a shot and blocks in it (E13, the cutter under the rim) | 17.5 s | 10.8 s | 1.6 |
| 6,326 readings of the value (every exam board and boards one action on), in one engine | 175 s | 96 s | 1.8 |

**The whole comparison set** (239 readings on every exam board, four at a time, heap held to 256 MB): 18 min 15 s before, 8 min 53 s after.

| Kind | Readings | Before | After | Times faster |
|---|---|---|---|---|
| Defence setups | 16 | 1,743 s | 631 s | 2.8 |
| The bad-start defence setup (check G4) | 1 | 111 s | 44 s | 2.6 |
| Offence setups | 6 | 684 s | 394 s | 1.7 |
| Turns | 16 | 437 s | 240 s | 1.8 |
| One-off readings (value, weight map, Coverage view) | 138 | 67 s | 59 s | 1.1 |
| Python engine (value and weight map) | 46 | 103 s | 92 s | 1.1 |

One-off readings barely move because each one starts a fresh engine, and starting up dominates. The app keeps one engine running, so in play it gets the larger gains in the first table.

**Memory.** All 239 readings ran inside a 256 MB heap. Unheld, a setup's engine process peaked at about 400 MB in all, down from about 670 MB.

## 4. What couldn't be done, and why

**Nothing needed a decision changed.** Twice a shortcut differed from the old reading, and both times the shortcut was fixed, not the decision:
- I passed the wrong figure in as what playing on is worth. Caught by the side-by-side check (2,743 of 98,987 candidates had a different count of tied routes).
- A weighted average can round one hair above both its ends, so 26.925 came out as 26.925000000000004. My "can't beat this" test now keeps a margin far below any real difference, and the ball handler's dribble routes, the only routes where this rounding can tip the answer, are always read in full.

**Not done in this fix, though possible without changing a decision:**
- **Building each board's map by difference.** When one player moves, the whole map of looks is built again. That is now about a quarter of a setup's time. Every attacker's looks depend on every defender (walls, passing lanes, steal chances, pass chances), so doing this exactly needs each look to record what it depends on. It's the next biggest saving, along with several cores.
- **The Python engine's own cost.** Its time is mostly in building the map and in contest geometry. The answer loop this fix targets was a small share of it.

**Not done, because it would change a decision:** on a board with blocks, about 40% of a turn is the old settlement that picks where the blocker resets (D-276). The positions really are all different, so remembering them saves little. Making it cheaper means changing how the reset square is chosen. That belongs with the open block-reset ruling.

**Why not 3 to 10 times.** That estimate assumed a movement touches a few players' worth of looks. In fact one defender's contest reach covers about 40% of the court. The ceilings recovered most of that. The rest of the time is now spread across building each board's map, setting up each reading, and memory housekeeping, each 10 to 25%.

## 5. What it proves

| Check | Result | Time |
|---|---|---|
| Before-and-after comparison (`tools/step_31_same.py`): every choice, value and line, both engines, every exam board | 239 readings, 0 different, none ran out of memory | 8 min 53 s (the "before" record was made first, before the change) |
| The new reading against the old, every candidate both ways (`tests/test_fix1_difference.py`), JavaScript and Python | Passed: 0 different | about 80 s |
| During the build, the same check over more boards | 0 different in about 560,000 JavaScript candidates (98,987 on boards one action on; 458,000 in two whole setups and two turns). 0 different in 6,326 whole JavaScript readings and 795 Python readings | (not part of the test run) |
| The rules (`test_rules_current.py`) and the memory tests (`test_step30b.py`) | 25 passed | 26 s |
| The golden game | 8 passed, no value moved, nothing re-recorded | 85 s |
| The value's own guards (`tests/test_exam.py`: cuts against every movement read in full, the memory against a fresh reading, the mix in both engines, both engines on five boards) | 9 passed | 54 s |
| Engine equality (`tools/js_equivalence.py`, 40 random states) | 0 mismatches | 47 s |

The fast tests ran three side by side in 2 min 4 s. With the comparison, testing came to about 11 minutes, a minute over the 10 asked for. **Not run:** the exam (as asked) and the rest of the suite.

## 6. For Shaun to decide

Nothing new from this fix. Fix 2 (later answers cost actions in every phase) is next.

## 7. Noticed, not touched

- **The arrows in the data** (the audit's open question). Each defender's stance in the setup and turn records gives `arrows` as one number from 0 to 7: N, NE, E, SE, S, SW, W, NW. That is his first arrow. His second points at the next direction clockwise, 45 degrees on. So `arrows: 7` means north-west and north. The pictures can draw them from that.
- The before-and-after records are 7.6 MB each, because they keep the Coverage view's full words for every board. They're kept so a later fix can compare against them.

## 8. Model for the next step

Claude Opus 5.5, effort high. Fix 2 changes what the number reads in both engines, and the two have to stay equal on every board.
