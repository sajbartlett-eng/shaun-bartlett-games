# Step 5 report: retire the old computer, then the one test run

## 1. Changes to the printed game

None.

## 2. What changed

- **Step 4 merged** (pull request 48). Branch `step-05-retire-old-computer` from `main` after the site rebuild finished.
- **The app's last links to the old computer:**
  - `review.py` no longer imports `LEVELS` from `computer.py`. It reads the same file the old computer read
    (`computer_levels.json`), for the wording of logs from steps 3e to 3k. The wording players see is unchanged (the
    two loads are identical). I didn't take the list from `agent.py`, because it differs: it holds only the level
    names, not the habit and concept words those old reviews print. See 4.
  - The `baseline` choice is gone: the branch in `game.py` `_policy`, its `GreedyPolicy` import, and the label in
    `static/app.js`. Asking for it now gets the same error as any unknown level. `GreedyPolicy` stays in `policies.py`
    (the command line's greedy player, `defence.py` and kept tests use it).
  - Setup placement: `Game._auto_place` calls `agent.propose_offence` and `agent.propose_defence`, the step 3m
    engine. Its other branch (preview squares, man-to-man) only ran for the baseline and can no longer be reached.
- **Archived to `archive/engine/`** (10 modules, 5,245 lines): `computer`, `planner`, `setup`, and what exists only
  for them, `advantage`, `capacity` and `guarding`. Also four from step 4's list: `headtohead` and `calibrate` (they
  need the old computer), `defence_check` and `agreement` (their helpers moved to the tests). All are out of the
  browser bundle list. Nothing kept imports any of them.
- **Kept from step 4's list:** `soak`, `analysis`, `matchups` (the `soak`, `ceilings` and `matchups` commands, and live
  tests) and `solver_report` and `solver_fixes` (`solve`, `solve-all`, `rule-health`). None needs the old computer;
  `solve` and `rule-health` were run to check. No command is archived.
- **Data files:** `computer_levels.json` stays, because `review.py` reads it. `goal_library.json` stays, because
  `labels.py` reads it.
- **`tests/helpers.py`:** new, 131 lines. It holds `golden_setup` (copied from `soak.py`, which still uses it) and the
  agreement and defence-set loaders and graders from the two archived modules, word for word. One forced change: in
  one file the two `PATH`s and the two `load`s would clash, so agreement's are named `AGREEMENT_PATH` and
  `load_agreement`.
- **Housekeeping:** the six PDFs (the 3l, 3m and 3n step reports, `Rule_Test_3h.pdf`, `Open_Questions.pdf`,
  `Solver_Report.pdf`) are in `docs/history/`. The README layout rows were brought into line.

| Part | Files before | Lines before | Files after | Lines after |
|---|---|---|---|---|
| `playmaker_engine`, Python | 55 | 18,082 | 45 | 12,839 |
| `playmaker_web`, Python / JavaScript | 7 / 7 | 2,255 / 4,902 | 7 / 7 | 2,252 / 4,902 |
| `tests`, Python (all files) | 35 (45) | 8,244 | 34 (44) | 6,604 |
| `tools` | 14 | 935 | 14 | 935 |

**The test files.** Collected tests, before and after. A split file is copied whole to `archive/tests/` as the
record, and only its live tests stay. A script checked that every kept test is the same text as before, apart from
the import lines pointed at `tests/helpers.py`.

| Label | Files (collected before → after) |
|---|---|
| Live, unchanged | accessibility 1, coach_gate 1, course_boards 2, golden_and_regression 8, intercepts_oq72 16, placement_ui 1, rolls_scoring 32, rulebook_nov 3, rules_current 18, scenarios 48, static 11, step3m 39, step3n 24, teams 4, timer 19, turns_phases 22 |
| Live, helper moved | scouting 25, solver 21, `conftest.py` (`golden_setup`, and in `test_solver` the agreement set, now from `tests/helpers.py`) |
| Live, baseline tests archived | web 15 → 13 |
| Old computer, whole file archived | deny_catch 5 → 0, passing 9 → 0 |
| Mixed, old-computer tests archived | advantage 11 → 1, breaking 39 → 5, breaking_live 7 → 1, computer 37 → 3, defence 9 → 3 (2 use helpers), intercepts_mti 29 → 28, levels_3l 37 → 36, movement 28 → 23, receiver_denial 12 → 11, revalidated_live 6 → 3, rulings_3i 19 → 18, setup_3k 18 → 2, wedge 12 → 10 |

588 collected before, 452 after: 136 archived.

## 3. What it proves

- **The one test run** (`pytest -q`, every kept test): 439 pass, 13 expected failures, 0 fail, 14 minutes 47 seconds.
- **Against the baseline:** 561 pass, 12 expected failures, 0 fail, 573 tests. Since then, 3 tests were archived in
  step 4, 136 in this step, and 18 added in steps 2 and 3. That predicts 452 tests, with 440 pass and 12 expected
  failures. All 136 archived tests passed at the baseline (every expected-failure marker is in `test_step3m` and
  `test_step3n`, which are untouched).
- **The one difference** is a timed exam board. 11 of the 12 marked exam boards failed against their marker, where 10
  did at the baseline. Board 1 passed, and board 14 (variety) failed: 4 different first actions over 20 seeds, the
  most common at 80%. These boards are judged within a time budget, so the result moves with the machine. The
  baseline's files don't record which two marked boards passed; the timed exam file shows boards 1 and 14 passing.
- **No test that passed at the baseline now fails.**
- `tools/js_equivalence.py` skipped: `engine.js` and the modules it ports (`agent`, `decide`, `search`, `goals`,
  `jsbridge`, `actions`, `resolve`, `scoring`) are untouched.
- Imports of the app, the server, the browser build and all 45 kept engine modules pass.

## 4. For Shaun to decide

- **Tests archived because keeping them means changing what they check:**
  - `test_web`: "computer places man to man" and "the computer's turn is reported with rolls and results". Both used
    the baseline, the second to force an intercept on card 3. The reporting and the best-cover setup log they also
    checked are now untested. Fix: a short test of each on a live level, in the step that rebuilds the tests.
  - `test_defence`: "the computer defence logs arrow jobs" (half of it checks that the baseline is a greedy policy).
  - `test_wedge`: "the golden solver search is identical". It checks the solver and the old computer's contest reach
    together.
  - `test_movement`: "every player type follows the movement rules". It drives the old computer to make the moves.
- **The level lists differ.** `agent.py` has the names; `computer_levels.json` also has the habit and concept words
  that reviews of step 3e to 3k logs print. I kept the words by reading the file directly. Options: keep that; or
  drop the old-log wording (old logs would review with names only).
- **Decisions that now describe archived code:** D-72 (who guards whom: `guarding`), D-73 and D-74 ("help pulled",
  "likely closeout defender": `advantage`). Check D-70 (setup) and D-94 (advantage states) against the step 3m engine
  (`agent`, `decide`, which has its own list). Options: mark them retired in `DECISIONS.md`, or restate them for the
  live engine.
- **`docs/build_audit_docs.py`** reads `computer.py` to build `docs/audit/`, so it no longer runs. Options: move it
  and `docs/audit/` to `docs/history/`; or rebuild the audit for the live engine.

## 5. Noticed, not touched

- `Game._auto_place` keeps its no-level branch (preview squares, `man_to_man`), unreachable now; its docstring still
  names the baseline.
- `defence.py` keeps `ReadingDefence` (step 3d); the app uses only `arrow_job` from it. Two live tests grade it.
- `docs/Rule_Test_3h.html` stays in `docs/` (the step named PDFs).
- The live site rebuilds after merge (the bundle list changed).
