# Step 18r: estimates, written before measuring (16 Nov 2026)

Shaun's order (16 Nov): the agreed rules first; then the offence takes an open lane; then the lane read inside the
speed budget; then setup judged by the lane; then passing options. Proof-sized (D-196): a stage past twice its
estimate stops and is reported.

| Stage | What the compute buys | Estimate (core-hours) |
|---|---|---|
| 1a | The agreed rules (D-198) in both engines, agreeing; the tests the rule change moves. | 1.0 |
| 1b | The maps refitted on play under the new rules (All-Star 200 possessions, Starter 90, Rookie 120), the goldens re-recorded. | 2.5 |
| 1c | What the rules do to play: reaches, fouls, turnovers and points a possession, before and after, from that same self-play. | 0 (the same runs) |
| 1d | Speed against step 18q's code. | 0.3 |
| 2 | The offence takes an open lane (the drive's effect on the other four): forced lines, 16 a line. | 1.5 |
| **Total** | | **5.3** (stop at 10.6) |

What I expect from the rules: reaches fall from about 0.8 a possession to well under half that; turnovers a
possession fall with them; fouls a possession fall; points a possession stay near 1.1 (the −5s and +5s roughly
cancel, and possessions that used to end at 0 now go on to a shot).

## Compute used
- self-play (fit_allstar, allstar, 200 possessions): 1.57 (running total 1.57)
- self-play (fit_starter, starter, 90 possessions): 0.19 (running total 1.76)
- self-play (fit_rookie, rookie, 120 possessions): 0.09 (running total 1.85)
- check 1 played (new_rules) (4 positions, 16 each, the lane reading {'O': False, 'X': False}): 0.55 (running total 2.41)
- speed, round 1 (one core): 0.08 (running total 2.48)
- speed, round 2 (one core): 0.08 (running total 2.56)
- self-play (after_refit, allstar, 100 possessions): 1.12 (running total 3.68)
- check 1 played (new_rules) (4 positions, 16 each, the lane reading {'O': False, 'X': False}): 0.63 (running total 4.31)
- speed, round 1 (one core): 0.06 (running total 4.37)
- speed, round 2 (one core): 0.06 (running total 4.43)
- one core: the agreement checks of the two engines under the new rules (about 1,500 seconds): 0.42 (running total 4.85)
- one core: the named tests, three full runs (1,524, 1,464 and 1,511 seconds), the site tests and the exam positions twice: 1.36 (running total 6.21)

**Total: 6.2 core-hours as tallied, against the estimate of 5.3 (the stop was 10.6).** No stage passed twice its
estimate. The refit was run and not kept, so the play-outs and the speed timing were each run twice.

**What I expected and what happened.** Reaches: expected well under half of 0.80; they fell to 0.07. Fouls fell with
them (0.33 to 0.01). Points a possession: expected near 1.1; they rose to 1.34, because a fifth of possessions used
to end at 0 on a turnover and now go on to a shot. Not expected: the speed budget breaking (the line the computer
reads no longer ends at a turnover), and the refit failing an exam position.

**The files here.** `stats_fit_allstar.json`, `stats_fit_starter.json`, `stats_fit_rookie.json`: self-play under the
new rules with the maps as they were (the report's numbers). `stats_after_refit.json` and `refit_not_kept/`: the
refit that was dropped. `played_new_rules.json`: the open-lane lines, the maps as they were.
`reach_on_shauns_board.json` was read with the refitted maps (a reach 25.0, no reach 25.4); with the maps as they
were it reads 23.5 against 23.1 to 23.3.
