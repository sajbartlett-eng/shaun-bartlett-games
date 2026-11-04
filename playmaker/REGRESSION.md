# Regression: first-turn ceilings

`python -m playmaker_engine ceilings` prints this table (about 100 seconds on 4 cores).

The question for each card is the best look the offence can get in one turn: one movement action
(or none), then a declared shot, then the defence's reaction. "Gift" asks it for the ball carrier.
"Top" asks it for any offence player as if they had the ball. Top is optimistic, because in play the ball
has to get there first. Values are expected looks: shot value, or the foul's points. Fractions come from
foul or steal rolls.

## The columns

- **Legacy:** the old `scenario_tests.py`, reproduced exactly. All 9 gifts and all 16 tops match
  (`test_legacy_ceilings_reproduced_exactly` runs the old script and compares).
- **No arrows:** engine movement rules, but every adjacent defender contests cleanly. This isolates
  movement differences from arrow and foul differences.
- **1 action:** full engine rules, with the defence reacting with a single action. This was the only
  engine column in the first report.
- **2 actions:** full engine rules, with up to two reaction actions by one defender, e.g. a Move that
  sets the arrow, then a Quick Step in. This is the real reaction (OQ-6). It is still a ceiling, because
  pairs of actions by two different defenders aren't searched. Those could only lower it further.

All columns use the current rulings: the and-one rule, both floors at 0, Challenge only from the
T square, and no Dribble while locked.

| # | Scenario | Gift: legacy | no arrows | 1 action | **2 actions** | Top: legacy | no arrows | 1 action | **2 actions** |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Baseline Box | n/a | n/a | n/a | n/a | 27 | 27 | 36 | **22** |
| 2 | Baseline Stack | n/a | n/a | n/a | n/a | 22 | 20 | 27 | **18.7** |
| 3 | Sideline Out | n/a | n/a | n/a | n/a | 18 | 18 | 18 | **16** |
| 4 | Deny Everything | n/a | n/a | n/a | n/a | 24 | 24 | 24 | **18** |
| 5 | Sideline, Late | n/a | n/a | n/a | n/a | 28 | 34 | 34 | **27.2** |
| 6 | Need a Three | 9 | 9 | 9 | **9** | 30 | 30 | 30 | **30** |
| 7 | Two or Three | 18 | 18 | 18 | **18** | 30 | 30 | 30 | **30** |
| 8 | Coach's Call | 18 | 18 | 18 | **18** | 28 | 28 | 28 | **22.3** |
| 9 | Coach's Call, Late | 20 | 20 | 20 | **19.2** | 21 | 22 | 30 | **21** |
| 10 | Late Clock Reset | 8 | 8 | 12.75 | **3** | 22 | 20 | 31.2 | **17.2** |
| 11 | After a Timeout | n/a | n/a | n/a | n/a | 27 | 27 | 27 | **27** |
| 12 | Mismatch on the Switch | 21 | 21 | 21 | **18.8** | 28 | 28 | 28 | **20** |
| 13 | One Phase Left | 18 | 18 | 18 | **18** | 21 | 22 | 22 | **21** |
| 14 | Hold for One | n/a | n/a | n/a | n/a | 24 | n/a | n/a | n/a |
| 15 | In the Bonus | 24 | 24 | 24 | **24** | 26 | 30 | 30 | **24.7** |
| 16 | Star Locked | 21 | 21 | 21 | **21** | 26 | 26 | 26 | **22.8** |

## What changed, and why

**The jumps in the first report came from the one-action column, not from the rules.** Baseline Box
(36), Late Clock Reset (31.2 and 12.75) and Coach's Call, Late (30) looked inflated because a defender
who could only Quick Step or Sprint in arrived side-on. With the real two-action reaction, the defender
Moves with its arrow set toward the shooter, then Quick Steps adjacent and contests cleanly, so there is
no foul roll. Every one of those cards drops below the legacy number: 22, 17.2 and 3, and 21.

**The and-one rule removed the "foul the shooter" cards.** In the first report, Sideline, Late (31.3),
In the Bonus (29.2), One Phase Left (21.2), Coach's Call (27.4), Deny Everything (23.2) and Mismatch
(27) came out below the clean-contest value because the defence did better by fouling. Under the
and-one a foul is never worth less than the open look. With one action those cards now sit at the
clean-contest value; with two they fall further.

**What still reaches 30:** only the optimistic "top" on Need a Three and Two or Three. That's a corner
shooter (O2 at A7, or O3) whom no defender can reach in one turn. The ball has to be passed there first,
which gives the defence a turn, so no card gives a 30+ look on the first turn.

## Movement differences (legacy → no arrows)

Checked by re-running with `move_either_order=False`:

- **2 Baseline Stack, 22 → 20.** With diagonal-then-straight Moves (OQ-11) a defender gets a stronger
  contest on the old best look (O1's K7 floater), so the best drops to a 20 floater from L5.
- **5 Sideline, Late 28 → 34, 9 Coach's Call, Late 21 → 22, 13 One Phase Left 21 → 22, 15 In the
  Bonus 26 → 30.** The shooter reaches I2 with a diagonal-then-straight Move (OQ-11). Straight-first
  only reproduces 28, 21, 21 and 26.
- **10 Late Clock Reset, 22 → 20.** O5 is still screening on this card, and a screener can't move. The old
  script moved it to I2 for a 22 post; the engine leaves it at J3 for a 20 layup.
- **14 Hold for One, 24 → n/a.** No shot is legal before the final phase; the old script ignored the
  card's constraint.

## Closeout matchups (pair by pair)

`python -m playmaker_engine matchups` (and `test_matchup_check_every_pairing`) checks all 39,375
pairings: 75 offence cards × 75 defence cards × 7 shot types, with the defender adjacent and nearer the
rim, using the engine's own contest code.

- **A foul is worth less to the offence than the open look: 0 pairings** under the and-one. Without it,
  10,725 pairings let the defence gain by fouling.
- **A clean closeout (arrow on, from a Move) is worse than no contest: 0 pairings.**
- **A side-on closeout (arrow off, foul roll first) pays in 28,376 pairings (72.1%).** Of the 10,999
  where it doesn't, 9,493 (86%) are open looks under 30, and 1,400 more are Excellent threes.
