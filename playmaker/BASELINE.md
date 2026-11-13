# Baseline: the state at `baseline-3n`

The tag `baseline-3n` marks commit `a4d5709` on `main` ("Step 3n: rebuild the link version (site, dist) with the
JavaScript search core"), the end of step 3n. Paths below are inside `playmaker/`. Figures marked "measured" were
measured at the tag for this file; every other figure is copied from the file named next to it.

## 1. Size (measured)

Committed files only (`git ls-files`).

| Part | Files | Lines |
|---|---|---|
| `playmaker_engine`, Python | 61 | 18,905 |
| `playmaker_engine`, other files (JSON data and the like) | 7 | |
| `playmaker_web`, Python | 7 | 2,255 |
| `playmaker_web`, JavaScript | 7 | 4,902 |
| `tests`, Python | 35 | 8,170 |
| `tests`, all files | 45 | |
| `tools`, Python and JavaScript | 14 | 935 |

The JavaScript in `playmaker_web/static`: `engine.js` 2,004 lines, `app.js` 1,955, `notation.js` 384, `coach.js` 191,
`trainer.js` 163, `records.js` 133, `pyodide-adapter.js` 72.

Committed built files and data:

| Path | Files | Size |
|---|---|---|
| `dist/` | 1 | 1.28 MB |
| `site/` | 10 | 1.34 MB |
| `docs/3n_seed/` | 9 | 5.61 MB |
| Other JSON in `docs/` (top level) | 17 | 6.89 MB |
| `solver_results/` | 33 | 5.50 MB |
| `tests/data/` | 10 | 2.31 MB |

The three largest JSON files in `docs/` are `3n_aggregate_rows.json` (2.94 MB), `3n_f5_tabletop.json` (1.94 MB) and
`3n_f5_digital.json` (1.88 MB).

## 2. Engine modules the app uses (measured)

Imports followed from every Python file in `playmaker_web/`, through the engine, including imports inside functions.

**Reached (32):** actions, advantage, agent, board, capacity, cards, computer, decide, defence, geometry, glicko2, goals,
guarding, jsbridge, labels, levels, plain, planner, policies, resolve, review, rosters, rules_config, scenarios, scoring,
scouting, search, solver, solver_config, state, timer, trainer.

**Not reached (20)**, each with the first line of its docstring:

| Module | What it was for |
|---|---|
| agreement | Agreement test set: 50 small endgames solved exactly, used to judge evaluation variants. |
| analysis | First-turn ceilings: the legacy scenario_tests.py model, and the same question under engine rules. |
| calibrate | Calibrate the computer levels (step 3e, section 8.4). |
| cli | Command line: show, play, test, soak, ceilings. |
| defence_check | How close the computer defence plays to the exact solver (step 3e). |
| deny_report | Research tool: how a pairing's possessions end against the computer defence. |
| exam | Step 3m B9: the exam (validation, not rules). |
| headtohead | Head-to-head calibration of the computer levels (step 3e, revised). |
| matchups | Pair-by-pair closeout check: every offence card against every defence card, every shot type. |
| pause_examples | Step 2b section 2.3: positions where the best defence is Pause, with the alternatives' values. |
| register | Step 3n Part K: the shared rules register. |
| rule_test_3h | Step 3h: a short comparison of four rule variants (not adopted). |
| selfplay | Step 3m: engine self-play (seeding the phase table, the aggregate check). |
| setup | Step 3k: the computer's setup (rulebook setup steps 4 and 5), offence and defence. |
| setup_check | Step 3k short check (research tool): All-Star v All-Star from the computer's own setups. |
| sim3i | Step 3i: the one combined simulation (research tool, not part of the game). |
| soak | Random-vs-random soak with invariants checked after every apply. |
| solver_fixes | Suggested card fixes: setup changes only (squares, arrows, clock, teams). |
| solver_report | Solve scenario cards and write SOLVER_REPORT.md. |
| solver_round2 | Round 2 of the solver programme (step 2b, sections 3 to 6). |

`__main__` (the `python -m playmaker_engine` entry) has no docstring and isn't reached by the app either.

## 3. Tests

From `docs/STEP3N_REPORT.md`: 573 tests, 561 pass, 12 expected failures, 0 fail, 42 minutes. Not rerun for this
file.

## 4. The exam

All-Star at fixed depth 4 from `docs/3n_exam_fixed4.json`; the time-budgeted run (budgets x 0.25, all three levels) from
`docs/3n_exam_timed.json`.

| # | Board | Fixed depth 4 (All-Star) | Timed: All-Star | Timed: Starter | Timed: Rookie |
|---|---|---|---|---|---|
| 1 | Straight lane | FAIL | PASS | FAIL | FAIL |
| 2 | Sag by shooting | PASS | FAIL | FAIL | PASS |
| 3 | Help the helper | FAIL | FAIL | FAIL | FAIL |
| 4 | Two threats, one answer | FAIL | FAIL | FAIL | FAIL |
| 5 | Closeout | FAIL | FAIL | FAIL | FAIL |
| 6 | Catch window | FAIL | FAIL | FAIL | PASS |
| 7 | Clock | FAIL | FAIL | FAIL | FAIL |
| 8 | Backdoor | FAIL | FAIL | FAIL | FAIL |
| 9 | Corner relocate or kick | FAIL | FAIL | FAIL | FAIL |
| 10 | Steal odds | FAIL | FAIL | FAIL | FAIL |
| 11 | Contested pass | FAIL | FAIL | FAIL | FAIL |
| 12 | Strong-side corner | PASS | PASS | PASS | PASS |
| 13 | Spacing | FAIL | FAIL | FAIL | FAIL |
| 14 | Variety | FAIL | PASS | PASS | FAIL |
| 15 | Goal consistency | PASS | PASS | FAIL | PASS |
| 16 | Capacity drain | FAIL | FAIL | FAIL | FAIL |
| 17 | Turn economy | PASS | PASS | PASS | PASS |
| | **Passes of 17** | **4** | **5** | **3** | **5** |

Both files judged board 1 by the earlier geometry check. Board 1 judged by outcome, at fixed depth 4 over 10 seeds
(`docs/3n_board1.json`): 10 of 10 pass, the straight drive available after the defence's answer in 10 of 10. Board 7
rerun at fixed depth 4 on the rebuilt phase table (`docs/3n_exam_board7_newtable.json`): fail.

## 5. Computer levels

Phone timing (`docs/3n_phone_timing.json`; the link version, Chromium 412 x 915, 4x CPU throttle):

| Level | Budget | Decisions | Median time | Max time | Median depth | Max depth | Leaves per second |
|---|---|---|---|---|---|---|---|
| Rookie | 0.3 s | 6 | 0.086 s | 0.34 s | 2 | 2 | 476 |
| Starter | 1.0 s | 29 | 1.005 s | 1.031 s | 2 | 3 | 1,896 |
| All-Star | 2.5 s | 49 | 2.508 s | 2.533 s | 3 | 6 | 1,286 |

Anchors (`docs/3n_anchors.json`; 12 matches of 4 possessions per pairing, Senior Pro digital):

| Pairing | Match score of the first level | Rating gap |
|---|---|---|
| Rookie v Starter | 0.403 | -68.3 |
| Starter v All-Star | 0.472 | -19.7 |
| Rookie v All-Star | 0.353 | -105.5 |

Fitted Senior anchors: Rookie 1525, Starter 1600, All-Star 1625.

Accuracy by level (`docs/3n_accuracy.json`; k = 2.0; targets 90, 75, 55):

| Level | Decisions graded | Possession accuracy | Per-decision accuracy |
|---|---|---|---|
| All-Star | 138 | 76.3 | 85.6 |
| Starter | 128 | 70.1 | 81.8 |
| Rookie | 91 | 68.2 | 81.5 |

## 6. Basketball checks

F5 (`docs/3n_f5_report.json`; 60 possessions each, All-Star v All-Star, Senior Pro):

| Per 100 possessions | Target | Digital | Tabletop |
|---|---|---|---|
| Steals | about 8 | 18.3 | 3.3 |
| Steal attempts | | 46.7 | 18.3 |
| Turnovers | about 13.6 | 18.3 | 18.3 |
| Reach fouls | fewer than steals | 16.7 | 8.3 |
| Team fouls per quarter | about 4 to 5 | 4.5 (3.5 in the one full quarter) | not counted |
| Points per possession | | 23.83 | 25.68 |
| Contested passes per possession | | 0.27 | 0.30 |
| Most locked pieces in one phase | | 1 | 2 |

Tabletop turnovers split (`docs/3n_f5_tabletop.json`, 60 possessions): 11 in all; 6 are shot-clock expiries (the
possessions that ended on a forced shot) and 5 are the rest (successful steals and interceptions).

Steal attempts by position: digital, in front after moving 13, in front from a standstill 7, level or behind 8;
tabletop, 5, 4 and 1, and 1 not recorded. Why no Intercept: no legal Intercept 99 times digital and 116 tabletop; could
intercept and chose not to 16 and 16; attempted 0 and 2.

The aggregate (`docs/3n_aggregate_report.json`; 100 possessions, All-Star v All-Star, Senior Pro digital):

| Figure | Value |
|---|---|
| Points per possession | 25.25 |
| Steal attempts, successes | 44, 10 |
| Turnovers per 100 | 10.0 |
| Intercept attempts | 0 |
| Dribbles, drive success | 32, 50% |
| Help depth, help shade | 0.679, 0.866 |
| On-ball defender on the ball-rim line | 12.7% |
| Shots by phase (1 to 6) | 28, 21, 9, 10, 6, 26 |
| Tight contests by phase (1 to 6) | 39%, 33%, 44%, 30%, 33%, 23% |
| Points by the phase a possession ended (1 to 6) | 21.1, 22.9, 27.9, 25.2, 27.5, 30.2 |
| Unnamed actions (from a Hesitate) | 41 (3) |

## 7. Open items

`OPEN_QUESTIONS.md` has 77 numbered rows. Counted by the word in each row: 26 ruled, 8 closed, 43 with neither word
(open, or settled by a default the row doesn't mark as ruled).

Tests marked as expected failures at the tag: 14 markers in the test files. The step 3n run counted 12 expected
failures: the exam marker only applies when a board fails, and two of the marked boards passed in that run (the files
don't record which).

| Test | Reason, in one line |
|---|---|
| `test_step3n.py` V by phase never rises | V rises from 24.9 in phase 1 to 29.5 in phase 6 at Senior Pro. |
| `test_step3n.py` All-Star reaches with 0 team fouls, declines with 4 | On the rebuilt table the bonus no longer deters a reach. |
| `test_step3m.py` exam board 1 | The defence doesn't put a defender on the ball-rim line. (Since D-165 the board's answer is X2's Quick Step to D6, the best by play.) |
| exam board 2 | A speed problem: passes at fixed depth 4, fails within the Python budget. |
| exam board 3 | The low man doesn't step up to help on the beaten drive. (Since D-165 the board's answer is that nobody moves, the best by play.) |
| exam board 4 | The overload isn't detected. |
| exam board 5 | The receiver drives on both closeout boards. |
| exam board 7 | The clock change doesn't change the choice. |
| exam board 8 | The denied receiver doesn't cut backdoor. (Since D-165 the board's answer is O2's cut to E10 and O1's pass, the best by play.) |
| exam board 9 | Neither the kick nor the corner relocation is chosen. |
| exam board 11 | The contested-pass boards don't separate early from late. |
| exam board 13 | The attacker in the driving lane isn't moved out of it. |
| exam board 14 | One first action reaches 80% on the rebuilt phase table. |
| exam board 16 | All-Star doesn't find the drain sequence in its first turn. |

