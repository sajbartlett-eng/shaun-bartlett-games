# Step 21: how both sides use the map

**In five lines.**

- **The defence is read as it really is this phase:** a defender who is spent, locked or beaten can't recover inside the phase, and the map says so. The offence still gets its full turn to come, because next phase it moves first.
- **Overloads count numbers now:** one on two, two on three, three on four. When a group of defenders is the only cover for more attackers than there are of them, the map gives the offence what the best assignment leaves open.
- **The computer always tries the map's own best answer,** so a switch is simply the answer that leaves the least. In the Watch game the defence switched 14 times in 87 defence turns.
- **The coverage view and the reports update after every action.** Each action carries its own change in the lasting gap, and the view says when its map is from ("Coverage after O1 passed to O2, before the defence answers").
- **Look for:** whether beaten defenders now go somewhere useful, whether switches look like communication, and whether the offence cashes an overload it has made.

**Branch:** `step-21-map-logic`, from `main` after PR 82. The pull request is open and not merged. `dist/playmaker.html` is built from the final commit.

**Changes to the printed game:** none (D-190).

## The beaten-defender fault: the cause and the fix

**The cause was in the reading, in two places.**

1. **Step 20 read every position as a fresh phase.** A defender's tokens, his movement and whether he was locked or beaten all reset before the map was read. A beaten defender far from the play read exactly like one in place, because the map assumed he would recover. On B1 (your example, below), step 20's computer read every one of X1's options at the same 24: moving, quick-stepping or pausing were all the same to it, so his choice fell to the order of the list. That is "no-man's land": nothing in the reading said where he was needed.
2. **The defence's move list never included the map's own answer.** The search only tries the moves its older reading suggests. So even when the map knew the rotation, the search could not play it unless the old reading happened to offer the same move.

**The fix (D-206, D-207):**
- The defence is read with what it really has left this phase: its tokens, who has moved, who has quick-stepped, who is locked or rushed, and any zone a Dribble broke.
- The search always tries each movement of the map's best answer. That answer matches all five defenders against every look on the board, so no defender is tied to his man.
- No rule tells anyone to chase or recover (D-156).

**One thing I found and changed on the way: the offence keeps its full turn to come.** At first I read both sides as they really are. B2 showed what that does: with the offence's tokens spent, the map lost every look that needs a pass next phase. After O2's sprint and the catch it read the position at 16, and play gets 34 every time, because next phase the offence moves first, before the defence can answer again. So the offence is read with its full turn to come (D-204's like for like, which your ruling leaves standing for the offence), and the defence as it really is. That is decision 1.

**Double counting:** none. A lane already covered by another defender doesn't lower the reading. On B1 the pass to O2 can't arrive with or without X1 (X2 already denies it), and the map reads X1's lane square the same as his other options.

**"The offence won't shoot yet":** with the defence to act, the shot now is 0 on all three boards, so the defence's choice is decided by the lasting gap alone.

## The forced lines (16 play-outs a line, All-Star against All-Star, the map on)

The positions are named in `tools/step_21.py` (B1, B2, B3), and the play-outs are in `docs/runs/step21/lines.json`. Lower is better for the defence. A range is the 95% range of the mean.

### B1: X1 beaten by O1's drive off O5's screen, X4 and X5 helping, 3 on 2 near the key, X2 tight on O2

| X1's line | Points | Range |
|---|---|---|
| The computer's choice (the defence pauses) | 23.8 | 23.3 to 24.2 |
| X1 chases the driver (to I5) | 24.0 | 24.0 to 24.0 |
| X1 recovers to the open look the help left (K6, between O5 and O3) | 23.9 | 20.0 to 27.7 |
| X1 drops to F8 on the left: the "lane to O2" | **19.0** | 17.0 to 21.0 |

**This one fails the test, and I haven't found the cause.** The best line by play is the one meant to stand for what you saw, and the computer's choice is 4.8 worse (2.8 to 6.7). But on this board F8 isn't really a passing lane: by the rules a pass to O2 can't arrive with or without X1 there. It is X1 dropping to the left elbow. The map reads all four lines within 0.2 of each other (17.8 to 18.0), except K6, which it reads worse (22). Play separates them by 4.8, and the scores come a few actions later on the right side (O3's floater, O4's three). So the map is missing something on this board that play sees. It is the first thing to look at next.

### B2: step 20's possession 4, phase 3, turn 3 (replayed action by action: no dice were rolled)

| Line | Points | Range |
|---|---|---|
| The computer's choice (O4 passes to O3) | **37.9** | 37.6 to 38.1 |
| Attack the overload at once: O2 sprints to H7, O4 passes to O5 | 29.4 | 28.1 to 30.6 |

Before the offence fix, step 21's computer drifted O4 to the corner (27.0) where attacking at once scored 34.0. Now it makes the better play itself.

### B3: X1 beaten up top, O5 open near the rim (the hole), X2 can reach it now, X1 can reach the lane to O2

| Line | Points | Range |
|---|---|---|
| The computer's choice (the defence pauses) | **28.4** | 26.6 to 30.1 |
| Nobody switches: X1 back onto O1, X2 stays on O2 | 29.6 | 28.9 to 30.4 |
| X1 chases to the hole himself | 30.9 | 30.2 to 31.6 |
| The rotation: X2 sprints to the hole (H4), X1 to the lane to O2 (G9) | 33.0 | 33.0 to 33.0 |

**The computer finds the best line.** The rotation as drawn is the worst: X2 leaving O2 gives up more than the hole does here. The map's own answer on this board is a different rotation, from the weak side: X4 drops from the corner to K3 and X1 goes to C11. The computer holds rather than commit, and play agrees with it.

### S3: your screen sequence again (D-209)

| Line | Points | Range |
|---|---|---|
| The offence as it chooses (no screen: O3 to N7, O5 to J7) | **29.2** | 27.5 to 30.8 |
| The screen on the on-ball defender (the T on his square) | 24.6 | 23.1 to 26.1 |
| The screen behind him (the T on his way back) | 25.7 | 24.6 to 26.7 |
| After the screen: the defence's own answer | **24.6** | 22.7 to 26.5 |
| After the screen: X1 challenges it | 25.6 | 24.3 to 27.0 |
| After the screen: the defence pauses | 26.5 | 25.1 to 27.9 |

**The screen still doesn't pay.** It costs 4.6 against the offence's own choice (2.1 to 7.1), and the computer doesn't choose it, even with the defence read as it really is. After the screen the defence's own answer is the best of its three. By your rule (D-209) this is yours to decide: decision 2.

## The design checks this changes

- **Check 6 holds again** (a body on the helper's way leaves more), now that the defence's spent token stays spent. Its expected-failure mark is gone.
- **Checks 2 and 3 still fail** (helping off the non-shooter costs less than off the sharpshooter). That board is a phase start, so the defence really does have all its tokens and recovers whichever man the helper left. It stays marked with your reason.
- Exam position 15 passes.

## Rotation in the Watch game

Game 983FC4: Five Out v High-Low, All-Star against All-Star, the map on. In 87 defence turns the defence made **14 switches** and no full rotation (one defender taking a man while the other picks up someone else). A switch is named only for a defender who moved that turn.

Example (possession 1, phase 2, turn 2): "Defence: X4 moved to E3, facing north (lasting gap from 24 to 18), then X4 quick-stepped to E4 (lasting gap from 18 to 20). That took the lasting gap from 24 down to 20. Switch: X4 took O1 from X1; X4 took O3 from X1."

All eight reports are in `docs/runs/step21/watch/`. Two earlier runs are kept beside them (`watch_first/`, `watch_second/`). Their words came before the last two fixes, which name the right pair in an overload line and only name switches by defenders who moved.

## One possession in full (possession 1)

```
Possession 1: Five Out v High-Low
The setup
  Offence: set up so that, after the defence's best answer, the best it can still force next phase is O2's three on A4, worth 18: X1 covers it.
  Defence: set up to hold the lasting gap to 21. X1 is the only cover for O3's three on J10 and O5's mid-range shot on L4: whichever he takes, the other is open (worth 18).
Phase 1
  Turn 1
    Offence: O2 sprinted to E9 (lasting gap from 21 to 24), then the offence hesitated (lasting gap at 24). The lasting gap rose from 21 to 24.
    Defence: X2 moved to F9, facing north (lasting gap from 24 to 21), then X1 quick-stepped to C7 (lasting gap at 21). That took the lasting gap from 24 down to 21.
  Turn 2
    Offence: O1 moved to I10 (lasting gap at 21), then O4 moved to C2 (lasting gap at 21). The lasting gap stayed at 21.
    Defence: X4 moved to D4, facing north-east (lasting gap from 21 to 24), then X5 moved to P3, facing north-east (lasting gap from 24 to 21). The lasting gap held at 21.
  Turn 3
    Offence: O4 quick-stepped to D3 (lasting gap at 21), then O3 moved to M9 (lasting gap at 21). The lasting gap stayed at 21.
    Defence: X1 moved to F7, facing north-east (lasting gap at 21), then X3 moved to M7, facing west. The phase ended: the next starts with the lasting gap at 18.
  The coach on phase 1
    Offence: The lasting gap went from 21 to 18 this phase: the defence got stronger.
    Offence: Best turn: turn 1, O2 sprinted to E9 (lasting gap from 21 to 24), then the offence hesitated (lasting gap at 24): from 21 to 24.
    Defence: Best answer: turn 1, X2 moved to F9, facing north (lasting gap from 24 to 21), then X1 quick-stepped to C7 (lasting gap at 21): from 24 down to 21.
    Next phase, after the defence's best answer, look for O2's three on A4, worth 18: X1 covers it.
Phase 2
  Turn 1
    Offence: O2 moved to G10 (lasting gap at 18), then O3 moved to P9 (lasting gap from 18 to 21). The lasting gap rose from 18 to 21.
    Defence: X2 moved to H10, facing north (lasting gap from 21 to 20), then X3 moved to M9, facing north (lasting gap from 20 to 18). That took the lasting gap from 21 down to 18. Switch: X2 took O2 from X3.
  Turn 2
    Offence: O1 sprinted to L7 (lasting gap from 18 to 20), then O1 passed to O3 (lasting gap from 20 to 24). The lasting gap rose from 18 to 24.
    Defence: X4 moved to E3, facing north (lasting gap from 24 to 18), then X4 quick-stepped to E4 (lasting gap from 18 to 20). That took the lasting gap from 24 down to 20. Switch: X4 took O1 from X1; X4 took O3 from X1.
  Turn 3
    Offence: O4 sprinted to H3 (lasting gap from 20 to 22), then O3 passed to O4 (lasting gap at 22). The lasting gap rose from 20 to 22. X5 is the only cover for O3's three on Q4 and O4's mid-range shot on L2: whichever he takes, the other is open (worth 22).
    Defence: X1 sprinted to I4, facing east (lasting gap from 22 to 27), then X5 moved to N5, facing south. The phase ended: the next starts with the lasting gap at 18.
  The coach on phase 2
    Offence: The lasting gap held at 18 this phase.
    Offence: Best turn: turn 2, O1 sprinted to L7 (lasting gap from 18 to 20), then O1 passed to O3 (lasting gap from 20 to 24): from 18 to 24.
    Defence: Best answer: turn 2, X4 moved to E3, facing north (lasting gap from 24 to 18), then X4 quick-stepped to E4 (lasting gap from 18 to 20): from 24 down to 20.
    Next phase, after the defence's best answer, look for O2's layup on G3, worth 18: X4 covers it.
Phase 3
  Turn 1
    Offence: O4 moved to G4 (lasting gap at 18), then O4 passed to O3 (lasting gap from 18 to 22). The lasting gap rose from 18 to 22. X5 is the only cover for O3's three on Q4 and O4's mid-range shot on N4: whichever he takes, the other is open (worth 22).
    Defence: X2 quick-stepped to I9 (lasting gap at 22), then X1 moved to I7, facing east (lasting gap from 22 to 20). That took the lasting gap from 22 down to 20. Switch: X1 took O5 from X5.
  Turn 2
    Offence: O3 moved to P7 (lasting gap at 20), then O1 moved to K5 (lasting gap from 20 to 22). The lasting gap rose from 20 to 22. X5 is the only cover for O3's three on Q2 and O4's mid-range shot on M2: whichever he takes, the other is open (worth 22).
    Defence: X2 moved to F9, facing north (lasting gap from 22 to 18), then the defence paused (lasting gap at 18). That took the lasting gap from 22 down to 18.
  Turn 3
    Offence: O2 moved to E10 (lasting gap from 18 to 22), then O5 moved to Q4 (lasting gap at 22). The lasting gap rose from 18 to 22. X5 is the only cover for O3's three on Q2 and O4's mid-range shot on N4: whichever he takes, the other is open (worth 22).
    Defence: X3 moved to N9, facing south-east (lasting gap at 22), then X1 quick-stepped to K7. The phase ended: the next starts with the lasting gap at 14. Three seconds: O4 was in the key when two phases in a row ended.
  The coach on phase 3
    Offence: The lasting gap went from 18 to 14 this phase: the defence got stronger.
    Offence: Best turn: turn 1, O4 moved to G4 (lasting gap at 18), then O4 passed to O3 (lasting gap from 18 to 22): from 18 to 22.
    Defence: Best answer: turn 2, X2 moved to F9, facing north (lasting gap from 22 to 18), then the defence paused (lasting gap at 18): from 22 down to 18.
    Next phase, after the defence's best answer, look for O3's layup on J2, worth 14: X4 covers it. X2 is the only cover for O2's three on A7 and O4's three on E9: whichever he takes, the other is open (worth 9).
Phase 4
  Turn 1
    Offence: O3 sprinted to L7 (lasting gap from 14 to 22), then O3 took on X1 off the dribble (X1 stopped the dribble) (lasting gap at 22). The lasting gap rose from 14 to 22. X5 is the only cover for O3's three on Q3 and O4's mid-range shot on M2: whichever he takes, the other is open (worth 22).
    Defence: X5 moved to P3, facing north (lasting gap from 22 to 18), then the defence paused (lasting gap at 18). That took the lasting gap from 22 down to 18.
  Turn 2
    Offence: O3 passed to O2 (lasting gap at 18). The lasting gap stayed at 18.
    Defence: X2 moved to F10, facing north (lasting gap from 18 to 17), then the defence ended its turn (lasting gap from 17 to 20). The answer let the lasting gap rise from 18 to 20.
  Turn 3
    Offence: O2 moved to C8 (lasting gap from 20 to 18), then O2 shot a three.
    Defence: X4 quick-stepped to E5, then X4 moved to D7, facing west. The possession ended.
  The coach on phase 4
    Offence: Turn 3: the shot went up with the defence not broken.
    Offence: Best turn: turn 1, O3 sprinted to L7 (lasting gap from 14 to 22), then O3 took on X1 off the dribble (X1 stopped the dribble) (lasting gap at 22): from 14 to 22.
    Defence: Turn 3: the shot went up against them.
    Defence: Best answer: turn 1, X5 moved to P3, facing north (lasting gap from 22 to 18), then the defence paused (lasting gap at 18): from 22 down to 18.
    Defence: Turn 2: the answer let the lasting gap rise from 18 to 20.
The coach on the possession
  Weak: the defence was never broken.
  The shot: O2's three from C8. Open, it was worth 33; the contest took 12 off, leaving 21.
  Scored 16 (Okay): turnovers -5. Three seconds: O4 was in the key when two phases in a row ended (phase 3, turn 3).
  The shot taken was the best one the measure saw all possession.
  The lasting gap at the start of each phase: 21, 18, 18, 14.
  Offence: Keep: phase 4, turn 1: the lasting gap rose from 14 to 22.
  Offence: Change: phase one only got you into position. Set up with a plan to weaken the defence from the start.
  Defence: Keep: phase 2, turn 2: the answer took the lasting gap from 24 down to 20.
  Defence: Change: phase 4, turn 2: the answer let the lasting gap rise from 18 to 20.
Played with: the heat map on for both sides; computer {'O': 'allstar', 'X': 'allstar'}
```

## What still looks illogical (reported, not fixed)

1. **Three-second violations.** The offence leaves a player in the key across two phase ends and loses 5: possession 1 (O4, phase 3), possession 3 (O5, twice) and possession 5 (O2). Possession 3 scored 9 with "turnovers -10".
2. **Hesitating after one action.** Possession 1, phase 1, turn 1: "O2 sprinted to E9 (lasting gap from 21 to 24), then the offence hesitated." The same happens in possessions 2, 3 and 4.
3. **Screens that change nothing.** Possession 6, turns 1 and 2: "O3 set a screen (lasting gap at 26)", then "O2 set a screen (lasting gap at 26)". The same in possessions 4 and 8.
4. **The defence ending its turn when that raises the gap.** Possession 1, phase 4, turn 2: "X2 moved to F10 (lasting gap from 18 to 17), then the defence ended its turn (lasting gap from 17 to 20)." Reading the defence as it really is shows the cost of giving up its tokens, but the computer still did it.
5. **A defender's move that makes things worse.** Possession 1, phase 2, turn 3: "X1 sprinted to I4, facing east (lasting gap from 22 to 27)."
6. **Drifting to the baseline corners.** Possession 2: "O5 moved to P1". Possession 4: "O5 moved to Q1 (lasting gap from 26 to 21)".
7. **B1 above:** the map can't separate X1's options where play can.

## Part 5: one map, after every action

- The coverage view asks for the map again after every action by either side: action 1, action 2, Hesitate, Pause, End turn, and any roll's result. The shading, the overload and switch marks, the words and the lasting gap all come from the board as it stands. The words say when the map is from.
- Each action's line in the report carries its own change ("O1 moved to H10 (lasting gap from 18 to 22), then O1 passed to O2 (lasting gap at 22)"), so a turn's two actions are counted apart. Phase starts and the setup are read like for like, where both sides really are fresh. A turn that ends a phase isn't put on the defence: "The phase ended: the next starts with the lasting gap at 18."
- The step-through replays read the same map.
- A test plays three actions and checks that the view, the report, the replay and the computer's own reading give the same number from the same position.

## Smaller changes

- **Overload words** name the look the defence's best assignment takes and the one it leaves open. One line had named two looks on the same square. Groups of two or three are named only when they are worth at least the best open look, so they explain the gap.
- **A pass in the air** is read by the rules' chance of the catch. Caught, it is the receiver's lasting gap; intercepted, it is -5 and the next phase read fresh. The search now reads it (step 20 fell back to its older reading there).
- **All-Star's setup** chooses among the placements within its 2-point margin each possession (D-208).
- **A latent cache fault fixed.** The Python engine's pass-chance caches keyed on the board's context id. Once a context is freed its id can come back for a new one, and a new board then read an old board's chance. They now key on the context itself.

## Tests

Run on their own (no full suite):

- **`tests/test_map_logic_21.py`, new: 10 pass.** They cover:
  - the rulings are recorded;
  - a spent defence can't answer;
  - the group rule on your 3 on 2, plus one on two, three on four, and two attackers too close to count;
  - overloads on the board follow the rule;
  - the search tries the map's answer;
  - switch and rotation words;
  - a pass in the air;
  - setup variety;
  - one map for the view, report, replay and computer;
  - each action's own change in the report.
- **Re-recorded, each with its reason in the test:**
  - step 20's like-for-like test, now on the reports' fresh read;
  - step 20's overload test, now on the group rule;
  - step 18s's tokens test, back to what it first asked (the answer stays inside the tokens left);
  - check 6's expected-failure mark removed (it holds);
  - checks 2 and 3: reason updated.
- **`tests/test_rules_current.py`, the golden tests, both engine-equality tests** (random states, and the whole search the same number of turns ahead), **plus steps 18s, 19 and 20's tests, `tests/test_web.py`, `tests/test_computer.py`, `tests/test_static.py` and exam position 15:** all pass but `test_a_play_cannot_run_past_the_end_of_its_turn`, which fails on `main` too (as in step 20).
- **The engines agree on the lasting gap, the groups and the answer:** 60 of 60 random positions, two of them with a pass in the air (`docs/runs/step21/lasting_equal.json`).

## Compute

**About 23 core-hours against an estimate of 17.6** (`docs/runs/step21/ESTIMATE.md`; the stop was 35).

| Part | Core-hours |
|---|---|
| B1, B2, B3, the first full run (before the offence fix; kept in `lines_before_the_offence_fix.json`) | 4.6 |
| B1, B2, B3, the final run | 7.3 |
| S3 at 16 a line | 9.6 |
| Three Watch games, the equality runs, the tests | about 1.5 |

- **The first B run cost 4.6 and was needed.** It is what showed the offence fault.
- **S3 cost 9.6 against the 12 estimated.**
- **Two runs I stopped early** (about 0.5 between them): the search wasn't yet trying the map's answer (the arrow match missed Quick Steps and Sprints), and a first S3 had started on the computer before the offence fix.

## Decisions for you (three)

1. **The offence read fresh, the defence as it really is.** Your ruling named the defence. I kept the offence's full turn to come, because reading the offence's spent tokens too lost every look that needs a pass next phase (B2: the map read 16 where play got 34). **I recommend keeping it.** If you want the offence read as it really is as well, the map's horizon has to reach into the next phase's first turn, which is a bigger change.
2. **The Screen rule.** S3 again: the screen costs 4.6 against the offence's own play, and the computer doesn't choose it. **I recommend trying "the T holds the defender it sits on" by forced lines on S3,** as step 18s proposed. It is the smallest change that gives the screen something to win.
3. **B1, the map that can't separate X1's options.** **I recommend making it the next step's first job:** play out the four lines with the map's reading printed at every action, find where it and play part, and fix the reading there.

## Model advice

Claude Fable 5.2, effort high, for the next step. It is a reading fault found by forced lines in two engines that must stay equal.
