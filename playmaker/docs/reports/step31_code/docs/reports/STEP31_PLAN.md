# Step 31, Part A: the plan for rebuilding how both computers think

**Status: plan only. No engine code has changed.** Branch `step-31`, from main (step 30 merged, PRs 106 and 107). This waits for Shaun's go-ahead before Part B.

The design is `docs/reference/GRAVITY_AND_SPACING_DESIGN.md` (copied in). The 20 November possession is `docs/reference/step31/playtest_20nov_possession1.html`.

## What I need from Shaun before building (the short list)

The full list is in section 9. These five change what gets built:

1. **The ten cards of the 20 November game.** The record has every square and every action, but not the cards (it was a dealt game, and the deal code isn't in the file). Check B4 needs them.
2. **Three turns or four.** The design says the reading goes up to three turns ahead. The build reads four today, by D-268 (19 Nov). Which stands?
3. **The lowest a shot can be worth.** The design says never below 1. The rules say a shot scores 0 at worst, and it is the contest that is never below 1. I will follow the rules unless you say otherwise.
4. **The segments, square by square** (my proposal is in section 9), and which side column I belongs to in the long two.
5. **The exam boards** in section 6.

## Step 30's four carry-overs

### 1. The map stops a block at −5

Still true on main. It is priced in three places, all the same way: the map (`decide.Read._block_value`, `engine.js blockValue`), the scout's shot review (`plan.case_value`) and the reply's ordering (`scoring.block_option`). Stage 1 closes it: the possession's value is one function, and a block inside it is "−5, the push, the reset, then the value of the new phase", the same sum the search uses. The kept-price problem from step 30 goes away because the new value is computed for the whole board, not kept per look.

### 2. Why every offence setup's best route used a pass fake

I read the defence's reply on step 30's board 3 (High-Low against Run and Gun; the Playmaker SG with the ball on I11 fakes a pass to the All-Rounder PF on A3; X1, the Attacking PG, on A6).

| X1's reply | Worth to the offence if the pass is real | If it is a fake |
|---|---|---|
| Move to D6 and go for the Intercept | 19.3 | 27 |
| Hold the lane by position (ten or more different replies; none goes for the ball) | 21 | 21 |
| Quick Step to B6, then wait | 22 | 18 |

- **Holding the lane was among its options**, and it is worth 21 whichever the offence does. Nothing the offence chooses can make it worse.
- The Intercept wins 1.7 if the pass is real and loses 6 if it is a fake.
- The mix works out the fake rate that makes the two level: the offence fakes 22 times in 100, and then the Intercept is also worth 21.
- **The fault:** with the two replies level, the mix has to choose one, and its tie rule took the first on its list, which was the Intercept, with all its weight. That is wrong by the mix's own sums. A defence that always goes for the ball is beaten by an offence that always fakes (27). A defence that holds can't be beaten (21). The right reply is to hold.
- Then the setup's read-ahead read the fake against "X1 goes for the Intercept", saw him locked, and scored the route 27. So every setup found a pass fake.
- **So this is a fault in step 29's mix, not basketball.** It is in both engines (`search.mix_game`, `engine.js mixGame`). With it fixed, this board's fake reads 21, the same as not faking, and the route disappears. It gets fixed in Stage 1, and checks A12 and A13 guard it.
- This matches the design: holding by position risks nothing, so the gamble should appear only when winning saves more than a miss or a fake gives away.

### 3. The computer never blocks: the values, for your ruling

Step 29's block board: Five Out against Iron Wall. O1 (Pass-First PG, layup 17) lays it up from H4 off a Sprint. X5 (Rim Protector Centre: contest 11, Block 9) is square in front on H3.

| | Worth to the offence |
|---|---|
| The layup against X5's Contest: (17 − 2 for the Sprint − 11) × 2 | **8** |
| The new phase after a block, only the blocker reset (the rule as built), after the −5 | **29** |
| The same new phase with the blocker left where he is | 28 |
| The same new phase with **all five defenders set afresh** by their own setup, after the −5 | **25** |
| Going for the block as built: 45 in 100 it works (29), 55 in 100 the layup still goes up (8) | **17** |
| Going for the block if the whole defence reset: 0.45 × 25 + 0.55 × 8 | **16** |

What this shows:

- **Resetting more defenders would not make the computer block here.** Even with the whole defence set afresh, the new phase reads 25 after the −5. The block pays only if the new phase is worth less than the shot it stops, which here is 8.
- **The shot on this board is already a bad shot.** A layup into the Rim Protector's 11 is worth 8. The defence is right to let him take it. A block should pay against a good shot: stop a shot worth 22 and the block pays whenever the new phase is under 22.
- **The 25 to 29 is the old stand-in talking.** Today "playing on" is read as the best look the offence might get next phase (the top of the list), not what the possession is worth. The design replaces exactly that. I expect the new phase's value to come down a long way under Stage 1, and the block to start appearing against good shots without any rule change.
- **My suggestion:** rule on the reset after Stage 1's numbers are in, and let me add a second block board with a good shot (a 19 layup into a weak contest with a good Block). No rule changes in this step either way.

### 4. Times and tests

- **Today:** setups 87 to 202 seconds, one turn 86 seconds.
- **What the design does to them.** The value itself costs about what today's map reading costs, plus the shot bar for the phases left. Two things add real time:
  - the defence's search now starts from five base positions and improves all five by the value, square and arrows together;
  - every placement the offence weighs is ranked against that full answer, read ahead.
- **My estimate, before any tuning:** a turn stays in the range of 1 to 3 minutes; a setup goes to something like 4 to 10 minutes. I can't know better until Stage 3 runs. I will time each stage as it lands and report it, and trade nothing in the design for speed.
- **Tests.** In Python a fresh board takes about 1 second to read and about 10 seconds once a search is involved. So:
  - the exam runs in JavaScript: one reading a check, seconds each;
  - both engines are compared on the value, the weight map and its centre for every exam board (about a second each in Python);
  - whole decisions are compared in both engines only on small boards built for it;
  - step 29's four two-engine tests (41 minutes) and the separate-thinking test as written (14 minutes) can't run inside the limit. I will rebuild them on smaller boards and say so. Nothing gets run past the 10 minutes.

## 1. The design in my own words

**One number.** Both computers read one number: what this possession is worth to the offence from here. The offence acts to raise it. The defence acts to lower it. It is measured on the game's own scale: shot rating less the contest it faces, times the points. A turnover is −5 and a foul is +5 on the same scale.

**How the number is made.** List every look the offence can get, best first. Each look has a value (what the shot is worth against the defence it faces) and a chance (the attacker and the ball both get there before the defence closes it). The offence only takes one shot, so it takes the best look that opens: the best look at its chance, then the second best at the chance the first didn't open, and so on. If nothing opens it plays on, worth the shot bar for the phases left. Looks that depend on the same thing (the same screen, the same pass, the same Dribble) are one route, not separate chances. Turnovers, violations and fouls are added at their chance. It is read ahead up to three turns, each side answering by its own model. This is the old list, kept in its order and now priced.

**The weight map** is the defence's picture of the floor: where a defender's presence saves the most points right now. Three layers:
1. **What a contest saves.** For each attacker and zone: the open shot's worth less its worth against the best legal answer (a set contest, a block with its foul risk, a rushed closeout, the fake). Defenders are drawn to where they save the most, not to where shots are worth the most.
2. **Who can get there.** The court is cut into segments; a segment no attacker can reach this phase is left out.
3. **Can the ball get there** before the defence recovers. A valuable square the ball can't reach pulls little.

**The centre of gravity** is where the map balances. It is a summary: when the weight has two lumps (a shooter at the arc, a big at the rim) the middle is empty, and defenders go to the weight itself. Weight a teammate already covers pulls the others less, by as much as his stance takes off.

**Goal-side comes from the weight.** Each defender's base position is on the line between his man and the heaviest weight he can reach in time that no teammate covers. Normally that weight is at the rim, so he stands between his man and the hoop. How far along the line he stands is the link rule: stay close to a real danger, drop toward the weight when his man is little danger now. If the weight moves (a three is all that matters), the right side of his man moves with it. The defence's search starts from this shape and never from nowhere.

**How the five stances are chosen.** A stance is a square and a pair of arrows, chosen together. All five are chosen together as the set that leaves the offence the least: start on the base positions, then try moving and turning one defender at a time, keeping any change that lowers the number, until none does. Switching, trapping, denying, fronting and sagging are just stances that search can reach. A trap is judged with the trapper gone from where he was. The link rule describes the answer and checks it; it isn't a separate mechanism.

**The arrows** wall a drive (the wedge between them), set the contest and the block's foul risk, and aim at a passing lane. They go wherever the whole stance saves the most. Three things should come out of that one sum: close the lane with the weakest cover behind it, send the ball where it can do least (usually the sideline), and weigh two smaller passes against one bigger one.

**Advantages are gaps.** Speed, a Dribble edge and passing have no value of their own. Each is worth the points it leads to on this board, times the chance of getting there first. The defence contains an edge with distance, direction or help, each judged by the points it takes off. A pass is worth more than the receiver's look: it also counts the rushed closeout it forces, the defender who went for the ball and missed, and the defender sold on a fake.

**The offence** reads the same number from the other end. It wants points the defence can't afford to cover: place and move so the link rule fails for as many defenders as possible, then attack what they had to leave. Six things feed it: what each attacker can score, how firmly that holds his defender, how far that defender must travel to help, the time the action needs, whether the ball can get to the receivers, and the room around the ball. Spread pins defenders further away; being close makes things happen sooner; the balance is as spread as the plan allows inside the phases left. With little time or blocked lanes, run several actions at once; with little room, run fewer. Setup follows an order: scout, the ball's start, each attacker's best segments, tie-breaks by secondary skills, the plan's conditions, then adjust. In play: shoot when the best shot now beats playing on; otherwise take the two actions that raise the number most; fakes stay a mix.

**Where the design is unclear or pulls two ways** (each is a question in section 9):
- "Up to three turns" against D-268's four.
- "Never below 1" against the rules' 0.
- Layer 1's "the best answer a defender can give": which defender's contest?
- The segments are named but not drawn square by square.
- "The offence takes the first look that opens" treats trying a route as free. In the game each try costs actions, and a turn has two.
- "Try one defender at a time" can miss a change that needs two to move together (a switch, a trap). The design also says switches and traps must be reachable.

## 2. The ledger, row by row

"Today" names where the point lives now. Python files are in `playmaker_engine/`; "JS" is `playmaker_web/static/engine.js`. The setup's planning code (`plan.py`) has no JavaScript copy: it runs in Python and reads the map through the JavaScript engine.

| # | Agreed point | Today | What I will change | Check |
|---|---|---|---|---|
| 1 | Each player's zones of average or better shooting demand a defender | The card bands (`scouting.band`, from `data.RANGES`) are display only. The scout has a floor (`plan.Scout.floor`) but no "zones that demand a defender" | Setup step 1 lists, for each attacker, the segments where his shot is average or better by the card bands. They feed the weight map's layer 1 and the placement | O3, O4 |
| 2 | Sub-zones: green 1, mid-range 3, long two 4, beyond the arc 5 | Not in the code. Only the four zones (`board.zone`, JS `ZONE`) | A segment table for every square, both engines (`board.segment`, JS `SEG`), from the squares Shaun approves | O3 |
| 3 | Players don't share a section while keeping their danger | Not in the code. Step 27 took candidate squares out (D-240); "space and occupy" is only listed in `conditions.py` | No rule. Two attackers in one segment hold one defender, so the value is lower; the placement search sees that. The report names any shared segment and what it cost | O3 |
| 4 | Distance large unless the plan needs players close | Not in the code as such. The race exists (`decide.attacker_reach`, `defender_map`; JS `attackerReach`, `defenderMap`) | Help distance is read by the race: how long a held defender needs to reach the gap and get back. It enters through the looks' chances | O3, O6 to O10 |
| 5 | Secondary skills break ties | Part: the scout's movement review (`plan.Scout.beat`), screens (`plan.screen_roles`), jobs (`plan._job_variants`) | Setup step 4: between placements level on the value, the one where his Dribble or screen opens the most | O11 |
| 6 | The setup order | `plan.place_offence`: a sweep of every square for each attacker, ranked by the list. No order | Rewritten to the design's six steps | B4 |
| 7 | Get out of each other's way | Part: a teammate on a path blocks it in the map (`decide.Read.map_options`, JS `covBuild`) | It falls out of the value: a blocked drive or cut is a look that no longer opens. The coach's line names it | O5 |
| 8 | Gaps in the key are worth the most | In the cards (layups 17 to 19) and the gaps (`decide.Read._gap_vec`, JS `gapVec`) | Kept as an input | D11, O1 |
| 9 | Spread so each defender is held by one man | The plan's "Attention" line (`plan.read_plan`); overloads (`decide.cover_groups`, JS `lgOverloads`) | Falls out of the value against the defence's joint answer. The offence's line reports who holds whom | O3, D4 |
| 10 | One sum for the stack and the spread | Not in the code. The read-ahead counts time (`plan.horizon_read`) | The value read ahead is that sum. The five situations are checks | O6 to O10 |
| 11 | Little time: several actions at once | Not in the code ("the budget" is only listed in `conditions.py`) | Falls out: with one phase left, the chance "at least one route opens" is what matters. The offence's line counts the routes | O6, O9 |
| 12 | Where the ball starts against the centre decides access | The plan's "Access" line; the pass chance (`decide.cov_pass`, JS `covPass`). No centre exists | The ball's start is setup step 2; layer 3 gives access | O6 to O8 |
| 13 | Room and angles are a separate limit | Not named. The boundaries only act through geometry | Room is read as the squares and lanes open from the ball (layer 3). The corner inbound is its check | O7 |
| 14 | Full denial is the same access case | Denial is a rule (`receiver_denial`) inside the pass chance | Nothing special: pass chances near 0 are low access | O10 |
| 15 | The team centre of gravity, three layers | Not in the code | New: `weight.py` and JS `weightMap`, read by setup and play | D1, G1 to G3 |
| 16 | Layer 1: open and contested, times points; the pull is the difference | The parts exist: the scout's cases (`plan.case_value`), the map's value and what the defence leaves (`covBuild` already reports their difference for display) | Built as layer 1 on the one scale, with the block, the rushed closeout and the fake as answers | D3, G2 |
| 17 | Add the weights across five attackers for the base centre | Not in the code | The balance point of layer 1's weights | D1 |
| 18 | Packed key, box-and-one, mid-range conceded | Results of the list today, unchecked | Results of the map and the value, each with a check. D3 reports what the cards say | D1, D2, D3 |
| 19 | Layer 2: occupation | The race (`decide.attacker_reach`) | Segments nobody can reach this phase are dropped | D4 |
| 20 | Layer 3: the ball's reach; one factor with layer 2 | The pass chance from every square the ball handler can reach (D-250), the map's "reach" | One reach factor a segment, counted once | D4, D8 |
| 21 | Each defender's jobs: his man, the ball, the gaps | The role lines (JS `defenderRoles`, `assignOf`; `conditions.stances`) | The coach's line for each defender is rebuilt on the weight map | D10, D12 |
| 22 | The link rule | Not in the code. Today's lines ("X2 sags off O5 to guard O1's look") come from the list | Used to set how far along his line a base position sits, and run as a check on the result | D4, D5, G2 |
| 23 | Defenders with nothing to guard move to the weight | Today they "cover the squares around E11": empty space | Their base position is on the line to the weight; the search keeps a move only if it lowers the value | D12 |
| 24 | The centre keeps defenders goal-side | Not in the code. Today's setup says "nobody starts anywhere" (JS `settleSetup`) | The search starts from the base positions | G1, G3, G4 |
| 25 | A defender or the whole team can shift its weight | The Need a Three card exists in the scoring only (`ctx.three_only`); the map ignores it | "Worth right now" for a two and a three, read by the map | D2, D7 |
| 26 | No weighting between team and individual | Today ties on the list are broken by "each defender's own cover of his own man" | Both in points inside one value; that tie-break goes | G2 |
| 27 | The trap | Not searched. A "takeover" by two helpers exists (D-226) | A stance the search can reach, judged with the trapper gone from where he was | D8, D9, A5 |
| 28 | Arrows chosen with the square | Part: the setup picks the square by a quick re-read, then the arrow (JS `settleSetup`) | Square and arrow pair are one choice, judged by the value | A1 to A6 |
| 29 | Arrows take the most value off | By the list today | By the value. The three effects are checks | A8, A9, A10 |
| 30 | Speed is a gap | The race and "outrun him" (`conditions`) | Kept; contained by distance, direction and help through the value | A7 |
| 31 | The pass counts closeouts, failed intercepts and fakes | The rushed closeout is priced (the off-balance cut in `Read._vals`, `_gap_late`); both outcomes of a pass (D-250, D-263); the fake only in the search | The value reads all four outcomes of a pass. The mix's tie rule is fixed | A11 to A13 |
| 32 | Worth right now; best legal contest; real chances; the map leads | Points are fixed at 2 and 3 (`RC.ZONE_POINTS`) | A per-possession worth for a two and a three; the map leads the defence | D7, D5 |
| 33 | The list kept, priced as the possession's value | The list leads, compared item by item (`plan.list_key`, `decide.top_of`, JS `topOf`, `lgBetter`) | The value leads everywhere. The list stays as the order of the looks and as a tie-break. The lasting gap is display only | G5, B1 |
| 34 | Take the good shot; three seconds from entry; no action without purpose | The shot is compared with the top of the list (`Read._map_leaf`). Three seconds cost nothing while he can still get out (`decide.three_seconds_owed`) | The shot is compared with the value of playing on. The action he must spend to leave is counted from the moment he enters | O1, O2, O11 |
| 35 | A fundamentals exam | An older exam exists (`exam.py`, steps 3m to 12) and the design checks in `docs/plans/COMPUTER_FIX_PLAN.md` | A standing test file, `tests/test_exam.py`, and a line in `CLAUDE.md` | all |

**The five recorded changes**

| What changed | Today | What I will do |
|---|---|---|
| "No two in a section" is a counted cost | Not in the code | As row 3: no rule, a cost the value shows |
| "Maximise distance" is measured by help distance | Not in the code | As row 4 |
| Cover comes in degrees | Already so: a look is worth what the best contest leaves of it (`Read._map_cov`, JS `covValue`), set, from the side, from behind or rushed | Kept, and carried into the weight map: covered weight pulls less by what the cover takes off |
| The five solved together | Part: the setup places one at a time and then lets any defender move again while that leaves less | Start from the base positions, improve all five by the value, then run the link rule as a check |
| The ball's reach counted once | Counted once in a look's worth today | Counted once, in layer 3. The link rule reads the map's values and doesn't discount again. A test compares the two |

## 3. The scale audit

Good news first: **nothing in either engine works in expected points per shot, and nothing converts between scales.** Every "divide by 20" is a dice chance. The rules, the search's final values, the map, the list, the lasting gap, the shot bar and the scout all use rating times points with −5 and +5.

**What is not on the scale, and is live today**

| # | What | Where | What it does today | Fix |
|---|---|---|---|---|
| 1 | Fitted maps over the reading | `learned_weights.json` (the level maps); `decide.calibrate`, `Read._quick_cont`; JS `calibrate`, `_quickCont` | The quick reading that orders and cuts every list of turns goes through a fitted curve. It is ranked beside rule-exact values | The quick reading becomes a cheap form of the same value. The fitted maps stop leading anything |
| 2 | The phase table and its averages | `vcoarse.json`, `eval.relative_average`; `decide.vcoarse`, JS `vcoarse` | Same quick reading. By its own note it was fitted with turnovers at 0, not −5 | Replaced by the shot bar, which is counted by the rules |
| 3 | Two hand multipliers: 0.7 and 0.85 | `ai_profiles.json` `later_p`, `continuation`; `Read._looks`, `_cont_of`; JS the same | In the quick reading: 0.7 on a look that needs another turn, 0.85 on the best look left | Removed. A look's chance comes from the race and the pass |
| 4 | The shot clock running out isn't priced | `Read._map_leaf`, `bars_of`; JS `_mapLeaf`, `barsOf` | A last-phase board with no shot reads 0. The rules score −5 | −5, by the rules |
| 5 | The closely guarded count in thirds | `conditions.py` line 357 | The plan's listing counts it as a third of −5 a phase; the map counts it all or nothing | One way: by the rule, as the map has it |
| 6 | Sums that are not one look's value | `plan.Scout.beat` ("grows": worths added over many squares), used in the defence's matchup price (`place_defence.price`) | The matchup rule's key | Re-priced as a gap: the value behind the defender at the chance the Dribble wins |
| 7 | Bare chances used as tests | `goals.py` lines 93 and 100 (a wall "halves" his look; a pass chance under a half is "denied"); `conditions.py` line 213 (60 in 100 of a look's value) | They name goals and rule a condition in | Replaced by comparisons in points, or kept as words only where nothing is decided on them |
| 8 | The block stops at −5 | `Read._block_value`, `plan.case_value`, `scoring.block_option`; JS `blockValue` | One thing read two ways | Read past the block everywhere (carry-over 1) |
| 9 | The search's window is −10 to 60 | `search.VMIN, VMAX`; JS the same | A possession with three turnovers banks −15, outside the window | Widened to what the rules allow |
| 10 | The reply's expected value leaves out the foul's +5 | `scoring.contest_options`, `block_option` | Shown in the advice panel; not in the computer's choice | Add the +5 so the panel and the computer agree |
| 11 | Possibly three seconds counted twice | A look's own worth (`map_options`) and again on the list's top (`top_of`) | Not confirmed: I didn't run a board | Stage 1 counts it once, from entry, and a test checks it |

**On the scale, but a different floor from the design's words:** a shot's value is floored at 0 everywhere, by the rules ("a declared shot worth less than 0 scores 0"). The design says 1. See section 7.

**Not live, left alone:** the learned weights and their readings (off), the foul table's two measured constants (dead in the app since D-198), the lane readings (off), and the old solver.

**Display only, on purpose:** percentages from ratings (a rating times 5), "times in 20", the colour ramp, the trainer's accuracy and rating. These convert for the eye and decide nothing.

**Still design values in points, not mine to change:** each level's pick noise (5.0, 2.5, 0.5), variety margin (0, 1, 2) and goal margin (8, 4, 1) in `ai_profiles.json`. The design says the levels differ only in how far and how widely they search. I list them here and in "Stand-ins" in the Part B report, and leave them.

## 4. What the code does today against what the design says

**How a position is scored**
- **Today.** The search reads a board as what is banked plus the larger of two things: the best shot that can go up now, and the top of the list (the single best look the offence could have by the start of the next phase, at its chance). Turns that read the same are ordered by comparing the whole list item by item. Setups compare the whole list item by item, then the lasting gap. The quick reading that orders and cuts the lists uses a different measure again (the fitted maps above).
- **The design.** One value: every look best first at its chance of opening, the best one that opens, the shot bar if none does, costs and gains at their chance, read ahead. The same value orders the lists.
- **The gap.** Today's number answers "how big is the defence's worst hole?" It has no chance of nothing opening, so "playing on" always looks as good as the best hole. That is why the cutter under the rim didn't shoot.

**How the defence's five stances and arrows are chosen**
- **Today, at setup.** Nobody starts anywhere. Defenders are put down one at a time, each time the defender and square that leave the least on the list, and then any may move again while that leaves less. The square is picked by a quick re-read, then the arrow.
- **Today, in play.** The search tries the map's own answer and settlement moves and a set of moves from geometry, and keeps the turn that leaves the least by the reading above.
- **The design.** Build the weight map. Put every defender on his goal-side line. Improve all five, square and arrows together, by the value. Check the result against the link rule.
- **The gap.** With no starting shape and a measure that only sees the worst hole, a defender can settle on empty squares "to cover" a hole nobody can use. That is what the playtest showed.

**How the offence places at setup and chooses in play**
- **Today, setup.** A sweep: each attacker in turn over every legal square, kept when the list reads better against a quick defence, then the best few read in full against the defence's real setup and four turns ahead. The best by the list wins.
- **Today, in play.** A search over its turns (two actions each), each line ending in the reading above. Ties go to the list, then to the plan's route.
- **The design.** Setup in six ordered steps, scored by the value against the defence's full answer. In play: shoot if the shot beats playing on, else the two actions that raise the value most.
- **The gap.** The sweep has no notion of segments, pins or help distance, and it chases the worst hole. So the point guard stood two squares past the arc: nothing in the list said he held nobody.

**When the offence decides to shoot**
- **Today.** When the shot's settled value is more than the reading of playing on, and playing on is the top of the list.
- **The design.** When the shot beats the value of playing on, which includes the chance nothing better opens and the falling shot bar.

**How the three seconds and the closely guarded count are costed**
- **Three seconds today.** −5 inside a look's worth if he was in the key at the last phase end and the look is in the key; and −5 on the list's top for each attacker who was in the key at the last phase end and can't get out with what the offence has left. If he can still get out, it costs nothing, however late.
- **The design.** The action he must spend to leave is counted from the moment he enters.
- **Closely guarded today.** −5 on the look only at the phase end where the count falls. Nothing before.
- **The design.** By the rule, as today (it is in "Kept"). I will make the plan's listing agree with the map (scale audit, row 5).

## 5. The build plan

I would keep Part B's six stages, with two changes:
- **Each check's test is written in the stage that builds its principle,** not all in Stage 6. The prompt asks that each test fails when its principle is missing; the surest moment to show that is just before the principle goes in. Stage 6 then assembles, reruns and reports them.
- **Stage 1 starts with the mix's tie rule** (carry-over 2), because the value's reading of a fake depends on it.

| Stage | What | Files |
|---|---|---|
| 0 | Rulings recorded (next free number is D-283). The exam's board file and a harness that reads one board in one engine or both | `DECISIONS.md`; new `tests/test_exam.py`, `tests/exam_boards.py`, `tools/step_31.py` |
| 1 | The scale leftovers (section 3). The mix's tie rule. The possession's value, with routes for looks that share a cause. The shot bar counted from the value. The value leads the search, the ties and the setups. The lasting gap becomes display only | `decide.py`, `search.py`, `scoring.py`, `plan.py`, `agent.py`, `conditions.py`, `goals.py`, `rules_config.py`, `data/ai_profiles.json`; `engine.js` |
| 2 | Segments. Layers 1 to 3. Worth right now. The centre and its lumps. Covered weight | new `weight.py`; `board.py`, `state.py` (the worth-now hook), `scenarios.py` (Need a Three sets it); `engine.js` |
| 3 | Base positions. The joint improvement of five stances, square and arrows. Traps, switches and denial as reachable stances. The link-rule and goal-side checks on the result | `weight.py`, `decide.py`, `plan.py` (`place_defence`), `agent.py`, `search.py`; `engine.js` (`settleSetup`, `settleMoves` replaced) |
| 4 | The offence in play (shoot or play on by the value; purpose for every action; three seconds from entry). The setup order | `plan.py` (`place_offence` rewritten), `agent.py`, `decide.py`, `search.py`; `engine.js` |
| 5 | The Coverage view from the weight map with the centre marked; each defender's line; the offence's line; the phase score from the value; the coaching tips | `playmaker_web/view.py`, `game.py`, `report.py`, `static/app.js`, `coach.js`, `tips.js`, `report.js`; `plain.py` checks |
| 6 | The exam assembled and run; a test for each older principle that has none; the `CLAUDE.md` line; the golden game once; times; the report, the code audit, the code folder and its zip | `tests/`, `CLAUDE.md`, `docs/reports/` |

**How I would build the value (Stage 1), so you can correct it now**
- **Looks** come from the map as it stands today: for each attacker, each square he can shoot from, with its chance and its value against the contests it faces.
- **A shared cause** is a shared roll or a shared action. Looks that need the same Dribble win, the same pass, or the same screen to hold are one route. The route counts once, at that roll's chance, and is worth the best look behind it. One attacker's several squares off the same movement are also one route (he can only be in one place). The map already records, for each look, where it starts from, whether it needs a Dribble win and whether it needs a pass, so the grouping reads those and adds nothing by hand.
- **Costs and gains** go in at their chance: a pass stopped (−5 and the phase), a Steal against him, a violation, a foul drawn.
- **Playing on** is the shot bar: the same value for the next phase, worked back from the last phase, where no shot is −5.
- **Reading ahead:** the search already alternates the two sides' turns. Each line now ends in the value. Each side's model of the other is that side's own search, as now.

**How I would search the defence (Stage 3)**
- Start on the base positions.
- One pass: for each defender in turn, every square he may take and each of the eight arrow pairs, keep the best if it lowers the value.
- Also try two defenders together where one alone can't show the gain: swapping men, and a second defender onto the ball with his own man read as left.
- Stop when a full pass changes nothing. That is "settled". Check G4 starts it from a deliberately bad shape as well and compares.

## 6. The exam boards

**How to read these.** Squares are column and row; the rim is I2. The key is columns G to K, rows 1 to 6. "Clock 12" is the full shot clock (six phases); "clock 2" is the last phase. Unless a board says otherwise it is the app's rules at Senior Pro, and each side has its full actions for the phase. Every check is one reading of one board unless it says otherwise. All boards were checked against the engine: every square is legal, and every pass chance quoted is the engine's own.

**The teams**

Prescribed teams (as printed):

| Team | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Five Out | Pass-First PG C | Sharpshooter SG A (three 11) | Two-Way SF B | Stretch PF A | Stretch C C |
| High-Low | Combo Guard A | Playmaker SG C | Stretch SF C | All-Rounder PF B | Post Scorer C A |
| Twin Towers | Scoring PG C | Two-Way SG A | Scoring SF A | Post Scorer PF C | Post Scorer C B |
| Ball Movement | Pass-First PG A (Pass 20) | Sharpshooter SG C | Point Forward SF B | All-Rounder PF A | Post Scorer C C |
| Shoot and Protect | Pass-First PG B | Three-and-D SG A | Stretch SF A | Stretch PF C | Rim Protector C C |
| Iron Wall (the defence on most boards) | Defensive PG B | Bucket Getter SG B | Defensive SF B | Stretch PF B | Rim Protector C B |
| Run and Gun | Attacking PG B | Two-Way SG B | Scoring SF B | Defensive PF A | Rim Runner C C |

Teams built for a check (each is one card a position, so a legal roster):

| Team | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Poor five | Attacking PG C (three 7) | Playmaker SG C (7) | Defensive SF C (6) | Defensive PF C (6) | Rim Protector C C (5) |
| One shooter | Attacking PG C | Sharpshooter SG A (11) | Defensive SF C | Defensive PF C | Rim Protector C C |
| Five Out, big centre | Pass-First PG C | Sharpshooter SG A | Two-Way SF B | Stretch PF A | Rim Protector C C |
| Speed | Combo Guard A (Quick Step 2) | Bucket Getter SG A (Quick Step 2, three 10) | Slashing Wing A (Quick Step 2, three 7) | Stretch PF A | Stretch C C |
| Two equal | Pass-First PG C | Three-and-D SG A (three 10) | Stretch SF A (three 10) | Defensive PF C | Rim Protector C C |
| Best in corner | Pass-First PG C | Sharpshooter SG A (three 11) | Stretch SF A (three 10) | Defensive PF C | Rim Protector C C |

"The spread" below means O1 I11 with the ball, O2 C9, O3 O9, O4 A3, O5 Q3.

### The boards

**E1. A poor-shooting five** (D1, D12). Poor five against Iron Wall, the spread, clock 12. The defence sets up.
- D1 passes when the weight map's centre is in the key, and at least four defenders stand in the key or on a square touching it.
- Fails without the principle: with the old setup's result put in its place, or the map switched off, the defenders stand out at their men.

**E2. One elite shooter, four weak** (D2). One shooter against Iron Wall, the spread, clock 12. The defence sets up.
- Passes when one defender stands next to O2, and each of the other four stands at least as far off his man as he does on E1.
- Fails without it: swap O2 back to the Playmaker SG C (that is E1) and his defender must drop off; if he doesn't, the test fails.

**E3. The normal board** (G1, G2, G4, A1, A3, A6, A16, D12, B1, B3). Five Out against Iron Wall, the spread, clock 12. The defence sets up.
- **G1** passes when every defender is nearer the rim than his man and within one square of the line from his man to the weight he would help, or the coach's line names what he gains elsewhere.
- **G2:** swap O2 for the Playmaker SG C (three 7). Passes when O2's defender stands further from him, along the line toward the weight, than he did against the Sharpshooter.
- **G4:** start the defence's search from the base positions, and again from a bad shape (all five defenders standing directly above their men, further from the rim). Passes when both end on the same five squares and arrows.
- **A1:** passes when the defender of an attacker one pass from the ball has one arrow on his man and the other across the passing lane to him.
- **A3:** passes when X1's wedge bars the drive that is worth most to O1 (I read each drive's worth with X1's wedge lifted).
- **A6** (also on E9 and E12): turn each defender's arrows, one defender at a time, to each of the other seven directions. Passes when none of them lowers the value.
- **A16:** five shooters spread. Passes when at least one defender stays in help (within two squares of the key), or, if all five deny, the offence's best next turn is a cut or drive into the paint and the value shows it.
- **D12** (also on E1 and E12): lift each defender off the court in turn. Passes when the value rises every time. A defender whose removal changes nothing is guarding empty space.
- **B1:** passes when the number the setup ranked by, the number the search ends its lines with, the coach's line and the phase score are the same number on this board, and the list and the lasting gap rank nothing.
- **B3:** change the offence's private plan (and, separately, the defence's private matchups) and run both through the app's own path. Passes when the other side's choice is the same.

**E4. The mid-range shooter at the elbow** (D3). Five Out against Iron Wall. O1 I11, O2 (Sharpshooter, mid-range 12) has the ball on L6, O3 C9, O4 A3, O5 Q3. X1 I10, X2 I4 (three squares off), X3 D8, X4 B4, X5 P4. Clock 10. The defence's turn.
- The report gives the open shot (24), what each defender's contest leaves, and what else the defence gives up by closing.
- Passes when the defence's turn is the one that leaves the lower value: close out, or stay.
- A table for all 81 cards (what a set contest takes off each card's mid-range shot) goes in the report, to answer "do the cards concede the mid-range?"

**E5. A non-shooter in the far corner** (D4). Five Out, big centre, against Iron Wall. O1 has the ball on C9, O2 A3, O3 I11, O4 O9, O5 (Rim Protector C C, three 5) Q3. Clock 12. The defence sets up.
- Passes when O5's defender stands at least three squares off him, toward the weight, and the coach's line says why.
- Fails without it: put the Sharpshooter in that corner and the defender must come back.

**E6. An elite shooter in control, his defender sagging** (D5). Five Out against Iron Wall. O2 (Sharpshooter) has just caught the ball on C9 and hasn't moved. O1 I11, O3 O9, O4 A3, O5 Q3. X2 is on G5: three empty squares between him and O2 on the diagonal, so only a Sprint gets him next to O2 and he would arrive rushed. X1 I10, X3 N8, X4 B4, X5 P4. Clock 10. The defence's turn.
- Passes when X2 ends the turn where one Move puts him next to O2.
- My reading of "three squares off": from three squares away in most directions one Move already reaches him. So I have set three empty squares between them. Say if you meant otherwise.

**E7. A shooter two squares past the arc** (D6). Five Out against Iron Wall. O2 (Sharpshooter) on C11, two squares past the arc. O1 I11 with the ball, O3 O9, O4 A3, O5 Q3. Clock 12. The defence sets up twice: with deep range open to five squares (Senior Pro), and with none open (Junior). Same cards both times, so only the level changes.
- Passes when O2's defender is within two squares of him at Senior Pro, and at least two squares further off at Junior.

**E8. The offence needs a three, last phase** (D7, G3). The Need a Three card's teams and squares: Five Out against Iron Wall, the spread. Clock 2. Worth right now: a three 3, a two 0 (the card's rule: only a three scores). The defence sets up.
- **D7** passes when the map's centre is outside the key, at the arc, and no defender stands in the key.
- **G3** passes when, against E3 (same teams, same squares, normal worth), every defender has moved from the hoop side of his man to level with him or above him.

**E9. The corner trap** (D8, A5). Poor five against Iron Wall. O3 (Defensive SF C, Pass 11) has the ball on Q2 with his dribble dead. O1 M6, O2 Q8, O4 C9, O5 K2. X3 P3 (on the ball), X1 N5, X2 Q7, X5 L2 (each next to his man on the passing line: those three passes are denied), X4 E8. The only pass open is to O4, 15 in 100. Clock 8. The defence's turn.
- **D8** passes when a second defender ends the turn next to O3.
- **A5** passes when, after that turn, O3 has no square to step to (with his dribble dead that means none of his four pivot squares).

**E10. A good passer at the top, lanes open** (D9). Ball Movement against Iron Wall, the spread. X1 I10, X2 D8, X3 N8, X4 B4, X5 P4. Clock 10. The defence's turn.
- Passes when no second defender goes to the ball, and the report shows the trap's value above the stance chosen.

**E11. Drive and kick** (D10, and the design's open question on drift, lift and fill). Speed against Iron Wall. O1 (Combo Guard) has driven to J5 with the ball; X1 is beaten behind him on J8. O2 (Bucket Getter, three 10) Q4, O3 O9, O4 C9, O5 G3. X2 M4 (three squares from the drive, so one Move gets him next to it; four from O2), X3 N7, X4 D8, X5 H3. Clock 10. The defence's turn.
- The report gives three values: nobody helps; X2 helps and nobody rotates; X2 helps and X3 rotates to O2.
- Passes when the value for "X2 helps" includes the pass out to O2, and the defence's turn is the lowest of the three.
- Then one more reading, the offence's next turn: do O2 and O3 drift or lift without any rule? Reported, not passed or failed.

**E12. Two bigs under the rim** (D11). Twin Towers against Iron Wall. O1 I11 with the ball, O2 C9, O3 O9, O4 G3, O5 K3. Clock 12. The defence sets up.
- Passes when each big has a defender next to him (in front, three-quarter, beside or behind with the lane cut), never more than one square off while the ball can reach him. The report gives the value of fronting against playing behind.

**E13. The cutter under the rim** (O1). High-Low against Iron Wall. O4 (All-Rounder PF, layup 18) has caught the ball on J3. O1 I11, O2 C9, O3 O9, O5 A3. X4 is late on L5, two squares off. X1 I10, X2 D8, X3 N8, X5 B4. Clock 8. The offence's turn. The phase's one Hesitate or fake is already used, so the answer is a clean yes or no.
- Passes when the offence's first action is O4's shot.

**E14. Two attackers in the key** (O2). Twin Towers against Iron Wall. O4 G3 and O5 K4 were both in the key when the last phase ended. O1 I11 with the ball, O2 C9, O3 O9. X1 I10, X2 D8, X3 N8, X4 H2, X5 J3. Clock 8. Two readings:
- **The offence's last turn of the phase** (two actions left). Passes when both are out of the key, or a shot is declared.
- **The offence's first turn.** Passes when the value already carries the cost of the two actions they must spend to leave (it is lower than on the same board with both standing just outside), and the turn doesn't send a third man in.

**E15. The offence's own setup, full clock** (O3, O4, O11). The offence sets up against Iron Wall, clock 12.
- **O3** (Five Out): passes when no two attackers share a segment, and lifting any one attacker off the court raises what the defence can hold (so each one is holding somebody).
- **O4** (Shoot and Protect, whose centre is the Rim Protector C C, three 5): passes when he starts in the green zone, on the baseline beside the key, in the post, or as the screener in the plan's first step, and not at the arc.
- **O11** (here, on E17 to E21 and in B4): for every screen or cut the computer chooses, take it out. Passes when the value drops.

**E16. A teammate in the driver's lane** (O5). High-Low against Iron Wall. O1 (Combo Guard) has the ball on I9 and has beaten X1, who is locked beside him on H9. O5 stands on I6, in the lane to the rim, with X5 on J5. O2 C9, O3 O9, O4 A3. X2 D8, X3 N8, X4 B4. Clock 10. The offence's turn.
- Passes when the turn moves O5 out of column I, and the value of that turn is above the best turn that leaves him there.

**E17. Baseline inbound under the rim** (O6). Five Out against Iron Wall (the Rim Protector at the rim). O3 inbounds from K0, under the rim. Card clock 8. The offence places the other four.
- Passes when at least three of the four start in or touching the key, and the plan's first phase runs two or more actions at once, heading outward.

**E18. Corner inbound** (O7). The same teams. O3 inbounds from B0, on the baseline by the left corner.
- Passes when the four are spread (no two in the same segment), with one primary action and a named fall-back.

**E19. Sideline inbound near half court** (O8). The same teams. O3 inbounds from R12, on the right sideline.
- Passes when the plan is one cut or one screen.

**E20. The top, last phase** (O9). Five Out against Iron Wall, the ball at the top, clock 2. The offence sets up.
- Passes when the five stand closer together than in E15's full-clock setup, and the turn runs two or more actions at once.

**E21. Full denial at the top** (O10). Five Out against Iron Wall. O1 I11 with the ball, O2 E7, O3 M7, O4 A3, O5 Q3. X1 I10, and X2 F8, X3 L8, X4 B4, X5 P4 each next to his man on the passing line. All four passes are denied (0 in 100). Clock 12. The offence's turn.
- Passes when the turn runs two or more off-ball actions at once and doesn't bring attackers together.
- My reading: the offence sets up before the defence, so "full denial" can only be met in play. Say if you meant a setup check.

**E22. The point guard past the arc** (O12). Five Out against Iron Wall. O1 has the ball on I13: plain wood, no shot. O2 C9, O3 O9, O4 A3, O5 Q3. X1 I10, X2 D8, X3 N8, X4 B4, X5 P4. Clock 12. The offence's turn.
- Passes when O1 moves to a square where he has a look, or the offence's line says what he gains by staying.

**E23. Two equal looks** (G5). Two equal against Iron Wall. O1 I11 with the ball. O2 (three 10) C9 and O3 (three 10) O9: mirror squares, and both passes land 100 in 100. O4 G13 and O5 K13 on plain wood with their defenders on G12 and K12. X1 I10. Three readings: X2 and X3 both sagging (F6, L6); X2 out on O2 only; both out.
- Passes when covering one leaves the value unchanged and covering both lowers it.

**E24. A man the ball can't reach** (A2). Five Out, big centre, against Iron Wall. O1 has the ball on K9. O5 is on Q3. X3 stands on P4, next to O5 on the passing line, so the pass is denied (0 in 100). O2 C9, O3 I12, O4 A3. X1 K8, X2 D8, X4 B4. X5 (O5's own defender) is on N4. Clock 10. The defence's turn.
- Passes when X5 ends with neither arrow on O5.

**E25. A screened defender** (A4). High-Low against Iron Wall. O1 has the ball on I10; X1 is on I9. O5 screens X1 from J8 (the board is made by playing that Screen). O2 C9, O3 O9, O4 A3. X2 D8, X3 N8, X4 B4, X5 J7. Clock 10.
- Passes when the reading has X1's diagonal arrow walling no drive and jumping no lane: the value equals the value with that arrow taken away.

**E26. Fast non-shooter, fast shooter** (A7). Speed against Iron Wall, the spread, clock 12. The defence sets up twice: with the Slashing Wing (three 7) on O9, and with the Bucket Getter (three 10) on O9 and the Slashing Wing on C9.
- Passes when the defender on the Slashing Wing gives more ground than the defender on the Bucket Getter at the same square, and with the Bucket Getter there a second defender stands nearer that side.

**E27. Sideline or middle** (A8). The ball handler on L10, right of centre. The defence sets up, clock 12.
- First: Two equal against Iron Wall. O2 (three 10) E9, O3 (three 10) Q3, O4 G13, O5 K13. Passes when X1's wedge bars the way to the middle and leaves the sideline.
- Second: Best in corner, with the Sharpshooter (three 11) on Q3 and the Stretch SF on E9. Passes when the wedge turns to bar the sideline side.

**E28. Two lanes or one** (A9). O1 I11 with the ball, O2 C9, O4 A3, O5 L7. X1 I10, X2 G5, X3 K5, X4 B4. The helper X5 stands on I9; only his arrows are in question. Clock 10.
- First: Five Out, O3 on O9. Arrows north and north-east cut both passes to the right (O3's three, 24, and O5's mid-range shot, 18: each lands 50 in 100, so 21 saved). Arrows west and north-west cut the one pass to the Sharpshooter (33: 16.5 saved). Passes when the arrows point north and north-east.
- Second: One shooter, O3 on P10 (two past the arc: 12), O5's shot 14. Each lane now lands 25 in 100. The two passes save 19.5; the one saves 24.75. Passes when the arrows point west and north-west.
- The report gives the points saved by each choice both times.

**E29. Help behind one lane** (A10). High-Low against Iron Wall. O1 has the ball on N8 on the right wing; X1 is on M7. Help stands behind the middle (X5 on J4, X3 on I9). Nobody is on the baseline side. O2 C9, O3 I11, O4 A3, O5 F3. X2 D8, X4 B4. Clock 10. The defence's turn.
- Passes when X1's wedge bars the baseline side and leaves the middle.

**E30. The skip pass** (A11). Five Out against Iron Wall. O1 has the ball on C9. O3 is on O9; his defender X3 is sagging on J4, five squares off, so he must Sprint to close out. O2 A3, O4 I11, O5 G3. X1 D8, X2 B4, X4 I9, X5 H3. Clock 10.
- Passes when O3's value after the catch is more than his shot over the rushed closeout alone, by the drive past the rushed defender; and starting X3 one Move away takes that drive back out.

**E31. The Intercept gamble** (A12, A13). Step 30's board 3: High-Low against Run and Gun. O2 has the ball on I11. O1 C9, O3 O9, O4 A3, O5 Q3. X1 A6, X2 F7, X3 P6, X4 J4, X5 L10. Clock 12. The offence declares a pass to O4.
- **A12:** the report gives the three numbers (today: winning 19.3, being faked 27, holding 21). Passes when the defence holds.
- **A13:** the same board with O2 rushed, so he can't fake. Passes when the defence now goes for the ball.

**E32. Denial with help behind** (A14, A17). Speed against Iron Wall. O1 I11 with the ball, O2 (Bucket Getter) C9, O3 O9, O4 A3, O5 K3 (so his defender is by the rim). Clock 12. The defence sets up.
- **A14** passes when O2's defender stands in the passing lane next to him.
- **A17:** from that board, O2 makes the one Move that raises the value most. Passes when the value shows the change and the defence's next stance is read against the new board.

**E33. Denial with nobody behind** (A15). The same, with O5 on Q3, so nobody is near the rim.
- Passes when O2's defender doesn't deny, or the report shows the cut behind him priced and still worth giving up.

**B4. The 20 November possession.** From its setup: O1 K4, O2 I2, O3 N6, O4 I11 with the ball, O5 Q3; X1 K3, X2 N7, X3 I10, X4 J4, X5 H4. Both computers play the possession once, All-Star against All-Star.
- Passes when no three seconds are called, a cutter who catches in the green zone with one late defender shoots, every screen raises the value, the ball handler doesn't sit past the arc without a named gain, and no defender guards empty space at any phase start.
- **It needs the ten cards** (question 1).

**B2. Both engines.** Every board above is read in Python and JavaScript: the value, the weight map and the centre must match. Whole decisions are compared on the boards small enough to search in Python inside the limit (E13, E23, E24, E28), and I will list any left out.

**Every check, by number**

| Check | Board | Check | Board | Check | Board |
|---|---|---|---|---|---|
| D1 | E1 | O1 | E13 | A1 | E3 |
| D2 | E2 | O2 | E14 | A2 | E24 |
| D3 | E4 | O3 | E15 | A3 | E3 |
| D4 | E5 | O4 | E15 | A4 | E25 |
| D5 | E6 | O5 | E16 | A5 | E9 |
| D6 | E7 | O6 | E17 | A6 | E3, E9, E12 |
| D7 | E8 | O7 | E18 | A7 | E26 |
| D8 | E9 | O8 | E19 | A8 | E27 |
| D9 | E10 | O9 | E20 | A9 | E28 |
| D10 | E11 | O10 | E21 | A10 | E29 |
| D11 | E12 | O11 | E15, E17 to E21, B4 | A11 | E30 |
| D12 | E1, E3, E12 | O12 | E22 | A12 | E31 |
| B1 | E3 | G1 | E3 | A13 | E31 |
| B2 | all | G2 | E3 | A14 | E32 |
| B3 | E3 | G3 | E8 | A15 | E33 |
| B4 | the possession | G4 | E3 | A16 | E3 |
| | | G5 | E23 | A17 | E32 |

## 7. Differences from the rules

Where the design's words differ from `RULES_CURRENT.md` or `DECISIONS.md`. In every case I will build to the rules.

| # | The design says | The rules say | What I will do |
|---|---|---|---|
| 1 | A look is worth rating less contest, "never below 1", times the points | A shot worth less than 0 scores 0. It is the **contest** that is always at least 1 (the app's contest rule) | Floor the shot at 0, as every part of the engine does now |
| 2 | Values run from 1 to 39 | On today's cards the most is 38 (a 19 layup or dunk); the best three is 33 | No change: the scale is the same, only its ends differ |
| 3 | The read-ahead is up to three turns (step 27) | D-268 (19 Nov) made it four, both sides alike. The build reads four | Ask (question 2) |
| 4 | Each defender has two arrows, 45 degrees apart | D-167 and D-170 say so for the app, and the app plays that way. But `RULES_CURRENT.md` says "each X piece points one arrow" and has no app entry for the zone of influence | Build to D-167. The rules text is missing an entry: I would add it to the register so the page says what the app plays (question 7). No rule changes |
| 5 | "A wall needs both arrows" | D-170: he is caught by one arrow and barred by the other. The same thing in other words | No difference in play |
| 6 | Locked: "no Move, Sprint, Dribble or arrow turn, and rushed" | The rules add that a Quick Step is still allowed | Follow the rules |
| 7 | Need a three: "a two is worth almost nothing" | The Need a Three card: only a three scores, so a two is worth 0 | Use 0 on that card (question 6) |
| 8 | A turn is "2 actions for the whole team" | 1 or 2 actions a turn, from 6 a phase | Follow the rules |
| 9 | "A failed Intercept or Steal leaves him out of the play" | A missed Intercept leaves him on the line with his Move used; a missed Steal locks him | Read each by its own rule |
| 10 | Inbound checks have the computer place its players | The scenario cards print every square. Placing around a fixed inbounder is new for the computer | Build it for the exam's three inbound boards; the cards themselves don't change |

## 8. Principles settled before 21 November

For each: the test that would fail today if it went missing, or "no test". "Slow" means it can't run inside this step's limit as written.

| Principle | Guarded today by | Verdict |
|---|---|---|
| The scout's shot review (step 24) | `test_step24::test_every_case_in_the_table_matches_the_contest_rules` (every case against the rules) | Guarded, Python only. Nothing checks it by square or that it is done before play |
| The scout's movement review | `test_step24::test_a_won_dribble_is_worth_more_at_the_top_of_the_key_than_in_the_green_zone` and one more | Partly: one board, one pair |
| The matchup table and "the edge counted where it hurts" | Nothing calls the matchup table or checks the matchup rule | **No test** |
| The race (steps 22 to 26) | `test_step22c` (four tests), `test_step26` (two), `test_step28::test_the_map_reads_shauns_shot_as_open` | Guarded. Most of `test_step22c` is slow |
| The danger of the pass, both outcomes | `test_step26::test_both_outcomes_of_a_pass_are_counted`, `test_step28::test_the_read_ahead_counts_both_outcomes_of_a_pass` | Guarded |
| The read-ahead, both sides alike | `test_step27` (the dive test, the full-ranking test). "Both sides alike" is only a check of the source text. Nothing pins three or four turns | Partly; slow |
| The shot bar falling with the clock | `test_step24::test_the_bar_falls_slowly_then_faster_and_is_nothing_in_the_last_phase` (both engines) | Guarded for its shape. **No test** that the computer's shot in play is ruled by it |
| Three seconds, by the rule | `test_step22`, `test_step26`, `test_step27` (one each), and the rule's own tests | Guarded |
| The closely guarded count | `test_step22c::test_the_closely_guarded_count_is_counted_at_its_distance_from_the_violation`, `test_step27` | Guarded; slow |
| The contest as an action | `test_step28` (five tests) | Guarded |
| The block, and after a block | `test_step29` (five), `test_step30` (twelve) | Guarded. The map past a block: not built, no test (carry-over 1) |
| Fakes and the mix | `test_step29` (eleven), `test_step30` (two) | Guarded, but the mix test missed the tie fault in carry-over 2 |
| The pivot | `test_step29` (two) | Guarded |
| Deep range | `test_step29` (three) | Guarded |
| Separate thinking | `test_step24::test_changing_one_sides_private_goals_never_changes_the_other_sides_choice` | Weak: the plan is put on one computer that the other never receives, so it can only fail through a leak in shared state; its second half compares two identical calls. 14 minutes |
| The list (D-219) | `test_two_responsibilities_22b` (two), `test_heat_map_20` (one) | Guarded today. These get re-recorded with a note when the value takes the lead |
| The lasting gap | `test_heat_map_20` (four) | Guarded. Stays as a display |
| The wedge stops the ball handler | `test_zone_18g` (four), `test_screen_22b` (six) | Guarded |
| The wedge never blocks a pass | Only a check that the words are in the rules text | **No test of the behaviour** |
| Turnovers −5, fouls +5, play on | `test_points_play_on_18r` (seven) | Guarded |
| No hand-set weights | Nothing scans the code or the settings | **No test** |
| Both engines agree | Many, but the strongest are slow (41 minutes for four) or are tools outside the test run | Guarded, slowly |
| Plain words | `test_step3n::test_no_banned_term_in_any_interface_string_or_template` and others | Guarded. Five script files aren't on its list |

**Tests I will add in Stage 6:** the matchup rule; a pass crossing a wedge lands; no hand-set weight leads a decision (a scan of the settings the live reading reads); the computer's shot in play against the shot bar (this is O1); separate thinking through the app's own path (this is B3); the read-ahead's length; the mix choosing to hold when holding is level.

## 9. Questions for Shaun

1. **The 20 November cards.** Can you send the deal code or the ten cards for game 75BFF6? From the values in the record, O1 looks like the Scoring Point Guard B (floater 14, three 9), and O2 like the Combo Guard C or the Defensive Point Guard A. I can't pin down the rest. Without them I can replay the squares with stand-in teams, but then B4 is not the same possession.
2. **Three turns or four** (section 7, row 3).
3. **The floor at 0** (row 1). Confirm, or say the design's 1 is a change you want (it would be a rule change, so not this step).
4. **The segments.** My proposal, for you to mark up. G: the green zone. ML, MM, MR: mid-range left, middle, right. LL and LR: the long two along each baseline. Ll and Lr: the long two above each elbow. CL and CR: the corners. WL and WR: the wings. T: the top. Deep squares count with the segment they sit behind.

```
     A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q
12   WL WL WL WL WL T  T  T  T  T  T  T  WR WR WR WR WR
11   WL WL WL WL WL T  T  T  T  T  T  T  WR WR WR WR WR
10   WL WL WL WL WL T  T  T  T  T  T  T  WR WR WR WR WR
 9   WL WL WL WL WL Ll Ll Ll ?  Lr Lr Lr WR WR WR WR WR
 8   WL WL WL Ll Ll Ll Ll Ll ?  Lr Lr Lr Lr Lr WR WR WR
 7   WL WL Ll Ll Ll ML MM MM MM MM MM MR Lr Lr Lr WR WR
 6   WL LL LL LL ML ML MM MM MM MM MM MR MR LR LR LR WR
 5   CL LL LL ML ML ML MM MM MM MM MM MR MR MR LR LR CR
 4   CL LL LL ML ML ML G  G  G  G  G  MR MR MR LR LR CR
 3   CL LL LL ML ML ML G  G  G  G  G  MR MR MR LR LR CR
 2   CL LL LL ML ML ML G  G  G  G  G  MR MR MR LR LR CR
```

   Two things to settle: which side I8 and I9 belong to (the long two has four segments and the middle column sits between two), and whether the corner ends at row 5.
5. **Layer 1, "the best answer a defender can give": whose contest?** Three readings:
   - the best contest any of the five could give there;
   - only a defender who can get there in time;
   - each defender's own (what he, with his card, would save there).
   I would use the first for the team's map and its centre, and the third for each defender's own base position, because the link rule compares what *he* saves. Say if you want one reading throughout.
6. **Worth right now on the Need a Three card:** 0 for a two, as the card says? And outside scenario cards it stays 2 and 3, with no control for the player, as the prompt says.
7. **The rules text and the two arrows.** `RULES_CURRENT.md` has no app entry for the zone of influence. May I add one to the register (text only, saying what D-167 and D-170 already rule)?
8. **The block.** The values are in carry-over 3. Do you want to rule on the reset now, or after Stage 1 shows what a new phase is worth under the design? And may I add a second block board with a good shot?
9. **Built teams.** Six of the exam's teams are built for their check (section 6). Each is a legal roster. Is that all right, or should every board use printed teams?
10. **D5:** three squares off means three empty squares between them (E6)?
11. **O1:** is it all right that the fake is already used on E13, so "he shoots" is a clean yes or no?
12. **O10:** an in-play check (E21), since the offence sets up first?
13. **O6 to O8:** the computer places four players around a fixed inbounder. The scenario cards print their squares, so this is only for the exam and for later cards. All right?
14. **The levels.** Today Rookie, Starter and All-Star differ in how far they look, and also by a pick noise, a variety margin and a goal margin set in points. The design says they differ only in how far and how widely they search. Leave those three settings as they are for now?
15. **B4 is a played possession,** not one reading. The prompt asks for it, so I will play it once. Confirm that doesn't break the "no play-outs" rule.

## 10. Risks

1. **"The first look that opens" treats tries as free.** The sum lets the offence fall back through every look. In the game each route costs actions and a turn has two. If I build the sum as written, the value will read too high on crowded boards. What I need to find out: whether limiting the routes to what the actions allow (counted by the rules, nothing by hand) changes any check. I will build it with that limit and report the difference.
2. **One defender at a time can stall.** A switch or a trap needs two to move. I have planned pair moves for those. G4 will show whether the search still depends on where it starts; if it does, the report says so and the base positions stay the only trusted start.
3. **The fake inside layer 1.** The design lists "the fake" among a defender's answers. A full mix needs a search, which a map can't carry for every look. My plan: for each look, a two-by-two mix (shoot or fake against close out or hold) from the scout's own case values, which is exact for that one look. The search keeps the full mix. If the two disagree on a check board, that is a finding.
4. **The value depends on the other side's answer, which depends on the value.** The offence's value needs the defence's best answer, and the reverse. The read-ahead cuts this off at three (or four) turns with the shot bar. On boards where the answer flips near the cut, a check could go either way. I will report any check whose result changes between three and four turns.
5. **D12 may be too strict.** Lifting any defender nearly always changes the value a little. I read "nothing to save there" as no change at all. If that never fires, the check proves nothing; if you meant "saves less than standing somewhere else", that is what the search itself already guarantees.
6. **The arrow checks need the geometry to exist.** A1 needs a square from which his man and the lane are 45 degrees apart. If the best square has no such pair, the stance may still be right. The report will give the value of the nearest stance that does, so you can judge.
7. **Speed.** Section "Times and tests" above. The risk is not the exam (seconds a check) but a setup long enough to be unplayable. I will report times at Stage 3, before the offence is built on top.
8. **Python is too slow to compare whole decisions.** Both engines will be compared on the value and the map everywhere, on whole decisions only on small boards. A difference that only shows in a deep search on a full board could slip through.
9. **Mid-range.** D3 can't fail by design: it reports what the cards say. On today's cards a set contest takes 3 to 8 off a mid-range rating, so I expect "not conceded" for the good shooters. That is for you to judge.
10. **The inbound boards** depend on new placement code (question 13). If that grows large, I will stop on those three checks and report, rather than bend the setup to pass them.
