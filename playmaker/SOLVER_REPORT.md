# Solver Report (round 2)

Budgets: **2 and 10 minutes per card**, 5 seeds at the short budget (the full defaults). Coach's Call cards give each of the five targets its own budget. The evaluation looks over the offence's next two turns against the defence's best reply. Every value is **estimated** (guided search, evaluation at the leaves) unless marked exact; a card is **unstable** if its values spread by more than 2 points across its runs, or its first play changes between budgets.

Cards 2, 3, 8, 9, 11 and 12 use Twin Towers or Ball Movement, which were rebuilt in step 3d; they were re-solved with the new teams, as were the context runs that swapped in a rebuilt team.

## Summary

| # | Card | Value | Look | P(30+) | Plans | Verdict | Label | Depth | Spread |
|---|---|---|---|---|---|---|---|---|---|
| 13 | One Phase Left | 18.0 | 18.0 | 0% | 15 | Wall | estimated | 2 | 0.0 |
| 7 | Two or Three | 26.2 | 28.5 | 88% | 4 | Gift | estimated | 2 | 0.0 |
| 10 | Late Clock Reset | 19.5 | 19.5 | 25% | 1 | Single trick | unstable | 2 | 0.0 |
| 6 | Need a Three | 30.0 | 30.0 | 100% | 2 | Gift | estimated | 2 | 0.0 |
| 5 | Sideline, Late | 27.2 | 28.2 | 80% | 1 | Gift | estimated | 2 | 0.0 |
| 3 | Sideline Out | 21.4 | 22.8 | 45% | 1 | Single trick | estimated | 2 | 0.0 |
| 4 | Deny Everything | 9.2 | 15.8 | 44% | 1 | Single trick | estimated | 2 | 0.8 |
| 1 | Baseline Box | 36.0 | 36.0 | 100% | 2 | Gift | estimated | 2 | 0.0 |
| 2 | Baseline Stack | 16.6 | 19.4 | 35% | 4 | Puzzle | estimated | 2 | 0.0 |
| 8 | Coach's Call | 20.5 | 20.3 | 24% | 0 | Single trick | unstable | 4 | 0.5 |
| 9 | Coach's Call, Late | 26.0 | 21.0 | 0% | 6 | Puzzle | unstable | 4 | 1.2 |
| 11 | After a Timeout | 28.8 | 25.6 | 60% | 17 | Puzzle | unstable | 4 | 6.0 |
| 12 | Mismatch on the Switch | 21.8 | 21.8 | 25% | 4 | Puzzle | estimated | 2 | 0.0 |
| 14 | Hold for One | 22.3 | 20.0 | 0% | 2 | Puzzle | estimated | 2 | 0.0 |
| 15 | In the Bonus | 29.0 | 24.0 | 0% | 18 | Puzzle | estimated | 2 | 0.0 |
| 16 | Star Locked | 24.0 | 24.0 | 0% | 1 | Single trick | estimated | 2 | 0.0 |

Verdicts: Puzzle 6, Single trick 5, Gift 4, Wall 1. Labels: estimated 12, unstable 4.

## The six re-solved cards (step 3d teams)

| # | Card | Before (old teams) | After (new teams) |
|---|---|---|---|
| 2 | Baseline Stack | Wall (estimated): 18.0, P(30+) 0%, 2 plans | **Puzzle (estimated): 16.6, P(30+) 35%, 4 plans** |
| 3 | Sideline Out | Single trick (estimated): 22.0, P(30+) 0%, 1 plans | **Single trick (estimated): 21.4, P(30+) 45%, 1 plans** |
| 8 | Coach's Call | Single trick (unstable): 25.0, P(30+) 0%, 1 plans | **Single trick (unstable): 20.5, P(30+) 24%, 0 plans** |
| 9 | Coach's Call, Late | Puzzle (unstable): 26.0, P(30+) 0%, 6 plans | **Puzzle (unstable): 26.0, P(30+) 0%, 6 plans** |
| 11 | After a Timeout | Puzzle (unstable): 32.1, P(30+) 60%, 17 plans | **Puzzle (unstable): 28.8, P(30+) 60%, 17 plans** |
| 12 | Mismatch on the Switch | Puzzle (estimated): 21.0, P(30+) 0%, 2 plans | **Puzzle (estimated): 21.8, P(30+) 25%, 4 plans** |

## Proposed card fixes, re-solved

Setup only (squares, arrows, matchups, teams, clock): never a rule. Each fix was re-solved at the full long budget (10 minutes, seed 0) and is compared with the card at the same budget.

| # | Card | Fix | Before | After |
|---|---|---|---|---|
| 13 | One Phase Left | Swap X1 and X3: the Defensive PG (contest 4 on threes) takes O3 at O9, the Small Forward (6) takes O1. | Wall: 18.0, P(30+) 0%, 15 plans | **Puzzle**: 23.3, P(30+) 20%, 16 plans |
| 13 | One Phase Left | Defence team Lockdown -> Pace and Space (contest 4 on threes for the wing). | Wall: 18.0, P(30+) 0%, 15 plans | **Puzzle**: 24.0, P(30+) 0%, 15 plans |
| 7 | Two or Three | Defence team Bucket Brigade -> Lockdown: real three-point contesters on both corner shooters. | Gift: 26.2, P(30+) 88%, 4 plans | **Single trick**: 21.0, P(30+) 0%, 1 plans |
| 7 | Two or Three | Swap X3 and X4: the Post Scorer PF (contest 5 on threes) starts on O3 at P8. | Gift: 26.2, P(30+) 88%, 4 plans | **Puzzle**: 23.5, P(30+) 0%, 14 plans |
| 10 | Late Clock Reset | Clock 4 -> 6: one more phase, so more than one way in. | Single trick: 19.5, P(30+) 25%, 1 plans | **Single trick**: 19.5, P(30+) 25%, 1 plans |
| 10 | Late Clock Reset | X4 sags to F6 (a step off O4 toward the lane). | Single trick: 19.5, P(30+) 25%, 1 plans | **Single trick**: 19.5, P(30+) 25%, 1 plans |
| 6 | Need a Three | Defence team Iron Wall -> Lockdown: contest 5 on O2 the sharpshooter and 6 on O4 in the corner. | Gift: 30.0, P(30+) 100%, 2 plans | **Single trick**: 24.0, P(30+) 0%, 1 plans |
| 6 | Need a Three | Swap X2 and X3: the Defensive SF (contest 6 on threes) takes O2, the sharpshooter. | Gift: 30.0, P(30+) 100%, 2 plans | **Puzzle**: 24.0, P(30+) 0%, 3 plans |
| 5 | Sideline, Late | X3 plays O3 straight up on B4 (arrow on him) instead of sagging on B5. | Gift: 27.2, P(30+) 80%, 1 plans | **Gift**: 27.2, P(30+) 80%, 1 plans |
| 5 | Sideline, Late | Defence team Five Out -> Lockdown. | Gift: 27.2, P(30+) 80%, 1 plans | **Puzzle**: 20.7, P(30+) 68%, 2 plans |
| 3 | Sideline Out | X5 takes K4, between O5 and the rim: the post entry is denied. | Single trick: 21.4, P(30+) 45%, 1 plans | **Single trick**: 15.2, P(30+) 40%, 1 plans |
| 3 | Sideline Out | Swap X4 and X5: the bigger defender on the post, the other on O4 at K10. | Single trick: 21.4, P(30+) 45%, 1 plans | **Single trick**: 24.0, P(30+) 0%, 1 plans |
| 4 | Deny Everything | X3 sags to L8, a step off O3: one lane opens. | Single trick: 9.2, P(30+) 44%, 1 plans | **Single trick**: 1.9, P(30+) 16%, 1 plans |
| 4 | Deny Everything | Clock 8 -> 10: one more phase against the denial. | Single trick: 9.2, P(30+) 44%, 1 plans | **Single trick**: 9.2, P(30+) 44%, 1 plans |
| 1 | Baseline Box | X1 starts on F6 and X2 on L7: both wing defenders outside their men, cutting the path to the arc. | Gift: 36.0, P(30+) 100%, 2 plans | **Single trick**: 21.0, P(30+) 0%, 1 plans |
| 1 | Baseline Box | Defence team Iron Wall -> Lockdown. | Gift: 36.0, P(30+) 100%, 2 plans | **Puzzle**: 24.0, P(30+) 0%, 2 plans |
| 8 | Coach's Call | Defence team Pace and Space -> Iron Wall. | Single trick: 20.5, P(30+) 24%, 0 plans | **Puzzle**: 21.1, P(30+) 40%, 5 plans |
| 8 | Coach's Call | Defence team Pace and Space -> Bucket Brigade (no stopper). | Single trick: 20.5, P(30+) 24%, 0 plans | **Puzzle**: 27.2, P(30+) 26%, 2 plans |
| 16 | Star Locked | X1 takes H10, the locked star's step-back spot. | Single trick: 24.0, P(30+) 0%, 1 plans | **Puzzle**: 24.0, P(30+) 0%, 3 plans |
| 16 | Star Locked | Defence team Iron Wall -> Lockdown. | Single trick: 24.0, P(30+) 0%, 1 plans | **Puzzle**: 21.0, P(30+) 0%, 14 plans |

### Notes on the candidate cards

- **Need a Three:** the fix that works puts a real three-point defender on the best shooter: swapping X2 and X3 moves the Defensive SF (contest 6) onto O2 the sharpshooter, and the card becomes a Puzzle (24.0). A new defence team (Lockdown) also stops the Gift but leaves a Single trick.
- **Coach's Call (Single trick, no Wall at full budget):** a different defence team fixes it: Iron Wall (Puzzle 21.1, 5 plans) or Bucket Brigade (Puzzle 27.2, 2 plans).
- **In the Bonus:** now a Puzzle at full budget (29.0, P(30+) 0%, 18 plans); no longer borderline.
- **Star Locked:** the one plan is the locked star himself: O1 Quick Steps to H10 for an arc three (a locked player may still Quick Step, by the ruling that a lock means "can't Move or Sprint"). It changes with the matchup (Lockdown v Bucket Brigade: kick to the post; Twin Towers v Run and Gun: kick to the shooter). If the intended lesson is "someone else has to score", that is a ruling question (OPEN_QUESTIONS 51). Taking H10 away (X1 starts there) makes it a Puzzle (24.0, 3 plans).
- **No fix found** for Late Clock Reset, Sideline Out or Deny Everything: every setup change tried kept a Single trick. Deny Everything is a Single trick at 9.2 by design of the card (the defence denies everything); Sideline Out's one plan is the post entry, and denying it only lowered the value (15.2).

## The context test

**Plan-change rate: 35 of 39 (90%).** That is how often the best opening plan changes when only the lineup changes (same squares and clock). A high rate is the goal.

| # | Card | Best plan with the card's teams | Other matchups: best plan |
|---|---|---|---|
| 13 | One Phase Left | shoot: shooter, arc three | Pace and Space v Shoot and Protect: drive: shooter to arc three; Run and Gun v Twin Towers: drive: slasher to arc three |
| 7 | Two or Three | kick to the shooter | Shoot and Protect v Pace and Space: kick to the shooter (same); Twin Towers v Run and Gun: drive: guard to long two |
| 10 | Late Clock Reset | drive: guard to plain wood | High-Low v Run and Gun: drive: shooter to arc three; Pace and Space v Run and Gun: drive: playmaker to arc three; Iron Wall v Ball Movement: relocate the shooter and kick; Ball Movement v Iron Wall: drive: playmaker to arc three; Twin Towers v Run and Gun: relocate the shooter and kick |
| 6 | Need a Three | kick to the shooter | Lockdown v Bucket Brigade: swing to the post; Twin Towers v Run and Gun: drive: guard to arc three |
| 5 | Sideline, Late | swing to the wing | Bucket Brigade v Lockdown: swing to the post; Lockdown v Bucket Brigade: kick to the wing |
| 3 | Sideline Out | relocate the post and kick | Pace and Space v Shoot and Protect: relocate the post and kick (same); Run and Gun v Twin Towers: relocate the big and kick |
| 4 | Deny Everything | relocate: post to mid-range | Bucket Brigade v Lockdown: relocate: shooter to plain wood; Run and Gun v Twin Towers: kick to the big |
| 1 | Baseline Box | relocate the shooter and kick | Five Out v High-Low: relocate: shooter to long two; Ball Movement v Iron Wall: relocate the playmaker and kick |
| 2 | Baseline Stack | relocate: big to plain wood | Five Out v High-Low: swing to the big; Pace and Space v Shoot and Protect: swing to the post |
| 8 | Coach's Call | drive: guard to arc three | Shoot and Protect v Pace and Space: relocate the shooter and kick; High-Low v Five Out: attack the closeout (shooter) |
| 9 | Coach's Call, Late | drive and shoot: post, rim | Iron Wall v Ball Movement: relocate the shooter and kick; High-Low v Five Out: drive and shoot: post, rim (same) |
| 11 | After a Timeout | relocate: shooter to long two | Ball Movement v Iron Wall: relocate: shooter to long two (same); Five Out v High-Low: kick to the shooter |
| 12 | Mismatch on the Switch | relocate: shooter to long two | Five Out v High-Low: swing to the wing; Pace and Space v Shoot and Protect: drive: playmaker to arc three; High-Low v Run and Gun: screen by the post; Pace and Space v Run and Gun: screen by the big |
| 14 | Hold for One | kick to the shooter | Bucket Brigade v Lockdown: drive: shooter to plain wood; Run and Gun v Twin Towers: drive: slasher to arc three |
| 15 | In the Bonus | attack the closeout (shooter) | Bucket Brigade v Lockdown: drive: shooter to long two; Lockdown v Bucket Brigade: drive: guard to arc three; Pace and Space v Bucket Brigade: relocate the shooter and kick; Twin Towers v Bucket Brigade: relocate the shooter and kick |
| 16 | Star Locked | drive: shooter to arc three | Lockdown v Bucket Brigade: kick to the post; Twin Towers v Run and Gun: kick to the shooter |

**Flagged plans** (within 90% of the best in most matchups on most cards): **none**.

## Dead rules

Across 179 best lines (every card, budget, seed, target and matchup):

- **Challenge Screen:** played 1 times; never among the defence's root options either (0). The offence's best lines use a Screen at all in 5 of 179.
- **Defensive Sprint closeouts:** 0 times.
- **Screen-heavy teams on the screen cards:** card 10: High-Low (0 screens, 0 challenges, value 25.1), Pace and Space (0 screens, 0 challenges, value 24.5), Twin Towers (0 screens, 0 challenges, value 24.0); card 12: Pace and Space (0 screens, 0 challenges, value 19.9), High-Low (1 screens, 0 challenges, value 24.0), Pace and Space (1 screens, 0 challenges, value 21.0); card 15: Pace and Space (0 screens, 0 challenges, value 29.8), Twin Towers (0 screens, 0 challenges, value 29.0).

Both are dead rules at this depth: no context makes either one best. That is a question for the designer (see OPEN_QUESTIONS), with the caveat that the search reaches two turns on most cards.

## The Pause result

Defence steps in the principal lines (the 16 cards at 10 minutes): pause 10, move 4, intercept 3, steal 2, qs 2, none 1 (22 steps). **Pause is still the most-used defensive action in the principal lines (10 of 22).** But searched on its own, each of these defence positions has a Move that is clearly better than Pause (below). The Pause comes from where the defence's turn sits in the principal line: below the root, where the search tries only its concept plays (raw actions are added at the root only) and has little depth left. **So Pause is a search artefact, not a rule question**, and the same shallowness means card values (Gift verdicts above all) may favour the offence.

**Card 6, Need a Three**, after "O1 Pass to O4" (search depth 1): best X2 Move to C8 facing SW. Pause: 30.0. Best alternatives: X2 Move to C8 facing SW 26.0; X2 Move to B7 facing E 26.0; X2 Move to B7 facing SE 26.0; X2 Move to B7 facing S 26.0; worst X4 Move to B4 facing SW then X2 Move to D9 facing SW 39.0.

**Card 5, Sideline, Late**, after "O2 Pass to O3" (search depth 1): best X3 Move to B4 facing W. Pause: 27.2. Best alternatives: X3 Move to B4 facing W 15.0; X3 Move to D3 facing N 15.0; X3 Move to D3 facing NE 15.0; X3 Move to D3 facing E 15.0; worst X2 Move to A9 facing W then X3 Move to B7 facing NW 27.2.

**Card 10, Late Clock Reset**, after "O1 Sprint to L8" (search depth 1): best X4 Move to J6 facing E. Pause: 19.5. Best alternatives: X4 Move to J6 facing E 15.0; X4 Move to J6 facing SE 15.0; X4 Move to I4 facing E 15.0; X4 Move to I4 facing SE 15.0; worst X3 Move to M9 facing SW then X4 Move to J6 facing NE 26.0.

## OQ-7: the defence's last token ends the phase

| # | Card | Budget | As built | Phase runs on | Difference | Opening changes |
|---|---|---|---|---|---|---|
| 13 | One Phase Left | 2 min | 18.0 | 18.0 | +0.0 | no |
| 13 | One Phase Left | 10 min | 18.0 | 18.0 | +0.0 | no |
| 7 | Two or Three | 2 min | 26.2 | 26.2 | +0.0 | no |
| 7 | Two or Three | 10 min | 26.2 | 26.2 | +0.0 | no |
| 10 | Late Clock Reset | 2 min | 19.5 | 19.5 | +0.0 | no |
| 10 | Late Clock Reset | 10 min | 19.5 | 19.5 | +0.0 | yes |
| 6 | Need a Three | 2 min | 30.0 | 30.0 | +0.0 | no |
| 6 | Need a Three | 10 min | 30.0 | 30.0 | +0.0 | no |
| 5 | Sideline, Late | 2 min | 27.2 | 27.2 | +0.0 | no |
| 5 | Sideline, Late | 10 min | 27.2 | 27.2 | +0.0 | no |
| 3 | Sideline Out | 2 min | 21.4 | 21.4 | +0.0 | no |
| 3 | Sideline Out | 10 min | 21.4 | 21.4 | +0.0 | no |
| 4 | Deny Everything | 2 min | 10.0 | 10.0 | +0.0 | no |
| 4 | Deny Everything | 10 min | 9.2 | 9.2 | +0.0 | no |
| 1 | Baseline Box | 2 min | 36.0 | 36.0 | +0.0 | no |
| 1 | Baseline Box | 10 min | 36.0 | 36.0 | +0.0 | no |
| 2 | Baseline Stack | 2 min | 16.6 | 16.6 | +0.0 | no |
| 2 | Baseline Stack | 10 min | 16.6 | 16.6 | +0.0 | no |
| 8 | Coach's Call | 2 min | 20.0 | 20.0 | +0.0 | no |
| 8 | Coach's Call | 10 min | 20.0 | 20.0 | +0.0 | yes |
| 9 | Coach's Call, Late | 2 min | 24.8 | 24.8 | +0.0 | no |
| 9 | Coach's Call, Late | 10 min | 24.8 | 24.8 | +0.0 | yes |
| 11 | After a Timeout | 2 min | 22.8 | 22.8 | +0.0 | no |
| 11 | After a Timeout | 10 min | 28.8 | 28.8 | +0.0 | no |
| 12 | Mismatch on the Switch | 2 min | 21.8 | 21.8 | +0.0 | no |
| 12 | Mismatch on the Switch | 10 min | 21.8 | 21.8 | +0.0 | no |
| 14 | Hold for One | 2 min | 22.3 | 22.3 | +0.0 | no |
| 14 | Hold for One | 10 min | 22.3 | 22.3 | +0.0 | no |
| 15 | In the Bonus | 2 min | 29.0 | 29.0 | +0.0 | no |
| 15 | In the Bonus | 10 min | 29.0 | 29.0 | +0.0 | no |
| 16 | Star Locked | 2 min | 24.0 | 24.0 | +0.0 | no |
| 16 | Star Locked | 10 min | 24.0 | 24.0 | +0.0 | no |

**Result:** 0 of 32 comparisons move the value; none do. The defence does not exploit ending the phase by spending its last token.

## Coach's Call: the secret's value

Known target: the defence plays against the target it knows. Guessing: one defensive strategy for all five targets. The secret is worth the difference, measured at the same budget as everything else.

| # | Card | Budget | Known target (best) | Per target | Guessing defence | Secret worth |
|---|---|---|---|---|---|---|
| 8 | Coach's Call | 2 min | 20.0 (O1) | O1 20.0, O2 18.0, O3 18.2, O4 18.0, O5 18.0 | 20.0 (O1) | +0.0 |
| 8 | Coach's Call | 10 min | 20.5 (O3) | O1 20.0, O2 18.0, O3 20.5, O4 20.0, O5 19.1 | 20.5 (O3) | +0.0 |
| 9 | Coach's Call, Late | 2 min | 24.8 (O5) | O1 19.2, O2 20.0, O3 19.2, O4 19.2, O5 24.8 | 24.8 (O5) | +0.0 |
| 9 | Coach's Call, Late | 10 min | 26.0 (O2) | O1 21.0, O2 26.0, O3 21.5, O4 22.1, O5 24.8 | 26.0 (O2) | +0.0 |
| 11 | After a Timeout | 2 min | 22.8 (O2) | O1 17.4, O2 22.8, O3 17.4, O4 17.4, O5 17.4 | 20.4 (O2) | -2.4 |
| 11 | After a Timeout | 10 min | 28.8 (O2) | O1 22.8, O2 28.8, O3 22.8, O4 27.0, O5 22.8 | 28.8 (O2) | +0.0 |

## Limits of this run

- **Depth:** at 10 minutes most cards reach 2 turns (Coach's Call targets reach 4). The two-turn evaluation fills in the rest, so values are "what the offence can force over the next few turns".
- **Seeds change only tie-breaking;** the spread reflects budget, not chance.
- **Fixes are one run each** at the long budget; a fix that lands within 2 points of a verdict threshold is borderline, not a verdict.

## Cards

<div class="file"></div>

### 13. One Phase Left

LATE CLOCK, clock 2. O: Shoot and Protect. X: Lockdown. *Six tokens each, then the clock is gone. Every action has to count.*

**Value 18.0**, look 18.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 15. **Verdict: Wall** (estimated; depth 2; spread 0.0 across 18.0, 18.0, 18.0, 18.0, 18.0, 18.0, 18.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (shoot, clock 2): O3 Shot (three)
2. **Defence** (no reaction, clock 2): X End turn

*Result:* total 18 (Okay), shot value 18, goal missed. O3 three 3 x (12 - 6) contested by X3

**Opening plans within 90% of best** (top 5): O3 Shot (three) (18.0); O3 Move to O8 (18.0); O3 Move to O8 then O3 Shot (three) (18.0); O3 Dribble vs X3 (17.9); O1 Screen, T S (17.9)

<div class="file"></div>

### 7. Two or Three

LATE CLOCK, clock 4. O: Shoot and Protect. X: Bucket Brigade. *Down 2. An Excellent three wins it; an Excellent two ties it.*

**Value 26.2**, look 28.5, P(30+) 88%, P(clock 0) 0%. Plans within 90%: 4. **Verdict: Gift** (estimated; depth 2; spread 0.0 across 26.2, 26.2, 26.2, 26.2, 26.2, 26.2, 26.2).

**Principal line** (best play, following the most likely roll):

1. **Offence** (kick, clock 4): O1 Pass to O2
2. **Defence** (intercept, clock 4): X2 Intercept — Pass O1->O2 vs Intercept X2: pass completes (offence needs 13 or less; 65%)

*Result:* search horizon reached; evaluation 30.0 (look 30.0)

**Opening plans within 90% of best** (top 5): O1 Pass to O2 (26.2); O3 Move to P7 then O1 Pass to O3 (26.2); O1 Move to K10 (24.1); O1 Quick Step to K10 (24.1)

<div class="file"></div>

### 10. Late Clock Reset

LATE CLOCK, clock 4. O: Iron Wall. X: Run and Gun. *The set broke down. Both Screens are spent: O4's is down, O5's is still up. Offence has 4 tokens left, defence 4.*

**Value 19.5**, look 19.5, P(30+) 25%, P(clock 0) 0%. Plans within 90%: 1. **Verdict: Single trick** (unstable; depth 2; spread 0.0 across 19.5, 19.5, 19.5, 19.5, 19.5, 19.5, 19.5).

**Principal line** (best play, following the most likely roll):

1. **Offence** (raw, clock 4): O1 Sprint to L8
2. **Defence** (pause, clock 4): X Pause

*Result:* search horizon reached; evaluation 19.5 (look 19.5)

**Opening plans within 90% of best** (top 5): O1 Sprint to L8 (19.5)

<div class="file"></div>

### 6. Need a Three

LATE CLOCK, clock 6. O: Five Out. X: Iron Wall. *Down 3. Only a three counts, and the defence knows it: nobody helps, everybody stays home.*

**Value 30.0**, look 30.0, P(30+) 100%, P(clock 0) 0%. Plans within 90%: 2. **Verdict: Gift** (estimated; depth 2; spread 0.0 across 30.0, 30.0, 30.0, 30.0, 30.0, 30.0, 30.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (kick, clock 6): O1 Pass to O4
2. **Defence** (pause, clock 6): X Pause

*Result:* search horizon reached; evaluation 30.0 (look 30.0)

**Opening plans within 90% of best** (top 5): O1 Pass to O4 (30.0); O2 Move to C8 then O1 Pass to O2 (27.8)

<div class="file"></div>

### 5. Sideline, Late

INBOUNDS, clock 4. O: High-Low. X: Five Out. *Inbound from the left wing, then 4 seconds: two phases to catch and score.*

**Value 27.2**, look 28.2, P(30+) 80%, P(clock 0) 0%. Plans within 90%: 1. **Verdict: Gift** (estimated; depth 2; spread 0.0 across 27.2, 27.2, 27.2, 27.2, 27.2, 27.2, 27.2).

**Principal line** (best play, following the most likely roll):

1. **Offence** (swing, clock 4): O2 Pass to O3
2. **Defence** (pause, clock 4): X Pause

*Result:* search horizon reached; evaluation 27.2 (look 28.2)

**Opening plans within 90% of best** (top 5): O2 Pass to O3 (27.2)

<div class="file"></div>

### 3. Sideline Out

INBOUNDS, clock 8. O: Ball Movement. X: Shoot and Protect. *Inbound from the right wing. The weak-side defender is two passes away and sags into the lane.*

**Value 21.4**, look 22.8, P(30+) 45%, P(clock 0) 0%. Plans within 90%: 1. **Verdict: Single trick** (estimated; depth 2; spread 0.0 across 21.4, 21.4, 21.4, 21.4, 21.4, 21.4, 21.4).

**Principal line** (best play, following the most likely roll):

1. **Offence** (relocate+kick, clock 8): O5 Move to K4 then O3 Pass to O5
2. **Defence** (pause, clock 8): X Pause

*Result:* search horizon reached; evaluation 21.4 (look 22.8)

**Opening plans within 90% of best** (top 5): O5 Move to K4 then O3 Pass to O5 (21.4)

<div class="file"></div>

### 4. Deny Everything

INBOUNDS, clock 8. O: Pace and Space. X: Lockdown. *Sideline inbound against a defence denying every lane. No pass is free: you must move to get open.*

**Value 9.2**, look 15.8, P(30+) 44%, P(clock 0) 0%. Plans within 90%: 1. **Verdict: Single trick** (estimated; depth 2; spread 0.8 across 9.2, 10.0, 10.0, 10.0, 10.0, 10.0, 9.2).

**Principal line** (best play, following the most likely roll):

1. **Offence** (raw, clock 8): O5 Move to L4
2. **Defence** (closeout+switch, clock 8): X2 Move to Q7 facing NE then X5 Move to L5 facing NE

*Result:* search horizon reached; evaluation 9.2 (look 15.8)

**Opening plans within 90% of best** (top 5): O5 Move to L4 (9.2)

<div class="file"></div>

### 1. Baseline Box

INBOUNDS, clock 8. O: Bucket Brigade. X: Iron Wall. *Inbound from the baseline beside the rim. The defence packs the lane, each player touching their man.*

**Value 36.0**, look 36.0, P(30+) 100%, P(clock 0) 0%. Plans within 90%: 2. **Verdict: Gift** (estimated; depth 2; spread 0.0 across 36.0, 36.0, 36.0, 36.0, 36.0, 36.0, 36.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (relocate+kick, clock 8): O1 Sprint to D9 then O5 Pass to O1
2. **Defence** (pause, clock 8): X Pause

*Result:* search horizon reached; evaluation 36.0 (look 36.0)

**Opening plans within 90% of best** (top 5): O1 Sprint to C2 (36.0); O1 Sprint to D9 then O5 Pass to O1 (36.0)

<div class="file"></div>

### 2. Baseline Stack

INBOUNDS, clock 8. O: Run and Gun. X: Twin Towers. *Inbound from the baseline corner. Four players stacked on the lane line, all defenders on the inside.*

**Value 16.6**, look 19.4, P(30+) 35%, P(clock 0) 0%. Plans within 90%: 4. **Verdict: Puzzle** (estimated; depth 2; spread 0.0 across 16.6, 16.6, 16.6, 16.6, 16.6, 16.6, 16.6).

**Principal line** (best play, following the most likely roll):

1. **Offence** (raw, clock 8): O5 Quick Step to K1
2. **Defence** (steal, clock 8): X2 Steal — Steal foul 5 (X2): no foul (75%); Dribble 14 v Steal 5 (O2 v X2): stolen (55%)

*Result:* search horizon reached; evaluation 12.4 (look 19.4)

**Opening plans within 90% of best** (top 5): O5 Quick Step to K1 (16.6); O1 Sprint to Q5 (16.3); O5 Move to K1 (15.0); O5 Sprint to K1 (15.0)

<div class="file"></div>

### 8. Coach's Call

COACH'S CALL, clock 8. O: Twin Towers. X: Pace and Space. *Before setup, secretly write the player you want to score. Run the play to get them the shot.*

**Value 20.5**, look 20.3, P(30+) 24%, P(clock 0) 0%. Plans within 90%: 0. **Verdict: Single trick** (unstable; depth 4; spread 0.5 across 20.5, 20.0).

Known-target values: O1 20.0, O2 18.0, O3 20.5, O4 20.0, O5 19.1.

**Principal line** (best play, following the most likely roll):

1. **Offence** (kick, clock 8): O1 Pass to O3
2. **Defence** (approach+intercept, clock 8): X3 Quick Step to N9 then X3 Intercept — Pass 14 v Intercept 6 (O1 to O3, X3): pass intercepted (offence needs 8 or less; 60%)
3. **Offence** (dribble, clock 8): O1 Dribble vs X1 — Dribble 17 v Agility 7 (O1 v X1): dribble wins (50%)
4. **Defence** (pause, clock 8): X Pause

*Result:* search horizon reached; evaluation 13.0 (look 18.0)

<div class="file"></div>

### 9. Coach's Call, Late

COACH'S CALL, clock 6. O: Lockdown. X: Ball Movement. *Secret target with 6 seconds left. The ball is with your centre at the elbow.*

**Value 26.0**, look 21.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 6. **Verdict: Puzzle** (unstable; depth 4; spread 1.2 across 26.0, 24.8).

Known-target values: O1 21.0, O2 26.0, O3 21.5, O4 22.1, O5 24.8.

**Principal line** (best play, following the most likely roll):

1. **Offence** (relocate+kick, clock 6): O2 Move to A5 then O5 Pass to O2
2. **Defence** (closeout, clock 6): X1 Move to D8 facing SW then X1 Quick Step to B6
3. **Offence** (drive, clock 6): O2 Quick Step to A6
4. **Defence** (pause, clock 6): X Pause

*Result:* search horizon reached; evaluation 26.0 (look 21.0)

**Opening plans within 90% of best** (top 5): O5 Pass to O2 / O1 Screen, T SE (26.0); O5 Pass to O2 / O4 Screen, T E (26.0); O2 Move to A5 then O5 Pass to O2 / O2 Quick Step to A6 (26.0); O2 Move to A4 then O5 Pass to O2 / O1 Move to E8 then O1 Screen, T NE (26.0); O5 Pass to O3 / O3 Dribble vs X3 (24.0)

<div class="file"></div>

### 11. After a Timeout

COACH'S CALL, clock 8. O: Ball Movement. X: High-Low. *Sideline inbound after a timeout, with a secret target. Draw it up: the defence has to guess.*

**Value 28.8**, look 25.6, P(30+) 60%, P(clock 0) 0%. Plans within 90%: 17. **Verdict: Puzzle** (unstable; depth 4; spread 6.0 across 28.8, 22.8).

Known-target values: O1 22.8, O2 28.8, O3 22.8, O4 27.0, O5 22.8.

**Principal line** (best play, following the most likely roll):

1. **Offence** (relocate, clock 8): O2 Move to B7
2. **Defence** (pause, clock 8): X Pause
3. **Offence** (relocate+kick, clock 8): O2 Quick Step to A6 then O1 Pass to O2
4. **Defence** (intercept, clock 8): X1 Intercept — Pass 20 v Intercept 8 (O1 to O2, X1): pass completes (offence needs 12 or less; 60%)

*Result:* search horizon reached; evaluation 43.0 (look 33.0)

**Opening plans within 90% of best** (top 5): O2 Move to B7 then O1 Pass to O2 / O2 Dribble vs X2 (34.6); O1 Pass to O2 / O2 Shot (three) (29.0); O1 Pass to O2 / O2 Dribble vs X2 (29.0); O1 Pass to O2 / O2 Screen, T E (29.0); O1 Pass to O2 / O3 Screen, T S (29.0)

<div class="file"></div>

### 12. Mismatch on the Switch

CONSTRAINT, clock 6. O: Twin Towers. X: Run and Gun. *A switch left X1, the point guard, on your post scorer, and X5 on the ball. The defence knows too.*

**Value 21.8**, look 21.8, P(30+) 25%, P(clock 0) 0%. Plans within 90%: 4. **Verdict: Puzzle** (estimated; depth 2; spread 0.0 across 21.8, 21.8, 21.8, 21.8, 21.8, 21.8, 21.8).

**Principal line** (best play, following the most likely roll):

1. **Offence** (raw, clock 6): O3 Sprint to K9
2. **Defence** (pause, clock 6): X Pause

*Result:* search horizon reached; evaluation 21.8 (look 21.8)

**Opening plans within 90% of best** (top 5): O3 Sprint to K9 (21.8); O4 Screen, T SW (21.0); O1 Move to K9 (21.0); O1 Sprint to K9 (21.0)

<div class="file"></div>

### 14. Hold for One

CONSTRAINT, clock 8. O: Pace and Space. X: High-Low. *Last shot of the quarter. No shot before the final phase (clock on 2). A turnover ends it at 0.*

**Value 22.3**, look 20.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 2. **Verdict: Puzzle** (estimated; depth 2; spread 0.0 across 22.3, 22.3, 22.3, 22.3, 22.3, 22.3, 22.3).

**Principal line** (best play, following the most likely roll):

1. **Offence** (kick, clock 8): O1 Pass to O3
2. **Defence** (steal, clock 8): X3 Steal — Steal foul roll X3: no foul (55%); Steal: Dribble O3 vs Steal X3: kept (70%)

*Result:* search horizon reached; evaluation 24.0 (look 24.0)

**Opening plans within 90% of best** (top 5): O1 Pass to O3 (22.3); O1 Move to K10 (22.3)

<div class="file"></div>

### 15. In the Bonus

CONSTRAINT, clock 8. O: High-Low. X: Bucket Brigade. *The defence has one steal foul: start on +5, and its next steal foul gives free throws. The goal is still a 30+ look.*

**Value 29.0**, look 24.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 18. **Verdict: Puzzle** (estimated; depth 2; spread 0.0 across 29.0, 29.0, 29.0, 29.0, 29.0, 29.0, 29.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (dribble, clock 8): O1 Dribble vs X1 — Dribble O1 vs X1: dribble wins (50%)
2. **Defence** (pause, clock 8): X Pause

*Result:* search horizon reached; evaluation 29.0 (look 24.0)

**Opening plans within 90% of best** (top 5): O1 Dribble vs X1 (29.0); O2 Screen, T E (29.0); O3 Screen, T W (29.0); O4 Screen, T S (29.0); O5 Screen, T E (29.0)

<div class="file"></div>

### 16. Star Locked

CONSTRAINT, clock 6. O: Bucket Brigade. X: Iron Wall. *Your star picked up the ball and is locked until the phase resets. He can still pass or shoot.*

**Value 24.0**, look 24.0, P(30+) 0%, P(clock 0) 0%. Plans within 90%: 1. **Verdict: Single trick** (estimated; depth 2; spread 0.0 across 24.0, 24.0, 24.0, 24.0, 24.0, 24.0, 24.0).

**Principal line** (best play, following the most likely roll):

1. **Offence** (drive, clock 6): O1 Quick Step to H10
2. **Defence** (deny, clock 6): X2 Move to D8 facing N

*Result:* search horizon reached; evaluation 24.0 (look 24.0)

**Opening plans within 90% of best** (top 5): O1 Quick Step to H10 (24.0)
