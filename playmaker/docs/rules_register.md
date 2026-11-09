# Playmaker rules register

Every rule value and mechanism, marked **Shared** (both formats), **Digital only**, **Tabletop only** or **Split by format** (deliberately different, with the reason). Written by `python3 -m playmaker_engine.register`; `tests/test_step3n.py` asserts every Shared entry has identical values in both formats, and any change to a shared value must be tested under both formats.

| Rule | Status | Value (tabletop) | Value (digital) | Notes |
|---|---|---|---|---|
| digital | Split by format | False | True | The match format switch. The two formats themselves. |
| Turnover cost | Split by format | minus5_lose_phase | minus5_lose_phase | A successful Intercept or Steal (and a steal of a declared shot). Tabletop: -5 and the shot clock loses a phase, play on (the setting). Digital, whatever the setting: the possession ends and scores 0, because a digital match is several possessions a side and the next possession is the cost. |
| Shot-clock expiry | Split by format |  |  | The clock reaches 0. Tabletop: -5 and a forced shot. Digital: a turnover, the possession scores 0 (as in basketball). |
| Match length | Split by format |  |  | Possessions a side. Tabletop: one possession each. Digital: 2 to 8 a side (per_side), sides alternating. |
| Steal-foul bonus | Split by format |  |  | When a steal foul gives free throws. Tabletop: the first steal foul of the possession is +5 and play on, the second gives free throws (one possession is the whole game). Digital (step 3n F3): team fouls run across a quarter; from the 5th a steal foul gives free throws and ends the possession. |
| quarter_possessions | Digital only | 18 | 18 | Possessions a side in a quarter (18). Team fouls across matches need a running quarter; the table plays one possession. |
| bonus_from | Digital only | 5 | 5 | The team foul that starts the bonus (5th). As above. |
| Team fouls carried across matches | Digital only |  |  | Stored with the pairing record. The table has no record between games. |
| Decision timer | Digital only |  |  | Optional per-player thinking clock (step 3c). An app feature; at the table players agree their own pace. |
| Computer opponents and the trainer | Digital only |  |  | Levels, grading, ratings. App features. |
| Board 17 x 14, rim I2 | Shared | (17, 14, (8, 2)) | (17, 14, (8, 2)) | The court. |
| Tokens per phase (6 a side) | Shared | (6,) | (6,) |  |
| Phase length (2 seconds), start clock 12 | Shared | (2, 12) | (2, 12) |  |
| d20 rolls | Shared | (20,) | (20,) | Every roll: d20 at or under the target. |
| Far-contest -3 | Shared | (3,) | (3,) | Contester further from the rim than the shooter. |
| Turnover points (-5) | Shared | (-5,) | (-5,) | The value of a turnover where one is scored. The number is shared; when it applies is the turnover-cost split above. |
| Steal foul +5 | Shared | (5,) | (5,) | A steal foul before the bonus. |
| Free-throw multipliers (x2, x3) | Shared | (2, 3) | (2, 3) |  |
| Two actions a turn | Shared | (2,) | (2,) |  |
| Move shape (3 straight, 2 diagonal) | Shared | (3, 2) | (3, 2) |  |
| Inbound phases (2) | Shared | (2,) | (2,) |  |
| Per-phase limits | Shared | ({'O': {'qs': 2, 'pass': 2, 'screen': 2, 'dribble': 2, 'hesi | ({'O': {'qs': 2, 'pass': 2, 'screen': 2, 'dribble': 2, 'hesi | Quick Steps, passes, screens, dribbles, waits, shots; intercepts, challenges, steals. |
| Turn-ending actions | Shared | (('challenge', 'dribble', 'hesitate', 'intercept', 'pass', ' | (('challenge', 'dribble', 'hesitate', 'intercept', 'pass', ' |  |
| Zones and shot types | Shared | ({'K': ('layup', 'dunk', 'post'), 'M': ('mid', 'floater'), ' | ({'K': ('layup', 'dunk', 'post'), 'M': ('mid', 'floater'), ' |  |
| Look bands and Coach's Call bonus | Shared | ([('Excellent', 30), ('Great', 25), ('Good', 20), ('Okay', 1 | ([('Excellent', 30), ('Great', 25), ('Good', 20), ('Okay', 1 |  |
| Playing levels (ages, standards, growth tags) | Shared |  |  | Step 3l: the ratings by age and standard, junior growth tags. Ratings carry age; both formats use the same cards. |
| turnover_play_on | Shared | play_on | play_on |  |
| pass_resolution | Shared | defence_turn | defence_turn |  |
| sprint_orth_base | Shared | 3 | 3 |  |
| sprint_diag_base | Shared | 2 | 2 |  |
| natural_rolls | Shared | False | False |  |
| floor_declared_shot | Shared | True | True |  |
| reaction_kinds | Shared | ('move', 'qs', 'sprint', 'steal') | ('move', 'qs', 'sprint', 'steal') |  |
| reaction_may_decline | Shared | True | True |  |
| defence_empty_ends_phase | Shared | True | True |  |
| wait_chain_block | Shared | True | True |  |
| screen_geometry | Shared | from_t_or_corner | from_t_or_corner |  |
| screen_rule | Shared | hold_until_move | hold_until_move |  |
| arrow_line_strict | Shared | True | True |  |
| drive_rule | Shared | zone | zone |  |
| intercept_return | Shared | True | True |  |
| intercept_rule | Shared | move_then_intercept | move_then_intercept |  |
| move_either_order | Shared | True | True |  |
| contest_choice | Shared | player | player |  |
| on_line_tolerance | Shared | 0 | 0 |  |
| lane_jump_keeps_facing | Shared | True | True |  |
| receiver_denial | Shared | True | True |  |
| receiver_denial_tol | Shared | 0.5 | 0.5 |  |
| qs_up_to | Shared | True | True |  |
| sprint_needs_qs | Shared | True | True |  |
| qs_once_per_player | Shared | True | True |  |
| arrow_mode | Shared | single | single |  |
| contest_geometry | Shared | current | current |  |
| carrier_can_screen | Shared | False | False |  |
| late_closeout | Shared | False | False |  |
| challenge_who | Shared | on_t | on_t |  |
| locked_can_dribble | Shared | False | False |  |
| dribble_win_lasts | Shared | phase | phase |  |
| inbounder_pass_only | Shared | True | True |  |
| floor_contest_zero | Shared | True | True |  |
| forfeit_when_stuck | Shared | True | True |  |
| three_only_ft_on_twos | Shared | False | False |  |
| coach_bonus_on_forced | Shared | True | True |  |
| arrow_line_adjacent_at | Shared | start | start |  |
| diag_move_straight | Shared | True | True |  |
| inbound_tie | Shared | offence | offence |  |
| forced_shot_choice | Shared | player | player |  |
| inbound_resolves | Shared | after_defence_turn | after_defence_turn |  |
| and_one | Shared | True | True |  |
| steal_lock | Shared | True | True |  |
| reach_angle_fouls | Shared | True | True |  |

## Splits for the designer

Where the best value differs between formats (a designer decision, not a bug):

- Turnover cost and shot-clock expiry: the engine values a risky pass or a reach differently by format, so a digital-tuned habit (gambling for a steal late in a possession) is wrong at the table, where play goes on at -5. The trainer grades each game under its own format.
- The steal-foul bonus: within the possession at the table, across a quarter in digital. A defence two fouls from the bonus behaves differently in each.
- The coarse phase table (engine data, not a rule) is solved from digital self-play; tabletop possessions play on after a turnover, so their late-phase values differ.

## Tokens and markers

| Mechanism | Token | Printed | Check |
|---|---|---|---|
| Locks (failed Challenge, lost Dribble, beaten-by-Dribble defender, failed Steal: F1) | grey lock tokens | printed: 4 lock tokens (rulebook p1) | see the F5 worst case: up to 2 Dribbles, 2 Challenges and 2 Steals a phase can lock up to 6 pieces in one phase |
| Screens (hold until the screener moves) | the O piece flipped to its T side | printed: the pieces have a T side | covered |
| A player's Move used this phase | Move token | printed: the action token pool | covered |
| A player's Quick Step used this phase (one each, OQ-52) | none printed | not on the component list | needs a marker or a note: flag for the designer |
| Dribble wins this phase (the carrier is free of that defender's zone) | the beaten defender's lock token | printed | covered by the lock token on the beaten defender |
| Growth tags at junior (Early, On time, Late) | one tag per card | the levels sheet lists them; no printed tag markers | needs 10 tag markers (5 a team) or written on the team sheet: flag for the designer |
| Steal fouls this possession (tabletop bonus) | none needed | one possession: players count 0, 1, 2 | covered |
