# Step 7 report: step 6 follow-ups

## 1. Changes to the printed game

- **Rulebook, Scoring, the steal-foul line:** add "A steal foul on a shooter is a shooting foul: free throws only." It
  goes beside the step 6 lines on the steal foul (every steal foul +5; in the bonus, free throws as well).

Nothing else printed changes. The forced-shot contest choice (D-110) is the rule as printed.

## 2. What changed

- **Step 6 merged.** Its answers are in `DECISIONS.md`:
  - D-110: the forced shot keeps the free contest choice. Ruled, built.
  - D-89 gains the shooter line.
  - D-111 to D-113 put the three tests under step 12.
  - D-107 is now built, and D-81 has the paired read.
- **A steal foul on a shooter (part 1).** A Steal against a declared shot that fouls now gives the shooting free throws
  only, with no +5, in both formats. It still counts as a foul, so in the app it is a team foul.
  - Built in `resolve.py`, `engine.js` and the computer's pricing (`solver.py`'s reaction model). The score needed no
    change: it adds the +5 only when the state carries it.
  - The register row and `RULES_CURRENT.md` say it.
  - New test: `test_a_steal_foul_on_a_shooter_is_free_throws_only`, both formats.
- **Wording (part 2).** The reaction's end button now reads exactly "End without a Contest: the shot goes up
  uncontested."
- **Match and matchup (part 3).** I checked every string players read: the page, Coach Vision and the course, the
  review, the trainer, records, level descriptions, card text, the scout phrases and `index.html`. That is 20 strings
  with "match" and 10 with "matchup". Every "match" means a whole game and every "matchup" means one player against
  another. **No string needed changing**, so there is no before-and-after list.
- **The three tests** are marked as expected failures, each with the reason "Contest as an action (D-18) changed the
  reading; re-based with the exam in step 12": exam board 6 (in the exam's open list), the early cut, and the decoy
  credit.
- **`tools/js_equivalence.py --reaction`** is new. It checks shot reactions only and also compares what each Contest,
  Steal and end of the reaction resolves to: every leaf of the roll tree, with its probability and score.
  `tools/js_probe.js` has the JavaScript side.
- **`tools/d81_paired_read.py`** is new. Outputs are in `docs/runs/step7/`.

## 3. What it proves

- **Named tests:** `test_rolls_scoring.py`, `test_step6.py`, `test_rules_current.py` and the three marked tests. 66
  pass and 3 are expected failures (the three markers), in 18 seconds.
- **Reaction-only equivalence:** 320 states (seed 7) inside a shot reaction, 0 mismatches on every check, including the
  outcomes. 37 seconds: 33 for Python, 3 for JavaScript.
  - Contest was available in 41 of them, Steal in 5 and ending the reaction in all 320; 111 were after one reaction
    action.
  - Steal was thin, so I ran 1,500 more (seed 8): 0 mismatches, with Contest in 234, Steal in 23, and 537 after one
    action. 150 seconds.
  - Files: `docs/runs/step7/js_equivalence_reaction_320.json` and `_1500.json`.
- **D-81, the paired read** (`docs/runs/step7/d81_pairs.json`). It used the current rules, including D-18 and D-82,
  with the rolls left out.
  - The 60 tabletop possessions hold 134 passes. **18 of them could be intercepted, giving 18 pairs**, from 12 of the
    possessions.
  - **Mean gap** (after a successful Intercept, minus the pass caught): **−6.4 points**. Spread 8.3, median −4.4, range
    −29.5 to +0.9; standard error about 2.0.
  - Before the last phase (15 pairs) the gap is −3.8 on average, between −2.9 and −5.5: the −5 and two seconds,
    partly offset because the passer keeps the ball. In the last phase (3 pairs) it is −19.7: two lose the whole
    possession (−29.5); in the third the pass was worth nothing anyway (0).
  - **1 of 18 leaves the offence better off after the Intercept,** by +0.9: Iron Wall v Ball Movement, seed 941, clock
    10. The pass went from a passer on a rim tile to a receiver on a long-two tile. Keeping the ball in the paint, even
    at −5 and two seconds, reads slightly better than the catch on the long two. With one case, that is the only pattern
    I can see.

## 4. For Shaun to decide

- **D-81:** the paired read says an intercept costs the offence about 6 points on average (about 4 before the last
  phase, the whole possession in it), and almost never helps. Options: rule that the cost stands as built; or raise it
  so it never falls short of the −5 a turnover is meant to cost. Before the last phase it averages −3.8, because the
  ball stays with the passer.
- **The analysis ceilings** stay pinned to the old rules, as asked. Nothing new.

## 5. Noticed, not touched

- The random reaction states in the equivalence tool rarely offer a Steal (about 1.5% of them), because random positions
  seldom leave a defender next to the shooter facing him. A biased generator would test Steals faster.
- The paired read reuses the run's own positions. Pairs from app-format runs would need the app's rules, where every
  turnover ends the possession.
