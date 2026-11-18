# Step 22b: position and arrows, ranked drivers, the screen that blocks the path around it

*The second half of this report, "the defence's two responsibilities", came later the same day. It replaces ranked drivers b to d described in this first half; the screen rule stands.*

1. A defender standing on a screen's T square now loses his diagonal arrow: it stops no drive and cuts no passing lane, and the board draws it dashed with "blocked". His contest is unchanged. Look for the ball handler driving round the screened defender.
2. When two choices leave the same lasting gap, the computer no longer picks by list order. It goes down Shaun's drivers in order: the offence's least likely actions by the rules' chances, then the fewest actions, then doubled cover. This applies in setup, in the turns it plays, and in the map's own answer (b and c swapped on Shaun's call, both sides).
3. Both setups now try every square: the defence moves any defender to any square with any arrow, and the offence tries each attacker on every empty square, inside its thinking time.
4. Tap a defender with Coverage on to read what his position and arrows take away and what he allows. The two defenders who matter most are also in the line under the board.
5. Look for: the screen paying off, and the defence's spots. The swap didn't fix X1: on today's board he still leaves O1 for E7. The board below shows why, and what would fix it.

## The board (item 6: checked, not tuned)

Shaun's board of today: the table's offence (O1 I11 with the ball, O2 C9, O3 O9, O4 A3, O5 Q3) against the defence step 22 set (X1 J10, X2 D8, X3 O8, X4 I6, X5 P2). Its lasting gap is 18. Six different looks are each worth 18, led by open threes.

**What the map says each defender does there:**
- **X1 (J10):** his position takes away O2's floater on F6 and O3's three on I10. His arrows take away nothing worth half a point. He allows O2's three on A4 (18).
- **X2 (D8):** his position takes away O2's long two on D8.
- **X3 (O8):** his position takes away O3's three on O8 and O5's mid-range on L2. His arrows cut the pass to O3 for a three on P7.
- **X4 (I6):** his position takes away O1's layup on I4 and O2's floater on I6 (worth 18 more without him). His arrows cut the passes to O3 and O5 for layups on J4 and K3.
- **X5 (P2):** his position takes away O5's long two on P2 and O3's long two on O2.

**Where the computer now puts each player, and which driver decided it:**
- **Defence (after the swap of b and c):** it still moves one player. X1 goes from J10 to E7, facing N, and the gap stays 18. Driver **(a)** is level at 18. Driver **(b)** is level too: every one of the six top looks is reached with a chance of 1, from J10 and from E7 alike. So **(c) efficiency** decided it: on J10 the defence needs one move in the phase to hold 18; on E7 it needs none. Nobody else moves. Before the swap the same move was decided by efficiency too.
- **Why (b) can't see O1's free sprint:** by the rules' own chances O1 reaches the same 15 paint squares with certainty whether X1 is on J10 or E7. On J10, X1's arrows point NW and N, at O1 and away from the rim, so they wall nothing on the drive. And O1's paint looks aren't among the top looks, because X4 on I6 covers them (worth 8 to 16 to O1 after X4's cover; the top looks are 18). So X1 standing on O1 changes no chance the map reads. What would change it: (1) the setup trying X1 on J10 facing the drive, so his arrows wall it and O1's paint squares need a Dribble; that only counts if the drive is a top look, and with X4 in the lane it isn't; (2) the map seeing what Shaun named, the collapse and kick-out after O1's sprint draws X4. That needs the map to read past the defence's answer, which it can't yet.
- **Offence:** it keeps the table placement (18). The every-square sweep found nothing better in its 20 seconds, so no driver changed a square.
- **The first turns from tip-off** (All-Star both sides, unchanged by the swap): O2 moves to A7, O4 moves to C3, X2 moves to F7 facing N, X4 Quick Steps to I7. The search's own value chose these. The drivers only reorder turns that read exactly the same.

**Beside Shaun's read:**
- **X1 walling the middle, arrows on the drive.** The map differs. It reads O1's best looks as worth 18 wherever X1 stands, because O1 can reach looks of the same worth around him this phase. A wall in front of O1 now buys nothing on the lasting gap, and on E7 X1 holds O2's side with no move needed. The cause is the reading itself: the lasting gap counts the defence's answer during the phase, so a wall the answer could rebuild is worth nothing. It doesn't price the offence's first actions, which come before the defence answers. Step 22 found the same thing, and that's where I'd look next.
- **X4 lower.** The map keeps X4 on I6. From there he takes away O1's layup on I4 and O2's floater on I6. No lower square left a smaller gap or needed fewer actions.
- **X3's arrows on the real passing lane.** The map keeps X3 on O8 facing N. The pass to O3 on O9 is already contested by X3's body (O3's three on O8 is what his position takes away). Turning onto the I11 to O9 lane takes nothing more off the gap.
- **X5 containing O5 on his own.** The map keeps X5 on P2. O5 going middle is picked up by X4 (X4's arrows cut the pass to O5 for the layup on K3). One attacker pulls two defenders onto him either way, so driver (d) never got a vote: it only decides when (a) to (c) are level.

## Screen cases for Shaun (D-217)

Each is read the way closest to "the screen stops the path around it, for his body and his arrows alike":

1. **Which arrows are blocked.** From the T square the rules already stop every diagonal step, all four, not only the two around the screener. So the blocked arrow is whichever of his arrows points diagonally. Under the zone his two arrows are always one straight and one diagonal, so he always keeps exactly the straight one.
2. **The drive wall.** A zone stops a drive by one arrow catching the ball handler and the other barring his line (D-170). With one arrow blocked, nothing catches him and bars the other, so a screened defender walls no drive at all. His straight arrow doesn't wall on its own. That's what makes the ball handler free to go round him (on Shaun's screen board, O1 gains K10, K11, L11 and the sprints right).
3. **Steal and "closely guarded".** Both read the arrow on the ball handler next to him, which is on the man, not around the screener. Both are left as they were.
4. **Any defender on the T.** The block is for whoever stands on the T square and hasn't beaten that screen with a Challenge, not only the defender it was set on, as the body rule already is.

## Tests

- **New:** the screen rule's cases (7) and the drivers, per-defender words and setup sweep (7). All pass.
- **The two engines agree:** every legal action on the screened board, and the map on 40 of 40 random positions.
- **Fast tests:** 148 passed, 1 failed, and 4 already marked as expected to fail (unchanged). After the swap I ran the rules text, golden and regression, both engine-equality tests, and the tests for every file changed.
- **Fixed along the way:** a contradiction in the report the new play exposed. A phase where the defence's own answer let the gap rise was called "weaker", and also "No turn raised the lasting gap". It now says only the first, and names the answer that let it rise. One step 22 test was also updated for the setup's extra return value.
- **Still failing, as on main:** `test_setup_18o.py::test_the_search_places_both_sides_legally_inside_its_time` takes about 5.7 seconds against a 1.6-second limit. Main fails it the same way.

---

# Step 22b, continued: the defence's two responsibilities (Shaun's model)

1. Every defender now plays for two things, both in points from the cards and the rules: his assigned man's best look as the defence stands (before it answers), and the open squares nobody influences (the average shooter's shot there). They go into one list, and the defence places all five to leave the lowest highest item, then the next.
2. A wall in front of the ball handler now counts: a path he can only take by winning a Dribble is priced at the Dribble's chance. Distance now counts too: a contest reached by a Quick Step or Sprint is off balance, by the rules, so a defender six squares away no longer covers a shot as well as one beside the shooter.
3. Setup places all five from nothing, over every square and arrow, and the result doesn't depend on the order the defenders are listed in. In play the search reads the same list first, so the defence holds the shape its setup chose.
4. Each defender has one assigned man from setup. He keeps him until a switch leaves strictly less uncovered. The coverage view says what each is doing: on his man, sagging to cover squares, beaten and chasing, or a switch.
5. Look for: the Sharpshooter's defender staying attached, a rim protector under the basket, corner shooters covered, and the shape holding when nothing changes. Two things will still look wrong to you, and the checks below say why: nobody guards the ball handler at the top, and a beaten X1 doesn't chase when the help has his man.

## The sense checks (Shaun's board of today; checked, not tuned)

| | Check | Result |
|---|---|---|
| 1 | The ball handler's defender stays with him and walls his drive | **Fails** |
| 2 | A poor shooter's defender sags towards the green zone | Passes |
| 3 | The Sharpshooter's defender stays attached | Passes |
| 4 | No two defenders fill the same gap while another is empty | Passes |
| 5 | Listing the defenders in a different order gives the same settlement | Passes |
| 6 | Over a few turns with nothing changing, nobody switches back and forth | Passes |
| 7 | A switch that costs more than it covers is not taken | Passes, thinly |
| 8 | X1 beaten by O1's drive: he chases, or picks up what the helper left | **Fails** |

**1. Fails.** The settlement gives O1 to X5, who stands under the basket on J3, eight squares from him. O1 is the Pass-First Point Guard: his three is worth 21 open, his layup 34. The reading says his danger is the drive, and a defender at the rim takes more off it (34 down to 21) than a defender on him at the top, who can be gone around. I tried every defender on every square next to O1 with every arrow, 440 placements read in full: none leaves less on the list than the settlement. Why this differs from basketball: the reading prices what each attacker can get. It doesn't price what an on-ball defender can take away, the Steal and the closely guarded count. That's the missing piece if you want pressure on the ball.

**2. Passes.** O1 and O5 are the poor shooters (three 7). O1's defender X5 sits at the rim and covers the squares around H2 (worth 29 with nobody there). O5's defender X3 sags off him too, though to the squares around Q3, not the lane.

**3. Passes.** O2 is the Sharpshooter (three 11, worth 33 open). X1 stays three squares from him on F7, one Move from a set contest, which takes his best look from 33 to 18.

**4. Passes.** Take any one defender off the court and the list gets worse, so nobody is spare. The squares each holds are different: X1 around B8, X3 around Q3, X4 around M9, X5 around H2.

**5. Passes.** I relisted the five defenders in two other orders. Each card ended on the same square with the same arrow.

**6. Passes.** Three defence turns in a row with the offence doing nothing: a Pause; then X2 a step from A2 to B2 and X4 turning on N7; then X3 turning on Q2. No assignment changed and nobody went back to a square he had left.

**7. Passes, thinly.** After O1 sprints to I7 the defence answers with X1 Quick Step to E6. No turn in its search left less on the list while costing more, so there was no costly switch to refuse on this board. The mechanism is in place (the search plays the real moves, tokens, rushed rolls and Sprint arrows before the list is read; a switch needs strictly less; level turns keep everyone on his man), but this board didn't test it hard.

**8. Fails.** On step 21's board (O1 in the key on I4 with the ball, X1 behind him on I8, X4 and X5 beside him on H3 and J3), the defence moved X2 and X3 and left X1 where he was. No one defender takes O1 on his own (the reading keeps "X1 on O1"), so by your words X1 should chase. He doesn't, because X4 and X5 together already contest every look O1 has there, so X1 arriving takes nothing more off the list, and the two movements the turn had bought more elsewhere. The reading sees "already covered by the help" and your model says "still his man until someone takes him". The fix I'd suggest is to read help by two defenders as a takeover, so X1 is handed what the helpers left.

## The board: where all five go and why, beside Shaun's read

Offence: O1 I11 (ball), O2 C9, O3 O9, O4 A3, O5 Q3. Shaun's board as it stood (X1 J10, X2 D8, X3 O8, X4 I6, X5 P2) leaves a largest item of 30 on the list. The settlement leaves 18.

| Defender | Goes to | Why, by the reading | Shaun's read |
|---|---|---|---|
| X1 | F7, facing N | On O2, the Sharpshooter: 33 open, 18 with X1 a Move away. Also covers the squares around B8. | Walling the middle on O1. Differs: see check 1. |
| X2 | A2, facing NE | On O4 in the corner (A3). Mostly cuts the pass to him. | Not named. |
| X3 | Q2, facing N | Sags off O5 (his best look is worth 21) to cover the squares around Q3. | X3's arrows on the real passing lane. Differs: X3 is on the other side here; X4 took O3. |
| X4 | N7, facing N | On O3 (O9): two squares off, and covers the squares around M9. | X4 lower. Differs: the rim went to X5, so X4 went out to the wing shooter. |
| X5 | J3, facing N | The rim. Takes O1's layup from 34 to 21 and covers the squares around H2 (29 with nobody there). | Containing O5 on his own. Differs: O5 is a poor shooter, so by the values X5 leaves him to X3 and takes the lane. |

Each step of the settlement was decided by the list, except two early placements that were level. The setup took 3.9 seconds.

## Choices your words didn't settle (each marked in DECISIONS.md)

1. **What leads the search (D-219).** Your prompt said the list replaces drivers b to d, which leaves the lasting gap first. I built both and ran checks 6 to 8 each way. With the lasting gap leading, the defence drifted off its own setup and swapped men twice in three turns with nothing changing (check 6 fails). With the list leading it held. So the list leads. One setting puts the lasting gap back (`eval.map_lead: "gap"`). This is the biggest change in the step and it has had no play-outs, so your playtest is the gate.
2. **Off balance in the map (D-222).** Without it every placement read the same, because distance cost nothing, and the settlement packed all five into the paint. It applies an existing rule (D-185); no rule or card changed. It also moves the lasting gap's numbers (your board: 18 before, 24 now).
3. **"Zone walls" in a square's gap.** I count a defender's influence on a square as the contest he can bring there by position and arrow. Walls count in the other half, the attacker's reach. A wall takes nothing off a shot once the shooter is standing there.
4. **A square's gap uses the one defender who would contest it best against the average shooter.** One defender contests a shot, so I didn't stack two.
5. **An attacker's look "this turn".** I used the map's existing reach: the rest of this phase, the first turn of the next, and the defence's reaction contest. It's wider than one turn.
6. **A lost Dribble costs nothing in the reading** (he's locked, nothing is banked against him). A lost pass is still -5.
7. **Assignments are read again only after the defence acts,** so an offence move never calls a switch by itself.
8. **The step-by-step replay in Watch doesn't show the new lines yet.** The live coverage view and tap-a-defender do.

## Tests

- **The two engines agree** on the lasting gap, the list, the answer and the settlement's moves on 24 of 24 random positions (40 of 40 before the last change).
- **New tests for items 1 to 4:** 10, all pass.
- **Fast tests:** 156 passed, 1 failed, and 4 already marked as expected to fail (unchanged). That covers the rules text, golden and regression, both engine-equality tests (the search included), and the tests for every file changed.
- **Re-recorded for the new rulings, each with a note in the test:** two tests that pinned the search's reading to the lasting gap (now the list, D-219; both settings are tested); three coverage checks and one map number that moved because off balance is now counted (D-222): the top look on the clear-lane board is O3's layup at 36, above the point guard's open 34; an arrow across the ball handler's way now leaves him a contested layup, where it left a rushed shot; a body on the helper's way now leaves as much as before (30 and 30), where it left one more.
- **Retired:** the tests of ranked drivers b to d, which the list replaced.
- **Still failing, as on main:** the setup timing test (`test_setup_18o.py::test_the_search_places_both_sides_legally_inside_its_time`). Speed is waived (D-200).
- **Speed:** the defence's setup takes about 4 seconds; a full All-Star possession in Watch took 164 seconds, almost all of it the search's own 2.5 seconds a decision.
