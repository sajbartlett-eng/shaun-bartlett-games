# Step 22: fix it, merge it, hand it to Shaun to test

1. The computer's defence now sets up from the map: it starts from the hug and moves any defender to any empty square with any arrow, keeping each change that lowers the lasting gap. On the table board it drops X4 into the key (I6), and the gap falls from 20 to 18.
2. The computer's offence setup is now judged against that defence, not a quick man-to-man, and setup gets eight times the level's thinking time (All-Star: about 20 seconds).
3. The map now reads the offence's whole first turn of the next phase (move, the defence's answer, then the next move or catch), and it counts the three-second -5, so the offence should stop parking in the key.
4. The offence's search always tries the moves and passes that make the map's best looks, so it no longer picks a move its own map reads as worse because the better one was never on its list.
5. Look for: defenders starting in the paint at tip-off, overload lines ending at a label ("O1's layup") instead of a blank ring, fewer three-second turnovers, and whether the defence's setup actually holds up in play (see "Still wrong" below).

## What changed (D-210 to D-213)

- **D-210, the horizon.** A receiver's start squares now include the squares he reaches with two actions of the next phase, read as places to set up a look.
- **D-211, three seconds.** An attacker in the key at the last phase end who can't get out this phase costs 5 in the map and the search.
- **D-212, the offence tries the map's looks.** For each of the map's top three looks and each overload look, the ball handler's move, the pass, or the receiver's move that starts it is always a candidate. This is the cause of item 4: the defence was judged against offence replies that left out the moves that make the map's best looks.
- **D-213, the defence's setup.** As line 1. When two placements leave the same gap, the one that leaves less behind it wins.
- **Overload labels.** Each dashed line now ends at a label naming the look, e.g. "O3's three".
- The All-Star variety margin (2 points) still lets it choose a turn up to 2 points below its best, by design (D-208).

## Forced lines, 16 play-outs each

**The setup board** (the app's table offence, I11 C9 O9 A3 Q3, O1 with the ball, played from tip-off, All-Star against All-Star, the map on). Shaun's 18 Nov screenshots weren't in the upload, so the table preset stands in for his setup board.

| Defence | Squares | Lasting gap at tip-off | Play-outs (offence's value) |
|---|---|---|---|
| The hug | J10 D8 O8 B4 P2 | 20 | 24 (all 16 a shot) |
| The packed paint | I10 D8 O8 H4 J4 | 18 | 27 (all 16 a shot) |
| The computer's own setup | J10 D8 O8 I6 P2 | 18 | 33 (all 16 a shot) |

All 16 play-outs of each line ran the same way, so each row is one line of play, not sixteen.

- Hug: the offence works it round, O2 takes a shot at C8 worth 24.
- Packed paint: one pass to O4 in the corner (A3), open three, 27.
- Computer's setup: X4 leaves the corner for I6, the offence moves it round and O2 shoots at C9 for 33.

**B1:** stopped (Shaun, 18 Nov: playtest is the gate).

**S3:** stopped (Shaun, 18 Nov: playtest is the gate).

## Still wrong

- **The defence's setup reads better than it plays.** Both setups that pack the paint read 18 against the hug's 20, but in play they gave up 27 and 33 against the hug's 24. Taking a defender off the corner shooter to pack the key leaves the corner three or the swing pass open, and the map at setup doesn't price that well enough. This is the thing to watch in the playtest. If it keeps happening, the next fix is to judge each setup by the shot the offence can take in its first turn before the defence answers, alongside the lasting gap.
- **One timing test fails, on main as well:** `test_setup_18o.py::test_the_search_places_both_sides_legally_inside_its_time` takes about 5 seconds against a 1.6-second limit. Main fails it the same way (5.4 seconds), so this step didn't cause it.

## Tests

- Engine equality on the map: 40 of 40 positions equal.
- Passed: test_rules_current, the golden and regression tests, test_step3n (both engine-equality tests), test_map_logic_21, test_heat_map_20, test_coverage_18s, test_strength_18s, test_setup_3k, the new test_step22 (4 tests), and the rest of test_setup_18o.
- Failed: the one timing test above.
