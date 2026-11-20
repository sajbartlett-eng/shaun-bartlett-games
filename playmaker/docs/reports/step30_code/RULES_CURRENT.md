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
- The screener's T marks one square next to him. No defender steps diagonally from the T square or across its corner. A defender standing on the T square loses his arrow that points diagonally too: it walls no drive and jumps no passing lane until he leaves the T, wins a Challenge, the screener moves or the phase ends. His other arrow and his contest are unchanged (D-217). (setting: screen_geometry)
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

- Declare a Shot (the ball carrier, never from plain wood). The defence replies with one last turn of 2 actions, shared by the whole team: Move, Quick Step, Sprint, Steal or the Contest. (setting: reaction_kinds)
- The reaction may be 0, 1 or 2 actions from the tokens left: Move, Quick Step, Sprint, Steal or Contest. † (setting: reaction_may_decline)
- Contest is an action, for every shot: one of the reply's 2 actions and its last, one a phase, by one defender next to the shooter at that moment, using a token. Nothing is automatic: no Contest, no contest, and the shot is open. So the most the defence can do is one movement and the Contest, as the offence gets one movement and the shot (D-261). A Steal ends the reply, so it can't also Contest. † (setting: contest_action)
- On a forced shot at clock 0, one adjacent defender contests, diagonals included: the defence picks who, or no one. None adjacent: the contest is 0. (setting: contest_choice)
- Arrow off the shooter: a foul roll first, Foul (Contest) or under. (setting: contest_geometry)
- Further from the rim than the shooter: contest at −3.
- The −3 never takes a contest below 0. † (setting: floor_contest_zero)

## Scoring

- A successful Intercept or Steal at the table: −5 and the shot clock loses a phase; play on. A stolen shot is cancelled. In the last phase the possession scores 0 (or less: see the turnover floor). The app differs (see Split by format). (setting: turnover_cost)
- At the table every foul on a Steal is +5 to the offence, and the +5 stays in the score. In the bonus it also gives free throws and the possession ends: at the table the bonus is the second steal foul of the possession. In the app every foul is +5 to the offence and play goes on, and team fouls carry no penalty: a steal foul is +5, a team foul counted, the defender locked, no free throws (D-198, D-179; see Split by format). A steal foul on a shooter is a shooting foul: at the table free throws only; in the app +5 and its free throws (D-198). †
- Free throws from a steal foul score 2 × the ball carrier's free-throw rating. †
- On Two or Three, a fouled three with 30 or more in foul points counts as an Excellent three. †
- A turnover that ends the possession at 0 (the last phase at the table, Hold for One) scores 0 or the total banked before it, whichever is lower. In the app a turnover is −5 and play goes on; only a turnover in the last phase ends the possession, on what it has banked (D-198). † (setting: turnover_floor)
- A foul on a shot (once it is declared, or forced): free throws or the open shot, whichever is higher. The possession ends. (setting: and_one)
- Free throws score 2 × the shooter's free-throw rating, or 3 × on a three.
- Scenario cards: a look of 30 or more (Excellent) beats the card. Coach's Call: if the secret target takes the shot, add the bonus for the look: Poor +0, Okay +2, Good +5, Great +8, Excellent +10. †
- Need a Three: only a three scores; a fouled two's free throws score 0 too. † (setting: three_only_ft_on_twos)
- The Coach's Call bonus uses the look's band (the shot value, or the free throws if fouled), and counts on a forced shot by the target too. † (setting: coach_bonus_on_forced)

## Winning

- After the first possession, swap seats and trackers, flip every card and set up again. After both, the higher score wins. Tied: each player rolls for their final shot, d20 at or under rating − contest. A make beats a miss.
- On Late Clock cards, compare results first (win, then tie, then loss); the shot value breaks ties. †

## Digital only

- **Quarters and team fouls.** Each side's defensive fouls (steal fouls and shooting fouls) count across a running quarter of 18 possessions a side. The count carries across matches between the same two players, or a player and a computer level, and resets when both sides have had 18. The screen shows the count and the possessions left. Since D-198 the count carries no penalty: every foul is +5. (settings: quarter_possessions, bonus_from)
- **Match length.** A match is 4, 8 or 12 possessions a side, sides alternating. The higher total wins; a tie goes to overtime (see Split by format).
- **The decision timer.** Each player may set an optional thinking clock.
- **Computer levels.** The computer plays at three levels: Rookie, Starter and All-Star. The levels differ in how deep and how long they look ahead, not in the rules.
- **The trainer.** After a possession the trainer grades a player's decisions against the best options it found, and keeps a rating for each player.

## Split by format

**Control.** At the table: no control rule: a shot or a Contest is worth the same after any movement.  
In the app: your last movement this phase decides your control. After a Quick Step or a Sprint you're rushed: your shot or Contest is 2 lower. A Move puts you back in control.  
Why: ruled for the app (D-153). The table's rules are on hold while the app's game settles (D-146).

**Off balance.** At the table: no such rule.  
In the app: rushed: after a Quick Step or Sprint, or while locked, every roll you make is 2 worse (not fouls) until you Move. That covers shots, soft and hard contests, Dribble, Pass, Screen, Agility, Steal, Intercept and Challenge. A locked player can't Move, so he stays rushed until the phase ends.  
Why: ruled for the app (D-185). It reverses the "no drive rule" line of D-151.

**Contests: position, and the block.** At the table: one Contest: the defender's contest rating, with a foul roll if his arrow is off the shooter.  
In the app: every contest is a Contest action, one of the reply's two actions: nothing is automatic, and a shot nobody contests is open (D-261). The defender must be next to the shooter when he contests. Its rating, by where he stands: in front with his arrow on the shooter, the full contest rating; in front with his arrow off him, or beside him, 3 less; behind him (further from the rim), 6 less; rushed, 2 more off wherever he is; and always at least 1. On a jump shot (mid-range, long two, three) that is the Contest, with no shooting foul. On every shot the Contest is this honest contest, never a foul; the block is its own action in its place (see The block, D-271).  
Why: ruled for the app (D-191, D-193, D-194). D-261 (Shaun, 19 Nov 2026) made it an action: "the contest, whether normal or hard, always counts as a defensive action."

**The steal foul.** At the table: +5 to the offence; the second of the possession also gives free throws and ends it.  
In the app: every steal foul is +5 to the offence and play goes on (D-198): a team foul counted, the defender locked, no free throws. Team fouls carry no penalty.  
Why: fIBA Article 41 for the lock (D-179); D-198 (Shaun) made every foul +5 and play on, with no penalty, in place of D-181 and D-182.

**The block (D-271).** At the table: no block: the Contest (Shaun's rulings are for the app while the table is on hold, D-146).  
In the app: a defender next to the shooter may go for the block instead of contesting, on any shot, threes included. It is one of the reply's two actions, and one defender per shot: a contest or a block, never both. Fouls first, on his Foul (Block): no roll from in front with his arrow on the shooter, one from in front with it off, two from the side or behind; a foul is a shooting foul (+5 and free throws). No foul: roll his Block or under, 3 less from beside or with the arrow off, 6 less from behind, 2 less if he is rushed, never below 1. A block is a turnover: −5, the phase ends, the same possession goes on with a new phase (D-276): the shooter is forced 3 squares straight back from the basket (along the row, column or diagonal that points most directly away from it; stopped short by a player or the court's edge) and starts the phase as if he had just caught the ball; then the blocker may reset to any open square within 3 and set his arrow; everyone else stays. In the last phase the possession ends on what it has banked. A miss: the shot goes up against his full contest rating, 3 less from behind, 2 less if he arrived rushed. Against a fake he is locked for the phase and rolls the same foul rolls; a foul there is an ordinary foul: +5, play on, no free throws.  
Why: shaun, 20 Nov 2026: "bring back the block attempt... Deny the shot entirely." Ratings from his ratings sheet (D-269).

**Shot and pass fakes (D-272).** At the table: none.  
In the app: the ball handler declares a shot or a pass (to whom) and privately chooses real or fake. The defence replies as it would to the real thing: that reply is its turn. Then it is shown. A fake is an action that ends the offence's turn; the offence gets one Hesitate or fake each phase, shared. No fake when rushed. A fake isn't a move or a dribble: it doesn't keep him active when closely guarded, and after he has moved with the ball it picks the ball up (pass or shoot only); from a standstill his dribble stays alive. On a shot fake the defence's movements stand, an honest contest does nothing, and going for the block locks him and risks an ordinary foul. On a pass fake an Intercept or a Steal locks him; holding the lane costs nothing.  
Why: shaun, 20 Nov 2026: "They've wasted 2 actions... Suddenly being tighter on potential shooters is the only way to contest a fake."

**The pivot (D-273).** At the table: none.  
In the app: after he picks the ball up, the ball handler may take one Quick Step (one square, one of the side's Quick Steps). He still may only pass or shoot, and he is rushed. No Quick Step on his card, no pivot: his post move is his version.  
Why: shaun, 20 Nov 2026: "Maybe limited to a quickstep? Slow centers don't have one."

**Deep range (D-274).** At the table: none: no shot past the three-point band.  
In the app: a three from past the band is 1 off for each square past it in that column, never below 1 (A8 1 off out to A12 5 off; the top rows past the arc 1 and 2 off). Rows open by the team's playing level: Senior Pro to 5 off, Semi-pro to 2 off, Amateur and Youth to 1 off, Junior none. Each shooter uses his own team's rows; a team with no playing level plays Senior Pro. Rows 13 and 14 are never a shot.  
Why: shaun, 20 Nov 2026: "Juniors shouldn't be shooting out there. Pros do."

**Three seconds.** At the table: no such rule.  
In the app: time is counted in phase ends. An attacker in the key (columns G to K, from the baseline to the free-throw line) when two phases in a row end commits a violation: a turnover. After it he must get out of the key at once: still in it when the next phase ends, he commits it again. He may still catch and shoot from the key before then. Defenders have no such rule.  
Why: fIBA Article 26, ruled for the app (D-171, D-172, D-254).

**Closely guarded.** At the table: no such rule.  
In the app: a ball handler is closely guarded when a defender is next to him with an arrow on him. If he has held the ball since he caught it and is closely guarded when three phases in a row end, it is a violation: a turnover. Moving with the ball or a Dribble starts his dribble, and a dribble is never counted. After that, two whole phases without an action from him and he has picked the ball up: he may only pass or shoot, and the count runs. The count starts again when nobody closely guards him at a phase end.  
Why: fIBA Article 27, ruled for the app (D-173).

**The fouled shot.** At the table: the free throws (2 or 3 times the shooter's free-throw rating), or the open shot if that is higher.  
In the app: the shot still counts as a shot, at its contested rating. Free throws follow: 1 if it went in, 2 or 3 (its points) if it missed, each at the shooter's free-throw rating. The score is what that is worth on average, to the nearest point.  
Why: fIBA Articles 34 and 38, ruled for the app (D-174).

**Turnover cost.** At the table: −5 and the shot clock loses a phase; play on.  
In the app: −5, the phase ends there and the next begins, the same possession going on; a turnover in the last phase ends the possession on what it has banked (D-198).  
Why: d-198 (Shaun): the turnover costs the phase and its 5 points, not the whole possession.

**Shot-clock expiry.** At the table: a turnover, −5, then a forced shot from where the pieces stand.  
In the app: a turnover, −5: the possession is over on what it has banked (D-198).  
Why: as in basketball: no shot before the clock runs out is a turnover.

**Steal-foul bonus.** At the table: every steal foul +5; the second of the possession also gives free throws and ends it.  
In the app: no penalty: every steal foul is +5, a team foul counted, the defender locked, play on, no free throws (D-198).  
Why: one possession is the whole tabletop game; in the app every foul is +5 and play goes on (D-198).

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
17. Contest is an action, for every shot: one of the reply's 2 actions and its last, one a phase, by one defender next to the shooter at that moment, using a token. Nothing is automatic: no Contest, no contest, and the shot is open. So the most the defence can do is one movement and the Contest, as the offence gets one movement and the shot (D-261). A Steal ends the reply, so it can't also Contest. See D-18. (setting: contest_action)
18. The −3 never takes a contest below 0. See D-15. (setting: floor_contest_zero)
19. At the table every foul on a Steal is +5 to the offence, and the +5 stays in the score. In the bonus it also gives free throws and the possession ends: at the table the bonus is the second steal foul of the possession. In the app every foul is +5 to the offence and play goes on, and team fouls carry no penalty: a steal foul is +5, a team foul counted, the defender locked, no free throws (D-198, D-179; see Split by format). A steal foul on a shooter is a shooting foul: at the table free throws only; in the app +5 and its free throws (D-198). See D-89.
20. Free throws from a steal foul score 2 × the ball carrier's free-throw rating. See D-30.
21. On Two or Three, a fouled three with 30 or more in foul points counts as an Excellent three. See D-36.
22. A turnover that ends the possession at 0 (the last phase at the table, Hold for One) scores 0 or the total banked before it, whichever is lower. In the app a turnover is −5 and play goes on; only a turnover in the last phase ends the possession, on what it has banked (D-198). See D-82. (setting: turnover_floor)
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
