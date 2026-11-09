# Playmaker: the rules as played

Every rule the game plays by, at the table and in the app, in the rulebook's order. Generated from the rules register (`python3 -m playmaker_engine.register --rules`). † marks a rule the rulebook and trackers don't state; the last section lists them.

## Aim of the game

- Two players, two possessions: each attacks once and defends once. The higher score wins. The app plays longer matches (see Split by format).

## In the box

- The court board has 17 columns (A to Q) and 14 rows. Squares are named by column and row, like I11. The rim is on I2.
- 8 grey lock tokens mark a player who is locked.

## Setup

- Each side puts its 6 action tokens in its tracker's pool. One token is one action.
- Put the shot clock marker on 12. Each phase is 2 seconds. Scenario cards may start the clock lower.
- The offence places its 5 O pieces anywhere. The ball goes on a player on plain wood beyond the three-point tiles. The defence places its 5 X pieces on empty squares, each arrow pointing any way.
- Each player takes 5 cards, one per position: a prescribed team, or a team from the playing levels (Senior, Youth or Junior; Pro, Semi-pro or Amateur; growth tags at Junior).

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
- The offence rolls Pass − Intercept or under: the pass gets through. Otherwise it is picked off. A missed Intercept leaves him on the line, his Move used.
- The jump keeps your facing. (setting: lane_jump_keeps_facing)
- Denied: no pass through the square of a defender next to the receiver. (setting: receiver_denial)
- A successful Intercept puts the interceptor back on the square and arrow he had at the start of the defence's turn; his Move stays used. † (setting: intercept_return)
- An inbound pass works like any other pass, and lands after the defence's whole turn. † (setting: inbound_resolves)

## Shooting

- Declare a Shot (the ball carrier, never from plain wood). The defence takes one last turn to react, with a Move or a Steal. (setting: reaction_kinds)
- The reaction may be 0, 1 or 2 actions, and may also use a Quick Step or a Sprint. † (setting: reaction_may_decline)
- Then one adjacent defender contests, diagonals included: the defence picks who, or no one. None adjacent: the contest is 0. (setting: contest_choice)
- Arrow off the shooter: a foul roll first, Foul (Contest) or under. (setting: contest_geometry)
- Further from the rim than the shooter: contest at −3.
- The −3 never takes a contest below 0. † (setting: floor_contest_zero)

## Scoring

- A successful Intercept or Steal at the table: −5 and the shot clock loses a phase; play on. A stolen shot is cancelled. In the last phase the possession scores 0. The app differs (see Split by format). (setting: turnover_cost)
- A foul on a Steal at the table: the first is +5 and play on; the second gives free throws and the possession ends. The app counts fouls across a quarter (see Split by format).
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
- **Match length.** A match is 4, 8 or 12 possessions a side, sides alternating. The higher total wins; a tie stays a tie.
- **The decision timer.** Each player may set an optional thinking clock.
- **Computer levels.** The computer plays at three levels: Rookie, Starter and All-Star. The levels differ in how deep and how long they look ahead, not in the rules.
- **The trainer.** After a possession the trainer grades a player's decisions against the best options it found, and keeps a rating for each player.

## Split by format

**Turnover cost.** At the table: −5 and the shot clock loses a phase; play on.  
In the app: the possession ends and scores 0.  
Why: a digital match has several possessions a side, so the next possession is the cost.

**Shot-clock expiry.** At the table: a turnover, −5, then a forced shot from where the pieces stand.  
In the app: a turnover: the possession scores 0.  
Why: as in basketball: no shot before the clock runs out is a turnover.

**Steal-foul bonus.** At the table: first steal foul +5 and play on; second, free throws and the possession ends.  
In the app: +5 and play on until the 5th team foul of the quarter; from the 5th, free throws and the possession ends.  
Why: one possession is the whole tabletop game; the app keeps fouls across a quarter.

**Match length.** At the table: 2 possessions, 1 each.  
In the app: 4, 8 or 12 possessions a side.  
Why: an app match can be longer.

**Tied match.** At the table: each player rolls for their final shot.  
In the app: the match stays a tie.  
Why: found in the code, not yet approved: no reason recorded.

## Rules the engine plays that the rulebook doesn't state

Each is something the engine does that no line of the rulebook or the trackers states. Listed, not judged.

1. A declared shot worth less than 0 scores 0, as a forced shot does. Question: What does a declared shot worth less than 0 score? OPEN_QUESTIONS.md row 5. (setting: floor_declared_shot)
2. A target of 20 or more always succeeds. A target of 0 or less always fails. A 1 or a 20 has no special meaning. Question: What do a natural 1 and a natural 20 do, and a target of 20 or more? OPEN_QUESTIONS.md row 4. (setting: natural_rolls)
3. The straight step and the diagonal step may come in either order. Question: Which comes first in a 1 straight + 1 diagonal Move? OPEN_QUESTIONS.md row 11. (setting: move_either_order)
4. Two diagonal steps go the same way, in a straight line. Question: Do the 2 diagonal steps of a Move go the same way? OPEN_QUESTIONS.md row 25. (setting: diag_move_straight)
5. Quick Step: straight, up to the card's number of squares (2, 1 or 0). Question: Is a Quick Step exactly the card's number, or up to it? OPEN_QUESTIONS.md row 14. (setting: qs_up_to)
6. Each player has one Quick Step a phase. A Sprint uses it. Question: How many Quick Steps may one player take in a phase? OPEN_QUESTIONS.md row 52. (setting: qs_once_per_player)
7. A player with Quick Step 0 can't Sprint. Question: Can a player with Quick Step 0 Sprint? OPEN_QUESTIONS.md row 15. (setting: sprint_needs_qs)
8. A side with tokens left but no legal action gives up its remaining tokens. Question: What happens to a side with tokens but no legal action? OPEN_QUESTIONS.md row 21. (setting: forfeit_when_stuck)
9. Before the ball is in, the inbounder may only pass. Question: What may the inbounder do before the ball is in? OPEN_QUESTIONS.md row 19. (setting: inbounder_pass_only)
10. On a forced shot the offence picks the shot type its tile allows. Question: On a forced shot from a tile with two shot types, who picks? OPEN_QUESTIONS.md row 30. (setting: forced_shot_choice)
11. "Next to him" means next to him when the movement starts. Question: Is "next to him" judged before or after the movement? OPEN_QUESTIONS.md row 24. (setting: arrow_line_adjacent_at)
12. A Dribble win lets you through his zone for the rest of the phase. Question: How long does a Dribble win free the carrier from that defender? OPEN_QUESTIONS.md row 18. (setting: dribble_win_lasts)
13. A successful Intercept puts the interceptor back on the square and arrow he had at the start of the defence's turn; his Move stays used. Question: Where does a successful interceptor end up? OPEN_QUESTIONS.md row 71. (setting: intercept_return)
14. An inbound pass works like any other pass, and lands after the defence's whole turn. Question: When does an inbound pass land? OPEN_QUESTIONS.md row 35. (setting: inbound_resolves)
15. The reaction may be 0, 1 or 2 actions, and may also use a Quick Step or a Sprint. Question: How many actions may the reaction take, and which? OPEN_QUESTIONS.md row 6. (setting: reaction_may_decline)
16. The −3 never takes a contest below 0. Question: Can the −3 take a contest below 0? OPEN_QUESTIONS.md row 20. (setting: floor_contest_zero)
17. Need a Three: only a three scores; a fouled two's free throws score 0 too. Question: On Need a Three, do free throws from a fouled two score? OPEN_QUESTIONS.md row 22. (setting: three_only_ft_on_twos)
18. The Coach's Call bonus uses the look's band (the shot value, or the free throws if fouled), and counts on a forced shot by the target too. Question: Does the Coach's Call bonus count on a forced shot, and on which look? OPEN_QUESTIONS.md row 23. (setting: coach_bonus_on_forced)

Printed on the scenario rules sheet, not in the rulebook or the trackers:

1. Inbounds (scenario cards): the inbounder sits off the court with the ball and can't move. The offence has 2 phases to complete the pass in, and the clock doesn't run. Once the ball is in, reset to a new phase with the card's clock. Not in after 2 phases: a turnover, −5, and play on with the ball to the player furthest from the rim, clock on the card's number.
2. On a failed inbound, if players tie for furthest from the rim, the offence picks. (setting: inbound_tie)
3. On a Hold for One card the offence can't shoot before the last phase, and any turnover scores 0.
4. Scenario cards: a look of 30 or more (Excellent) beats the card. Coach's Call: if the secret target takes the shot, add the bonus for the look: Poor +0, Okay +2, Good +5, Great +8, Excellent +10.
5. On Late Clock cards, compare results first (win, then tie, then loss); the shot value breaks ties.
