# Playmaker rules register

Every rule value and mechanism, marked **Shared** (both formats), **Digital only**, **Tabletop only** or **Split by format** (deliberately different, with the reason). Written by `python3 -m playmaker_engine.register`; `tests/test_step3n.py` asserts every Shared entry has identical values in both formats, and any change to a shared value must be tested under both formats. The value columns give each rule's value in words; the plain rules are in `RULES_CURRENT.md` (`python3 -m playmaker_engine.register --rules`).

| Rule | Status | Value (tabletop) | Value (digital) | Notes |
|---|---|---|---|---|
| digital | Split by format | tabletop | digital | The match format switch. The two formats themselves. |
| Turnover cost | Split by format | −5, the shot clock loses a phase, play on | the possession ends and scores 0 | A successful Intercept or Steal (and a steal of a declared shot). Tabletop: -5 and the shot clock loses a phase, play on (the setting). Digital, whatever the setting: the possession ends and scores 0, because a digital match is several possessions a side and the next possession is the cost. |
| Shot-clock expiry | Split by format | turnover, −5, then a forced shot | turnover, the possession scores 0 | The clock reaches 0. Tabletop: -5 and a forced shot. Digital: a turnover, the possession scores 0 (as in basketball). |
| Match length | Split by format | 2 possessions, 1 each | 4, 8 or 12 possessions a side, alternating | Possessions a side. Tabletop: one possession each. Digital: 4, 8 or 12 a side (per_side), sides alternating. |
| Tied match | Split by format, approved | roll for the final shot | overtime, one more possession a side | What settles a tied match. Tabletop: each player rolls for their final shot. Digital: overtime, one more possession a side until a side leads after equal possessions (DECISIONS.md D-19, built in step 6); team fouls carry on as in the quarter. |
| Steal-foul bonus | Split by format | +5 every time; the 2nd also free throws, over | no +5; from the 5th team foul two free throws, over | When a steal foul also gives free throws. Tabletop: every steal foul is +5 (D-89), and the second steal foul of the possession also gives free throws and ends it (one possession is the whole game). Digital (step 3n F3; D-179, D-181): no foul gives +5; team fouls run across a quarter, and from the 5th a steal foul gives two free throws and ends the possession. A steal foul on a shooter is a shooting foul in both formats: free throws only (a team foul in the app). |
| Junior growth | Split by format, approved | none, the cards as printed | dealt at random, shown in the ratings | Growth at Junior (D-88). Tabletop: none, the junior cards play as printed. Digital: dealt at random when a junior roster is made, shown only in the ratings and in a Coach Vision line. At the table it needed markers and a term players found unclear; the app can apply it unseen. |
| quarter_possessions | Digital only | not used | 18 possessions a side | Possessions a side in a quarter (18). Team fouls across matches need a running quarter; the table plays one possession. |
| bonus_from | Digital only | not used | the 5th team foul | The team foul that starts the bonus (5th). As above. |
| Team fouls carried across matches | Digital only | not used | kept for the same two players, or a player and a computer level | Stored with the pairing record. The table has no record between games. |
| Decision timer | Digital only | none | optional thinking clock for each player | Optional per-player thinking clock (step 3c). An app feature; at the table players agree their own pace. |
| Computer opponents and the trainer | Digital only | none | Rookie, Starter and All-Star; the trainer grades decisions | Levels, grading, ratings. App features. |
| Board 17 x 14, rim I2 | Shared | 17 columns by 14 rows, rim on I2 | 17 columns by 14 rows, rim on I2 | The court. |
| Tokens per phase (6 a side) | Shared | 6 action tokens a side | 6 action tokens a side |  |
| Phase length (2 seconds), start clock 12 | Shared | shot clock 12, phases of 2 seconds | shot clock 12, phases of 2 seconds |  |
| d20 rolls | Shared | d20, succeed at or under the target | d20, succeed at or under the target | Every roll: d20 at or under the target. |
| Far-contest -3 | Shared | −3 | −3 | Contester further from the rim than the shooter. |
| Turnover points (-5) | Shared | −5 | −5 (where a turnover is scored) | The value of a turnover where one is scored. The number is shared; when it applies is the turnover-cost split above. |
| Steal foul +5 | Tabletop only | +5 | none (D-181) | Every steal foul at the table (D-89). In the app no foul gives +5 (D-181). |
| Steal-foul free throws | Shared | the ball carrier's | the ball carrier's | Whose rating a steal foul's free throws use (D-30). |
| Fouled three on Two or Three | Shared | counts as an Excellent three | counts as an Excellent three | A fouled three on the Two or Three card (D-36). |
| Free-throw multipliers (x2, x3) | Shared | 2 ×, or 3 × on a three | 2 ×, or 3 × on a three |  |
| Two actions a turn | Shared | 1 or 2 actions a turn | 1 or 2 actions a turn |  |
| Move shape (3 straight, 2 diagonal) | Shared | 3 straight, 2 diagonal, or 1 + 1 | 3 straight, 2 diagonal, or 1 + 1 |  |
| Inbound phases (2) | Shared | 2 phases to inbound | 2 phases to inbound |  |
| Per-phase limits | Shared | as printed on the trackers | as printed on the trackers | Quick Steps, passes, screens, dribbles, waits, shots; intercepts, challenges, steals, the Contest (D-18). |
| Turn-ending actions | Shared | Pass, Screen, Dribble, Hesitate, Shot; Intercept, Challenge, Steal, Pause | Pass, Screen, Dribble, Hesitate, Shot; Intercept, Challenge, Steal, Pause |  |
| Zones and shot types | Shared | rim, mid-range and long two score 2, threes 3 | rim, mid-range and long two score 2, threes 3 |  |
| Look bands and Coach's Call bonus | Shared | Excellent 30+ | Excellent 30+ |  |
| Playing levels (ages, standards) | Shared | same cards and levels | same cards and levels | Step 3l: the ratings by age and standard. Ratings carry age; both formats use the same cards (junior growth: see Junior growth). |
| Lock tokens (8) | Shared | 8 lock tokens | shown on screen | Grey tokens that mark a locked player. |
| Setup placement | Shared | offence places first, then defence | offence places first, then defence | Where the pieces start. |
| Phase reset | Shared | tokens back, locks off, clock down 2 | tokens back, locks off, clock down 2 | What the reset does between phases. |
| Dribble | Shared | Dribble − Agility | Dribble − Agility | Taking on a defender. |
| Intercept roll | Shared | Pass − Intercept | Pass − Intercept | The roll and a missed Intercept. |
| Hold for One cards | Shared | no shot before the last phase | no shot before the last phase | Scenario cards that hold for the last shot. |
| Late Clock results | Shared | result first, then shot value | result first, then shot value | How Late Clock cards are compared. |
| Tie-break roll | Tabletop only | roll for the final shot | see Tied match | A tied two-possession game. The app has no tie-break: see Tied match. |
| control | Split by format | none (the table's rules are on hold, D-146) | a rushed shot or Contest is 2 lower (D-153); no extra foul roll (D-154) | A shot or a Contest after a Quick Step or a Sprint. The app plays the control rule at size 2 (D-153, D-154). The table's rules are on hold (D-146). |
| three_seconds | Split by format | none | in the key when two phases in a row end: a turnover (D-172) | An attacker who stays in the key. The app plays three seconds (D-172). The table has no such rule. |
| closely_guarded | Split by format | none | holding the ball closely guarded when three phases in a row end: a turnover (D-173) | A ball handler who holds the ball with a defender on him. The app plays the closely guarded rule (D-173). The table has no such rule. |
| soft_contest | Split by format | none: a shot is contested only by a Contest | next to the shooter is a soft contest, 3 lower, no action, no foul; a Contest action is a hard contest (D-177) | A defender next to the shooter, and the Contest action. The app plays the soft and the hard contest (D-177). The table keeps one Contest. |
| fiba_steal_foul | Split by format | +5 to the offence on every steal foul | no +5: a team foul and the defender locked; from the 5th team foul two free throws (D-179, D-181) | What a steal foul gives. In the app no foul gives +5: a steal foul is a team foul, and from the 5th two free throws (D-179, D-181). The table keeps its +5. |
| off_balance | Split by format | none | rushed (after a Quick Step or Sprint, or while locked): 2 off every rating he rolls, not fouls, until he Moves (D-185) | What being rushed, or locked, costs on every roll. The app plays off balance (D-185): a rushed or locked player is 2 worse on every roll he makes, fouls aside. |
| fiba_fouled_shot | Split by format | the free throws, or the open shot if that is higher | the contested shot plus the free throws that follow, on average (D-174) | What a fouled shot scores. The app scores a fouled shot as the contested shot plus the free throws that follow (D-174). |
| turnover_play_on | Shared | not in play (kept so old logs replay) | not in play (kept so old logs replay) |  |
| pass_resolution | Shared | the defence answers first | the defence answers first |  |
| sprint_orth_base | Shared | 3 + Quick Step straight | 3 + Quick Step straight |  |
| sprint_diag_base | Shared | 2 + Quick Step diagonal | 2 + Quick Step diagonal |  |
| natural_rolls | Shared | no special 1 or 20 | no special 1 or 20 |  |
| floor_declared_shot | Shared | below 0 scores 0 | below 0 scores 0 |  |
| reaction_kinds | Shared | Move, Quick Step, Sprint or Steal | Move, Quick Step, Sprint or Steal |  |
| reaction_may_decline | Shared | 0, 1 or 2 actions | 0, 1 or 2 actions |  |
| defence_empty_ends_phase | Shared | defence's last token ends the phase at once | defence's last token ends the phase at once |  |
| wait_chain_block | Shared | no wait straight after the other side's | no wait straight after the other side's |  |
| screen_geometry | Shared | no diagonal from or across the T | no diagonal from or across the T |  |
| screen_rule | Shared | holds until the screener moves | holds until the screener moves |  |
| arrow_line_strict | Shared | not in play (kept so old logs replay) | not in play (kept so old logs replay) |  |
| drive_rule | Shared | into the zone, not through | into the zone, not through |  |
| intercept_return | Shared | back where he started the turn | back where he started the turn |  |
| intercept_rule | Shared | one straight movement, then Intercept | one straight movement, then Intercept |  |
| move_either_order | Shared | either order | either order |  |
| contest_choice | Shared | the defence picks | the defence picks |  |
| on_line_tolerance | Shared | through the square's centre | through the square's centre |  |
| lane_jump_keeps_facing | Shared | keeps the facing | keeps the facing |  |
| receiver_denial | Shared | no pass through a defender next to the receiver | no pass through a defender next to the receiver |  |
| receiver_denial_tol | Shared | through his square | through his square |  |
| qs_up_to | Shared | up to the card value | up to the card value |  |
| sprint_needs_qs | Shared | no Sprint at Quick Step 0 | no Sprint at Quick Step 0 |  |
| qs_once_per_player | Shared | 1 per player a phase | 1 per player a phase |  |
| arrow_mode | Shared | one arrow | one arrow |  |
| contest_geometry | Shared | any adjacent defender; arrow off means a foul roll | any adjacent defender; arrow off means a foul roll |  |
| carrier_can_screen | Shared | not the ball carrier | not the ball carrier |  |
| late_closeout | Shared | off (a rule test, not adopted) | off (a rule test, not adopted) |  |
| challenge_who | Shared | only from the T square | only from the T square |  |
| locked_can_dribble | Shared | a locked carrier can't Dribble | a locked carrier can't Dribble |  |
| dribble_win_lasts | Shared | rest of the phase | rest of the phase |  |
| inbounder_pass_only | Shared | pass only | pass only |  |
| floor_contest_zero | Shared | never below 0 | never below 0 |  |
| forfeit_when_stuck | Shared | gives up its tokens | gives up its tokens |  |
| three_only_ft_on_twos | Shared | score 0 | score 0 |  |
| coach_bonus_on_forced | Shared | counts, forced shots too | counts, forced shots too |  |
| arrow_line_adjacent_at | Shared | at the start of the movement | at the start of the movement |  |
| diag_move_straight | Shared | same way | same way |  |
| inbound_tie | Shared | offence picks | offence picks |  |
| forced_shot_choice | Shared | offence picks the type | offence picks the type |  |
| inbound_resolves | Shared | after the defence's turn | after the defence's turn |  |
| and_one | Shared | free throws or the open shot if higher | free throws or the open shot if higher |  |
| steal_lock | Shared | a Steal that misses without a foul locks the defender | a Steal that misses without a foul locks the defender |  |
| reach_angle_fouls | Shared | 1 roll from closer, 2 from level or behind | 1 roll from closer, 2 from level or behind |  |
| contest_action | Shared | an action, the last of the reaction | an action, the last of the reaction |  |
| turnover_floor | Shared | 0 or the banked total if lower | 0 or the banked total if lower |  |
| zone | Shared | off (a rule test for the app, D-167; not adopted) | off (a rule test for the app, D-167; not adopted) |  |
| steal_foul_always_plus5 | Shared | every steal foul +5 | every steal foul +5 |  |

## Splits for the designer

Where the best value differs between formats (a designer decision, not a bug):

- Turnover cost and shot-clock expiry: the engine values a risky pass or a reach differently by format, so a digital-tuned habit (gambling for a steal late in a possession) is wrong at the table, where play goes on at -5. The trainer grades each game under its own format.
- The steal-foul bonus: within the possession at the table, across a quarter in digital. A defence two fouls from the bonus behaves differently in each.
- The coarse phase table (engine data, not a rule) is solved from digital self-play; tabletop possessions play on after a turnover, so their late-phase values differ.
- A tied match: the table rolls for the final shots, the app plays overtime. Approved (DECISIONS.md D-19).
- Junior growth: none at the table, applied unseen in the app. Approved (DECISIONS.md D-88).

## Tokens and markers

| Mechanism | Token | Printed | Check |
|---|---|---|---|
| Locks (failed Challenge, lost Dribble, beaten-by-Dribble defender, failed Steal: F1) | grey lock tokens | printed: 8 lock tokens (rulebook page 1, token sheet) | covered: the worst case in one phase is 6 (2 Dribbles, 2 Challenges and 2 Steals) |
| Screens (hold until the screener moves) | the O piece flipped to its T side | printed: the pieces have a T side | covered |
| A player's Move used this phase | Move token | printed: the action token pool | covered |
| A player's Quick Step used this phase (one each, OQ-52) | the action token in that player's Quick Step slot | printed: each player has a Quick Step slot on the tracker | covered |
| Dribble wins this phase (the carrier is free of that defender's zone) | the beaten defender's lock token | printed | covered by the lock token on the beaten defender |
| Growth at junior | none: no growth at the table (D-88) | the levels sheet changes (by Shaun) | covered |
| Steal fouls this possession (tabletop bonus) | none needed | one possession: players count 0, 1, 2 | covered |
