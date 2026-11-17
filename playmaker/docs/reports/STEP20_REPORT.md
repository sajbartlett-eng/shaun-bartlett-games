# Step 20: the heat map fixed, and on for both sides

**In five lines.**

- **The heat map now shows what stays open after the defence's best answer.** Each square is shaded by what the offence can still get there next phase once the defence has moved its five (arrows turned included). A switch shows "now", before it answers.
- **A ringed defender with "!" is overloaded:** the only cover for two attackers' looks. Whichever he takes, the other is open.
- **One number runs everything: the lasting gap,** the best open look or the look an overload leaves, whichever is higher. The offence plays to raise it, the defence to lower it, and when it can't, to leave the cheapest one. That is the whole of each side's logic, at every level, in both engines.
- **The reports read it like for like,** so a phase ending can't move it, each change goes to the side that made it, every roll and every plus or minus 5 is in its line, and a claim the numbers can't back is never printed.
- **Look for:** whether the defence's answers look like help and recover, whether the offence goes at the defender it has overloaded, and whether possessions still drift. Try Watch the computer with Coverage shown.

**Branch:** `step-20-heat-map`, from `main` after PRs 80 and 81. The pull request is open and not merged. `dist/playmaker.html` is built from the final commit.

**Changes to the printed game:** none (D-190). No rule or card value moved.

## What changed

- **The lasting gap** (both engines, `engine.js` `lastingOf`, `decide.py` `lasting_of`). Read from the position as a fresh phase finds it: the offence's full turn to come, the defence's tokens full, whatever either side has spent. The defence's answer is found by search over its real moves (each defender one movement at most: a Move to any square with any arrow, turning on the spot included, a Quick Step or a Sprint), ranked by the highest look it leaves, then the next highest. An overload is a defender who is the only cover for looks from two attackers who stand at least three squares apart (so no one square is next to both); it is worth the smaller of the two, what is left once he takes the bigger. No weight is set by hand.
- **The computer plays from it** (D-204): every line it weighs ends worth what is banked plus the larger of the shot that can go up now and the lasting gap. It is in points already, so it is used as it is, with no fitted line. Step 18s's fitted line is no longer read. `eval.map` is `true` in `ai_profiles.json`: both sides, every level, the app, Watch the computer and the reports. `?map=0` turns it off for a game.
- **The server's computer plays on the fast engine** (the JavaScript one, in Node), as the one-file version already does: the Python engine reads a lasting gap in about 480 ms, the fast one in 24.
- **The coverage view:** after the answer by default, "now" on a switch, overload rings with a dashed line to each of the two looks, and the line of words.
- **The reports** (`report.py`): see part 2 below.
- **Fresh dice, and a fresh computer, each possession** (`game.py`). See the dice below.
- **Decisions recorded:** D-203 (the map on, both sides, no matter what), D-204 (each side's logic is the lasting gap), D-205 (your playtest is the gate).

## Part 1: the hand checks

Three boards: yours of 15 November, the screen board (step 18s, S3) and the closeout board (step 18d). The data is `docs/runs/step20/hand.json`.


#### Shaun, 15 Nov

Before the answer the best look is worth 34; the lasting gap is 24.

```
      A   B   C   D   E   F   G   H   I   J   K   L   M   N   O   P   Q  
 14   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 13   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 12   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 11   .   .   .   .   .   .   .   .  O1*  .   .   .   .   .   .   .   .  
 10   .   .   .   .   .   .   .   .   .   X1  .   .   .   .   .   .   .  
  9   .   .   O2  .   .   .   .   .   .   .   .   .   .   .   O3  .   .  
  8   .   .   .   X2  .   .   .   .   .   .   .   .   .   .   X3  .   .  
  7   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  6   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  5   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  4   .   X4  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  3   O4  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   O5 
  2   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   X5  .  
  1   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
```

After the defence's best answer (LG: the square it leaves; Va/Vb: an overloaded defender's two looks):

```
      A   B   C   D   E   F   G   H   I   J   K   L   M   N   O   P   Q  
 14   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 13   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 12   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 11   .   .   .   .   .   .   .   .  O1*  .   .   .   .   .   .   .   .  
 10   .   .   .   .   .   .   .   .   .   X1  .   .   .   .   .   .   .  
  9   .   .   O2  .   .   .   .   .   .   .   .   .   .   .   O3  .   .  
  8   .   .   .   X2  .   .   .   .   .   .   .   .   .   .   .   .   .  
  7   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  V1a 
  6   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  5   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  4   .   .   .   .   .   X4  .   .   .   .   X3  .   .   .   .   .  V1b 
  3   O4  .   .   .   .   .   LG  .   .   .   .   .   .   .   .   .   O5 
  2   .   .   .   .   .   .   .   .   .   .   .   .   X5  .   .   .   .  
  1   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
```

The defence's best answer: X3 to K4, X4 to F4, X5 to M2. That leaves a post shot for O4 on G3, worth 24: X4 covers it. X3 is the only cover for O3's three on Q7 and O5's three on Q4: whichever he takes, the other is open (worth 18).

#### the screen board

Before the answer the best look is worth 34; the lasting gap is 26.

```
      A   B   C   D   E   F   G   H   I   J   K   L   M   N   O   P   Q  
 14   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 13   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 12   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 11   .   .   .   .   .   .   .   .  O1*  .   .   .   .   .   .   .   .  
 10   .   .   .   .   .   .   .   .   X1  O5  .   .   .   .   .   .   .  
  9   .   .   O2  .   .   .   .   .   .   .   X5  .   .   .   O3  .   .  
  8   .   .   .   X2  .   .   .   .   .   .   .   .   .   .   X3  .   .  
  7   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  6   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  5   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  4   .   X4  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  3   O4  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  2   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  1   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
```

After the defence's best answer (LG: the square it leaves; Va/Vb: an overloaded defender's two looks):

```
      A   B   C   D   E   F   G   H   I   J   K   L   M   N   O   P   Q  
 14   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 13   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 12   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 11   .   .   .   .   .   .   .   .  O1*  .   .   .   .   .   .   .   .  
 10   .   .   .   .   .   .   .   .   .   O5  .   .   .   .   .   .   .  
  9   .   .   O2  .   .   .   .   .   .   .   X5  .   .   .   O3  .   .  
  8   .   .   .   X2  .   .   .   .   .   .   .   .   .   .   .   .   .  
  7   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  6   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  5   .   .   .   .   .   .   .   .   X1  .   .   .   .   .   .   .   .  
  4   .   .   .   .   X4  .   .   .   .   LG  X3  .   .   .   .   .   .  
  3   O4  .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  2   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  1   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
```

The defence's best answer: X1 to I5, X4 to E4, X3 to K4. That leaves a post shot for O5 on J4, worth 26: X4 covers it.

#### the closeout board

Before the answer the best look is worth 24; the lasting gap is 24.

```
      A   B   C   D   E   F   G   H   I   J   K   L   M   N   O   P   Q  
 14   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 13   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 12   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 11   .   .   .   .   .   .   .   .   O1  .   .   .   .   .   .   .   .  
 10   .   .   .   .   .   .   .   .   X1  .   .   .   .   .   .   .   .  
  9   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  8   .   .   X2  .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  7   .   O2  .   .   .   .   .   .   .   .   .   .   .   .   X4  O3  .  
  6   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  5   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  4   .   .   .   .   .   X3  .   .   .   .   .   .   .   .   .   .   .  
  3  O4*  .   .   .   .   .   .   .   .   .   .   .   .   .   .   X5  O5 
  2   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  1   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
```

After the defence's best answer (LG: the square it leaves; Va/Vb: an overloaded defender's two looks):

```
      A   B   C   D   E   F   G   H   I   J   K   L   M   N   O   P   Q  
 14   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 13   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 12   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
 11   .   .   .   .   .   .   .   .   O1  .   .   .   .   .   .   .   .  
 10   .   .   .   .   .   .   .   .   .  V1b  .   .   .   .   .   .   .  
  9   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  8   .   .   X2  .   .   .   .   .   .   .   .   .   .   .   .   .   .  
  7   .   O2  .   .   .   .   .   .   .   .   .   .   .   .   X4  O3  .  
  6   .   .   .   .   .   .   .   .   X1  .   .   .   .   .   .   .   .  
  5   .   .   .   X3  .   .   .   .   .   .   .   .   .   .   .   .   .  
  4   .   .   .   .   .   .   .   .   .  V1a  .   .   .   .   .   .   .  
  3  O4*  .   .   .   .   .   .   .   .   .   .   .   .   .   .   X5  O5 
  2  V2a  .   .  V2b  .   .   LG  .   .   .   .   .   .  V3b  .   .  V3a 
  1   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .   .  
```

The defence's best answer: X3 to D5, X1 to I6. That leaves a layup for O2 on G2, worth 20: X1 covers it. X1 is the only cover for O3's layup on J4 and O1's three on J10: whichever he takes, the other is open (worth 21). X3 is the only cover for O4's three on A2 and O2's floater on D2: whichever he takes, the other is open (worth 24). X5 is the only cover for O5's three on Q2 and O3's floater on N2: whichever he takes, the other is open (worth 20).


**My read of the three:**

- **Your board.** The answer packs the paint against the point guard's open layup lane (34 before the answer): X3 drops from the wing to K4, X4 from the corner to F4, X5 to M2. What is left is O4's post shot on G3 (24, X4 on it) and the overload on X3: he is the only cover for O3's three on the wing and O5's three in the corner. That is the help-and-recover picture: sensible, and the overload is real (one man, two shooters on the same side).
- **The screen board.** The same shape: X1 sinks to I5, X4 and X3 into the lane. O5's post on J4 is left (26). No overload: every remaining look has two defenders who can get there.
- **The closeout board.** Three overloads, all real on the board: X1 between O3's layup and O1's three up top, X3 between the corner shooter's three and O2's floater, X5 between O5's corner three and O3's floater. The lasting gap is the 24 that X3's overload leaves, more than the best open look (20).
- **The shading and the words agree** on all three: the darkest square after the answer is the square the words name, at the same number (tested).

## Part 2: the reports, ruler fixed

| Shaun's 4E81CC finding | Now |
|---|---|
| It fell whenever the offence acted (spent actions) | Read like for like: the same position reads the same whatever has been spent (tested) |
| It jumped at every phase end and the defence was blamed | A phase ending can't move it by itself. The last phase has no next phase, so its number is left out ("the last phase begins: only a shot counts now") instead of falling to 0 |
| "No turn raised their best look" beside "the defence got weaker" | "Weaker" or "stronger" only when a turn in that phase made it so; otherwise the line says only what the number did. A check records any line that slips through (none in 16 possessions) |
| Possession 7: "fouls +5, turnovers −10" with no word about either | Every roll is in its line ("took on X5 off the dribble (X5 stopped the dribble)", "went for the steal (the steal won the ball)") and every plus or minus 5 too ("Stolen: −5", "Pass intercepted: −5"), and again in the score line with its phase and turn |
| The setup line used the before number | The setup line uses the after-the-answer number |
| "X2 now has O1, O2, O3 and O4 to cover" | Gone. Overloads are named only as part 1 defines them |
| "Good: the defence broke" with no break | "Good" only when the shot went up with the defence broken by the measure; "the best one the measure saw" only when it was |

**The dice.** Possessions 4 and 6 of 4E81CC were the same twice over, and the cause was two things. The dice: each possession now gets its own, from the seed and the possession's number when a seed is set (so a game replays), fresh otherwise. And the computer: its own variety (its small random choices between near-equal turns) restarted from the game's seed every possession, so the same teams in the same seats replayed the same possession whenever the dice fell the same. It now gets a fresh stream each possession too. Both are tested.

**What still repeats.** In the new game (below) possessions 1, 3 and 5 are the same short possession, and 2, 4 and 8 open the same way. No dice were rolled in any of them. All-Star varies only between turns within 2 points of its best, and here the best was clear. That is the computer, not the dice: decision 2.

## Part 4: the new eight possessions

Game 799D78: Five Out v High-Low (4E81CC's teams), All-Star against All-Star, the map on for both sides. Eight possessions, 21, 24, 21, 26, 21, 18, 15, 27. Every report is in `docs/runs/step20/watch2/` (text and data); a first run before the last fixes is in `watch1/`. I read all sixteen. The lines that still contradicted themselves in the first run were fixed in the builder (the score line named "O5 is locked" as a plus or minus 5, and a steal into the last phase read as the defence taking the number to 0). None remain in the second run, and none of the computer's play was tuned to them.

### Possession 4 in full

```
Possession 4: Five Out v High-Low
The setup
  Offence: set up so that, after the defence's best answer, the best it can still force next phase is O2's three on A4, worth 18: X1 covers it.
  Defence: set up to hold the lasting gap to 21. X1 is the only cover for O2's long two on J9 and O3's floater on L4: whichever he takes, the other is open (worth 20).
Phase 1
  Turn 1
    Offence: O1 moved to I10, then O3 moved to M9. The lasting gap rose from 21 to 26. X2 is the only cover for O1's three on D9 and O2's three on A7: whichever he takes, the other is open (worth 21).
    Defence: X1 quick-stepped to K9, then X3 moved to O5, facing south. That took the lasting gap from 26 down to 20.
  Turn 2
    Offence: O5 moved to Q4, then O1 passed to O5. The lasting gap rose from 20 to 26.
    Defence: The defence paused. The lasting gap held at 26.
  Turn 3
    Offence: O2 moved to D9, then the offence ended its turn. The lasting gap stayed at 26.
    Defence: X2 moved to D8, facing north, then X5 moved to P3, facing north. That took the lasting gap from 26 down to 18.
  Turn 4
    Offence: O5 passed to O1. The lasting gap rose from 18 to 26. X1 is the only cover for O1's three on J10 and O3's three on M9: whichever he takes, the other is open (worth 24).
    Defence: X1 moved to J8, facing north-east. That took the lasting gap from 26 down to 21.
  The coach on phase 1
    Offence: The lasting gap held at 21 this phase.
    Offence: Best turn: turn 4, O5 passed to O1: from 18 to 26.
    Defence: Best answer: turn 3, X2 moved to D8, facing north, then X5 moved to P3, facing north: from 26 down to 18.
    Next phase, after the defence's best answer, look for O4's post shot on G2, worth 20: X3 covers it. X4 is the only cover for O2's floater on D2 and O1's three on A2: whichever he takes, the other is open (worth 21).
Phase 2
  Turn 1
    Offence: O1 moved to J10, then O5 moved to N4. The lasting gap rose from 21 to 26.
    Defence: X1 quick-stepped to I8, then X2 moved to D8, facing north-east. That took the lasting gap from 26 down to 21.
  Turn 2
    Offence: O2 moved to E9, then O1 passed to O2. The lasting gap rose from 21 to 26. X2 is the only cover for O1's three on E10 and O3's three on H10: whichever he takes, the other is open (worth 24).
    Defence: X3 quick-stepped to N5, then the defence paused. The lasting gap held at 26.
  Turn 3
    Offence: O3 moved to M10, then O2 quick-stepped to E10. The lasting gap stayed at 26.
    Defence: X3 moved to L7, facing west, then X4 moved to E4, facing west. That took the lasting gap from 26 down to 16.
  The coach on phase 2
    Offence: The lasting gap went from 21 to 16 this phase: the defence got stronger.
    Offence: Best turn: turn 1, O1 moved to J10, then O5 moved to N4: from 21 to 26.
    Defence: Best answer: turn 3, X3 moved to L7, facing west, then X4 moved to E4, facing west: from 26 down to 16.
    Next phase, after the defence's best answer, look for O2's layup on G4, worth 16: X3 covers it. X4 is the only cover for O2's three on A4 and O4's mid-range shot on D2: whichever he takes, the other is open (worth 5).
Phase 3
  Turn 1
    Offence: O5 moved to K4, then O2 passed to O4. The lasting gap rose from 16 to 26. X1 is the only cover for O1's three on J10 and O5's long two on N7: whichever he takes, the other is open (worth 14).
    Defence: X4 moved to B4, facing east, then X2 moved to C8, facing north. That took the lasting gap from 26 down to 20.
  Turn 2
    Offence: O4 moved to A5, then O1 moved to G10. The lasting gap rose from 20 to 32. X1 is the only cover for O1's three on L10 and O2's three on I10: whichever he takes, the other is open (worth 21).
    Defence: X3 moved to J5, facing south-east, then X1 moved to G9, facing west. That took the lasting gap from 32 down to 26.
  Turn 3
    Offence: O2 sprinted to H7, then O1 quick-stepped to E10. The lasting gap rose from 26 to 34. X3 is the only cover for O5's post shot on K2 and O2's layup on H2: whichever he takes, the other is open (worth 34).
    Defence: X3 quick-stepped to I4, then X1 quick-stepped to G8. That took the lasting gap from 34 down to 26.
  The coach on phase 3
    Offence: The lasting gap went from 16 to 26 this phase: the defence got weaker.
    Offence: Best turn: turn 2, O4 moved to A5, then O1 moved to G10: from 20 to 32.
    Defence: Best answer: turn 3, X3 quick-stepped to I4, then X1 quick-stepped to G8: from 34 down to 26.
    Next phase, after the defence's best answer, look for O5's post shot on G2, worth 26: X3 covers it. X2 is the only cover for O1's three on E10 and O2's three on H10: whichever he takes, the other is open (worth 21).
Phase 4
  Turn 1
    Offence: O4 passed to O3. The lasting gap stayed at 26.
    Defence: X1 moved to I10, facing east, then X4 moved to D5, facing north-west. The lasting gap held at 26.
  Turn 2
    Offence: O3 passed to O5. The lasting gap stayed at 26.
    Defence: The defence paused. The lasting gap held at 26.
  Turn 3
    Offence: O1 set a screen. The lasting gap stayed at 26.
    Defence: X2 moved to C8, facing north-east, then the defence ended its turn. The lasting gap held at 26.
  Turn 4
    Offence: O5 shot a post shot.
    Defence: X3 moved to J3, facing north, then the defence ended its turn. The possession ended.
  The coach on phase 4
    Offence: Turn 4: the shot went up with the defence not broken.
    Defence: Turn 4: the shot went up against them.
The coach on the possession
  Weak: the defence was never broken.
  The shot: O5's post shot from K4. Open, it was worth 36; the contest took 10 off, leaving 26.
  Scored 26 (Great).
  The shot taken was the best one the measure saw all possession.
  The lasting gap at the start of each phase: 21, 21, 16, 26.
  Offence: Keep: phase 3, turn 2: the lasting gap rose from 20 to 32.
  Offence: Change: phase one only got you into position. Set up with a plan to weaken the defence from the start.
  Defence: Keep: phase 2, turn 3: the answer took the lasting gap from 26 down to 16.
Played with: the heat map on for both sides; computer {'O': 'allstar', 'X': 'allstar'}
```

### What still looks illogical in the computer's play (reported, not fixed)

1. **The same possession, again and again.** Possessions 1, 3 and 5: "O2 moved to B7, then O1 passed to O2", then "O2 shot a three", 21 each time. Possessions 2, 4 and 8 open with the same setup and the same first turn ("O1 moved to I10, then O3 moved to M9").
2. **Screens that change nothing.** Possession 2, phase 2, turns 3 and 4: "O1 set a screen. The lasting gap stayed at 26." and "O5 set a screen. The lasting gap stayed at 26." Again in possession 2 phase 3 turn 2, possession 4 phase 4 turn 3, possession 8 phase 2 turns 2 and 3. The screen still buys nothing on the map (step 18s, S3: your Screen ruling is still open).
3. **Gaps made and not used.** Possession 8: the lasting gap sat at 26 for seven turns across phases 2 and 3 ("No turn raised the lasting gap this phase"), with passes and screens, before a three in phase 4. Possession 4, phase 3, turn 3: the offence overloaded X3 ("the only cover for O5's post shot on K2 and O2's layup on H2", 34), the defence answered, and phase 4 was three passes and a screen before the post shot.
4. **Hesitates.** Fewer than in 4E81CC: possession 6, phase 2, turn 1 and possession 8, phase 3, turn 1, each with the lasting gap at 26.
5. **The defence pausing on a raised gap.** Possession 4, phase 1, turn 2, and possession 8, phase 1, turn 2: "O1 passed to O5. The lasting gap rose from 20 to 26." then "The defence paused. The lasting gap held at 26."
6. **Drifting to the edges.** Much less than in 4E81CC. The first run had "O4 moved to A1, then O5 shot a post shot" (possession 2, phase 6) and X1 drifting deep to J13 and I12 (possession 7).
7. **A defender leaving the shot.** First run, possession 1, turn 3: O2 shot a three from E9 and "X2 moved to P10", the far side.

## The checks (run and reported, not gating)

All with the map on for both sides (today's default), All-Star against All-Star, 8 play-outs a line on the same dice (step 18s used 16, so its ranges here are wider). The data is in `docs/runs/step20/`.

| Check | Result | Computer or measure? |
|---|---|---|
| **Exam position 15** (goal consistency) | **Passes** now, with the map on (`exam15.txt`). It was the reason the map stayed off in step 18s. It stays marked as an expected failure with your reason, so it can't stop the switch either way | |
| **Design check 1** (the clear lane is a big gap and the answer shrinks it) | Holds: 34 before the answer, 24 after | |
| **Checks 2 and 3** (helping off the non-shooter costs less than off the sharpshooter) | **Fail.** Helping off the non-shooter reads 22, off the sharpshooter 21, staying home 24 | **The measure.** The defence gets a fresh phase to answer, so where a helper stands now counts for little: both recover. Decision 1 |
| **Checks 4 and 5** (arrows matter; the reaction gives a fresh defender a square contest) | Hold | |
| **Check 6** (a body on the helper's way leaves more) | **Fails:** 24 either way | **The measure,** the same cause: the one token the board leaves the defence becomes a full phase of movement, and the helper gets round the body |
| **Closeout, the shooter can't move** | The computer's pick is the best line by play (24.0, against 33.0 for the old "right" answer) | |
| **Closeout, step 2** | The computer's pick is the best line (22.4) | |
| **Game EB3F5B, the pass in the air** | **Fails:** the computer's pick gives up 28.0, the Pause (what the log did) 24.0, 4 worse | **The computer.** It moves X5 to M3 and reads that at 21; play gives 28. The map reads a pass in the air as caught, so a move made for after the catch can read better than it plays. One position: worth watching for in your playtest |
| **Check 7** (the offence takes an open lane; the answer leaves the least) | **Holds for the offence where it chooses:** lane open 28.2 (22.8 to 33.7) against 24.5 without the map; your board 26.8 (23.9 to 29.6) against 24.8. Help in the lane: level (19.6 both). Made to sprint into the lane: 24.0 against 27.8 | Mixed. The forced sprint is worse with the map on: the defence's answer after it is better too, which is the defence playing from the map, as it should |
| **Check 8 and S2** (the turn picked against the others weighed) | Offence: its pick 24.5, its last choice 24.9: level. Defence: its pick 26.5 against the turn the map calls weakest, 29.0: the pick is 2.5 better, the right way. But the defence's last choice, which the map reads at 34, played 24.0: the best of the three | **The measure,** on that one turn: the lasting gap reads a Pause that leaves a defender in place as worse than play finds it |
| **S1** (a body or a move that pulls a covering defender off reads as weakening) | Holds by the map in part 1 (the overloads it names come from bodies and moves). A screen's own effect is still inside the phase only | |
| **S3** (your screen sequence) | The screen still doesn't pay: the screen on the on-ball defender 24.0 against the offence's own choice 26.1 (−2.1, −4.6 to 0.4), and the computer doesn't choose it. After the screen the defence's own answer (24.0) is better than a Challenge (28.8) or a Pause (28.6) | **The rule,** as in step 18s: decision 3 |
| **S4** (setup planned for the first phase) | **Not run (Shaun, 17 Nov: playtest is the gate).** For the record, it finished just as the stop came: on 4 deals, 4 play-outs each, the setup judged by the map for both sides scored 29.5 (26.9 to 32.1) against 25.9 (23.4 to 28.5) for the setup as it was, and started the defence stronger (20.5 against 23.5). Too few play-outs to rest on | |
| **Check 9** (the system map's checks 10 to 12) | Not run again: nothing in the scout or the goals changed | |


## Tests

Run on their own (no full suite), with the map on:

- **New, `tests/test_heat_map_20.py`: 13 pass.** The rulings and the switch; the lasting gap is what the answer leaves; the shading agrees with the words; overloads are one defender, two attackers, worth the smaller look; the answer stays within one movement each; the measure is like for like; both engines agree on the number, the answer and the overloads; the search reads it for both sides; a game plays with it on unless it asks otherwise; fresh dice and a fresh computer each possession, a seed replays; every roll and every plus or minus 5 is in its line and no report contradicts itself; the roll words follow the rules' own outcomes; the consistency check catches a "weaker" no turn made.
- **`tests/test_coverage_18s.py` and `tests/test_strength_18s.py`: 28 pass, 2 expected failures** (checks 2 and 3, check 6, with your reason). Re-recorded, each with its reason in the test: check 1 (the answer is found jointly, so no answer-by-answer "leaves"), the tokens test (like for like), strength and fragility (now the lasting gap and the overloads), the map's reading (now the lasting gap, not a fitted line) and the default (on).
- **`tests/test_rules_current.py`, the golden tests and both engine-equality tests** (random states, and the whole search on one position, the same number of turns ahead): **28 pass.** Nothing needed re-recording: the golden games run under rules the map doesn't read.
- **`tests/test_ux_19.py`: 6 pass. `tests/test_web.py`, `tests/test_computer.py`, `tests/test_static.py`: all pass but one,** `test_a_play_cannot_run_past_the_end_of_its_turn`, which fails on `main` too (a stored game from before D-184, as step 18s reported). Two browser tests timed out once while the play checks had all four cores; both pass on their own. One real break I made and mended: the overload ring sat over a map square and took its tap.
- **Exam position 15:** passes (above). The banned-word tests: pass.
- `tests/test_step3m.py` gains exam position 15 in its list of expected failures with your reason; nothing else was loosened.

## Compute

**About 19 core-hours.** No estimate was set for this step.

| Part | Core-hours |
|---|---|
| The play checks: closeout 2.5, check 7 3.3, check 8 3.2, S3 6.0, S4 3.5 | 18.3 |
| The two eight-possession games (one core each, 5 and 6 minutes) | 0.2 |
| The engines' equality run, the hand checks, exam position 15 | 0.1 |
| The tests | about 0.5 |

- **S3 alone was 6.0:** its six lines each play a full possession at All-Star's full thinking time with the map read at every line's end, both sides.
- **Speed (D-200, waived):** the fast engine reads a lasting gap in 24 ms, the Python one in 480. An All-Star possession took 10 to 90 seconds in the Watch game, at the same thinking time as before.

## Decisions for you (three)

1. **The defence's tokens in the lasting gap.** Today the map gives the defence a fresh phase to answer, whatever it has spent. That is what stops a phase ending from moving the number, and it is why design checks 2, 3 and 6 now fail: where a helper stands now, or a defender who has used his tokens, counts for little when he gets a full phase to recover. The other way is to read the defence's tokens left this phase. **I recommend keeping today's read through your playtest,** and if the defence looks too good at recovering, trying the tokens-left read for the computer's own decisions while the reports stay like for like.
2. **Variety at All-Star.** With no dice rolled, All-Star replays the same possession (1, 3 and 5 above). **I recommend letting its setup choose among the placements within its 2-point margin each possession,** the same rule its turns already use. It changes no reading.
3. **The Screen rule** (open since step 18s). Screens still buy nothing on the map, and the computer still sets them. **I recommend trying "the T holds the defender it sits on" by forced lines,** as step 18s proposed, now that the map can show what a screen leaves.

## Model advice

Claude Fable 5.2, effort high, for the next step if it changes what the computer plays (both engines must stay equal). If the next step is only your playtest notes on the report's words, a lighter model at medium effort is enough.
