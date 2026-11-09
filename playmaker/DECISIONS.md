# Playmaker decisions

Every design decision for Playmaker, in one place. If this file doesn't record a decision, there isn't one.

- **Ruled:** Shaun has decided. Status: **built**; **ruled, not built** (with the step that builds it); or **built, not
  printed** (the game plays it, but the rulebook or trackers don't say it yet).
- **Engine defaults awaiting sign-off:** what the engine does today because a design value decides it, and Shaun hasn't
  ruled.
- **Open:** questions still to decide, with their options, grouped by the plan step that settles them.

Each entry keeps its old `OPEN_QUESTIONS.md` number (OQ) where it had one. That file is in `archive/`. The index at the
end maps OQ numbers to D numbers.

## 1. Ruled

### Shaun, 9 Nov 2026: rules the engine played that no printed page stated

**D-1** (OQ-5). A declared shot worth less than 0 scores 0, as a forced shot does.
Reason: otherwise a bad shot could be worse than letting the clock run out. · 3 Nov 2026, confirmed 9 Nov 2026 ·
Source: OQ-5; Shaun, 9 Nov 2026 · **Built, not printed.** (setting: floor_declared_shot)

**D-2** (OQ-4). A target of 20 or more always succeeds, 0 or less always fails; a 1 or a 20 has no special meaning.
Reason: sure things stay sure and hopeless rolls stay hopeless. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 ·
**Built, not printed.** (setting: natural_rolls)

**D-3** (OQ-11). In a 1 straight + 1 diagonal Move, the two steps may come in either order.
Reason: the same squares either way, so long as the middle square is empty. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 ·
**Built, not printed.** (setting: move_either_order)

**D-4** (OQ-25). A Move's 2 diagonal steps go the same way, in a straight line.
Reason: "2 diagonal" on the trackers means a straight diagonal. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 ·
**Built, not printed.** (setting: diag_move_straight)

**D-5** (OQ-14). A Quick Step goes up to the card's number of squares, not exactly that number.
Reason: a quick player can take a shorter burst. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built, not printed.**
(setting: qs_up_to)

**D-6** (OQ-52, C2). Each player has one Quick Step a phase, and a Sprint uses it. The side's limit of 2 still applies.
Reason: the trackers say a Sprint "uses that player's Move and Quick Step". · ruled step 2b, confirmed 9 Nov 2026 ·
Source: OQ-52; Shaun, 9 Nov 2026 · **Built, not printed.** (setting: qs_once_per_player)

**D-7** (OQ-15). A player with Quick Step 0 can't Sprint.
Reason: it removes a pointless option (a straight Move that spends a Quick Step). · 9 Nov 2026 · Source: Shaun,
9 Nov 2026 · **Built, not printed.** (setting: sprint_needs_qs)

**D-8** (OQ-21). A side with tokens left but no legal action gives up its remaining tokens.
Reason: every game must end; the rules were silent. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built, not printed.**
(setting: forfeit_when_stuck)

**D-9** (OQ-19). Before the ball is in, the inbounder may only pass.
Reason: the scenario rules say the inbounder can't move; passing is the only thing left for him to do. · 9 Nov 2026 ·
Source: Shaun, 9 Nov 2026 · **Built, not printed.** (setting: inbounder_pass_only)

**D-10** (OQ-30). On a forced shot the offence picks the shot type its tile allows.
Reason: the player decides, as with a declared shot. · step 3b, confirmed 9 Nov 2026 · Source: OQ-30; Shaun,
9 Nov 2026 · **Built, not printed.** (setting: forced_shot_choice)

**D-11** (OQ-24). "A defender next to the ball carrier" is judged when the movement starts.
Reason: the carrier reads the defence before he moves. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 ·
**Built, not printed.** (setting: arrow_line_adjacent_at)

**D-12** (OQ-18). A Dribble win lets the carrier through that defender's zone for the rest of the phase.
Reason: the beaten defender's lock lasts the phase too. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 ·
**Built, not printed.** (setting: dribble_win_lasts)

**D-13** (OQ-71). A successful Intercept puts the interceptor back on the square and arrow he had at the start of the
defence's turn; his Move stays used.
Reason: approved for now; revisited in step 9 with the cost of a pick-off (D-81). · step 3i, confirmed 9 Nov 2026 ·
Source: OQ-71; Shaun, 9 Nov 2026 · **Built, not printed.** (setting: intercept_return)

**D-14** (OQ-35). An inbound pass works like any other pass and lands after the defence's whole turn; then the phase
resets to the card's clock, offence first.
Reason: otherwise the receiver got a free turn after the catch. · step 2b, confirmed 9 Nov 2026 · Source: OQ-35; Shaun,
9 Nov 2026 · **Built, not printed.** (setting: inbound_resolves)

**D-15** (OQ-20). The far-contest −3 never takes a contest below 0.
Reason: a contest never makes a shot better. · 3 Nov 2026, confirmed 9 Nov 2026 · Source: OQ-20; Shaun, 9 Nov 2026 ·
**Built, not printed.** (setting: floor_contest_zero)

**D-16** (OQ-22). On Need a Three, only a three scores; a fouled two's free throws and steal-foul free throws score 0.
Reason: the scenario rules say "only a three-point shot scores". · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 ·
**Built, not printed.** (setting: three_only_ft_on_twos)

**D-17** (OQ-23). The Coach's Call bonus uses the look's band (the shot value, or the free throws if fouled), and counts
on a forced shot by the target.
Reason: the scenario rules say "add the bonus for how good the look was". · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 ·
**Built, not printed.** (setting: coach_bonus_on_forced)

### Shaun, 9 Nov 2026: two rule changes, built in step 6 (plan step 9)

**D-18** (replaces OQ-6). Contest becomes an action. After a shot is declared the defence reacts with up to 2 actions
from its remaining tokens: Move, Quick Step, Sprint, Steal or Contest. Contest is the last action, one a phase, by a
defender next to the shooter at that moment. No Contest means a contest of 0. The foul roll and the −3 work as now.
Reason: the offence spends 2 actions on a Move and a Shot; the defence had 2 actions plus a free contest. A closeout is
now a Sprint and a Contest, 2 actions, as in basketball, and a spent defence can't both get there and contest. ·
9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** (step 6, plan step 9). Printed game: the defence tracker gains a
Contest slot; the rulebook's Shooting section changes (by Shaun). A forced shot at clock 0 isn't declared, so it keeps
the contest choice. (setting: contest_action)

**D-19.** Overtime in the app. A tied app match plays one more possession a side, repeated until a side leads. The table
keeps its final-shot roll (D-60). A Split by format, approved.
Reason: basketball has no ties. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** (step 6, plan step 9).

### Shaun, 9 Nov 2026 (the open questions): rulings, built in step 6 (plan step 9)

**D-82** (OQ-74). A turnover that scores the possession 0 scores 0 or the total banked before it, whichever is lower.
Reason: a turnover never helps the offence. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** (step 6), both
formats. (setting: turnover_floor)

**D-83** (OQ-51). The lock stays as it is, for every player: no Move; a Quick Step still allowed if unused. No exceptions.
Reason: the rule as played. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built.**

**D-84.** Distance rings. "Closer, level or further from the rim" is the count of squares to the rim, diagonals
included (the engine's own test). The court shows it as faint rings. One check decides the steal and contest foul rolls
and the −3.
Reason: one test players can see. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** in the app (step 6); the
printed court by Shaun.

**D-85.** Player-facing words: never "pick-off", "picked off" or "clean miss". Say "intercepted", "stolen" and "a
Steal that misses without a foul".
Reason: plain basketball words. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** (step 6); the print by Shaun.

**D-87** (C5). "Plain wood", never "plain maple", everywhere players read.
Reason: one name for one thing. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** in the app (step 6); the print by
Shaun.

**D-88.** Growth at Junior. In the app the growth effect is applied when a Junior roster is made (dealt at random, as
before); only the resulting ratings show, no tag names anywhere a player reads, and Coach Vision gives one line on the
two players it changes (Early: "Bigger and stronger than most players his age."; Late: "Still growing: smaller and
slower than most players his age."). At the table there is no growth: the Junior cards play as printed. Split by
format, approved. Internally the tags are early, typical and late.
Reason: at the table it needed markers and a term players found unclear; the app can apply it unseen. · 9 Nov 2026 ·
Source: Shaun, 9 Nov 2026 · **Built** (step 6).

**D-89** (with D-90). Every steal foul is +5 to the offence, in both formats, and the +5 adds to the score over the
match. In the bonus, the offence also gets free throws, and the possession ends. At the table the bonus is the second
steal foul of the possession; in the app, the 5th team foul of the quarter. A steal foul on a shooter is a shooting
foul: free throws only (no +5); in the app it still counts as a team foul (Shaun, step 7 prompt; built in step 7).
Reason: a foul should always cost the defence. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** (step 6).
(setting: steal_foul_always_plus5)

**D-101.** All-Star's level description says it studies your saved games: "Studies your saved games and plans against
your habits."
Reason: players should know. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** (step 6).

**D-104** (OQ-44). When a screen blocks a step, the app shows that step greyed, with "Blocked by the screen".
Reason: legibility. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** (step 6).

**D-110.** A forced shot at clock 0 keeps the free contest choice: one defender next to the shooter contests, the
defence picks who, or no one. It is not a declared shot, so Contest as an action (D-18) doesn't apply.
Reason: the defence is out of tokens, and an adjacent defender always gets a hand up on a buzzer shot. · 9 Nov 2026 ·
Source: Shaun, step 7 prompt · **Built** (step 6).

**D-107.** Words: "match" is a whole game; "matchup" is one player against another. Used that way in everything players
read.
Reason: plain words. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Built** (step 7 checked every string; none misused).

**D-103** (OQ-49) and **D-105** (OQ-45). Superseded by the coach's goals design (D-106). No change now.
Reason: the coach's goals replace the Coach's Call questions in the app. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 ·
**Superseded.**

### Rulings from 3 Nov 2026 to step 3i (the old questions list)

**D-20** (OQ-1). After a successful Intercept or Steal that plays on, the ball stays with the passer or the carrier.
Reason: the rulebook and trackers say "play on". · confirmed 3 Nov 2026 · Source: OQ-1 · **Built.**
(setting: turnover_play_on)

**D-21** (OQ-2). A pass lands on the defence's next turn: the defence answers with its first action, or the pass lands.
Reason: a defender who can reach the lane gets one chance to close it. · confirmed 3 Nov 2026 · Source: OQ-2 ·
**Built.** (setting: pass_resolution)

**D-22** (OQ-3). A Sprint is up to 3 plus the Quick Step straight, or 2 plus the Quick Step diagonal.
Reason: a Move and a Quick Step in one straight line. · confirmed 3 Nov 2026 · Source: OQ-3 · **Built.**
(settings: sprint_orth_base, sprint_diag_base)

**D-23** (OQ-7, OQ-38). When the defence plays its last token the phase ends at once.
Reason: as written; a token-heavy defence sets the pace, and at full budgets it never moved a value. · step 3i ·
Source: OQ-7, OQ-38 · **Built.** (setting: defence_empty_ends_phase)

**D-24** (OQ-8). Hesitate and Pause can't be played on the turn straight after the other side's wait.
Reason: it stops wait-for-wait stalling. · confirmed 3 Nov 2026 · Source: OQ-8 · **Built.** (setting: wait_chain_block)

**D-25** (OQ-9). A screen's T bans a defender's diagonal step that starts on the T square or cuts its corner.
Reason: the screen has to block a path, not just one square. · confirmed 3 Nov 2026 · Source: OQ-9 · **Built.**
(setting: screen_geometry)

**D-26** (OQ-12, C1). The defence chooses which adjacent defender contests, or that no one does.
Reason: the player decides; the rulebook's old "nearest defender" wording was changed to match. · step 3b ·
Source: OQ-12, C1 · **Built.** (setting: contest_choice)

**D-27** (OQ-13). A defender is "on" the pass line when it passes through his square's centre.
Reason: the rulebook's wording ("through your square's centre"). · Nov 2026 rulebook · Source: OQ-13 · **Built.**
(setting: on_line_tolerance)

**D-28** (OQ-16). Only the defender standing on a screen's T square may Challenge it.
Reason: he is the one it blocks; it covers the post seal. · 3 Nov 2026 · Source: OQ-16 · **Built.**
(setting: challenge_who)

**D-29** (OQ-17, C4). A locked player can't Move, Sprint, Dribble or turn his arrow; he may still Quick Step. A locked
ball carrier can't Dribble: a lost dribble means pass or shoot.
Reason: the trackers' reading; the rulebook's "can't move" was changed to match. · 3 Nov 2026 · Source: OQ-17, C4 ·
**Built.** (setting: locked_can_dribble)

**D-30** (OQ-26). Free throws from a steal foul score 2 × the ball carrier's free-throw rating.
Reason: the rulebook names "the shooter", and on a steal foul the ball carrier is the one fouled. · confirmed 3 Nov 2026
· Source: OQ-26 · **Built, not printed.** Register row to be added in step 9, when the print is updated (Shaun, step 4
prompt).

**D-31** (OQ-27). On a failed inbound, if players tie for furthest from the rim, the offence picks who gets the ball.
Reason: the scenario rules say "offence picks if tied". · 3 Nov 2026 · Source: OQ-27 · **Built.**
(setting: inbound_tie)

**D-32** (OQ-28). Once the ball is in, the inbounder stays on his off-court square until he moves onto the court. He
can catch a pass there but can't shoot.
Reason: the scenario rules say "the inbounder may step onto the court". · confirmed 3 Nov 2026 · Source: OQ-28 ·
**Built.**

**D-33** (OQ-29). A Screen is the turn's first action, or its second straight after that player's own Move, and ends the
turn. It lasts until the screener moves, a Challenge beats it (for everyone), or the phase ends. A failed Challenge
locks the challenger.
Reason: the offence can set a screen, let the defence answer, use it, and only then release the screener. · step 3i ·
Source: OQ-29 · **Built.** (setting: screen_rule)

**D-34** (OQ-31). A defender who moves onto the pass line but then doesn't Intercept lets the pass land.
Reason: any other action means the pass lands. · confirmed 3 Nov 2026 · Source: OQ-31 · **Built.**

**D-35** (OQ-32). Lock tokens have no cap. The rulebook and token sheet print 8; the worst case in one phase is 6 (2
Dribbles, 2 Challenges and 2 Steals, since a failed Steal locks too).
Reason: 8 tokens cover the worst case. · 3 Nov 2026, reasoning updated 9 Nov 2026 · Source: OQ-32 · **Built.**

**D-36** (OQ-33). On Two or Three, a fouled three with 30 or more in foul points counts as an Excellent three.
Reason: it follows from the and-one (D-37). · 3 Nov 2026 · Source: OQ-33 · **Built, not printed.** Register row to be
added in step 9, when the print is updated (Shaun, step 4 prompt).

**D-37** (OQ-34). The and-one: once a shot is declared or forced, any foul scores the higher of the free throws and the
shot's open value.
Reason: fouling a good look can never help the defence. · 3 Nov 2026 · Source: OQ-34 · **Built.** (setting: and_one)

**D-38** (OQ-39). Shot-clock expiry stays as built: a turnover, −5, and a forced shot.
Reason: under best play it never happens, and a forced shot below 0 already scores 0. · step 2b · Source: OQ-39 ·
**Built.** (See D-99 for how often it happens in play.)

**D-39** (OQ-59, OQ-60, OQ-61, OQ-62). The step 3h contest geometries (wedge mirror, rim distance) are not adopted.
Reason: a rule test; the questions they raised close with it. · step 3i · Source: OQ-59 to OQ-62 · **Built.**
(setting: contest_geometry)

**D-40** (OQ-63). The ball carrier can't Screen.
Reason: a handoff is a short pass, not a screen. · step 3i · Source: OQ-63 · **Built.** (setting: carrier_can_screen)

**D-41** (OQ-64). Each side gets one wait a phase: one Pause (defence) or one Hesitate (offence).
Reason: as the trackers say. · step 3i · Source: OQ-64 · **Built.**

**D-42** (OQ-65). A handoff is a short pass to a teammate next to the passer; it doesn't use the Screen rule.
Reason: the passer's piece blocks a chasing defender by standing on a square. · step 3i · Source: OQ-65 · **Built.**

**D-43** (OQ-66). Rebounds, transition and deliberate fouls are out of scope.
Reason: a half-court game about building one shot. · step 3i · Source: OQ-66 · **Built.**

**D-44** (OQ-67). A Sprint faces its run; a Quick Step 0 card has no movement once its Move is used; the reaction budget
is shared by the whole defence.
Reason: all three match the rules as written. · step 3i · Source: OQ-67 (b to d) · **Built.** (The computer's matchup
record, OQ-67 (a), is D-72.)

**D-45** (OQ-68). A defender's zone is the squares along his arrow he could reach with one movement from what he has
left, stopping at the first player in the way.
Reason: it makes a defender's reach visible on the board. · step 3i · Source: OQ-68 · **Built.**

**D-46** (OQ-70, OQ-10). Drives: the ball carrier may step into the zone of a defender next to him, but not through it,
unless he beat that defender on a Dribble this phase.
Reason: replaces the old "crossing the arrow line" test. · step 3i · Source: OQ-70 · **Built.** (setting: drive_rule)

**D-47** (OQ-72, OQ-73, OQ-53, C3). Interception: the pass line is fixed when the pass is declared. One defender
answers: one straight Move, Quick Step or Sprint along his arrow onto the line, then Intercept; or the line passes
through his square and the Intercept is his first action, whatever his facing. Anything else first and the pass lands.
No Intercept on any square next to the passer; he Steals instead. A missed Intercept leaves him on the line, his Move
used.
Reason: replaces the wider "approach" reading; a defender must really reach the lane. · step 3i · Source: OQ-73
(refining OQ-72) · **Built.** (setting: intercept_rule)

**D-48** (OQ-74). At the table a successful Intercept or Steal costs −5 and the shot clock loses a phase; play goes on
with the same tokens. In the last phase the possession scores 0. A stolen shot is cancelled and doesn't use the
phase's shot.
Reason: a turnover should cost time as well as points. · step 3i · Source: OQ-74 · **Built.** (setting: turnover_cost;
its open edge is D-82)

**D-49** (OQ-75, OQ-69). One arrow per defender. The two-line wedge stays available but off, and the late-closeout
test stays off.
Reason: after the interception run, one arrow with late closeouts off was closest to basketball. · step 3i ·
Source: OQ-75 (superseding OQ-69) · **Built.** (settings: arrow_mode, late_closeout)

**D-50** (OQ-76). A lane jump keeps the defender's facing.
Reason: the rulebook says "keeping your facing". · Nov 2026 rulebook · Source: OQ-76 · **Built.**
(setting: lane_jump_keeps_facing)

**D-51** (OQ-77). Receiver denial: no pass through the square of a defender next to the receiver, whatever his facing.
Reason: face-guards and fronting the post become real denials; the offence must move, cut, change the angle or screen.
· Nov 2026 · Source: OQ-77 · **Built.** (settings: receiver_denial, receiver_denial_tol)

### Rulings in the step prompts (solver steps 2b to 3n, and plan steps 1 and 2)

**D-52.** The app's match: 4, 8 or 12 possessions a side, sides alternating. A successful Intercept or Steal, and
shot-clock expiry, end the possession at 0. Steal fouls work as at the table until the quarter's bonus (D-55).
Reason: an app match has several possessions, so the next possession is the cost. · step 3m · Source: step 3m prompt,
Part A · **Built.** Split by format, recorded in the rules register. (setting: digital)

**D-53.** A failed Steal (no foul, the ball kept) locks the defender, both formats.
Reason: a reach costs something; timing now matters. · step 3n · Source: step 3n prompt, F1 · **Built.**
(setting: steal_lock)

**D-54.** The angle of a reach sets the foul risk: one foul roll from closer to the rim than the ball carrier or
shooter, two from level or behind, for Steals and contests alike. The −3 is unchanged.
Reason: reaches from beside or behind foul more. · step 3n · Source: step 3n prompt, F2 · **Built.**
(setting: reach_angle_fouls)

**D-55.** In the app, team fouls run across a quarter of 18 possessions a side, carried between matches of the same
pairing; from the 5th team foul a steal foul gives free throws and ends the possession. The table keeps its
within-possession rule.
Reason: about a real quarter at the cards' level. · step 3n · Source: step 3n prompt, F3 · **Built.**
(settings: quarter_possessions, bonus_from)

**D-56.** The engine prices a foul by its effect on the rest of the quarter.
Reason: a foul should cost more as the bonus nears. · step 3n · Source: step 3n prompt, F4 · **Built.**

**D-57.** Playing levels: ages (Senior, Youth, Junior), standards (Pro, Semi-pro, Amateur), growth tags at Junior, and
the roster modes (prescribed, build, your team, random, draft).
Reason: the designer's levels handoff, copied unedited. · step 3l · Source: step 3l prompt; levels sheet · **Built.**

**D-58.** One card pool per matchup; the draft handicap; jobs read at the card's age; the old custom route retired.
Reason: follow-ups to the levels. · step 3m · Source: step 3m prompt, Part 0 · **Built.**

**D-59.** Two formats, one game: a shared rule is the same in both formats; any difference is deliberate, marked Split
in the register and approved by Shaun.
Reason: protect the printed game. · step 3n · Source: step 3n prompt, K; `CLAUDE.md` · **Built.**

**D-60.** A tied two-possession table game: each player rolls for their final shot, d20 at or under rating − contest; a
make beats a miss.
Reason: the rulebook's tie-break. · rulebook · Source: rulebook page 2 · **Built.**

**D-61.** `CLAUDE.md` governs the Playmaker folder only, not the website.
Reason: its paths are Playmaker's. · step 2 · Source: step 2 prompt · **Built.**

**D-76** (OQ-40, OQ-41, OQ-50). Solver findings are read as recorded: a verdict means "best over the next few turns";
the evaluation looks over the offence's next two turns against the defence's best reply; the step 3d teams changed one
card's verdict (Baseline Stack Wall, 18.0 to 16.6), so the old verdict isn't reused.
Reason: the solver reaches only a few turns deep, and the one-turn evaluation was blind to defensive position. · solver
steps 2b and 3d · Source: those step prompts (OQ-40, OQ-41, OQ-50); Shaun, step 4 prompt · **Built.**

**D-78.** Coach Vision during play shows at the Learn level only, and there it reads the same way for both sides (the
threat, the offence's read, the defence's read). At Scout and Pro no coach line shows during play.
Reason: coaching in play is for learners, and it mustn't favour one side. · step 3i follow-up · Source: that step
prompt; Shaun, step 4 prompt · **Built.**

**D-79.** The decision timer: off by default; 60, 45 or 30 seconds a decision, chosen at the start, the same for both
players and written to the log. Each player may have their own setting only when both tick "handicap" at setup.
Reason: the table slows decisions far below basketball pace; the timer brings back some pressure. · step 3d · Source:
step 3d prompt; Shaun, step 4 prompt · **Built.**

### Shaun, 9 Nov 2026 (step 8 prompt): the engine's settings, and the open questions settled

**D-62.** Responses read per defender: 3. Shapes how well the computer and the trainer read the defence, and the
search's speed. (setting: eval.responses_per_defender)
· 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, provisional (phase 4).** Phase 4 tunes it against the exam; any change needs evidence and Shaun's approval.

**D-63.** Looks per attacker: 6. Shapes how many shots the engine sees for each attacker, and the search's speed.
(setting: eval.looks_per_attacker)
· 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, provisional (phase 4).** Phase 4 tunes it against the exam; any change needs evidence and Shaun's approval.

**D-64.** A look that needs another offence turn counts at 70%, and the leaf credits 85% of the best uncovered look.
Shapes how much the computer values setting up against shooting now. (settings: eval.later_p, eval.continuation)
· 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, provisional (phase 4).** Phase 4 tunes it against the exam; any change needs evidence and Shaun's approval.

**D-65.** The foul price assumes 0.25 defensive fouls a possession and a play-on value of 20 points. The phase table
says an average possession is worth about 28, so the price is low. Shapes when the computer reaches.
(settings: eval.fouls_per_possession, eval.play_on_value)
· 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, provisional (phase 4).** Phase 4 tunes it against the exam; any change needs evidence and Shaun's approval.

**D-66.** The phase table (the value of an average possession at each phase) is solved from app self-play and used as
the leaf's floor. Shapes every evaluation and the trainer's grades; it flattens marginal positions.
(data: vcoarse.json)
· 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, provisional (phase 4).** Phase 4 tunes it against the exam; any change needs evidence and Shaun's approval.

**D-67.** The computer levels: search depth, beam, opponent model, noise, attention, reaction delay, time budget, goal
and variety margins, and All-Star scouting. Shapes how each level plays. (ai_profiles.json, profiles)
· 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, provisional (phase 4).** Phase 4 tunes it against the exam; any change needs evidence and Shaun's approval.

**D-68.** The trainer: bands for a slip (1), a mistake (3) and a big mistake (6 points); accuracy constant 2.0; summary
of 3 points; fading by rating; flags need agreement at two search depths. Shapes every grade and summary.
(ai_profiles.json, trainer)
· 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, provisional (phase 4).** Phase 4 tunes it against the exam; any change needs evidence and Shaun's approval.

**D-69.** The rating anchors: Rookie 1525, Starter 1600, All-Star 1625 (Senior), Youth 20 lower, Junior 50 lower,
fitted from self-play in step 3n. Shapes every rating. (ai_profiles.json, trainer.anchors)
· 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, provisional (phase 4).** Phase 4 tunes it against the exam; any change needs evidence and Shaun's approval.

**D-80.** The browser search runs at the full time budgets (scale 1.0); the computer's search is cut at the budget.
Shapes how deep the computer looks on a phone. (setting: eval.browser_budget_scale)
· 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, provisional (phase 4).** Phase 4 tunes it against the exam; any change needs evidence and Shaun's approval.

**D-81** (OQ-54). The cost of an Intercept stands as built. The paired read (step 7): an Intercept costs the offence 6.4
points on average, about 3.8 before the last phase and the whole possession in it; 1 of 18 pairs helped the offence, by
0.9. D-13 (the interceptor returns to his start square) resolved the original problem.
Reason: the measurement shows an Intercept always costs the offence. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 ·
**Closed.**

**D-91.** The All-Star searches a median of 3 turns deep on a phone, against a target of 4 to 6: accepted for now.
Reason: revisit with the levels. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, for now;** revisit in step 14.

**D-94** (OQ-57). An open shot is not an advantage. Shaun's principle: "An advantage is what creates a better shot, not
the shot itself. A shot is an option, held against a standard that can differ for each team: the offence is satisfied
when the look beats what its possession is worth now; the defence may deliberately offer looks below what it can live
with. A wide-open shot is not the advantage; the advantages created that opportunity." The six advantage states stay.
Note for the trainer: never call a shot an advantage in player-facing text.
Reason: the principle above. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled.**

**D-95** (OQ-55). Responsibility comes from coverage, not fixed matchups. Each defender holds shares across the offensive
threats, from the engine's own coverage. 100% on one player is guarding him (always the case for the ball). Splits
across two or three are help or zone. Man-to-man is the case where every share is near 100% on one player. "His man" in
reads and the trainer means the threat he holds the largest share of, and the trainer says splits plainly ("X3 is
splitting O2 and O4"). No new rules.
Reason: the defence's responsibilities come from what it covers. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, not
built:** phase 4, with the trainer's flags (step 16).

## 2. Engine defaults awaiting sign-off

**D-70.** The computer's setup and placement: the offence takes the placement worth most against the defence's best
reply, without seeing the real defence; the defence takes the placement and matchups that cover best. Shapes every game
against the computer. (Restated for the step 3m engine, Shaun, step 6 prompt; `agent.propose_offence`,
`agent.propose_defence`)

**D-71** (OQ-43). The human's setup: place by hand, accept the engine's proposed setup, or repeat the last one; a
one-tap standard setup. Shapes how fast a game starts.

**D-72** (OQ-67). The computer's record of who guards whom: set by distance when the possession starts, changed only by
a switch or a replacement. Shapes the computer's defence and the advantage reads.
**Retired:** the code it described is archived, step 5 (Shaun, step 6 prompt).

**D-73** (OQ-56). "Help pulled" is read against the board the offence handed over at the end of its turn. Shapes the
advantage reads.
**Retired:** the code it described is archived, step 5 (Shaun, step 6 prompt).

**D-74** (OQ-58). "The likely closeout defender" is the defender nearest the shooter (the lower number on a tie). Shapes
the advantage reads.
**Retired:** the code it described is archived, step 5 (Shaun, step 6 prompt).

**D-75** (OQ-42, OQ-43, OQ-46). Playtest interface defaults: every roll says who rolls; opening placement for full
games; every court choice repeated as a full-size button on phones. Shapes the interface only.

**D-77** (C6). Scenario 10 is played with the card's numbers (4 tokens left a side, both Screens spent). Shapes one card.

## 3. Open

### Step 9: the tabletop rules

**D-86** (OQ-37, OQ-48). Wait: Contest as an action may bring back Challenge and the Sprint closeout. Measure in a later
step. · Source: Shaun, 9 Nov 2026 · **Open, after step 6.**

### Step 10: the digital bonus

None open: D-89 and D-90 were ruled on 9 Nov 2026 (see Ruled).

### Step 11: engine choices

**D-93** (OQ-36, OQ-47). Pause was the defence's most-used action in the solver's lines; it looks like a search artefact.
Options: widen the defence's candidate moves below the root; or read it as a rule problem. Effect: whether Pause is too
cheap.
Shaun, 9 Nov 2026: re-measure in phase 4 under the 9 November rules.

### Step 12: the exam

**D-96.** Exam boards that predate rulings: board 1 (the straight lane, now judged by outcome), 7 (the clock), 10 (steal
odds, before the steal lock and two foul rolls) and 11 (contested passes, before the app's turnover rule).
Options: restate each board against today's rules; retire it. Effect: what the exam can tell a design fault from.

**D-97.** Board 14 (variety): at depth 4 one first action wins every time, because the noise and the variety margin are
smaller than the value gaps a deeper search finds. The depth-6 run was not done.
Options: widen the variety margin; restate the board; accept it. Effect: how predictable the All-Star is.

**D-108.** Exam candidate (from Shaun's playtest reports): the defence denies an elite shooter's catch (the old
`test_deny_catch`). · Source: Shaun, step 6 prompt · **Open:** to be added as an exam board in step 12.

**D-109.** Exam candidate (from Shaun's playtest reports): the offence prefers a clean pass to a contested one (the old
`test_passing`). · Source: Shaun, step 6 prompt · **Open:** to be added as an exam board in step 12.

**D-111.** Exam board 6 (catch window) is marked as an expected failure: Contest as an action (D-18) changed the
reading; re-based with the exam in step 12. · Source: Shaun, step 7 prompt · **Open:** step 12.

**D-112.** The trainer test "an early cut is flagged with a legal reorder" is marked as an expected failure for the same
reason; re-based with the exam in step 12. · Source: Shaun, step 7 prompt · **Open:** step 12.

**D-113.** The trainer test "the credit names the helper who answered the decoy" is marked as an expected failure for the
same reason; re-based with the exam in step 12. · Source: Shaun, step 7 prompt · **Open:** step 12.

### Step 13: the phase table

**D-92.** The phase table rises from about 25 in phase 1 to about 29 in phase 6 at Senior Pro, and as the leaf's floor it
flattens marginal positions.
Options: use the table only where the board read has no look; blend it with the read; keep it. Effect: the computer's
sense of the clock and the trainer's flags (D-100).
Shaun, 9 Nov 2026: settled in step 13, with exam evidence.

### Step 14: the levels

**D-98.** The levels are closer than the old anchors assumed: All-Star beats Starter only a little (match score 0.47),
and the trainer can't tell the levels apart by decision quality (each loses about 0.8 points a decision).
Options: widen the profiles (D-67); grade with a searched reply; accept closer levels. Effect: what Rookie, Starter and
All-Star mean to a player.

### Step 15: the shot clock

**D-99.** Shot-clock expiries at the table: 10 per 100 possessions (`BASELINE.md`), against about 1 in basketball.
Options: an engine choice (the computer holds too long); a rule (the forced shot, the −5). Effect: how often a
possession ends without a real shot.

### Step 16: the trainer's flags

**D-100.** No off-ball, minimal-value or timing flag fired in 20 real possessions. The flags need agreement at two
depths, and the phase table's floor flattens the reads (D-92).
Options: change what a flag needs; grade with a searched reply; accept it. Effect: what the trainer tells players.

### The design step

**D-106.** Coach's goals (app only), to be designed. Before setup, the coach gives each side up to two secret goals.
Goals can counter each other. If a goal looks to be failing, the coach offers a new one. In advanced play a player may
set their own. Meeting a goal earns no match points: it counts only toward the coach's judgement and the player's
rating. The tabletop keeps its scenario cards and Coach's Call as they are. · Source: Shaun, 9 Nov 2026 · **Open:**
design step.

### Not yet placed in a step

**D-102.** The lock count measurement may read low: the runs count locked pieces before each action. Low priority: 8
tokens cover the worst case of 6.
Options: count after each action; leave it. Effect: one reported figure.

## Index: old question numbers

| OQ | D | OQ | D | OQ | D | OQ | D |
|---|---|---|---|---|---|---|---|
| 1 | D-20 | 21 | D-8 | 41 | D-76 | 61 | D-39 |
| 2 | D-21 | 22 | D-16 | 42 | D-75 | 62 | D-39 |
| 3 | D-22 | 23 | D-17 | 43 | D-71, D-75 | 63 | D-40 |
| 4 | D-2 | 24 | D-11 | 44 | D-104 | 64 | D-41 |
| 5 | D-1 | 25 | D-4 | 45 | D-105 | 65 | D-42 |
| 6 | D-18 | 26 | D-30 | 46 | D-75 | 66 | D-43 |
| 7 | D-23 | 27 | D-31 | 47 | D-93 | 67 | D-44, D-72 |
| 8 | D-24 | 28 | D-32 | 48 | D-86 | 68 | D-45 |
| 9 | D-25 | 29 | D-33 | 49 | D-103 | 69 | D-49 |
| 10 | D-46 | 30 | D-10 | 50 | D-76 | 70 | D-46 |
| 11 | D-3 | 31 | D-34 | 51 | D-83 | 71 | D-13 |
| 12 | D-26 | 32 | D-35 | 52 | D-6 | 72 | D-47 |
| 13 | D-27 | 33 | D-36 | 53 | D-47 | 73 | D-47 |
| 14 | D-5 | 34 | D-37 | 54 | D-81 | 74 | D-48, D-82 |
| 15 | D-7 | 35 | D-14 | 55 | D-95 | 75 | D-49 |
| 16 | D-28 | 36 | D-93 | 56 | D-73 | 76 | D-50 |
| 17 | D-29 | 37 | D-86 | 57 | D-94 | 77 | D-51 |
| 18 | D-12 | 38 | D-23 | 58 | D-74 | C1 | D-26 |
| 19 | D-9 | 39 | D-38 | 59 | D-39 | C2 to C6 | D-6, D-47, D-29, D-87, D-77 |
| 20 | D-15 | 40 | D-76 | 60 | D-39 | | |
