# Step 17D report: labels from strong play, and the calibrated reading

## The pilot's yes or no

**No signal at this size.** On 640 possessions played by today's computer, the learned weights predict what a
possession goes on to earn no better than the phase average alone (`fit_strong.json`).

| Held-out error, points | Result |
|---|---|
| The phase average alone | 13.65 |
| The learned weights | 13.68 |
| Their gain over the phase average | the interval runs from -3.5 to +2.3: zero is inside |
| Learning curve at 64, 160, 320 and 640 possessions | 13.97, 13.81, 13.71, 13.68 |

The 5,000-possession run is not triggered (D-136).

**Asked again on the calibrated computer's play** (640 possessions, `fit_strong2.json`): 8.75 against 8.82. The
interval runs from -0.04 to +2.44, so it is still not clear of zero, but it is closer, and the curve is still falling
(9.21, 9.10, 9.07, 8.75).

## Calibration: head to head, and when it shoots

**The calibrated reading beats today's computer.** `eval.calibrated` is off; this is the first round's map.

| Test against today's computer | Result |
|---|---|
| Head to head (sequential) | Stopped at 160 pairs with "a gain": **+3.2 points a pair, interval +0.9 to +5.5** |
| Wins, losses, ties | 69, 63, 28: it wins by more, not more often |
| The outcome exam, 218 positions | **+3.0 points a position, interval +1.9 to +4.0**; better on 125, worse on 64 |
| The offence to act (145 positions) | +4.0, interval +2.7 to +5.3 |
| The defence to act (73 positions) | +0.9, interval -1.2 to +2.9: level |
| The hand boards (22 decisions) | +3.3, interval -0.3 to +6.9 |
| Speed | The same as today's computer |

**When it shoots,** each computer playing itself, 640 possessions:

| | Today's computer | Calibrated | Basketball |
|---|---|---|---|
| Points a possession | 26.5 (25.4 to 27.6) | 28.8 (28.0 to 29.5) | |
| Ends with a shot or free throws | 82% | 92% | |
| The clock runs out with no shot | 3 in 100 | 0 in 640 | about 1 in 100 |
| Ends some other way with no shot | 15 in 100 | 8 in 100 | |
| Shots by phase, 1 to 6 | 20, 22, 13, 9, 7, 29% | 37, 35, 16, 9, 2, 0% | |
| Average phase of the shot | 3.5 | 2.1 | |
| Decisions a possession | 38 | 21 | |

**It has swung from late to early.** 72% of its shots come in the first two phases and almost none in the last. The
points say that pays. Whether it looks like basketball is yours to judge.

## Compute against the predictions

Cap: 16 core-hours. Used: about 14.9. Every run's prediction is in `docs/runs/step17/PREDICTIONS.md`.

| Run | Predicted | Used | Against the prediction |
|---|---|---|---|
| The strong-play pilot, 640 possessions | 3.6 | 3.73 | 26.5 points (22 predicted); the clock out on 3 in 100 (5 to 15 predicted) |
| Head to head, the first map | at most 3.8; a gain of 1 to 3 | 1.46 | +3.2: the top of the range; stopped early |
| Self-play by the calibrated computer | 2.3 | 1.96 | as predicted |
| Head to head, the second map | at most 2.5; no clear further gain | 3.25 | **over on cost**; no further gain, as predicted |
| The outcome exam, 218 positions | 3.5; +2 to +3 on offence, level on defence | 4.42 | **over on cost**; +4.0 on offence, level on defence |

## 1. Changes to the printed game

None. `eval.calibrated` is off.

## 2. What changed

- **D-135 to D-137 recorded.**
- **`eval.calibrated`** (off), in `decide.py` and `engine.js`: today's reading of what a position has left to earn
  is passed through a map fitted to what positions went on to earn. One map per phase and side to act, stored as
  knots in the shared weights file. Nothing else in the search changes.
- **The map kept** (`calibration_strong_linear.json`): per phase and side, earned = a + b x reading, fitted on the
  640 strong-play possessions. It was the best of four forms on held-out error:

| Form | Held-out error |
|---|---|
| Today's reading as it stands | 14.99 |
| A level per phase and side only | 13.79 |
| A never-falling map | 13.73 |
| One slope for every phase | 13.67 |
| **A straight line per phase and side** | **13.64** |

- **What the map says:** today's reading is 2 points too hopeful in phase 1 and 10 in phase 6. A point of reading
  is worth 0.2 points early and 0.8 late: the reading means more as the clock runs down.
- **The outcome exam has 73 positions with the defence to act** (66 added from the strong-play run, 11 a phase).
- **Tools:** `tools/learn_17.py` fits the maps, runs the head-to-head in batches until the sequential test decides,
  and counts how possessions end.

## 3. What it proves

- **The two engines agree with the switch on:** 1,000 positions, the calibrated value equal on all 954 compared,
  within 1e-9 (`golden_calibrated_1000.json`); 400 positions and 4 whole searches, 0 mismatches
  (`js_equivalence_calibrated.json`).
- **The defence held.** Today's computer scored 26.5 a possession against the calibrated defence, the same as
  against its own.
- **The second round added nothing, so the rounds stop** (`h2h_calibrated_round2_vs_default.json`). The map fitted
  again on the calibrated computer's own play scored +2.1 a pair (interval +0.2 to +4.0, 320 pairs), not better than
  the first. It also had a hole: that computer so rarely reaches the last phase that there were too few positions to
  fit one, so in phase 6 it fell back on today's reading.
- **Tests, every switch off:** `test_rules_current`, `test_static`, `test_step3n`, `test_step3m`: 77 pass, 13 expected
  failures, 1 unexpected pass, 1 fail (board 10's test, on the Python search's clock). **Step 16's own code gives
  exactly the same today,** fail included: the machine is running these tests about 15% slower than when step 16 was
  reported, and that board turns on the clock. It isn't from this step's changes.

## 4. For Shaun to decide

- **Switch `eval.calibrated` on?**
  - For: +3.2 points a pair head to head and +3.0 a position on the exam, both clear of zero; the clock no longer
    runs out; no cost in speed; the defence unchanged.
  - Against: it shoots early. 72% of shots in the first two phases may not be the basketball you want.
  - Option: switch it on for the All-Star only, or for every level.
- **Stage 2 (learning which moves to consider), on which judgement?** I'd build it on the calibrated reading. The
  learned weights have shown no clear signal twice.
- **The learned weights, a third time?** On calibrated play the fit is within a hair of clear and still improving
  with data. A run of 2,500 possessions by the calibrated computer costs about 8 core-hours (its possessions are
  half the length). It was not approved, so it wasn't run.
- **The second-round lesson:** a map fitted on a computer's own play loses the phases that computer no longer
  reaches. If the map is ever refitted, the play it is fitted on needs positions from every phase.

## 5. Noticed, not touched

- **The marks themselves overlap** (11.3 against 8.4, each with an interval about 3.5 either side), because offence
  and defence positions pull the mark opposite ways. The gain is measured position by position on the same dice,
  and that interval is clear of zero.
- **No worked examples of the reasons record.** The calibrated reading has no per-reading weights to explain; its
  reason is the map itself.
- **The first step 17 weights (the weak-play pilot) are still in the weights file** beside the calibration, for the
  golden test. `eval.learned` stays off.
- **The exam book** is untouched.

## 6. Model for the next step

Claude Fable 5.2, effort high: stage 2 is new design work (a move prior across both engines), and its results will
need the same care in reading as these.
