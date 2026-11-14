# Step 18l report: off balance, the refit, and the game beside FIBA

## In five lines

1. **The off-balance rule is built and on in the app.** Rushed or locked, a player is 2 worse on every roll he
   makes, fouls aside. One marker, one help line, both engines agree.
2. **On the new cards the All-Star still scores 1.36 points a possession (1.30 to 1.42). FIBA is about 1.0.** The
   lower jump shots moved the offence to the rim: half its shots are at the rim now, and two shots in three go up with
   no contest.
3. **Reaching is still about three times FIBA's, and the rule did not lower it.** 48 Steals tried and 21 fouled in
   100 possessions; FIBA is 5 to 8 fouls. Two free throws are still worth about what the possession was, so a foul
   has no price.
4. **The rule does what it says on each roll, and the offence uses it:** it drives at an off-balance defender more
   often and wins more. After a missed Steal it seldom needs to drive at him: he is locked, so it goes past.
5. **One part is not done, and it is my mistake.** My first refit and FIBA run played on the old cards. I caught it
   late, redid the refit and the FIBA table on the new cards, and had no compute left to replay the sense-check
   set. Compute: 11.8 core-hours of the 12 allowed.

## The mistake, plainly

- **What happened.** The self-play pool and the sense-check set each keep their own copy of every card, saved when
  they were made. Both were made before the card update. I copied the pool file from the last step's folder (it is
  not kept in the repository) when I should have rebuilt it.
- **What it spoiled.** The first refit, the first FIBA run, the run with the rule off, and the replay of the set:
  6.9 core-hours, all on the cards before D-184. The rule on against off is still worth having from those. The
  rest is not.
- **How I found it.** The set's re-recorded answers came back with the same shot values as step 18k's, to the
  decimal. I opened a position and found O2's three still at 13.
- **What I did.** Rebuilt the pool on today's cards (`python3 tools/step_18.py pools`). Reran self-play at all
  three levels on it. Refitted the maps and the foul numbers from those runs. Took the FIBA table from the new
  All-Star run.
- **What that leaves short.**
  - **The FIBA table was measured before the new maps went in,** not after. The All-Star in that run read the
    board through the map fitted on old-card play. The final default has not been played.
  - **The All-Star's map rests on 200 possessions,** not the 400 I had settled on.
  - **The sense-check set is not re-recorded on the new cards.** Nor are the exam answers that hang on it.
  - **The rule on against the rule off was only measured on the old cards.**
- **So it can't happen again.** `tools/step_18l.py` now refuses a pool that holds any card that is not today's.
  The set's old-card replay is kept under a name that says so, and the set's README says what it carries.

## Part 0: the rulings, built

- **Merged:** step 18k (pull request 72), then the card update (pull request 73).
- **`DECISIONS.md`:** D-185 (off balance, and the reversal of 18d's "no drive rule" line), D-186 (the card
  correction), D-187 (the rulings on 18k and the card update), D-188 (the shooter test at junior age, below).
- **D-186, the card correction.** Threes, mid-range and long twos re-derived for the 75 table cards from the cards
  before D-184, then your 20 single changes.
  - Band averages: threes 51 / 43 / 33%, mid-range 56 / 48 / 38%, long twos 52 / 43 / 35%.
  - No tier is out of order. The Sharpshooter reads 55 / 50 / 45% from three.
- **The names:** Slashing Wing and Switch Centre.
- **`tools/levels_generator.py`** runs from its real paths.

**Shooters.** The threshold stays a three of 9.

| | Before D-184 | D-184 as first merged | Now (D-186) |
|---|---|---|---|
| Table cards that are shooters | 30 | 43 | 24 |
| Shooters in a random pro deal | 2.0 | 2.7 | 1.5 |
| In a semi-pro deal | 1.75 | 2.6 | 1.2 |
| In an amateur deal | 1.3 | 2.2 | 0.6 |
| Random pro deals that are coherent, in 100 | 32 | 44 | 22 |

- Senior coherent deals still work at every standard, and hold 2 shooters or a little more.
- **The count went under where it started.** Your tier changes took six of the old shooters under 9.

**Junior deals broke, and I changed how the threshold is carried (D-188).**

- A job's threshold is carried to a younger age as "the cut that as many cards reach". On the new cards no junior
  cut gives 24 shooters: a junior three of 7 gives 15, and 6 gives 37.
- The rule took 15. **Coherent junior semi-pro deals stopped existing,** and coherent junior pro deals fell from 37
  in 100 to 7.
- I now take the nearest count in proportion, which picks 37 (it was 36 before the card update). Junior deals are
  back where they were. No other job's cut changes at any age.

**Tests re-recorded, each with the reason "D-184 cards".** The seven you named, and eight more that held old-card
values. Four of them needed more than a new number, so you should know:

- **A soft contest next to a jump shooter is now nothing.** A three's contest is 2 or 3, and a soft contest is the
  rating less 3. The soft-contest tests moved to a layup, where it still counts.
- **No real pair of cards gives a shot below nothing any more.** The two "floors at zero" tests now use a rushed
  post shot and a test copy of a card.
- **On exam board 16 the off-ball move's worth over the phase fell from +2.5 to +0.13.** Taking a contester away
  is worth less when his contest of a three is 2. The test asked for more than 1.0; it now asks for more than 0.
- **A late contest on a three** (2 less 3) floors at nothing; the test says so.

## Part 1: the rule, built

- **One state.** You are rushed if your last movement this phase was a Quick Step or a Sprint, or you are locked.
  A Move resets it; a locked player can't Move.
- **Every roll, both sides:** Dribble against Agility, Dribble against Steal, Pass against Intercept, Screen
  against Challenge. Shots and contests as before, and now for a locked player too. Never foul ratings.
- **One marker:** RUSHED shows on a locked player as well.
- **The sentence,** in the help and the rules text: "Rushed: after a Quick Step or Sprint, or while locked, every
  roll you make is 2 worse (not fouls) until you Move."
- **The explanations:** "X2 reached and missed, so he's off balance: every roll he makes is 2 worse until the phase
  ends. O1's drive at him is easier." The roll previews show the lower number and why.
- **The switch:** `rules.off_balance`, on in the app, off at the table. `?offbalance=0` turns it off.

**Cases the three lines don't settle. I read each the way closest to "off balance". Marked for you.**

1. **A defender who jumps into the passing lane on a Quick Step or Sprint rolls that Intercept rushed.** One who
   Moves onto it rolls it set.
2. **A ball handler who lost a Dribble is locked, so his shots and passes are rushed** for the rest of the phase.
3. **A defender held by a screen is locked, so he is rushed too.** His next Challenge is 2 lower.
4. **A locked defender next to the shooter gives a soft contest 2 lower.**
5. **The computer's reading of a pass takes each defender as he stands now,** not as he would stand after stepping
   into the lane.

**Two faults found on the way, both fixed.**

- **A locked defender who lost a second Challenge got no line in the app.** He does now.
- **The Python engine kept pass chances in a store that did not ask who was rushed.** Under the new rule it could
  hand back a chance worked out before a player lost his balance. The two engines drifted apart by up to 0.05 of a
  point in two checks. The games and every measurement here run on the JavaScript engine, which was right.

## Part 2: the refit, on the new cards

**The maps.** Each level's own self-play on today's cards with the rule on, as in 18h.

| | Possessions | Positions | Lines of its own | Lines borrowed |
|---|---|---|---|---|
| All-Star | 200 | 3,329 | phases 1 to 3, both sides; phase 4, offence | the rest |
| Starter | 90 | 959 | phases 1 and 2 | the rest |
| Rookie | 120 | 1,321 | phases 1 and 2 | the rest |

- **Every line fitted on the new cards slopes the right way:** a better reading is worth more.
- **Borrowed lines** come from the three runs together (410 possessions) through phase 3 and phase 4 for the
  offence. Later phases had too few positions and keep the line from before D-184, marked as such in the file.
- **Why the All-Star needs more.** On the old-card runs its phase 3 lines sloped the wrong way at 200 possessions
  and the right way at 400. On the new cards 200 was enough for the slope. I would still add a second 200.

**What a possession scores, by level, on the new cards:**

| Level | Points a possession | As real points |
|---|---|---|
| Rookie | 20.3 (18.5 to 22.1) | 1.02 |
| Starter | 23.5 (21.7 to 25.4) | 1.18 |
| All-Star | 27.2 (25.9 to 28.5) | 1.36 |

**The foul-price numbers,** from the All-Star run: 0.21 fouls a possession (0.15 to 0.28) and 27.2 a possession
(25.9 to 28.5). They were 0.25 and 26.9.

**Not done on the new cards:** the sense-check set's answers, the exam answers, and the computer's score on the
set.

- **For the record, the set on its old cards under the new rule:** the computer is best or level on 16 of 19.
  Your closeout order is best by play again, by 17.8 points (10.1 to 25.5) over the computer's choice.
- **The exam at the All-Star, new maps in:** positions 1 and 14 now pass. Positions 6 and 16 now fail, and are
  listed as open.
  - Position 6: O4's open corner three is worth 27, about what a possession scores now. The computer plays on.
  - Position 16: using up the one defender who can answer is worth less, as above.

## Part 3: beside FIBA

All-Star self-play, 200 possessions, the new cards, the rule on. Nothing was tuned to these.

| Measure | Real FIBA | The game |
|---|---|---|
| Points a possession | 0.95 to 1.0 | **1.36** (1.30 to 1.42) |
| Turnovers a possession | 0.15 (live ball 0.085) | 0.08 (0.04 to 0.12), all live ball |
| Steals a possession | 0.09; 0.05 from a reach | 0.08 (0.04 to 0.12), all from a reach |
| Steals tried a possession | not tracked | 0.48 (0.38 to 0.58) |
| Fouls on a Steal a possession | 0.05 to 0.08 | **0.21** (0.15 to 0.27) |
| Shooting fouls on threes | 1 in 100 | 0 of 89 (0 to 4 in 100) |
| Shooting fouls at the rim | 20 to 30 in 100 | **1 of 89** (0 to 6 in 100) |
| Free-throw trips in 100 possessions | 10 | 0.5 (0 to 1.5) |
| Blocks | 6 in 100 twos, 1 in 100 threes | the game has none; no shot was taken to nothing by a contest |

**How close.** Steals won sit on FIBA's figure. Everything else is off, and in three ways.

- **Scoring is a third too high.** Rookie plays at FIBA's level; the All-Star does not.
- **Fouls are in the wrong place.** Four times FIBA's fouls on the reach, and almost none on the shot.
- **Every turnover is a reach.** No pass was intercepted and no violation was called in 200 possessions.

**Shots.** 184 in 200 possessions.

| | In 100 shots |
|---|---|
| Threes | 48 |
| At the rim | 48 |
| Other twos | 3 |
| In phase 1, 2, 3, 4, 5 | 39, 37, 16, 6, 3 |
| No contest | 67 (60 to 74) |
| Soft contest | 9 (6 to 14) |
| Hard contest | 23 (18 to 30) |
| Threes contested | 25 (17 to 35) |
| Rim shots a contest took something off | 37 (33 of 89) |
| Threes a contest took something off | 11 (10 of 89) |
| Rushed shots | 10 (7 to 16) |

- **The offence moved to the rim.** On the old cards 28 shots in 100 were at the rim. Now 48 are.
- **That is the cards working as you meant:** an open layup is worth clearly more than an open three. But the
  defence does not take it away.
- **A contest takes little off.** Where one counted it took 2.2 rating points on average, at the rim as well: under
  a contest the offence dunks, and a dunk's contest is small on the new cards. 15 of the 60 contests took nothing
  off at all (rushed, or a hand up next to a jump shooter).
- **Every hard contest came from in front** with the arrow on the shooter, which rolls no foul. That is why
  shooting fouls are near nothing.

**Drives.** 40 Dribbles at a defender.

| | Drives | Won | The chance by the rules |
|---|---|---|---|
| At a set defender | 33 | 19 | 50 in 100 |
| At a rushed or locked defender | 7 | 7 | 59 in 100 |
| By a set ball handler | 29 | 20 | 56 in 100 |
| By a rushed ball handler | 11 | 6 | 40 in 100 |
| By a ball handler who had Sprinted | 6 | 2 | 34 in 100 |

The counts are small. The chance by the rules is the fair comparison: it is each roll's own chance, averaged.

**The off-balance tests.**

- **After a missed Steal, does the offence attack that defender? Mostly it goes past him.** 77 Steals missed or
  fouled with play going on. The offence acted again that phase after 75 of them.
  - Its next action: a movement 50 times, a shot 19, a pass 3, other 3. Never a Dribble at him.
  - It shot later that phase 46 times.
  - It drove at him later that phase 6 times and won all 6.
  - **Why so few drives:** he is locked and can't follow. Beating him on the dribble gains nothing the offence
    doesn't already have.
- **Is a Sprint closeout driven past more often than a set one? There were none to test.** No defender who had
  Sprinted was driven at. The 7 drives at off-balance defenders were at locked ones (5) and Quick Steppers (2).
- **Does a ball handler who Sprints into a Dribble lose more? Yes.** 2 won of 6, a chance of 34 in 100 by the
  rules against 56 for a set ball handler. And he is easier to strip: a Steal on a ball handler who had Sprinted
  wins the ball 24 times in 100 by the rules, against 20 on a set one.

**What the rule changed, measured on the old cards** (the comparison is fair: the same cards on both sides).

| In 100 possessions | Rule on (200) | Rule off (160) |
|---|---|---|
| Points a possession | 26.5 (24.9 to 28.1) | 26.7 (25.0 to 28.3) |
| Steals tried | 68 (56 to 79) | 53 (41 to 64) |
| Fouls on a Steal | 28 (20 to 35) | 19 (12 to 26) |
| Turnovers | 15 (10 to 20) | 12 (7 to 17) |
| Shots at the rim, in 100 shots | 28 | 19 |
| Drives at a rushed or locked defender | 5.5 | 1.9 |

- **Scoring did not move.**
- **Reaching went up, not down,** though the two ranges overlap. A rushed ball handler is a better target, and the
  defence takes it.
- **The offence picks on off-balance defenders about three times as often.**

**Game EB3F5B, the pass to O4 in the corner.** Not played out on the new cards. Two things are known.

- **On the set's old cards, with the rule on, X4 Moving to C4 and facing him is still best by play.** He contests
  set. A Quick Step in would contest 2 lower. The computer there moved X5 and Quick Stepped X4 in: 3.0 behind.
- **On today's cards the computer moves X2 to B7 and leaves X4 where he is.** O4's corner three is a 9 now and reads
  27, about what the possession is worth anyway. Whether that is right needs the replay.
- The same search on all 19 positions: 12 of the computer's choices are different on today's cards
  (`docs/runs/step18l/set_choices_on_new_cards.json`). On board 8 it now finds the backdoor cut and the pass.

## Part 4: speed

The time to finish 1 pair on 9 decisions in 10, in seconds, two rounds, 18k's code timed in turn with this step's.

| Level | Target | 18k's code | This step | This step, the rule off |
|---|---|---|---|---|
| Rookie | 0.3 | 0.35, 0.33 | 0.28, 0.28 | 0.28, 0.28 |
| Starter | 1.0 | 1.17, 1.08 | 1.06, 0.86 | 1.01, 0.96 |
| All-Star | 2.5 | 2.20, 2.27 | 2.26, 1.92 | 2.10, 1.98 |

- **Every level fits, judged as D-161 says.** The machine ran about a quarter slower than when 18k was reported:
  18k's own code took 1.17 and 1.08 at Starter in this hour, against 0.91 and 0.78 then. Scaled by that, this step
  is about 0.22 at Rookie, 0.72 at Starter and 1.74 at the All-Star.
- **Raw, one Starter round is over its line** (1.06), with 18k's code at 1.17 beside it.
- **This step is no slower than 18k's code at any level.** The rule costs nothing that shows.

## What changed

- **`playmaker_engine` and `engine.js`:** `rules.off_balance`; one function for the rating a player rolls with;
  rushed includes locked when the rule is on.
- **The app:** the marker on a locked player, the rule sentence, the roll previews, the log lines.
- **The cards:** D-186. `levels_data.py`, the team sheet and the site regenerated.
- **`rosters.py`:** the shooter test at a younger age, in proportion (D-188).
- **`learned_weights.json`:** the maps per level and the shared map. **`ai_profiles.json`:** the two foul numbers.
- **`DECISIONS.md`** D-185 to D-188; the rules register and `RULES_CURRENT.md`.
- **Tools:** `tools/step_18l.py`; `tools/playout.js` keeps each Dribble's and Steal's own chance and how both
  players stood; `tools/js_equivalence.py --off-balance`.
- **Tests:** `tests/test_off_balance_18l.py` (7 tests); 15 older tests re-recorded for the cards.

## What it proves

- **The two engines agree,** after the store fix. With the rule on: 200 positions and 12 searches; with
  `rules.zone` on as well, 200 positions and 8 searches; 100 positions with a broken zone and 4 searches; 60
  positions and 12 searches with the three search switches on; 200 shot reactions. With the rule off: 100
  positions and 6 searches. No differences.
- **Tests,** after the last change: the 24 named files and four more (`test_off_balance_18l.py`, `test_scouting.py`,
  `test_teams.py`, `test_static.py`). 469 passed, 11 expected failures, 1 expected failure that now passes, 2
  failed. `tests/test_rules_current.py` passes with `RULES_CURRENT.md` regenerated.
  - **Failed, as since 18f:** the timing test. Not loosened.
  - **Failed only in company:** the check of the browser bundle. Run in one go with the exam tests it counts two
    research files they load. On its own, as in every step before, `tests/test_static.py` passes: 11 of 11.
  - **15 tests re-recorded for the cards,** each with its reason in the test.
- **What it does not prove:**
  - How the All-Star plays with the new maps in. The FIBA table was measured just before them.
  - How a person plays under the rule.

## Compute

Estimate 9.5 core-hours. Limit 12. Used 11.8. Over the estimate because of the mistake above.

| Part | Estimate | Used | |
|---|---|---|---|
| Self-play for the refit | 1.85 | 4.32 | 2.64 on the old cards, then 1.68 on the new |
| The sense-check set replayed | 2.6 | 2.06 | all on the old cards; stopped when they were found |
| All-Star self-play for the FIBA table | 1.2 | 1.26 | on the old cards; the new-card table comes from the refit's own run |
| The same with the rule off | 1.2 | 0.94 | on the old cards |
| Speed | 0.3 | 0.21 | |
| Agreement checks between the engines | 0.6 | 1.59 | run twice, and 0.56 finding the store fault |
| Tests | 1.2 | 1.29 | |
| Searches and small checks | 0.55 | 0.07 | |

- **6.9 of the 11.8 went on the old cards.**
- Nothing was started that could not finish inside 12. That is why the set was not replayed.

## Noticed, not touched

- **The scout report reads differently on the new bands.** Five Out no longer reads "shooters to space the floor":
  only 6 cards are above-average three-point shooters now. "Gives up open threes" can no longer fire: 2 cards are
  below average at contesting threes. The lines were cut for the old bands.
- **The phase table is from the old cards.** The maps sit on top of it and take up the difference.
- **The timing test still fails** as it has since 18f. Not loosened.
- **Predictions.** Scoring: wrong. I expected 1.05 to 1.2 points a possession; it did not fall at all. Steals
  tried: 48, inside my 35 to 55, but not for my reason: the rule alone raised them. A drive at the defender straight
  after his missed Steal: wrong, it never happened. Speed: right.

## For Shaun to decide (three)

1. **Finish what this step left short.** *Recommend: a short step next, about 5 core-hours.* A second 200
   All-Star possessions for its map; the FIBA table again with the new maps in; the rule on against off on the new
   cards; the sense-check set rebuilt on today's cards and replayed; the exam answers that hang on it. Why: every
   later step reads these maps and this set.
2. **Where to aim after that: the defence's cover, not another rule.** *Recommend: yes.* Why: one fact sits under
   both gaps. Two shots in three are uncontested and half are layups, so a possession is worth 1.36. Two free
   throws are worth about 1.45. So a foul costs the defence a tenth of a point and the reach pays every time. At
   FIBA's 1.0 the same foul would cost half a point and the reach would stop paying. 18k found the defence's search
   stops one turn short of seeing its own closeout land. That is the lever.
3. **The readings I took.** *Recommend: accept all of them.* The five off-balance cases in Part 1; the junior
   shooter test (D-188); the four tests whose meaning moved with the cards.
   - One you may want to rule on its own: **a hand up next to a jump shooter now takes nothing off.** If that is
     not what you want, the soft contest needs a floor of 1 on jump shots.

## Model for the next step

Claude Opus 5.5, effort high, for the short measuring step: it is runs and bookkeeping. Claude Fable 5.2, effort
high, for the defence's cover after it.
