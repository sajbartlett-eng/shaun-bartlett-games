# Step 4 report: shrink the repo

## 1. Changes to the printed game

None.

## 2. What changed

- **Step 3 merged** (pull request 47). Branch `step-04-shrink` from the updated `main`, after the site rebuild landed.
- **`DECISIONS.md`, the five edits:** D-30 and D-36 note that their register rows come in step 9; D-76, D-78 and D-79
  move to Ruled (source: the step prompts that set them; status: built), keeping their numbers; D-103 moves to step 9
  as a scenario-card rule.
- **README:** 923 lines down to 120: what Playmaker is, how to run it (server, link, Windows, logs, command line), the
  folder layout, where things live, how a step works. No link to `OPEN_QUESTIONS.md`. The old README is in
  `docs/history/README_history.md`, word for word, under a one-line note.
- **Moved** (`git mv`, contents unchanged):
  - to `docs/history/`: `SOLVER_REPORT.md`, `REGRESSION.md`, `PROMPT_rules_engine.md`, `GOAL_LIBRARY.md`. No kept
    module reads them at run time (`solver_report.py` writes a solver report; `labels.py` reads `goal_library.json`).
  - to `docs/reports/`: `STEP3M_REPORT.md`, `STEP3N_REPORT.md`, `Step3h_rulebook_drafts.md`.
  - to `docs/runs/3m/`: 2 `3m_*.json`. To `docs/runs/3n/`: 15 `3n_*.json` and `3n_seed/` (9). To `docs/runs/solver/`:
    all 33 files of `solver_results/`.
  - to `archive/engine/`: `deny_report`, `pause_examples`, `rule_test_3h`, `setup_check`, `sim3i`, `solver_round2`.
  - to `archive/tests/`: `test_round2.py` (it tests only `solver_round2`).
- **Paths updated:** `calibrate.py`, `headtohead.py`, `solver_report.py` (the solver results folder);
  `tools/phase_table_3n.py` (reads `3n_seed/`); usage lines in `tools/js_equivalence.py` and `tools/seed_3n.py`; path
  mentions in `tests/test_step3m.py` and `tests/test_step3n.py`; `.gitignore`.
- **New: `pytest.ini`** with `testpaths = tests`, so a bare `pytest` doesn't collect `archive/tests/` (see 4).

| Part | Files before | Lines before | Files after | Lines after |
|---|---|---|---|---|
| `playmaker_engine`, Python | 61 | 19,377 | 55 | 18,082 |
| `playmaker_web`, Python / JavaScript | 7 / 7 | 2,255 / 4,902 | 7 / 7 | 2,255 / 4,902 |
| `tests`, Python (all files) | 36 (46) | 8,281 | 35 (45) | 8,244 |
| `tools` | 14 | 935 | 14 | 935 |
| Markdown at the Playmaker root | 10 | 3,040 | 6 | 1,050 |
| Run data: `docs/` JSON, `3n_seed/`, `solver_results/` | 59 | 18.0 MB | 0 | 0 |
| `docs/runs/` | 0 | 0 | 59 | 18.0 MB |

`dist/` (1.32 MB), `site/` (1.37 MB) and `tests/data/` (2.31 MB) are unchanged.

## 3. What it proves

- No tests were run except `tests/test_rules_current.py`: 18 pass, 0.3 seconds.
- `import playmaker_web.game, playmaker_web.api` works, and so do all 47 kept engine modules, `server`, `view` and
  `build_site`.
- `pytest --collect-only -q`: 588 collected, no errors. The baseline's 573, minus the 3 archived tests, is 570. The 18
  in `test_rules_current.py` (steps 2 and 3) make 588.
- `git diff -M main`: 73 moves, all with unchanged contents.

## 4. For Shaun to decide

- **Nine candidates couldn't be archived:** kept code or kept tests import them. Moving them breaks a command or a test.
  - `soak`: `tests/conftest.py` and 6 test files take the standard test position from it; it also backs the `soak`
    command.
  - `analysis`, `matchups`, `solver_report`: the `ceilings`, `matchups`, `solve`, `solve-all` and `rule-health`
    commands in `cli.py`. Tests: `test_golden_and_regression`, `test_revalidated_live`, `test_rolls_scoring`,
    `test_solver`.
  - `solver_fixes`: `solver_report` needs it.
  - `headtohead`: start positions for `test_advantage`, `test_deny_catch` and `test_passing` (imported at the top of
    each) and `test_revalidated_live`.
  - `defence_check`, `calibrate`, `agreement`: `test_computer`, `test_defence`, `test_revalidated_live`,
    `test_solver`.

  These tests test kept modules and use the candidate as a helper, so they stay where they are. To archive these
  modules: drop the five commands from `cli.py`, and move the helpers the tests use (positions, data loaders) into the
  tests. That's for the step that rebuilds the tests.
- **How the link version is deployed.** GitHub Pages serves the whole repository from `main` (branch, root). On every
  push to `main` that touches `playmaker/`, or a manual run, `.github/workflows/playmaker-site.yml` runs
  `python -m playmaker_web.build_site`. If `site/` or `dist/` changed, it commits them to `main` as "Rebuild the
  Playmaker playtest site" (18 such commits so far). It rebuilds when a bundled engine file changes: step 3 changed
  `register.py`, so the merge was followed by a 2-file rebuild.
  - **Building on release instead is possible.** Switch Pages to "GitHub Actions". A workflow builds the site, then
    uploads the website plus the built `site/` as the Pages artifact, on each push or on a release tag; `dist/playmaker.html`
    becomes a release download. `site/` and `dist/` then leave git, and the bot stops committing to `main`. The
    website's own files deploy the same way.
- **`pytest.ini`:** a bare `pytest --collect-only -q` collected `archive/tests/test_round2.py`, which errors because its
  module moved. A conftest in `archive/` breaks the tests' own `from conftest import P`. The one-line `testpaths =
  tests` fixes it and changes nothing else. Keep it or remove it.
- **README length:** 120 lines covers everything asked. Say if you want more in it.

## 5. Noticed, not touched

- The archived modules keep their old paths (`solver_results/`, package imports); they won't run from `archive/`.
- `BASELINE.md` still describes the state at the tag, `OPEN_QUESTIONS.md` and old paths included, as it should.
- `docs/` still holds the PDF step reports (3h to 3n), `Open_Questions.pdf` and `Solver_Report.pdf`, outside the step's
  list.
