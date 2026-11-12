# Step 18e: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine.

## Estimate: about 12 core-hours without part 4, about 20 with it

| Part | Core-hours | Why |
|---|---|---|
| 1. The rule as the default | 0.2 | agreement checks only; no refit (18d found the map's error didn't rise) |
| 2. Pilot: the 11 defence positions, up to three passes | 2.7 | 0.9 a pass at 18d's settings |
| 2. Head to head, up to 400 pairs, All-Star, sequential | 5.0 | 18c's 240 pairs cost 2.0; the open list makes each search slower |
| 2. The sense checks played out by the rules | 1.0 | a few positions, two moves each, a few hundred play-outs |
| 2. Speed, agreement checks | 0.8 | |
| 3. Shaun's playtest | 0.1 | one position, two settings |
| 4. The offence's list: pilot on 18a's 48 positions, then a head to head | 8.0 | only if part 2 wins and the pilot shows a gain |
| 5. The 19 boards, shot timing and the rushed shares | 2.0 | one self-play run of 200 possessions, the boards at 1 pair |

Stop rules: part 2 stops at the pilot if the choice isn't best more often and the points left don't fall. Part 4
stops at its pilot the same way. The head to head stops early once its interval is clear of 0 either way.

## Cost found before building (not a run over 30 minutes)

Reading every legal defence action with the full ordering reading costs about 250 microseconds an action, and a
defence position has 500 to 1,200 legal first actions (a Move to each square with each of 8 facings is most of them).
A search asks for a list at about 25 positions, each with first and second actions. That is tens of seconds a
decision. So the build uses the form the prompt allows: a cheap first read of every legal action, by the reading's own
re-read of one moved defender, then the full read of the best.

## 1. The pilot: 18d's 11 defence positions under the new default rules, today's list and the open list

- Cost: 0.9 a pass, two passes.
- **Today's list:** about as before (the choice best on 4 of 11, 1.2 to 1.35 points left), since the rule changed
  only by the foul roll.
- **The open list:** the choice best on 7 or more of 11, and under 0.6 points left. The first build already puts
  "step in, then Steal" on the list on three of the positions without being told.
- **Result:** 1.76 core-hours for the two passes, on 12 positions (the twelfth no longer fails). **Right.**
  - Today's list under the new rules: the choice best on 5 of 12, 1.11 points left (interval 0.28 to 1.95); all 7
    losses a first action never generated.
  - The open list: best on 9 of 12, 0.29 left (interval -0.07 to 0.65); none over 2 points.
  - An earlier pass of the open list was stopped and thrown away (about 0.7 core-hours): the replay of Shaun's game
    showed a fault in the cheap read (it denied a defender his Move in the reaction when the defence had two tokens
    left). Fixed before these passes.

## 2. Head to head: the All-Star with the open list against the new default, up to 400 pairs

- Cost: about 5 (the open list makes a decision on offence slower: about 25 defence lists a search, each about 11 ms
  dearer).
- **A gain of 0 to +2.5 points a pair, most likely about +1.** The pilot's gain is by the computer's own reading 1
  pair ahead; a head to head is play to the end. The reading still can't tell many defence turns apart (they read the
  same at the phase table's floor), so a longer list of them buys less than the pilot suggests. I expect the
  sequential test to need most of the 400 pairs, and a fair chance (about 2 in 5) that it ends "no gain".
- Shot timing on offence unchanged. On defence, more Steals tried, so more possessions ended by a Steal or a steal
  foul.
- **Result:** 1.95 core-hours; the sequential test said "a gain" at 186 pairs and the run stopped at 240. **Wrong on
  the size:** +4.7 points a pair (interval 2.7 to 6.8), 98 wins, 81 losses, 61 ties. Right on where it comes from:
  the open list's defence ends 75 of 240 possessions with the ball lost (a Steal), against 30 of 240 the other way.
  Shot timing on offence unchanged (70% and 72% of shots in phases 1 and 2).

## 3. The sense checks: five positions, each move played out 160 times

- Cost: about 1 (written as 1.0 in the estimate).
- I expect the computer's move to look right on the Steal positions and too close to call on the closeout board.
- **Result:** 2.26 core-hours for a first pass that was thrown away: its four parallel parts shared dice (the
  play-outs were about 43 distinct ones repeated), so its intervals were far too narrow. Rerun with separate dice:
  see the report.

## 4. Self-play on the final default, 200 possessions (part 5)

- Cost: 1.0.
- Points about 29 (as 18d's size 2); the ball lost about twice as often as 18d's 4.7 in 100 phases kept; rushed
  shots about 18%; the map's error about 8.
- **Result:** 1.06 core-hours. **Wrong on points and the ball lost:** 26.8 points (interval 25.1 to 28.4); the ball
  lost 14.2 times in 100 phases kept (10.1 to 19.7), three times 18d's. Rushed shots 13%. The map's error rose to
  10.8 (9.2 to 12.4).

## 5. The offence's list, a pilot (part 4): 24 of step 18a's offence positions

- Two passes: today's offence list, and every legal offence action read in full (`search.open_list` 'both': too slow
  to play, but it answers the pilot's question). Cost: about 1.5 a pass.
- Today's list: the choice best on about half, about 0.75 points left (18a's figure).
- Every action read: best on 3 in 4, under 0.3 left.

Sense checks, the rerun with separate dice: 2.17 core-hours.
- **Result (the offence's pilot):** 0.24 core-hours for both passes (offence positions have about 5,000 legal turns,
  not 270,000). **Wrong:** today's offence list is best on 17 of 24 with 0.55 left (0.02 to 1.09); with every legal
  offence action read it is best on 15 of 24 with 0.65 left (0.14 to 1.16). No gain, so part 4 stops at its pilot.
  - Against the prediction: right on the two Steal positions (the computer's move scores 3.8 and 2.3 better) and on
    the closeout board's second step (too close to call). **Wrong on its first step:** Shaun's Quick Step closer is
    1.9 better (0.8 to 3.1). On Shaun's own game the computer's Move closer is 3.0 better.
