# Step 18q: estimates, written before measuring (15 Nov 2026)

Proof-sized (D-196): each stage is estimated here first; a stage that runs past twice its estimate stops and is
reported; a point proved stops its stage.

| Stage | What the compute buys | Estimate (core-hours) |
|---|---|---|
| 1a | The way to the rim next phase goes into the reading, both engines, and they agree (the agreement runs). | 0.6 |
| 1b | Design checks 1, 3 and 4 on Shaun's board, lane on against lane off: the reading, the search, and forced lines (16 play-outs a line, up to 4 rounds). | 1.2 |
| 1c | Speed against step 18p's code, timed in the same hour. | 0.3 |
| 1d | If the checks fall out: the map refitted on play where lanes are taken, the goldens re-recorded, the named tests. | 2.0 |
| 2 | In-play faults the checks still show after 1 (the defender's step and reach after the ball handler; the block; shot types): forced lines only. | 1.5 |
| **Total** | | **5.6** (stop at 11) |

What I expect: with the way to the rim read one phase on, the offence takes the open lane on Shaun's board
(baseline: 0 of 16) and the reading of "lane open" sits clearly above "help in the lane" (baseline: 23.3 either way).
The defence should put a man between the ball and the rim when it can. An arrow walling a drive (check 3) may not
fall out from this alone.

## Compute used
- speed, round 1 (one core): 0.09 (running total 0.09)
- check 1 played (lane_on) (4 positions, 16 each, the lane reading {'O': True, 'X': True}): 0.64 (running total 0.72)
- check 1 played (lane_on2) (6 positions, 16 each, the lane reading {'O': True, 'X': True}): 1.03 (running total 1.76)
- self-play, the lane reading on (lane1, allstar, 120 possessions): 0.85 (running total 2.61)
- a second self-play round, stopped after 4 minutes when the measure changed (the Dribble added): 0.27 (running total 2.87)
- self-play, the lane reading on (lane3, allstar, 160 possessions): 1.18 (running total 4.05)
- check 1 played (lane_final) (4 positions, 16 each, the lane reading {'O': True, 'X': True}): 0.61 (running total 4.66)
- speed, round 1 (one core): 0.12 (running total 4.78)
- speed, round 2 (one core): 0.11 (running total 4.88)
- one core: the agreement checks of the two engines, all rounds (about 2,300 seconds): 0.64 (running total 5.52)
- one core: the design checks by the reading and the search, five rounds (about 1,200 seconds): 0.33 (running total 5.86)
- one core: the named tests (1,370 seconds) and the golden and engine tests (65): 0.4 (running total 6.25)

**Total: 6.3 core-hours as tallied, against the estimate of 5.6 (the stop was 11).** Stage 1b (the design checks) used
2.6 against 1.2, past twice its estimate: the measure was rebuilt twice after its first play-outs (the defence's step
into the lane, then the Dribble) and each form was played again. Stage 2 was not reached.

**What I expected and what happened.** The reading does put "lane open" above "help in the lane" (25.1 against 23.2;
it was 24.8 against 23.7). The offence does not take the open lane (expected: it would). The defence does not put a
man between more often in play (expected: it would): its best turn is the reach, and help can't arrive in one turn.

**The files here.** `played_lane_on.json` and `played_lane_on2.json` are play-outs of two earlier forms of the measure
(before the defence's step into the lane, and before the Dribble and the fitted map); `played_lane_final.json` is the
measure as built. `selfplay_lane1.json` and `arm_lane1.json` are the first round (before the Dribble);
`selfplay_lane3.json` and `arm_lane3.json` the round the map is fitted on. `readings_allstar.json` is the table of
section 3 of the report.
