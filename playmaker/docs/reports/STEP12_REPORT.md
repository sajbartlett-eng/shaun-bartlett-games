# Step 12 report: stop the depth flip, and let the computer see reach

**What was measured.** Shaun stopped the long runs part-way. In their place I ran a cut-down measurement, finished in
21 of its 45 minutes:
- two settings: both switches off, and both on;
- 1 team-turn pair ahead (an offence turn and the defence's reply), and the clock;
- depth stability on boards 2, 7, 9, 10 and 16;
- the three sensitivity pairs.

Results marked **[before the stop]** come from runs finished before it:
- the equivalence checks;
- the tempo and margin measures;
- the 2-pair exam: off complete, stable on 12 of 19 boards, reach on 10 of 19, both not started.

Everything else is **[cut-down]**.

## The exam: fixed look-ahead first, the clock beside it

P = pass, F = fail. "(1)" means the search reached only 1 team turn in the time it had.

| Board | Off: 1 pair | Off: clock | Both on: 1 pair | Both on: clock | Off: 2 pairs [before] | Stable: 2 pairs [before] | Reach: 2 pairs [before] |
|---|---|---|---|---|---|---|---|
| 1 | F | F | F (1) | F | F | F (2) | F |
| 2 | P | P | P (1) | P | P | F (1) | F (1) |
| 3 | F | F | F | F | F | F | F |
| 4 | P | P | P | P | P | P | P |
| 5 | F | F | F (1) | F | F | F | P |
| 6 | F | F | F | F | F | F | F |
| 7 | F | P | P (1) | P | P | P | P (3) |
| 8 | F | F | F | F | F | F | F |
| 9 | F | F | F | F | F | F | F |
| 10 | F | F | F (1) | P | F | F (1) | F (1) |
| 11 | F | F | F (1) | F | F | F (2) | not run |
| 12 | P | P | P (1) | P | P | P (2) | not run |
| 13 | F | F | F | F | F | not run | not run |
| 14 | P | P | P | P | P | not run | not run |
| 15 | P | P | P (1) | P | P | not run | not run |
| 16 | P | F | P | P | F | not run | not run |
| 17 | P | P | P | P | P | not run | not run |
| C1 | P | P | P (1) | P | P | not run | not run |
| C2 | P | P | P | P | P | not run | not run |
| **Passes** | **9 of 19** | **9 of 19** | **10 of 19** | **11 of 19** | **9 of 19** | **3 of 12** | **3 of 10** |

The 1-pair and clock columns are [cut-down]; the 2-pair columns are [before the stop].

## Depth stability [cut-down]

The table lists the computer's first action at each completed depth (team turns ahead), on the boards that flipped in
steps 9 to 11. Each board's decisions had at most 2 minutes.

| Board | Off | Both on |
|---|---|---|
| 2 A (three rated 4) | 1: X2 to D6 · 2: X2 quick-steps to D7 · 3: X2 quick-steps to D7. Changes from 1 to 3 | only depth 1 finished |
| 2 B (three rated 12) | 1: X3 to N7 · 2: X3 quick-steps to N7 · 3: X2 quick-steps to D7. Changes from 1 to 3 | only depth 1 finished |
| 7 A | O3 sprints to E9 at every depth (1 to 4). Stable | only depth 1 finished |
| 7 B | O3's mid-range at every depth (1 to 4). Stable | 1: floater · 2, 3, 4: mid-range. Changes once, from 1 to 3 |
| 9 | O1 moves to J3 at every depth (1 to 4). Stable | the same at 1 and 2 |
| 10 A (good odds) | 1: X4 steals · 2, 3, 4: X1 to J10. Changes from 1 to 3 | only depth 1 finished |
| 10 B (bad odds) | 1: defence holds (Pause) · 2, 3: X4 to B4. Changes from 1 to 3 | only depth 1 finished |
| 16 | O2 moves to A5 at every depth (1 to 4). Stable | the same at 1 and 2 |

- **Off:** the first action changes between like-with-like depths (1 against 3, or 2 against 4) on 4 of 8 decisions:
  2 A, 2 B, 10 A and 10 B. Each change is from 1 to 3; from 2 to 4 none changes.
- **Both on:** only 3 decisions got past depth 2 within the 2 minutes, so stability is **not measured** for both on.
  The one that did (7 B) changes once, from 1 to 3, then holds.

## 1. Changes to the printed game

None. Both switches are off by default, and the game plays as before.

## 2. What changed

- **Step 11 merged** (pull request 55). Its rulings are recorded:
  - D-117: board 7 B has 1 token, rebuilt.
  - D-118: the fixed look-ahead is the exam's main measure.
- **`search.stable`** (off), in `search.py` and `engine.js`:
  - **Quiet points:** look-ahead counts completed team turns; a side is never judged between its two actions.
  - **Play on while pending:** at the horizon, a declared shot, a pass in the air, a contest choice, or a shot worth
    more than the possession is played on with only the forcing replies (the shot, Contest, Steal, Intercept, ending
    the reaction). There are at most 2 extra team turns (`extension_cap`, provisional).
  - **Like with like:** the answer comes from the deepest even depth (an offence turn plus the reply).
  - **Change only for a clear reason:** the choice from two depths earlier stands unless the new best beats it by more
    than one standard error of the reading at that phase (`stable_margin`, provisional).
  - **The tempo term**, a measured term not a chosen one: it is material (see section 3), so with the switch on each
    reading is shifted by half the measured gap toward the side not to act.
- **`eval.reach`** (off): `playmaker_engine/reach.py` and `engine.js` build the reach map. For every player and every
  square it holds:
  - the fewest Move and Quick Step uses to get there this phase, with what he has left;
  - the same next phase, fresh;
  - the earliest turn he can arrive.

  It follows the movement rules exactly (blocking pieces, screens, locks). With the switch on, the reading uses it for
  three things:
  - who can Contest in time (the exact reach, in every reading);
  - who can step into a pass;
  - who reaches an attacker's path before he does: a defender whose reply lands on every path to a later look removes
    that look.

  No new weights.
- **What the reading already used, before reach:**
  - The continuation reading already uses each defender's *remaining* Move and Quick Step this phase, for his contests
    and his replies. It does not use what he gets back next phase.
  - Board 16 barely moves because the continuation counts only the best look the defence's cover leaves open.
  - Spending X2 matters only through the one look he was covering: O4's rises from 12.0 to 13.0. O2's own look stays
    at 19.5 either way, so the reading moves by 1.6.
- **Tools:**
  - `tools/js_equivalence.py --stable --reach --search N` checks the reach map square by square, the reading and whole
    searches.
  - `tools/stable_measures.py` measures the tempo and the margin.
  - `tools/exam_12.py` runs the exam, depth stability and sensitivity; `tools/exam_12_summary.py` builds the tables.
- **The exam book** shows the step 12 results on each page.

## 3. What it proves

- **Equivalence [before the stop]:** 200 states and 4 whole searches in each of the four settings, with 0 mismatches,
  including the reach map, square by square, on 193 states each.
- **The tests for the changed files, switches off [before the stop]:** `test_rules_current`, `test_static`,
  `test_step3n`, `test_step3m` give 79 pass, 11 expected failures, 1 unexpected pass, and 1 fail, which I fixed.
  - The fail was my own change: the equivalence tool returned the reach map to a test that doesn't ask for it.
  - The reach map is now opt-in; with that, `test_step3n` gives 21 pass and 3 expected failures. What the test checks
    is unchanged.
- **Sensitivity [cut-down]:** each pair's reading difference against the margin of error, which is 0.92 in phase 1.

| Pair | Off | Both on |
|---|---|---|
| Board 13: O5 in the lane, against O5 cleared to J6 | 0.0 (inside the margin) | 0.0 (inside the margin) |
| Board 16: X2 fresh, against X2 spent | +1.62 (beyond) | +0.96 (beyond, just) |
| Board 12: the help (X1) near the mismatch at D4, against drawn away to I8 | +6.43 (beyond) | +6.43 (beyond) |

  The third pair is my choice. O2 is an elite corner shooter (his three is rated 13) against X2 (whose contest on a
  three is 3). Drawing X1 away from him lifts the reading by 6.4 in both settings.
- **The tempo [before the stop]:** the same position reads 2.3 points better with the offence to act than with the
  defence (standard error 0.09; 1,501 Senior Pro seed positions). That ranges from 1.7 in phase 1 to 2.9 in phase 5.
  It is material, above the margin, so it is in as a measured term.
- **The margin of error [before the stop]:** one standard error of the reading, from the phase table's own error and
  the average's: 0.92, 1.05, 1.22, 1.34, 1.42 and 1.52 for phases 1 to 6.
- **The extension cap:**
  - [cut-down] both on, 1 pair: 42 cap hits in 2,962 extensions (1.4%).
  - [cut-down] both on, clock: 0 in 397.
  - [before the stop] stable, 2 pairs: 0 in 602,439.
  - "Change only for a clear reason" kept the earlier choice 0 times.
- **Speed [cut-down, the All-Star only, from the clock runs]:**
  - Off: median 2 team turns on the clock.
  - Both on: median 1; most boards finish only 1 team turn.
  - At a fixed 1 pair, a decision takes a median 0.4 s off and 5.2 s with both on, about 14 times as long.

## 4. For Shaun to decide

- **Switch the stable search on? Not yet: the evidence that it removes the flips isn't there.**
  - With the switches off, the flips seen now are all between depths 1 and 3 (boards 2 and 10).
  - With both on, those boards finished only depth 1, so whether the rule removes them is unmeasured.
  - It costs about 14 times the time, so on the clock the All-Star falls from 2 team turns to 1.
  - Before the stop it reached only 1 or 2 pairs on boards 1, 2, 10, 11 and 12.
  - Option: keep it off until the search is faster.
  - Option: switch on only "quiet points" and "like with like", which cost little; "play on while pending" is most of
    the cost.
- **Switch the reach map on? Not on its own evidence yet.**
  - For: it changes contest and pass readings to the exact movement, and board 5 passes with it at 2 pairs.
  - Against: it is also slow, and on board 16 it shrinks the spent-defender difference (1.62 to 0.96) rather than
    growing it.
- **The provisional numbers:**
  - The 2-turn extension cap was hit 0 to 1.4% of the time.
  - The margin is 1 standard error: 0.92 in phase 1, and it kept no choices in these runs.
- **The missing term:** a crowded or clear driving lane (board 13). Clearing O5 changes nothing, even with reach,
  because O5 is a teammate: the reach map covers defenders reaching the path. This is D-115, already moved to the goals
  design.

## 5. Noticed, not touched

- **Not measured, because of the stop:**
  - the 2-pair exam with both on, and stable and reach alone on their remaining boards;
  - stable alone and reach alone in the cut-down run;
  - the clock depth per level (Rookie, Starter, All-Star) here and at phone speed, for any setting; the All-Star's
    depth above comes from the clock runs;
  - depth stability with both on, beyond depth 1 or 2.
- **The readings were not fetched.** Every reading link is outside this session's network: skatgame.net,
  en.wikipedia.org, www.chessprogramming.org, www.researchgate.net, databallpy.readthedocs.io and arxiv.org. I
  searched the titles and used the summaries:
  - Hauk, Buro and Schaeffer: Star2 and the strength of the evaluation against depth;
  - Plaat's MTD(f) note: seeding from two iterations back for odd and even swings;
  - Nau: lookahead pathology;
  - Spearman: arrival time per location;
  - databallpy: space occupation;
  - Franks et al.: shared defensive attention.
- **The cut-down runs took 4 cores at once,** so the clock results carry some load.
- **Four parallel deep searches ran this 16 GB machine out of memory** and restarted the container. The tool now uses
  a fresh engine per board.
