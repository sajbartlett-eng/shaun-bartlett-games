# Step 18n report: jump shots contested by position, the new contest ratings, the refit and the test

## In five lines

1. **Jump shots are contested by where the defender stands, and nothing else.** Anyone next to the shooter takes his
   card's contest off: no Contest move, no foul. Inside, the hand up is automatic and the block is a real gamble.
   Built in both engines, on in the app.
2. **Does the computer take contested threes only with its good shooters? Mostly yes.** 35 of its 37 contested
   threes came from shooters rated 9 or more. Shooters rated 8 or less took 13 threes, 2 of them contested.
3. **Scoring came down from 1.36 to 1.28 points a possession (1.22 to 1.34). FIBA is about 1.0.** Shots contested
   rose from 33 in 100 to 55.
4. **The generous part is now inside, and the block is never used.** Inside shots go in 75 times in 100. The defence
   went for the block once in 92, because on these cards it fouls half the time or more.
5. **A speed fault found and fixed on the way; the sense-check set only part re-recorded.** 14 of its 19 positions
   were replayed. Compute: 8.6 core-hours of the 10 allowed.

## Parts 0 and 1: merged, ruled, and the cards

- **Merged:** step 18l (pull request 74). There was no 18m pull request, so the restore was done here.
- **`DECISIONS.md`:** D-189 (contests restored), D-190 (no card or rule change without your agreement), D-191
  (position only), D-192 (the new jump-shot contest ratings), D-193 (nothing is zero).
- **The cards match the table.** All 81 cards, all seven contests, checked against
  `docs/reference/JUMP_CONTESTS_14NOV.md` by a test. Nothing but contest ratings changed on any card.
  - Inside contests are back at your original values, with their ranges and three floater chart entries.
  - Mid-range, long two and three contests are the map on your originals. Their range: average from 2, above
    average from 3.
  - The two new types take the Scoring Small Forward's and the Defensive Power Forward's contests, and keep their own
    foul ratings.
- **Levels:** contest ratings are the same at every level. The level files are regenerated.
- **One thing that had to follow the restore:** the anchor job's dunk-contest threshold. D-184 had carried it from 11
  to 5 with the rating. It is 11 again, or nearly every card would be an anchor.

## Part 2: the rule, built

- **Jump shots** (mid-range, long two, three). Every defender next to the shooter contests with no action, at his
  card's contest rating: 3 less from behind, 2 less if he is rushed. His arrow changes nothing. There is no Contest
  action and no shooting foul.
- **Inside shots** (layup, dunk, post, floater). A hand up next to the shooter is automatic: the rating less 3, 3
  less again from behind, never a foul. From in front with his arrow on the shooter the full rating is automatic and
  never a foul. From anywhere else he may go for the block, a Contest action: one foul roll from in front with the
  arrow off, two from the side or behind.
- **Only the best contest counts. A contesting defender always takes at least 1 off** (D-193).
- **The switch:** `rules.position_contest`, on in the app, off at the table. `?positioncontest=0` turns it off.
- **The sentence,** in the help and the rules text, as you wrote it.
- **The explanations:** "X2 was beside O4, so the three was contested (20% off)." Inside: "X5's hand up from
  behind: 1 off", "X5 went straight up in front of O1 with his arrow on him: 8 off, and no foul", "X5 went for the
  block from the side: 8 off".
- **The computer's search has no jump-shot Contest move.** Its reading of a look counts any defender who can get
  next to the shooter in the reaction, by position.
- **The foul price no longer touches jump shots.** It prices steal fouls and fouls on inside shots only.
- **Derived files regenerated:** the JavaScript engine, `site/engine_bundle.json`, the level files, the one-file app,
  the team sheet, `RULES_CURRENT.md` and the rules register.

**Cases the lines don't settle. I read each the way closest to "position decides". Marked for you.**

1. **Both of the reaction's actions can now be movements on a jump shot.** A contest needs no action, so a defender
   can Quick Step in and then Move to be set, or come from two movements away. The reaction rule itself is unchanged.
2. **Beside the shooter counts in full on a jump shot.** Your lines name only "from behind" as a reduction.
3. **Inside, a rushed defender straight up in front still contests in full, 2 lower.** Rushed takes 2 off every
   contest.
4. **The block is held at 1 too.** A defender who goes for it from behind while rushed takes at least 1 off.
5. **How far the look-ahead follows a closeout differs by level.** The All-Star plays a second movement that ends
   next to the shooter; Starter and Rookie stop at one (Part 5). None of them plays a closeout whose first movement
   ends away from the shooter, inside the look-ahead at a declared shot.

**Nothing is zero: the other rolls (D-193, listed, not changed).**

- **A rushed defender's Steal.** 35 of the 81 senior cards have a Steal of 2 or less. Rushed, that is 0 or less.
  (The roll is the ball handler's Dribble less the defender's Steal.) At youth level 6 cards; at junior none.
- **A shot after its contest.** The rating a shot is rolled at is the shooter's rating less the contest, held at 0.
  - With the shooter set, one senior pair reaches 0: a post shot of 8 against a post contest of 8.
  - With the shooter rushed as well, more do: 172 senior shooter-and-defender pairs on a three, 123 on a floater,
    122 on a dunk, 77 on a post shot, 11 on a long two.
  - At junior level it is common: 223 pairs on a three with the shooter set.
- **Nothing else reaches 0.** Dribble, Pass and Screen never fall under 9. Agility, Intercept and Challenge never
  fall under 1, rushed.
- The full list by level is in `docs/runs/step18n/zero_ratings.txt`.

## Part 3: the refit and the re-recording

**The maps.** Each level's own self-play on today's cards and rules, as in 18h.

| | Possessions | Positions | Lines of its own | Points a possession | As real points |
|---|---|---|---|---|---|
| All-Star | 200 | 5,817 | phases 1 to 5, both sides | 25.8 (24.4 to 27.2) | 1.29 |
| Starter | 90 | 1,207 | phases 1 and 2 | 21.8 (20.0 to 23.6) | 1.09 |
| Rookie | 120 | 1,129 | phases 1 and 2 | 17.7 (16.1 to 19.4) | 0.89 |

- **Every line slopes the right way.** The All-Star now has lines of its own through phase 5: possessions run
  longer, so later phases have enough positions.
- Starter and Rookie were played twice. Their first runs came before the speed fix in Part 5, which changes how
  they value a declared shot. The table is the second run. The All-Star's play did not change, so its run stands.

**The foul-price numbers,** from the All-Star's run: 0.22 fouls a possession (0.15 to 0.29) and 25.8 a possession
(24.4 to 27.2). They were 0.21 and 27.2.

**The sense-check set, on today's cards and rules.** The set is rebuilt card for card (`positions_18n.json`), and
the tool refuses a position holding a card that is not today's.

- **14 of the 19 positions were replayed, not all 19.** A possession under the new rule runs half as long again
  (28 decisions, from 19), so a play-out costs about 30 core-seconds. The full set at 16 play-outs would have cost
  about 5 core-hours.
- **What was played:** the candidates the set names and the computer's own choice. 10 positions at 16 play-outs, 4
  at 8.
- **Not replayed:** board 3 (it needs its 24 level turns played out) and the four "shoot now or play on" positions.
- **The computer is best or level on all 14.** Points lost a position: 2.1 (0.6 to 3.6). With 8 or 16 play-outs
  "level" is a wide band, so read that as "nothing clearly wrong", not "all right".

| Position | Best by play | The computer |
|---|---|---|
| Closeout, the shooter cannot move | X3 Moves to C4 and keeps the Quick Step; X2 to B6: 24.0 | X2 to B6 alone: 2.3 behind (1.0 ahead to 5.7 behind) |
| The same, your order | | 0.7 behind the best (3.8 ahead to 5.1 behind): level |
| Closeout, the shooter can move | X3 Moves to C4; X2 to B6 | 5.3 behind (1.0 ahead to 11.6 behind) |
| Closeout, step 2 | X3 Moves next to him, then a Steal | pauses: 2.3 behind (8.7 ahead to 13.3 behind) |
| Game EB3F5B | four turns level, 26.6 to 26.9 | X2 to B7: level |
| The Steal position, clock 2 | step in, then Steal | pauses: 2.9 behind (6.2 ahead to 11.9 behind) |
| The Steal position, clock 10 | step in, then Steal | pauses: 11.7 behind (0.1 ahead to 23.4 behind) |
| Contest or not, 1 to 4 | every turn level | level |
| Move, then shoot, 1 and 2 | the move, then the shot | level, and the same turn on 2 |
| Board 1 | X1 steps in for a Steal: 25.8; every other turn 30.0 | X2 to B4: 4.2 behind (2.1 ahead to 10.5 behind) |
| Board 8 | the cut alone: 27.8 | O1 to E10, then waits: 0.6 behind |

- **Your closeout order is level with the best again.** The best by play now is the Move that arrives set. A set
  contest is the full rating; a Quick Step in is 2 lower.
- **On both Steal positions stepping in to Steal still plays out best,** and the computer pauses. On the second it
  is nearly a clear miss.
- **"Contest or not" no longer asks anything.** The contest is automatic, so every turn there scores the same.

**The exam.** Position 1 takes its answer from the replay: stepping in for a Steal, doing nothing, or moving X2 or
X4 are level by play, and each was played out. It passes again. Position 3's answer hangs on board 3, which was not
replayed: it fails and is listed as open. Position 16 fails as in 18l.

**Golden values re-recorded, each with the reason "D-189 to D-193" in the test:** the two ceilings in
`test_golden_and_regression.py`, and seven tests that held contest values or a Contest on a jump shot.
`test_contest_18j.py` now tests D-177 with D-191's switch off, since D-191 replaces it in the app.

## Part 4: the test, player against player

All-Star self-play, 200 possessions, on the final default: today's cards, the rule on, the refitted maps in.

**Does the computer shoot contested threes with everyone, or mainly with its great shooters? Mainly with its good
ones.** 35 of its 37 contested threes were taken by shooters rated 9 or more. Shooters rated 8 or less took 13
threes, and 2 of those were contested.

**Every three: the shooter's open rating against the contest that counted.** Each cell is shots taken, then in
brackets the makes the cards give them. (The game scores a shot by its chance, rating less contest in 20. It rolls
no make or miss, so "made" is that chance added up.)

| Shooter's open three | Open | Contest 1 | Contest 2 | Contest 3 | Contest 4 | All |
|---|---|---|---|---|---|---|
| 11 | 6 (3.1) | 3 (1.5) | 3 (1.4) |  |  | 12 (6.0) |
| 10 | 8 (3.9) | 14 (6.3) | 1 (0.4) |  |  | 23 (10.6) |
| 9 | 28 (12.6) | 5 (2.0) | 7 (2.2) | 2 (0.6) |  | 42 (17.4) |
| 8 | 9 (3.6) |  | 1 (0.3) |  |  | 10 (3.9) |
| 7 | 1 (0.3) |  |  |  |  | 1 (0.3) |
| 6 | 1 (0.3) |  |  | 1 (0.1) |  | 2 (0.4) |
| **All** | 53 (23.8) | 22 (9.8) | 12 (4.3) | 3 (0.7) | 0 (0.0) | 90 (38.6) |

- **90 threes in 200 possessions; 37 contested (41 in 100, 32 to 51).** Before this step 25 in 100 were.
- **Shooters rated 10 and 11 took 35 threes and 21 of them were contested.** They shoot over a defender.
- **Shooters rated 9 took 42 and 14 were contested.** They mostly wait for the open one.
- **Shooters rated 8 or less took 13, all but 2 open.**
- **No three met a contest of 4, and only 3 met a contest of 3.** 22 of the 37 contests took just 1 off.

**Mid-range and long twos: none were taken.** Not one in 200 possessions. An open mid-range shot is worth at most
12 in 20 for 2 points; the computer always finds a three or a rim shot worth more.

**Where the contested threes came from.**

| Shooter | Contested threes |
|---|---|
| Stretch Small Forward A (three 10) | 8 |
| Sharpshooter A (three 11) | 6 |
| Scoring Point Guard A (three 10) | 6 |
| Scoring Small Forward A (three 9) | 4 |
| Stretch Small Forward B (three 9) | 3 |
| Bucket Getter B, Combo Guard A (three 9) | 2 each |
| Sharpshooter C, Two-Way Shooting Guard A, Three-and-D B (three 9), Three-and-D A (three 10) | 1 each |
| Scoring Small Forward B (three 8), Post Scorer Centre A (three 6) | 1 each |

| Where the defender stood | Contested threes | Points a shot |
|---|---|---|
| In front, set | 13 | 1.00 |
| In front, rushed | 9 | 1.33 |
| Beside, set | 4 | 1.20 |
| Beside, rushed | 9 | 1.32 |
| Behind | 2 | 1.43 |
| Nobody (open) | 53 | 1.35 |

- **Half the contests (18 of 37) were rushed:** a defender who got there on a Quick Step or a Sprint. Rushed, most
  defenders take 1 off, and a three contested that way scores what an open one does.
- **Only a set defender in front brings a three down to FIBA's level:** 1.00 a shot.

**Inside shots.** 92 in 200 possessions: 78 layups, 8 floaters, 6 post shots, no dunks.

| Shooter's open rating | Open | Contest 1 | Contest 2 | Contest 3 | Contest 4 | Contest 5 | Contest 6 | Contest 8 | Contest 9 | All |
|---|---|---|---|---|---|---|---|---|---|---|
| 19 | 7 (6.4) | 4 (3.3) | 1 (0.8) | 6 (4.5) |  | 4 (2.8) | 1 (0.7) |  |  | 23 (18.5) |
| 18 | 14 (12.0) | 3 (2.4) | 6 (4.8) | 6 (4.4) | 9 (6.2) | 5 (3.2) |  | 1 (0.5) | 1 (0.5) | 45 (34.0) |
| 17 | 2 (1.6) | 3 (2.3) | 4 (3.0) | 5 (3.5) |  |  |  |  |  | 14 (10.4) |
| 16 |  |  |  |  |  |  | 1 (0.5) |  |  | 1 (0.5) |
| 15 | 2 (1.3) | 1 (0.7) |  |  |  |  |  |  |  | 3 (2.0) |
| 14 | 2 (1.4) | 1 (0.7) |  |  |  |  |  |  |  | 3 (2.1) |
| 13 |  | 1 (0.6) |  |  |  |  |  |  |  | 1 (0.6) |
| 11 | 2 (1.0) |  |  |  |  |  |  |  |  | 2 (1.0) |
| **All** | 29 (23.7) | 13 (10.0) | 11 (8.6) | 17 (12.4) | 9 (6.2) | 9 (6.0) | 2 (1.2) | 1 (0.5) | 1 (0.5) | 92 (69.1) |

| Where the defender stood | Inside shots | Went for the block | Fouls | Made, in 100 |
|---|---|---|---|---|
| Nobody (open) | 29 | | | 82 |
| Behind | 41 | 0 | 0 | 74 |
| In front | 16 | 1 | 0 | 67 |
| Beside | 6 | 0 | 0 | 68 |

- **The defence went for the block once in 92 inside shots, and fouled nobody.**
- **Why: on these cards the block is a bad bet.** A Contest foul rating of 10 is a foul half the time on one roll, and
  three times in four on the two rolls from the side or behind. A fouled layup then scores more than an open one.
- **Most inside shots are taken with the defender behind** (41 of 63 contested ones). The hand up from behind takes 1
  to 3 off a layup of 17 to 19.
- **Straight up from in front with the arrow on him happened once** (a contest of 9). The other in-front contests
  were hands up with the arrow off.

**Beside FIBA.** Nothing was tuned to these.

| Measure | Real FIBA | The game now | Before this step |
|---|---|---|---|
| Points a possession | 0.95 to 1.0 | **1.28** (1.22 to 1.34) | 1.36 (1.30 to 1.42) |
| Shooting fouls on threes | 1 in 100 | none, by rule | 0 of 89 |
| Shooting fouls at the rim | 20 to 30 in 100 | **0 of 78** (0 to 5 in 100) | 1 of 89 |
| Blocks | 6 in 100 twos | the game has none; the block was tried once in 92 | |
| Turnovers a possession | 0.15 | 0.085 (0.045 to 0.125), all from a reach | 0.08 |
| Steals tried a possession | not tracked | 0.47 (0.37 to 0.56) | 0.48 |
| Fouls on a Steal a possession | 0.05 to 0.08 | 0.20 (0.14 to 0.26) | 0.21 |

- **Scoring came down by 0.08 of a point and is still above FIBA by more than a quarter.**
- **Shots contested rose from 33 in 100 to 55** (48 to 62).
- **Possessions run longer:** 28 decisions each, where it was 19. Shots by phase 1 to 6, in 100: 22, 38, 16, 11,
  10, 3. Before: 39, 37, 16, 6, 3, 0.
- **The shot mix:** 90 threes, 78 at the rim, 14 other twos.

**Game EB3F5B, the pass to O4 in the corner.** Played out on today's cards and rules, 16 times each.

| What the defence does | The offence goes on to score |
|---|---|
| The computer's choice: X2 moves to B7 | 26.6 (24.5 to 28.7) |
| X4 Quick Steps to E4 | 26.6 (24.8 to 28.4) |
| The defence pauses, as in your game | 26.6 (25.9 to 27.4) |
| X4 Moves to C4, facing him | 26.9 (24.7 to 29.1) |

- **Nothing separates the four.** O4's corner three is a 9 now, worth about what the possession is worth anyway.

**Shooting that looks too generous, player against player. Listed, not changed.**

1. **An inside shot with the defender on the shooter's back: 74 in 100.** 41 shots. The hand up from behind is the
   rating less 6, so a contest of 8 or 9 takes 2 or 3 off an 18. European league rim shooting, most of it contested,
   is about 64 in 100 (your card audit).
2. **Open inside shots, and layups in all: 82 and 77 in 100.** FIBA's 20 to 30 fouls in 100 rim shots are missing
   too. A layup here is worth 1.54 points, and every inside shot 1.50.
3. **A three contested by a rushed defender: 44 in 100,** the same as an open one. 18 shots. Rushed takes 2 off a
   contest of 2 or 3, and D-193 holds it at 1.
4. **A three with a set defender beside the shooter: 40 in 100.** 4 shots, so thin.
5. **Open threes for shooters rated 9: 45 in 100, 28 shots.** That is the card, and the audit's "elite" line. It is
   also the single biggest cell in the table.
6. **Good shooters over a contest:** a 10 or 11 with 1 off still scores 45 to 50 in 100. 17 shots.

## Part 5: speed

**A speed fault, reported first as the rules ask.** My first build was too slow at Rookie and Starter.

- **The cause:** when the search values a declared shot it plays the reaction out. With no Contest move on a jump
  shot, both of the reaction's actions can be movements, and I had it play a second movement ending next to the
  shooter.
- **The fix:** that second movement is the All-Star's alone (`closeout_twice` in its profile). Rookie and Starter
  play the reaction as before: one movement, then a Steal, the block or the end.
- **What it costs them:** their look-ahead does not see a defender Quick Step in and then Move to be set. The
  defence still does it when it is the one moving.

The time to finish 1 pair on 9 decisions in 10, in seconds, two rounds, 18l's code timed in turn with this step's.

| Level | Target | 18l's code | First build | | 18l's code, later | After the fix |
|---|---|---|---|---|---|---|
| Rookie | 0.3 | 0.27, 0.25 | **0.45, 0.39** | | 0.36, 0.39 | 0.36, 0.32 |
| Starter | 1.0 | 0.98, 0.95 | **1.12, 1.18** | | 1.18, 1.40 | 1.01, 1.09 |
| All-Star | 2.5 | 2.00, 1.89 | 1.87, 2.03 | | 2.59, 2.92 | 2.43, 2.59 |

- **After the fix this step is no slower than 18l's code at any level,** timed side by side. Every level fits, judged
  as D-161 says.
- **The second pair of rounds ran on a busier machine** (play-outs were running beside them), so read them against
  18l's code in the same rounds, not against the targets.
- **How much faster without the jump-shot Contest move?** By the middle decision, in the second pair of rounds:
  Rookie 0.23 against 0.27, Starter 0.77 against 0.91, All-Star 1.80 against 1.96. About a seventh faster at Rookie
  and Starter, a twelfth at the All-Star, which also spends time on its second closeout movement.

## What it proves

- **The two engines agree.** With the rule on: 150 positions and 8 searches; 200 shot reactions; with `rules.zone`
  on as well, 100 positions and 4 searches; 60 positions with a broken zone and 2 searches; 40 positions and 6
  searches with the three search switches on; with the rule off, 60 positions and 3 searches; and 6 searches the way
  Starter and Rookie settle a shot. No differences.
- **The cards:** every contest value matches the table, by a test. No other rating changed.
- **Tests:** `tests/test_rules_current.py` passes. The 28 named test files: 468 passed and 1 failed, the timing test
  (2.3 seconds on one decision against a limit of 1.7), as since 18f. `tests/test_static.py`, run on its own: 11
  passed. 13 tests are marked as known failures, as before, and none of them is new.
- **One recorded value moved after the maps were redone, and I re-recorded it.** A trainer board in
  `tests/test_step3m.py` asks what an off-ball move is worth over a phase because it uses up a defender's actions.
  It was worth +2.5 before D-184 and +0.3 on my first maps; it is worth 0.6 less than nothing now. The move still
  uses up X2's Move and Quick Step. The test holds the new value, with the reason.
- **What it does not prove:**
  - How a person plays under the rule.
  - The five positions of the set that were not replayed.
  - Starter and Rookie against FIBA: the tables are the All-Star's.

## Compute

| | Core-hours |
|---|---|
| Self-play to fit the maps (All-Star 200, Starter 90 twice, Rookie 120 twice) | 2.8 |
| The test run (All-Star, 200 possessions) | 1.7 |
| The set: replays that count | 1.5 |
| The set: a first replay stopped as too costly | 0.6 |
| Speed, four rounds | 0.3 |
| Agreement checks, tests and exam runs, on one core | 1.7 |
| **Total** | **8.6** |

- **The estimate was 7.0 and the hard stop 10.** The 1.6 over the estimate is the stopped replay (0.6), the second
  Starter and Rookie runs after the speed fix (0.3) and the tests, which I had not counted (0.9 of the 1.7).
- The line by line tally is at the foot of `docs/runs/step18n/PREDICTIONS.md`.

## Noticed, not touched

- **The reaction got longer in effect.** A defender two movements away can now reach a jump shooter and contest.
  That is case 1 in Part 2. It is the main reason contested shots rose.
- **No mid-range shot or long two was taken in 200 possessions.** They are never the best shot on these cards.
- **No dunk was taken either.** A dunk's contest is back at 4 to 14, above the layup's 5 to 12, and the dunk's
  rating is lower.
- **Every turnover is still a reach.** No pass was intercepted and no violation called.
- **Steals tried and fouled did not move:** 47 and 20 in 100 possessions.
- **The timing test still fails** as it has since 18f. Not loosened.
- **An off-ball move that uses up a defender's actions is worth less under D-191.** The contest it used to take
  away is automatic now. One trainer board changed sign because of it ("What it proves", tests). The trainer's teaching on
  that point may need a look once the rules settle.
- **Predictions.** Scoring: wrong, I expected 1.10 to 1.25 and got 1.28. Contested threes going to the good
  shooters: right. The block on fewer than 1 inside shot in 4 and few fouls: right, more than I expected. Speed:
  wrong at first, see Part 5. The set: all 14 played were level, above my 13 to 16 of 19, but 5 went unplayed.

## For Shaun to decide (three)

1. **Keep D-192's contest ratings. And test one thing: rushed takes 1 off a jump-shot contest, not 2.**
   *Recommend: keep them, and test that next.* Why: the ratings do what you wanted. But 18 of the 37 contested
   threes met a rushed defender, and those scored like open threes (1.33 a shot against 1.35). On a scale of 1 to
   4, taking 2 off leaves the floor of 1 almost every time. The table D-190 asks for:

   | Card contest | Set | Rushed: now, proposed | Behind | Behind and rushed: now, proposed |
   |---|---|---|---|---|
   | 4 | 4 | 2, **3** | 1 | 1, 1 |
   | 3 | 3 | 1, **2** | 1 | 1, 1 |
   | 2 | 2 | 1, 1 | 1 | 1, 1 |
   | 1 | 1 | 1, 1 | 1 | 1, 1 |

   It touches one modifier: D-185's 2 off, for mid-range, long two and three contests only. Shots, inside contests
   and every other roll keep their 2. D-193's floor is unchanged.
2. **Is the block meant to be a live choice?** *Recommend: yes, and test reading the block's foul roll as the
   rating in 40, not in 20.* Why: today it is never right. Take a layup of 18 against a contest of 9 and a Contest
   foul rating of 10:

   | The defender is | Hand up: the shot scores | The block: no foul / fouled | Foul chance now | The block scores on average | The block pays under |
   |---|---|---|---|---|---|
   | In front, arrow off | 24 | 18 / 41 | 50 in 100 | 29.5 | 26 in 100 |
   | Beside | 24 | 18 / 41 | 75 in 100 | 35.3 | 26 in 100 |
   | Behind | 30 | 24 / 45 | 75 in 100 | 39.8 | 29 in 100 |

   With the roll read in 40 the chances become 25, 44 and 44 in 100: the block from in front becomes about even,
   and from the side or behind stays a bad bet unless the defender's foul rating is low. That would bring fouls
   back to rim shots, where FIBA has 20 to 30 in 100 and the game has none. It touches the block's foul roll only:
   not the Steal's foul roll, not the ratings on the cards.
3. **The sense-check set.** *Recommend: leave the last five positions until the next rule test is settled, then
   replay all 19 once.* Why: a full replay costs about 5 core-hours now, and decisions 1 and 2 would each make it
   out of date again.

**Not a decision, but yours to know:** the open-shot ratings you expected to revisit. The evidence is in Part 4's
last list. The clearest is the inside shot with a trailing defender.

## Model for the next step

Claude Fable 5.2, effort high, if decisions 1 and 2 go ahead: two small rule changes in both engines, then the
refit and the same test. Budget about 12 core-hours: a possession now costs half as much again to play out.
