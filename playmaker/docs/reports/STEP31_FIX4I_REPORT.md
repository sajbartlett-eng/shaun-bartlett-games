# Step 31, fix 4i: exact speed only. Report

**On branch `step-31`. Not merged. The exam was not run. Stopped as you asked: the exact savings don't reach the targets.**

- **Every answer equals fix 4h's.** Both new ways of reading, and the old way, give the same number and answer on all 21 R and P boards. The turn and the defence setup make the same decisions.
- **A turn is 25% faster:** 83 s to 63 s on four cores, against about 20.
- **The defence setup barely moved:** 409 s to 405 s, against about a minute.
- **The offence setup is still far over:** past 20 minutes when its run was cut off, against about a minute.
- **What's left is reading named movements' races.** No exact saving I found shrinks it (section 4).

## 1. Changes to the printed game

None.

## 2. Where the offence setup's time goes (profiled first)

**What the offence setup does:**
1. It reads 15 starting placements, each against the defence's quick stance.
2. It improves the best two, one player at a time; each try is another quick stance.
3. It runs a full defence setup on each of those two.

So it contains dozens of quick stances and two whole defence setups.

**One quick stance, on one core: 68.5 s.**
- **Almost all of it, 66.7 s, is the goal-side shape it starts from.** That's 45 readings of the number.
- **Those readings named 3,670 movements** (2,735 of them by the two-step routes). The floor skipped 2,273, and 1,510 were read in full.
- **Of its time:**
  - 88% is the answer's named movements: reading their races 53%, their floors 19%, kind 3's test 10%;
  - the fake's follow-up, read inside those, is 23%.
- **Four cores ran past 25 minutes before even the first 15 placements were read.** That's 15 quick stances shared among four workers.

**A turn, on one core: 127.5 s.**
- 80% is the named movements: read in full 44% (races 37%), kind 3's test 18%, floors 16%.
- The fake's follow-up is 31%, and two-thirds of that is ranking every look again from nothing after each movement tried.
- **On four cores the turn was only 1.5 times faster than on one.** The workers were often idle: each batch went out in four fixed blocks, and the readings in a batch differ in cost by up to 50 times.

## 3. What was built (D-320)

1. **The fake's follow-up, read by difference.**
   - A movement changes the follow-up only through two things:
     - the mover's own contests, his column; for the closer that column doesn't count, as the follow-up puts his closeout in its place;
     - the race looks, once the races are read again.
   - So the board's readings are kept, and each look is read again only where one of those changed.
   - The best look after the fake is kept unless a changed look can reach it. A look whose ceiling (its worth with the closer's contest taken off) is below the best can't.
   - When the movement is taken back, the board's own readings come back whole.
   - It serves kind 3's test, the floors and the full reads alike. Kind 3's test is item 2 of your brief: the two-step route by difference.
2. **Batches handed out from a shared counter.**
   - Each worker takes the next run of neighbouring readings as it goes free, two runs per worker, and the answers go back in the batch's own order.
   - In Node and in the app's workers.
   - One reading at a time was slower (99 s on the turn): neighbouring readings share most of their work, and splitting them loses that.

**Not built, and why:**
- **Handing one reading's named movements to the workers.** A worker would have to rebuild the reading up to the step being answered: everything before the full reads, about 40% of a reading. The full reads are the other 60%, so splitting them four ways saves nothing. The batch-level counter is what pays.
- **Keeping race reads across readings.** The same movement onto the same board doesn't always read the same race. Its kick-outs use each look's contests from the map of the board before the movement, so reusing a read isn't exact.

## 4. Times

Four cores, the engine and each worker held to 256 MB (`docs/runs/step31/fix4i_times.txt`):

| Reading | Fix 4h | + follow-up by difference | + the queue (fix 4i) | Target |
|---|---|---|---|---|
| A turn on E13 | 83.3 s | 71.7 s | **62.7 s** | about 20 s |
| Defence setup (E1) | 409.5 s | 396.5 s | **404.8 s** | about a minute |
| Offence setup (E15b) | over 30 min | | still reading after about 20 min* | about a minute |

- *The container restarted about 20 minutes into the offence setup's run. I didn't run it again: by its parts (section 2) it can't come near a minute.
- **The same decision at every step:** the turn's results and line, and E1's whole answer, hash equal to fix 4h's.
- **How close:**
  - **The turn:** 63 s, three times the target.
  - **The defence setup:** 6.7 minutes, about seven times.
  - **The offence setup:** over 20 minutes, more than 20 times. It holds two defence setups and about 45 quick stances.
- **What's left:** in every reading, the named movements' races (about half the time in a setup), then their floors.
  - Each named movement needs its races read, and on the board after the movement nearly every race state changes (fix 4e found this).
  - The floor already skips about 60% of the named movements in a setup.
  - I found no exact saving left that reads fewer of them, or reads them for less.

## 5. The checks

| Check | Result | Time |
|---|---|---|
| The proof (`tools/step_31_fix4i_proof.py`): JavaScript by difference and afresh against fix 4h, all 21 boards; Python on its five fastest | the same as fix 4h on 21 of 21; Python the same on its five (R5 c, R5 control, P3, P5, P5 two off) | 4.7 min |
| A turn and the defence setup against fix 4h | the same decisions | (in section 4's runs) |
| Fix 4i's test: P4 and P2 two off, follow-up by difference against afresh and fix 4h | passed | lane D |
| Fix 4f's test (four cores, now on the queue, against one), fix 4g's tests, fix 4h's by-difference test | 5 passed | lane D (9 min) |
| Engine equality (40 random positions) | 0 mismatches | lane C |
| Fix 2's, 3's, 4's and 4c's tests | 7 passed (fix 4c's also alone, 3.6 min) | lane C |
| The rules, memory and golden game | 33 passed | lane A (3 min) |

**Over the 10 minutes, and skipped:**
- The proof took 4.7 minutes and the lanes about 15 side by side. Lane C ran past its runner's limit after its tests had passed; I reran fix 4c's alone.
- **Python ran on 5 of 21 boards.** Its engine is unchanged in fix 4i, and fix 4h's proof holds it to the JavaScript on all 21.
- **Not run:**
  - fix 4e's tests (the exact answer, whose code fix 4i doesn't touch);
  - fix 4h's Python test of the new kinds;
  - the value's guards;
  - fix 1's test and the P held searches;
  - the exam, as asked.

## 6. For Shaun to decide

The exact savings stop here: a turn at 63 s, the setups at 7 and over 20 minutes.
- **Kind 3 is most of the gap.** At fix 4h, without kind 3, a turn took 40 s and the defence setup 4 minutes; it closed the last three boards.
- **The offence setup holds two whole defence setups and about 45 quick stances.** Its time is the defence's answer's time, many times over.

The ways on that keep every answer are yours to choose: accept the time, or change what the setups read, which is a design question.

## 7. Model for the next step

Claude Opus 5.5, effort high. Your choice in section 6, then fix 5.
