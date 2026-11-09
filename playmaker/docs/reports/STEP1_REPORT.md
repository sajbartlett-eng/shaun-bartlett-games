# Step 1 report: freeze the baseline and set the ground rules

The tag `baseline-3n` is made but not pushed: the session's GitHub connection refused the tag (see 4). No code, data or
tests changed.

## 1. Changes to the printed game

None.

## 2. What changed

- Three new files, nothing else: `playmaker/CLAUDE.md` (the working rules, word for word as given, including the
  updated Tests section), `playmaker/BASELINE.md` (the state at the tag) and this report.
- The files sit in `playmaker/`, the Playmaker project root, not the repository root. The repository root is the games
  website; every path the step names (`reference/`, `docs/rules_register.md`, `OPEN_QUESTIONS.md`, `dist/`, `site/`)
  exists only under `playmaker/`.
- The annotated tag `baseline-3n` is on `main` at `a4d5709`, with the given message, in the local repository only.
- Branch `step-01-ground-rules`, pull request to `main`, not merged.

## 3. What it proves

- No tests were relied on. Under the first version of this step I started the full suite at the tag. When the updated
  step arrived I stopped it, about three quarters through, and kept nothing from it. No tuning, self-play, exam or solver
  ran.
- `BASELINE.md` copies each figure from its source file and names it: the step 3n test counts
  (`docs/STEP3N_REPORT.md`), the exam (`docs/3n_exam_fixed4.json`, `docs/3n_exam_timed.json`), phone timing, anchors,
  accuracy, F5 and the aggregate (`docs/3n_*.json`). Measured: the sizes (`git ls-files` at the tag) and the modules the
  app reaches (imports traced from `playmaker_web/`: 32 reached, 20 not).
- `git diff --stat main` on the branch: 3 files added, nothing else.

## 4. For Shaun to decide

- **Pushing the tag.** The GitHub connection in this session accepts branch pushes but refused the tag push (a 403
  from the access proxy). Options: push it yourself from a clone (`git fetch origin main`, then
  `git tag -a baseline-3n a4d5709 -m "State at the end of step 3n, before the step 1 to 16 clean-up."` and
  `git push origin baseline-3n`), or create a release named `baseline-3n` on commit `a4d5709` in GitHub, which makes the
  same tag. Until then, `a4d5709` is the baseline commit.
- **Where CLAUDE.md lives.** Options: keep it in `playmaker/`, where its relative paths resolve and it governs work in
  the Playmaker folder; or move it to the repository root, where it would govern all work in the repository, the website
  too, and its paths would need a `playmaker/` prefix. The step's paths favour `playmaker/`. Left there.

## 5. Noticed, not touched

- **Lock tokens.** `OPEN_QUESTIONS.md` row 32 is ruled "no cap" because a phase makes at most 4 new locks (2 Dribbles, 2
  Challenges), matching the rulebook's 4 lock tokens. Since step 3n F1 a failed Steal also locks, so up to 6 can come in
  one phase. The ruling's reasoning no longer holds. The register's token list says so; row 32 doesn't.
- **Exam board 1 has two verdicts.** `docs/3n_exam_fixed4.json` and `docs/3n_exam_timed.json` judged it by the old
  geometry check (the ball-rim line). `playmaker_engine/exam.py` now judges it by outcome (`docs/3n_board1.json`: 10 of
  10 pass). The expected-failure reasons for boards 1 and 7 in `tests/test_step3m.py` still describe the old check and
  the old phase table.
- **`setup.py` is shipped but unused.** The browser bundle (`playmaker_web/build_site.py`) includes it, but the app never
  imports it; `agent.py` has its own setup search. Only `setup_check.py` uses it.
- **Lock count measurement.** The F5 runs count locked pieces before each action, so a lock made by a phase's last
  action isn't counted; "most locked pieces in one phase" (1 digital, 2 tabletop) may be low.
- **Two `tools/` folders.** The repository root has its own `tools/`, apart from `playmaker/tools/`.
