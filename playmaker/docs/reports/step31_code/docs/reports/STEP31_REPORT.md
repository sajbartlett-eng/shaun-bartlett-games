# Step 31 Part B: the build. Report

**Not merged.** 20 of the 50 exam checks fail because the build doesn't yet do what the design says, 3 are not built, and one turn of the computer's thinking needs 2 GB of memory or more. The prompt's merge rule says don't merge in that case, so the work is on branch `step-31`, no pull request was opened, the site was not rebuilt and the live site is unchanged. What failed, what was tried and the cause are in sections 3 and 4.

## 1. Changes to the printed game

None. No rule and no card changed (D-190). The rules register gained one app-only line (the two arrows a defender has, ruling 7); `RULES_CURRENT.md` was regenerated from it.

## 2. In five lines

1. Both computers now read one number: what the possession is worth to the offence from here, with the defence's answer inside it. It is the same number in both engines on all 46 exam boards.
2. The cutter under the rim now shoots (O1). Covering one of two equal looks no longer moves the number (G5). The defence holds a lane when holding is level with the gamble (A12, A13). Standing still wins a level tie, so nobody moves without a reason.
3. The clocks are gone from the computer's thinking. A level is a fixed number of turns ahead. The same board gives the same decision on any device.
4. The exam exists: 50 checks, each with a board and a verdict. Today: 24 pass, 3 fail as written for a reason that is yours to judge, 20 fail, 3 not built.
5. It is not ready to play. The setups place players by the new number but land in shapes a coach wouldn't choose (defenders above their men, two attackers on one wing), in play the defence often reads every turn as level, and one turn's thinking needs 2 GB of memory or more. Don't judge it by playing yet; judge the exam table.

## 3. Why it is not merged: four causes, and memory

The failed checks come down to four causes. Each is a cause in the build, not in the cards.

**Cause 1. The defence's setup search stops early (G4, and behind it G1, G3, A1, A8, A14, D2, D6).** The search moves one defender one square at a time (and tries pairs swapping), keeping a change only when the number drops. Check G4 is the design's own test of that: start from the goal-side shape and from a bad shape, and both must end in the same place. They don't (16.8 against 18). So the search can't be trusted without its starting shape, and the shapes it ends in are whatever was nearest the start. What was tried: starting from each defender on the line from his man to the heaviest weight that isn't his own man's, a first pass that plays the defence's own best answer for free, then the square-by-square pass, then pairs. Widening the square-by-square pass from one square to two is in the caps table (section 9): it changes the answer, which confirms the search is the limit. The fix is a wider search, which is a speed problem first: a defence setup already takes 11.6 to 166.8 s (middle 64.2 s).

**Cause 2. In play the defence reads most of its turns as level (A2, A9, A10, D8, A5, and D5).** The number has the defence's answer inside it: at the end of the defence's turn, the offence's best route is read with the defence free to answer it afterwards. So turning an arrow now, or stepping across now, reads the same as doing it later, and "wait" is level with nearly every turn (on E6, all 24 of the defence's turns read 30). With standing still winning level ties, the defence waits. That is right when nothing is gained, and it removed the pointless moves, but it also means arrows are never turned in play, no second man goes to a trapped ball handler, and a helper's arrows stay where the setup left them. What would fix it is reading the defence's turn against what the offence does next with only the actions the defence then has left, turn by turn, further ahead than one turn. That is the look-ahead, and the look-ahead is one turn (section 9).

**Cause 3. The offence's setup shares a wing and the inbound setups are not built (O3, O6, O7, O8, and O9, O10 partly).** The setup scouts each attacker's best areas from his card, tries the ball handler in three starts, and improves one attacker at a time against a quick defence. Five Out ends with two attackers on the left wing and the ball handler deep at C13. The design's counted cost for sharing a segment is not a term in the build (rule 5 forbids a special term; the value was meant to show it, and against the quick defence it doesn't). Placing four players around a fixed inbounder was not built: the plan's risk 10 said to stop on those checks if it grew large, and it did, because the value has no reading yet for an inbound pass as the first route.

**Cause 4. The offence's turn takes the best single thing, not several at once (O5, O10, O2).** With a teammate in his lane, the ball handler goes round the other way and the teammate stays (O5). With every pass denied, one screen is set, not two actions at once (O10). With two men in the key and six actions left, the number doesn't yet carry the cost of leaving, because spare actions cover it (O2). These are the look-ahead again: one turn ahead, a two-step idea never shows its second step.

D12 fails on one board of three: on E12 lifting X4 changes nothing, because the others' answer covers what he was guarding. On E1 every defender saves 1 to 4; on E3, 7 to 13.

B4, the played possession, shows two of the five faults of 20 November again: six screens were set without a reading that each one raised the number, and the ball handler stood on I11 with no look at the start of three phases (section 5).

**And a fifth thing that would block the merge on its own: memory** (section 9).

## 4. The exam, check by check

24 pass (D3, D4, D9, D10, D11, O1, O4, O11, O12, B1, B2, B3, G2, G5, A3, A4, A6, A7, A11, A12, A13, A15, A16, A17). 3 fail as written for a reason that is Shaun's to judge (D1, D5, D7). 20 fail (D2, D6, D8, D12, O2, O3, O5, O9, O10, B4, G1, G3, G4, A1, A2, A5, A8, A9, A10, A14). 3 not built (O6, O7, O8).

Every reading is the JavaScript engine's (the app's), taken by `tools/step_31_exam.py read` and judged by `judge` against the plan's own pass conditions. The setups and the turn search were read at All-Star. The exam reads the search's own best turn; in the app the All-Star then adds its pick noise and variety (section 6), so a played turn can differ from the turn shown here. `tests/test_exam.py` judges all 50 from the same readings and runs the quick ones live.

| Check | Board | Result | What the computer did | How it fails without the principle |
|---|---|---|---|---|
| D1 | E1 | **for Shaun** | The weight's centre is on H6 (in the key). 1 of 5 defenders stand in or touching the key: X1 I10 (0 off O1); X2 D8 (0 off O2); X3 M7 (1 off O3); X4 B3 (0 off O4); X5 H4 (8 off O5). Value 14. The defence stays out: on these cards an open three from a 7 is worth 21, more than the rim gives against the Rim Protector, so packing the key would raise the number. | With the weight map built from the Five Out cards (E3) the arc carries more weight and the centre moves out. |
| D2 | E2 | **fail** | X3 stays next to the Sharpshooter (O2); the other four: X1 I9 (1 off O1); X2 M7 (1 off O3); X3 D10 (0 off O2); X4 I2 (7 off O5); X5 E5 (3 off O4). On E1 (O2 a 7 shooter): X1 I10 (0 off O1); X2 D8 (0 off O2); X3 M7 (1 off O3); X4 B3 (0 off O4); X5 H4 (8 off O5). | Swap O2 back to the Playmaker SG C (that is E1) and his defender must be no closer. |
| D3 | E4 | **pass** | O2's open mid-range shot on L6 is worth 27. The defence's turn: X Pause (value 33; 24 of its 24 turns read the same). The card table is in the report. | The turn is the one that leaves the lower value: every turn the defence has is read, and none reads lower. |
| D4 | E5 | **pass** | O5 (a non-shooter) stands in the far corner; X5 stands 3 squares off him, on M3, toward the key. | NOT CONFIRMED. With the Sharpshooter in that corner (E5b) his defender stands 3 off as well: the ball is on the far wing, so the sag comes from how seldom the pass across lands, not from O5's card. This board can't tell the two apart. |
| D5 | E6 | **for Shaun** | X2 starts 4 away from the Sharpshooter (three empty squares). The defence's turn: X Pause (value 30; 24 of its 24 turns read the same). X2 ends 3 squares off him. By the rules as read he can't take the shot away this phase: only a Sprint reaches O2, and a Sprint leaves his contest rushed, so O2's shot now is worth 30 wherever X2 ends the turn. Standing two squares nearer lowers what playing on is worth (26, not 30), but the shot now is the bigger number, so no turn reads lower and he stays. | With X2 placed two squares off by hand the value is 27 (he contests in control); from three or more off it is 30. |
| D6 | E7 | **fail** | O2 stands two squares past the arc. At Senior Pro (deep range open) his defender is 4 off him; at Junior (none open) 6 off. | Only the level changes between the two readings. |
| D7 | E8 | **for Shaun** | Need a three, last phase: a two is worth 0. Every look beyond the arc weighs 18 to 26.6; every look inside it 4.5 (a shot worth nothing still beats the shot clock running out, minus 5, and a block takes that away). No defender stands in the key: X1 H9 (1 off O1); X2 N8 (0 off O3); X3 C7 (1 off O2); X4 A4 (0 off O4); X5 P3 (0 off O5). The check as written wants the map's centre at the arc. The centre is the balance point of the weight, and weight spread round the arc balances inside it, on G6. So the map moved to the arc and the defence went with it, but the centre as defined can't sit on the arc. | With a two worth 2 again (E3) the key carries the most weight. |
| D8 | E9 | **fail** | O3 has the ball in the corner, his dribble dead, three passes denied. The defence's turn: X3 Steal (value 17.4). 1 defender(s) end next to him: the defence reaches for the ball with the one already there and sends no second man. | On E10 (a good passer, open lanes) no second defender goes. |
| D9 | E10 | **pass** | A good passer at the top with open lanes. The defence's turn: X Pause. 1 defender(s) next to the ball. | On E9 a second defender goes. |
| D10 | E11 | **pass** | O1 has driven to J5; X1 is beaten. The defence's turn: X2 Move to O2 facing N (value 24; 15 of its 24 turns read the same, and none reads lower). Every turn's value is the offence's best route after it, the pass out to the man a helper left among them. | The value of helping includes the pass out to the man left: the routes are every attacker's best look, each with the pass that reaches him. |
| D11 | E12 | **pass** | Two bigs under the rim (O4 G3, O5 K3). Nearest defender: O4 1 away, O5 1 away. X1 I10 (0 off O1); X2 B7 (1 off O2); X3 N6 (2 off O3); X4 G4 (0 off O4); X5 J3 (0 off O5). | Lift either big's defender and the value rises (D12 reading). |
| D12 | E1 | **pass** | Each defender lifted in turn, the offence gains: X1 +1, X2 +1, X3 +4, X4 +1, X5 +3.4. | A defender whose removal changes nothing saves nothing where he stands. |
| D12 | E3 | **pass** | Each defender lifted in turn, the offence gains: X1 +10.19, X2 +7.19, X3 +12.57, X4 +12.38, X5 +10.19. | A defender whose removal changes nothing saves nothing where he stands. |
| D12 | E12 | **fail** | Each defender lifted in turn, the offence gains: X1 +6, X2 +9, X3 +9, X4 +0, X5 +5.33. Lifting X4 changes nothing as the board stands: the others' answer covers it. | A defender whose removal changes nothing saves nothing where he stands. |
| O1 | E13 | **pass** | O4 has caught the ball under the rim, X4 late. His shot now is worth 36; playing on is worth 23.53. The offence's turn: O4 Move to G3 then O4 shoots (layup). | With the defence's answer left out of the number, playing on reads 38, more than the shot, and he doesn't shoot (the 20 November fault). |
| O2 | E14 | **fail** | O4 and O5 were in the key at the last phase end. The offence's first turn (six actions left): O1 passes to O3; no third man goes in. The value with both in the key is 27; with both standing just outside it is 27: the same, because with six actions left the two they must spend to leave come off nothing the best route needs. The last turn (two actions left): O1 passes to O3 (value 27); they are still in the key and no shot is declared. | The action each must spend to leave comes off the actions a route may use; the count is made once, at the phase end. |
| O3 | E15 | **fail** | Five Out sets up: O1 C13 (WL), O2 C8 (WL), O3 A2 (CL), O4 O8 (WR), O5 H2 (G), the ball with O1. Value 23.1875 against the defence's full answer. | Two in one segment hold one defender: the value against the answer is lower (read in the report). |
| O4 | E15b | **pass** | Shoot and Protect sets up: O1 A2, O2 C8, O3 O13, O4 D6, O5 H2. The Rim Protector centre (three 5) starts on H2. | His only shot that is average or better on his card is at the rim, so that is the one place that demands a defender. |
| O5 | E16 | **fail** | O5 stands in O1's lane to the rim. The offence's turn: O1 Sprint to M9 then O1 Dribble (value 25.05). O5 ends on I6: he does not clear the lane. O1 goes round the other way instead. | With O5 left in column I the drive is blocked and the turn's value is lower. |
| O6 | E17 | **not built** | The computer does not yet place four players around a fixed inbounder (plan risk 10): the reading of an inbound board needs the inbound pass read as the first route, which the value does not do yet. |  |
| O7 | E18 | **not built** | The computer does not yet place four players around a fixed inbounder (plan risk 10): the reading of an inbound board needs the inbound pass read as the first route, which the value does not do yet. |  |
| O8 | E19 | **not built** | The computer does not yet place four players around a fixed inbounder (plan risk 10): the reading of an inbound board needs the inbound pass read as the first route, which the value does not do yet. |  |
| O9 | E20 | **fail** | Last phase: O1 O8, O2 I13, O3 A2, O4 C8, O5 H2 (the squares between the five add up to 86; with a full clock 91: closer together). Against the defence's own setup the offence's turn is: O2 passes to O3 (value 21): 1 action(s). | The same teams with a full clock are E15. |
| O10 | E21 | **fail** | Every pass is denied. The offence's turn: O3 Screen (value 26). | A turn has two actions: two off-ball actions at once is the most one turn can run. |
| O11 | E21 | **pass** | The turn chosen (O3 Screen) is worth 26; without it (waiting) 24. | A screen or cut is chosen only if it raises the value: equal values go to the turn with fewer actions. |
| O11 | E22 | **pass** | The turn chosen (O3 Screen) is worth 32; without it (waiting) 26. | A screen or cut is chosen only if it raises the value: equal values go to the turn with fewer actions. |
| O12 | E22 | **pass** | O1 has the ball on I13 with no shot there. The offence's turn: O3 Screen (value 32). He ends on I13: he stays this turn because that turn is worth more than his best step in (26). | From I13 he has no look; a turn that leaves him there is chosen only when it is worth more than every turn that moves him in. |
| B1 | E3 | **pass** | The setups, the end of every line the search reads, and the tie order all read the possession's value (possParts); the list and the lasting gap rank nothing when eval.map_lead is "value". The coach's lines and the phase score: see the report (stage 5 is partly built). | Set eval.map_lead back to "list" and the old reading leads again. |
| B2 | all | **pass** | Python and JavaScript give the same value, the same bar, the same answer and the same weight map on all 46 boards (docs/runs/step31/both_value.json, both_weight.json). The setups are the JavaScript engine's only. | Any difference fails tools/step_31.py both and bothweight. |
| B3 | E9 and E13 | **pass** | Through the agents the app plays with: the defence's choice on E9 with the offence holding its own plan, a different plan and no plan: X1 Move to L6 facing N, X1 Move to L6 facing N, X1 Move to L6 facing N. The offence's choice on E13 with the defence holding two different sets of matchups: O4 Move to G3, O4 Move to G3. The new setups are handed the board, the cards and the rules only. | tests/test_exam.py runs this live (the old test took 14 minutes on a full board). |
| B4 | the 20 November possession | **fail** | Played once, All-Star against All-Star, from its setup (the cards are the best reading of the record, so it is not the same possession). Three seconds called: no. A better shot than playing on, not taken: no. Screens set: phase 1 O1 Screen, phase 2 O1 Screen, phase 2 O1 Screen, phase 4 O1 Screen, phase 4 O3 Screen, phase 5 O1 Screen. The ball handler past the arc with no look at the start of an offence turn: phase 1 on I11, phase 2 on I11, phase 4 on I11. Phase by phase in the report. | Each of the five faults of 20 November is looked for in the record of the play. |
| G1 | E3 | **fail** | 3 of 5 defenders stand nearer the rim than their men: X1 D5 (2 off O4); X2 Q6 (2 off O5); X3 J9 (1 off O1); X4 K4 (4 off O3); X5 D10 (0 off O2). Each defender's line is in the report. | From a shape above their men the search must come back to the hoop side (G4). |
| G2 | E3 | **pass** | O2's defender stands 0 off the Sharpshooter and 3 off the Playmaker SG C (three 7) on the same square. | Only O2's card changes between the two readings. |
| G3 | E8 | **fail** | With only a three worth anything, 1 of 5 defenders stand level with or above their men: X1 H9 (1 off O1); X2 N8 (0 off O3); X3 C7 (1 off O2); X4 A4 (0 off O4); X5 P3 (0 off O5). They close up on their men (on E3 they stand 2, 2, 1, 4, 0 off; here 1, 0, 1, 0, 0) but stay on the hoop side. | The same teams and squares with normal worth are E3. |
| G4 | E3 | **fail** | From the base positions: D5 Q6 J9 K4 D10 (value 16.8055). From every defender above his man: I9 D10 G3 P6 B6 (value 18). | If the two differ the search is too short to be trusted without the goal-side start. |
| G5 | E23 | **pass** | Two equal looks. Both defenders sagging: 30. One covered: 30. Both covered: 27. | A sum of the looks would drop when one is covered; the number does not. |
| A1 | E3 | **fail** | Defenders one pass away: X1 an arrow on his man, none toward the passer; X2 no arrow on his man, none toward the passer; X4 no arrow on his man, one toward the passer; X5 no arrow on his man, none toward the passer. | Turn that arrow away and the pass to his man lands more often (A6 reading). |
| A2 | E24 | **fail** | The pass to O5 is denied by X3. The defence's turn: X Pause. X5 ends on N4 with arrows E and SE: one on O5. | An arrow on a man the ball can't reach saves nothing. |
| A3 | E3 | **pass** | X3 is on the ball on J9, arrows E and SE: chosen with his square by the value (each of the eight pairs read in full). | A6: no other pair of arrows lowers the value. |
| A4 | E25 | **pass** | O5 screens X1 on I9. With the screen on, X1 facing north and north-east reads 22; facing north-west and north reads 22: his diagonal arrow is dead either way, so turning it changes nothing. With no screen the same two stances read 20.75 and 20.75. | Without the Screen rule in the reading the two stances read as they do with no screen (on this board those two are level as well, so the board cannot tell them apart: see the report). |
| A5 | E9 | **fail** | No trap was set, so its wedges were not read. | With one defender on him he keeps a pivot square. |
| A6 | E3 | **pass** | The stance search ends only when no other pair of arrows, for any defender, lowers the value (each pair is read in full on the board as it would be). | By construction; the test turns each defender's arrows and reads the value again. |
| A7 | E26 | **pass** | On O9: the defender of the fast non-shooter (Slashing Wing) stands 3 off; of the fast shooter (Bucket Getter) 0 off. | Only the card on O9 changes. |
| A8 | E27 | **fail** | Ball on L10. Equal shooters either side: X2 on M9, arrows NW+N. The best shooter in the right corner: X2 on M9, arrows NW+N. | The stance must change when the bigger look changes sides. |
| A9 | E28 | **fail** | The defence's turn: X3 Quick Step to L6 then X1 Move to G10 facing S (value 22.25). X5 ends on I9 with arrows SE and S; the plan's sum favours N and NE. | The plan's sum counts lanes only; the turn is chosen by the whole value. |
| A9 | E28b | **fail** | The defence's turn: X4 Move to B7 facing N then X1 Steal (value 20.98). X5 ends on I9 with arrows SE and S; the plan's sum favours W and NW. | The plan's sum counts lanes only; the turn is chosen by the whole value. |
| A10 | E29 | **fail** | The ball on N8, help behind the middle, nobody on the baseline. The defence's turn: X Pause. X1 ends on M7 with arrows NE and E. | Move the help to the baseline side and the wedge should turn. |
| A11 | E30 | **pass** | O3's defender five squares off (he must Sprint to close out): the possession is worth 22.25. One Move away: 22.2453. | Start X3 one Move away and the rushed closeout, and the drive past it, are gone. |
| A12 | E31 | **pass** | The three replies on step 30's board, worth to the offence (real, fake): go for the Intercept (19.3, 27), hold the lane (21, 21), step off (22, 18). The defence holds: 21 whatever the offence does. | Before the fix the mix took the first reply on its list, the gamble. |
| A13 | E31 | **pass** | Against a ball handler who can't fake the fake column is the real one, and the Intercept (19.3) is the reply. | With the fake open the same reply loses 6. |
| A14 | E32 | **fail** | A strong shooter (O2) one pass away, a helper by the rim. X1 stands on E8, 1 off him, not in the passing lane. | With nobody behind (E33) the denial should fade. |
| A15 | E33 | **pass** | The same shooter with nobody near the rim. X2 stands on D8, 0 off him, not in the passing lane (value 21). | The cut behind a denier is read as any other look. |
| A16 | E3 | **pass** | Five shooters spread. Defenders in or touching the key: X4. | With every defender out on his man the paint is empty and the value of a cut rises. |
| A17 | E32 | **pass** | From the defence's own setup the possession is worth 18.6987. O2's best Move is from C9 to B8: the value reads 24, with the defence's answer to the new board inside it (X4 to C5). | Every Move of his is read on the board as it would be, the defence answering afresh: B8 24, C6 24, C8 24, D7 24, D8 24. |

**Checks whose "fails without the principle" is weak.** D4 passes the plan's condition, but the same sag happens against the Sharpshooter, so that board doesn't separate the card from the pass. A11 passes by very little (21 against 20.93 for O3's look). D3, D9, D10 and D11 pass on boards where every turn the defence has reads level, so they show the number isn't lowered by acting, not that the defence found the right act. A3 and A6 pass by how the search is built (every pair of arrows is read at the setup), and cause 1 limits what that is worth.

**D3, the mid-range, on Shaun's cards.** On E4 the Sharpshooter's open mid-range shot on L6 is worth 27. The possession reads 33 whatever the defence does this turn, because a better look than that shot is open elsewhere. So on that board the defence doesn't close out to the elbow, and the cards say that is right there. That is one board, not a ruling on whether the cards concede the mid-range in general; that needs the setups to be trusted first (cause 1).

## 5. The 20 November possession (check B4)

The cards are my best reading of the record, so this is not the same possession. Offence: O1 Scoring Point Guard (B), O2 Combo Guard (C), O3 Scoring Small Forward (B), O4 All-Rounder Power Forward (B), O5 Post Scorer Centre (B). Defence: X1 Defensive Point Guard (B), X2 Two-Way Shooting Guard (B), X3 Defensive Small Forward (B), X4 Defensive Power Forward (B), X5 Rim Protector Centre (B). If Shaun sends the deal, B4 is rerun. A first run was stopped part-way when it showed the old list still ordering level turns (fixed, D-300); it was not used.

Played once, seed 20, All-Star against All-Star, through the agents the app uses. 59 actions in 1976.5 seconds of thinking and play. It ended: shot, 2 points; the possession scored 11 on the game's scale; 0 foul(s), 3 turnover(s).

**Phase 1** (shot clock 12). O: K4 I2 N6 I11 Q3, the ball with O4. X: K3 N7 I10 J4 H4. In the key: O1, O2.
- Offence: O1 Move to I5. Before it: shot now 8, playing on 18. [28.4 s]
- Offence: O5 Move to O1. [0.0 s]
- Defence: X1 Move to J5 facing W. Before it: shot now none, playing on 27. [3.6 s]
- Defence: X4 Move to H2 facing N. [1.4 s]
- Offence: O1 Quick Step to H5. Before it: shot now 8, playing on 21. [40.1 s]
- Offence: O2 Move to G1. [5.3 s]
- Defence: X3 Move to G9 facing E. Before it: shot now none, playing on 27. [3.5 s]
- Defence: X Pause. [0.4 s]
- Offence: O1 Screen. Before it: shot now 18, playing on 24. [5.8 s]
- Defence: X5 Move to F4 facing NE. Before it: shot now none, playing on 24. [5.8 s]
- Defence: X2 Move to O5 facing N. [0.0 s]

**Phase 2** (shot clock 10). O: H5 G1 N6 I11 O1, the ball with O4. X: J5 O5 G9 H2 F4. In the key: O1, O2.
- Offence: O1 Move to F3. Before it: shot now 18, playing on 21. [26.4 s]
- Offence: O1 Screen. [3.2 s]
- Defence: X3 Move to I9 facing NE. Before it: shot now none, playing on 24. [5.5 s]
- Defence: X Pause. [1.4 s]
- Offence: O1 Quick Step to E4. Before it: shot now 18, playing on 18. [8.4 s]
- Offence: O ends the turn. [0.9 s]
- Defence: X1 Sprint to F5. Before it: shot now none, playing on 24. [3.5 s]
- Defence: X ends the turn. [1.0 s]
- Offence: O1 Screen. Before it: shot now 18, playing on 21. [7.1 s]
- Defence: X2 Move to O5 facing NE. Before it: shot now none, playing on 27. [1.3 s]
- Defence: X1 challenge (failure). [0.0 s]
- Offence: O4 passes to O2. Before it: shot now 21, playing on 26. [12.3 s]
- Defence: X5 Move to E3 facing N. [9.8 s]

**Phase 3** (shot clock 8). O: E4 G1 N6 I11 O1, the ball with O2. X: F5 O5 I9 H2 E3. In the key: O2.
- Offence: O2 Move to H3. [53.9 s]
- Offence: O3 Move to L4. [0.0 s]
- Defence: X2 Quick Step to N5. [5.1 s]
- Defence: X5 Move to F4 facing N. [0.0 s]
- Offence: O3 Quick Step to L5. [126.5 s]
- Offence: O2 Dribble (failure). [21.4 s]
- Defence: X1 Move to E5 facing S. [8.0 s]
- Defence: X Pause. [1.0 s]
- Offence: O2 passes to O4. [73.7 s]
- Defence: X4 Move to I4 facing N. [5.9 s]
- Defence: X3 Move to K9 facing S. [0.0 s]

**Phase 4** (shot clock 6). O: E4 H3 L5 I11 O1, the ball with O4. X: E5 N5 K9 I4 F4. In the key: O2.
- Offence: O1 Move to F6. Before it: shot now 18, playing on 18. [18.1 s]
- Offence: O4 passes to O1. [11.0 s]
- Defence: X4 Move to J3 facing NE. [6.6 s]
- Defence: X1 Move to E5 facing N. [0.7 s]
- Offence: O1 passes to O2. [57.8 s]
- Defence: X Pause. [2.1 s]
- Offence: O1 Screen. [45.2 s]
- Defence: X2 Move to N5 facing N. [0.9 s]
- Defence: X ends the turn. [0.2 s]
- Offence: O3 Screen. [39.1 s]
- Defence: X5 Move to E3 facing N. [4.6 s]
- Defence: X1 Quick Step to F5. [0.0 s]

**Phase 5** (shot clock 4). O: F6 H3 L5 I11 O1, the ball with O2. X: F5 N5 K9 J3 E3. In the key: O2.
- Offence: O1 Screen. [74.1 s]
- Defence: X1 Quick Step to G4. [4.3 s]
- Defence: X1 Move to H6 facing N. [0.0 s]
- Offence: O4 Sprint to F8. [38.8 s]
- Offence: O2 passes to O3. [5.9 s]
- Defence: X3 Quick Step to J9. [3.5 s]
- Defence: X ends the turn. [1.0 s]
- Offence: O3 passes to O1. [33.2 s]
- Defence: X Pause. [1.7 s]
- Offence: O1 Move to G7. [11.7 s]
- Offence: O1 shoots (floater). [565.6 s]
- Defence: X1 Contest. [558.8 s]

**The five faults of 20 November, looked for in this record:**

- Three seconds called: no.
- A better shot than playing on, not taken: no.
- Screens set: phase 1 O1 Screen, phase 2 O1 Screen, phase 2 O1 Screen, phase 4 O1 Screen, phase 4 O3 Screen, phase 5 O1 Screen.
- The ball handler past the arc with no look at the start of an offence turn: phase 1 on I11, phase 2 on I11, phase 4 on I11.
- Defenders guarding empty space: check D12 reads this at a setup (each defender lifted in turn); it was not read at each phase start of this possession.


## 6. Stand-ins left anywhere

None of these is hidden; each is a place where something other than the possession's value, the rules or the cards has a say.

| Stand-in | Where | What it does | Status |
|---|---|---|---|
| Pick noise (Rookie 5, Starter 2.5, All-Star 0.5) | `ai_profiles.json`, `agent._choose` | A random nudge on each turn's value before choosing | Kept as ruled (answer 14): it is what makes the levels differ |
| Variety margin (0, 1, 2) | the same | One at random among turns within the margin of the best | Kept as ruled |
| Goal margin (8, 4, 1) | the same, `Commitment.choose` | How much better a turn must be to drop the goal being chased | Kept as ruled. It reads goals named by `goals.py`, which still uses two bare chances as tests (scale row 7) |
| Attention and reaction delay (Rookie, Starter) | the same | How many players a level watches; whether it sees the board late | Kept: level settings from step 3m, not touched here |
| The search keeps the best 8, 16 or 24 turns a step | `beam` in `ai_profiles.json` | Width of the turn search | A cap: on trial in section 9 |
| The defence's answer inside the number is built one movement at a time | `possRead` (engine.js), `poss_read` (value.py) | Best single movement, then the next, never two planned together | A simplification of "the defence's best answer". Exact cuts inside it are proven; the one-at-a-time order is not. Listed for Shaun |
| The defence's setup search: one square at a time, pairs by swapping | `stanceSearch` | See cause 1 | A cap: on trial; it changes answers |
| The offence's setup: three areas a player, two finalists read in full, a quick defence in between | `offenceSetup` | See cause 3 | A cap: on trial |
| Weight grouped into lumps when two entries are within 2 squares | `weightMap` | Names the heaviest lump for the base positions | A hand-set distance. Listed for Shaun |
| The old list still names goals and words | `goals.py`, `conditions.py`, `plan.py` (the Plan panel) | Words and the goal being chased | Display and the goal margin only. It ranks no turn |
| The old setups and their clocks | `plan._place_offence`, `_place_defence`, `agent._search_*` | Run only if `eval.map_lead` is set back to "list" | Kept for comparison, not live |

No special term was added for a backdoor cut, fronting, a trap, denial, spacing or a packed key. Where a check needed one to pass, the check is reported as failed.

## 7. The scale

Found on other scales or off the rules' scale, and what was done:

| # | What | Done |
|---|---|---|
| 1 | The quick reading went through a fitted curve | Under the value, the quick reading is the value itself. Fixed |
| 2 | The phase table and its averages | Replaced by the bar counted from the rules (what playing on is worth, phase by phase). Fixed |
| 3 | Two hand multipliers, 0.7 and 0.85 | Not read under the value. Fixed (the code stays for the old readings) |
| 4 | The shot clock running out read 0 | Minus 5, by the rules. Fixed, with a test |
| 5 | The closely guarded count in thirds (`conditions.py`) | Not fixed. It is in the old plan's wording only, which the value doesn't read |
| 6 | Sums of worths in the old matchup price | Not fixed. The old defence setup only; not live |
| 7 | Bare chances used as tests (`goals.py`, `conditions.py`) | Not fixed. They still name goals (see the goal margin above) |
| 8 | The block stopped at minus 5 | The value reads past a block, the same way in both engines. `scoring.block_option` (the advice panel) and `plan.case_value` (the old plan) still stop at minus 5 |
| 9 | The search's window was minus 10 to 60 | Widened to minus 100 to 150 (several turnovers or fouls can be banked). Fixed |
| 10 | The advice panel's reply value leaves out a foul's plus 5 | Not fixed |
| 11 | Three seconds possibly counted twice | Counted once, at the phase end. Fixed |

"Worth right now" is on the scale: a shot's points are what they are worth on the scoreboard now, so under Need a Three a two is worth 0 (D-289).

## 8. Differences from the rules, and from the design

**From the rules:** none found in what was built. The low end of the scale is the rules' (a shot never scores below 0; a contest is at least 1). Where the design's words differed, the rules won (the table "Rulings of 25 November" already records these).

**Built differently from the design:**
- **The centre of gravity is a balance point, so it can't sit on the arc** (D7). Weight spread round the arc balances inside it. The map moves to the arc under Need a Three; its centre doesn't. The design's check wants the centre at the arc.
- **A worthless shot still weighs a little in the last phase.** A two worth 0 beats the shot clock running out (minus 5), and a block takes that away, so each look inside the arc weighs 4.5 on E8. That follows from the scale.
- **The read-ahead of four turns** belongs to the old turn-by-turn plan. Under the value, every phase left is read by the value's own sum, and the turn search looks one turn ahead (section 9). I did not compare three turns with four, because neither is what the build reads.
- **The fake inside layer 1 as a two-by-two mix per look** was not built. Layer 1 reads a block only against a rushed shooter and takes the hold's value otherwise. So there is no finding to report on whether it disagrees with the search's mix.
- **Sharing a segment as a counted cost** and **help distance** are not terms in the build (cause 3).
- **Plan conditions** (setup step 4) are not built: the new offence setup returns squares and a value, no named plan. The Plan panel shows the old wording.
- **Secondary skills breaking ties** is not built. Level turns go to the one order in D-300.

## 9. Times, the look-ahead, the caps and the segments

**The goal was about a minute a setup and 20 seconds a turn. It is not met.** On this machine (one laptop-class core per reading):

| Board | Offence setup | Defence setup | One turn |
|---|---|---|---|
| Twin Towers v Lockdown | 209.0 s | 84.8 s | 34.1 s |
| High-Low v Run and Gun | 150.5 s | 9.1 s | 12.4 s |
| Five Out v Iron Wall (the block board) | 115.5 s | 29.3 s | 190.4 s |

These were timed with five other jobs sharing the machine's four cores, so they are high, perhaps by half. A run with fewer jobs gave offence setups of 93 to 111 seconds and defence setups of 8 to 38 seconds on the same boards. The block board's turn is the defence's reply to a layup that may be a fake: the mix behind that reply, with no clock, takes minutes.

Across the exam's boards: a defence setup 11.6 to 166.8 s (middle 64.2 s); an offence setup 50.1 to 111.6 s (middle 105.2 s); the turn search alone 3.1 to 49.6 s (middle 4.6 s); one reading of the value 0.1 to 0.6 s (middle 0.3 s).

**Is it playable?** No, not yet, for two reasons. A setup of one to three minutes and a turn of up to a minute is too slow to play against, and a phone is commonly 2 to 4 times slower (not measured). And the engine's memory is too high for a browser (next paragraph). Fidelity came first, as told; speed didn't get to its goal.

**Memory, found while playing the possession.** One All-Star turn's thinking, one turn ahead, on the 20 November board held 1.7 to 1.95 GB in the engine and failed outright when the engine was held to 1 GB. The biggest think of the possession (the offence weighing a fake) reached about 5 GB. The first run of the possession was stopped by the system for memory in phase 5; the replay used a fresh engine process each turn and made the same 57 actions up to that point. For comparison, the live site's engine needs 0.95 GB for the same search when it has no clock: until now the 2.5 second clock stopped the search long before that. So taking the clocks out exposed a cost the clocks were hiding, and this step's heavier readings doubled it. A phone's browser will not give a page that much. I did not find which store holds it: it is not the count of remembered readings (cutting that to a tenth still failed at 500 MB). This alone would have blocked the merge.

**Times after each stage** (Twin Towers v Lockdown; offence setup, defence setup, one turn):
- Before the step (30b): 143, 113, 23 seconds.
- After stage 1 (the value in, the old setups still running, clocks out): 275, 298, 67 seconds. A fourth run of an old setup with no clock ran past 25 minutes and was stopped; the old setups were replaced in stages 3 and 4.
- After stages 3 and 4 (the new setups): the table above.
- Stages 2 and 5 added readings for display only (the weight map and the lines) and were not timed apart.

**What takes the time.** One reading of the value is 15 to 30 milliseconds; a defence setup reads about 50 milliseconds a candidate and tries each defender's nine squares and eight arrow pairs, round after round; an offence setup runs a quick defence under every placement it tries.

**Speed work built:** the one-think memory holds the value, the weight map and each stance reading; inside one reading the defence's movements are read by difference (only what the movement touched), checked against full readings; the cuts inside the value are proven not to change it (765 boards, and a test); the memory's keys are the whole state (the hand-picked hash is gone); the tie rule is one rule in both engines. **Not built:** reading the map by difference across boards (after an action, only the players it touched). The guard test for it exists and passes, but today it guards the memory, which reads a changed board afresh. That is the biggest lever left and is why the goal was missed.

**Several cores.** The readings inside a setup are independent and are combined in a fixed order (the exam tool already runs three processes side by side and gathers by name, never by finishing order). The app still thinks on one worker. To use the cores it needs a pool of engine workers in `pyodide-adapter.js` and the Python that drives a setup to hand out a round's candidates and wait for all of them.

**The look-ahead table.** Each level is set to what its clock reliably finished on step 30b's machine: one turn.

| Level | Look-ahead | Turn time at that | Setup time | Turn time one step further |
|---|---|---|---|---|
| Rookie | 1 turn | 2.7 to 9.7 s | the same at every level (the table above) | 17.0 to 234.7 s |
| Starter | 1 turn | 2.3 to 13.7 s | the same at every level (the table above) | 28.1 to 225.6 s |
| All-Star | 1 turn | 3.4 to 15.0 s | the same at every level (the table above) | 52.0 to 324.4 s |

Turn times are the search alone on three exam boards (E10, the defence to act; E13 and E22, the offence to act), taken while other jobs shared the machine. One step further is 4 to 30 times slower, so every level stays at one turn ahead for now. The levels differ in how many turns they keep at each step (8, 16, 24), their pick noise, their variety and what they pay attention to, not in how far ahead they look. The setups don't use the look-ahead: they read the possession's value, which already counts every phase left.

**Clocks removed:** the three thinking clocks (Rookie 0.3 s, Starter 1.0 s, All-Star 2.5 s: `time_budget_s`); the clock on each fake's mix; the clock inside the JavaScript search (it runs to its fixed look-ahead); the setup's share of a decision's time (the new setups take none). **Clocks left, none live under the value:** the old setups' clocks and the old plan's read-ahead clocks (12, 30 and 60 seconds in `plan.py`), which run only if the old readings are switched back on, or when a human asks the old Plan panel for its words. **Trainer clocks, not changed:** the decision timer the player sees, and the Trainer's timing grades.

**The caps table.** Every limit on what gets read:

| Cap | What was done | Trial | Time |
|---|---|---|---|
| Looks kept per attacker when bounding the defence's answer (2) | Kept as a provable cut | Proven: with the cut off the value and the answer are the same (765 boards; `tests/test_exam.py`) | none |
| Movements that can't lower the number are skipped | Kept as a provable cut | The same proof | none |
| The search's clock | Removed | | |
| The setup's clocks | Removed (new setups) | | |
| The stance search tries squares 2 away from each defender, not 1 | 5 board(s): E1, E5b, E26b, E33, E12 | CHANGED on E1 | 84 s to 313 s |
| Each attacker tries 6 segments, not 3, and 4 placements are read in full, not 2 | 1 board(s): E15b | no change | 50 s to 111 s |
| The search keeps twice as many turns a step | 16 board(s): E4, E6, E9, E10, E11, E13, E14, E16, E21, E22, E24, E28, E28b, E29, BLK1, BLK2 | CHANGED on E10, E28 | 217 s to 441 s |
| The defence's answer is one movement at a time | Kept, not trialled | No wider form exists to compare with. Listed for Shaun | |
| The turn search's first-action lists (8 read in full, 4 followed) | Kept, not trialled | Level settings from step 18; ran out of time | |
| Lumps join within 2 squares | Kept, not trialled | Display and base positions only | |

Where a widened cap changed the answer:

- **E1, the defence's setup.** Trying squares two away, three defenders end somewhere else (X3 on O10 not M7, X4 on D4 not B3, X5 on I5 not H4) and the possession reads 9.8, not 14. A much better defence was there to find, and the one-square search missed it. This is cause 1, measured.
- **E10, the defence's turn.** Keeping twice as many turns, it finds X2 Quick Step to E7 then X1 Steal (25.4) where it had chosen to wait (26).
- **E28, the defence's turn.** A different turn of the same value (22.25): X2 Move to G4, not X3 Quick Step to L6 then X1 Move to G10.

The trials ran on the boards named, not on every exam board: a doubled setup search on all sixteen setup boards would have taken hours.

**The segments trial (answer 4).** Every reading that uses the segments table (the weight map on all 46 boards, the 17 defence setups, the 3 offence setups) was taken again under each other table, and all 50 checks judged again:

| The table read instead | Readings that changed | Checks whose result changed |
|---|---|---|
| I8 and I9 left only | 4 of 66 | none |
| I8 and I9 right only | 0 of 66 | none |
| the corner ends at row 6 | 3 of 66 | none |

What changed: the weight's centre moved by one square on E12, E16, E20, E4, E6. No setup changed a square, an arrow or its value. So on today's build the three open choices make no difference to any check. That will be worth asking again once the setups lean on the segments more (cause 3).

The turn search and the value don't read the segments, so every other check is unchanged by construction.

## 10. Tests

Tests ran for about 16 minutes in all, against a limit of about 10 plus the golden game: the suite sweep took its full 10, and the exam's own file, the rules, the memory tests, engine equality and the golden game took 6 more. No test was loosened, skipped or marked as expected to fail. Nothing was re-recorded.

| What | Result | Time |
|---|---|---|
| The exam (`tests/test_exam.py`) | 41 passed, 23 failed. Every live reading passed (O1 and its "fails without", G5, the shot clock, A12 and A13, the mix in both engines, B2 on five boards, the full-read guard, the memory guard, B3). The 23 failures are the failed and unbuilt checks, each by its number | 2 min 1 s |
| The rules (`test_rules_current.py`) and step 30b's memory tests (`test_step30b.py`) | 25 passed | 25 s |
| Engine equality (`tools/js_equivalence.py`, 40 random states) | 0 mismatches | 37 s |
| The golden game (`test_golden_and_regression.py`) | 8 passed, no value moved | 73 s |
| The rest of the suite: each file in its own process, 90 seconds a file, 10 minutes in all | 30 files passed, 7 failed, 15 not finished in their time, 8 not reached | 10 min |

**The 7 files that failed:**

| File | Why | From this step? |
|---|---|---|
| `test_revalidated_live.py` | A ceiling reads 6 where the test expects 9 | No: it fails the same way on the live code |
| `test_computer.py` | A recorded replay diverges | No: fails on the live code |
| `test_coach_gate.py` | The coach's line comes back empty | No: fails on the live code |
| `test_placement_ui.py` | A tap in the browser times out | No: fails on the live code |
| `test_static.py` | Reads the removed thinking clock (`time_budget_s`) | In part: on the live code it already fails two lines later, on the browser build running over that clock |
| `test_setup_18o.py` | Asserts a setup keeps to its clock (8.5 s against 0.12 s) | Yes: the clocks are gone (D-293). Its premise is gone, so it was not re-recorded. For Shaun: retire it or rewrite it as a look-ahead test |
| `test_heat_map_20.py` | Expects the old reading's number on a board (36; the value reads 25.69) | Yes: the reading changed. Not re-recorded, because the heat map view itself still shows the old list |

**Not finished inside 90 seconds** (or cut off by the 10 minutes): accessibility, foul_price_18k, map_logic_21, movement, scouting, solver, step22c, step24, step27, step28, step29, step30, step3m, step3n, strength_18s. **Not reached:** teams, timer, turns_phases, two_responsibilities_22b, ux_19, web, wedge, zone_18g. These include the step 27 to 30 files, which run well past 10 minutes and assert the old list-led setups; expect many of them to need re-recording once the new setups are trusted.

**Not tested:** the order of level turns (D-300) is the same rule written once in each engine, with no two-engine test of its own. The site was not built and the site packing test was not rerun, because nothing was merged.

**Passed (30):** advantage, breaking, breaking_live, contest_18j, course_boards, coverage_18s, defence, drivers_22b, fiba_18i, intercepts_mti, intercepts_oq72, lane_18q, levels_3l, off_balance_18l, points_play_on_18r, position_contest_18n, receiver_denial, rolls_scoring, rulebook_nov, rules_current, rulings_3i, scenarios, screen_22b, see_the_steal_18j, setup_3k, step18p, step22, step26, step30b, step6.

## 11. The ledger, row by row

Built means it is in the code and read by both setups and play. The check column is the exam's verdict today.

| # | Agreed | Status | Where | Check |
|---|---|---|---|---|
| 1 | Each player's areas of average or better shooting demand a defender | Built | `offenceSetup` scout (card marks by segment) | O3 fail, O4 pass |
| 2 | Sub-zones: green as one, mid-range in three, long two in four, five beyond the arc | Built, provisional | `data/segments.json`, one table for both engines | O3 fail |
| 3 | Don't share a section while keeping each player dangerous | Changed: no counted cost; left to the value | `offenceSetup` | O3 fail |
| 4 | Distance kept large unless the plan needs players close | Not built as a measure (help distance) | | O3, O6 to O10 |
| 5 | Secondary skills break ties | Not built | | O11 pass |
| 6 | Setup order: scout, ball handler's start, positions, plan conditions, adjustments | Changed: four of five steps; no plan conditions | `offenceSetup`, `setup31.place_offence` | B4 fail |
| 7 | Get out of each other's way | Left to the value; didn't show | | O5 fail |
| 8 | Gaps in the key are worth the most | Built (the value and the weight) | `possRead`, `weightMap` | D11 pass, O1 pass |
| 9 | Spread so each defender is pinned to one man | Left to the value | | O3 fail, D4 pass |
| 10 | Push and pull; one formula for the stack and the spread | Built as the one value; the stack setups not built | `possRead` | O6 to O10 |
| 11 | Little time means several actions at once | Not showing | | O6 not built, O9 fail |
| 12 | Where the ball starts against the centre decides access | Not built (inbound) | | O6 to O8 |
| 13 | Room and angles separate from access; the corner inbound spreads | Not built (inbound) | | O7 not built |
| 14 | Full denial is the same access case | Left to the value; didn't show | | O10 fail |
| 15 | The team's centre of gravity in three layers | Built | `weightMap` (engine.js), `weight.py` | D1 for Shaun, G1 fail, G2 pass, G3 fail |
| 16 | Layer 1: rating out of 20, open and contested, times points; the pull is the difference | Built | `weightMap`, `_valsCalc` split | D3 pass, G2 pass |
| 17 | Add the weights across five attackers for the base centre | Built | `weightBase` | D1 for Shaun |
| 18 | Poor shooters give a packed key; one shooter a box-and-one; mid-range conceded | Falls out only in part | | D1 for Shaun, D2 fail, D3 pass |
| 19 | Layer 2: occupation, usually a small shift | Built | `weightMap` | D4 pass |
| 20 | Layer 3: the ball's reach, one factor with occupation | Built | `weightMap` (reach) | D4 pass, D8 fail |
| 21 | Individual assignments: the man, the ball, the gaps | Built | `weightMap` own, `stanceBase` | D10 pass, D12 fail |
| 22 | The link rule: leave only when helping saves more than his man would cost | Built as a check on the answer (each defender lifted) | `stanceSearch`, `lifted` | D4 pass, D5 for Shaun, G2 pass |
| 23 | Defenders with nothing to guard move to the centre | Built in the base positions | `stanceBase` | D12 fail |
| 24 | The centre keeps defenders on the right side of their men | Built in the base positions; the search loses it | `stanceBase`, `stanceSearch` | G1 fail, G3 fail, G4 fail |
| 25 | A defender, or the team, can shift its weight | In part | `ctx.worth`, `weightMap` | D2 fail, D7 for Shaun |
| 26 | No weighting between team and individual: both in points | Built | | G2 pass |
| 27 | The trap appears when lanes, access and angles are contained | Didn't appear (no special term allowed) | | D8 fail, D9 pass, A5 fail |
| 28 | Arrows are chosen with the square | Built at the setup; not in play (cause 2) | `stanceSearch` | A1 to A6 |
| 29 | Arrows maximise what they take off the value | Built at the setup; the checks fail | `stanceSearch` | A8 fail, A9 fail, A10 fail |
| 30 | Speed is a gap like a dribble edge | Built (the race) | `covBuild` | A7 pass |
| 31 | The pass counts closeouts, failed intercepts and fakes | Built | `routeT`, `mixGame` | A11 pass, A12 pass, A13 pass |
| 32 | Worth right now; the best legal contest; both sides at real chance; the map leads | Built | `ctx.worth`, `RC.worth_now` | D7 for Shaun, D5 for Shaun |
| 33 | The list kept, best look first, priced as the possession's value | Built | `possParts` looks | G5 pass, B1 pass |
| 34 | Take the good shot; three seconds from entry; no action without purpose | Built | `_mapLeaf`, `threeSecondsLeave`, D-300 | O1 pass, O2 fail, O11 pass |
| 35 | A fundamentals exam every step must pass | Built | `tests/test_exam.py`, `CLAUDE.md` | all |

**The five recorded changes:**

| What | Status |
|---|---|
| "No two players in the same section" as a counted cost, segments as an aid | Changed again: segments are the aid; there is no counted cost (cause 3) |
| "Maximise distance" measured by help distance | Not built |
| Cover in degrees | Built: each entry keeps the weight left after the cover, and a rushed contest covers less |
| The five defenders solved together; the link rule describes and checks | Built (the joint search and the lifted reading). The search is too short (G4) |
| The ball's reach counted once, in the map | Built |

**Rulings of 25 November:**

| What | Status |
|---|---|
| The read-ahead: four turns | Changed: see section 8 |
| A turn: 1 or 2 actions, from 6 a phase | Built (the routes and the answer are limited by actions) |
| Locked: a Quick Step is still allowed | The rules, as they were |
| A missed Intercept and a missed Steal, each by its own rule | The rules, as they were |
| The low end of the scale | The rules. For Shaun to confirm |
| Need a Three: a two is worth 0 | Built (D-289) |
| Whose contest in layer 1 | Built: the best of five for the team's map, his own for a defender's base position |
| Falling back through looks is limited by actions | Built (D-294) |
| The defence's search also tries two together | Built (pairs swap) |
| The levels: a fixed number of turns, never a clock | Built (D-293) |
| Speed only from never doing work twice, cheaper machinery, the whole device | In part (section 9) |
| The block's reset | Not ruled. A second block board was added (BLK2) |
| The segments | Provisional. Trial in section 9 |

**Principles settled before 21 November ("still to be audited").** With a test: the pass's danger and the missed pass (`tests/test_step29.py`, value routes in `test_exam.py`), the contest as an action (`test_step28*`), deep range (`test_step29.py`; check D6 reads it at two levels), fakes and the mix (`test_step29.py`, `test_step30.py`, A12 and A13), separate thinking (B3, rebuilt), the Screen rule (A4). I did not add a test for each remaining item in "Kept"; that list was not walked item by item.

## 12. For Shaun to decide

1. **Whether to carry on down this road.** The one number is right on the boards where it is simple (O1, G5, the mix), and both engines agree on it. The shapes it produces are not basketball yet, for the four causes in section 3. The options: (a) fix the causes in order, search first, which is mostly speed work; (b) keep the value for play and the end of every line, and put the setups back on a goal-side starting shape that the search may only improve; (c) stop and rethink the design's claim that shapes fall out of one number. I'd take (a) with (b) as its first stage, because G4 says the search needs its starting shape.
2. **The low end of the scale** (answer 3): a shot never below 0, a contest at least 1. No change wanted?
3. **The segments** (answer 4): still provisional. The trial is in section 9.
4. **D1, the packed key.** On E1's cards an open three from a 7 shooter is worth 21, more than the rim gives against the Rim Protector, so the defence stays out. Is that the cards as you want them?
5. **D5, the closeout.** By the rules as read, a defender three squares off can't take the shot away this phase (only a Sprint reaches, and it leaves his contest rushed). So closing out early gains nothing now, only next phase. Should the computer close out anyway, for the next phase?
6. **D7, the centre.** A balance point can't sit on the arc. Is the centre the balance point, or the heaviest place?
7. **The tie rule (D-300):** standing still wins a level tie. Confirm.
8. **Memory and the clocks.** With no clock, one think needs gigabytes (section 9). Until that is fixed the build can't go to the site, whatever the exam says. The fix is engineering (find the store, bound it without changing an answer); no ruling needed, but it comes before anything else.
9. **The defence's answer one movement at a time** (section 6). Accept as the reading of "the defence's best answer", or should it plan two together?
10. **The block's reset** is still open. With the value in, a phase after a block can now be read; BLK1 and BLK2 are the boards.
11. **The design's open questions.** Catch and finish: not touched. Whether the cards concede the mid-range: one board says yes there (section 4, D3); not answered in general. Worth right now outside scenario cards: it is the points, and Need a Three sets a two to 0. Reaction moves after the first action (drift, lift, fill behind): did not fall out; in play the defence mostly waits (cause 2) and the offence takes one best thing (cause 4).
12. **The 20 November cards**, if you have the deal.
13. **Two tests whose premise this step removed** (section 10): `test_setup_18o.py` (a setup keeps to its clock) and `test_heat_map_20.py` (the old reading's number). Retire, rewrite or re-record?
14. **The caps that change answers** (section 9): widening the defence's setup search changed E1, and doubling the turn search's list changed E10 and E28. By the prompt's rule a cap that changes an answer can't stay as it is. Each needs either a proof or more reading, and more reading is more time.

## 13. Noticed, not touched

- The app's Plan panel and the coach's lines still speak from the old list. They rank nothing now, but they can describe a plan the computer isn't following.
- `tools/speedtest.js` (the hidden speed page) still reads the removed thinking clocks.
- The All-Star's variety margin of 2 means it will sometimes pass up the best turn for one 2 points worse. With the value flat across many turns, that is a lot of freedom.
- `tools/step_31_exam.py b4` starts a fresh engine process each turn, because of the memory above. The app has one long-lived engine.
- The Python engine is 10 to 15 times slower than the JavaScript engine on the value; the setups live in the JavaScript engine only.
- Step 30b's timing tool gave the offence an old-style plan before timing a turn; it now times the turn as the app plays it.

## 14. Model for the next step

Claude Fable 5.2, effort high. The next step is search and speed work inside a large engine file where one wrong cut changes decisions silently; it needs the strongest reasoning and the same-decisions checks run every time.

