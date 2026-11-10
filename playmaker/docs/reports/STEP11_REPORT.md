# Step 11 report: switch on the adjusted position value

## 1. Changes to the printed game

None.

## The exam on the clock, against step 10

The All-Star, the JavaScript search, `relative` by default. P = pass, F = fail.

| Board | Step 10, relative, on the clock | Step 11 (the new default) |
|---|---|---|
| 1 Straight lane | F | F |
| 2 Sag by shooting | P | P |
| 3 Help the helper | F | F |
| 4 Two jobs, one defender | P | P |
| 5 Closeout | F | F |
| 6 Catch window | F | F |
| 7 Clock | P | **F** |
| 8 Backdoor | F | F |
| 9 Corner | F | F |
| 10 Steal | F | F |
| 11 Contested pass | F | F |
| 12 Strong-side corner | P | P |
| 13 Spacing | F | F |
| 14 Variety | P | P |
| 15 Goal consistency | P | P |
| 16 Wearing out one defender | P | **F** |
| 17 Turn economy | P | P |
| C1 Deny the shooter's catch | P | P |
| C2 Clean pass | P | P |
| **Passes (of 19)** | **10** | **8** |

**Why 7 and 16 differ: the computer now looks further on the clock, not the new averages.**
- The exam boards are all Senior Pro, whose averages are unchanged.
- At a fixed 3 moves ahead, both boards give the same choice and pass, as in step 10.
- Step 10's clock run shared four cores with three other runs; this one ran alone. Board 7 reached 4 moves ahead
  where step 10 reached 3, and board 16 reached 4 where step 10 reached 3.
- Two more clock runs of the two boards gave the same failures.
- **Board 7 B:** looking 4 moves ahead, O3 sprints out to E9 instead of shooting.
  - With 2 tokens left, a one-action turn isn't the offence's last: he keeps a token for another turn.
  - So the final-turn rebuild holds only when the offence uses both actions. Making it 1 token would make it final
    whatever he does.
- **Board 16:** looking 4 moves ahead, the computer plays O2's move first and O1's sprint second. Its line no longer
  ends in the pass to O3, and the possession reads 23.1 instead of 42.5.

## 2. What changed

- **Step 10 merged** (pull request 54). Branch `step-11-relative-on` from `main`.
- **`DECISIONS.md`** ("Shaun, 10 Nov 2026"):
  - **D-92 ruled:** relative by default, with only the continuation read against the average.
  - **D-114:** the averages (the 100 positions is provisional).
  - **D-115:** the driving-lane term moved to the goals design (plan step 12).
  - **D-116:** the failing boards kept as targets.
- **`ai_profiles.json`:** `eval.leaf_mode` is `relative` in both engines (they read the same file); `floor` stays the
  other setting.
- **`tools/relative_average.py`** builds the scaled averages (D-114) and writes each level and phase's source to
  `eval.relative_average_source`. The run is in `docs/runs/step11/relative_average.json`.
- **`tools/js_equivalence.py`** now uses the configured mode unless `--leaf-mode` names one.
- **A step 10 slip, fixed:** the averages filed the semi-pro levels as "semi-pro", but the engine names them
  "semi_pro". In step 10, under relative, semi-pro games used Senior Pro's averages. They now use their own scaled
  ones.

## 3. What it proves

- **Which levels and phases use scaled averages:** all but Senior Pro, at every phase.
  - Senior Pro is the base (160, 114, 84, 65, 48 and 41 positions for phases 1 to 6).
  - No other level has 100 positions at any phase; the most is 16. So the other eight age and standard tables use
    Senior Pro's average scaled by their phase table.
  - Junior Semi-pro in phase 1, for example: 15.58 × 13.44 / 24.89 = 8.41.
- **Equivalence** (`--n 200`, the default, relative): 0 mismatches (`docs/runs/step11/js_equivalence_200.json`).
- **The tests for the changed files** (`test_rules_current`, `test_static`, `test_step3n`, `test_step3m`): 78 pass, 13
  expected failures, 1 unexpected pass, 0 fail, once the one mode below is stated.
- **The test whose mode I made explicit:**
  - `test_step3m.py::test_horizon_credit_on_the_capacity_drain_board` now uses a new fixture, `floor_leaf`, which
    states `floor`. What it checks is unchanged.
  - Under relative, O3's lift reads +0.51 over the phase where the test asks for more than 1.0 (+2.06 under floor).
  - With `floor` stated it passes, as on `main`.
- **Unexpected pass:** `test_an_early_cut_is_flagged_with_a_legal_reorder` (D-112) now passes under relative. It
  stays marked as an expected failure, as ruled, until the goals step.

## 4. For Shaun to decide

- **Board 7 B:** make it 1 token, so the offence's turn is final whatever it does; or keep 2.

## 5. Noticed, not touched

- **How far the computer looks on the clock moves with machine load:** 3 to 4 moves ahead on boards 7 and 16 here.
  Boards near a tie can flip between runs, so the clock exam is a noisy measure. The fixed 3 moves ahead is the stable
  one.
- The test runs rewrite two screenshots in `docs/`; I restored them.
