# Step 18c: the compute estimate, and predictions written before each run

## The estimate (written before any run)

**About 14 core-hours** on this machine (4 cores). What this step needs:

| Work | Core-hours | Why |
|---|---|---|
| `eval.settle_shots` at Rookie and Starter, 160 pairs each | 1.5 | 18a's level checks cost 0.54 and 1.06 |
| Boards 1 and 3 taken apart, the diagnosis, the agreement checks | 1.5 | each defence board is about 8 core-minutes a pass |
| Head to head, `eval.help_readings` on, up to 400 pairs | 2.5 | 18b's decided at 160 pairs for 0.8; a smaller gain needs more |
| The outcome exam, the default and the new switch | 2.0 | 18b's cost 1.85 |
| The defence's list cost, 12 positions, switch off and on | 3.5 | about 8 core-minutes a position a pass |
| Self-play for shot timing, 200 possessions | 0.6 | 18b's cost 0.53 |
| A second variant (the coverage budget with the readings as its prices), only if the readings gain alone | 2.5 | one more head to head |

App only: nothing is measured under the table's rules (Shaun, 11 Nov 2026).

## 1. `eval.settle_shots` at Rookie and Starter (each against its calibrated self without it, 160 pairs, its own pick noise)

- Cost: 0.5 and 1.0.
- Rookie: no clear difference. Its pick noise (5.0) is larger than the fix's effect; I expect -1 to +3 a pair with
  zero inside the interval.
- Starter: a small gain, 0 to +3 a pair; the interval may include zero.
- Neither loses clearly, so the switch goes on by default.
