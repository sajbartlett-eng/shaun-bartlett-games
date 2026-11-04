# Playmaker rules engine

Step 1 of the solver programme: the rules of Playmaker as code. Python 3.11+, standard library only
(pytest for the tests).

## Run it

From this folder (`playmaker/`):

```
python -m playmaker_engine show 6                                   # print scenario 6's board
python -m playmaker_engine play 6 --offence greedy --defence greedy --seed 1
python -m playmaker_engine play 8 --offence random --defence greedy --seed 4 --target 5
python -m playmaker_engine test                                     # full suite, ~80 s on 4 cores
python -m playmaker_engine soak --games 10000                       # random v random, invariants
python -m playmaker_engine ceilings                                 # REGRESSION.md table (~100 s)
python -m playmaker_engine matchups                                 # closeout check, every card pairing
```

`PLAYMAKER_SOAK_GAMES=500 python -m playmaker_engine test` shortens the soak while iterating.

## Play from a link (no install: laptop or phone)

**https://sajbartlett-eng.github.io/shaun-bartlett-games/playmaker/site/**

The link version runs the same Python engine inside the browser (Pyodide 0.26.4 from cdn.jsdelivr.net;
about 10 MB the first time, cached after). It plays hot-seat, against the computer, all 16 scenario
cards, full matches with placement, and Coach's Call. **Remote play** (two browsers in one game) needs
the server version below. The solver-backed review is not in the link version (too slow in the browser):
download the log and run `review` on a computer.

There is also a single self-contained file, `playmaker/dist/playmaker.html` (engine and data inside;
only Pyodide comes from the CDN), to share or host anywhere.

**Switching the link on (one time).** GitHub Pages already serves this repository from `main`, so the
link works as soon as this work is merged into `main`:

1. On github.com open the repository, then **Pull requests → New pull request**.
2. Base: `main`; compare: the branch with this work. **Create pull request**, then **Merge pull request**.
3. Open **Settings → Pages** and check *Source* says **Deploy from a branch**, branch **main**, folder **/ (root)**.
4. Open **Settings → Actions → General → Workflow permissions**, choose **Read and write permissions**, **Save**
   (lets the build workflow commit the rebuilt site).
5. Wait a minute or two, then open the link.

**Updating it.** Every push to `main` that touches `playmaker/` runs *Build Playmaker playtest site*
(`.github/workflows/playmaker-site.yml`), which rebuilds `playmaker/site` and `playmaker/dist`; Pages
then publishes them. To rebuild by hand: `python -m playmaker_web.build_site`.

## Play on Windows without the link

1. Install Python from **python.org** (Downloads → Windows). In the installer, tick **Add python.exe to PATH**.
2. On the repository page on GitHub: **Code → Download ZIP**. Unzip it.
3. Open the unzipped folder, then the `playmaker` folder inside it. Click the address bar, type
   `powershell` and press Enter.
4. Type `py -m playmaker_web` and press Enter. Open **http://localhost:8765** in your browser.
5. Stop it with Ctrl+C in that window.

## Where the logs go

- **Link version:** in the browser tab only. At the end of a game, after the feedback form, use
  **Download log** (a `.jsonl` file named `<date>_<code>.jsonl`) or **Copy log** (paste it into an email
  on a phone). Closing the tab without downloading loses it.
- **Server version:** `playmaker/playtest_logs/<date>_<code>.jsonl`, written as you play.
- Either log works with `python -m playmaker_engine review <file>.jsonl`.

## Playtest in the browser (step 3)

```
python -m playmaker_web                 # serves http://localhost:8765 (add --port N to change it)
```

Open the page, pick **Full game** (two possessions, sides swap, the preview pack's table setup),
**Scenario card** (any of the 16) or **One possession**, then **Hot-seat** (one screen) or **Remote**.
Tick *computer plays offence/defence* to play alone against the test opponent (the greedy baseline:
it is a sparring partner, not a strong player).

- **Playing:** click one of your players (or Tab to it and press Enter), then an action. Only the
  engine's legal actions are offered. Squares, receivers and T directions light up; defenders pick an
  arrow after choosing a square. Turn-enders have dashed borders and say "(ends turn)". With the ball
  carrier selected, the arrow lines it can't cross are drawn; every pass lists which defenders could
  intercept it. Both sides see the same help.
- **Rolls:** before a roll the page says what is needed ("Pass 18 v Intercept 5: success on 13 or less").
  The server rolls from the game's seed; the page never rolls. The d20 face shown is the one the
  engine used.
- **Coach's Call:** the offence picks its target privately at the start (hot-seat: the defence looks
  away); it is revealed after the shot.
- **Undo:** hot-seat only, back to the last roll. In a remote game both players must agree.
- **Remote play through a tunnel:** everything runs on one port, so one tunnel is enough:
  `cloudflared tunnel --url http://localhost:8765` (or `ngrok http 8765`). Start a Remote game, pick
  your seat, and send the other player the tunnel URL plus the code shown at the top. They choose
  **Join a remote game**, enter the code and take the other seat. A direct link also works:
  `https://<tunnel>/?code=ABC123` fills in the code.
- **Logs:** every game writes `playtest_logs/<date>_<code>.jsonl`: the setup (teams, scenario, seed),
  every action with the legal alternatives at that moment, every roll with its probability and face,
  the time per decision, the score and band, and the five feedback answers from the end screen.
- **Review a log:** `python -m playmaker_engine review playtest_logs/<file>.jsonl [--budget 5]` replays
  the game and shows, at each human decision, the solver's preferred action and the gap in value.
  It is "where the solver disagreed", not a list of mistakes: the solver's values are estimates.

- **The contest is the defence's decision:** after its reaction, the defence picks who contests
  (each option shows its contest value, and whether it is clean or carries a foul roll), or not to
  contest. At clock 0 the offence picks the forced shot's type.
- **Full-game setup:** the offence places its five pieces (ball on plain wood beyond the three-point
  tiles), then the defence places its five and sets the arrows; or use the preview table setup.
  **The computer places like this:** on offence, the preview squares; on defence, man-to-man: each X on
  the empty square next to its man that is closest to the rim (ties in compass order), arrow on its man.

Screenshots: `docs/playtest_mid_possession.png` (laptop), `docs/playtest_phone_portrait.png`,
`docs/playtest_contest_decision.png`, `docs/playtest_match_end_feedback.png`,
`docs/playtest_scenario_card.png`, `docs/playtest_end_of_possession.png`.

## Scouting and detail levels (steps 3c and 3d)

**The rule: the screen may arrange information, never judge it.** It can put two cards side by side,
mark ▲ and ▼ values (the bands come from the locked range table), and say which defender can contest
or intercept. It never says what a play is worth before you commit, never ranks your options and never
tells you what to do. Judgement only appears after the game, in the review, and solver numbers there are
labelled "estimate". The word "mistake" never appears.

- **Card comparison:** tap or click a piece and its card opens beside its matchup's card (the
  defender whose arrow points at it, otherwise the nearest). "Next matchup" flips through the others.
- **Matched-value chips:** every pass, dribble, screen, steal, intercept, challenge and shot shows the
  two ratings that meet, for example "Pass 18▲ v Intercept 5▼ (X3)". No odds, no point sums.
- **Scout report (step 3d):** written the way a scout writes: strengths and weaknesses only, in
  words, no numbers and nothing average. Team lines come first (for example "fast and athletic · moves the
  ball · inside-out"), then each player's offence and defence, at most 3 strengths and 3 weaknesses
  each, with a mini shot chart (solid = ▲ zone, hatched = ▼ zone). Every phrase traces to a ▲ or ▼ on the
  card; every team line to a threshold. All wording, thresholds and pairings live in
  `playmaker_engine/scout_phrases.json`, so they can be reworded without touching code. Phrases that are
  typical for a position (computed from all 75 cards) drop down the order, so the unusual ones show first.
- **Read the cards first (Scout level):** each player makes the scouting call from the cards alone.
  The offence picks one matchup to hunt and the defence one weakness to protect (both, in a full match).
  The call locks when saved, then the report unlocks for that player (hot-seat: once both have locked).
  Calls stay hidden from the other side until the review.
- **Custom teams:** pick "Custom team…" in either team list. Choose one card per position from all 75,
  or load a prescribed team as a start. A tier shape other than BBBBB, ABBBC or AABCC is allowed but
  labelled experimental in the log. Both sides using the same card gets a warning (the table game would
  need two card sets).
- **Post-game review:** (1) your call next to the team-sheet calculation, (2) the three biggest ▲ shot
  edges the board offered and whether you used them, (3) where a short solver search disagreed, as
  estimates (server version only; the link version says how to run it on the log), (4) **the report in
  play**: for each scout line, the plain counts from the log ("12 passes, 0 intercepted") or "not
  tested", (5) a reflective question saved with the log.

| Level | Scout report | During | After |
|---|---|---|---|
| **Learn** | Team lines and player lists at once, plus Mismatches in words for each numbered pairing (O1 v X1 ...), both directions | Chips and card comparison | Full review |
| **Scout** (default) | Team lines and player lists, unlocked after your call locks | Chips and card comparison | Full review |
| **Pro** | None: cards only | Chips and card comparison | Review on request |

Both players always get the same level and the same report; the level is written to the log.
`tests/test_scouting.py` checks no numbers or marks in the report, average stays out, the caps and order,
the golden team reads, the calibration (no team line on more than 5 of the 10 teams), 250 random custom
lineups, banned words, the shot charts, the lock, the report in play and the phone layout.
`docs/TEAM_SHEET_HUNT_PROTECT.md` lists the team-sheet Hunt / Protect line for every pairing.

Screenshots: `docs/playtest_scout_report.png` (phone, with shot charts), `docs/playtest_scout_lock.png`
and `docs/playtest_scout_reveal.png` (read the cards first), `docs/playtest_learn_mismatches.png`,
`docs/playtest_team_builder.png`, `docs/playtest_report_in_play.png`, `docs/playtest_card_compare_phone.png`,
`docs/playtest_pass_chips.png`, `docs/playtest_post_game_review.png`.

## How the computer plays (step 3e)

Pick **Computer plays offence / defence: Rookie, Starter or All-Star** at the start. Each side's level is
shown on screen and saved in the log.

- **Rookie:** makes beginner mistakes you can learn to spot.
- **Starter:** solid, with one habit to find.
- **All-Star:** plays the full read.

**What every level sees:** the cards, the board and the trackers, nothing else. No level gets hidden
information or extra tokens, and the defence never sees the Coach's Call target. There are no stored
solver results; every choice is worked out at the table from what is in front of it.

**How it values things.**
- **A contest is judged after the defence's legal reaction.** When a shot is declared the defence may
  spend 0, 1 or 2 actions from its pool. A defender with their Move unused, not locked and a token
  available can still get adjacent and facing. A Quick Step keeps the facing, a Sprint faces the way it
  ran, and a locked defender can't turn (`reachable_contest` in `computer.py`).
- **A position is judged by the offence's best next action against it:** shoot now, drive, or pass
  and then shoot, with interception risk from the arrow lines. This is the solver's evaluation, so walls,
  lanes and help count, and a spent reaction (the "closeout tax") counts too. Help is not a special
  rule: a defender's square and arrow are worth what they cut from the offence's best look (help gain)
  minus what they open up on their own man (leave cost).
- **The comfort line:** the defence won't spend to push the offence's look below 15 (the Okay/Poor
  line). That's "let them shoot it": a ▼ shooter left open is a choice, not a lapse.
- **The offence picks two targets** (its biggest ▲ edges, the secret target on a Coach's Call card,
  threes only on Need a Three). It builds toward them, re-plans when the defence takes the target away,
  and shoots when the look beats what continuing is worth. A patience curve stops obviously early shots.
- **Setup:** man-to-man by number, unless a switch puts the best on-ball defender on the most explosive
  creator, or the best three-point contester on the ▲ shooter, and the evaluation says it's worth it.
  The on-ball arrow is on the carrier unless walling the carrier's best drive is worth more. The others'
  squares (next to their man, or sagging up to two squares off) and arrows come from the same evaluation.

**The levels** (`playmaker_engine/computer_levels.json`):

| | Rookie | Starter | All-Star |
|---|---|---|---|
| Defence concepts | the reaction only | all except keeping a reaction in hand | all |
| Offence concepts | reaction-aware shot value and risk | all except draining the reserve | all |
| Habits (drawn per game, named in the review) | 2 | 1 | none |
| Tunnel vision (defence) | the 2 attackers nearest the ball | 4 | all 5 |
| Reads the cards by | position (`role`) | ▲ / plain / ▼ only (`marks`) | the numbers (`exact`) |
| Comfort line | 15 + 6 | 15 + 2 | 15 |
| Looks ahead | the shot on the board now | the offence's next turn | the solver's search, short budget |
| Second-best choice | 15% of the time | 5% | never |

Defence habits: always force middle, nearest closes out, never leaves a ▲ shooter, ball watcher, jumps
the first pass. Offence habits: settles for the first shot, never screens, ignores the mismatch (passes by
position order), star only. A habit overrides the choice every time it applies, so it can be scouted and
beaten. After the game, **About the computer** in the review names the level, the habits drawn, the
concepts switched off, and the offence's targets and plan. It never appears during play.

**Thinking time:** at most 1 second a decision on the server and 0.45 seconds in the link version,
the best choice found so far being used when time is up.

CALIBRATION_PLACEHOLDER

## Decision timer (step 3d, optional)

Off by default. The table game slows decisions far below basketball pace; the timer brings some
pressure back once players read the board faster.

- **Settings:** Off, 60, 45 or 30 seconds per decision, chosen at the start, the same for both players
  and written to the log.
- **Handicap:** each player may have their own setting (for example an experienced player teaching a
  new one), only when both players tick "handicap" at setup. It is shown on screen and in the log.
  Player A is on offence in possession 1.
- **Penalty:** each full period without an action costs the acting side 1 token from its pool; the
  turn goes on and the timer restarts at full. Losing the last token ends the turn, exactly as spending
  it on an action does. A token-free decision (the contest choice, the forced shot type) gets one period,
  then the default applies (don't contest; the first legal shot type), and no token is lost. The
  defence's turns and reactions are timed the same way.
- **When it runs:** only while the acting player is deciding. It stops for roll previews and results,
  the other side's turn, the Coach's Call secret entry, scouting calls and placement. Hot-seat: after
  each handover a Ready screen hides the board, and the timer starts when the next player taps Ready.
- **Admin grace:** selecting an action (Move, Pass, Shot ...) pauses the main timer and gives 15
  seconds to pick its square, target or direction. Finishing in time commits it and resets the timer.
  If the grace runs out, the main timer resumes from where it paused and the action stays selected.
  Cancelling resumes the main timer without a reset or a penalty. A fresh grace needs 5 seconds of main
  timer since the last selection, so select-and-cancel can't freeze the clock. Both numbers are in
  `TIMER_CONFIG` (`playmaker_engine/timer.py`).
- **Display:** a countdown ring on the acting side's tracker (on phones, above the actions) and a smaller
  ring for the grace. At 10 seconds the ring turns dashed (not colour alone), the phone vibrates where
  supported, and an optional sound plays (off by default). A forfeit is written in the turn bar
  ("Timer: 1 token lost. 3 left."). Screen readers hear the timer at full, at 10 seconds and on each
  forfeit.
- **Engine and log:** `timer_forfeit` (in `playmaker_engine/timer.py`) is an ordinary logged state change,
  so timed games replay exactly. It is never a legal action and never reaches the solver. The log keeps
  the setting and handicap, every forfeit (phase and turn), every grace that ran out and every
  cancellation. `review` and the post-game review list forfeits as plain facts ("the offence lost 1
  token to the timer in phase 3").
- **Presets from data:** `python -m playmaker_engine timer-stats` reads every playtest log and prints
  decision time at the 50th, 75th and 90th percentiles by action and side (admin grace excluded;
  scripted test games left out). There are not enough real games logged yet: games played on the link
  version stay in that browser, so use **Download log** and put the files in `playtest_logs/`. About 20
  games are needed before the presets can be set from data; until then keep 60, 45 and 30.

Screenshots: `docs/playtest_timer_ready.png`, `docs/playtest_timer_ring.png`, `docs/playtest_timer_grace.png`.

## Solver (step 2)

```
python -m playmaker_engine solve 13 --budget 2          # one card, 2-minute budget (or --depth 3)
python -m playmaker_engine solve 13 --exact             # exact from the start (only tiny positions finish)
python -m playmaker_engine solve-all --short 1.5 --long 4
python -m playmaker_engine rule-health
```

`solver.py` holds the exact endgame solver, the fast evaluation, the candidate plays and the guided search;
`solver_config.py` every limit and threshold; `solver_report.py` the card runs and `SOLVER_REPORT.md`;
`solver_fixes.py` the setup fixes tried. Results are saved in `solver_results/runs.json` as each run finishes.

## Layout

| File | What it holds |
|---|---|
| `rules_config.py` | Every number in the rules, and every open ruling as a `Rules` setting (see OPEN_QUESTIONS.md) |
| `board.py` | Squares, zones, adjacency, arrows, pass lines, movement shapes, screen geometry |
| `cards.py` | Loads the provided `data/` files (cards, teams, scenario cards) unchanged |
| `state.py` | `GameState` (frozen, hashable), `encode()` and the ASCII `board()` |
| `actions.py` | `Action` and `legal_actions(state)` |
| `resolve.py` | `apply(state, action)`, `ChanceNode`, `sample`, phase and turn flow |
| `scoring.py` | Rolls, contests, free throws, bands, `score(state)`, match tiebreak |
| `scenarios.py` | The 16 scenario cards and normal-game setup |
| `policies.py` | `Policy`, `RandomPolicy`, `GreedyPolicy`, `play()` |
| `analysis.py` | First-turn ceilings, legacy and engine, one- and two-action reactions (REGRESSION.md) |
| `matchups.py` | Closeout check for every offence card × defence card × shot type |
| `soak.py` | The invariant checker and the random soak |

## How a solver plugs in

```python
from playmaker_engine import scenario_state, legal_actions, apply, ChanceNode, is_terminal, score

def value(state):                                  # plain expectimax over the engine
    if is_terminal(state):
        return score(state).total
    best = max if state.side == 'O' or state.stage == 'target' else min
    return best(expect(apply(state, a)) for a in legal_actions(state))

def expect(node):
    if isinstance(node, ChanceNode):
        return sum(p * expect(s) for p, _, s in node.outcomes)
    return value(node)
```

- **States** are frozen dataclasses: hash them straight into a transposition table. `state.encode()` is a
  compact one-line key for logs and caches; `state.board()` prints the court. The static context (teams,
  rules, scenario) sits in `state.ctx` and is excluded from equality, so keep one table per scenario.
- **Who decides:** `state.side` is `'O'` or `'X'`; `state.stage` is `'target'` (Coach's Call pick),
  `'play'`, `'reaction'` (defence answering a declared shot) or `'over'`.
- **Randomness is explicit.** `apply` returns a `GameState` or a `ChanceNode` whose `outcomes` are
  `(Fraction probability, label, GameState | ChanceNode)`. Steals nest: foul, then kept or stolen.
  `node.flatten()` gives the leaves with products of probabilities; `sample(node, rng)` picks one;
  `force(node, 'no foul', 'stolen')` follows named outcomes for tests and replays.
- **Legal actions** come in a fixed order (kind, then piece, then destination, then arrow). Defender
  Moves list all 8 arrows, so the defence's branching factor is large (often 500 to 1,500); a solver
  will want move ordering or abstraction, but the engine never hides an option.
- **Rulings are data.** Pass `rules=with_rules(contest_choice='nearest')` to `scenario_state` or
  `game_state` to solve under a different ruling.
- **Agents** implement `Policy.choose(state) -> Action` (and optionally `reset(seed)`).
  `play(setup, offence, defence, seed)` returns the log and the `Score`; same seed, same game.

## Results

- 133 tests pass in about 4 minutes (4 cores): 120 engine tests (about 90 seconds) and 13 solver tests, including the 10,000-game soak
  (435,809 applies checked, 0 invariant failures) and the 39,375-pairing closeout check.
- The legacy first-turn ceilings are reproduced exactly; every engine difference is explained in
  REGRESSION.md.
- Designer rulings and the and-one rule are applied; OPEN_QUESTIONS.md marks each one, and #7 is
  still open for the solver.

The source material is in `reference/` (PDFs), `PROMPT_rules_engine.md`, and `playmaker_engine/data/`
(unchanged copies of the provided data files and scripts).
