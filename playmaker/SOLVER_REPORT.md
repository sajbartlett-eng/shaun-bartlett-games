# Solver Report

Budgets used in this run: **90 s and 240 s per card** (defaults in `solver_config.py`: 2 and 10 minutes), seeds 0 and 1 at the short budget. Every value is **estimated** (guided search, evaluation at the leaves) unless marked exact. A card is **unstable** if its values spread by more than 2 points across runs, or its first play changes between budgets.

Value is the expected possession score under best play; look is the expected shot value (or foul points); P(30+) is the chance of an Excellent look. Coach's Call rows use the known-target value.

## Summary

**Stale (step 3d):** cards 2, 3, 8, 9, 11 and 12 use Twin Towers or Ball Movement, which were rebuilt in step 3d. Their rows below were solved with the old teams and are kept for comparison; the re-solve with the new teams is queued (`round3d_jobs`, results in `solver_results/runs_3d.json`). See `solver_results/STALE.json`.

| # | Card | Value | Look | P(30+) | Plans | Verdict | Label | Depth | Spread |
|---|---|---|---|---|---|---|---|---|---|
| 13 | One Phase Left | 21.0 | 21.0 | 0% | 4 | Puzzle | unstable | 4 | 3.0 |
| 7 | Two or Three | 28.1 | 30.5 | 88% | 19 | Gift | unstable | 4 | 4.1 |
| 10 | Late Clock Reset | 19.5 | 19.5 | 25% | 2 | Puzzle | unstable | 4 | 4.5 |
| 6 | Need a Three | 30.0 | 30.0 | 100% | 17 | Gift | unstable | 4 | 6.0 |
| 5 | Sideline, Late | 27.7 | 28.4 | 70% | 15 | Puzzle | estimated | 4 | 0.5 |
| 3 | Sideline Out (stale) | 23.2 | 23.2 | 45% | 9 | Puzzle | estimated | 4 | 1.2 |
| 4 | Deny Everything | 3.6 | 7.6 | 20% | 2 | Puzzle | estimated | 2 | 0.0 |
| 1 | Baseline Box | 36.0 | 36.0 | 100% | 11 | Gift | unstable | 4 | 0.0 |
| 2 | Baseline Stack (stale) | 19.5 | 19.5 | 35% | 2 | Puzzle | unstable | 4 | 7.5 |
| 8 | Coach's Call (stale) | 20.0 | 18.0 | 0% | 4 | Wall | estimated | 2 | 0.0 |
| 9 | Coach's Call, Late (stale) | 24.8 | 20.4 | 35% | 2 | Puzzle | estimated | 2 | 0.0 |
| 11 | After a Timeout (stale) | 25.5 | 22.7 | 0% | 3 | Puzzle | estimated | 2 | 0.0 |
| 12 | Mismatch on the Switch (stale) | 21.0 | 21.0 | 0% | 16 | Puzzle | estimated | 3 | 0.0 |
| 14 | Hold for One | 22.3 | 20.0 | 0% | 12 | Puzzle | unstable | 4 | 0.0 |
| 15 | In the Bonus | 29.7 | 25.9 | 76% | 111 | Gift | unstable | 4 | 0.7 |
| 16 | Star Locked | 26.0 | 26.0 | 0% | 1 | Single trick | unstable | 4 | 4.0 |

## Suggested fixes, re-solved

Each fix changes only the card setup. Both columns are the same budget (240 s, seed 0).

| # | Card | Fix | Before | After |
|---|---|---|---|---|
| 6 | Need a Three | Swap X2 and X3: the Defensive SF (contest 6 on threes) takes O2, the sharpshooter; X2 (contest 3) takes O3. | Gift: 30.0, P(30+) 100%, 17 plans | **Single trick**: 27.4, P(30+) 25%, 1 plans |
| 6 | Need a Three | Swap X1 and X2: the Defensive PG (contest 5 on threes) starts on O2 at D9; X2 takes the ball at I10. | Gift: 30.0, P(30+) 100%, 17 plans | **Single trick**: 27.4, P(30+) 25%, 1 plans |
| 7 | Two or Three | Swap X3 and X4: the Post Scorer PF (contest 5 on threes) starts on O3 at P8, X3 (contest 2) on O4 at F9. | Gift: 28.1, P(30+) 88%, 19 plans | **Puzzle**: 24.4, P(30+) 29%, 36 plans |
| 15 | In the Bonus | Swap X4 and X5: the Post Scorer PF (contest 6 on posts) starts on O5 at H3, X5 on O4. | Gift: 29.7, P(30+) 76%, 111 plans | **Gift**: 29.7, P(30+) 76%, 111 plans |
| 15 | In the Bonus | X5 fronts the post: starts on G4 (between O5 and the ball) instead of H3. | Gift: 29.7, P(30+) 76%, 111 plans | **Gift**: 29.7, P(30+) 76%, 111 plans |
| 8 | Coach's Call | X4 starts behind O4, on G2 instead of G3: a seal for the post looks, contested from the far side. | Wall: 20.0, P(30+) 0%, 4 plans | **Wall**: 20.0, P(30+) 0%, 4 plans |
| 8 | Coach's Call | Swap X1 and X5: the switch leaves a guard (Combo Guard B, post contest 3) on O5 and the Rim Runner on O1. | Wall: 20.0, P(30+) 0%, 4 plans | **Wall**: 20.0, P(30+) 0%, 15 plans |
| 8 | Coach's Call | Defence team Pace and Space -> Bucket Brigade (weaker interior defence). | Wall: 20.0, P(30+) 0%, 4 plans | **Single trick**: 29.0, P(30+) 0%, 1 plans |
| 1 | Baseline Box | X1 starts on F6, outside O1 (G6), instead of H5 in the lane: the perimeter cut is taken away. | Gift: 36.0, P(30+) 100%, 11 plans | **Gift**: 30.0, P(30+) 100%, 2 plans |
| 1 | Baseline Box | X1 starts on F5 (below and outside O1) instead of H5. | Gift: 36.0, P(30+) 100%, 11 plans | **Gift**: 30.0, P(30+) 100%, 14 plans |
| 1 | Baseline Box | X1 starts on F6 and X2 on L7: both wing defenders outside their men, cutting the path to the arc. | Gift: 36.0, P(30+) 100%, 11 plans | **Single trick**: 27.1, P(30+) 32%, 1 plans |
| 16 | Star Locked | Clock 6 -> 8: one more phase gives the locked star a second way in. | Single trick: 26.0, P(30+) 0%, 1 plans | **Single trick**: 26.0, P(30+) 0%, 1 plans |
| 16 | Star Locked | X2 plays O2 straight up on D9 (arrow on him) instead of denying from D8. | Single trick: 26.0, P(30+) 0%, 1 plans | **Single trick**: 26.0, P(30+) 0%, 1 plans |

## Search settings and their tested effect

All live in `solver_config.py`.

| Setting | Value | Tested effect |
|---|---|---|
| `top_k_raw` (K) | 8 | Candidate coverage 50/50 on random endgames. In the principal lines, 52 turns used a concept play and 3 a raw action. |
| `raw_depth` | 1 | Raw actions are added at the root only; deeper nodes use concept plays (cost). |
| `beam` / `root_beam` | 6 / 40 | Not varied in this run (time). Guided search on micro positions with beam 30 matched exact values within 0.5. |
| `endgame_tokens` (N) / `exact_node_cap` | 2 / 4000 | The exact solver never triggered on a full card: no principal line reaches the last phase with 2 or fewer tokens inside the horizon. Exactness is tested on micro positions (matches brute force; pruning changes nothing). |
| `quiescence` | on | Leaves where the defence is to move get one more defence turn. Without it, Need a Three showed P(30+) = 100% on a line with a 45% interception risk. Costs 2 to 4 times the search time. |
| Inbound evaluation prices interception risk | on | Before → after (240 s): Baseline Box 36.0 → 36.0, Baseline Stack 28.1 → 19.5, Sideline Out 23.2 → 23.2, Deny Everything 38.0 → 3.6, Sideline, Late 27.9 → 27.7, After a Timeout 46.0 → 25.5. |
| `kick_weight` | 0 | 0.9 tried on One Phase Left and Need a Three at depth 3: no change in value (21.0, 30.0). Kept at 0. |
| Budgets | 90 s and 240 s | Defaults are 2 and 10 minutes; see Limits. Values moved by up to the spreads in the summary table between the two budgets. |

## Audit: arrows and the reaction (step 3e)

**Question:** does the solver's evaluation score a contest from the arrow's current facing, which would
ignore that a defender can still turn or step in as a reaction once the shot is declared?

**Answer: no.** `Evaluator.defended` uses `defender_reach` with the reaction budget (up to 2 actions,
limited by the tokens left). A defender whose Move is unused and who is not locked reaches every Move
square with any facing (including a turn in place), and Quick Step or Sprint arrivals keep their set
facing. A contest counts as clean when a reachable arrival faces the shooter; otherwise it counts as a
foul roll; with no reach it doesn't count. The search itself plays real reactions. So the solver already
charges for a lost reaction (Move used, locked, no tokens) and nothing else.

**What that means for the Pause result:** the facing model is not its cause. The known cause stands
(the one-turn evaluation doesn't score defensive position for the offence's later turns; round 2's
two-turn evaluation addresses it). The computer opponent had the blind spot, not the solver: it judged
contests from the current facing. Step 3e replaced it with a defence that uses this evaluation.

## Limits of this run

- **Budgets were scaled down** from 2 and 10 minutes to 90 and 240 seconds, and from 5 seeds to 2, to fit the session (the full default set is about 30 hours of compute on this machine). `python -m playmaker_engine solve-all` runs the defaults.
- **Depth is 2 to 4 turns.** Clock-8 cards last 20 or more turns, so the value is "the best look the offence can force in the next few turns", not the whole possession. The leaf evaluation fills in the rest.
- **Seeds only change tie-breaking.** The search is deterministic, so the spread mostly reflects budget (depth reached), not randomness.
- **Coach's Call** searches reached depth 2 only (five targets share the budget), so the secret's value could not be measured at this depth.
- **The evaluation does not score defensive position for later turns.** That is why Pause (doing nothing) often ties for best: see rule health 2.

## Coach's Call bounds

| # | Card | Known target (defence plays against it) | Guessing defence | Secret worth | Best target |
|---|---|---|---|---|---|
| 8 | Coach's Call | 20.0 (O1) | 20.0 (O1) | +0.0 | O1 |
| 9 | Coach's Call, Late | 24.8 (O5) | 24.8 (O5) | +0.0 | O5 |
| 11 | After a Timeout | 25.5 (O2) | 25.5 (O2) | +0.0 | O2 |

## Rule health

### 1. Open question 7: the defence playing its last token ends the phase

| # | Card | As built | Phase runs on | Difference | Opening changes |
|---|---|---|---|---|---|
| 13 | One Phase Left | 18.0 | 18.0 | +0.0 | no |
| 7 | Two or Three | 24.1 | 24.1 | +0.0 | no |
| 10 | Late Clock Reset | 15.0 | 15.0 | +0.0 | no |
| 6 | Need a Three | 24.0 | 30.0 | +6.0 | no |
| 5 | Sideline, Late | 27.2 | 27.2 | +0.0 | no |
| 3 | Sideline Out | 22.0 | 22.0 | +0.0 | no |
| 4 | Deny Everything | 3.6 | 3.6 | +0.0 | no |
| 1 | Baseline Box | 36.0 | 36.0 | +0.0 | no |
| 2 | Baseline Stack | 12.0 | 12.0 | +0.0 | no |
| 8 | Coach's Call | 20.0 | 20.0 | +0.0 | no |
| 9 | Coach's Call, Late | 24.8 | 24.8 | +0.0 | no |
| 11 | After a Timeout | 25.5 | 25.5 | +0.0 | no |
| 12 | Mismatch on the Switch | 21.0 | 21.0 | +0.0 | no |
| 14 | Hold for One | 22.3 | 22.3 | +0.0 | no |
| 15 | In the Bonus | 29.0 | 29.0 | +0.0 | no |
| 16 | Star Locked | 22.0 | 22.0 | +0.0 | no |

### 2. Action use in the principal lines

| Side | Action | Times played | Cards using it |
|---|---|---|---|
| Offence | move | 7 | 7 of 16 |
| Offence | qs | 2 | 2 of 16 |
| Offence | sprint | 3 | 3 of 16 |
| Offence | pass | 13 | 11 of 16 |
| Offence | screen | 3 | 3 of 16 |
| Offence | dribble | 3 | 3 of 16 |
| Offence | hesitate | 1 | 1 of 16 |
| Offence | shot | 2 | 2 of 16 |
| Defence | move | 11 | 8 of 16 |
| Defence | qs | 1 | 1 of 16 |
| Defence | sprint | 0 | 0 of 16 |
| Defence | intercept | 2 | 2 of 16 |
| Defence | challenge | 0 | 0 of 16 |
| Defence | steal | 2 | 2 of 16 |
| Defence | pause | 10 | 10 of 16 |
| Defence | end_turn | 0 | 0 of 16 |

### 3. And-one

No principal line contains a foul outcome.

### 4. Clock expiry

Best play never runs the clock out on any card: every principal line shoots inside the search horizon, so P(clock 0) is 0% throughout. To give the designer the numbers anyway, this table prices a forced shot from each card's starting position (the carrier shoots where it stands after the defence's last two actions; inbound cards use the player furthest from the rim).

| # | Card | Forced shot | As built (forced shot − 5) | Alternative (worse of forced shot or −5) |
|---|---|---|---|---|
| 13 | One Phase Left | 18.0 | 13.0 | -5.0 |
| 7 | Two or Three | 0.0 | -5.0 | -5.0 |
| 10 | Late Clock Reset | 0.0 | -5.0 | -5.0 |
| 6 | Need a Three | 0.0 | -5.0 | -5.0 |
| 5 | Sideline, Late | 0.0 | -5.0 | -5.0 |
| 3 | Sideline Out | 0.0 | -5.0 | -5.0 |
| 4 | Deny Everything | 0.0 | -5.0 | -5.0 |
| 1 | Baseline Box | 19.4 | 14.4 | -5.0 |
| 2 | Baseline Stack | 18.7 | 13.7 | -5.0 |
| 8 | Coach's Call | 0.0 | -5.0 | -5.0 |
| 9 | Coach's Call, Late | 14.0 | 9.0 | -5.0 |
| 11 | After a Timeout | 0.0 | -5.0 | -5.0 |
| 12 | Mismatch on the Switch | 0.0 | -5.0 | -5.0 |
| 14 | Hold for One | 0.0 | -5.0 | -5.0 |
| 15 | In the Bonus | 0.0 | -5.0 | -5.0 |
| 16 | Star Locked | 0.0 | -5.0 | -5.0 |

Because forced shots are floored at 0, "the worse of the two" is always −5: the alternative simply removes the forced shot. Per-card values from the solver runs:

| # | Card | P(clock 0) | Expected forced-shot points | Value as built | Value with "forced shot or −5, whichever is worse" |
|---|---|---|---|---|---|
| 13 | One Phase Left | 0% | 0.00 | 21.0 | 21.0 |
| 7 | Two or Three | 0% | 0.00 | 28.1 | 28.1 |
| 10 | Late Clock Reset | 0% | 0.00 | 19.5 | 19.5 |
| 6 | Need a Three | 0% | 0.00 | 30.0 | 30.0 |
| 5 | Sideline, Late | 0% | 0.00 | 27.7 | 27.7 |
| 3 | Sideline Out | 0% | 0.00 | 23.2 | 23.2 |
| 4 | Deny Everything | 0% | 0.00 | 3.6 | 3.6 |
| 1 | Baseline Box | 0% | 0.00 | 36.0 | 36.0 |
| 2 | Baseline Stack | 0% | 0.00 | 19.5 | 19.5 |
| 8 | Coach's Call | 0% | 0.00 | 20.0 | 20.0 |
| 9 | Coach's Call, Late | 0% | 0.00 | 24.8 | 24.8 |
| 11 | After a Timeout | 0% | 0.00 | 25.5 | 25.5 |
| 12 | Mismatch on the Switch | 0% | 0.00 | 21.0 | 21.0 |
| 14 | Hold for One | 0% | 0.00 | 22.3 | 22.3 |
| 15 | In the Bonus | 0% | 0.00 | 29.7 | 29.7 |
| 16 | Star Locked | 0% | 0.00 | 26.0 | 26.0 |

## Cards

<div class="file"></div>

### 13. One Phase Left

LATE CLOCK, clock 2. O: Shoot and Protect. X: Lockdown. *Six tokens each, then the clock is gone. Every action has to count.*

**Value 21.0**, look 21.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 4. **Verdict: Puzzle** (unstable; depth 4; spread 3.0 across 18.0, 18.0, 21.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (swing, clock 2): O3 Pass to O1
2. **Defence** (pause, clock 2): X Pause
3. **Offence** (kick, clock 2): O1 Pass to O2
4. **Defence** (closeout, clock 2): X2 Move to D9 facing W

*Result:* search horizon reached; evaluation 21.0 (look 21.0)

**Opening plans within 90% of best** (top 5 shown): O3 Pass to O1 / O1 Pass to O2 (21.0); O3 Pass to O1 / O2 Move to D9 then O1 Pass to O2 (21.0); O3 Move to N9 / O3 Pass to O2 (21.0); O3 Move to N9 / O2 Move to D9 then O3 Pass to O2 (21.0)

<div class="file"></div>

### 7. Two or Three

LATE CLOCK, clock 4. O: Shoot and Protect. X: Bucket Brigade. *Down 2. An Excellent three wins it; an Excellent two ties it.*

**Value 28.1**, look 30.5, P(30+) 88%, P(clock 0) 0%. Plans within 90%: 19. **Verdict: Gift** (unstable; depth 4; spread 4.1 across 24.1, 24.1, 28.1).

**Principal line** (best play, following the most likely roll):

1. **Offence** (relocate+kick, clock 4): O3 Move to P7 then O1 Pass to O3
2. **Defence** (intercept, clock 4): X3 Intercept — Pass O1->O3 vs Intercept X3: pass completes (offence needs 13 or less; 65%)
3. **Offence** (dribble, clock 4): O3 Dribble vs X3 — Dribble O3 vs X3: dribble wins (50%)
4. **Defence** (pause, clock 4): X Pause

*Result:* search horizon reached; evaluation 36.0 (look 36.0)

**Opening plans within 90% of best** (top 5 shown): O3 Move to P7 then O1 Pass to O3 / O3 Dribble vs X3 (33.0); O1 Pass to O3 / O3 Dribble vs X3 (31.5); O1 Pass to O2 / O2 Dribble vs X2 (31.1); O1 Pass to O2 / O3 Move to P7 then O2 Pass to O3 (30.0); O1 Pass to O3 / O1 Screen, T S (30.0)

**Suggested fix:** Swap X3 and X4: the Post Scorer PF (contest 5 on threes) starts on O3 at P8, X3 (contest 2) on O4 at F9. Re-solved at the same budget: Gift 28.1 → Puzzle 24.4 (P(30+) 29%, 36 plans): becomes a **Puzzle**.

<div class="file"></div>

### 10. Late Clock Reset

LATE CLOCK, clock 4. O: Iron Wall. X: Run and Gun. *The set broke down. Both Screens are spent: O4's is down, O5's is still up. Offence has 4 tokens left, defence 4.*

**Value 19.5**, look 19.5, P(30+) 25%, P(clock 0) 0%. Plans within 90%: 2. **Verdict: Puzzle** (unstable; depth 4; spread 4.5 across 15.0, 15.0, 19.5).

**Principal line** (best play, following the most likely roll):

1. **Offence** (raw, clock 4): O1 Sprint to L8
2. **Defence** (closeout, clock 4): X3 Move to M9 facing SW
3. **Offence** (kick, clock 4): O1 Pass to O5
4. **Defence** (closeout, clock 4): X4 Move to I4 facing SE

*Result:* search horizon reached; evaluation 19.5 (look 19.5)

**Opening plans within 90% of best** (top 5 shown): O1 Move to K9 / O1 Pass to O5 (19.5); O1 Sprint to L8 / O1 Pass to O5 (19.5)

<div class="file"></div>

### 6. Need a Three

LATE CLOCK, clock 6. O: Five Out. X: Iron Wall. *Down 3. Only a three counts, and the defence knows it: nobody helps, everybody stays home.*

**Value 30.0**, look 30.0, P(30+) 100%, P(clock 0) 0%. Plans within 90%: 17. **Verdict: Gift** (unstable; depth 4; spread 6.0 across 24.0, 30.0, 30.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (kick, clock 6): O1 Pass to O4
2. **Defence** (pause, clock 6): X Pause
3. **Offence** (kick, clock 6): O4 Pass to O2
4. **Defence** (closeout, clock 6): X2 Move to D9 facing W

*Result:* search horizon reached; evaluation 30.0 (look 30.0)

**Opening plans within 90% of best** (top 5 shown): O2 Move to C8 then O1 Pass to O2 / O2 Dribble vs X2 (34.0); O1 Pass to O2 / O2 Shot (three) (30.0); O1 Pass to O2 / O2 Dribble vs X2 (30.0); O1 Pass to O2 / O1 Screen, T S (30.0); O1 Pass to O2 / O3 Screen, T W (30.0)

**Suggested fix:** Swap X2 and X3: the Defensive SF (contest 6 on threes) takes O2, the sharpshooter; X2 (contest 3) takes O3. Re-solved at the same budget: Gift 30.0 → Single trick 27.4 (P(30+) 25%, 1 plans): improves to **Single trick** but is not yet a Puzzle.

<div class="file"></div>

### 5. Sideline, Late

INBOUNDS, clock 4. O: High-Low. X: Five Out. *Inbound from the left wing, then 4 seconds: two phases to catch and score.*

**Value 27.7**, look 28.4, P(30+) 70%, P(clock 0) 0%. Plans within 90%: 15. **Verdict: Puzzle** (estimated; depth 4; spread 0.5 across 27.2, 27.2, 27.7).

**Principal line** (best play, following the most likely roll):

1. **Offence** (kick, clock 4): O2 Pass to O5
2. **Defence** (allow, clock 4): X End turn
3. **Offence** (dribble, clock 4): O5 Dribble vs X5 — Dribble O5 vs X5: dribble wins (50%)
4. **Defence** (pause, clock 4): X Pause

*Result:* search horizon reached; evaluation 33.8 (look 33.8)

**Opening plans within 90% of best** (top 5 shown): O5 Move to I2 then O2 Pass to O5 / O5 Dribble vs X5 (32.6); O2 Pass to O5 / O5 Dribble vs X5 (27.7); O2 Pass to O5 / O3 Screen, T NE (27.2); O2 Pass to O3 / O3 Pass to O5 (27.2); O2 Pass to O5 / O1 Screen, T SE (27.2)

<div class="file"></div>

### 3. Sideline Out

INBOUNDS, clock 8. O: Ball Movement. X: Shoot and Protect. *Inbound from the right wing. The weak-side defender is two passes away and sags into the lane.*

**Value 23.2**, look 23.2, P(30+) 45%, P(clock 0) 0%. Plans within 90%: 9. **Verdict: Puzzle** (estimated; depth 4; spread 1.2 across 22.0, 22.0, 23.2).

**Principal line** (best play, following the most likely roll):

1. **Offence** (relocate+kick, clock 8): O5 Move to K4 then O3 Pass to O5
2. **Defence** (allow, clock 8): X End turn
3. **Offence** (dribble, clock 8): O5 Dribble vs X5 — Dribble O5 vs X5: dribble loses (55%)
4. **Defence** (pause, clock 8): X Pause

*Result:* search horizon reached; evaluation 16.0 (look 16.0)

**Opening plans within 90% of best** (top 5 shown): O5 Move to K4 then O3 Pass to O5 / O5 Dribble vs X5 (23.2); O4 Screen, T S / O5 Move to K4 then O3 Pass to O5 (22.0); O5 Move to K4 then O3 Pass to O5 / O1 Screen, T S (22.0); O5 Move to K4 then O3 Pass to O5 / O4 Screen, T S (22.0); O5 Move to K4 then O3 Pass to O5 / O Hesitate (22.0)

<div class="file"></div>

### 4. Deny Everything

INBOUNDS, clock 8. O: Pace and Space. X: Lockdown. *Sideline inbound against a defence denying every lane. No pass is free: you must move to get open.*

**Value 3.6**, look 7.6, P(30+) 20%, P(clock 0) 0%. Plans within 90%: 2. **Verdict: Puzzle** (estimated; depth 2; spread 0.0 across 3.6, 3.6, 3.6).

**Principal line** (best play, following the most likely roll):

1. **Offence** (screen, clock 8): O3 Screen, T S
2. **Defence** (pause, clock 8): X Pause

*Result:* search horizon reached; evaluation 3.6 (look 7.6)

**Opening plans within 90% of best** (top 5 shown): O3 Screen, T S (3.6); O3 Move to M8 then O3 Screen, T NW (3.6)

<div class="file"></div>

### 1. Baseline Box

INBOUNDS, clock 8. O: Bucket Brigade. X: Iron Wall. *Inbound from the baseline beside the rim. The defence packs the lane, each player touching their man.*

**Value 36.0**, look 36.0, P(30+) 100%, P(clock 0) 0%. Plans within 90%: 11. **Verdict: Gift** (unstable; depth 4; spread 0.0 across 36.0, 36.0, 36.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (screen, clock 8): O2 Screen, T SW
2. **Defence** (closeout, clock 8): X3 Move to J1 facing SE
3. **Offence** (relocate+kick, clock 8): O1 Sprint to D3 then O5 Pass to O1
4. **Defence** (allow, clock 8): X End turn

*Result:* search horizon reached; evaluation 36.0 (look 36.0)

**Opening plans within 90% of best** (top 5 shown): O2 Screen, T SW / O1 Sprint to D3 then O5 Pass to O1 (36.0); O1 Sprint to C2 / O5 Pass to O1 (36.0); O1 Sprint to C2 / O1 Quick Step to A2 then O5 Pass to O1 (36.0); O1 Sprint to D9 then O5 Pass to O1 / O2 Screen, T SW (36.0); O1 Sprint to D9 then O5 Pass to O1 / O3 Screen, T E (36.0)

**Suggested fix:** X1 starts on F6 and X2 on L7: both wing defenders outside their men, cutting the path to the arc. Re-solved at the same budget: Gift 36.0 → Single trick 27.1 (P(30+) 32%, 1 plans): improves to **Single trick** but is not yet a Puzzle. Root cause is open question 35 (a completed inbound gives the receiver a free turn); setup changes only trim it.

<div class="file"></div>

### 2. Baseline Stack

INBOUNDS, clock 8. O: Run and Gun. X: Twin Towers. *Inbound from the baseline corner. Four players stacked on the lane line, all defenders on the inside.*

**Value 19.5**, look 19.5, P(30+) 35%, P(clock 0) 0%. Plans within 90%: 2. **Verdict: Puzzle** (unstable; depth 4; spread 7.5 across 12.0, 12.0, 19.5).

**Principal line** (best play, following the most likely roll):

1. **Offence** (raw, clock 8): O1 Sprint to Q5
2. **Defence** (closeout+closeout, clock 8): X2 Move to O1 facing SW then X5 Move to M1 facing SE
3. **Offence** (relocate+kick, clock 8): O1 Quick Step to Q7 then O2 Pass to O1
4. **Defence** (allow, clock 8): X End turn

*Result:* search horizon reached; evaluation 19.5 (look 19.5)

**Opening plans within 90% of best** (top 5 shown): O1 Sprint to Q5 / O1 Quick Step to Q7 then O2 Pass to O1 (19.5); O1 Sprint to P1 / O2 Pass to O1 (18.7)

<div class="file"></div>

### 8. Coach's Call

COACH'S CALL, clock 8. O: Twin Towers. X: Pace and Space. *Before setup, secretly write the player you want to score. Run the play to get them the shot.*

**Value 20.0**, look 18.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 4. **Verdict: Wall** (estimated; depth 2; spread 0.0 across 20.0, 20.0, 20.0).

Known-target values: O1 20.0, O2 18.0, O3 18.0, O4 18.0, O5 18.0.

**Principal line** (best play, following the most likely roll):

1. **Offence** (drive, clock 8): O1 Move to J10
2. **Defence** (pause, clock 8): X Pause

*Result:* search horizon reached; evaluation 20.0 (look 18.0)

**Opening plans within 90% of best** (top 5 shown): O1 Move to J10 (20.0); O1 Move to J10 then O1 Shot (three) (20.0); O1 Quick Step to J10 (20.0); O1 Quick Step to J10 then O1 Shot (three) (20.0)

**Suggested fix:** Defence team Pace and Space -> Bucket Brigade (weaker interior defence). Re-solved at the same budget: Wall 20.0 → Single trick 29.0 (P(30+) 0%, 1 plans): improves to **Single trick** but is not yet a Puzzle. The Pace and Space interior contests cap every Twin Towers post look below 30; only a team change moves it.

<div class="file"></div>

### 9. Coach's Call, Late

COACH'S CALL, clock 6. O: Lockdown. X: Ball Movement. *Secret target with 6 seconds left. The ball is with your centre at the elbow.*

**Value 24.8**, look 20.4, P(30+) 35%, P(clock 0) 0%. Plans within 90%: 2. **Verdict: Puzzle** (estimated; depth 2; spread 0.0 across 24.8, 24.8, 24.8).

Known-target values: O1 19.2, O2 20.0, O3 20.7, O4 19.2, O5 24.8.

**Principal line** (best play, following the most likely roll):

1. **Offence** (drive+shoot, clock 6): O5 Move to I4 then O5 Shot (post)
2. **Defence** (closeout+steal, clock 6): X4 Move to J4 facing W then X4 Steal — Steal foul roll X4: no foul (65%); Steal: Dribble O5 vs Steal X4: kept (65%)

*Result:* total 25 (Great), shot value 20, coach's call +5, goal missed. O5 post 2 x (16 - 6) contested by X4

**Opening plans within 90% of best** (top 5 shown): O5 Move to I4 then O5 Shot (post) (24.8); O5 Move to I4 (24.2)

<div class="file"></div>

### 11. After a Timeout

COACH'S CALL, clock 8. O: Ball Movement. X: High-Low. *Sideline inbound after a timeout, with a secret target. Draw it up: the defence has to guess.*

**Value 25.5**, look 22.7, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 3. **Verdict: Puzzle** (estimated; depth 2; spread 0.0 across 25.5, 25.5, 25.5).

Known-target values: O1 19.9, O2 25.5, O3 19.9, O4 19.9, O5 19.9.

**Principal line** (best play, following the most likely roll):

1. **Offence** (kick, clock 8): O1 Pass to O2
2. **Defence** (intercept, clock 8): X1 Intercept — Pass O1->O2 vs Intercept X1: pass completes (offence needs 12 or less; 60%)

*Result:* search horizon reached; evaluation 35.0 (look 27.0)

**Opening plans within 90% of best** (top 5 shown): O1 Pass to O2 (25.5); O2 Move to B7 then O1 Pass to O2 (25.5); O2 Sprint to B4 (24.6)

<div class="file"></div>

### 12. Mismatch on the Switch

CONSTRAINT, clock 6. O: Twin Towers. X: Run and Gun. *A switch left X1, the point guard, on your post scorer, and X5 on the ball. The defence knows too.*

**Value 21.0**, look 21.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 16. **Verdict: Puzzle** (estimated; depth 3; spread 0.0 across 21.0, 21.0, 21.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (raw, clock 6): O4 Screen, T SW
2. **Defence** (pause, clock 6): X Pause
3. **Offence** (drive+shoot, clock 6): O1 Move to J10 then O1 Shot (three)

*Result:* search horizon reached; evaluation 21.0 (look 21.0)

**Opening plans within 90% of best** (top 5 shown): O4 Screen, T SW / O1 Move to J10 then O1 Shot (three) (21.0); O4 Screen, T SW / O1 Quick Step to J10 then O1 Shot (three) (21.0); O3 Sprint to K9 / O1 Move to J10 (21.0); O3 Sprint to K9 / O1 Move to J10 then O1 Shot (three) (21.0); O3 Sprint to K9 / O1 Quick Step to J10 (21.0)

<div class="file"></div>

### 14. Hold for One

CONSTRAINT, clock 8. O: Pace and Space. X: High-Low. *Last shot of the quarter. No shot before the final phase (clock on 2). A turnover ends it at 0.*

**Value 22.3**, look 20.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 12. **Verdict: Puzzle** (unstable; depth 4; spread 0.0 across 22.3, 22.3, 22.3).

**Principal line** (best play, following the most likely roll):

1. **Offence** (drive, clock 8): O1 Move to K10
2. **Defence** (pause, clock 8): X Pause
3. **Offence** (kick, clock 8): O1 Pass to O3
4. **Defence** (steal, clock 8): X3 Steal — Steal foul roll X3: no foul (55%); Steal: Dribble O3 vs Steal X3: kept (70%)

*Result:* search horizon reached; evaluation 24.0 (look 24.0)

**Opening plans within 90% of best** (top 5 shown): O3 Move to O8 then O1 Pass to O3 / O3 Quick Step to P7 (33.0); O3 Move to O8 then O1 Pass to O3 / O3 Dribble vs X3 (31.5); O3 Move to O8 then O1 Pass to O3 / O1 Screen, T S (31.5); O3 Move to O8 then O1 Pass to O3 / O2 Screen, T SE (31.5); O3 Move to O8 then O1 Pass to O3 / O3 Screen, T NW (31.5)

<div class="file"></div>

### 15. In the Bonus

CONSTRAINT, clock 8. O: High-Low. X: Bucket Brigade. *The defence has one steal foul: start on +5, and its next steal foul gives free throws. The goal is still a 30+ look.*

**Value 29.7**, look 25.9, P(30+) 76%, P(clock 0) 0%. Plans within 90%: 111. **Verdict: Gift** (unstable; depth 4; spread 0.7 across 29.0, 29.0, 29.7).

**Principal line** (best play, following the most likely roll):

1. **Offence** (drive, clock 8): O1 Move to H10
2. **Defence** (pause, clock 8): X Pause
3. **Offence** (kick, clock 8): O1 Pass to O5
4. **Defence** (help, clock 8): X4 Move to I3 facing W

*Result:* search horizon reached; evaluation 29.7 (look 25.9)

**Opening plans within 90% of best** (top 5 shown): O1 Pass to O5 / O5 Dribble vs X5 (30.1); O5 Move to I2 then O1 Pass to O5 / O5 Dribble vs X5 (29.9); O1 Pass to O5 / O1 Screen, T S (29.7); O1 Pass to O5 / O2 Screen, T E (29.7); O1 Pass to O5 / O4 Screen, T S (29.7)

**Suggested fix:** Swap X4 and X5: the Post Scorer PF (contest 6 on posts) starts on O5 at H3, X5 on O4. Re-solved at the same budget: Gift 29.7 → Gift 29.7 (P(30+) 76%, 111 plans): improves to **Gift** but is not yet a Puzzle. The card starts at +5, and P(30+) of 76% sits just over the 75% Gift line; the post entry to O5 decides it.

<div class="file"></div>

### 16. Star Locked

CONSTRAINT, clock 6. O: Bucket Brigade. X: Iron Wall. *Your star picked up the ball and is locked until the phase resets. He can still pass or shoot.*

**Value 26.0**, look 26.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 1. **Verdict: Single trick** (unstable; depth 4; spread 4.0 across 22.0, 22.0, 26.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (hesitate, clock 6): O Hesitate
2. **Defence** (closeout, clock 6): X1 Move to J11 facing W
3. **Offence** (drive, clock 6): O1 Quick Step to H10
4. **Defence** (closeout, clock 6): X2 Move to F10 facing E then X2 Quick Step to G10

*Result:* search horizon reached; evaluation 26.0 (look 26.0)

**Opening plans within 90% of best** (top 5 shown): O Hesitate / O1 Quick Step to H10 (26.0)

**Suggested fix:** Clock 6 -> 8: one more phase gives the locked star a second way in. Re-solved at the same budget: Single trick 26.0 → Single trick 26.0 (P(30+) 0%, 1 plans): improves to **Single trick** but is not yet a Puzzle. Neither candidate changed the single plan (Hesitate, then O1 Quick Steps to H10).
