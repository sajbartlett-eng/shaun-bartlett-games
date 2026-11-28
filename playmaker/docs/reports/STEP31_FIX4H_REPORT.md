# Step 31, fix 4h: the named answers, faster and exact, then three more kinds. Report

**On branch `step-31`. Not merged. The exam was not run.**

- **With all three kinds, the new answer now equals the exact answer on all 21 R and P boards.** Fix 4g missed on five. Both engines read the same on all 21.
- **The speed work is exact and changes no number.** A turn and the defence setup got faster, but none of the three readings reached its target.
- **The new kinds cost time, kind 3 most. On four cores within 256 MB, with every kind on:**
  - a turn takes 86 s (77 s warm), against about 20;
  - the defence setup takes 6.6 minutes, against about a minute;
  - the offence setup runs past 30 minutes.

  As you asked, nothing was dropped or trimmed to save time.
- **The arrow facing the line stays, listed as a cut** (section 5).

## 1. Changes to the printed game

None.

## 2. Speed first, exact (D-319)

1. **Races read by difference, for the named movements only.**
   - The board's races keep a trace of what they read (fix 4e's).
   - A named movement that changes nothing in it leaves every race as it stands.
   - Otherwise its races are read by difference from the board's race kit.
   - Each accepted movement reads the races once afresh, with a new trace.
2. **A floor under each movement, and the lowest first.**
   - The number only rises with what a race is worth, and a race that's gone is worth nothing. So the number with the movement played and every race on the board gone is a floor under its full reading.
   - A movement whose floor is above the number, or above the best read so far, can't be the answer, so its races aren't read.
   - Movements are read lowest floor first, so the best is found soonest. Order can't change which one is best.
3. **The number before a movement's races go in is read only when it's needed:** when the movement opens a race the board didn't have.

**What each gave.** One reading of each R and P board, one core, before the new kinds:

| | All 21 boards |
|---|---|
| Fix 4g | 22.8 s |
| Races by difference | 25.0 s (no gain: a defender's own arrival touches most of what a race reads, as fix 4e found) |
| Plus the floor | 15.0 s |
| Plus the number read only when needed | 13.7 s |

- **Exact on every count.** The same number and answer on all 21 boards, every way.
- **Every race read by difference equals it read afresh.** The proof re-checks this (section 4).
- **One saving tried and taken out.** I kept the follow-up's map looks across a change of races. It gained nothing: the follow-up is read again mostly because the board changed, not the races.

## 3. The missing answers, one kind at a time

Each kind is in both engines. After each, the gap to the exact answer on R1 to R5 and P1 to P5. The exact answer is fix 4g's recorded run: nothing it reads changed in fix 4h. The proof re-reads every stage live (`docs/runs/step31/fix4h_proof.txt`).

| Stage | What the races name | Boards that miss | Total gap |
|---|---|---|---|
| 0: fix 4g's naming | the line, in front of it, its passing lanes, beside its finish | 5: R5b +1, P1 two off +0.25, P2 two off +1.5, P4 +1.5, P4 two off +1.88 | 6.13 |
| 1: helpers arriving in time | as 0, and a square a defender reaches from which he gets in front in time, or takes over the ball | 3: P2 two off +1.5, P4 +1.5, P4 two off +1.88 | 4.88 |
| 2: the rim | as 1, and the rim and the squares round it when a line stops short | the same 3 | 4.88 |
| 3: the two-step routes | as 2, and every movement that stops a two-step route | **none** | **0** |

1. **Kind 1, helpers arriving in time.** It's two things, both by the race's own rules.
   - **In front in time.** The race counts a helper when he reaches a square in front of the ball (next to it, nearer the rim) within the phases since it began. So a square is named for a defender if, from there, his phases reach one of those in time. This closed **P1 two off**: X3 to J6, the exact number 28.5. The exact answer has X3 to I6, at the same 28.5.
   - **A switch.** From the square, the pairing of who guards whom gives the ball handler to another defender. This closed **R5b**: X3's Sprint to J8 makes him O1's defender, and every race on O1 goes. It also took the first half of **P2 two off**: X1's drop to K2 hands O1 to X5 under the rim.
2. **Kind 2, the rim.** It closed nothing more, as the misses said it wouldn't. No remaining miss was a drive stopping short of the rim; P2 two off's drop was a switch. It's in, and it costs a little time.
3. **Kind 3, the two-step routes.** Each two-step look the number turns on is put to every defender's movement, read as the exact answer reads a look: his contests from where it leaves him, the fake's follow-up with him there and his Move spent. One that lowers the route is named. This closed the last three:
   - **P4:** X2 to D6, 30. It stops O2's next-phase closeout, fake and drive at A5.
   - **P4 two off:** X2 to D7, 29.63.
   - **P2 two off:** after the switch, X2 to D9, 30. It stops O2's closeout, fake and drive at H10.

   The map's own candidates read the fake's follow-up without the movement played, so they never offered these. Fix 4f's guard had flagged that on P4 since fix 4f.

**Where the new answer takes other movements to the same number** (no gap):
- R4 and R4c: X4 to F4 then X2 to C7 on R4; X1 to J8 on R4c. The exact answer has X1 to H8 on both.
- P2: X1 to I2 facing S, not N.
- P1 two off: X3 to J6, not I6.
- P5 control, two off: no movement. The exact answer's X1 to E11 leaves the number the same.

## 4. Times and memory

Four cores, the engine and each worker held to 256 MB of heap, one reading at a time (`docs/runs/step31/fix4h_times.txt`):

| Stage | A turn on E13 | Defence setup (E1) | Offence setup (E15b) |
|---|---|---|---|
| Fix 4g | 35.5 s (29.6 warm) | 461 s | 927 s |
| 0: speed only | 31.5 s (25.6 warm) | 291 s | 885 s |
| 1: plus helpers | 35.0 s (27.8 warm) | 194 s | **over 30 min**, stopped |
| 2: plus the rim | 39.9 s (32.8 warm) | 242 s | not run (stage 1 already over the cap) |
| 3: plus two-step routes | **86.0 s (76.9 warm)** | **396 s** | **over 30 min**, stopped |
| Target | about 20 s | about a minute | about a minute |

- **The time each kind adds:**
  - **Kind 1:** a turn +3.5 s. The defence setup got faster (291 s to 194 s): its better answers let the floor stop sooner. The offence setup more than doubled, past 30 minutes.
  - **Kind 2:** a turn +5 s, the defence setup +48 s.
  - **Kind 3:** a turn +46 s (more than doubled), the defence setup +154 s. One reading of all 21 boards went from 21 s to 61 s.
- **Where kind 3's time goes:** each step puts every defender's every movement, about a thousand, to the two-step routes, then reads those that lower one in full.
- **Memory held:** no worker failed under its cap. The process with its four workers used 0.8 to 1.3 GB in all.
- **The defence setup's decision** is the same at stages 1, 2 and 3, and different from stage 0's. The new answers change the shape it picks.

**Not reached, and the exact savings I'd build next:**
1. **Kind 3's test by difference.** A movement changes a two-step route only through the mover's own contests and the follow-up's closeouts. Reading only what it touches, as fix 1 did for the map, keeps the same answers for less work.
2. **The offence setup's readings.** It reads thousands of boards, and speed alone took it only from 927 s to 885 s. I haven't profiled it yet; that comes first.
3. **Handing a reading's named movements to the workers.** A setup's own readings are already spread across them, but a turn's last reading isn't.

## 5. The cut, watched by the exact answer

**A named Move faces the line** (Shaun's answer to question 2). A Move to a named square faces the ball's square on the line that named it, or the ball handler for a switch; a Quick Step or Sprint keeps its own arrows. Kind 3's movements are named by test, every arrow. On these 21 boards this cut lost nothing: where the exact answer faced another way (R4, R4c, P2), the new one reached the same number. The exact answer will keep watching it.

## 6. The checks

| Check | Result | Time |
|---|---|---|
| The proof (`tools/step_31_fix4h_proof.py`): the speed against reading afresh; each stage's gap to the exact answer; both engines with every kind | section 3. The speed is exact on all 21 boards: 1,639 races read by difference, none different from afresh. With every kind, no gap, and both engines the same on all 21 | 16 min (mostly Python) |
| Engine equality (40 random positions) | 0 mismatches | in lane C |
| Fix 4h's tests: by difference against afresh on R1 and P2; the new kinds in both engines on R5b, P1 two off, P4 and P2 two off | 2 passed | in lane D |
| Fix 4e's, 4f's and 4g's tests | 6 passed, after the change below | lane D (14 min) |
| Fix 2's, 3's, 4's and 4c's tests | 7 passed (fix 4c's alone in 3 min, after the lane hit its limit) | lane C |
| The rules, memory and golden game | 33 passed | lane A (3 min) |

**One test changed, and why.** Fix 4g's take-back test needs a board where the answer tries a movement and takes it back. With every kind named, P2's answer no longer does. It now reads P2 at fix 4g's naming, where it still does: the take-back is the same code, and the number after it still equals the number before.

**Over the 10 minutes, and what I didn't run:**
- The proof took 16 minutes and the lanes about 25, because Python's reading is slower with kind 3.
- **Not run:** the value's guards (`tests/test_exam.py -k "not test_check"`, 17 minutes in fix 4g, with its memory check already past its 10-minute limit then).
- **Not run:** `tests/test_fix1_difference.py` and the P held searches, as in earlier fixes.
- **Not run, as asked:** the exam.

## 7. For Shaun to decide

1. **Fidelity first, at this cost?** The answer now matches the exact one on every board here, but a turn takes about 1.5 minutes and the setups 6.6 and over 30 minutes. I'd build the savings in section 4 next, kind 3's test by difference first.
2. **Kind 2 (the rim)** closed nothing on these boards. It's in, since you asked for every kind; it costs a turn about 5 s.

## 8. Model for the next step

Claude Opus 5.5, effort high. The savings in section 4, then fix 5.
