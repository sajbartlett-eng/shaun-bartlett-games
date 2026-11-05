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
  minus what they open up on their own man (leave cost). The Starter and All-Star defences also weigh a
  dribble at the dice: a won dribble, the defence's answer, then the step-out shot.
- **The defence's candidates** include containing the carrier's best step-then-shoot squares: a defender
  next to each, facing it (a step that keeps the arrow facing elsewhere still forces a foul roll).
  Mid-turn, ending the turn is always a candidate, and no play runs past the turn's action limit.
- **The comfort line:** the defence won't spend to push the offence's look below 15 (the Okay/Poor
  line). That's "let them shoot it": a ▼ shooter left open is a choice, not a lapse.
- **The offence thinks in advantages (step 3g).** It creates one, keeps it when help arrives, and
  finishes it. An advantage is one of six things on the board, each belonging to one attacker and worth
  the shot it opens (after the defence's reaction):
  - **Beaten defender:** a defender is locked (he lost a Dribble, or a Screen held him) and can't
    contest the shot of the man he was guarding.
  - **Mismatch:** an attacker's ▲ shot meets a ▼ contester, and that defender is the only one who can
    reach him.
  - **Help pulled:** a defender stepped toward the ball and away from the man he was nearest to, and
    that man now has no clean contest coming.
  - **Bad closeout:** the only defender who can reach the shot gets there facing the wrong way (a foul
    roll) or from the rim side (the −3).
  - **Spent defence:** the defence has no tokens left, or the defender nearest the shooter has used his
    Move.
  - **Numbers:** more ▲ shooters standing in their zones than defenders who can reach a clean contest
    on them.

  Its plays, one turn each: **shoot**; **dribble attack** (valued by the chance to win and what the win
  opens: a 40% dribble that frees a shooter beats a 60% one that leads nowhere); **screen for a
  mismatch**; **speed burst** (a Quick Step or Sprint to a square nobody can cleanly contest); **post
  seal** (a ▲ post scorer seals a ▼ post defender); **cut** (an off-ball attacker moves to open a lane
  or a shot); and **pass**, but only to move an advantage to a better attacker or to finish one
  (`pass_risk`, step 3f). Each play is scored over create (the play), reply (the defence's best answer)
  and exploit (the best finish next turn), less turnover risk and the clock spent (by the shot bars).
  A play that leaves no advantage scores nothing. Only when nothing scores above zero does it fall back
  to the older search over every action.
- **The plan is the play being worked** ("Screen for a mismatch: O2 screens X1 off O1"). It holds until
  the advantage is finished or the defence takes it away. If help moves the advantage to another
  attacker, the plan follows it ("Help came from X5; the advantage moved to O5"). The targets (the two
  biggest ▲ edges, the Coach's Call target, threes on Need a Three) still steer it, and it shoots only
  when the look clears its **shot bar** and beats what continuing is worth. The bar is set by the clock
  and is higher for a look a defender can still contest than for an open one. It drops each phase: a
  defence that keeps the good looks covered forces a lesser one late. On the last phase there is no bar.
  The bar reads the look itself, not points already banked (turnovers, the steal-foul bonus). Rookie
  takes its best shot from the phase before the last (`shoot_by`).
- **No loops:** a play that ends where the offence already stood earlier in the possession (its five
  squares and the ball) loses 2 points per earlier visit (up to 3). A pass that was intercepted is not
  thrown again from the same position.
- **Passing judgement (step 3f).** A Pass ends the offence's turn and the defence answers before it
  resolves, so a lane is **clean** only if no defender can legally get an Intercept on it in that turn:
  on the line, or by an approach (a Move, Quick Step or Sprint onto the line by a defender whose arrow
  crosses it, then Intercept), with the defence's tokens, unused Moves, locks and the intercept limit as
  the rules have them (`pass_risk` in `computer.py`, worked out from the legal actions). Otherwise it is
  **contested**, at the best interception chance any defender can reach, 1 − P(d20 ≤ Pass − Intercept).
  A pass is worth (1 − risk) × the position after the catch (valued after the defence's reply) − risk ×
  5 × `pass_risk_tolerance` (Rookie 0.5, Starter 0.8, All-Star 1.0). The pick-off counts as the −5
  alone, not as the play-on position it leaves (OQ-54). Against a contested pass the computer weighs its
  alternatives, each valued with the next turn able to pass, after the defence's full reply: moving the
  receiver to open a lane (every level), moving the passer or dribbling, and a screen or seal (Starter and
  All-Star), and two shorter clean passes (All-Star). Each extra pass costs a turn: the defence answers
  it before the catch is valued. Rookie can draw the habit **forces passes**: it passes to its primary
  target whenever the pass is legal, whatever the risk.
- **Setup:** man-to-man by number, unless a switch puts the best on-ball defender on the most explosive
  creator, or the best three-point contester on the ▲ shooter, and the evaluation says it's worth it.
  The on-ball arrow is on the carrier unless walling the carrier's best drive is worth more. The others'
  squares (next to their man, or sagging up to two squares off) and arrows come from the same evaluation.

**The levels** (`playmaker_engine/computer_levels.json`, as tuned by the head-to-head calibration below):

| | Rookie | Starter | All-Star |
|---|---|---|---|
| Defence concepts | the reaction only | all | all |
| Offence concepts | all but draining the reaction | all | all |
| Habits (drawn per game, named in the review) | defence 2, offence 1 | 1 | none |
| Tunnel vision (defence) | the 2 attackers nearest the ball | 4 | all 5 |
| Reads the cards by | defence: position (`role`); offence: the numbers | defence: ▲ / plain / ▼ (`marks`); offence: the numbers | the numbers (`exact`) |
| Comfort line | 15 + 6 | 15 + 3 | 15 |
| Looks ahead | defence: the shot on the board now; offence: the defence's reply | the offence's next turn / the defence's reply | the same, with no handicaps |
| Shot bar, open look (clock 12 / 10 / 8 / 6 / 4) | 24 / 22 / 20 / 17 / 15 | 27 / 25 / 22 / 19 / 16 | as Starter |
| Shot bar, contested look | 33 / 30 / 26 / 21 / 17 | 36 / 32 / 27 / 22 / 17 | as Starter |
| Must shoot by | clock 4 | the last phase | the last phase |
| Advantage plays known | shoot, dribble attack, pass | + screen, speed burst, post seal | + cut, moving the advantage |
| Advantage lookahead | create only (the board after the play) | create, reply, exploit | create, reply, exploit |
| Second-best choice | defence 15%, offence 3% | defence 5%, offence never | never |

Defence habits: always force middle, nearest closes out, never leaves a ▲ shooter, ball watcher, jumps
the first pass (never drawn at Rookie: at Pass 14 v Intercept 6 an intercept attempt succeeds 60% of the
time, so it is often the right play). Offence habits: settles early (reads its shot bar one phase ahead), forces passes (Rookie only), never screens, ignores the mismatch (passes by
position order), star only. A habit overrides the choice every time it applies, so it can be scouted and
beaten. After the game, **About the computer** in the review names the level, the habits drawn, the
concepts switched off, the offence's targets, and the advantage plays it ran in plain words ("Screen
for a mismatch: O2 screens X1 off O1. O1 has a mismatch on X4, for a three. Help came from X5; the
advantage moved to O5. Finished: O5 three."). It never appears during play.

**Thinking time:** about 2 seconds a decision on the server and in the link version (raised in step
3f), the best choice found so far being used when time is up. Python's cycle collector is paused while
the computer thinks: walking the search's caches cost up to 5 seconds a decision. Measured in step 3g
(server, 8 possessions a level, offence): Rookie median 0.15 s (max 0.64), Starter 0.46 s (max 1.90),
All-Star 0.64 s (max 2.01).

*All figures in this section were measured before OQ-52 (one Quick Step per player per phase, a Sprint uses it).
After it, the board-reading defence keeps more arrows on the ball (52% against 34%): a reaction can no
longer Quick Step and Sprint the same defender, so the arrow's facing matters more.*

**Calibration: head-to-head.** Each offence level played each defence level on the 16 scenario cards
and 20 random prescribed-team possessions, 3 seeds each (972 possessions, 22 minutes on two cores at
play speed). A possession is scored as the game scores it (shot quality, bonuses, turnovers). Mean
points per possession, with a 95% interval:

| Offence ↓ / Defence → | Rookie | Starter | All-Star |
|---|---|---|---|
| **All-Star** | 26.3 ± 2.0 | 26.0 ± 1.7 | 24.3 ± 1.8 |
| **Starter** | 23.6 ± 1.9 | 23.9 ± 1.7 | 21.7 ± 1.5 |
| **Rookie** | 22.7 ± 1.8 | 21.7 ± 1.6 | 19.6 ± 1.5 |

Against the All-Star opponent, paired over the same start and seed (99 pairs):

| | Measured | Target |
|---|---|---|
| Starter defence concedes | +1.7 ± 1.6 | +2 |
| Rookie defence concedes | +1.7 ± 1.6 | +4 (**not met**; not separated from Starter: 0.0 ± 2.0) |
| Starter offence scores | −2.7 ± 1.4 | −2 |
| Rookie offence scores | −4.7 ± 1.8 | −4 (separated from Starter: 2.0 ± 1.5) |

The defensive levels can't be pushed further apart with the levers: every Rookie setting tried
(looking ahead 0 or 1, tunnel vision 2 or 3, role or marks reading, comfort +6 or +8, randomness 0.10 or
0.15) lands at +2 to +3 against the All-Star offence, which mostly finds looks nobody can reach in the
reaction. The settings changed, and why:

- **All-Star, both sides: looks ahead one turn instead of the solver's search.** Inside a one-second
  budget the search is shallow, and in head-to-head play it did worse than the one-turn ranking: a
  Starter offence outscored it by 2 points.
- **Starter defence: keeps a reaction in hand (reserve on); comfort offset +3 (was +2).** Without the
  reserve it conceded 7.6 more than All-Star against an offence that drains the reaction.
- **Starter offence: reads the cards exactly (was marks); works to drain the reserve (was off);
  randomness 0 (was 0.05); patience 14 / 12 / 10 (was 20 / 18 / 14).** Reading by marks cost about
  3 points on its own, and the old curve waited too long.
- **Rookie offence: reads exactly (was role); one habit (was two); looks at the defence's reply (was
  the shot now); plans toward a target; randomness 0.03 (was 0.15); settles at 18 / 16 / 12 (was a
  threshold of 12).** It drew "settles for the first shot" in most games and took looks of 12; it
  still settles early, but on better looks.
- **Offence, every level: a shot wins a tie with continuing** (section 7.3: shoot when the shot, valued
  after the reaction, is worth at least what continuing is estimated to be worth). Before this, a
  one-action setup play that the lookahead valued the same as a two-action step-back three won the tie,
  and All-Star passed up the golden position's 27-point line.
- Unchanged: the Rookie defence preset, the Starter defence's reading, tunnel and habit, the comfort
  line, every habit's behaviour.

**Shot bars (after playtest log 3A9C33).** A Starter v Starter game had both offences pass once and
shoot a contested three in the first phase. The old rule shot whenever a look beat a low bar (14 at
Starter, 12 with "settles for the first shot") and the one-turn estimate of continuing, which
undervalues waiting. Now each level has a bar by clock, higher for a contested look, dropping each
phase (table above), and the plan bonus no longer counts toward it. "Settles for the first shot"
became "settles early": the same bars, read one phase ahead. Re-measured on 36 starts x 3 seeds, each
offence level against the Starter and All-Star defences (648 possessions a run):

| Offence | Points v Starter D, before → after | Points v All-Star D, before → after | Shots in the first phase | Contested shots in the first phase |
|---|---|---|---|---|
| Rookie | 21.5 → 25.2 | 20.3 → 24.4 | 55% → 25% | 34% → 1% |
| Starter | 22.6 → 27.1 | 22.3 → 27.0 | 51% → 25% | 36% → 6% |
| All-Star | 26.4 → 29.0 | 26.3 → 28.5 | 49% → 28% | 15% → 9% |

(Intervals about ± 1.7. Shares are of all shots.) Waiting pays at every level. Against the All-Star
defence, paired: Starter offence −1.2 ± 1.3 against All-Star (target −2), Rookie −3.8 ± 1.9 (target −4).
The defence levels' concessions in the table further up were measured against the old offence.

**Re-measured after playtest logs D7D923 and 82866B** (the defence and loop fixes above; the full
3 x 3 matrix, 972 possessions, `solver_results/headtohead_fixed.json`):

| Offence ↓ / Defence → | Rookie | Starter | All-Star |
|---|---|---|---|
| **All-Star** | 30.6 ± 1.5 | 28.2 ± 1.6 | 26.6 ± 1.8 |
| **Starter** | 30.1 ± 1.5 | 26.4 ± 1.7 | 25.4 ± 2.0 |
| **Rookie** | 27.9 ± 1.8 | 24.3 ± 1.7 | 23.2 ± 2.0 |

| Against the All-Star opponent (99 pairs) | Measured | Target |
|---|---|---|
| Starter defence concedes | +1.8 ± 1.7 | +2 |
| Rookie defence concedes | +4.3 ± 1.7 (separated from Starter: +2.5 ± 1.7) | +4 |
| Starter offence scores | −1.1 ± 1.6 | −2 |
| Rookie offence scores | −3.2 ± 1.9 (separated from Starter: −2.1 ± 1.6) | −4 |

Every target is now inside its interval, and the Rookie defence is separated from the Starter defence
for the first time. The All-Star defence holds the All-Star offence to 26.6 (28.5 before these fixes).
Contested shots in the first phase: 2% of Rookie shots, 9% of Starter and All-Star shots.
Thinking time is not capped hard: a few decisions ran to 2 to 4 seconds (the designer prefers a slower,
better choice).

**Every preset change from the step 3e spec** (`git log` on `computer_levels.json`):

| Preset | Spec | Now | Why |
|---|---|---|---|
| Rookie offence concepts | reaction-aware shot value and risk only | all but draining the reaction (plan, lookahead and patience on) | calibration: plan and lookahead brought it to its target; patience is the shot-bar rule (all levels) |
| Rookie offence habits | 2 | 1 | calibration: with two it nearly always drew "settles for the first shot" and took looks of 12 |
| Rookie offence reads | position (`role`) | the numbers (`exact`) | calibration |
| Rookie offence looks ahead | the shot now (0) | the defence's reply (1) | calibration |
| Rookie offence randomness | 0.15 | 0.03 | calibration |
| Starter offence reads | ▲ / plain / ▼ (`marks`) | `exact` | calibration: marks cost about 3 points on its own |
| Starter offence drains the reaction | off | on | calibration |
| Starter offence randomness | 0.05 | 0 | calibration |
| All-Star offence and defence look ahead | the solver's search | one turn | calibration: the search is shallow inside a second and did worse |
| Starter defence keeps a reaction in hand | off | on | calibration: without it, 7.6 more conceded to a draining offence |
| Starter defence comfort offset | +2 | +3 | calibration |
| Offence patience, every level | one curve, three modes | shot bars by clock, open and contested; Rookie must shoot by clock 4 | playtests 3A9C33 and 82866B |
| Offence habit "settles for the first shot" | a fixed bar of 12 | "settles early": the bars one phase ahead | playtest 3A9C33 |
| Rookie defence habit pool | all five | not "jumps the first pass" | playtest 82866B: it is often the right play |

**Against the All-Star offence** (from the same matrix):

| Defence | Shots declared | Clean contest | Foul roll | No contest | Reaction couldn't change the contest | Comfort line decided |
|---|---|---|---|---|---|---|
| Rookie | 107 | 25% | 0% | 75% | 53% | never (help is off) |
| Starter | 104 | 37% | 3% | 60% | 45% | 6% of choices |
| All-Star | 105 | 41% | 8% | 51% | 50% | 6% of choices |

The defence never had an empty pool when a shot was declared. In-play arrow jobs: Rookie 38% on the
ball, 22% lanes, 16% on its man; Starter 62% lanes, 13% on the ball, 9% walls; All-Star 65% lanes, 13% on
the ball, 9% walls. Clean contests are well under 90%, so there is no rule question here: the All-Star
offence mostly shoots where no defender can still reach.

**Setup sag (golden table, Five Out v High-Low preview setup):** All-Star's own setup keeps X5 next to
O5 (the Stretch Centre on Q3, Three 8, tied weakest with the ball-handler O1). Sagging X5 two squares off
to O3, facing the ball, scored 33.6 ± 3.3 against the All-Star offence; the setup as chosen scored
33.6 ± 3.3 (40 seeds each, paired difference +0.03 ± 0.74). Neither is better here, so the setup rule
is left as it is.

*Diagnostic, before this tuning:* the value given up per decision against a depth-2 solver judge was
offence 5.6 / 2.8 / 2.1 and defence 4.1 / 2.1 / 0.9 (Rookie / Starter / All-Star). It isn't used as the
target because summed per possession it penalises patience.

## The other side's turn, one action at a time

When the computer (or a remote opponent) acts, the page plays its turn back one action at a time.
The board shows where everything stood after that action, with a dashed ghost where the piece came from.
A bar says what it did, any dice rolled and what happened. **OK: next action** shows the next one;
the last says **OK: your turn**. Nothing still to come is shown, so you can try to call the next action
(a steal? another help defender moving?) before you press OK. The timer, if on, waits until your turn
is on the board. Each feed entry carries a small board snapshot (`board_json` in `view.py`) for this.

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
