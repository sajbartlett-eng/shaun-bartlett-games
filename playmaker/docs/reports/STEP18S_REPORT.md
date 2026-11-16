# Step 18s, stop one: the coverage map, the coach's view, design checks 1 to 6

**In five lines.**

- **What the computer can now see.** For every attacker and every square: what the look is worth with nobody on it, the chance he has the ball there when the next phase starts, what the defence takes off it and what is left, who covers it and who is next. Then the defence's best answers inside the tokens it has. One snapshot a phase. Built from the game's own rules; nothing fitted is in its path. Nothing in the computer's play reads it yet: that is stop two.
- **Which design checks fall out.** 1, 2, 3 and 4 fall out of the map. 5 falls out of the rules but the map only shows it when the defence is out of tokens (decision 1). 6 falls out for a body on the helper's way and not for the Screen action (section 2).
- **Check 1 also holds by play.** Your defence of 15 November gives up 26.5 a possession and 8 layups in 16. The placement the map chose for itself gives up 23.2 and 1 layup in 16.
- **What to look for with "Defence map: shown".** Dark red by the rim when no big is behind the on-ball defender, fading when one steps in. Tap a square: is the defender it names the one you would name? Read the one line of words: is the defence's best answer the one you would make?
- **The map found a fault in the reading the computer plays from today.** It prices every pass on your board as arriving 1 time in 4. By the rules two of them can't be intercepted at all. That is first in stop two.

![The coverage view](../runs/step18s/coverage_view.png)

## 1. What was built

| Part | What it is |
|---|---|
| **Value** | The attacker's best shot on that square with nobody on it, from his card. An open three for the sharpshooter is 27; for the Post Scorer Centre, 18. Nothing is ranked by hand (the refinement in D-199). |
| **Reach** | The chance he has the ball there when the next phase starts. The ball handler: his own movement. A teammate: one movement and the catch, at the rules' own pass chance. A lost ball is −5 (D-198). |
| **Influence** | What the defence takes off the look: each defender given the two actions of the reaction from where he stands, bodies and arrows counted as they stand. |
| **Weakness** | Value less influence: what is left. |
| **Who covers** | The defender who takes the most off it, and the next best. One defender covers many squares and several attackers. |
| **The defence's best answers** | One movement at a time, each the one that leaves the least, until its tokens run out or nothing gets smaller. "It can't cover two at once" is what is left after that. Not fitted. |
| **The snapshot** | Kept for each phase of the possession, with the change since the phase before. |
| **The coach's view** | "Defence map: shown / hidden" (hidden unless you turn it on; the name is decision 2). A heat map on the board, all five attackers or one at a time. Tap a square for who gets what there and who covers it. One line of words under the board. |

**Three approximations, each stated in the code.**

1. A teammate off the ball gets one movement before the catch, not two.
2. An arrow bars the ball handler's way at its present length. A defender who steps is given his new arrow's first square only.
3. The defence's answers are picked one action at a time. A pair of steps that only works together can be missed.

**Also mended:** the reading priced a shooting foul without D-198's +5. Now it carries it, in both engines.

## 2. The design checks (your board of 15 November, the zone on)

The cards on it: O1 Defensive Point Guard (open three 21, at the rim 34), O2 Sharpshooter (27, 34), O3 Bucket Getter (27, 38), O4 Post Scorer Power Forward (21, 38), O5 Post Scorer Centre (18, 38).

### Check 1. The clear lane reads as a large weakness; the defence's own best placement reads it smaller, and plays out smaller. **Holds.**

| | The map reads | By play, 16 possessions |
|---|---|---|
| Your game (X4 and X5 next to their men) | **34**: a layup for O1 on I3, nobody able to contest it | **26.5** (24.6 to 28.4). Layups 8, post shots 2, threes 5, a floater 1 |
| The map's own placement (J10, D4, O8, F4, M2) | **22**: a layup for O3 on J4, X4 on it and X5 next | **23.2** (20.5 to 25.9). Threes 15, layups 1 |

- The map's answers, in its order: X4 sprints to F4 (leaves 26), X5 moves to M2 (24), X2 sprints to D4 (22).
- The play is by the computer as it plays today. It doesn't read the map yet, so this is the placement being judged and nothing else. Same dice, copy by copy.
- The ranges touch at 16 a side (24.6 against 25.9). The shots don't: 8 layups against 1.

### Check 2. A non-shooter's three is worth little; his defender in the lane costs little. **Holds.**

O5, the Post Scorer Centre. His open three is worth 18, the lowest on the floor. With X5 off him and in the lane (I4), the offence's best falls from 34 to **24**. His own three where he stands goes from 6 to 9.

### Check 3. A sharpshooter's three is worth a lot; his defender leaving reads as a large weakness. **Holds, by less than the blueprint expects.**

O2, the Sharpshooter. His open three is worth 27. With X2 off him and in the lane, the offence's best is **28**, against 24 when the help comes off the non-shooter. So the map does prefer helping off O5 to helping off O2. But his own three where he stands only goes from 12 to 15: X4, from next to his own man, still gets out to him inside the reaction. See decision 1.

### Check 4. Arrows matter. **Holds, in three places.**

| Where | The arrow | Result |
|---|---|---|
| X1's arrow and the ball handler's way | Across his way to the rim | 98 squares reached, 5 worth 30 or more, and his best is a rushed layup at 30 |
| | On him (your game) | 116 squares, 10 worth 30 or more, a set layup at 34 |
| | Away from everything | 118 squares, 10 worth 30 or more |
| X2's arrow and the pass to O2 | Down the passing lane (north-west or north) | The pass arrives 3 times in 10 |
| | Off it (east or south) | The pass can't be intercepted |
| X2 in front of O2's three, no token left | On him | The three is worth 12 |
| | Off him | 21 |

### Check 5. Square in front beats beside, and beside beats behind. **Holds by the rules. The map shows it only when the defence is out of tokens.**

O2's three going up now, X2 next to him:

| X2 stands | No token left | With the reaction (a fresh defender) |
|---|---|---|
| In front (C8) | 12 | 12 |
| Beside (D9) | 21 | 12 |
| Behind (C10) | 24 | 12 |

At a phase's start the defence has its tokens, and the reaction's two actions get a fresh defender square from beside or behind. So the map, which reads the start of the next phase, shows all three alike. This is the rules, not the map. Decision 1.

### Check 6. A screen that stops a covering defender shows his squares going weak. **Holds for a body. Does not hold for the Screen action.**

The defence with one token left has one answer: X4 to F4, leaving 26.

- **A body on his way:** with O4 on C4, between X4 and the lane, that answer is gone. The best left is X1 to J6, leaving 28. With O4 one square off his way (C5), it is 26 again.
- **The Screen action:** none of the 16 Screens I could place next to X4 or X5 stops either of them. The Screen bars a diagonal step past its square, and these helpers travel straight.
- **How I read it:** check 6 is met by a body or a Screen that stops a covering defender. A screener standing on the helper's way works today with no rule change, and the map reads it. Say if you want the Screen action itself to bar more.

## 3. What the map replaces, and what it found

**Nothing is replaced at this stop.** The map stands beside the computer's reading and is shown to you. At stop two it takes the place of:

- **the lane reading of step 18q** (`eval.lane`, off), which was the map's first row built on its own;
- **the reading's pass chance**, which is wrong (below);
- **the "passing options" measure** the system map had as its next iteration.

**The fault it found: the reading's pass chance is not the rules'.** The reading lets any defender who can step onto any square of the pass's line take the pass, the on-ball defender next to the passer included. On your board it prices every pass at 1 in 4. By the rules:

| Pass from O1 to | The reading | The rules (and the map) |
|---|---|---|
| O2 | 0.25 | 0.30 (X2's arrow is down the lane) |
| O3 | 0.25 | Can't be intercepted |
| O5 | 0.25 | Can't be intercepted |

A computer that thinks three passes in four are lost will not drive and kick. In step 18r the offence against help settled for a three 16 times in 16 and scored 19.9, where the forced drive and kick scored 24.8. I think this is why. It is not mended here, because it changes what the computer plays and needs its own proof; it is first in stop two.

## 4. Speed, for the record (D-200)

- **The map takes 1.4 to 1.7 seconds a position** on the desktop. The app asks for it once a phase, and only while "Defence map: shown". Hidden, it costs nothing.
- **The computer's own decisions were not timed again.** Nothing in its search changed but the +5 on a shooting foul. Step 18r's table stands: over the budget at Starter, at the edge at Rookie and All-Star.
- **The timing test fails as before** (3.2 seconds on one decision against a limit of 1.7, run on its own; 3.3 in step 18r). Not loosened.

## 5. What it proves

- **Both engines agree:** 300 positions with 8 searches and 200 shot reactions, 0 different. The map itself is in the fast engine only until stop two.
- **Tests:** `tests/test_rules_current.py`, the named test files, the golden tests and the new file: 303 passed, 14 expected failures from before, and 1 failed, the timing test. `tests/test_static.py`, run on its own: 12 passed. `tests/test_computer.py`: the one failure it had before (a stored game from before D-184).
- **One test caught me.** The step 3n test that bans engine words on screen failed on the word "coverage" in the button. I renamed the button and left the test alone (decision 2).
- **New tests:** `tests/test_coverage_18s.py` (15) and one in `tests/test_static.py` that turns the view on in the built site, reads the words and taps a square.

## 6. Compute

**1.7 core-hours against an estimate of 2.8** (`docs/runs/step18s/PREDICTIONS.md`). The stop was 5.6.

| Part | Estimate | Used |
|---|---|---|
| 1 The map, read on named positions | 0.3 | 0.1 |
| 2 Design checks 1 to 6; check 1 by play | 1.5 | 0.5 |
| 3 The view in the app; the tests | 1.0 | 1.1 |

No part ran past twice its estimate.

## 7. Decisions for you (three)

1. **Position at a phase's start (checks 3 and 5).** By the rules a fresh defender next to a shooter gets square inside the reaction, and one two squares away gets out to him. So a defender's exact square shows on the map through his reach, his arrow's bar, the lanes he can jump and his tokens, and hardly at all through "in front, beside, behind". Options: (a) leave the rules and judge it with the view on; (b) rule that a contest made after a Move in the reaction is 2 lower, as it already is after a Quick Step or Sprint (D-151). **I recommend (a) first.** Play a few phases with the view on. If the board looks too safe next to a badly placed defender, (b) is the smallest rule that changes it, and the map will show the difference the same day.
2. **The word on the button.** Your prompt names the view "Coverage: shown / hidden". A test from step 3n bans the word "coverage" on every screen: it was an engine word then. I don't loosen tests, so the button reads "Defence map: shown / hidden" and the test is untouched. Options: (a) keep "Defence map"; (b) take "coverage" off the banned list, since D-199 makes it your word, and the button becomes "Coverage" as you wrote it. **I recommend (b).** It is your term, the reports already use it, and it is a two-line change once you say so.
3. **Stop two.** **I recommend going ahead, in this order:** the reading's pass chance replaced by the rules' in both engines, with its own proof; then the search and the setup read the map; then checks 7 to 9 on forced lines (the 18o closeout position replayed under D-198 first, check 8 on named positions); then the port to the other engine. Your playtest of the view comes first: anything the map shows that your eye disagrees with is cheaper to mend before the computer plays from it.

## 8. Model advice

Claude Fable 5.2, effort high, for stop two. It changes what the computer plays in two engines that must stay equal, and it is judged on forced lines.
