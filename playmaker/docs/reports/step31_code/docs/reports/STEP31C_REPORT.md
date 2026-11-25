# Step 31 Part C: the design built in full. Report

**Not merged.** One think now fits in a phone's browser (the first condition is met). The exam is not: 25 of 50 checks fail because the build doesn't yet do what the design says. So the work stays on branch `step-31`; no pull request, no site rebuild, the live site unchanged.

## 1. Changes to the printed game

None. No rule and no card changed.

## 2. What changed, in six lines

1. **Memory is fixed.** One All-Star think held 2 GB or more; it now runs inside 256 MB with the same decisions and under 10 in 100 slower. The whole 20 November possession was replayed in one engine held to 300 MB.
2. **The new ruling is built in both engines:** inside the number, the defence's later answer gets only the movements it can really make before a look's shot goes up. Both engines agree on all 46 boards.
3. **The defence's setup search looks much wider** (every square within three of a defender's man or on his line, the best read in full), and all three inbound setups now run.
4. **The list is back as the tie-break** the design allows: level on the number, every look best first decides. The defence now acts in play where it used to wait.
5. **Nothing in the exam is unbuilt any more, but more of it fails:** 22 pass, 3 for you to judge, 25 fail. Passing now that didn't: D12, A8. Failing now that passed: D11, G2, G5, A7.
6. **The cause is now clear, and it is a design question, not a bug** (section 3).

## 3. The one thing to decide first

The design's sum is V = p1 v1 + (1 - p1) p2 v2 + ..., each look at "its chance of being open in time". In Playmaker, movement has no dice. Once the defence's answer is fixed, a look is open or it isn't. The only chances in the engine are the rules' own: a pass landing, a Dribble winning, a Steal. So on most boards every p is 1 and the sum collapses to its single best look. Everything the design expects to "fall out" (how far a defender sags, who helps, where the offence spreads) lives in the looks below the best one, and the number doesn't see them.

Part C's answer is the list as tie-break (D-303): level on the number, compare every look best first. That makes the defence care about every look, in order. It moved things, but not to basketball: it makes defenders tight on everyone (G2 and A7 now fail: the defender of a non-shooter stands as close as the defender of a shooter), because a tie-break has no sense of "a little off a big look is worth more than a lot off a small one".

The options, as I see them:
- **(a) Give "open in time" a real chance.** For example, a look's chance falls with each defender who could still get there, by how many actions it would cost him. That is a model you would have to rule on: it is new, and it is not in the rules.
- **(b) Sum the looks, with a fixed fall-off.** The second look counts some share of the first, and so on. Simple, but the share is a hand-set weight (D-156 forbids it unless you set it).
- **(c) Keep the number as it is for shoot-or-play-on (it is right there: O1, the mix), and put shape back on a measure that adds over looks:** the weight map's "weight left after cover", summed. The defence minimises weight left; the offence maximises it. That is two measures, which the design's check B1 forbids, so it too needs your ruling.

I'd take (c) for the setups only, because the weight map is already built, in both engines, in points, and it adds. But it is yours to rule.

## 4. The merge conditions

**One think fits in a phone's browser: yes.**

| Think | Before | Now, held to 256 MB | Same decision |
|---|---|---|---|
| An All-Star turn on the 20 November board (the offence, one turn ahead) | 1.95 GB; failed outright at 1 GB | Runs. 289 MB in all, 33 s (27 s unheld) | Yes |
| The widest turn in the exam (E21, every pass denied) | Over 1.4 GB | Runs. 308 MB in all, 57 s (51 s unheld) | Yes |
| A defence setup (E1) | About 1 GB | Runs. 240 MB in all, 10 s | Yes |
| A defence setup (E3, the longest) | Not measured | Runs. 324 MB in all, 138 s | Yes |
| An offence setup (E15b) | About 1.2 GB | Runs. 282 MB in all, 41 s | Yes |

What held the memory: three stores of whole readings, each kept by count with no thought for size (2,000 one-think readings, 6,000 remembered readings, 8,000 reach maps), and two geometry stores with no limit at all. Each is now two small generations (D-301). Bigger stores gave no speed back.

**Every exam check passes or fails for a reason that is yours: no.** 25 fail. Section 6.

## 5. The design, section by section

Built means the build does what the section says. Built differently means it does something else, with the reason. Not built means it isn't there.

| The design's section | Status | What the build does |
|---|---|---|
| **The game in brief** (the glossary) | Built | Rules as in `RULES_CURRENT.md`. Differences between the document and the rules are listed in section 7 |
| **Why this design:** one currency | Built | Every comparison is in points on the game's scale. No hand-set weight was added. What is left that is hand-set is listed in section 8 |
| **Why this design:** it depends | Built | No special term for a trap, a packed key, denial, a stack or spacing. Where a check needed one, the check fails |
| **Why this design:** every claim has a check | Built | 50 checks, all built, in `tests/test_exam.py` |
| **The one number:** the possession's value | Built | One number, both engines, the same on all 46 boards |
| The weight map and what the stances take off | Built | `weightMap`; `possRead` |
| One look, on the 1 to 39 scale; turnovers and fouls at 5 | Built | By the rules: a contest at least 1, a shot never below 0 |
| A look's chance of happening | **Built differently** | The pass's and the Dribble's chance by the rules. Movement has no dice, so "open in time" is yes or no (section 3) |
| Combining looks: the sum, best first | **Built differently** | One route for each attacker (his best look), a pass or Dribble at its chance, a lost pass at minus 5 and the phase. With most chances at 1 the number is its best look; the looks below it are the tie-break (D-303). Section 3 |
| Looks that share a cause read as one route | **Built differently** | Routes are by attacker, not by cause. A screen that frees two men is two routes |
| Costs and gains at their chance | Built in part | Turnover, three seconds, the closely guarded count: yes. A foul drawn: only through the block's foul risk |
| Tries cost actions | Built | A route is limited by the actions it needs (D-294) |
| **Later answers cost actions too** (the new ruling) | Built | D-302. A shot this turn faces no movement; after a pass, a Dribble or a second action, two for each turn handed over; plus what is left of the defence's own turn. **Differently in one way:** phases after this one face the whole answer |
| Reading ahead, up to four turns | **Built differently** | The value reads every phase left by its own sum. The turn search looks one turn ahead at every level. Two turns took 17 to 324 seconds a turn when measured (Part B), so four is out of reach until the readings are much cheaper |
| **How each side chooses.** The defence: map, base positions, improve, check | Built, with two differences | Steps 1 to 3 as written (step 3 now looks at every square within three of his man or on his line). Step 4: each defender's line and what the offence gains if he is lifted are reported; there is no sentence explaining a defender who is off his line. And "each time it takes a turn": in play the defence chooses among its legal turns by the number; it doesn't rebuild base positions |
| The offence in play: shoot if the shot beats playing on; else the best 1 or 2 actions; a fake as a mix | Built | O1 pass. One turn ahead |
| Separate thinking | Built | B3 pass |
| The levels: a fixed number of turns, never a clock | Built | One turn at each level; they differ in width, noise and attention |
| **Part 1, layer 1:** the points a contest saves | Built, one difference | Uncontested less the best set contest in front. A block is read only against a rushed shooter; the fake against a shooter in control is not a mix inside the map (the hold's value is used) |
| The base map and the base centre | Built | `weightBase` |
| Layer 2: occupation by segment | Built, provisional | `data/segments.json`. Part B's trial: the three open choices changed no check |
| Whose contest | Built | Best of five for the map, his own for a defender's base position |
| Layer 3: can the ball get there | Built in part | The pass's and the Dribble's chance by the rules. "Room to use a skill advantage" is not a separate factor |
| The map leads; covered weight pulls less; the map moves every turn | Built | `left` is the weight after cover. Read afresh each time; not read ahead |
| **The centre of gravity keeps the defence goal-side:** the base position | **Built differently** | On the line from his man to the heaviest group of weight that isn't his own man's. Not checked: that he can reach it in time, or that no teammate already covers it |
| When the weight moves, the right side moves | Does not happen | G3 fail |
| The search starts from this shape | Built | And still ends somewhere else from another start: G4 fail |
| The ball shades it | Not built as a step | Left to the search |
| **Part 2:** three jobs (his man, the ball, the gaps) | Built as readings | `own` in the weight map; the ball and the gaps through the number |
| The link rule | **Built differently** | Not each defender's own comparison. The five are solved together (as the design says) and what the offence gains if a defender is lifted is reported as the check (D12 pass) |
| No weighting needed | Built | Points throughout |
| Who covers the man he leaves; the cost of getting back; one danger after another | Built in part | The cost of getting back is the new ruling (actions are counted). The pass to the man he left is in the routes. A rotation chain is whatever the answer's one-at-a-time movements find |
| Solved together; cover in degrees; the ball's reach once | Built | |
| Pairs: two swapping men, and a second defender to the ball with his own man read as left | Built in part | Swaps are tried. A second man going to the ball is tried as a single move (his man is then read as left, by construction), not as a pair |
| **Advantages are gaps:** speed, the dribble, the pass | Built | The race; the value behind at the Dribble's chance; layer 3 |
| Contained by distance, direction, help | Left to the number | A7 fail |
| The matchup rule prices this at setup | **Built differently** | The new setup tries swapping men by the number. Step 23's matchup table is not read |
| **The pass makes gaps:** closeout, a miss, a fake, a stop; the gamble | Built | A11 pass, A12 pass, A13 pass |
| **Part 3:** what the arrows do | Built | The rules, unchanged |
| How the arrows are chosen: square and pair together, by points | Built at the setup | Every pair on every square read in full. In play arrows now turn when that takes something off the list (D-303) |
| Three things the arrows weigh | Left to the number | A8 pass, A9 fail, A10 fail |
| What should fall out (on the ball, one pass away, far, post, trap, no hugging) | Mostly does not | A1 fail, A2 fail, A3 pass, A5 fail |
| When denial pays | In part | A14 fail, A15 pass, A16 pass, A17 pass |
| Its effect on the offence (help distance to the zone; a screen worth the arrow it removes) | In part | A4 pass. Help distance is not measured |
| **What should fall out for the defence** | In part | Packed key: for Shaun. Box-and-one: fail. Mid-range: pass. Sag off a far non-shooter: pass. Tight on a shooter in control: for Shaun. Follow past the arc: fail. The arc when a three is needed: for Shaun |
| **The trap,** judged with the trapper gone | **Built differently** | No trap reading of its own. A second defender going to the ball is an ordinary turn, read on the board as it would be. It doesn't appear: D8 fail, D9 pass |
| **The offence:** the value of a setup | **Built differently** | The possession's value against the defence's quick answer, the list as tie-break; the best two against its full answer |
| The six variables | Built in part | What each attacker can score (the scout) and time (actions and phases) are in. Pin is reported (the lifted reading), not used. Help distance, access and room are not measures |
| The push and the pull; three principles as counted costs | Not built as costs | Left to the number, and they don't show: O3 fail, O5 fail |
| How many actions at once | Not built | Left to the turn search, which takes the one best thing: O6 fail, O9 fail, O10 fail |
| The setup order, steps 1 to 6 | Built in part | 1: the scout reads each card's shooting marks by segment (not his dribble, screens or the defence). 2: three starts for each possible ball handler. 3: best segments, improved one man at a time. 4 (secondary skills break ties): not built. 5 (the plan's conditions): not built; no plan is named. 6: the improvement loop only |
| The five situations | Built, and failing | Inbounds now run (the inbounder fixed, four placed round him): O6 fail, O7 fail, O8 fail. The top: O3 fail, O9 fail, O10 fail |
| **What this changes:** replaced | Built, one gap | The value leads; the list is display and tie-break. "Spacing counted directly (crowding, wasted pins, help distance)": not built |
| Kept, and used as inputs | Built | The race, the pass's danger, the bar counted by the rules, three seconds, the contest as an action, blocks, fakes, the pivot, deep range, separate thinking. The four-turn read-ahead: see above |
| Fixes: take the good shot; three seconds from entry; no action without a purpose | Built | O1 pass, O2 fail, O11 pass |
| **A worked example** | Not run | The example's board was not built as a check |
| **What the player sees** | Built in part | The weight map and its centre in the Coverage view: yes. Each defender's line: in the setup's words. The number as the phase score: shown with the Coverage view. The offence's line and the coaching tips still speak from the old list |
| **Board checks** | Built | Section 6 |
| **The ledger and the rulings** | As Part B's report | Changed since: "later answers" built; the inbound rows now run |

## 6. The exam, check by check

22 pass (D3, D4, D9, D10, D12, O1, O4, O11, O12, B1, B2, B3, A3, A4, A6, A8, A11, A12, A13, A15, A16, A17). 3 for Shaun (D1, D5, D7). 25 fail (D2, D6, D8, D11, O2, O3, O5, O6, O7, O8, O9, O10, B4, G1, G2, G3, G4, G5, A1, A2, A5, A7, A9, A10, A14).

Against Part B: now passing, D12, A8; now failing, D11, G2, G5, A7; changed otherwise, O6 (not built to fail), O7 (not built to fail), O8 (not built to fail).

| Check | Board | Result | What the computer did | How it fails without the principle |
|---|---|---|---|---|
| D1 | E1 | **for Shaun** | The weight's centre is on H6 (in the key). 1 of 5 defenders stand in or touching the key: X1 M8 (1 off O3); X2 E8 (1 off O2); X3 G10 (1 off O1); X4 D5 (2 off O4); X5 I5 (7 off O5). Value 14. The defence stays out: on these cards an open three from a 7 is worth 21, more than the rim gives against the Rim Protector, so packing the key would raise the number. | With the weight map built from the Five Out cards (E3) the arc carries more weight and the centre moves out. |
| D2 | E2 | **fail** | Nobody stands next to the Sharpshooter (O2); the other four: X1 F10 (2 off O1); X2 M8 (1 off O3); X3 B7 (1 off O2); X4 D4 (2 off O4); X5 I5 (7 off O5). On E1 (O2 a 7 shooter): X1 M8 (1 off O3); X2 E8 (1 off O2); X3 G10 (1 off O1); X4 D5 (2 off O4); X5 I5 (7 off O5). | Swap O2 back to the Playmaker SG C (that is E1) and his defender must be no closer. |
| D3 | E4 | **pass** | O2's open mid-range shot on L6 is worth 27. The defence's turn: X2 Quick Step to H4 (value 33; 24 of its 24 turns read the same). The card table is in the report. | The turn is the one that leaves the lower value: every turn the defence has is read, and none reads lower. |
| D4 | E5 | **pass** | O5 (a non-shooter) stands in the far corner; X4 stands 3 squares off him, on O7, toward the key. | NOT CONFIRMED. With the Sharpshooter in that corner (E5b) his defender stands 7 off as well: the ball is on the far wing, so the sag comes from how seldom the pass across lands, not from O5's card. This board can't tell the two apart. |
| D5 | E6 | **for Shaun** | X2 starts 4 away from the Sharpshooter (three empty squares). The defence's turn: X5 Move to P3 facing N then X1 Move to G8 facing W (value 30; 24 of its 24 turns read the same). X2 ends 3 squares off him. By the rules as read he can't take the shot away this phase: only a Sprint reaches O2, and a Sprint leaves his contest rushed, so O2's shot now is worth 30 wherever X2 ends the turn. Standing two squares nearer lowers what playing on is worth (26, not 30), but the shot now is the bigger number, so no turn reads lower and he stays. | With X2 placed two squares off by hand the value is 27 (he contests in control); from three or more off it is 30. |
| D6 | E7 | **fail** | O2 stands two squares past the arc. At Senior Pro (deep range open) his defender is 6 off him; at Junior (none open) 5 off. | Only the level changes between the two readings. |
| D7 | E8 | **for Shaun** | Need a three, last phase: a two is worth 0. Every look beyond the arc weighs 18 to 26.6; every look inside it 4.5 (a shot worth nothing still beats the shot clock running out, minus 5, and a block takes that away). No defender stands in the key: X1 B9 (0 off O2); X2 N5 (2 off O5); X3 B6 (2 off O4); X4 M9 (1 off O3); X5 H9 (1 off O1). The check as written wants the map's centre at the arc. The centre is the balance point of the weight, and weight spread round the arc balances inside it, on G6. So the map moved to the arc and the defence went with it, but the centre as defined can't sit on the arc. | With a two worth 2 again (E3) the key carries the most weight. |
| D8 | E9 | **fail** | O3 has the ball in the corner, his dribble dead, three passes denied. The defence's turn: X1 Move to L6 facing N then X3 Steal (value 17.4). 1 defender(s) end next to him: the defence reaches for the ball with the one already there and sends no second man. | On E10 (a good passer, open lanes) no second defender goes. |
| D9 | E10 | **pass** | A good passer at the top with open lanes. The defence's turn: X2 Move to D8 facing N then X1 Move to I7 facing W. 0 defender(s) next to the ball. | On E9 a second defender goes. |
| D10 | E11 | **pass** | O1 has driven to J5; X1 is beaten. The defence's turn: X1 Sprint to G11 then X2 Move to O2 facing N (value 24; 15 of its 24 turns read the same, and none reads lower). Every turn's value is the offence's best route after it, the pass out to the man a helper left among them. | The value of helping includes the pass out to the man left: the routes are every attacker's best look, each with the pass that reaches him. |
| D11 | E12 | **fail** | Two bigs under the rim (O4 G3, O5 K3). Nearest defender: O4 3 away, O5 1 away. X1 M8 (3 off O1); X2 I8 (5 off O3); X3 D6 (2 off O2); X4 D4 (2 off O4); X5 J3 (0 off O5). | Lift either big's defender and the value rises (D12 reading). |
| D12 | E1 | **pass** | Each defender lifted in turn, the offence gains: X1 +7, X2 +1, X3 +4, X4 +1, X5 +20. | A defender whose removal changes nothing saves nothing where he stands. |
| D12 | E3 | **pass** | Each defender lifted in turn, the offence gains: X1 +6.19, X2 +5.56, X3 +9.19, X4 +6.19, X5 +6.19. | A defender whose removal changes nothing saves nothing where he stands. |
| D12 | E12 | **pass** | Each defender lifted in turn, the offence gains: X1 +9, X2 +5.94, X3 +6, X4 +6, X5 +8.18. | A defender whose removal changes nothing saves nothing where he stands. |
| O1 | E13 | **pass** | O4 has caught the ball under the rim, X4 late. His shot now is worth 36; playing on is worth 36. The offence's turn: O4 Move to G3 then O4 shoots (layup). | With the defence's answer left out of the number, playing on reads 38, more than the shot, and he doesn't shoot (the 20 November fault). |
| O2 | E14 | **fail** | O4 and O5 were in the key at the last phase end. The offence's first turn (six actions left): O1 passes to O3; no third man goes in. The value with both in the key is 27; with both standing just outside it is 27: the same, because with six actions left the two they must spend to leave come off nothing the best route needs. The last turn (two actions left): O1 passes to O3 (value 27); they are still in the key and no shot is declared. | The action each must spend to leave comes off the actions a route may use; the count is made once, at the phase end. |
| O3 | E15 | **fail** | Five Out sets up: O1 C13 (WL), O2 C8 (WL), O3 A2 (CL), O4 O8 (WR), O5 G5 (MM), the ball with O1. Value 21.654 against the defence's full answer. | Two in one segment hold one defender: the value against the answer is lower (read in the report). |
| O4 | E15b | **pass** | Shoot and Protect sets up: O1 A2, O2 C8, O3 O8, O4 I13, O5 H2. The Rim Protector centre (three 5) starts on H2. | His only shot that is average or better on his card is at the rim, so that is the one place that demands a defender. |
| O5 | E16 | **fail** | O5 stands in O1's lane to the rim. The offence's turn: O1 Sprint to M9 then O1 Dribble (value 25.05). O5 ends on I6: he does not clear the lane. O1 goes round the other way instead. | With O5 left in column I the drive is blocked and the turn's value is lower. |
| O6 | E17 | **fail** | Inbound from the baseline, under the rim: O3 puts the ball in on K0; the four: O1 F10 (T), O2 A2 (CL), O4 C8 (WL), O5 H2 (G). Value 6.6766 against the defence's answer. The offence's first turn: O3 passes to O5 (value 21.6). 1 of the four start in or touching the key; the turn runs 0 off-ball action(s). | The same teams from the corner (E18) and the sideline (E19). |
| O7 | E18 | **fail** | Inbound from the corner: O3 puts the ball in on B0; the four: O1 F10 (T), O2 A2 (CL), O4 C8 (WL), O5 H2 (G). Value 7.9231 against the defence's answer. The offence's first turn: O5 Move to K2 then O3 passes to O2 (value 21). The four are in four different segments; the turn runs 2 action(s). No fall-back is named: the setup returns no plan. | The same teams from under the rim (E17). |
| O8 | E19 | **fail** | Inbound from the sideline near half court: O3 puts the ball in on R12; the four: O1 F10 (T), O2 A2 (CL), O4 C8 (WL), O5 H2 (G). Value 6.3075 against the defence's answer. The offence's first turn: O5 Move to J2 then O3 passes to O5 (value 16). The turn runs 2 action(s). | The same teams from under the rim (E17). |
| O9 | E20 | **fail** | Last phase: O1 H2, O2 O13, O3 A2, O4 C8, O5 G5 (the squares between the five add up to 77; with a full clock 86: closer together). Against the defence's own setup the offence's turn is: O2 Move to Q12 then O2 Quick Step to Q11 (value 20.57): 1 player(s) act. | The same teams with a full clock are E15. |
| O10 | E21 | **fail** | Every pass is denied. The offence's turn: O3 Screen (value 26). | A turn has two actions: two off-ball actions at once is the most one turn can run. |
| O11 | E21 | **pass** | The turn chosen (O3 Screen) is worth 26; without it (waiting) 24. | A screen or cut is chosen only if it raises the value: equal values go to the turn with fewer actions. |
| O11 | E22 | **pass** | The turn chosen (O3 Screen) is worth 32; without it (waiting) not read. | A screen or cut is chosen only if it raises the value: equal values go to the turn with fewer actions. |
| O12 | E22 | **pass** | O1 has the ball on I13 with no shot there. The offence's turn: O3 Screen (value 32). He ends on I13: he stays this turn because that turn is worth more than his best step in (27.65). | From I13 he has no look; a turn that leaves him there is chosen only when it is worth more than every turn that moves him in. |
| B1 | E3 | **pass** | The setups, the end of every line the search reads, and the tie order all read the possession's value (possParts); the list and the lasting gap rank nothing when eval.map_lead is "value". The coach's lines and the phase score: see the report (stage 5 is partly built). | Set eval.map_lead back to "list" and the old reading leads again. |
| B2 | all | **pass** | Python and JavaScript give the same value, the same bar, the same answer and the same weight map on all 46 boards (docs/runs/step31/both_value.json, both_weight.json). The setups are the JavaScript engine's only. | Any difference fails tools/step_31.py both and bothweight. |
| B3 | E9 and E13 | **pass** | Through the agents the app plays with: the defence's choice on E9 with the offence holding its own plan, a different plan and no plan: X1 Move to L6 facing N, X1 Move to L6 facing N, X1 Move to L6 facing N. The offence's choice on E13 with the defence holding two different sets of matchups: O4 Move to G3, O4 Move to G3. The new setups are handed the board, the cards and the rules only. | tests/test_exam.py runs this live (the old test took 14 minutes on a full board). |
| B4 | the 20 November possession | **fail** | Played once, All-Star against All-Star, from its setup (the cards are the best reading of the record, so it is not the same possession). Three seconds called: no. A better shot than playing on, not taken: no. Screens set: phase 5 O1 Screen, phase 5 O1 Screen, phase 6 O1 Screen, phase 6 O1 Screen. The ball handler past the arc with no look at the start of an offence turn: phase 1 on I11. Phase by phase in the report. | Each of the five faults of 20 November is looked for in the record of the play. |
| G1 | E3 | **fail** | 4 of 5 defenders stand nearer the rim than their men: X1 C10 (0 off O2); X2 I9 (1 off O1); X3 D5 (2 off O4); X4 I5 (5 off O3); X5 P6 (2 off O5). Each defender's line is in the report. | From a shape above their men the search must come back to the hoop side (G4). |
| G2 | E3 | **fail** | O2's defender stands 0 off the Sharpshooter and 0 off the Playmaker SG C (three 7) on the same square. | Only O2's card changes between the two readings. |
| G3 | E8 | **fail** | With only a three worth anything, 2 of 5 defenders stand level with or above their men: X1 B9 (0 off O2); X2 N5 (2 off O5); X3 B6 (2 off O4); X4 M9 (1 off O3); X5 H9 (1 off O1). They close up on their men (on E3 they stand 0, 1, 2, 5, 2 off; here 0, 2, 2, 1, 1) but stay on the hoop side. | The same teams and squares with normal worth are E3. |
| G4 | E3 | **fail** | From the base positions: C10 I9 D5 I5 P6 (value 17.8137). From every defender above his man: F9 L8 B7 H4 N5 (value 17.6). | If the two differ the search is too short to be trusted without the goal-side start. |
| G5 | E23 | **fail** | Two equal looks. Both defenders sagging: 30. One covered: 30. Both covered: 29.925. | A sum of the looks would drop when one is covered; the number does not. |
| A1 | E3 | **fail** | Defenders one pass away: X1 an arrow on his man, none toward the passer; X3 no arrow on his man, none toward the passer; X4 an arrow on his man, none toward the passer; X5 no arrow on his man, none toward the passer. | Turn that arrow away and the pass to his man lands more often (A6 reading). |
| A2 | E24 | **fail** | The pass to O5 is denied by X3. The defence's turn: X1 Move to I7 facing N. X5 ends on N4 with arrows E and SE: one on O5. | An arrow on a man the ball can't reach saves nothing. |
| A3 | E3 | **pass** | X2 is on the ball on I9, arrows W and NW: chosen with his square by the value (each of the eight pairs read in full). | A6: no other pair of arrows lowers the value. |
| A4 | E25 | **pass** | O5 screens X1 on I9. With the screen on, X1 facing north and north-east reads 22; facing north-west and north reads 22: his diagonal arrow is dead either way, so turning it changes nothing. With no screen the same two stances read 20.75 and 21. | Without the Screen rule in the reading the two stances read as they do with no screen (which differ). |
| A5 | E9 | **fail** | No trap was set, so its wedges were not read. | With one defender on him he keeps a pivot square. |
| A6 | E3 | **pass** | The stance search ends only when no other pair of arrows, for any defender, lowers the value (each pair is read in full on the board as it would be). | By construction; the test turns each defender's arrows and reads the value again. |
| A7 | E26 | **fail** | On O9: the defender of the fast non-shooter (Slashing Wing) stands 0 off; of the fast shooter (Bucket Getter) 0 off. | Only the card on O9 changes. |
| A8 | E27 | **pass** | Ball on L10. Equal shooters either side: X1 on I5, arrows NW+N. The best shooter in the right corner: X4 on M9, arrows NW+N. | The stance must change when the bigger look changes sides. |
| A9 | E28 | **fail** | The defence's turn: X1 Steal (value 23.75). X5 ends on I9 with arrows SE and S; the plan's sum favours N and NE. | The plan's sum counts lanes only; the turn is chosen by the whole value. |
| A9 | E28b | **fail** | The defence's turn: X4 Move to B7 facing N then X1 Steal (value 20.98). X5 ends on I9 with arrows SE and S; the plan's sum favours W and NW. | The plan's sum counts lanes only; the turn is chosen by the whole value. |
| A10 | E29 | **fail** | The ball on N8, help behind the middle, nobody on the baseline. The defence's turn: X1 Quick Step to N7 then X3 Quick Step to J8. X1 ends on N7 with arrows NE and E. | Move the help to the baseline side and the wedge should turn. |
| A11 | E30 | **pass** | O3's defender five squares off (he must Sprint to close out): the possession is worth 22.25. One Move away: 22.2453. | Start X3 one Move away and the rushed closeout, and the drive past it, are gone. |
| A12 | E31 | **pass** | The three replies on step 30's board, worth to the offence (real, fake): go for the Intercept (19.3, 27), hold the lane (21, 21), step off (22, 18). The defence holds: 21 whatever the offence does. | Before the fix the mix took the first reply on its list, the gamble. |
| A13 | E31 | **pass** | Against a ball handler who can't fake the fake column is the real one, and the Intercept (19.3) is the reply. | With the fake open the same reply loses 6. |
| A14 | E32 | **fail** | A strong shooter (O2) one pass away, a helper by the rim. X4 stands on D8, 0 off him, not in the passing lane. | With nobody behind (E33) the denial should fade. |
| A15 | E33 | **pass** | The same shooter with nobody near the rim. X2 stands on D8, 0 off him, not in the passing lane (value 19.69). | The cut behind a denier is read as any other look. |
| A16 | E3 | **pass** | Five shooters spread. Defenders in or touching the key: X4. | With every defender out on his man the paint is empty and the value of a cut rises. |
| A17 | E32 | **pass** | From the defence's own setup the possession is worth 21. O2's best Move is from C9 to F9: the value reads 28, with the defence's answer to the new board inside it (it stays as it stands). | Every Move of his is read on the board as it would be, the defence answering afresh: F9 28, D9 22.25, E9 22.1875, A10 21, A11 21. |

## 7. Where the document and the rules differ

The rules won each time.

- **The low end of the scale.** The document says a contest is always at least 1. The rules say that for the app's contest by position; at the table the minus 3 never takes a contest below 0. Built by the rules. (Still for Shaun to confirm he wants no change.)
- **"Open in time" as a chance.** The document reads each look at a chance. The rules roll dice only for passes, Dribbles, Steals, Intercepts, Challenges and shots. Movement is certain. Built by the rules (section 3).
- Nothing else found. The glossary's other terms match `RULES_CURRENT.md` as checked: turns of 1 or 2 from 6, locked and the Quick Step, rushed, the wedge never blocking a pass, the contest by position (3 less, 6 less), the block's foul rolls, a missed Intercept and a missed Steal.

## 8. What it proves, and what is hand-set

- Both engines, the value, the bar and the defence's answer: 46 of 46 boards the same (`tools/step_31.py both`).
- The cuts inside the value against every movement read in full: 712 boards, the value the same on all 712. On 9 the full reading's answer has one more movement that leaves the number unchanged. So the cut is proven for the number and not, any more, for the last value-neutral movement of the answer.
- Memory: the table in section 4 (`docs/runs/step31/memory.json`).
- Times on the exam's boards, three readings side by side: a defence setup 37 to 163 s (middle 91 s); an offence setup 26 to 168 s (middle 91 s); the turn search 3 to 96 s (middle 5 s). Still not playable for speed: the goal was a minute a setup and 20 seconds a turn.
- The 20 November possession, section 9.

**Hand-set or limited, each listed:** the stores' sizes (D-301: speed and memory only, never a decision); the setup search's reach (three squares from his man, the best five squares read in full: a cap, not trialled in this part); the offence setup's three areas a player and two finalists (Part B's trial: no change when doubled); the turn search's width (8, 16, 24: Part B's trial changed two boards); the defence's answer built one movement at a time; lumps joined within two squares; the levels' noise, variety and goal margin (as ruled). The list tie-break for level turns is in the JavaScript engine only; the Python engine's turn search still uses D-300 alone (the app plays on the JavaScript engine).

## 9. The 20 November possession

Replayed once, seed 20, All-Star against All-Star, in one engine process held to 300 MB (the app's way: one long-lived engine). 71 actions in 1163 seconds. The engine's memory peaked at 375 MB. It ended on a turnover in the last phase; the possession scored -10 on the game's scale (3 turnovers, 1 foul). The longest single think took 400 seconds.

**Phase 1** (shot clock 12). O: K4 I2 N6 I11 Q3, the ball with O4. X: K3 N7 I10 J4 H4.
- Offence: O1 Move to I5. [33.9 s]
- Offence: O5 Move to O1. [0.0 s]
- Defence: X4 Move to H2 facing N. [4.2 s]
- Defence: X2 Move to M7 facing N. [0.0 s]
- Offence: O1 Quick Step to J6. [31.2 s]
- Offence: O4 passes to O1. [12.3 s]
- Defence: X Pause. [3.5 s]
- Offence: O3 Move to O7. [102.3 s]
- Offence: O ends the turn. [11.5 s]
- Defence: X1 Sprint to N6. [1.8 s]
- Defence: X3 Move to J10 facing N. [0.2 s]
- Offence: O1 passes to O2. [0.5 s]
- Defence: X5 Move to H3 facing N. [4.1 s]

**Phase 2** (shot clock 10). O: J6 I2 O7 I11 O1, the ball with O2. X: N6 M7 J10 H2 H3.
- Offence: O1 Sprint to F6. [15.4 s]
- Offence: O2 passes to O1. [4.5 s]
- Defence: X2 Move to M4 facing E. [5.5 s]
- Defence: X5 Move to F5 facing N. [0.0 s]
- Offence: O1 Dribble (failure). [8.7 s]
- Defence: X1 Quick Step to N7. [4.2 s]
- Defence: X3 Move to H8 facing W. [0.0 s]
- Offence: O2 Move to H4. [10.4 s]
- Offence: O1 passes to O2. [1.0 s]
- Defence: X1 Move to M6 facing SW. [11.8 s]
- Defence: X4 Move to I3 facing N. [0.0 s]

**Phase 3** (shot clock 8). O: F6 H4 O7 I11 O1, the ball with O2. X: M6 M4 H8 I3 F5.
- Offence: O2 Move to H3. [399.6 s]
- Offence: O2 passes to O1. [49.6 s]
- Defence: X1 Quick Step to M7. [6.5 s]
- Defence: X3 Move to H5 facing S. [0.0 s]
- Offence: O1 passes to O4. [97.7 s]
- Defence: X Pause. [0.2 s]
- Offence: O1 Move to F7. [2.8 s]
- Offence: O4 Move to I10. [0.6 s]
- Defence: X1 Move to M7 facing N. [0.1 s]
- Defence: X ends the turn. [0.2 s]
- Offence: O4 Quick Step to J10. [0.4 s]
- Defence: X5 Move to G7 facing N. [7.5 s]
- Defence: X2 Move to N4 facing S. [0.0 s]

**Phase 4** (shot clock 6). O: F7 H3 O7 J10 O1, the ball with O4. X: M7 N4 H5 I3 G7.
- Offence: O3 Move to M6. [42.5 s]
- Offence: O4 passes to O3. [4.8 s]
- Defence: X1 Move to M9 facing S. [4.4 s]
- Defence: X5 Move to E8 facing N. [0.0 s]
- Offence: O2 Move to G4. [46.4 s]
- Offence: O2 Quick Step to F5. [0.0 s]
- Defence: X2 Quick Step to N5. [4.4 s]
- Defence: X Pause. [0.9 s]
- Offence: O3 Dribble (failure). [40.9 s]
- Defence: X2 Move to N5 facing N. [3.9 s]
- Defence: X3 Move to G7 facing N. [0.0 s]

**Phase 5** (shot clock 4). O: F7 F5 M6 J10 O1, the ball with O3. X: M9 N5 G7 I3 E8.
- Offence: O1 Screen. [47.6 s]
- Defence: X3 challenge (failure). [3.6 s]
- Offence: O1 Screen. [45.6 s]
- Defence: X2 Move to M5 facing N. [3.4 s]
- Defence: X3 challenge (failure). [0.0 s]
- Offence: O2 Move to I5. [14.6 s]
- Offence: O Hesitate. [0.0 s]
- Defence: X2 Steal (foul). [1.6 s]
- Offence: O3 passes to O2. [17.3 s]
- Defence: X1 Move to K7 facing SE. [3.9 s]
- Defence: X3 Move to F8 facing N. [0.0 s]

**Phase 6** (shot clock 2). O: F7 I5 M6 J10 O1, the ball with O2. X: K7 M5 F8 I3 E8.
- Offence: O1 Screen. [10.5 s]
- Defence: X3 challenge (failure). [3.3 s]
- Offence: O1 Screen. [10.4 s]
- Defence: X3 challenge (failure). [3.4 s]
- Offence: O3 Move to K4. [8.1 s]
- Offence: O2 passes to O1. [1.8 s]
- Defence: X3 Move to E6 facing NE. [1.9 s]
- Defence: X3 Steal (no foul/kept). [0.0 s]
- Offence: O1 Move to I7. [0.7 s]
- Offence: O1 shoots (floater). [0.2 s]
- Defence: X1 Move to J6 facing W. [0.2 s]
- Defence: X1 Contest (blocked). [0.0 s]

**The five faults of 20 November in this record:**

- Three seconds called: no.
- A better shot than playing on, not taken: no.
- Screens set: phase 5 O1 Screen, phase 5 O1 Screen, phase 6 O1 Screen, phase 6 O1 Screen.
- The ball handler past the arc with no look at the start of an offence turn: phase 1 on I11.


## 10. Tests

About 15 minutes of testing in all: the exam's own file, the rules, the memory tests, engine equality and the golden game took 5; the rest of the suite took its full 10. No test was loosened, skipped or marked as expected to fail.

| What | Result | Time |
|---|---|---|
| The exam (`tests/test_exam.py`) | 38 passed, 26 failed. The failures are the 25 failing checks (each by its number) and the live G5 reading (covering both looks now lowers the number by 0.075, not by 1 or more: the same failure as check G5). Every other live reading passed: O1, the shot clock, A12 and A13, the mix in both engines, B2 on five boards, the full-read guard, the memory guard, B3 | 2 min 2 s |
| The rules (`test_rules_current.py`) and step 30b's memory tests | 25 passed | 26 s |
| Engine equality (`tools/js_equivalence.py`, 40 random states) | 0 mismatches | 37 s |
| Both engines on the value (`tools/step_31.py both`) | 46 of 46 boards the same | about 8 min (run once, with the exam's readings) |
| The golden game | 8 passed, no value moved, nothing re-recorded | 85 s |
| The rest of the suite: each file in its own process, 90 seconds a file, 10 minutes in all | 29 files passed, 7 failed, 15 not finished in their time, 9 not reached | 10 min |

**Re-recorded, with a note in the test:** the two live O1 tests in `tests/test_exam.py`. They asserted the shot was worth more than playing on (36 against 23.5). Under the new ruling a step and a shot in the same turn face no defensive movement, so playing on reads 36 as well: it is the same shot one square over. They now assert that playing on is never worth more than the shot, and still that the turn ends in his shot.

**The 7 files that failed** are the same seven as in Part B, for the same reasons: four fail the same way on the live code (coach_gate, computer, placement_ui, revalidated_live); `test_static.py` reads the removed thinking clock (and already failed on the live code two lines later); `test_setup_18o.py` asserts a setup keeps to its clock; `test_heat_map_20.py` expects the old reading's number.

**Not finished inside 90 seconds** (or cut off by the 10 minutes): accessibility, foul_price_18k, map_logic_21, movement, points_play_on_18r, scouting, solver, step22c, step24, step27, step28, step29, step30, step3m, step3n. **Not reached:** strength_18s, teams, timer, turns_phases, two_responsibilities_22b, ux_19, web, wedge, zone_18g.

**Passed (29):** advantage, breaking, breaking_live, contest_18j, course_boards, coverage_18s, defence, drivers_22b, fiba_18i, intercepts_mti, intercepts_oq72, lane_18q, levels_3l, off_balance_18l, position_contest_18n, receiver_denial, rolls_scoring, rulebook_nov, rules_current, rulings_3i, scenarios, screen_22b, see_the_steal_18j, setup_3k, step18p, step22, step26, step30b, step6.

## 11. For Shaun to decide

1. **Where "the chance of being open in time" comes from** (section 3). Everything else waits on this.
2. **The list as tie-break (D-303).** Is "every look, best first" what you meant? It makes the defence tight on everyone.
3. **Later phases face the whole answer (D-302).** Right, or should the phases after this one be limited too?
4. **G4.** The search still ends in different places from different starts. The design says that means it can't be trusted without its starting shape. Accept that the starting shape carries the result, or wait for a measure that adds (section 3)?
5. **Speed.** Memory is fixed. Time is not: a setup is still one to three minutes.
6. From Part B, still open: the low end of the scale; the segments; D1, D5 and D7; the tie rule D-300; the block's reset; the two tests whose premise went with the clocks; the 20 November cards.

## 12. Noticed, not touched

- The fake's mix (the defence's reply to a shot or pass that may be a fake) reads every reply twice with no clock. It took over nine minutes in Part B's possession; the longest think in this part's replay is given in section 9.
- The Plan panel and the coach's lines still speak from the old list.
- The value's answer moves a defender's contests, not the drives he walls or the lanes he cuts; those change only when the board is read again after he has moved.

## 13. Model for the next step

Claude Fable 5.2, effort high. The next step turns on a design ruling and then deep work in the same engine code.
