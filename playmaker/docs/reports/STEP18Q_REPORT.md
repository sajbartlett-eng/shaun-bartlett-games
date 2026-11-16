# Step 18q: the scout, the goals, the reads, and the first read mended (the middle)

**In five lines.**

- **Speed first: with the lane reading on, every level is over its time** (All-Star 3.4 to 3.6 seconds against 2.5). It is off by default, where nothing is slower. It has to be made faster before it can go on.
- **The system is mapped** (`docs/plans/SYSTEM_MAP.md`): scout, goals, reads, decisions and the three ways results feed back, what exists, what is proven, and the order to perfect it. Your rule is recorded as D-197.
- **The computer can now read the way to the rim.** The clear lane on your board reads worse for the defence than help in the lane, a defender in front reads better than one beside or behind, and "who is behind the on-ball defender" counts before anyone is beaten. Both engines agree. `?lane=1` turns it on for a playtest.
- **By play, half of design check 1 holds and half doesn't.** Help in the lane costs the offence 4 to 7 points. But the offence still doesn't take the open lane: made to sprint into it, it scores 27.8; by its own choice, 22.0.
- **The defence does not help more in play, and I found why.** Its best turn is nearly always the reach, which wins the ball 1 time in 4. And no big can get behind the on-ball defender in one turn, so help has to come from the setup.

## 1. The map (what you asked for)

`docs/plans/SYSTEM_MAP.md` holds it in full. The short version:

- **The loop:** the scout says who each player is and what each matchup gives up. The goals say what each team is trying to make happen or stop. The reads measure how far the board is from each goal, in points. The search decides. What happened goes back three ways: inside the possession (a goal reached or lost), between possessions (the scout learns the opponent), and between versions (a read is corrected where play proves it wrong).
- **A goal in the engine is a measure, a side and a source.** It never names a move (D-156). "Protect the middle" is the measure built this step. "Limit future passing options" is the next one. Your fluid goals ("deny all passes to O2"; "contain the three, force the drive") are the same measures aimed at one player with a worth from the scout, so they need no code of their own.
- **The order:** one measure at a time, each proved by design checks on forced lines before anything above it uses it. Iteration 1 is this step.
- **Three new design checks (10 to 12) are in the map for you to confirm.**

## 2. What was built: the way to the rim

One new part of the reading, the same in both engines, switched by `eval.lane` (off). It is worked out from the movement rules and nothing else:

1. **The race.** The ball handler gets the movement he has left this phase and one movement the next. Each defender gets the movement he has left this phase (inside the defence's tokens) and then the two actions of the reaction. A body on the way stops him. An arrow that bars the way stops him (the zone's own crossing rule).
2. **"No defender able to get between."** The lane is worth only what is left after the defence's best single step into it. With no defence token left this phase, nobody can step in.
3. **The Dribble.** The defender next to the ball handler stays in the race only if he wins the roll. So the lane also counts, at the chance of the Dribble, what it is worth with him beaten.
4. **The finish.** A shot straight after a Quick Step or Sprint is off balance (2 lower). A lane square one Move away gives a set shot.

The defence's quick look at its own actions carries the same measure, so a step into the lane can be picked for a full look.

It has its own fitted map (`calibration_lane`), fitted on 160 possessions of All-Star play with it on. With it off, nothing changes: no golden value moved.

## 3. The design checks

### By the reading (the All-Star's own, your board of 15 November, the zone on)

| Position | Lane off | Lane on |
|---|---|---|
| After the beat, the lane open | 24.8 | 25.1 |
| After the beat, X4 and X5 in the lane | 23.7 | 23.2 |
| After the beat, X5 on I4 | 24.4 | 23.5 |
| After the point guard sprints into the lane | 23.1 | 25.1 |
| Start, X1 square in front | 23.4 | 24.2 |
| Start, X1 as in your game | 23.4 | 24.2 |
| Start, X1 beside him | 23.4 | 25.1 |
| Start, X1 behind him | 23.4 | 25.1 |
| Start, your game but X5 on I4 | 23.3 | 23.5 |
| Start, your game but X4 and X5 in the lane | 23.1 | 23.2 |

- **Check 1 (a clear lane is bad for the defence):** holds. 25.1 against 23.2 with help (1.9); it was 1.1 for other reasons.
- **Check 2 (in front beats beside or behind):** holds by the reading for the first time. 24.2 against 25.1. Before, all four squares read 23.4.
- **Who is behind the on-ball defender:** your game's defence reads 24.2 at the start; with a big in the lane, 23.2 to 23.5. Before, there was nothing between them.
- **The sprint into the lane no longer reads as nothing:** 25.1 before and after. It used to fall to 23.1.
- **Check 3 (an arrow that covers beats one that covers nothing):** not shown. By the search X1's arrow on the ball handler reads 19.4 and pointing away 24.2, but that is the reach (a reach needs the arrow on him), not a wall. Off the ball every arrow still reads the same. That is the passing measure, next.
- **Check 9 (both sides read the same):** holds by construction. One measure, one number.

### By play (forced lines, 16 play-outs a line, after the beat)

| Line | Lane off (18p) | Lane on |
|---|---|---|
| Lane open, the offence as it chooses | 25.1 (20.1 to 30.0) | 22.0 (16.5 to 27.5) |
| Lane open, made to sprint into it | 26.9 (21.6 to 32.1) | 27.8 (26.9 to 28.8) |
| Help in the lane, the offence as it chooses | 22.5 (18.0 to 27.0) | 18.2 (12.7 to 23.7) |
| Help in the lane, made to sprint into it | 23.4 (19.9 to 26.9) | 21.1 (15.6 to 26.7) |

- **The defence's half of check 1 holds.** Help costs the offence 3.8 by its own choice and 6.7 when it drives. Before: 2.6 and 3.5.
- **The offence's half fails.** Made to sprint it scores 27.8, and 13 of the 16 end in a three off the kick-out. By its own choice it starts with a wing stepping sideways 15 times in 16 and scores 22.0. The same gap showed in the run before the map was fitted (28.0 against 20.1). So the reading is still short on what a drive does to the other four defenders.
- **Sixteen play-outs a line do not separate lane on from lane off.** The ranges overlap in every row. I stopped there: that point is made, and more play-outs would not change what comes next.

### In self-play (All-Star against itself, the app's rules)

| | Lane off (18o, 200 possessions) | Lane on (160 possessions) |
|---|---|---|
| Points a possession | 1.09 | 1.02 (0.92 to 1.12) |
| Rim shots in 100 possessions | 30 | 31 |
| Drives finished inside with no square defender | 42 of 47 | 30 of 33 |
| Defence steps into the paint, a possession | 0.69 | 0.71 |
| Reaches a possession | 0.80 | 1.07 |
| Ball won by a reach | 39 of 159 | 43 of 171 |
| Possessions ending in a turnover | 20 in 100 | 27 in 100 |
| Defence fouls a possession | 0.33 | 0.42 |

**The defence does not help more.** It steps into the paint as often as before. It reaches more.

## 4. Why the defence still doesn't help: three findings

**Presumed the computer wrong first (D-196). Two of these are not the computer.**

1. **The reach beats everything.** On your board, at the defence's first turn, a reach by X1 reads 18.5 for the offence. Every turn without one reads 23.2 or more. The same holds with the lane off (18.1). By the cards a reach wins the ball 1 time in 4. So a defender next to the ball handler should reach, by the rules, and where the other four stand hardly matters. Real FIBA basketball has about 0.15 turnovers a possession of every kind; this has 0.20 to 0.27 from reaches alone.
2. **Help can't arrive in one turn.** From next to their men (B4, P2), X4 and X5 can't get behind X1 before the drive. Nothing the defence does at its first turn changes the reading. Help has to be in the setup. The old setup places by its old reading; the searched setup, read with the lane, puts X5 by the rim (J2) but scatters the other four. That is stage 3 of the plan and it is now the next thing to build.
3. **A shot from the rim square can never be faced square.** "In front" means nearer the rim than the shooter, and nothing is nearer than the rim square (I2). Every contest there counts as from behind: the rating less 6, at least 1. 30 of 61 inside shots in the last run were contested that way, and 45 of 78 in 18o's. A big standing set under the basket takes 1 off a layup.

## 5. What it proves, and what it doesn't

- **Both engines agree** with the lane on: 120 positions and 12 searches (the defence's open list included), 0 different. The step's own test repeats it on 24.
- **Speed (desktop, 9 decisions in 10, seconds; two rounds, timed beside step 18p's code):**

  | | Rookie | Starter | All-Star |
  |---|---|---|---|
  | Target | 0.3 | 1.0 | 2.5 |
  | Step 18p | 0.23 to 0.24 | 0.68 to 0.76 | 1.87 to 1.89 |
  | This step, lane off (the default) | 0.21 to 0.22 | 0.76 | 1.79 to 1.84 |
  | This step, lane on | 0.74 to 0.76 | 1.55 to 1.83 | 3.41 to 3.64 |

  **With the lane on, all three levels break the speed budget.** The first form of the measure cost a tenth (All-Star 1.93). The step into the lane and the Dribble each read the lane again, and that is the cost. It is the first thing to mend before the lane goes on. A playtest with `?lane=1` will feel slow, most on a phone.
- **Tests:** `tests/test_rules_current.py` and the named test files: 321 passed, 14 marked as expected failures from before, and 1 failed, the timing test (1.95 seconds on one decision against a limit of 1.7), as since 18f. Not loosened. `tests/test_static.py`, run on its own: 11 passed. `tests/test_computer.py`: 2 passed, 1 failed, the stored game from before D-184 that already failed on 18n's code. The new file is `tests/test_lane_18q.py` (14 tests).
- **Not proven:** that the lane makes the computer play better. By the reading it meets checks 1 and 2. By play it does not yet change what the defence does, and the offence still passes up the open lane. So it stays off.
- **The setup as it was reads without the lane.** Its readings run in the slow engine, where the lane took it to 3.7 seconds against a budget of 1.2 on your board.

## 6. Compute

**6.3 core-hours against an estimate of 5.6** (`docs/runs/step18q/PREDICTIONS.md`). The stop was 11.

| Stage | Estimate | Used |
|---|---|---|
| 1a The measure in both engines, agreeing | 0.6 | 0.6 |
| 1b The design checks (the reading, the search, forced lines) | 1.2 | 2.6 |
| 1c Speed | 0.3 | 0.3 |
| 1d The map fitted on play with the lane on; the tests | 2.0 | 2.7 |
| 2 In-play faults | 1.5 | 0 (not reached) |

Stage 1b ran past twice its estimate. The measure was rebuilt twice after its first play-outs (the step into the lane, then the Dribble), and each form was played again. I stopped playing there and report it here, as the rule asks.

## 7. Decisions for you (three)

1. **The reach.** It decides every defensive turn (finding 1). Options: (a) I bring you the reach's numbers by matchup next step, with two or three ways it could be ruled, before any more defence is built; (b) leave it until human error is modelled, as D-196 point 4 would have it. **I recommend (a).** Every defensive goal in your message (sag, help, deny a pass) loses to a reach while a reach wins the ball 1 time in 4. This is the cards and the rule, not the computer.
2. **The rim square.** Options: (a) leave it: the rim is guarded by standing on it; (b) rule that against a shooter on the rim square, a defender next to him with his arrow on him is square. **I recommend (b).** It is a hole in the board's geometry, not a design choice, and half of all inside shots go through it.
3. **The next iteration.** I recommend this order, and that you confirm design checks 10 to 12 in the map:
   - first, **the setup judged by the lane** (who is behind the on-ball defender), since that is where help has to come from;
   - with it, **the drive's effect on the other four** (why the kick-out pays), so the offence takes the lane;
   - then **passing options**, your constant goal, as iteration 2 of the map.
   The lane stays off by default until the setup uses it. Your playtest with `?lane=1` is welcome before then.

## 8. Model advice

Claude Fable 5.2, effort high, for the next step. It is the setup stage and a rules question, both of which turn on reading positions closely.
