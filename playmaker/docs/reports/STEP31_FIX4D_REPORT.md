# Step 31, fix 4d: the answer reads every legal movement. Report

**Stopped at the cost, as you asked. On branch `step-31`. Not merged. The exam was not run.**

- **The full reading is built in JavaScript** and changes answers. On R4 it finds the step over that keeps X1's cushion, and the number drops from 34 to 29.
- **It costs 60 to 280 times the time of one reading.** One reading went from about half a second to 31 to 141 seconds. A turn would take hours. So I stopped, and added no shortlist.
- **It ships switched off** (`PV_FULL = false`), so the game and every test read as in fix 4c. It's a switch for measuring, nothing else.
- **R4 is rewritten:** a weak dribbler for O1 (25 in 100 against X1), both with 2 Quick Steps.
- **Not done, because I stopped:** the Python mirror of the full reading, the P1 to P5 proof, the fast tests, and a full-reading turn and setups.

## 1. Changes to the printed game

None.

## 2. What was built

1. **The full reading (JavaScript, behind a switch).** The defence's answer reads every legal movement of every defender, at every square and arrow pair:
   - The two filters are off: it no longer needs a movement to lower a look on the map, or its square to contest one.
   - Each movement is played, the races are read again on the board it leaves, and it's taken back. The best by the whole number is taken, round after round, as before.
   - The bound and the best-first stop are skipped. They ignore the races, so they can't prove a movement won't help.
2. **One shared way to play, re-read and take back a movement** (`applyMove`, `raceAfter`, `takeBack`). The normal answer now uses it too. On R1 to R5 it reads the same as fix 4c in both engines (section 4).
3. **R4 rewritten** (`tests/exam_boards.py`):
   - O1 is Defensive Point Guard C, a weak dribbler. His Dribble against X1 is 25 in 100.
   - X1 stays Defensive Point Guard A, the quickest card.
   - Both have 2 Quick Steps left, so only the Dribble chance differs and neither side has a speed edge.
   - Fix 4c's R4 is kept as R4c.

## 3. The proof, before and after

**R1 to R5.** "Before" is the answer with its filters. "After" is the full reading. (`docs/runs/step31/fix4d_full_reading.txt`)

| Board | Before | After | Time after (one reading) |
|---|---|---|---|
| R1 | 30 | **29.42** | 35 s |
| R2 | 29 | 29 | 31 s |
| R3 | 36 | 36 | 54 s |
| **R4 (new)** | 34 | **29** | 141 s |
| R4c | 38 | **29.23** | 121 s |
| R5a | 36 | 36 | 63 s |
| R5b | 30 | **29** | 133 s |
| R5c | 29 | 29 | 72 s |
| R5 control | 29 | 29 | 61 s |

- **Four of nine answers change**, so the old filters are not exact once races count.
- All nine took 712 s, against about 5 s before.

**R4, the step over, phase by phase** (`docs/runs/step31/fix4d_r4_step.txt`). O1 on I9, X1 on I8 in front of him.

| | Before the answer | After the answer |
|---|---|---|
| The answer | none | X1 from I8 to H8, arrows NE+E. X4 from B4 to C2 |
| Speed this phase | O1 to G4, nobody in front: 34 | to G6 only, 26 |
| Speed next phase | to G4: 34 | **gone**: from H8, X1 gets in front of G4 next phase |
| The Dribble (25 in 100) | 27 | 26.5 |
| **The number** | **34** | **29**, the set defence's best look |

- X1 gives up one square toward the side O1's speed drive goes. That's the cushion: from H8 he's in time for G4 in both phases.
- X4 drops from B4 to C2, so the drive's finish at the rim has help.
- **R4 is now a control on the full reading.** With the filters, it isn't (34).

**P1 to P5: not run.** Each held search reads hundreds of positions. At the full reading's cost, the 20 searches would take days.

## 4. Cost, and the checks

**One reading, the full reading against the normal one:**

| Board | Normal | Full | Movements read |
|---|---|---|---|
| R1 | 0.55 s | 34.5 s | 1,589 |
| R4 | 0.50 s | 134 s | 2,779 |
| R5 control | 0.55 s | 59 s | 1,167 |

**A turn and both setups.** The default path is timed today, one at a time, the engine held to 256 MB. The setups with the full reading are estimated from the ratio above:

| Reading | Normal (default path, timed today) | Full reading |
|---|---|---|
| A turn on E13 | 18.7 s (fix 4c: 16.4 s) | **over 10 minutes**: run, and stopped at the cap. At 60 to 280 times: 20 to 90 minutes |
| Defence setup (E1) | 89 s, the same shape (21) | not run. At 60 to 280 times: **1.5 to 7 hours** |
| Offence setup (E15b) | 193 s, the same value (29.375) | not run. At 60 to 280 times: **3 to 15 hours** |

| Check | Result | Time |
|---|---|---|
| Both engines on R1 to R5 and R4c, the default path | the same on all nine | 30 s |
| R4's step over, before and after | above | 2 s |
| The fast tests, the P proof, the Python mirror | not run: I stopped at the cost | |
| The exam | not run, as asked | |

## 5. Where the answer and the searches still keep a shortlist

With `PV_FULL = false` (the default), all of these are on. With it on, the first four are off.

**The defence's answer inside the number:**
1. **"Lowers a look" filter.** A movement is offered only if it lowers a look on the act list. Cuts: any movement whose worth shows only through a race, such as R4's step over.
2. **"Bears" filter.** A square is read only if some arrow pair there contests a look on the act list. Cuts: squares that only wall a drive route.
3. **The bound.** Movements are read best bound first. The bound reads the map without races. Cuts nothing alone, but it feeds:
4. **The best-first stop.** Reading ends when no bound left can beat the best found. Exact for the map. Not exact once races count, as section 3 shows.

**The stance search (the defence's setup and the held searches):**

5. **STANCE_STEP = 1, STANCE_NEAR = 3.** Each round, a defender's squares are read only within 1 step, and within 3 of his man. Cuts: anything farther.
6. **STANCE_TOP = 5.** Squares are ranked by a quick probe, and only the top 5 per defender are read in full. Cuts: the rest.
7. **SETUP_K, and the 16-candidate list** (`cands.slice(0, 16)`). Only the best few ranked shapes get the full reading. Cuts: the others.

**The offence's setup:**

8. **OFF_SEGS = 3, OFF_FINAL = 2.** Only 3 segments per player are tried, and 2 shapes go to the final reading.
9. **The 12 readings kept** (`out.slice(0, keep || 12)`). Cuts: the 13th best spot on.

**The turn's search:**

10. **The beam.** Only the best `beam` turns are kept each step, and a third of them are expanded. Turns read exactly as kept are added back.
11. **Looks per player.** Movement targets come from each player's best looks only (top looks, and the single best spot for the help).
12. **Screens.** Only the 4 screens nearest a defender are tried.
13. **Two-action and gain lists** (lines 2539, 2643). Only the best `L` and `k` are kept.

**The lasting gap:**

14. **LG_BEAM = 3, LG_WIDE = 3, LG_HEAD = 6.** A beam of 3, 3 options wide, 6 phases ahead.

**Called exact, kept as they are:**
- The races' start-skipping cut (proved in fix 4).
- The fake mix's best-first scan.
- BOUND_LOOKS = 2: it only sets how tight a bound is.
- Ties among a turn's best (`results.slice(0, g)`): every tied turn is read.
- The coverage list's top 64: only used to compare two lists, after the number is read.

## 6. For Shaun to decide

The full reading is correct but far too slow to play. Three ways on, with no shortlist:
1. **Exact savings first.** Prove a bound that includes the races, so the best-first stop is exact again. Read each movement's races only on the routes it touches. Use several cores.
2. **Accept the cost** for the setups only, run once before the game, and keep the filtered answer for turns.
3. **Keep the filters** and record that the answer misses a step back when only a race shows it.

I recommend 1.

## 7. Model for the next step

Claude Opus 5.5, effort high. The exact savings in section 6, then fix 5.
