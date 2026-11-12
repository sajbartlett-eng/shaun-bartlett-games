# Step 18e report: the control rule set, and the defence sees every legal move

## First: two levels go over their speed targets with the open list, so they don't have it

- **The open list fits the All-Star** (2.0 s to finish 1 pair, target 2.5 s) and is on for it.
- **It puts the Rookie at 0.44 s (target 0.3) and the Starter at 1.2 s (target 1.0).** I stopped there and trimmed
  nothing. Both keep today's list, so both still fit (0.23 s and 0.66 s). The speed section has the table.

## In plain words: what the defence now does, and what it still can't

**What it does now that it didn't:**

- **It looks at every legal action.** Nothing in the code names a kind of move to keep or prefer any more. About
  1,000 legal first actions a position are read, and only the reading decides which go forward.
- **It steps next to the ball handler and goes for the Steal.** Nobody told it to. In self-play the ball is now lost
  on about 1 possession in 7, where it was 1 in 20.
- **It closes out to a shooter with a Move,** so the Contest that follows isn't wasted.
- **It finds two-defender turns** the old list never offered.
- **It beats the old list** by 4.7 points a pair, head to head.

**What it still can't do:**

- **It doesn't find your closeout order** (Quick Step closer first, keep the Move for the Contest). It reads the
  Quick Step and the Move closer as the same. Played out by the rules, your order is about 2 points better.
- **It can't tell many defence turns apart.** Many read exactly the same, so which one it plays is partly chance.
- **A one-action turn is judged before the offence replies.** That makes some turns look better than they are. It
  was true before this step; the open list makes it show more.
- **The offence's list is still hand-written.** Reading every legal offence action didn't help in its pilot (part 4).

## Part 1: the rule

- **Size 2 without the extra foul roll is the app's rule,** in both engines (D-153, D-154). The table's rules are
  unchanged.
- **The sentence is in the app's rules text, the rule reminders, the course and the result line:** "Your last
  movement this phase decides your control. After a Quick Step or a Sprint you're rushed: your shot or Contest is 2
  lower. A Move puts you back in control."
- **The "RUSHED" marker is on** whenever the rule is.
- **No refit of the map for the rule.** I didn't run one, as ruled.
- `?control=0` in the address turns the rule off; `1` or `3` plays another size.

## Part 2: the open list (`search.open_list`)

**How it is built.** Reading every legal defence action in full costs about 250 microseconds each, and a search
builds about 25 lists. That is tens of seconds a decision. So, as the prompt allows:

1. **Every legal action gets a cheap first read:** the position's own looks, read again with that one defender
   where the action leaves him.
2. **Every pair of actions by two defenders** is read the same way.
3. **After the best first actions,** the same defender moving again, a Steal, a Challenge or an Intercept is read.
4. **The best by the cheap read get the full read,** and the best of those are the list. The list is as long as
   before.

- An action that moves nobody (a Pause, a Steal) has no cheap read, so it gets the full read at once.
- Actions the cheap read can't tell apart count as one.

**The pilot** (12 defence positions from play, the new rules; `pilot_defence_*.json`):

| | Today's list | The open list |
|---|---|---|
| The choice is the best turn found | 5 of 12 | **9 of 12** |
| Points left on the table a decision | 1.11 (0.28 to 1.95) | **0.29 (-0.07 to 0.65)** |
| Left more than 2 points | 3 | 0 |

**The head to head** (All-Star against All-Star, 1 pair ahead, the new rules; `h2h_open_defence.json`):

| | Result |
|---|---|
| Gain a pair | **+4.7 points** (2.7 to 6.8) |
| Wins, losses, ties | 98, 81, 61 |
| Stopped | the sequential test said "a gain" at 186 pairs; the run ended at 240 |
| Shots in phases 1 and 2, each on offence | 70% and 72% |

- **Where the gain comes from:** against the old list's computer the open list's defence took the ball on 75 of 240
  possessions. The other way it was 30 of 240.
- **Why so many:** the old list's offence doesn't expect a defender to step in and Steal, so it leaves the ball
  there. When both sides have the open list (the self-play below) the ball is lost on 29 of 200.

**Do the answers fall out?** Nothing was told to the computer; these are the tests.

| The missing move | Does it reach the search? | Is it chosen? |
|---|---|---|
| Step in, then Steal: the position 18d lost 4.1 on | yes | **yes** (the step in; the Steal follows) |
| The same: 18d's 1.4 position | yes | **yes** |
| The same: 18d's 2.9 position | no | no: a Quick Step elsewhere reads 0.4 better |
| Step next to the shooter now (the closeout board, worth 7.4) | yes | **yes,** with a Steal added |
| Your line, step 1: Quick Step closer | no | no: it Moves closer; the two read the same |
| Your line, step 2: Pause | yes | no: it Moves next to him and Steals, 7.4 better by its reading |
| Your line, step 3: Move into the Contest | yes | **yes:** the three is worth 15 |

**The sense checks.** Where the computer prefers something else, both moves played out by the rules 160 times each
with the same dice, the All-Star on both sides (`sense_checks.json`). The number is what the offence went on to score.

*1. The closeout board, step 1.* O4 (three 11) has the ball at A3 and can't move again. X3 is at F4.

| Move | Why, by the reading | Offence scored | Against the computer's |
|---|---|---|---|
| The computer's: X3 Moves to C4, facing him | closer, and a Quick Step still reaches him | 31.3 (30.4 to 32.1) | |
| Yours: X3 Quick Steps to E4 | keeps the Move, so the Contest is full | 29.4 (28.5 to 30.2) | **1.9 better** (0.8 to 3.1) |
| X3 Sprints next to him | | 33.1 | 1.8 worse |
| Nothing | | 32.8 | 1.6 worse |

- **My view: your move looks right.** The reading can't see that a Move kept is worth more than a Quick Step kept.

*2. The closeout board, step 2.* X3 is at E4 after his Quick Step; the offence has moved an off-ball player.

| Move | Offence scored | Against the computer's |
|---|---|---|
| The computer's: X3 Moves next to him, then Steals | 19.5 (16.6 to 22.3) | |
| Yours: the defence Pauses | 18.2 (15.6 to 20.8) | 1.3 better (5.3 better to 2.7 worse) |
| X3 Moves next to him and stops | 26.8 (24.8 to 28.8) | 7.3 worse |

- **My view: too close to call.** After your Pause the computer's offence didn't shoot. It moved two players, and
  the defence then stepped in and Stole anyway. The Steal succeeds 35 times in 100 either way.

*3. Your game EB3F5B, the pass to the corner in the air.* X4 is at F4, four squares from O4.

| Move | Offence scored | Against the computer's |
|---|---|---|
| The computer's: X4 Moves to C4, facing him | 30.0 (every play-out) | |
| X4 Quick Steps to E4 (your order) | 33.0 (every play-out) | 3.0 worse |
| The log: the defence Pauses | 33.0 (every play-out) | 3.0 worse |

- **My view: the computer's move looks right here.** O4 can still move. After the Quick Step he sidesteps and
  shoots open. After the Move closer, X4 reaches him wherever he goes, though rushed.

*4 and 5. Two of 18d's Steal positions.* The computer no longer takes the Steal 18d's reading wanted.

| Position | The computer's move | Offence scored | "Step in, then Steal" | Against the computer's |
|---|---|---|---|---|
| 18d's 2.9 (clock 2) | X1 Quick Steps to N7 | 27.2 | 31.0 (28.5 to 33.5) | **3.8 worse** (1.3 to 6.3) |
| 18d's 1.2 (clock 10) | X4 Quick Steps to M9 | 30.7 | 33.0 (30.5 to 35.6) | 2.3 worse (0.4 better to 5.0 worse) |

- **My view: the computer's move looks right on the first, and probably on the second.**

## Part 3: your playtest, game EB3F5B

- **The log replays to the end, every line legal,** and gives the logged 33 (`replay.json`). The log doesn't give
  the defence's facing at placement; it doesn't matter, because every defender moves before his facing counts.
- **Once the three was declared, nothing helped.** X4 was at F4. His only way to the shooter was a Sprint: rushed,
  from further out than the shooter, and facing the wrong way. That Contest takes almost nothing off and risks a
  foul, so no Contest (33) was right. The computer's two reaction moves in the log changed nothing.
- **The mistake was the Pause** while the pass was in the air. From that position:

| | The defence, pass in the air | Then the three is worth |
|---|---|---|
| The log | Pauses | 33 |
| The old default (no rule, the old list) | X2 Moves, X4 Quick Steps to E4; then X4 Moves into the Contest | 21 |
| The new default | X4 Moves to C4, X2 Moves; then X4 Quick Steps into the Contest, rushed | 27 |

- **So: it closes out and Contests under both.** It doesn't help early, and it doesn't leave him.
- **The new default's closeout is the wrong order for a shooter who stands still** (27 against 21), and the right
  one for a shooter who sidesteps (sense check 3). You shot from where you stood.

## Part 4: the offence's list

**Stopped at the pilot: it shows no gain.** 24 of step 18a's offence positions, the defence's replies on the open
list both times (`pilot_offence_todays_list.json`, `pilot_offence_every_action.json`).

| | Today's offence list | Every legal offence action read in full |
|---|---|---|
| The choice is the best turn found | 17 of 24 | 15 of 24 |
| Points left on the table a decision | 0.55 (0.02 to 1.09) | 0.65 (0.14 to 1.16) |

- **Why it doesn't help:** the offence's loss isn't that moves are missing. With every action read, the better
  turns are there and the one-turn reading ranks them too low to make the list (38th, 55th, 136th). On offence the
  fault is in how the reading ranks, not in what is generated.
- **A two-action turn still needs its first action to rank in the best few.** "Move, then shoot" was lost that way
  on one position.
- **The tests:** board 9's corner man relocating still isn't on the list, and still reads 1.2 better. Board 11's
  pass in the air wasn't looked at.
- Reading every offence action in full is too slow to play anyway. A cheap read for the offence would be a build
  the size of part 2, and this pilot says it wouldn't pay yet.

## Part 5: the re-measure on the final default

**The boards** (`boards.json`; the search's choice 1 pair ahead):

| Board | Old default | New default |
|---|---|---|
| 1: doing nothing, against the choice | 4.4 worse | 0.2 worse (the drive is a Sprint, so its layup is rushed) |
| 3: the board's early help, against doing nothing | 2.1 to 2.4 worse | 1.6 to 2.1 worse |
| 8: the backdoor cut and pass, against the choice | level | 0.4 behind |
| 9: the kick-out, against the choice | 1.2 behind | 1.2 behind |
| 9: the corner man relocating | 1.2 better, not on the list | 1.2 better, not on the list |

**The 19 boards at 1 pair** (`exam_default_fixed.json`, `exam_todays_list_fixed.json`):

| | Pass | Changed from step 18c |
|---|---|---|
| Step 18c (no rule, today's list) | 10 of 19 | |
| The new rule, today's list | 8 of 19 | lost 2, 10 and 12; gained 9 |
| The final default (the rule, the open list) | 8 of 19 | lost 2 and 10 |

- **Boards 2 and 10 are lost to ties.** On both the computer still reads the board's turn as well as its own choice
  (the same value to two decimals) and plays a different one of the equal turns. That is the "can't tell turns
  apart" weakness, not a worse reading.
- **Board 9** passes with the rule alone and fails with the open list; **board 12** the other way round.
- I didn't run the boards on the clock: the 1-pair run answers the step's question.

**Self-play, All-Star, 200 possessions** (`fidelity.json`), beside step 18d's size 2 (which had the extra foul roll
and the old list):

| | 18d, size 2 | The final default |
|---|---|---|
| Points a possession | 29.5 (28.4 to 30.7) | **26.8** (25.1 to 28.4) |
| The ball lost, in 100 phases kept | 4.7 (2.6 to 8.4) | **14.2** (10.1 to 19.7) |
| Possessions that end with the ball lost | 10 of 200 | 29 of 200 |
| Shots in phases 1 and 2 | 72% | 76% |
| Shots by phase, 1 to 6 | 35, 37, 20, 6, 2, 1% | 40, 36, 19, 4, 2, 1% |
| The clock runs out | 0 of 200 | 0 of 200 |
| Shots taken rushed | 18% (14 to 25) | 13% (9 to 19) |
| Contests after a Move | 69% | 62% (51 to 73) |
| Contests after a Quick Step, after a Sprint | 5%, 23% | 22%, 14% |
| Contests that draw a foul | 17% | 16% |

- **The ball lost is now near basketball's rate** (about 13 or 14 possessions in 100).
- **The calibrated map's error rose** from 8.0 to 10.8 (9.2 to 12.4). The cause is the open list, not the rule: more
  possessions end at 0. I haven't refit it; the weights are held.

## Speed

1 pair on 9 decisions in 10, in seconds, two runs each, timed in turn in the same run (`speed_defence.json`).

| Level | Target: desktop, phone | The new rule, today's list | With the open list |
|---|---|---|---|
| **Rookie** | 0.3, 1.0 | 0.23, 0.23 | **0.45, 0.44: over** |
| Starter | 1.0, 2.0 | 0.69, 0.64 | **1.20, 1.14: over** |
| All-Star | 2.5, 3.0 | 1.04, 1.08 | 1.99, 2.02 |

- **As built:** the All-Star has the open list (2.0 s). The Rookie and Starter don't (0.23 s and 0.66 s).
- At the assumed phone speed (4 times slower) the All-Star is at 8 s. It was over before (4.2 s).
- The machine ran faster today than at 18d (the All-Star on today's list took 1.4 to 1.5 s then).
- An open list costs about 19 ms to build; today's costs 8.

## Compute against the estimate

Estimate: about 12 core-hours without part 4, 20 with it. Used: about 11, of which 3 on two passes I had to throw away.

| Run | Predicted | Used | Against the prediction |
|---|---|---|---|
| The pilot, two passes | 0.9 a pass; the open list best on 7 or more of 11, under 0.6 left | 1.76 | right: 9 of 12, 0.29 |
| A pilot pass thrown away | | 0.7 | a fault in the cheap read, found by replaying your game |
| The head to head | 5; +1, a fair chance of "no gain" | 1.95 | **wrong on the size:** +4.7, clear at 186 pairs |
| The sense checks | 1.0 | 2.17 | a first pass (2.26 more) was thrown away: its dice were shared |
| Self-play on the final default | 1.0; 29 points, the ball lost twice as often | 1.06 | **wrong:** 26.8 points, lost three times as often |
| The offence's pilot, two passes | 1.5 a pass; best on 3 in 4 with every action read | 0.24 | **wrong:** no gain (15 of 24 against 17) |
| Speed, boards, replay, agreement checks | 1.0 | about 0.6 | |

## 1. Changes to the printed game

None. The control rule is the app's only (D-153); the table's rules and every printed page are unchanged.
`RULES_CURRENT.md` gains one entry under "Split by format".

## 2. What changed

- **Step 18d is merged.** D-153 to D-156 are recorded.
- **`rules.control`** is `'app'` by default: size 2 in the app's format, off at the table. `'0'` turns it off.
- **The extra foul roll on a rushed Contest is gone** (D-154), in the rules and in the reading.
- **A game log from before the rule replays without it.**
- **`search.open_list`** in both engines: `search.open_turns_x` and `Read.reread` in Python, `openTurnsX` and
  `Read.reread` in `engine.js`. The All-Star's profile has it on for the defence. `search.open_list: false` turns it
  off for every level.
- **The old hand-written list is still in the code,** for the Rookie, the Starter and the offence.
- **Tools:** `tools/step_18e.py` (the replay, the closeout line, the sense checks, the head to head, speed, the
  boards), and `open_list` options in the diagnosis, line, play-out, exam and agreement tools.

## 3. What it proves

- **The two engines agree** on the new default (the All-Star's open list on) and with the open list forced on for
  the defence: 0 mismatches.
  - The new default: 600 positions, 4 whole searches and 300 shot reactions.
  - The open list forced on: 600 positions (249 of them open lists, turn for turn) and 4 whole searches.
  - The open list forced off: 300 positions and 2 whole searches.
- **Nothing in the open list names a kind of move.** Two places name kinds for other reasons, and I'd rather you
  knew: an action "moves a piece" or doesn't (that decides whether the cheap read applies), and two movements in
  either order are one turn (as before).
- **With the rule off and the open list off the computer plays as it did on `main`:** the same choice and value on
  all 22 hand-board decisions at each of the three levels.
- **Tests on the new default** (`test_rules_current`, `test_static`, `test_step3n`, `test_step3m`,
  `test_course_boards`): 79 pass, 14 expected failures, 1 fail.
  - The fail is the timing test that sits at its limit: 2.16 s against 1.70 s, as at steps 18b to 18d. Not
    loosened.
  - Exam board 2 is an expected failure again (it passed once at 18d, on a fast run).
- **The golden tests** (`test_golden_and_regression.py`): 8 of 8 pass.

**Three things a coach could say, from the measured positions:**

- "X3 was a Quick Step and a Move from the corner. Quick Step first and keep the Move: the Contest is then worth its
  full 6. Move first and the Quick Step into the Contest is rushed: 4."
- "The ball handler stood next to nobody. X2 stepped next to him and reached: 35 in 100 to take it, 30 in 100 to
  foul. We'd never looked at that before."
- "X4 helped on the drive from the corner and was a Sprint away when the ball went back there. From that far, and
  from the high side, don't Contest: it takes nothing off and risks a foul."

## 4. For Shaun to decide

- **The Rookie and the Starter.** The open list puts both over their speed targets. Options:
  - leave them on today's list, as built. The All-Star then defends very differently from the other two;
  - let me cut the open list's cost for them in the next step (fewer full reads, or the cheap read on fewer turns):
    I'd expect to reach the Starter's target, not the Rookie's;
  - raise their targets.
- **Steals.** The computer now steps in and Steals often: the ball is lost on 1 possession in 7 in self-play, and on
  3 in 10 against a computer that doesn't expect it. A player who leaves the ball next to a defender will be robbed
  the same way. If that is too many, the Steal's odds are the lever, and they are yours.
- **The five sense checks.** My views: your move on the closeout board's step 1; too close to call on its step 2;
  the computer's on your game's position and on the two Steal positions.
- **Is the open list the All-Star's default?** It won the head to head and keeps the All-Star's speed target, so by
  the prompt's rule it is on. Say if you'd rather hold it until the Steal rate is settled.
- **The map.** Its error rose with the open list. A refit is the next step's first job if you release the weights.

## 5. Noticed, not touched

- **A one-action turn is judged before the offence replies.** The switch that fixes it (`quiet_points`) has been
  off since D-122. With the open list it matters more: the first action is often one of many that read the same.
- **Your closeout order needs the reading to value a Move kept.** That is a change to the reading, which is held.
- **The cover's own re-read doesn't know the control rule** (it reads a moved defender's Contest with his old
  control state). The open list's re-read does. I left the cover as it is: it is part of the held reading.
- **The trainer's lists are still the old ones.**
- **The golden figure 18d said moves** is unchanged in the test file: the test runs under the table's rules, where
  the control rule is off.
- **The exam book** is untouched.

## 6. Model for the next step

Claude Fable 5.2, effort high. The next work is inside the reading in both engines (a Move kept, turns that read the
same, a one-action turn judged too early, the map), where a small change moves every decision and the speed budget.
