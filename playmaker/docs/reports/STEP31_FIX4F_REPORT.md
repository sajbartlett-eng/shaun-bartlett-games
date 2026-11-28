# Step 31, fix 4f: the follow-up as it stood, and several cores. Report

**On branch `step-31`. Not merged. The exam was not run.**

- **Shaun's ruling is in both engines.** A movement can't change what happened before it. In the answer in play, the full reading and fix 4e's answer, a look whose shot or fake goes up before a defender's movement now reads its fake's follow-up on the board as it stood then.
- **Fix 4e's answer equals the corrected full reading on R1 to R5:** every board, number, movement and race.
- **Several cores are built,** for the turn search and for both setups, in Node and in the app. They give the decision one core gives.
- **The answer in play, with four cores:**
  - a turn in 12.7 s;
  - the defence setup in 49 s;
  - the offence setup in 114 s.

  That's within your playable targets, except the offence setup, at about two minutes.
- **Fix 4e's answer is still not playable.** A turn went past 10 minutes on four cores. So it stays off, and I didn't build its Python copy.

## 1. Changes to the printed game

None.

## 2. What was built

1. **The ruling (D-316), both engines.**
   - The answer keeps the board as it stood after each of its movements.
   - A look whose limit is k movements reads its fake's follow-up on the board after k movements, as its contests already do.
   - Fix 4e's special case for such looks is gone: they can no longer change, so no movement is put to them.
2. **Several cores (D-317).**
   - **What's handed out.** Three searches' independent readings go to workers, each as one batch:
     - the turn search's candidate turns, first and second actions;
     - the stance search's candidate stances, each defender's batch, and its swaps;
     - the offence setup's placements and each attacker's tries.
   - **Each worker** is the same engine, given the request and every setting of the engine that hands the batch out.
   - **Batches go in contiguous blocks.** Neighbouring readings share most of their work, so each worker keeps its neighbours together. Round-robin was slower.
   - **The results go back in the batch's own order,** so the search compares the same readings in the same order.
   - **In Node:** worker threads (`tools/engine_pool.js`), each held to 256 MB. The runner uses them with `PM_CORES=4`.
   - **In the app:** Web Workers inside the engine's own worker, waiting on shared memory. The browser allows that only on a cross-origin isolated page. The local server now sends the two headers; a host that doesn't send them runs the app on one core.

## 3. The proof

**R1 to R5: fix 4e's answer against the corrected full reading, both read live** (`docs/runs/step31/fix4f_proof.txt`):

| Board | Full reading | Fix 4e's answer | The movements (both) | Same |
|---|---|---|---|---|
| R1 | 29.42 | 29.42 | X3 to J8 | yes |
| R2 | 29 | 29 | none | yes |
| R3 | 36 | 36 | none | yes |
| R4 | 29 | 29 | X1 to H8, X4 to C2 | yes |
| **R4c** | **29.67** (was 29.23) | **29.67** | X1 to H8 | yes |
| R5a | 36 | 36 | none | yes |
| R5b | 29 | 29 | X3 to J8 | yes |
| R5c | 29 | 29 | none | yes |
| R5 control | 29 | 29 | none | yes |

- The races match too, every one.
- **R4c changed under the ruling.** X4's drop to A2, and X3's step after it, paid only through the follow-up of a shot that goes up before them. Read as it stood then, they don't lower the number.
- **The answer in play is unchanged on all nine boards and on P1 to P5** (both engines read the same).

**P1 to P5, each board as written:**

| Board | Before (in play) | After (fix 4e's answer) | After: the answer |
|---|---|---|---|
| P1 | 30 | 30 | none |
| P1 two off | 28.75 | 28.5 | X3 to I6 |
| **P2** | **34.75** | **31.84** | **X1 to I2** |
| P2 two off | 33 | 30 | X1 to K2, X2 to D9 |
| P3 | 27 | 27 | X2 to E8 |
| P3 two off | 27 | 27 | X2 to E8 |
| P4 | 31.5 | 30 | X2 to D6 |
| P4 two off | 31.5 | 29.63 | X2 to D7 |
| P5 | 38 | 38 | none |
| P5 two off | 38 | 38 | none |
| P5 control | 36 | 36 | none |
| P5 control, two off | 36 | 36 | X1 to E11 (the number the same) |

**P2's answer, and why.**
- **The board.** O1 has the ball on I6, in mid-range. X1 is pressed on I5.
- **Before: 34.75.** The number in play is held by O1's created Dribble. He beats X1 at 50 in 100 from H4, then drives to the rim. That race is worth 34.75, his best look.
- **After: X1 drops from I5 to I2, under the rim, facing north.** From there no beaten man is left between O1 and the rim:
  - the Dribble's race falls to 30;
  - O1's own looks fall with it (his drive's look at I6 drops from 34.75 to 30).
- **The number becomes O2's three from H10: 31.84.**
- In basketball words: against a guard who beats him off the dribble, X1 gives up the mid-range and protects the rim. That's the trade the number takes.
- The old filters never offered that drop: it lowers no look on the map, only the race.

## 4. Times and memory

One at a time. The engine and each worker were held to 256 MB, on this container's 4 cores (`docs/runs/step31/fix4f_times.txt`):

| Reading | One core | Four cores | Target |
|---|---|---|---|
| A turn on E13 | 15.4 s | **12.7 s** (7.4 s once the workers have read a turn) | about 20 s: **met** |
| Defence setup (E1) | 79 s | **49 s** | about a minute: **met** |
| Offence setup (E15b) | 169 s | **114 s** | about a minute: **not met** (75 s with memory not held) |
| Fix 4e's answer: one reading | 24 to 120 s | | |
| Fix 4e's answer: a turn on E13 | ran out of memory (4e) | **over 10 minutes**, stopped at the cap | |

- **The same decision on every run.** Each run's answer was compared one core against four: the same signature on the turn, on E1 (the same shape, at 21) and on E15b (the same placement, at 29.375).
- **Memory:**
  - the main engine used 76 to 187 MB;
  - each worker ran under a 256 MB cap and none failed;
  - the cap costs the setups time (E15b 75 s uncapped, 114 s capped), because the workers keep less of their work.
- **The first turn is the slowest.** A worker starts cold. Over a game its memory warms, and a turn falls to about 7 s.
- **A normal laptop.** These times are on 4 cores here. A laptop with 8 cores would hand out more, but the speed-up isn't even: four cores gave 1.2 to 1.8 times on a turn.

**The app's pool in a browser** (Chromium, the adapter's own pool code, P5's stance search):

| Run | Result |
|---|---|
| One core | 180 s |
| Four cores | **81 s** (the page cross-origin isolated) |
| The decision | the same on both, and the same as Node's (the same signature: shape E8, I8, M5, D4, I4, at 25.9) |

## 5. The checks

| Check | Result | Time |
|---|---|---|
| Fix 4e's answer against the corrected full reading (R1 to R5), P1 to P5 before and after | section 3 | 7 min 53 s, four at a time |
| Both engines, R1 to R5 and P1 to P5, with the ruling | the same on all 21 | about 1 min |
| Engine equality (40 random positions) | 0 mismatches | in lane C |
| Fix 4e's and 4f's tests: the answer against the full reading on R2; every race by difference against afresh; both engines with the ruling; four cores against one on E13's turn | 4 passed | 181 s (lane D) |
| Fix 2's, 3's, 4's and 4c's tests | 7 passed | 170 s (lane C) |
| The rules, memory and golden game | 33 passed | 141 s (lane A) |
| The value's guards | 13 passed, 1 failed (G5, as in 4b to 4e) | 221 s (lane B) |

- The tests ran four lanes side by side in under 4 minutes. With the proof, tests and proofs took about 12 minutes, two over the 10.

- **Not run, because it can't fit:** `tests/test_fix1_difference.py` and the P held searches.
- **Not run, as asked:** the exam.

## 6. What's not built, and why

- **Fix 4e's answer in play.** It's exact, but a turn takes over 10 minutes on four cores. Every movement still needs its races read again, and the race reads three phases ahead.
- **Its Python copy.** You asked for it only with the answer switched on.
- **The offence setup in about a minute** with memory held to 256 MB (114 s). Uncapped it's 75 s.
- **The app's cores on a host that sends no isolation headers.** A static host has to send `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Embedder-Policy: credentialless`. The local server does.

## 7. For Shaun to decide

1. **The answer in play now meets your playable targets on a turn and the defence setup.** Keep fix 4d's answer in play until the exact one is fast enough?
2. **The exact answer's next saving.** Most of its cost is re-reading races for movements that differ only in their arrows. The next exact saving I'd build is to read a race once per square, and reuse it for each arrow whose walls and passes read the same. On R1 in fix 4e, 243 changed races came from 45 squares.

## 8. Model for the next step

Claude Opus 5.5, effort high. Your answers to section 7, then fix 5.
