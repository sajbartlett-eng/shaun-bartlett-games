# Step 22b: position and arrows, ranked drivers, the screen that blocks the path around it

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
