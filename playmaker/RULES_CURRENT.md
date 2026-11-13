# Playmaker: the rules as played

Every rule the game plays by, at the table and in the app, in the rulebook's order. Generated from the rules register (`python3 -m playmaker_engine.register --rules`). † marks a rule the rulebook and trackers don't state: ruled and not yet printed, or printed only on the scenario rules sheet; ‡ marks a rule ruled to change, played as written until the change is built. The last sections list them; each ruled one points to its entry in `DECISIONS.md`.

## Aim of the game

- Two players, two possessions: each attacks once and defends once. The higher score wins. The app plays longer matches (see Split by format).

## In the box

- The court board has 17 columns (A to Q) and 14 rows. Squares are named by column and row, like I11. The rim is on I2.
- 8 grey lock tokens mark a player who is locked.

## Setup

- Each side puts its 6 action tokens in its tracker's pool. One token is one action.
- Put the shot clock marker on 12. Each phase is 2 seconds. Scenario cards may start the clock lower.
- The offence places its 5 O pieces anywhere. The ball goes on a player on plain wood beyond the three-point tiles. The defence places its 5 X pieces on empty squares, each arrow pointing any way.
- Each player takes 5 cards, one per position: a prescribed team, or a team from the playing levels (Senior, Youth or Junior; Pro, Semi-pro or Amateur).
- Junior growth (app only): when a junior roster is made, one player on each team is bigger and stronger than most his age and one is still growing; the cards show the ratings they play with. At the table the junior cards play as printed (see Split by format). †

## The shot

- A declared shot worth less than 0 scores 0, as a forced shot does. † (setting: floor_declared_shot)

## Reading the court

- Every shot is worth points × (rating − contest). Points come from the tile the shooter stands on: rim tiles 2 (layup, dunk or post move), mid-range tiles 2 (mid-range or floater), long-two tiles 2 (long two), three-point tiles 3 (three-pointer). Plain wood: no shot.

## Rolling

- Roll the d20. You succeed on equal to or under your rating minus theirs. Shots are never rolled.
- A target of 20 or more always succeeds. A target of 0 or less always fails. A 1 or a 20 has no special meaning. † (setting: natural_rolls)

## Playing a possession

- The offence goes first. Then the sides take turns. On your turn, take 1 or 2 actions.
- Pass, Screen, Dribble, Hesitate and Shot end the offence's turn. Intercept, Challenge, Steal and Pause end the defence's turn. Play them last.
- Each phase, each player has one Move. Each side has 2 Quick Steps (Sprints count). Offence: 2 Passes, 2 Screens, 2 Dribbles, 1 Hesitate, 1 Shot. Defence: 2 Intercepts, 2 Challenges, 2 Steals, 1 Pause.
- Move: up to 3 squares straight, 2 diagonal, or 1 straight and 1 diagonal. Never through another player.
- The straight step and the diagonal step may come in either order. † (setting: move_either_order)
- Two diagonal steps go the same way, in a straight line. † (setting: diag_move_straight)
- Quick Step: straight, up to the card's number of squares (2, 1 or 0). † (setting: qs_up_to)
- Each player has one Quick Step a phase. A Sprint uses it. † (setting: qs_once_per_player)
- Sprint: a Move and a Quick Step in one straight line, as one action, any direction: up to 3 plus the Quick Step straight, or 2 plus the Quick Step diagonal. It uses that player's Move and Quick Step. (setting: sprint_orth_base)
- A player with Quick Step 0 can't Sprint. † (setting: sprint_needs_qs)
- Hesitate (offence) and Pause (defence) are each side's one wait a phase. Neither may come straight after the other side's wait. (setting: wait_chain_block)
- The phase ends when the offence plays its last token (the defence gets one more turn first), when the defence plays its last token (at once), or when a shot is taken. (setting: defence_empty_ends_phase)
- A side with tokens left but no legal action gives up its remaining tokens. † (setting: forfeit_when_stuck)
- Locked: no Move, Sprint, Dribble or arrow turn for the rest of the phase; Quick Step is still allowed. A player is locked by losing or being beaten on a Dribble, missing a Steal, or failing a Challenge. (setting: locked_can_dribble)
- Inbounds (scenario cards): the inbounder sits off the court with the ball and can't move. The offence has 2 phases to complete the pass in, and the clock doesn't run. Once the ball is in, reset to a new phase with the card's clock. Not in after 2 phases: a turnover, −5, and play on with the ball to the player furthest from the rim, clock on the card's number. †
- Before the ball is in, the inbounder may only pass. † (setting: inbounder_pass_only)
- On a failed inbound, if players tie for furthest from the rim, the offence picks. † (setting: inbound_tie)
- Reset: all action tokens back to the pools, lock tokens off, the shot clock down 2. Players stay where they are.
- On a Hold for One card the offence can't shoot before the last phase, and any turnover scores 0. †
- If the clock reaches 0 before a shot, at the table: a turnover, −5, and the ball carrier takes a forced shot from where the pieces stand, contested as normal; plain wood scores 0. The app differs (see Split by format).
- On a forced shot the offence picks the shot type its tile allows. † (setting: forced_shot_choice)

## Screens

- Any player except the ball carrier may Screen. (setting: carrier_can_screen)
- A Screen is the turn's first action, or its second straight after that player's own Move, and it ends the turn. It lasts until the screener moves, a Challenge beats it, or the phase ends. (setting: screen_rule)
- The screener's T marks one square next to him. No defender steps diagonally from the T square or across its corner. (setting: screen_geometry)
- Challenge: only the defender on the T square may Challenge. The offence rolls Screen − Challenge or under: the screen holds and the challenger is locked. Otherwise the screen is removed for everyone. (setting: challenge_who)

## Defender arrows

- Each X piece points one arrow, in one of 8 directions. Turning the arrow uses his Move. A Quick Step can't turn it. After a Sprint it faces the way he ran. (setting: arrow_mode)
- A defender's zone is the squares along his arrow that one movement could reach. It stops at the first player in the way, and shrinks once he has used his Move. The ball carrier may step into the zone of a defender next to him, but not through it, unless he has beaten him on a Dribble. (setting: drive_rule)
- Dribble: take on a defender 1 square away; succeed on Dribble − Agility or under. Win: he is locked, and you may go through his zone. Lose: you are locked, but may still pass or shoot.
- "Next to him" means next to him when the movement starts. † (setting: arrow_line_adjacent_at)
- A Dribble win lets you through his zone for the rest of the phase. † (setting: dribble_win_lasts)
- Steal: from 1 square away, arrow on the ball carrier. No foul, and the carrier keeps the ball on Dribble − Steal or under: the defender is locked. Otherwise the ball is stolen. (setting: steal_lock)
- The foul roll comes first, Foul (Steal) or under: once if the defender is closer to the rim than the ball carrier, twice if level or further, and either roll fouls. The same count applies to a contest's foul roll. (setting: reach_angle_fouls)

## Passes and intercepts

- A pass fixes a line from passer to receiver. Passes cross players. The defence answers with its first action, or the pass lands. (setting: pass_resolution)
- Through you: the line passes through your square's centre. Intercept, whatever your facing. (setting: on_line_tolerance)
- Jump the lane: one straight Move, Quick Step or Sprint along your arrow whose path touches or crosses the line, ending where it meets it. Then Intercept. That is the defence's whole turn. No intercept on any square next to the passer: Steal instead. (setting: intercept_rule)
- The offence rolls Pass − Intercept or under: the pass gets through. Otherwise it is intercepted. A missed Intercept leaves him on the line, his Move used.
- The jump keeps your facing. (setting: lane_jump_keeps_facing)
- Denied: no pass through the square of a defender next to the receiver. (setting: receiver_denial)
- A successful Intercept puts the interceptor back on the square and arrow he had at the start of the defence's turn; his Move stays used. † (setting: intercept_return)
- An inbound pass works like any other pass, and lands after the defence's whole turn. † (setting: inbound_resolves)

## Shooting

- Declare a Shot (the ball carrier, never from plain wood). The defence takes one last turn to react, with a Move or a Steal. (setting: reaction_kinds)
- The reaction may be 0, 1 or 2 actions from the tokens left: Move, Quick Step, Sprint, Steal or Contest. † (setting: reaction_may_decline)
- Contest is an action: the reaction's last, one a phase, by one defender next to the shooter at that moment, using a token. A Steal ends the reaction, so it can't also Contest. No Contest: the contest is 0. † (setting: contest_action)
- On a forced shot at clock 0, one adjacent defender contests, diagonals included: the defence picks who, or no one. None adjacent: the contest is 0. (setting: contest_choice)
- Arrow off the shooter: a foul roll first, Foul (Contest) or under. (setting: contest_geometry)
- Further from the rim than the shooter: contest at −3.
- The −3 never takes a contest below 0. † (setting: floor_contest_zero)

## Scoring

- A successful Intercept or Steal at the table: −5 and the shot clock loses a phase; play on. A stolen shot is cancelled. In the last phase the possession scores 0 (or less: see the turnover floor). The app differs (see Split by format). (setting: turnover_cost)
- Every foul on a Steal is +5 to the offence, and the +5 stays in the score. In the bonus it also gives free throws and the possession ends: at the table the bonus is the second steal foul of the possession; the app counts team fouls across a quarter (see Split by format). A steal foul on a shooter is a shooting foul: free throws only (it counts as a team foul in the app). †
- Free throws from a steal foul score 2 × the ball carrier's free-throw rating. †
- On Two or Three, a fouled three with 30 or more in foul points counts as an Excellent three. †
- A turnover that ends the possession at 0 (the last phase at the table, Hold for One, any turnover in the app) scores 0 or the total banked before it, whichever is lower. † (setting: turnover_floor)
- A foul on a shot (once it is declared, or forced): free throws or the open shot, whichever is higher. The possession ends. (setting: and_one)
- Free throws score 2 × the shooter's free-throw rating, or 3 × on a three.
- Scenario cards: a look of 30 or more (Excellent) beats the card. Coach's Call: if the secret target takes the shot, add the bonus for the look: Poor +0, Okay +2, Good +5, Great +8, Excellent +10. †
- Need a Three: only a three scores; a fouled two's free throws score 0 too. † (setting: three_only_ft_on_twos)
- The Coach's Call bonus uses the look's band (the shot value, or the free throws if fouled), and counts on a forced shot by the target too. † (setting: coach_bonus_on_forced)

## Winning

- After the first possession, swap seats and trackers, flip every card and set up again. After both, the higher score wins. Tied: each player rolls for their final shot, d20 at or under rating − contest. A make beats a miss.
- On Late Clock cards, compare results first (win, then tie, then loss); the shot value breaks ties. †

## Digital only

- **Quarters and team fouls.** Each side's defensive fouls (steal fouls and shooting fouls) count across a running quarter of 18 possessions a side. The count carries across matches between the same two players, or a player and a computer level, and resets when both sides have had 18. The screen shows the count, the bonus line and the possessions left. (settings: quarter_possessions, bonus_from)
- **Match length.** A match is 4, 8 or 12 possessions a side, sides alternating. The higher total wins; a tie goes to overtime (see Split by format).
- **The decision timer.** Each player may set an optional thinking clock.
- **Computer levels.** The computer plays at three levels: Rookie, Starter and All-Star. The levels differ in how deep and how long they look ahead, not in the rules.
- **The trainer.** After a possession the trainer grades a player's decisions against the best options it found, and keeps a rating for each player.

## Split by format

**Control.** At the table: no control rule: a shot or a Contest is worth the same after any movement.  
In the app: your last movement this phase decides your control. After a Quick Step or a Sprint you're rushed: your shot or Contest is 2 lower. A Move puts you back in control.  
Why: ruled for the app (D-153). The table's rules are on hold while the app's game settles (D-146).

**Soft and hard contest.** At the table: one Contest: the defender's contest rating, with a foul roll if his arrow is off the shooter.  
In the app: a defender next to the shooter gives a soft contest with no action: his contest rating less 3. It never fouls. A Contest action is a hard contest: the full rating. From behind the shooter (further from the rim) either is 3 lower again. A hard contest from in front with the arrow on him rolls no foul; from in front with the arrow off him, one foul roll; from the side or behind, two, as a Steal does. Only the defence's best contest counts. A rushed defender's contest, soft or hard, is 2 lower.  
Why: ruled for the app (D-177).

**The steal foul.** At the table: +5 to the offence; the second of the possession also gives free throws and ends it.  
In the app: outside the penalty: a team foul, the defender is locked, play on, no +5. From the 5th team foul of the quarter: +5 and two free throws, and the possession ends.  
Why: fIBA Article 41, ruled for the app (D-179).

**Three seconds.** At the table: no such rule.  
In the app: time is counted in phase ends. An attacker in the key (columns G to K, from the baseline to the free-throw line) when two phases in a row end commits a violation: a turnover. Defenders have no such rule.  
Why: fIBA Article 26, ruled for the app (D-171, D-172).

**Closely guarded.** At the table: no such rule.  
In the app: a ball handler is closely guarded when a defender is next to him with an arrow on him. If he has held the ball since he caught it and is closely guarded when three phases in a row end, it is a violation: a turnover. Moving with the ball or a Dribble starts his dribble, and a dribble is never counted. After that, two whole phases without an action from him and he has picked the ball up: he may only pass or shoot, and the count runs. The count starts again when nobody closely guards him at a phase end.  
Why: fIBA Article 27, ruled for the app (D-173).

**The fouled shot.** At the table: the free throws (2 or 3 times the shooter's free-throw rating), or the open shot if that is higher.  
In the app: the shot still counts as a shot, at its contested rating. Free throws follow: 1 if it went in, 2 or 3 (its points) if it missed, each at the shooter's free-throw rating. The score is what that is worth on average, to the nearest point.  
Why: fIBA Articles 34 and 38, ruled for the app (D-174).

**Turnover cost.** At the table: −5 and the shot clock loses a phase; play on.  
In the app: the possession ends and scores 0.  
Why: a digital match has several possessions a side, so the next possession is the cost.

**Shot-clock expiry.** At the table: a turnover, −5, then a forced shot from where the pieces stand.  
In the app: a turnover: the possession scores 0.  
Why: as in basketball: no shot before the clock runs out is a turnover.

**Steal-foul bonus.** At the table: every steal foul +5; the second of the possession also gives free throws and ends it.  
In the app: every steal foul +5; from the 5th team foul of the quarter it also gives free throws and ends the possession.  
Why: one possession is the whole tabletop game; the app keeps fouls across a quarter.

**Junior growth.** At the table: none: the junior cards play as printed.  
In the app: dealt at random when a junior roster is made; the cards show the ratings, Coach Vision names the two players it changes.  
Why: at the table it needed markers and a term players found unclear; the app can apply it unseen. Approved (D-88).

**Match length.** At the table: 2 possessions, 1 each.  
In the app: 4, 8 or 12 possessions a side.  
Why: an app match can be longer.

**Tied match.** At the table: each player rolls for their final shot.  
In the app: overtime: one more possession a side, repeated until a side leads after equal possessions.  
Why: basketball has no ties. Approved (D-19).

## Ruled, not yet printed

Rules the engine plays that no line of the rulebook or the trackers states. Shaun approved each as the engine plays it (9 Nov 2026); the printed pages don't say them yet.

1. Junior growth (app only): when a junior roster is made, one player on each team is bigger and stronger than most his age and one is still growing; the cards show the ratings they play with. At the table the junior cards play as printed (see Split by format). See D-88.
2. A declared shot worth less than 0 scores 0, as a forced shot does. See D-1. (setting: floor_declared_shot)
3. A target of 20 or more always succeeds. A target of 0 or less always fails. A 1 or a 20 has no special meaning. See D-2. (setting: natural_rolls)
4. The straight step and the diagonal step may come in either order. See D-3. (setting: move_either_order)
5. Two diagonal steps go the same way, in a straight line. See D-4. (setting: diag_move_straight)
6. Quick Step: straight, up to the card's number of squares (2, 1 or 0). See D-5. (setting: qs_up_to)
7. Each player has one Quick Step a phase. A Sprint uses it. See D-6. (setting: qs_once_per_player)
8. A player with Quick Step 0 can't Sprint. See D-7. (setting: sprint_needs_qs)
9. A side with tokens left but no legal action gives up its remaining tokens. See D-8. (setting: forfeit_when_stuck)
10. Before the ball is in, the inbounder may only pass. See D-9. (setting: inbounder_pass_only)
11. On a forced shot the offence picks the shot type its tile allows. See D-10. (setting: forced_shot_choice)
12. "Next to him" means next to him when the movement starts. See D-11. (setting: arrow_line_adjacent_at)
13. A Dribble win lets you through his zone for the rest of the phase. See D-12. (setting: dribble_win_lasts)
14. A successful Intercept puts the interceptor back on the square and arrow he had at the start of the defence's turn; his Move stays used. See D-13. (setting: intercept_return)
15. An inbound pass works like any other pass, and lands after the defence's whole turn. See D-14. (setting: inbound_resolves)
16. The reaction may be 0, 1 or 2 actions from the tokens left: Move, Quick Step, Sprint, Steal or Contest. See D-18. (setting: reaction_may_decline)
17. Contest is an action: the reaction's last, one a phase, by one defender next to the shooter at that moment, using a token. A Steal ends the reaction, so it can't also Contest. No Contest: the contest is 0. See D-18. (setting: contest_action)
18. The −3 never takes a contest below 0. See D-15. (setting: floor_contest_zero)
19. Every foul on a Steal is +5 to the offence, and the +5 stays in the score. In the bonus it also gives free throws and the possession ends: at the table the bonus is the second steal foul of the possession; the app counts team fouls across a quarter (see Split by format). A steal foul on a shooter is a shooting foul: free throws only (it counts as a team foul in the app). See D-89.
20. Free throws from a steal foul score 2 × the ball carrier's free-throw rating. See D-30.
21. On Two or Three, a fouled three with 30 or more in foul points counts as an Excellent three. See D-36.
22. A turnover that ends the possession at 0 (the last phase at the table, Hold for One, any turnover in the app) scores 0 or the total banked before it, whichever is lower. See D-82. (setting: turnover_floor)
23. Need a Three: only a three scores; a fouled two's free throws score 0 too. See D-16. (setting: three_only_ft_on_twos)
24. The Coach's Call bonus uses the look's band (the shot value, or the free throws if fouled), and counts on a forced shot by the target too. See D-17. (setting: coach_bonus_on_forced)

## Ruled, not yet built

Rulings that change the game. Until they are built the game plays as the rest of this page says.

None. Step 6 built Contest as an action (D-18) and overtime in the app (D-19).

## On the scenario rules sheet only

Printed on the scenario rules sheet, not in the rulebook or the trackers:

1. Inbounds (scenario cards): the inbounder sits off the court with the ball and can't move. The offence has 2 phases to complete the pass in, and the clock doesn't run. Once the ball is in, reset to a new phase with the card's clock. Not in after 2 phases: a turnover, −5, and play on with the ball to the player furthest from the rim, clock on the card's number.
2. On a failed inbound, if players tie for furthest from the rim, the offence picks. (setting: inbound_tie)
3. On a Hold for One card the offence can't shoot before the last phase, and any turnover scores 0.
4. Scenario cards: a look of 30 or more (Excellent) beats the card. Coach's Call: if the secret target takes the shot, add the bonus for the look: Poor +0, Okay +2, Good +5, Great +8, Excellent +10.
5. On Late Clock cards, compare results first (win, then tie, then loss); the shot value breaks ties.
