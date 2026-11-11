# Step 18b: predictions, written before each run

The prompt's cap was 4 core-hours; Shaun left the cap to my judgement ("time caps are flexible"). My plan: about 10.
Costs are core-hours on this machine (4 cores). A prediction isn't edited after its run; the result goes under it.

## 1. Head to head: `eval.settle_shots` on, against the calibrated default (sequential, up to 400 pairs)

- Cost: 1.5 to 2.5.
- Result: a gain of 1 to 4 points a pair, clear of zero. Most of it on defence: today the defence's search reads
  every shot the offence could declare as an open-play position on the uncalibrated scale, so it can't tell a
  shot it can Contest from one it can't.
- Shot timing: still early. 60% to 75% of the settled computer's shots in phases 1 and 2.

## 2. Head to head: `play_on` on, against the calibrated default (sequential, up to 400 pairs)

- Cost: 1.5 to 2.5.
- Result: less than the new switch, 0 to 2 points a pair, and the interval may include zero. `play_on` settles a
  declared shot with only the defenders already next to the shooter; it doesn't count a defender who steps in and
  then Contests, so it reads some contested shots as open.

## 3. Self-play with `eval.settle_shots` on, 200 possessions under the app's rules and 200 under the table's

- Cost: 0.6 and 1.0.
- The chance of losing the ball in a phase the offence keeps it: about the same as with the switch off (the stored
  logs give 7.4 in 100 under the app's rules and 1.1 in 100 at the table). The switch changes which shots are
  taken, not how risky passing is.
- The clock runs out: 0 to 2 in 100 under the app's rules; 2 to 6 in 100 at the table.

## 4. The outcome exam, 218 positions: the default, `eval.settle_shots`, and `play_on`

- Cost: 2.2 an engine, 6.6 in all. If the head-to-heads run long, `play_on`'s exam is dropped first, then the whole
  exam.
- `eval.settle_shots`: a gain with the defence to act (+1 to +3 a position), level or a small gain on offence.
