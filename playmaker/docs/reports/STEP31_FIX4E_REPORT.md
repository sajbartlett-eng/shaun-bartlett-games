# Step 31, fix 4e: each side answers what it can see. Report

**Stopped at the cost, as you asked. On branch `step-31`. Not merged. The exam was not run.**

- **The answer that answers every look and race is built, in JavaScript, and it's exact.** On R1 to R5 it gives the full reading's number, movements and races on all nine boards, R4's step over included.
- **It isn't playable.** It costs about what the full reading costs: 31 to 154 seconds a reading, against about half a second for the answer in play. A turn ran out of a phone's memory, and with 4 GB went past 10 minutes. Section 4 says why, in numbers.
- **So it's a switch (`_pvAnswers`), off in play.** The answer in play is fix 4d's, unchanged. The full reading (`_pvFull`) stays only as the test that holds the new answer to it.
- **No shortlist was added.** Shortlists 5 to 14 are untouched, for fix 6.
- **The design is version 6 on the branch**, with its new section and table row.
- **Not done, because I stopped:** the Python copy of the new answer, the bound that would make the early stop exact again, and several cores.

## 1. Changes to the printed game

None.

## 2. What was built (JavaScript, D-315)

1. **Every legal movement is put to every look and race the number turns on**, and to the pass a lost Dribble falls back on.
   - One that lowers none of them leaves the number where it is or higher, so it can't be the answer. Leaving it out is exact.
   - One that lowers any of them is read in full, exactly as the full reading reads it, and the best is taken in the full reading's own order. So ties fall the same way.
2. **Each look is read as the full reading reads it with the movement played:**
   - the defender's contests from his new square;
   - the fake's follow-up with him there and his Move spent;
   - and that follow-up even on a look whose shot goes up before the movement. The full reading does it this way, and it's what R4 and R4c needed (section 4).
3. **Each race is read again only on what the movement changes.**
   - **What a race reads is written down:**
     - who guards whom;
     - the squares the ball handler's movement asked about;
     - each defender's phases where they were read;
     - the walls and the passes it checked.
   - **A movement that changes none of these** leaves every race exactly as it is.
   - **Otherwise the race is read by difference.** A race state keeps its worth when its square reads the same and every state it leads to reads as it did. "Reads the same" means each helper's arrival there, as that state reads it; the chaser's; the passes from it; the ball handler's movement from it; and the walls, in the phase of the advantage.
4. **The two checks that hold it:**
   - against the full reading;
   - each race read by difference against the same race read afresh. That second check found two faults in my own work, both now fixed: two kinds of race that share the same phases, and a look read through the fake's follow-up.

## 3. The proof

**R1 to R5, against the full reading as recorded in fix 4d.** That's `docs/runs/step31/fix4d_full_reading.json`, now kept beside the text. Nothing the full reading reads has changed since: the answer as played gives the same numbers in both engines on all nine boards. The new answer's run is `docs/runs/step31/fix4e_proof.txt`.

| Board | Full reading | Fix 4e | The answer's movements (both) | Same |
|---|---|---|---|---|
| R1 | 29.42 | 29.42 | X3 to J8 | yes |
| R2 | 29 | 29 | none | yes |
| R3 | 36 | 36 | none | yes |
| **R4** | **29** | **29** | **X1 to H8, X4 to C2** | yes |
| R4c | 29.23 | 29.23 | X1 to H8, X4 to A2, X3 to K8 | yes |
| R5a | 36 | 36 | none | yes |
| R5b | 29 | 29 | X3 to J8 | yes |
| R5c | 29 | 29 | none | yes |
| R5 control | 29 | 29 | none | yes |

The races match too, every one, on every board. R4's step over, phase by phase, is in fix 4d's report and reads the same here.

**P1 to P5, each board as written: the answer in play (before) and fix 4e (after).** The held searches couldn't fit: each reads hundreds of positions, and at this cost that's days.

| Board | Before | After | After: the answer |
|---|---|---|---|
| P1 | 30 | 30 | none |
| P1 two off | 28.75 | **28.5** | X3 to I6 |
| P2 | 34.75 | **31.84** | X1 to I2 |
| P2 two off | 33 | **30** | X1 to K2, X2 to D9 |
| P3 | 27 | 27 | X2 to E8 |
| P3 two off | 27 | 27 | X2 to E8 |
| P4 | 31.5 | **30** | X2 to D6 (was B7) |
| P4 two off | 31.5 | **29.63** | X2 to D7 (was B7) |
| P5 | 38 | 38 | none |
| P5 two off | 38 | 38 | none |
| P5 control | 36 | 36 | none |
| P5 control, two off | 36 | 36 | X1 to E11 (the number the same) |

- The new answer finds lower numbers on five boards, with movements the old filters never put forward.
- **P2:** X1 drops to I2, under the rim. Pressed and two off both come down by about 3.

## 4. Why it isn't faster, in numbers

**R4c, over the answer's three steps:**

| | Count |
|---|---|
| Legal movements | 3,191 |
| Movements that lower a look or race, read in full | 814 |
| Movements whose races had to be read again | 3,191 (all) |

1. **Every race is touched by nearly every movement.** The race reads three phases ahead, so a defender's own arrival changes at most of its squares when he moves a step.
   - On R1, of the 364,000 checks of a race square that read differently, 330,000 were the moved defender's own arrival.
   - That's a real input to the race, not a leak. Read by difference, a race still re-reads most of its states.
2. **The fake's follow-up makes most movements count.** The full reading reads a fake's follow-up on the board the answer leaves. It does that even for a look whose shot goes up before the movement, a shot whose contests are already fixed.
   - So almost any movement can lower such a look a little, and must be read in full.
   - On R4c that's 814 of 3,191. On R1, before I added this, it was 7 of 1,565. That gave the wrong answer on R4 and R4c, so it's in.

## 5. Cost, and the checks

One reading at a time, the engine held to 256 MB:

| Reading | The answer in play (fix 4d's) | Fix 4e |
|---|---|---|
| One R board | about 0.5 s | 31 to 154 s (four at a time) |
| A turn on E13 | 16.7 s (fix 4d: 18.7 s) | **ran out of memory** at 256 MB. With 4 GB: over 10 minutes, stopped at the cap |
| Defence setup (E1) | 89 s, the same shape (21) | not run: hours |
| Offence setup (E15b) | 194 s, the same value (29.375) | not run: hours |

| Check | Result | Time |
|---|---|---|
| Fix 4e against the full reading on R1 to R5 (9 boards), and P1 to P5 before and after (12) | the same on all nine; section 3 | 6 min 47 s, four at a time |
| The answer in play, both engines, R1 to R5 | the same on all nine, every number as fix 4d | 30 s |
| Engine equality (40 random positions) | 0 mismatches | in lane C |
| Fix 4e's tests (`tests/test_fix4e_answers.py`): R2 against the full reading live; every race by difference against afresh | 2 passed | 156 s (lane D) |
| Fix 2's, 3's, 4's and 4c's tests | 7 passed | 185 s (lane C) |
| The rules, memory and golden game | 33 passed | 158 s (lane A) |
| The value's guards | 13 passed, 1 failed (G5, as in 4b and 4c) | 239 s (lane B) |

- **Memory, too.** The new answer keeps every race state of the board as it stands, and what each leads to, so each movement can be read by difference. A turn holds many such boards, more than a phone's 256 MB.
- The tests ran four lanes side by side in 4 minutes. With the proof, tests and proofs took about 11 minutes, one over the 10. The proof alone was 7.
- **Not run, because it can't fit:** `tests/test_fix1_difference.py` and the P held searches. **Not run, as asked:** the exam.

## 6. Where the answer and the searches still keep a shortlist

With `_pvAnswers` on, items 1 to 4 from fix 4d's list are gone:

1. The "lowers a look" filter: replaced by the exact test above.
2. The "bears" filter: gone.
3. The bound: gone.
4. The best-first stop: gone.

Items 5 to 14 are untouched, for fix 6:

5. STANCE_STEP and STANCE_NEAR.
6. STANCE_TOP.
7. SETUP_K and the 16-candidate list.
8. OFF_SEGS and OFF_FINAL.
9. The 12 readings kept.
10. The turn search's beam.
11. Looks per player.
12. Screens.
13. The two-action and gain lists.
14. The lasting gap's beam.

With the switch off, play is as fix 4d left it: all 14 are on.

## 7. Not built

- **The bound that includes the races, so the best-first stop is exact again.** I found no lower bound on a race that is cheap and tight. A defender's body and arrival reach most of the tree, so any bound that holds for every movement drops too low to stop on.
- **Several cores.** The readings that don't depend on each other are the turn search's, not one answer's. Splitting them needs the search to hand positions to workers, in the app and in Node. Not built.
- **The Python copy of the new answer.** I stopped at the cost. Both engines still read the same with the switch off.

## 8. For Shaun to decide

1. **The fake's follow-up on a shot already taken.** Inside the number, a look whose shot goes up before a defender's movement keeps its contests, but its fake's follow-up still reads the board after the movement. That's what makes most movements count (section 4).
   - Should the follow-up read the board as it stands when that shot goes up, as its contests do?
   - Then fewer movements need reading in full. On R1, 7 of 1,565 rather than most. Some numbers would change, R4c's among them.
2. **Next:**
   - (a) rule on 1;
   - (b) build several cores, by handing the turn search's positions to workers;
   - (c) accept the cost for the setups only.

   I recommend (a) first, then (b).

## 9. Model for the next step

Claude Opus 5.5, effort high. Your ruling on section 8, then fix 5.
