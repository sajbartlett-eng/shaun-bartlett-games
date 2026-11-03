# Solver Report

Budgets used in this run: **90 s and 240 s per card** (defaults in `solver_config.py`: 2 and 10 minutes), seeds 0 and 1 at the short budget. Every value is **estimated** (guided search, evaluation at the leaves) unless marked exact. A card is **unstable** if its values spread by more than 2 points across runs, or its first play changes between budgets.

Value is the expected possession score under best play; look is the expected shot value (or foul points); P(30+) is the chance of an Excellent look. Coach's Call rows use the known-target value.

## Summary

| # | Card | Value | Look | P(30+) | Plans | Verdict | Label | Depth | Spread |
|---|---|---|---|---|---|---|---|---|---|
| 13 | One Phase Left | 18.0 | 18.0 | 0% | 15 | Wall | estimated | 2 | 0.0 |
| 7 | Two or Three | 24.1 | 25.8 | 65% | 2 | Puzzle | estimated | 2 | 0.0 |

## Rule health

### 1. Open question 7: the defence playing its last token ends the phase

| # | Card | As built | Phase runs on | Difference | Opening changes |
|---|---|---|---|---|---|

### 2. Action use in the principal lines

| Side | Action | Times played | Cards using it |
|---|---|---|---|
| Offence | move | 0 | 0 of 2 |
| Offence | qs | 0 | 0 of 2 |
| Offence | sprint | 0 | 0 of 2 |
| Offence | pass | 1 | 1 of 2 |
| Offence | screen | 0 | 0 of 2 |
| Offence | dribble | 0 | 0 of 2 |
| Offence | hesitate | 0 | 0 of 2 |
| Offence | shot | 1 | 1 of 2 |
| Defence | move | 0 | 0 of 2 |
| Defence | qs | 0 | 0 of 2 |
| Defence | sprint | 0 | 0 of 2 |
| Defence | intercept | 1 | 1 of 2 |
| Defence | challenge | 0 | 0 of 2 |
| Defence | steal | 0 | 0 of 2 |
| Defence | pause | 0 | 0 of 2 |
| Defence | end_turn | 0 | 0 of 2 |

### 3. And-one

No principal line contains a foul outcome.

### 4. Clock expiry

| # | Card | P(clock 0) | Expected forced-shot points | Value as built | Value with "forced shot or −5, whichever is worse" |
|---|---|---|---|---|---|
| 13 | One Phase Left | 0% | 0.00 | 18.0 | 18.0 |
| 7 | Two or Three | 0% | 0.00 | 24.1 | 24.1 |

## Cards

<div class="file"></div>

### 13. One Phase Left

LATE CLOCK, clock 2. O: Shoot and Protect. X: Lockdown. *Six tokens each, then the clock is gone. Every action has to count.*

**Value 18.0**, look 18.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 15. **Verdict: Wall** (estimated; depth 2; spread 0.0 across 18.0, 18.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (shoot, clock 2): O3 Shot (three)
2. **Defence** (no reaction, clock 2): X End turn

*Result:* total 18 (Okay), shot value 18, goal missed. O3 three 3 x (12 - 6) contested by X3

**Opening plans within 90% of best** (top 5 shown): O3 Shot (three) (18.0); O3 Move to O8 (18.0); O3 Move to O8 then O3 Shot (three) (18.0); O3 Dribble vs X3 (17.9); O1 Screen, T S (17.9)

<div class="file"></div>

### 7. Two or Three

LATE CLOCK, clock 4. O: Shoot and Protect. X: Bucket Brigade. *Down 2. An Excellent three wins it; an Excellent two ties it.*

**Value 24.1**, look 25.8, P(30+) 65%, P(clock 0) 0%. Plans within 90%: 2. **Verdict: Puzzle** (estimated; depth 2; spread 0.0 across 24.1, 24.1).

**Principal line** (best play, following the most likely roll):

1. **Offence** (kick, clock 4): O1 Pass to O3
2. **Defence** (intercept, clock 4): X3 Intercept — Pass O1->O3 vs Intercept X3: pass completes (offence needs 13 or less; 65%)

*Result:* search horizon reached; evaluation 30.0 (look 30.0)

**Opening plans within 90% of best** (top 5 shown): O1 Pass to O3 (24.1); O3 Move to P7 then O1 Pass to O3 (24.1)
