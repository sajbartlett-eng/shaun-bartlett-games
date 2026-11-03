# Build the Playmaker rules engine (step 1 of the solver programme)

You are building a rules engine for **Playmaker**, a two-player half-court basketball board game. One player attacks (offence, white O pieces), one defends (defence, black X pieces). A possession is scored on the quality of the shot it creates, not on whether the shot goes in.

This is step 1 of 4. The later steps are: a scenario solver, a solo-defence policy search, and matchup simulations. **Do not build those yet**, but design every interface so they plug in without rewrites (see "Built for the solver" below).

The governing principle of the game is **System Fidelity**: the rules should model real basketball decisions. Your job is to encode the rules exactly as written. **Never invent a rule.** Where the rules below are silent or ambiguous, implement a named setting in `rules_config.py` with the default stated here, and record it in `OPEN_QUESTIONS.md`. The designer will settle those after playtesting, so a ruling must be a one-line config change, never a rewrite.

## Files provided (in `data/` and `reference/`)

- `data/data.py`: all 75 player cards. Each card: key, piece number (1 to 5 = position), role, tier (A/B/C), tagline, Quick Step squares (0/1/2), an offence string and a defence string. Values are written like `19H` (rating 19, band H/A/L). Use the provided `parse()` and the `OFF` and `DEF` name lists:
  - Offence: dribble, pass, screen | shot_layup, shot_dunk, shot_post, shot_floater, shot_mid, shot_long, shot_three, free_throw
  - Defence: agility, intercept, challenge, steal, foul_steal | con_layup, con_dunk, con_post, con_floater, con_mid, con_long, con_three, foul_contest
  - It also holds `RANGES`, `FOUL_RANGES` and `band()`: the locked range table. Fouls are lower-is-better.
- `data/teams.py`: 10 prescribed teams, each a list of 5 card keys in position order O1 to O5. `FIRST_GAME` names the default matchup.
- `data/scenarios.py`: 16 scenario cards: title, kind, starting clock, offence and defence team names, O squares, X squares with an arrow intent, ball holder, inbounder, target flag, and constraints (`screen`, `locked`). Off-board inbounder squares are written `K0` (below row 1), `@n` (left of column A), `Rn` (right of column Q).
- `data/court_zones.json`: every square to a zone: `K` rim zone (2 points: layup, dunk, post), `M` mid zone (2 points: mid-range, floater), `L` long-two zone (2 points), `3` three-point zone (3 points), `.` plain wood (no shot allowed).
- `reference/`: the 2-page rulebook, both trackers, scenario rules and the High-Low play as PDFs. The trackers hold the most detailed action text. If anything in this prompt conflicts with the PDFs, **stop and list the conflict** in `OPEN_QUESTIONS.md` rather than choosing.

## The board

- 17 columns A to Q (x = 0 to 16) by 14 rows 1 to 14 (row 1 is the baseline). The rim is **I2**.
- "Adjacent" always includes diagonals (8-neighbourhood).
- "Distance to the rim" is Chebyshev distance to I2: a diagonal step counts as 1.
- One piece per square. No piece ever moves through another piece.

## The pieces

- 5 O pieces and 5 X pieces, numbered by position. Each piece uses its team's card for that position.
- Every X piece has an **arrow** pointing in one of 8 directions.
- The ball sits on one O piece, the ball carrier.
- An O piece may be **screening** (flipped to its T side). The T marks one adjacent square.
- Any piece may be **locked** (grey lock token).

## Setup (normal game)

1. Each side takes a prescribed team.
2. The shot clock starts on **12**. Scenarios may set any start.
3. The offence places its 5 O pieces anywhere. The ball goes on a player on plain wood beyond the three-point tiles.
4. The defence places its 5 X pieces on empty squares, each arrow pointing any way.
5. Each side puts **6 action tokens** in its pool.

## Phases, turns and tokens

- A possession is played in **phases** of 2 seconds.
- Each side has 6 action tokens per phase. Playing an action moves one token from the pool to that player's action slot.
- **The offence goes first,** then the sides alternate turns. On a turn, a side takes **1 or 2 actions**.
- Some actions **end your turn** (see the table). A turn-ender must be the last action of the turn: play one and the turn is over.
- **The phase ends when:**
  - the offence plays its last token: the defence gets one final turn, then the phase ends;
  - the defence plays its last token: the phase ends at once;
  - a shot is taken: the possession ends.
- **Reset:** all action tokens return to the pools, lock tokens come off, the shot clock drops by 2, and pieces stay where they are.
- **Clock reaches 0 without a shot:** turnover, −5, and the ball carrier takes a **forced shot** from where the pieces stand, contested as normal. A ball carrier on plain wood, or a shot value below 0, scores 0 for that shot.

### Per-phase limits

| Action | Side | Ends turn | Limit per phase |
|---|---|---|---|
| Move | both | no | once per player |
| Quick Step | both | no | 2 per side (Sprints count) |
| Sprint | both | no | 1 token; uses that player's Move and counts toward Quick Step |
| Pass | O | yes | 2 |
| Screen | O | yes | 2 |
| Dribble | O | yes | 2 |
| Hesitate | O | yes | 1 |
| Shot | O | yes | 1 |
| Intercept | X | yes | 2 |
| Challenge Screen | X | yes | 2 |
| Steal | X | yes | 2 |
| Pause | X | yes | 1 |
| Contest | X | automatic, no token | |

## Rolls

Every opposed roll works the same way: the **offence** rolls a d20 and succeeds on a result **equal to or under** its rating minus the defender's rating. This holds even when the defence starts the action (Steal, Challenge, Intercept).

Foul rolls are straight rolls with no subtraction: d20 ≤ the defender's Foul rating means a foul.

**Shots are never rolled.** (The only exception is the match tiebreaker; see Scoring.)

## Movement

**Move.** Up to 3 squares straight, or 1 straight + 1 diagonal, or up to 2 diagonal. Never through another player.
- An X piece sets its arrow as part of its Move. Turning the arrow uses that player's Move.
- The ball carrier can't cross the **arrow line** of an adjacent defender. The arrow line is the ray from that defender, in its arrow's direction, to the board edge. Stepping onto the line is allowed; crossing it is not. Winning a Dribble against that defender removes this restriction.

**Quick Step.** 0, 1 or 2 squares in a straight line, as set by the card (speed green = 2, yellow = 1, red = 0).
- Allowed while locked.
- A defender's Quick Step can't turn its arrow.

**Sprint.** A Move and a Quick Step in one straight line, in any of the 8 directions, for 1 token.
- It uses that player's Move for the phase and counts toward the side's Quick Step limit.
- A defender who Sprints ends with its arrow facing the way it ran.

**Locked.** A locked player can't Move, Sprint or turn its arrow. Quick Step is still allowed, and a locked ball carrier can still pass or shoot. Locks clear at the phase reset.

## Arrows (defence)

- **Arrow pointing at an adjacent ball carrier:** that defender may Steal, and its contest is clean.
- **Arrow pointing elsewhere, while adjacent to the ball carrier:** the ball carrier can't cross that arrow line without winning a Dribble.
- **Any arrow:** threatens passes whose line crosses it (see Intercept).

## Offence actions

**Pass.** To any teammate. A pass is a straight segment from the passer's square to the receiver's square, and passes go over players. Ends the turn.

**Screen.** Any player may screen, including the ball carrier, who keeps the ball (a pass from a screener is a hand-off). Ends the turn.
- The screener flips to its T side, and the T marks one adjacent square.
- No defender may go diagonally round the screener from or through the T square.
- The screener can't move, and it flips back after the offence's next turn.
- **Post seal:** in one turn, Move round your own defender, then Screen with the T on that defender. The pass into the post comes on the next turn.

**Dribble.** Take on an adjacent defender: roll ≤ Dribble − Agility. Ends the turn.
- Win: that defender is locked, and the ball carrier may cross its arrow line. Getting past it is up to later movement.
- Lose: the ball carrier is locked, but can still pass or shoot.

**Hesitate.** The offence's one wait per phase. It uses a token. The defence must act before the offence acts again. Not allowed straight after the defence's Pause. Ends the turn.

**Shot.** Only the ball carrier, and never from plain wood. A shot is a **declaration**:
1. The defence gets one turn to react: move, turn arrows, or Steal.
2. Then one adjacent defender contests (see Contest).
3. The possession ends.

Once a shot is declared, **any foul gives free throws**, and a steal ends the possession at −5 with no shot.

## Defence actions

**Intercept.** Answers a Pass. Ends the turn.
- A defender standing **on** the pass segment may intercept, facing any way.
- A defender whose **arrow line crosses** the segment must first reach the segment with one Move, Quick Step or Sprint, which costs its own token.
- A defender **adjacent to the passer** counts only through its arrow. If that arrow points at the passer, it can only stop a pass thrown through its own square.
- Roll ≤ Pass − Intercept: the pass succeeds. Otherwise it's intercepted: turnover, −5. There is no foul roll.

**Challenge Screen.** Answers a Screen; name the screen being fought. Ends the turn.
- Roll ≤ Screen − Challenge: the screen holds and the defender is locked.
- Otherwise the defender may cross the screen's T square but not stop on it.

**Steal.** The defender must be adjacent to the ball carrier with its arrow on it. Ends the turn.
1. Foul roll first: d20 ≤ Foul (Steal) means a foul. The 1st foul is +5 to the offence and play continues. The 2nd foul gives free throws and the possession ends. After a declared shot, any foul gives free throws.
2. Otherwise the offence keeps the ball on ≤ Dribble − Steal. If it fails: stolen, −5.

**Pause.** The defence's one wait per phase. It uses a token. The offence must act before the defence acts again. Not allowed straight after the offence's Hesitate. Ends the turn.

## Contest (automatic, no token)

- One adjacent defender contests, using its contest rating for the declared shot type. The defence chooses which.
- If that defender is **further from the rim (I2)** than the shooter, the contest is −3.
- **Arrow off the shooter:** foul roll first, d20 ≤ Foul (Contest). A foul gives free throws and the possession ends. A defender with its arrow off the shooter may also choose not to contest.
- No adjacent defender: contest 0.

## Scoring

- **Shot value = points × (shot rating − contest).** Points are 2, or 3 from a `3` square. The shooter chooses any shot type its zone allows.
- **Free throws** score 2 × the shooter's FT rating, or 3 × on a three-point shot.
- **Possession score** = shot value (or free throws) + 5 per first-steal-foul bonus − 5 per turnover.
- **Prestige bands:** Excellent 30+, Great 25 to 29, Good 20 to 24, Okay 15 to 19, Poor under 15.
- **Match:** two possessions, each player attacks once, and the higher total wins. On a tie, each player rolls for their final shot (d20 ≤ rating − contest); a make beats a miss.

## Scenario rules (from `scenarios.py` and the scenario rules PDF)

- **Setup:** the card's squares and arrows, the card's starting clock, and full pools. Arrow intents in the data (`man`, `ball`, `deny`, `help`) resolve to directions using the existing checker logic; port it from `check_scenarios.py`.
- **Goal:** a look with **shot value 30+**. Fouls and bonuses still add to the possession score.
- **Inbounds:**
  - The inbounder sits off the board, next to the edge square shown, and can't move.
  - The offence has **two phases** to complete a pass from the inbounder, and the clock doesn't run.
  - Once the pass succeeds: reset to a new phase, set the clock to the card's number, and the inbounder may step onto the court.
  - Not in after two phases: turnover, −5. Play on from where everyone stands, with the ball given to the player furthest from the rim (the offence picks if tied), and the clock on the card's number.
- **Coach's Call:** before setup, the offence secretly names a target. If the target takes the shot, add a bonus by band: Poor +0, Okay +2, Good +5, Great +8, Excellent +10.
- **Late Clock:** Need a Three counts only threes. Two or Three: an Excellent three wins and an Excellent two ties. Head-to-head comparisons rank the result first (win, then tie, then loss), and shot value breaks ties.
- **Constraints:**
  - Late Clock Reset: tokens already spent and O5's screen standing.
  - In the Bonus: the offence starts at +5 with one steal foul already counted.
  - Hold for One: no shot before the final phase, and a turnover ends the possession at 0.
  - Star Locked: O1 starts locked.

## Known open questions (implement each as a setting with this default, and list it)

1. **Ball after an intercept or steal that "plays on":** default, the ball returns to the passer (intercept) or stays with the carrier (steal), at −5. Alternative: the possession ends.
2. **When a pass resolves:** default, on the defence's next turn, which may Intercept. If it doesn't, the pass completes at the start of that turn. Alternative: it resolves immediately unless an on-line defender is already present.
3. **Sprint length:** default, up to 3 + QS orthogonally and 2 + QS diagonally.
4. **Roll bounds:** default, a target ≥ 20 always succeeds and a target ≤ 0 always fails, with no natural 1s or 20s.
5. **Negative shot value on a declared shot:** default, it scores as negative. Alternative: a floor of 0.
6. **Defence reaction to a declared shot:** default, 1 or 2 actions using tokens still in the pool. With an empty pool, only the automatic contest. Steal limits apply.
7. **Defence out of tokens while the offence has some:** the phase ends at once, per the rules. Confirm this is intended.
8. **Hesitate and Pause:** default, each passes the turn and uses a token. Confirm the "not straight after" chaining.
9. **Screen geometry:** default, "going diagonally round the screener from or through the T square" bans any diagonal step that starts on the T square or whose path passes its corner. Write unit tests showing the exact squares.
10. **Arrow line crossing:** default, a ball carrier move whose path segment strictly crosses the ray (not merely touches it) is illegal.
11. **Move path order for 1 straight + 1 diagonal:** default, either order is allowed if the intermediate square is empty.
12. **Contest choice:** default, the defence picks the adjacent defender that minimises the shot value, counting foul expected value under setting 5.

Add every new ambiguity you find in the PDFs to `OPEN_QUESTIONS.md` with the file and line it comes from.

## Built for the solver (required interfaces)

- **`GameState`:** immutable or cheaply clonable, hashable (for transposition tables), with a compact text encoding and a readable ASCII board printer.
- **`legal_actions(state)`:** returns every legal action for the side to act, including movement destinations, arrow choices, pass targets and shot types. Deterministic order.
- **`apply(state, action)`:** returns either a new state or a **chance node** listing every outcome with its exact probability (d20 rolls collapse to success/failure probabilities, and foul-then-steal nests). Never hide randomness inside `apply`; a separate `sample(chance_node, rng)` picks an outcome.
- **`is_terminal(state)` / `score(state)`:** the final possession score with a breakdown (shot value, free throws, bonus, turnovers, band).
- **Agents:** a `Policy` interface (`choose(state) -> action`), with a `RandomPolicy` and a `GreedyPolicy` (the offence takes the best immediate shot; the defence takes the best immediate contest) as baselines.
- **`play(scenario_or_setup, offence_policy, defence_policy, seed)`:** returns the full action log and score. Same seed, same game.

## Tests (must all pass)

1. **Unit tests for every rule above,** at least one legal and one illegal case each: movement shapes, blocking, arrow line crossing, the screen T geometry, the Sprint arrow, locked behaviour, every per-phase limit, turn-ender ordering, the phase-end conditions, reset, the clock-expiry forced shot, the contest −3 and foul branches, free throws, intercept geometry (on-line, arrow-across with its token, the adjacent-passer cases), the steal foul sequence, and the Coach's Call bonus.
2. **Probability tests:** each chance node's outcome probabilities sum to 1 and match hand calculations (for example, Pass 18 against Intercept 5 succeeds 13/20).
3. **Scenario setup tests:** all 16 scenarios load, pass the same checks as `check_scenarios.py` (no shared squares, inbounders beside an edge, on-ball defenders adjacent, deny arrows crossing their lane), and print a board matching the card.
4. **Golden game: the preview pack's table setup.** Five Out attacking High-Low, first phase:
   - **Setup:** O1 I11 (ball), O2 C9, O3 O9, O4 A3, O5 Q3. X1 I10 on the ball; X2 D8 and X3 N8 with arrows across the passing lanes; X4 G4 and X5 N4 sagging.
   - **Offence:** O1 passes to O3.
   - **Defence:** X3 Moves N8 to L10 onto the line and Intercepts. Force the roll to succeed for the offence.
   - **Offence:** O3 Moves O9 to N7; O1 Moves I11 to G10.
   - **Defence:** X5 Moves N4 to N6; X1 Moves I10 to H9.
   - **Assert:** offence has 3 tokens left, defence 2. A pass from O3 to O5 crosses no arrow line. No defender can legally become adjacent to Q3 this phase, so a three by O5 is contested at 0.
5. **Regression numbers:** reproduce the first-turn ceilings from `scenario_tests.py` (included in `data/`), or explain each difference as a rule the old script simplified.
6. **Invariants, checked after every `apply` in a 10,000-game random-vs-random soak:** no shared squares; tokens conserved; limits never exceeded; the clock never negative; every game terminates; scores finite.

## Deliverables

- A Python 3.11+ package `playmaker_engine/` with `rules_config.py`, `board.py`, `state.py`, `actions.py`, `resolve.py`, `scoring.py`, `scenarios.py`, `policies.py` and `cli.py`.
- **CLI:**
  - `python -m playmaker_engine show <scenario#>` prints the board.
  - `python -m playmaker_engine play <scenario#> --offence greedy --defence greedy --seed 1` prints the log and score.
  - `python -m playmaker_engine test` runs the suite.
- A `tests/` folder (pytest), runnable in under 2 minutes.
- `OPEN_QUESTIONS.md`: each item numbered, with the default chosen, the alternative, and what it changes.
- `README.md`: one page on how to run it and how a solver plugs in.
- No dependencies beyond the standard library and pytest.

## Working rules

- Read every PDF in `reference/` before writing code, and reconcile it with this prompt.
- Build in order: board and movement, then actions and limits, then the chance nodes, then scoring, then scenarios, then the golden game, then the soak test. Run the tests at each step.
- Keep rule logic out of the UI and the policies. Every number in the rules (6 tokens, 2-second phases, −3, −5, +5, the bands, the bonus ladder) lives in `rules_config.py`.
- When finished, report: the number of tests passed, the soak results, every open question, and anything in the reference PDFs that contradicts this prompt.
