# Step 18i: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine, counted by processor time; single-core runs count as one
core.

## Estimate: 7.5 core-hours. Hard stop: 12 (the lower of 12 and twice the estimate)

| Part | Core-hours | Why |
|---|---|---|
| Agreement checks between the two engines (each rule off and on, the capture rule), tests | 1.5 | one core; the named tests take about half an hour a run |
| The sense-check set: the positions each rule touches, replayed under the new rules | 2.0 | about 30 candidates at 32 play-outs |
| Self-play, All-Star, 160 possessions, before and after | 2.0 | about 1.0 each at 18g's cost |
| Pilots for each rule (a few dozen possessions) | 0.5 | |
| The same Steal position under three foul situations, by play | 0.5 | 3 situations, 3 candidates, 32 play-outs |
| A player in foul trouble: the pilot | 0.5 | stopped if it can't be measured cheaply |
| Speed, beside 18g's code | 0.3 | one core, two rounds |
| Searches | 0.2 | |

- A running tally is kept at the foot of this file. No run is started that can't finish inside 12.

## Predictions

1. **Three seconds:** with the rule on and nothing else changed, 3 to 10 possessions in 100 end in the violation,
   because the computer looks one pair ahead and a count that started a phase ago is out of its sight until the
   phase's last turn. If the reading is told when a violation can no longer be avoided, under 2 in 100.
2. **Closely guarded:** rare. Under 2 violations in 100 possessions: the ball rarely stays with one closely guarded
   player for three phase ends. A ball handler is closely guarded at about a third of phase ends.
3. **The fouled shot:** worth less than today on a three and more on a layup. Today a fouled shot scores the higher
   of the free throws and the open shot; under FIBA it scores the contested shot plus the free throws that follow.
   Points a possession move by less than 0.5.
4. **The foul situation:** at 4 team fouls with 10 possessions left the computer stops trying the Steal it tries at 0
   fouls; at 4 fouls with 1 left it tries it again only if the free throws cost less than what the Steal saves.
5. **Speed:** under 3% at each level. The counts are a few integer checks at a phase end.

## Tally (core-hours used)

- self-play (pilot_on, 32 possessions): 0.24 (running total 0.24)
- self-play (pilot_off, 32 possessions): 0.22 (running total 0.47)
- self-play (before, 160 possessions): 0.99 (running total 1.46)
- self-play (after, 160 possessions): 1.13 (running total 2.59)
- agreement checks between the two engines: the capture rule, broken zones, the FIBA rules with searches and reactions (one core each): 0.75 (running total 3.34)
- searches (fiba, 19 positions): 0.01 (running total 3.34)
- play-outs (108 candidate copies of 16 on 19 positions): 1.84 (running total 5.19)
