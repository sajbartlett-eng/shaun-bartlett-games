# Regression: first-turn ceilings

`python -m playmaker_engine ceilings` prints this table (about 50 seconds).

**Legacy mode reproduces `scenario_tests.py` exactly**: all 9 first-turn gifts and all 16 reachable
ceilings match (`tests/test_golden_and_regression.py::test_legacy_ceilings_reproduced_exactly` runs the
old script and compares). Legacy mode is built from the engine's own movement shapes with two settings
changed (`move_either_order=False`, `sprint_needs_qs=False`) plus the old script's three simplifications:
defenders ignore O pieces when moving, the ball carrier ignores arrow lines, and the contest is the
highest adjacent contest regardless of arrows or fouls.

The engine columns ask the same question under the real rules: the carrier's one legal movement action,
then the declared shot, then the defence's best single reaction (any legal reaction action, Steal
included) scored with the real contest choice. "No arrows" keeps engine movement but lets every adjacent
defender contest cleanly, which isolates movement differences from arrow and foul differences.
Fractions are expected values from foul or steal rolls.

| # | Scenario | Gift: legacy | no arrows | engine | Top: legacy | no arrows | engine |
|---|---|---|---|---|---|---|---|
| 1 | Baseline Box | n/a | n/a | n/a | 27 | 27 | 36 |
| 2 | Baseline Stack | n/a | n/a | n/a | 22 | 20 | 27 |
| 3 | Sideline Out | n/a | n/a | n/a | 18 | 18 | 18 |
| 4 | Deny Everything | n/a | n/a | n/a | 24 | 24 | 23.2 |
| 5 | Sideline, Late | n/a | n/a | n/a | 28 | 34 | 31.3 |
| 6 | Need a Three | 9 | 9 | 9 | 30 | 30 | 30 |
| 7 | Two or Three | 18 | 18 | 18 | 30 | 30 | 30 |
| 8 | Coach's Call | 18 | 18 | 18 | 28 | 28 | 27.4 |
| 9 | Coach's Call, Late | 20 | 20 | 20 | 21 | 22 | 30 |
| 10 | Late Clock Reset | 8 | 8 | 12.75 | 22 | 20 | 31.2 |
| 11 | After a Timeout | n/a | n/a | n/a | 27 | 27 | 27 |
| 12 | Mismatch on the Switch | 21 | 21 | 21 | 28 | 28 | 27 |
| 13 | One Phase Left | 18 | 18 | 18 | 21 | 22 | 21.2 |
| 14 | Hold for One | n/a | n/a | n/a | 24 | n/a | n/a |
| 15 | In the Bonus | 24 | 24 | 24 | 26 | 30 | 29.2 |
| 16 | Star Locked | 21 | 21 | 21 | 26 | 26 | 26 |

**Headline:** no scenario gives a 30+ look on the first turn under either model. The engine confirms 8
of the 9 legacy gift numbers exactly.

## Each difference, and the rule the old script simplified

Movement (legacy → "no arrows"), checked by re-running with `move_either_order=False`:

- **2 Baseline Stack, 22 → 20.** With diagonal-then-straight Moves (OQ-11) a defender gets a stronger
  contest on the old best look (O1's K7 floater), so the best drops to a 20 floater from L5.
  Straight-first only gives 22 again.
- **5 Sideline, Late, 28 → 34; 9 Coach's Call, Late, 21 → 22; 13 One Phase Left, 21 → 22; 15 In the Bonus,
  26 → 30.** The shooter reaches I2 with a diagonal-then-straight Move (OQ-11). Straight-first only
  reproduces 28, 21, 21 and 26.
- **10 Late Clock Reset, 22 → 20.** O5 is still screening on this card, and a screener can't move. The old
  script moved it to I2 for a 22 post; the engine leaves it at J3 for a 20 layup.
- **14 Hold for One, 24 → n/a.** No shot is legal before the final phase; the old script ignored the card's
  constraint.

Arrows and fouls ("no arrows" → engine):

- **1 Baseline Box 27 → 36, 2 Baseline Stack 20 → 27, 9 Coach's Call, Late 22 → 30, 10 Late Clock Reset
  20 → 31.2 (top) and 8 → 12.75 (gift).** The only defenders who can get adjacent arrive by Quick Step or
  Sprint, so their arrow ends off the shooter. Contesting then risks a foul worth 2 or 3 × the shooter's
  FT rating, which costs more than not contesting. The old script assumed every arriving defender contests
  cleanly.
- **5 Sideline, Late 34 → 31.3, 13 One Phase Left 22 → 21.2, 15 In the Bonus 30 → 29.2, 8 Coach's Call
  28 → 27.4, 4 Deny Everything 24 → 23.2, 12 Mismatch 28 → 27.** The defence does better than a clean
  contest: either it contests with its arrow off and accepts the foul risk because free throws are worth
  less than the look (e.g. 2 × FT 14 = 28 against a 34 post), or it Steals. The old script had neither
  option.
- Unchanged: 3, 6, 7, 11, 16 match the legacy ceiling exactly.
