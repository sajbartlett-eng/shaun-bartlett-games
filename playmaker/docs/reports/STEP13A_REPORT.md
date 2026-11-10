# Step 13, part A report: finish stage 1

**Stopped here for Shaun's approval. Part B is not started.**

## The stability result: off against cheap

"Cheap" is `quiet_points`, `like_with_like` and `tempo` together. Boards 2, 7, 9, 10 and 16 give 8 decisions. Each
had 200 s. The run took 27 of its 30 minutes (`docs/runs/step13/stability_*.json`).

| | Off | Cheap |
|---|---|---|
| Decisions that reached 4 team turns ahead | 8 of 8 | 1 of 8 (the other 7 reached 3) |
| First action changes from 1 to 3 team turns ahead | 4 of 8 (2 A, 2 B, 10 A, 10 B) | 3 of 8 (2 B, 7 B, 10 B) |
| First action changes from 2 to 4 | 1 of 8 (2 B) | 1 of 1 measured (7 B) |
| Median time to finish 1, 2, 3, 4 team turns ahead | 0.24, 1.06, 8.2, 46.8 s | 0.23, 3.3, 46.8 s, not reached |

- **Cheap doesn't remove the flips:** 3 of 8 against 4 of 8, and it adds one on board 7 B (pass at 1 and 2, the
  mid-range shot at 3 and 4).
- **Cheap isn't cheap.** The same look-ahead takes 3 times as long at 2 team turns and 6 times at 3.
- **The exam is lower with cheap on** (the All-Star; `exam_*.json`, 14 of the 20 minutes used):

| | Off | Cheap | Light (`like_with_like`, `tempo`) | Rest (all but `quiet_points` and `clear_reason`, with the reach map) |
|---|---|---|---|---|
| 1 pair ahead | 9 of 19 | 7 of 19 | 7 of 19 | **10 of 19** |
| The clock | 9 of 19 | 8 of 19 | 8 of 19 | **10 of 19** |

- Cheap loses boards 2 and 12. On the clock it gains 16, and 10 of its 19 boards finish only 1 team turn.
- **Which switch does what** (1 pair ahead, each alone, `parts_*.json`):
  - `like_with_like`: 9, nothing changes. Free.
  - `tempo`: 7. It loses boards 2 and 12.
  - `quiet_points`: 8. It loses board 2, and takes 3 times as long.
  - `play_on`: 9. It gains board 7 and loses 16.
  - The reach map: 9, nothing changes.
  - `play_on` with the reach map: 10. It gains board 7 and keeps 16.

## The speed-ups and their gains

Where the time goes (`profile_*.json`, the 8 decisions, 1 pair ahead):

- **Everything off:** the reading is over 80% of the time. The defence's best cover is 42%, each attacker's looks 35%,
  move generation 7%. Clearing memory is 24%.
- **`play_on` costs 4%.** Its branching is 1.6% of the time and its check 6.5%. Step 12 said it was most of the cost.
  That was wrong.
- **`quiet_points` costs 7.5 times the positions read** (35,140 against 4,687). Each one costs the same as before.
- **The reach map cost 21 times,** all in one place: each defender's exact movement was rebuilt for every pass lane of
  every reading (70% of the time).

Built, each proved to change nothing:

| Speed-up | Before | After | Gain |
|---|---|---|---|
| The reach map kept per position, and across moves that don't touch a defender's paths (reach map on) | 103.0 s | 10.4 s | **9.9 times** |
| Forcing replies generated without the full move list (cheap with `play_on`) | 32.1 s | 32.7 s | none |
| `play_on`'s check shares the reading the ordering already made (cheap with `play_on`) | 34.0 s | 32.7 s | 1.04 times |
| A position's best turn from the shorter look-ahead tried first (off, 3 team turns ahead) | 56.7 s | 55.7 s | 1.02 times |

Times are the 8 decisions at 1 pair ahead (`speed_*.json`). With the reach map on, the search is now 1.2 times the
time of off, not 21 times. The other three are in, but the
time is in the reading, not in the search around it.

## The budget proposal

`docs/SPEED_BUDGET_PROPOSAL.md`. Each level finishes 1 pair on 9 decisions in 10:

| Level | Desktop | Phone |
|---|---|---|
| Rookie | 0.3 s | 1.0 s |
| Starter | 1.0 s | 2.0 s |
| All-Star | 2.5 s | 3.0 s |

- Off, light and rest fit, or come within 20% on a phone.
- Any set with `quiet_points` needs to be 2.5 to 8 times faster on a desktop and 6 to 16 times on a phone.

## 1. Changes to the printed game

None. Every switch is off, and the game plays as before.

## 2. What changed

- **Step 12 merged** (pull request 56). D-119, D-120 and the D-115 extension are recorded. `CLAUDE.md` has the time
  caps, the speed budget and the report's sixth item.
- **`search.stable` is five switches** in `search.py` and `engine.js`, each off: `quiet_points`, `like_with_like`,
  `tempo`, `play_on`, `clear_reason`. `search.stable` turns on all five. The measured tempo numbers moved to
  `search.tempo_gap`, so that `search.tempo` can be the switch.
- **The speed-ups** above, in `engine.js`. Each can be turned off by a tool, to time and prove it. The ordering one is
  in `search.py` too. The Python search is otherwise unchanged and stays the reference.
- **Tools:** `tools/exam_13.py` (settings, stability, levels, pair times, records), `tools/profile_13.js`,
  `tools/exam_13_summary.py`; `tools/js_equivalence.py` takes `--switches` and `--without`. Each search now records
  the time at which each look-ahead finished.

## 3. What it proves

- **The split changes nothing:** with all five on, the search gives the same values, choices and counts as step 12's
  code (4 decisions).
- **The engines agree, 0 mismatches,** for each switch alone, cheap, cheap with `play_on`, and all five: 10 whole
  searches each, values and choices (`js_equivalence_*.json`).
- **Each speed-up changes nothing:**
  - JavaScript against the unchanged Python, 0 mismatches with the speed-ups on and with them off: all five switches
    (10 searches), the reach map (8 searches, and the map square by square on 56 positions), everything off (12).
  - The same choices and values with and without each, on the 8 decisions (`speed_*.json`).
- **Tests, switches off:** `test_rules_current`, `test_static`, `test_step3n`, `test_step3m`: 78 pass, 13 expected
  failures, 1 unexpected pass, twice. Step 12 logged 11 expected failures. The 2 extra are exam boards, which that
  test runs on the Python search's clock (board 2 is one). Run alone, the exam-board tests give the same on step 12's
  code and on this step's, with the ordering speed-up on or off: 8 pass, 9 expected failures.
- **Caps:** stability 27 of 30 minutes; the exam 14 of 20; the levels 19 of 30. All finished.

## 4. For Shaun to decide

- **Switch cheap on? I'd say no.** It scores 7 and 8 against 9 and 9, doesn't remove the flips, and breaks the budget.
  - **The rival: "rest".** `like_with_like`, `tempo` and `play_on`, with the reach map. It scores 10 and 10, the best
    measured, at 1.35 times the time. It fits the desktop budget and is 10 to 20% over on a phone.
  - Or `play_on` with the reach map only: 10 at 1 pair. Not run on the clock.
- **`quiet_points`: leave it off.** The flips it was aimed at are swings between odd and even look-aheads.
  `like_with_like` takes the answer from even ones only, where 1 of 8 changes, at no cost.
- **`tempo`:** accepted as measured (D-119), but alone it loses boards 2 and 12. In "rest" both pass.
  Option: keep it off until part B is in, then measure again.
- **The budget targets** in the table above.
- **Speed-ups that change results** (measured in a scratch copy, not built):
  - **A window at the root.** Turns more than 6 points behind the best stop being valued exactly. 15 to 19% faster,
    and the same choice and best value on 8 of 8 decisions. Cost: the trainer's numbers for clearly worse turns become
    "at most". I'd take it only if "rest" must fit a phone exactly.
  - **Narrow `quiet_points`:** a side's second action from its best 6, not 24. 1.5 times faster, but 3 of 8 choices
    change, and it needs 8 to 16 times. Not recommended.

## 5. Noticed, not touched

- **One speed-up that changes no result isn't built:** the look builder makes a record for every square an attacker
  can shoot from, then keeps 6. That's most of the memory clearing. It needs a rewrite of the builder for about 10 to
  20%, so it waits for a step where the budget needs it.
- **Cheap, 4 team turns ahead:** not reached in 200 s on 7 of 8 decisions, so its 2 to 4 comparison rests on 1.
- **All five switches with the reach map, in Python:** too slow for whole searches (stopped after 10 minutes). The
  two were proved apart.
- **A fresh engine's first decision** takes about twice as long as a warm one.
- **Under cheap the Starter is slower than the All-Star,** because it reads the opponent as a mix and can't prune.
- **"Rest" and "light"** are extra settings I added to find which switch costs what. They ran inside the caps.
- **The off exam was run again** beside cheap, so both columns come from the same conditions.

## 6. Model for the next step

Claude Fable 5.2, effort high. Part B is open design work (choosing and proving the allocation method) across both
engines.
