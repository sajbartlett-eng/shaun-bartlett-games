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
The six states (from step 3g, now in `archive/engine/advantage.py`; the live computer doesn't use them) are kept as the
trainer's vocabulary for step 16, alongside the coverage shares (D-95). (Shaun, step 9 prompt)
Reason: the principle above. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled.**

**D-95** (OQ-55). Responsibility comes from coverage, not fixed matchups. Each defender holds shares across the offensive
threats, from the engine's own coverage. 100% on one player is guarding him (always the case for the ball). Splits
across two or three are help or zone. Man-to-man is the case where every share is near 100% on one player. "His man" in
reads and the trainer means the threat he holds the largest share of, and the trainer says splits plainly ("X3 is
splitting O2 and O4"). No new rules.
Reason: the defence's responsibilities come from what it covers. · 9 Nov 2026 · Source: Shaun, 9 Nov 2026 · **Ruled, not
built:** phase 4, with the trainer's flags (step 16).

### Shaun, step 9 prompt: the answers to step 8

**D-77** (C6). Scenario 10 is played with the card's numbers (4 tokens left a side, both Screens spent). Shapes one card.
· Source: Shaun, step 9 prompt · **Ruled.**

### Shaun, 9 Nov 2026 (step 10 prompt): the marks on the exam boards

From the step 9 evidence. Built in step 10: the boards marked "fix" are rebuilt to the stated intent, with the facts on
their exam-book pages. · Source: Shaun, 9 Nov 2026 · **Ruled.**

| Board | Ruling |
|---|---|
| 1 Straight lane | Fix: the drive must start strong (worth more than the offence's best other option) before the defence acts. |
| 2 Sag by shooting | Keep. A real gap (the moves read level). |
| 3 Help the helper | Fix: the computer was right that X1 could recover. Rebuild so X1 can't get back beside O1, so help must come. |
| 4 Two jobs, one defender | Fix: rebuild so the pass to O5 is legal. Judge only what the offence does (attack X5: O1 shoots or drives, or passes to O5) or that it picks something the evidence shows is worth more. Drop the part that judges the computer's own reading. |
| 5 Closeout | Fix B: stepping up for an open three is right. B is met by a shot now or a move to a spot where no defender can Contest. A: the drive must end closer to the rim. |
| 6 Catch window | Keep, judged by D-94: O4 acts at once when the open look beats what the possession is worth (33 against 24.9). A real gap (the screen reads level with the shot). |
| 7 Clock | Fix B: make it the offence's final turn of the possession. |
| 8 Backdoor | Fix: clear the passing lane, so no defender can step into the backdoor pass. The board then tests the cut, not a risky pass. |
| 11 Contested pass | Fix B: make the pass to O2 legal (X2 off the line, X5 in the lane), on the offence's final turn. |
| 13 Spacing | Keep. A real gap (everything reads 24.9). |
| 14 Variety | Accept (D-97): being predictable is fine when one move is clearly best. The judge is met when the top first move leads by more than the variety margin; otherwise, no first move above 70%. |
| 16 Wearing out one defender | Keep. A real gap: the computer spends X2, then doesn't use it. |
| C1 (D-108) | Keep (met). |
| C2 (D-109) | Fix: rebuild so the clean pass really is clean (no defender can step into it) and the other pass is contested. |
| T1, T2 (D-112, D-113) | Keep; re-base after the goals step. They stay marked as expected failures. |
| 9, 10, 12, 15, 17 | Keep. |

This settles D-96 (boards 1, 7 and 11 fixed; 10 kept), D-97 (accepted, the judge restated), D-108 (kept), D-109
(rebuilt) and D-111 (board 6 kept, judged by D-94). D-112 and D-113 stay open until the goals step.

### Shaun, 10 Nov 2026 (step 11 prompt): the position value against the average

**D-92, ruled.** `leaf_mode` is `relative` by default (`eval.leaf_mode`, both engines). A position is worth the phase
table's average plus how much better or worse its continuation reads than an average position at that phase. A shot now
and a look released this turn stay at their own value; only the continuation is read against the average. `floor`
(the phase table as the reading's floor) stays as the switch's other setting. · Source: Shaun, 10 Nov 2026 ·
**Ruled, built** (step 11).

**D-114. The averages.** Senior Pro's averages are the base for every level. For any other age and standard, Senior
Pro's average at each phase is scaled by that level's phase table value over Senior Pro's at the same phase. A level
uses its own averages only once it has at least 100 positions at that phase (the 100 is provisional).
`tools/relative_average.py` builds them and records, for each level and phase, which it used. · Source: Shaun,
10 Nov 2026 · **Ruled, built** (step 11); the 100 is **provisional**.

**D-115. The driving-lane term** (a crowded or clear driving lane, exam board 13): moved to the goals design (plan step
12). · Source: Shaun, 10 Nov 2026 · **Open:** plan step 12.

**D-116. The rebuilt boards that still fail** (1, 3, 5 A, 6, 8 and 11) and boards 9 and 10: kept as they are, as honest
targets for the goals step and the "don't stop mid-action" step. · Source: Shaun, 10 Nov 2026 · **Ruled.**

### Shaun, 10 Nov 2026 (step 12 prompt): the answers to step 11

**D-117. Exam board 7 B: 1 token,** so the offence's turn is final whatever it does. Rebuilt in step 12. · Source:
Shaun, 10 Nov 2026 · **Ruled, built.**

**D-118. The exam's main measure is a fixed look-ahead.** The clock run moves with machine load and is a second check
only. From step 12 on, every exam table leads with the fixed look-ahead (2 team-turn pairs: an offence turn and the
defence's reply, twice) and gives the clock result beside it. · Source: Shaun, 10 Nov 2026 · **Ruled.**

### Shaun, 10 Nov 2026 (step 13 prompt): the answers to step 12

**D-119. The tempo term is a measured term.** The same position reads 2.3 points better with the offence to act than
with the defence (1.7 in phase 1 to 2.9 in phase 5; `search.tempo`, from `tools/stable_measures.py`). It is accepted as
measured, not chosen. Its switch stays off. · Source: Shaun, 10 Nov 2026 · **Ruled.**

**D-120. The reading's margin of error** (one standard error by phase: 0.92, 1.05, 1.22, 1.34, 1.42, 1.52;
`search.stable_margin`) is accepted as **provisional**. · Source: Shaun, 10 Nov 2026 · **Ruled, provisional.**

**D-115, extended.** Teammates in an attacker's path are part of the reading: a look at the rim or the post counts only
from the squares the attacker can reach in time, by the movement rules, teammates included. ·
Source: Shaun, 10 Nov 2026 · **Ruled, built** behind `eval.coverage_budget` (off) in step 13, part B, for the ball
handler's squares two actions away. Board 13 itself doesn't move: its rim is three actions away (STEP13B_REPORT).

### Shaun, 10 Nov 2026 (after step 13, part A): the stable search's switches and the speed budget

**D-121. On by default, in both engines:** `like_with_like` (the answer comes from the deepest even look-ahead: an
offence turn and the reply) and the reach map (`eval.reach`). · Source: Shaun, 10 Nov 2026 · **Ruled, built** (step 13).

**D-122. Off:** `quiet_points`, `clear_reason`, `tempo` and `play_on`. `tempo` and `play_on` are measured again after
step 13, part B, on the bigger exam. · Source: Shaun, 10 Nov 2026 · **Ruled;** the second measure is **open**.

**D-123. The speed budget** is accepted as **provisional**, as proposed: each level finishes 1 team-turn pair on 9
decisions in 10, in 0.3, 1.0 and 2.5 s on a desktop (Rookie, Starter, All-Star) and 1.0, 2.0 and 3.0 s on a phone.
"Phone" is an assumed quarter of desktop speed until a real phone is measured. `docs/SPEED_BUDGET.md`. · Source: Shaun,
10 Nov 2026 · **Ruled, provisional.**

**D-124. The two speed-ups that change results** (a window at the root; narrow quiet points) are not built now. ·
Source: Shaun, 10 Nov 2026 · **Ruled.**

### Shaun, 10 Nov 2026 (step 13C prompt): the answers to step 13, part B

**D-125. The Contest under the budget** (`eval.coverage_budget`). A Contest from where a defender stands is free
across every attacker he is next to: only one shot happens, so a defender between two shooters really covers both.
Only answers that need a movement (a Move, a Quick Step or a Sprint to reach a shooter or a lane) share the defender's
budget. · Source: Shaun, 10 Nov 2026 · **Ruled, built** (step 13C).

**D-126. The phone budget.** A real phone is measured (the app's speed test, `?speedtest=1`) before any phone target
changes. Until then the All-Star's phone target stays at 3.0 s, and the overrun is noted, not fixed. · Source: Shaun,
10 Nov 2026 · **Ruled;** the measurement is **open**.

**D-127. Board 13.** The crowded lane needs a look beyond one team turn. That is goal progress, so it moves to stage 3
(advantages: create, keep and convert). No discount for later looks is added now. · Source: Shaun, 10 Nov 2026 ·
**Open:** stage 3.

### Shaun, 10 Nov 2026 (step 16 prompt): the answers to step 13C

**D-128. The re-measured averages are stored** in step 16, since that step changes the reading anyway:
`eval.relative_average` under the default game (the reach map on), and `eval.relative_average_budget` under
`eval.coverage_budget`. · Source: Shaun, 10 Nov 2026 · **Ruled, built** (step 16).

**D-129. Foundation work stops here.** No more speed-only steps unless Shaun's phone test shows the game is
unplayable. · Source: Shaun, 10 Nov 2026 · **Ruled.**

**D-130. The checkpoint.** If the exam doesn't clearly improve with step 16's switches on (`eval.advantages`,
`search.goals`), stop and rethink before stages 5 to 8 (the defence's answers, the coach's goals, the trainer,
scouting) are built on top. · Source: Shaun, 10 Nov 2026 · **Ruled;** step 16 reports it, Shaun decides.

### Shaun, 10 Nov 2026 (step 17 prompt): the checkpoint, and learned judgement

**D-131. The checkpoint result (D-130).** Goals as built didn't clearly improve the exam: 0 boards alone, 1 with the
budget, within noise. Stages 5 to 8 (the defence's answers, the coach's goals, the trainer, scouting) are held.
`eval.advantages` and `search.goals` stay off. · Source: Shaun, 10 Nov 2026 · **Ruled.**

**D-132. The engine's judgement moves to learned weights** over the existing readings (step 17). No hand-set weights:
every number comes from the rules, the cards or data. · Source: Shaun, 10 Nov 2026 · **Ruled;** step 17 builds it.

**D-133. The exam is rebuilt larger,** with answers measured by playing positions out (step 17, stage 0). The 19 hand
boards stay as a teaching set and are measured too. Where Shaun's label and the measured answer disagree, Shaun
rules. · Source: Shaun, 10 Nov 2026 · **Ruled;** the disagreements are **open** until listed and ruled.

**D-134. Board 13 is flawed:** by the cards, the lane isn't worth clearing. · Source: Shaun, 10 Nov 2026 · **Ruled.**

### Shaun, 10 Nov 2026 (step 17D prompt): the rulings on step 17's checkpoints 0 and 1

**D-135. The outcome exam** is accepted as the bigger exam for now. Defence-to-act positions are added until the
defence has at least 60 (from self-play, spread over the phases). No overnight measured-answer runs for now. · Source:
Shaun, 10 Nov 2026 · **Ruled, built** (step 17D).

**D-136. The strong-play pilot** is approved: 640 possessions by today's computer (All-Star settings, light pick
noise). The 5,000-possession run is approved only if the pilot's held-out fit clearly beats the phase average alone
(the interval apart). If the pilot says no, it is recorded as "no signal at this size", and the question is asked
again on the calibrated computer's play. Step 17D's cap is 16 core-hours, a second calibration round included; the
head-to-head may run to 1,000 pairs within it. · Source: Shaun, 10 Nov 2026 · **Ruled.**

**D-137. The over-hopeful reading is a fault to fix.** Today's reading values positions 6 to 20 points above what
they go on to earn, and the computer holds the ball and shoots late. It plays unlike basketball (System Fidelity). It
is fixed by calibrating to played-out results (`eval.calibrated`, off), not by hand. The shot-clock expiry rate in
self-play is reported beside basketball's (about 1 in 100 possessions). · Source: Shaun, 10 Nov 2026 · **Ruled;**
step 17D builds and measures it.

### Shaun, 11 Nov 2026 (step 18 prompt and go): the rulings on step 17D

**D-138. The calibrated reading is the default.** `eval.calibrated` is on by default, for every level, in both
engines. Steps 17 and 17D are merged into `main` with that default. `eval.learned` stays off; its weights stay only
for the golden tests. · Source: Shaun, 11 Nov 2026 · **Ruled, built** (step 18a).

**D-139. Shot timing is a fidelity measure.** The calibrated computer takes 72% of its shots in phases 1 and 2. NBA
teams shoot less early than the optimum: players hold the ball for a better shot and force late ones (Skinner, "The
problem of shot selection in basketball", arXiv 1107.5793: four NBA seasons; the optimal strategy would add about
0.05 points a possession). So earlier is the right direction. Shot timing is reported with every change from now on:
shots by phase, the clock-out rate, decisions a possession. Shaun's playtests judge whether it needs tempering. It
isn't tempered by hand. · Source: Shaun, 11 Nov 2026 · **Ruled.**

**D-140. Stage 2 is built on the calibrated reading.** The learned weights are held. Ask again after step 18, on the
better computer's play. · Source: Shaun, 11 Nov 2026 · **Ruled.**

**D-141. The tabletop format.** Check calibration under the table's rules (a turnover costs −5 and play continues;
the steal-foul and bonus differences in the register). Fit a separate tabletop map from tabletop-rules play if it
differs materially. Then re-measure the table's shot-clock expiry rate (10 in 100 at step 3n, D-99). If it falls to
about basketball's 1 in 100, record plan step 24 as closed. · Source: Shaun, 11 Nov 2026 · **Ruled, built** (step
18a). Measured: the table's positions go on to earn 3 to 4 points more than the app's map says, so the table has its
own map (`calibration_tabletop` in the weights file), fitted the same way on tabletop-rules play. With it the expiry
rate is 3.5 in 100 (interval 1.7 to 7.0), down from 9; with the app's map it is 0 in 200, but that map loses to the
table's own by 1.7 points a pair. **Plan step 24 is not closed** (D-99).

**D-142. Other ages and standards.** The Senior Pro map is scaled by each level's own phase table, as D-114 did for
the averages: at each phase, the scale is that level's phase table value over Senior Pro's, and what a position has
left to earn = scale × map(reading ÷ scale). Senior Pro's scale is exactly 1. Junior Amateur is checked head to head
(160 pairs against its uncalibrated self). Each level gets its own map later, once there is enough of its play.
· Source: Shaun, 11 Nov 2026 · **Ruled, built** (step 18a).

**D-143. Step 18 in two parts.** 18a: the merge, the level checks (Rookie and Starter, 160 pairs each against their
uncalibrated selves; the levels still in order), the tabletop check (today's computer first, then the calibrated one,
under the table's rules), the 19 boards on the calibrated computer (board 13 off the persistent list, D-134), and the
candidate diagnosis. Cap about 9 core-hours. Stop and report. Then the fork: if the diagnosis says the computer isn't
considering the right moves, 18b is the move prior, trained on a full-width search at 1 pair, cap 16 core-hours. If
it says judgement, 18b is the third try at the learned weights, on calibrated play (2,500 possessions, about 8
core-hours). Either way 18b waits for Shaun's go. · Source: Shaun, 11 Nov 2026 · **Ruled.**

### Shaun, 11 Nov 2026 (step 18b prompt): the order of the fixes, and the value ceiling

**D-144. The order: judgement before candidates.** 18b (settle the shot at the horizon, the ceiling, the shot-timing
test), then 18c (the defence's missing readings), 18d (widen the list by rule first, a learned prior only if a clear
loss remains), 18e (refit calibration, then ask the learned weights a third time). Reason: any learned move list
takes its labels from the search, so the search's faults are fixed first. · Source: Shaun, 11 Nov 2026 · **Ruled.**

**D-145. The value ceiling.** Shaun: "The value system is very clear. (Shot rating minus contest rating) × points
value. There aren't any shots that exceed 39 value that I know of, and that is an uncontested three pointer by the
best shooter." Step 18a reported a position reading 42.3 on board 8. A possession ends in one shot, so no position
may read above the most the possession can still earn under the rules. This is a fault, and the ceiling is a fixed
rule from now on. · Source: Shaun, 11 Nov 2026 · **Ruled, built** (step 18b, behind `eval.settle_shots`, off).
Derived (step 18b): the ceiling of a position is what the possession has already earned plus the best open shot any
attacker's card can score (points × rating; 39 on the best card, the 13 three). The rules can pay more than one
shot's value (a fouled three pays 3 × the free-throw rating, up to 54; each steal foul pays +5), but only through a
Contest or a Steal the defence chooses to make, so against the defence's best reply the ceiling stands. With Coach's
Call in play the target's shot also earns the bonus for its look.

**Still open, not ruled** (step 18b prompt): the table's own map (18a), the cost of a turnover at the table, and
plan step 24. Step 18b changes none of them.

### Shaun, 11 Nov 2026 (step 18c prompt): the app first, and the rulings on steps 18a and 18b

**D-146. The app only.** The tabletop format is on hold until the app is right. Nothing is measured, fitted or tuned
under the table's rules in step 18c or the steps after it until Shaun says so. The table's own map (18a) stays built
and untouched. The turnover cost at the table and plan step 24 stay open. · Source: Shaun, 11 Nov 2026 · **Ruled.**

**D-147. Steps 18a and 18b are merged into `main`.** Shaun approved both. · Source: Shaun, 11 Nov 2026 · **Done.**

**D-148. `eval.settle_shots`.** Check it at Rookie and Starter first (each against its calibrated self without it,
sequential, up to 160 pairs, its own pick noise). If neither level loses clearly, it is on by default for every
level, in both engines. If one loses, it stays off and is reported. · Source: Shaun, 11 Nov 2026 · **Ruled;**
**built** (step 18c). Rookie: +11.4 a pair (interval +8.8 to +13.9, 160 pairs). Starter: +2.4 (interval +0.3 to
+4.5, 160 pairs). Neither loses, so `eval.settle_shots` is on by default for every level.

**D-149. `play_on` is retired.** It is removed from the defaults and the menus, and kept in the code only where the
golden tests need it. Its one useful part, playing on while a pass is in the air, goes to 18d with board 11.
· Source: Shaun, 11 Nov 2026 · **Ruled, done** (step 18c): it is off, marked retired in `ai_profiles.json`, and
not offered by the step 18c tools. The code stays: the engines' agreement tests switch all five search parts on
together.

**D-150. Compute is estimated, not capped from outside.** From step 18c the step's own estimate, with its reasons,
is written in its `PREDICTIONS.md` before any run. Predict before every run over 30 minutes, pilot before scaling,
stop early when a sequential test decides, and say why in the report if the estimate is well exceeded.
· Source: Shaun, 11 Nov 2026 · **Ruled.**

### Shaun, 11 Nov 2026 (step 18d prompt): the rulings on step 18c, and the control rule

**D-151. A rule candidate under test, the app only: control against reaction.** Shaun: "A contest depends on control
against reaction. A Move is a controlled action. A shot following no movement or a Move is worth full rating. A shot
following a Quick Step or a Sprint has a reduced rating. Similarly, a contest following a Quick Step or a Sprint has
a reduced rating and a higher foul risk. Then a late closeout becomes worse."

- **Rushed:** the player's last movement action this phase was a Quick Step or a Sprint, whatever came between
  (Sprint, receive the ball, shoot: still rushed). Quick Step counts as rushed, like Sprint.
- **Set:** his last movement this phase was a Move, or he hasn't moved this phase. A Move after a Quick Step or
  Sprint restores control.
- **The same test for both sides,** the shooter for the shot and the contesting defender for the Contest. Phase
  boundaries reset it. Only Move, Quick Step and Sprint count as movement; a Dribble or a Screen doesn't.
- **The forced shot and its free Contest follow the same test,** with no exceptions ("it needs to be consistent").
- **The foul risk** is the existing wrong-angle foul roll: a rushed Contest takes the same roll as a Contest with
  the arrow off the shooter. No new mechanic.
- **No drive rule.** A defender who closed out hard is not made easier to beat off the dribble.
- **One size for every shot.** Shaun: "A layup at full sprint is uncommon in basketball. What would be most common
  is to use a sprint to get into an advantage position and then a move to take the layup, or a quick step and a
  move. They teach basketball youth to drive hard and then control the finish." Sizes tested: 1, 2 and 3 rating
  steps, the same for the shot and the Contest. Shaun picks.
- **Why (from 18c):** under today's rules a defender one Move away steps in during the reaction and Contests fully,
  so late help works as well as early help.
- **The app only.** Today's rules stay the default. `RULES_CURRENT.md` and the printed game are unchanged until
  Shaun rules. Nothing is changed, measured or printed for the table.

· Source: Shaun, 11 Nov 2026 · **Ruled at size 2 for the app (D-153), without the extra foul roll (D-154).** Built behind
`rules.control` in both engines (step 18d).

**D-152. Step 18c is accepted.** `eval.settle_shots` stays on by default. `eval.help_readings` stays off. Step 18c is
merged into `main`. Boards 1 and 3 are held, not retired: they are re-read under the control rule (D-151). The closer
Rookie and Starter are accepted for now, and revisited once the control rule is decided, because it reshapes both
levels. · Source: Shaun, 11 Nov 2026 · **Ruled, done.**

### Shaun, 11 Nov 2026 (step 18e prompt)

**D-153. The control rule is the app's rule at size 2.** `rules.control` plays size 2 by default in the app's format,
in both engines (D-151's rule: a shot or Contest whose last movement this phase was a Quick Step or a Sprint is 2
lower; a Move restores control). The table's rules stay as they are (on hold, D-146). Step 18d is accepted and merged.
The cases 18d listed stand as 18d read them, except the foul roll (D-154). · Source: Shaun, 11 Nov 2026 · **Ruled;
built in step 18e** (`rules.control`: `'app'` by default, `'0'` turns it off).

**D-154. No extra foul roll on a rushed Contest.** A rushed Contest takes the reduction and today's foul rolls for its
position (closer to the rim than the shooter, or level or further), with no extra roll for being rushed. Why
(fidelity): as built in 18d, a rushed Contest on a good shooter's three fouled 7 times in 20, which made contesting
worse than letting him shoot. In basketball fouls on threes are rare and hard closeouts still happen. The reduction
alone carries the loss of control. · Source: Shaun, 11 Nov 2026 · **Ruled; built in step 18e.**

**D-155. Late help from one step stays as it is.** A defender who steps in with a Move during the reaction contests
at full rating. A defender one step away is in time in real basketball too. The rule already punishes help from across
the floor (a Quick Step or Sprint). Board 3 is held: its "help early" answer may be the board's mistake, not the
rules'. · Source: Shaun, 11 Nov 2026 · **Ruled.**

**D-156. The computer is given no moves.** Shaun: "Giving it moves is me telling it an answer. The idea was to tune it
so that the answers fall out naturally. That's the difference between a generative tool and a simulation." No move
kind is named, guaranteed or favoured. The hand-written generators that choose which kinds of action the search
considers are the scripted part, and are removed: every legal action reaches the computer's own reading, and only that
reading decides what goes forward. The moves steps 18a to 18d found missing are tests of whether the answers fall
out, never instructions. Where the computer prefers something else, neither side is assumed wrong: Shaun rules on a
sense check of each. · Source: Shaun, 11 Nov 2026 · **Ruled; built behind `search.open_list` in step 18e.**

### Shaun, 12 Nov 2026 (step 18f prompt)

**D-157. The levels must think the same way.** The Rookie and the Starter must not stay on the old hand-written list.
Levels differ in how well they choose (their look-ahead, their pick noise, how many turns they read in full), not in a
scripted list. Step 18f makes the open list affordable for them. · Source: Shaun, 12 Nov 2026 · **Ruled; step 18f.**

**D-158. Step 18e is accepted.** It is merged into `main`. `search.open_list` stays on for the All-Star's defence.
Steals stay as they are: the ball is lost about as often as in basketball, and their odds are not a lever now. On
18e's five sense checks Shaun agrees with the views given: his order on the closeout board's step 1; too close to
call on its step 2; the computer's move on game EB3F5B and on the two Steal positions. · Source: Shaun, 12 Nov 2026 ·
**Ruled, done.**

**D-159. The reading is released for step 18f.** The parts the step names may change, behind switches: a one-action
turn judged before the offence replies; turns that read exactly the same; what a player's unused actions are worth;
how the offence's turns are ranked; the calibrated map (refit last). The learned weights stay held. Every fix is to
how the computer values positions, from the rules, the cards and data: no kind of move is named, guaranteed or
favoured, in the list or in the reading (D-156). Where the computer disagrees with an expected move, it is not
assumed wrong: a sense check, and Shaun rules. · Source: Shaun, 12 Nov 2026 · **Ruled; step 18f.**

### Shaun, 12 Nov 2026 (step 18h prompt)

**D-160. Step 18f is accepted.** It is merged into `main`. The tie splitter (`search.split_ties`) stays on.
`search.rank_in_hand` is on by default in both engines: it fixes a real reading error at no cost in speed. The
Rookie's Steals stay as they are; Shaun revisits the levels later. · Source: Shaun, 12 Nov 2026 · **Ruled, done.**

**D-161. Speed is judged against the previous step's code timed in the same hour,** on the same machine, because this
machine's speed varies by up to 30% in a day. Recorded in `docs/SPEED_BUDGET.md`. · Source: Shaun, 12 Nov 2026 ·
**Ruled, done.**

**D-162. Sense checks are the main gate from now on.** A fixed set of positions whose answers are measured by playing
them out by the rules with common dice (`tools/sense_set/`). A change to the reading must improve the set clearly and
break none that passed. The head to head is a backstop. Where the computer disagrees with an expected move, the
played-out answer decides, not the reading and not our expectation; Shaun rules on what is still unclear. (The step
18h prompt gives this the number D-159, which step 18f had already used.) · Source: Shaun, 12 Nov 2026 · **Ruled;
step 18h.**

**D-163. One calibrated map for each level,** fitted after the floor is fixed, from that level's own play. Step 18g
(the zone of influence) waits for step 18h, because its strength is the defender's movement left, which the floor
stops the computer from valuing. · Source: Shaun, 12 Nov 2026 · **Ruled; step 18h.**

### Shaun, 13 Nov 2026 (step 18g prompt)

**D-164. Step 18h is accepted.** It is merged into `main`. The maps for each level stay on: level evidence with better
shot timing is enough. `eval.no_floor`, `eval.exact_shot` and `eval.kept_actions` stay off. The offence's hand-written
list (it can drop an exact open shot) is opened in the step after 18g, with the sense-check set as its gate. · Source:
Shaun, 13 Nov 2026 · **Ruled, done.**

**D-165. Boards 1, 3 and 8 take their played-out answers.** The played-out answer decides (D-162). From step 18h's
sense-check set: board 1, X2 Quick Steps to D6 (28.9 against 31.4 for doing nothing and 39.0 for step 18a's choice);
board 3, nobody moves (28.4 against 32.1 and 37.9 for the board's help); board 8, O2 cuts to E10 and O1 passes to him
(39.0 against 33.0 for the cut to D7). Each board's judge in `exam.py` carries the old answer and the evidence. ·
Source: Shaun, 13 Nov 2026 · **Ruled, done.**

**D-166. The sense-check set is grown first:** about ten positions two of the defence's turns before a shot nobody
could reach, from play, to answer why only about a quarter of shots are contested. · Source: Shaun, 13 Nov 2026 ·
**Ruled; step 18g.**

**D-167. The zone of influence (app only, under test; `rules.zone`, off).** The step 18g prompt gives this the number
D-158, which step 18e's acceptance had already used. In Shaun's words (12 Nov 2026):

> "Two equal arrows on each defender, 45 degrees apart. Normal arrow rules apply. This becomes your zone of influence.
> An adjacent ball handler captured by one arrow still cannot pass through your zone of influence. The other arrow's
> reach becomes a barrier to them. It means you can contest and steal within an angle, rather than a pure direction.
> And you have two angles you can intercept through. The offensive goal doesn't change. A successful Dribble breaks
> the defender's zone of influence and takes away its move ability. Off-ball movement reduces the zone of influence
> just the same. A stagnant offence has a court covered in strong defensive influence, and you can see it diminish.
> Right now the defence can only choose to deny a driving direction or threaten a steal or a contest. Real defenders
> cover both at once: low stance to one side, force baseline, one hand defends the dribble and one defends the shot."

His rulings on the details: (1) each defender carries two arrows 45 degrees apart, each under the normal arrow rules;
the wedge between them is his zone of influence; (2) a ball handler or shooter anywhere within the wedge counts as
"the arrow on him" for a Steal or a Contest; (3) an Intercept goes through either arrow; (4) an adjacent ball handler
caught by one arrow can't pass through the zone: the other arrow's reach blocks him; (5) "Direction is the intent,
movement capability is the strength": the zone's reach comes from the movement the defender still has this phase,
and every movement he spends shrinks it; (6) a successful Dribble against him breaks his zone and takes away his
movement, as today's lock does; a broken zone is "basically gone; what is left is purely position": he can still
intercept a pass that goes straight through him, and his Contest is read as having no arrow on the shooter; (7) the
pair turns as part of a Move, not after a Quick Step alone, both together; (8) a Contest on a shooter outside both
arrows takes the wrong-angle foul roll; (9) the control rule (D-153) still applies. On strength: "It represents
smart, high pressure defence, whereas a single arrow represents amateur or low pressure defence." A stronger defence
is not a fault to fix. Nothing tells the computer how to set its zones (D-156). · Source: Shaun, 12 and 13 Nov 2026 ·
**Under test; step 18g.**

### Shaun, 13 Nov 2026 (step 18i prompt)

**D-168. What the app is.** In Shaun's words: "The app does not simulate full basketball games. It simulates the
quality of single possessions. Then it gives the chance to switch roles and improve or beat your personal goals and
each other's results." So every rule is scored within one possession, as the quality of a decision. Nothing simulates
a match. Where a match situation matters (team fouls, possessions left), the scenario sets it as context. Also in
`docs/reference/SHAUN_PRINCIPLES.md`. · Source: Shaun, 13 Nov 2026 · **Ruled.**

**D-169. Step 18g is accepted.** It is merged into `main`. `rules.zone` stays off, held, until the computer can see
"step in, then Steal". It is retested after step 18j. Cases A to E and G to I stand as step 18g read them. The zone's
levers (by level; by player, Agility 7 or more; by the coach's intent, with team fouls as the cost) wait until the
retest. · Source: Shaun, 13 Nov 2026 · **Ruled, done.**

**D-170. The zone's barrier (case F) is Shaun's exact words, not step 18g's reading.** In his words:

> "The rule should clearly be one if the arrow catches the ball handler. The other arrow restricts where he can get
> through. The ball handler can break through with a Dribble action, or can leave in another direction. Picture the
> arrows as the foot position of the defender. One is in front of the ball handler and one is up in the direction of
> the second arrow. That direction is now blocked to move past. As soon as the offence touches a square adjacent to
> an arrow, they are captured. That's where help defence on the drive is enforced even before the defence can react.
> You're set in a position to capture the offence and control them."

So: (1) the ball handler is caught the moment his movement touches a square one of the defender's arrows points at
(the square next to the defender in that arrow's direction), checked square by square, mid-movement, with no reaction
needed; (2) once caught, the other arrow's direction is barred to him: he can't move past the defender that way; he
may leave in any other direction with the movement he has left, or break through with a won Dribble; (3) "The ball
handler may hit the arrow boundary but not cross it": he may step onto an arrow's square, but not cross the arrow's
line into the squares beyond it; (4) a defender whose arrows don't catch him bars nothing. Built in `rules.zone`
(still off). · Source: Shaun, 13 Nov 2026 · **Ruled; built in step 18i, off.**

**D-171. Time is counted in phase ends.** A phase is 2 seconds and a player can arrive at any point in it, so time is
counted in phase ends: the end of the phase he arrived in, then each phase after. Two phase ends in a row are about
3 seconds; three are about 5. One method for every timed rule. Each count shows on the player as a small plain
marker, like RUSHED. · Source: Shaun, 13 Nov 2026 · **Ruled; step 18i.**

**D-172. Three seconds in the key (the app; FIBA Article 26; the offence only).** An attacker in the key at two phase
ends in a row commits a violation: the possession is over, scored as a turnover. Defenders have no three-second rule.
Behind `rules.three_seconds`; on in the app once its checks pass; `?three=0` turns it off. · Source: Shaun, 13 Nov
2026 · **Ruled; step 18i.**

**D-173. Closely guarded, and picking the ball up (the app; FIBA Article 27).** Closely guarded: a defender next to
the ball handler with an arrow on him (under `rules.zone`, a defender whose arrows have captured him). Holding after
a catch: from the catch until he moves or dribbles, if he is still holding and closely guarded at three phase ends in
a row (the phase he caught it in plus two), it is a violation: a turnover ("Stagnant basketball has consequences").
Picked up: after he has dribbled, if he goes two full phases without a Move, Quick Step, Sprint, Dribble, pass or
shot, he has picked the ball up; from then he may only pass or shoot, and the closely guarded count runs. What keeps
him active: a Move, Quick Step, Sprint, Dribble, pass or shot by him; not a team Hesitate, not a teammate's action.
The count resets when nobody closely guards him at a phase end, or when he dribbles or moves before picking up. FIBA
never counts a live dribble, which is why a pick-up needs two idle phases. Behind `rules.closely_guarded`; on in the
app once its checks pass; `?guarded=0` turns it off. · Source: Shaun, 13 Nov 2026 · **Ruled; step 18i.**

**D-174. The fouled shot, scored by FIBA (the app; Articles 34 and 38).** The shot is still a shot: rolled at its
contested rating; if it goes in, it counts. Free throws are set by the rules, not dice: 1 if the shot went in, 2 for
a missed 2, 3 for a missed 3. Each free throw is rolled against the shooter's free-throw rating. Its quality score is
the expected value: the shot's chance, plus the expected free throws for each outcome. The dice decide what happened;
decision quality is judged on the expected value, the outcome on the dice. Behind `rules.fiba_fouled_shot`; on in the
app once its checks pass; `?fouledshot=0` turns it off. · Source: Shaun, 13 Nov 2026 · **Ruled; step 18i.**

**D-175. The foul situation is set by the scenario.** In Shaun's words: "Have the tool calibrate its foul risk to a
set scenario. The team is on X fouls out of 5 with Y possessions to go in the quarter. No players are in foul
trouble, or player Z is in foul trouble. That sets actual steal calibration for both teams and is a learning scenario
that doesn't require a match worth of possessions." Scenario fields: each team's team fouls this quarter; possessions
left in the quarter; any player's personal fouls, and who replaces him if he fouls out. The cost of a foul is the
cost now (what the rules give the offence: the +5 on a steal foul; from the 5th team foul, FIBA Article 41, 2 free
throws on a foul not on a shot) plus the cost later (how much this foul raises the free throws the team is likely to
give up over the possessions left by bringing the penalty nearer: one number, from the rules and how often fouls
happen in play; and, for a player on his fifth, what is lost while his replacement plays). Not simulated. The
computer's reading uses the cost in every foul-risking action, on both sides; the coach judges the player's choice
against it. · Source: Shaun, 13 Nov 2026 · **Ruled; step 18i.**

**D-176. Not in step 18i:** charges (parked), five fouls in a whole match, shot-clock resets after fouls, defensive
three seconds, anything for the table. · Source: Shaun, 13 Nov 2026 · **Ruled.**

### Shaun, 13 Nov 2026 (step 18j prompt)

**D-177. The soft and the hard contest (the app only; `rules.soft_contest`).** In Shaun's words: "Adjacency is a form
of contest. We need to distinguish a weak contest from a hard contest. A soft contest is just position with a hand
up. A hard contest is jumping to get a hand on the ball. Good defenders are better at hard contests without fouling.
Weak contests are probably most shots outside the keyway." Keep it simple for players: no halving or mental
arithmetic; side and behind consistent with the Steal. The rule: (1) next to the shooter is a soft contest: the
defender's contest rating less 3; it never fouls and needs no action; (2) a Contest action is a hard contest: the
full contest rating; (3) from behind him (further from the rim than the shooter): 3 less again, on either kind;
(4) fouls on a hard contest: from in front with the arrow on him, no foul roll; from in front with the arrow off
him, one; from the side or behind, two, as with a Steal. A soft contest costs no action ("a free action because you
are just there"), so a reaction may spend both its actions on movement and still contest softly from where the
defender ends. Only one contest counts per shot, the defence's best. The control rule applies on top (a rushed
defender's contest, soft or hard, is 2 less). The forced shot's free Contest is unchanged. A soft contest can't be
negative; at 0 it does nothing. Player-facing words: "soft contest", "hard contest". On by default in the app once
its checks pass. · Source: Shaun, 13 Nov 2026 · **Ruled; step 18j.**

**D-178. Step 18i is accepted.** It is merged into `main`. The key is the lane as drawn (G to K, rows 1 to 6),
FIBA's restricted area. The three-second cases that don't fall out of the phase-end count stay as they are. The
capture rule's three choices stand (the barred line's length, caught for the rest of that movement, the capture
square). A player in foul trouble is left out. · Source: Shaun, 13 Nov 2026 · **Ruled, done.**

**D-179. The penalty gets its bite, the FIBA way (the app only; `rules.fiba_steal_foul`).** A steal foul outside the
penalty no longer gives +5: it costs a team foul, the defender is locked, and play goes on. In the penalty (from the
5th team foul), two free throws, as now. The table keeps its +5. The two numbers that price a foul over the quarter
are remeasured. Reason: two penalty free throws are worth about 1.6 average half-court possessions under FIBA, so
the penalty should cost more than an ordinary foul; under step 18i's rules it didn't. · Source: Shaun, 13 Nov 2026 ·
**Ruled; step 18j.**

**D-180. A scenario card that sets a foul situation plays under the app's rules.** · Source: Shaun, 13 Nov 2026 ·
**Ruled; step 18j.**

**D-181. No +5 on any foul in the app (consistency).** In Shaun's words: "You cannot have the +5 on the shot foul and
take it off the steal foul." In the app no foul carries +5: a foul on a shot is FIBA scoring, as now (D-174); a steal
foul outside the penalty is a team foul, the defender locked, play on (D-179); a steal foul in the penalty (from the
5th team foul) is two free throws, nothing more. This replaces step 18j's reading 3 (the +5 kept in the penalty). The
table keeps its +5: a deliberate difference between the formats. · Source: Shaun, 14 Nov 2026 · **Ruled; step 18k.**

**D-182. Every foul's price comes from the foul situation.** With no points on a foul, its cost is what it is in
basketball: it brings the penalty nearer. When nothing sets a foul situation, the app plays a typical mid-quarter one:
2 team fouls each, 8 possessions left. The foul's later cost is priced as built in step 18i (D-175). The screen shows
it plainly. Steals tried, steals won and steal fouls per 100 possessions are checked against basketball as a band, not
a target (NBA: about 8 steals and 8 to 10 non-shooting fouls per 100 possessions a team); nothing is tuned to hit it.
· Source: Shaun, 14 Nov 2026 · **Ruled; step 18k.**

**D-183. Step 18j is accepted.** It is merged into `main`. `search.keep_settled` is on by default in its final form.
`search.dice_in_hand` goes on by default if, under D-181 and D-182, Steals tried and steal fouls land within about
twice basketball's band and the sense-check set doesn't get worse; otherwise it stays off. `eval.ball_loss` stays off.
The contest rule's readings 1 and 2 stand (the side is level with the shooter; a hard contest from the side or behind
rolls twice even with the arrow on him), and the hard contest from the side vanishing from the computer's play is
accepted. Exam position 10's expected answer is updated to the rules: by play, stealing early on a strong dribbler and
holding back are level, so either passes. On the sense-check set, a pick among turns the computer reads level is
scored by the average of those turns played out, so a board stops passing or failing by luck. The zone waits until
after step 18k. · Source: Shaun, 14 Nov 2026 · **Ruled; step 18k.**

**D-184. The card fidelity update.** Reason: FIBA-based card audit, 14 Nov: open jump shots and hard contests on jump
shots and dunks were above real basketball; layups, dunks, floaters, post shots and free throws were faithful
(`docs/reference/CARD_AUDIT_14NOV.md`). On every card: three 10 to 9, 11 to 9, 12 to 10, 13 to 11; mid-range 10 to 9,
11 and 12 to 10, 13 and 14 to 11, 15 and 16 to 12; long two 9 to 8, 10 and 11 to 9, 12 and 13 to 10, 14 to 11;
layup 16 to 17; the Rim Runner Centre B's dunk 18 to 19; three contest 2 to 1, 3 to 2, 4 and 5 to 2, 6 and 7 to 3;
mid-range and long-two contests 2 to 1, 3 and 4 to 2, 5 and 6 to 3, 7 and 8 to 4; floater contest 3 to 2, 4 to 3, 5
to 4, 6 and 7 to 5; dunk contest 4 to 1, 5 and 6 to 2, 7 and 8 to 3, 9 and 10 to 4, 11 and 12 to 5, 13 and 14 to 6;
layup contest 11 and 12 to 10. The range table changes for those ratings and every band is recomputed from it. (The
prompt's three-point map read 10 to 8 with 9 unchanged, which put 11 A-tier cards below their B tier; Shaun chose 10
to 9 when asked.) Two new types, the app only for now, three tiers each and plain ratings: the Slashing Wing (small
forward) and the Switch Centre. No conditionals on cards. The table keeps its 25 types; the printed cards are not
reprinted now. · Source: Shaun, 14 Nov 2026 · **Ruled; card update.**

**D-185. Off balance (the app only; `rules.off_balance`).** Shaun: "A sprint closeout is easy to beat. A sprint drive
is harder to control and susceptible to losing the ball off a targeted dribble move." (1) You're rushed if your last
movement this phase was a Quick Step or a Sprint (as now), or you're locked. (2) Rushed is 2 off every rating you
roll, except foul ratings: shots, soft and hard contests, Dribble, Pass, Screen, Agility, Steal, Intercept and
Challenge. (3) A Move resets it; a locked player can't Move, so it lasts the phase. So a missed Steal, which locks the
defender, leaves him easier to drive past for the rest of the phase: that is the cost of a failed gamble. **This
reverses D-151's "No drive rule" line** (step 18d: "a defender who closed out hard is not made easier to beat off the
dribble"). One state, one marker: the RUSHED marker also shows on a locked player. The rule text: "Rushed: after a
Quick Step or Sprint, or while locked, every roll you make is 2 worse (not fouls) until you Move." · Source: Shaun,
14 Nov 2026 · **Ruled; step 18l.**

**D-186. A correction to D-184's jump-shot maps.** Reason: D-184's maps for threes, mid-range and long twos lowered
the top but left average shooters a step high, and squeezed good, decent and average shooters onto the same number.
The three ratings are re-derived for the 75 table cards from the cards as they were before D-184: three 13 to 11, 12
to 10, 11 and 10 to 9, 9 to 8, 8 to 7; mid-range 16 to 12, 15 to 11, 14 and 13 to 10, 12 to 9, 11 and 10 to 8, 9 to
7; long two 14 and 13 to 11, 12 to 10, 11 to 9, 10 to 8, 9 and 8 to 7. Then, to keep a shooting type's tiers apart on
its own shots, 20 single changes: threes `spgC` 8, `bgsC` 8, `tndC` 8, `stpfB` 8, `stpfC` 7, `scsfB` 8, `scsfC` 7,
`stsfC` 8; mid-range `spgC` 9, `bgsC` 9, `tndC` 9, `stpfC` 9, `scsfC` 9, `stsfB` 9, `stsfC` 8, `pnpB` 9, `pnpC` 8,
`stcC` 9; long twos `shsB` 10, `shsC` 9. Each band's average lands near FIBA's (threes 51 / 43 / 33%, mid-range 56 /
48 / 38%, long twos 52 / 43 / 35%: above average / average / below), no tier is out of order, and the Sharpshooter
reads 55 / 50 / 45% from three. All other D-184 changes stand; the range table is unchanged and every band is
recomputed. · Source: Shaun, 14 Nov 2026 · **Ruled; step 18l.**

**D-187. Rulings on step 18k and the card update.** Step 18k is accepted and merged as it stands (no +5 on any foul
in the app; the mid-quarter foul situation; `search.keep_settled` on; the shortlist fix and `search.dice_in_hand`
off). Its proposal to score penalty free throws at three times the rating is rejected: the cause was the open
jump-shot ratings, now fixed by D-184. The card update (D-184) is accepted and merged. The new types are named
"Slashing Wing" (small forward) and "Switch Centre". The "shooter" job threshold stays a three of 9 (on the corrected
cards that is 24 of the 75 table cards; it was 30 before D-184). Steal and foul ratings stay as they are (Shaun: "I
think the current ratings are better": a Steal is a deliberate hand in the pot, a real gamble; the game reaches more
often than basketball because a missed reach costs too little, not because of the odds of each reach). · Source:
Shaun, 14 Nov 2026 · **Ruled, done.**

**D-188. The shooter test at junior age.** The senior test stays a three of 9, as ruled (D-187). A job threshold is
carried to a younger age as the same share of the deck (step 3m): the cut that as many cards reach at that age as
reach the pro cut. On the D-186 cards no junior cut gives 24 shooters: a junior three of 7 gives 15 and 6 gives 37.
The nearest by difference was 7, and with 15 junior shooters (14 of them A-tier) coherent junior semi-pro deals
stopped existing and coherent junior pro deals fell from 37 in 100 random deals to 7. The nearest is now taken in
proportion (15 against 24 is further off than 37 against 24), which picks 6: 37 junior shooters (36 before the card
update), and junior deals as they were. No other job's cut at any age changes. · Source: step 18l, under Shaun's
"keep it at 9 unless the coherent random deals look wrong" (14 Nov 2026) · **Built; for Shaun to confirm.**

**D-189. Contest ratings restored.** Shaun: "Reducing the contest ratings was a mistake." D-184 lowered them without
tracing their effect through the modifiers built on them. Every contest rating on the 75 table cards goes back to its
value before D-184 (layup, dunk, post, floater, mid-range, long two, three), with their range entries and the chart
fixes D-184 removed. The two new types take an existing type's original contests tier for tier: the Slashing Wing
takes the Scoring Small Forward's, the Switch Centre the Defensive Power Forward's. They keep their own foul ratings.
Everything else from D-184 and D-186 stays (open jump shots as corrected, the 85% layup floor, the Rim Runner B
dunk). The anchor job's dunk-contest threshold goes back to 11 with the rating (D-184 had carried it to 5). (The
mid-range, long two and three contests are then set by D-192.) · Source: Shaun, 14 Nov 2026 · **Ruled; step 18n.**

**D-190. No card value or rule changes without Shaun's explicit agreement.** Every proposal comes with a table of every
rule and modifier it touches, and every case before and after. · Source: Shaun, 14 Nov 2026 · **Ruled.**

**D-191. Jump shots are contested by position only (the app only; `rules.position_contest`).** Shaun: "There is no
contest decision for jump shots. There is only position. Hard contest is specific to inside scoring moves."
**Jump shots** (mid-range, long two, three): an adjacent defender's contest is automatic. It takes off the card's
contest rating in full, with no hand-up subtraction: from behind, 3 less; rushed (D-185: after a Quick Step or
Sprint, or while locked), 2 less; only the best contest counts; the arrow has no effect on the shot; there is no hard
contest and no shooting foul. **Inside scoring moves** (layup, dunk, post, floater): as before, with one change. The
hand up is automatic: the contest rating less 3, never a foul. The defender may go for the full contest, with the foul
rolls as before: one from in front with the arrow off, two from the side or behind. The change: from in front with
the arrow on him, the full contest is automatic and never a foul. The choice only existed where it cost nothing, so
it wasn't a real choice (FIBA's verticality principle). The rule sentence: "Jump shots: an adjacent defender's
contest is automatic and set by position. Inside shots: you may go for the block and risk the foul, except straight
up from in front with your arrow on him, which is automatic and safe." · Source: Shaun, 14 Nov 2026 · **Ruled; step
18n.**

**D-192. New jump-shot contest ratings** (Shaun agreed to test them; **replaced by D-194, 15 Nov 2026**). For mid-range, long two and three contests, one
map on Shaun's original values, on every card including the new types (from the source type's originals): 2 to 1, 3
and 4 to 2, 5 and 6 to 3, 7 and 8 to 4. Card by card: `docs/reference/JUMP_CONTESTS_14NOV.md`. The reason: with one
automatic contest the card number is the whole contest, and a professional's hand up on a jump shot takes about 5%
(weak) to 20% (elite) off, about 10% for an average defender. The range for all three: average from 2, above average
from 3. Inside contests stay at Shaun's original values. Contest ratings don't change with the level. · Source:
Shaun, 14 Nov 2026 · **Ruled, to be tested; step 18n.**

**D-193. Nothing is zero** (Shaun's ratings rule: 5% is the lowest). A contesting defender always takes at least 1
off the shot, after every modifier (behind, rushed, the hand-up 3). Built with D-191, under the same switch. · Source:
Shaun, 14 Nov 2026 · **Ruled; step 18n.**

**D-194. The square defender (replaces D-192's ratings; the app only).** Shaun's evidence, from a live NBL game:
"Kristian Doolittle defending guards like Tyler Harvey on the 3 point line. They physically could not get a shot off
over him unless they made a move first." Real tracking data only counts shots that were taken, so it hides the shots
a square defender takes away. The 18n test measured beaten defenders. **Jump-shot contests go back to Shaun's
original values** (before D-184) on every card; the new types take their source types' originals, as D-189; the
`con_mid`, `con_long` and `con_three` ranges and chart fixes are back in their form before D-184. **One contest
table for every shot, set by position:** in front with his arrow on the shooter, set: the full rating. In front with
the arrow off, or beside: the rating less 3. Behind: the rating less 6 (less 3, and 3 more from behind). Rushed
(D-185): 2 more off, wherever he is. Always at least 1 (D-193). **Jump shots:** that is the whole rule: no choice and
no shooting foul (D-191 stands). **Inside shots:** as in 18n: when he isn't square the defender may go for the block,
with the foul rolls as they were. In effect the only change from 18n is that on a jump shot a defender who isn't
square takes 3 less, and a square one takes his full original rating: the arrow now matters on jump shots.
**Not taken from step 18n's report:** halving the block's foul roll, and rushed taking 1 off jump-shot contests. Both
would make one modifier mean different things on different rolls. The block stays a live choice for low-foul
defenders who get in front. **Step 18n's open case 1 stands as built:** with no contest action, a defender may use
both reaction actions as movements to reach a jump shooter. Shaun may rule on it later. · Source: Shaun, 15 Nov 2026
· **Ruled; step 18o.**

**D-195. The setup must fit the players (restates D-70 and D-71).** Shaun's playtest: two post scorers, poor outside
shooters, stood on the low wings with X4 and X5 next to them, arrows on, and the lane was empty for a drive once the
point guard was beaten. "Help defence appears broken." The cause: both sides' setups were improved by the quick
reading from a fixed start (each defender next to his man; the offence on the table's squares), never judged by
play, and the setup offered to a human was the table's fixed squares whatever his cards. **Ruled:** setup placements
are judged by the search's own played-out reading, both sides, every level, and the proposal shown to a human; they
are searched without a fixed starting answer, and nothing names or favours a placement; arrows are part of every
placement and every direction can be played out; in the app the setup offered to a human by default is the engine's
proposal for his cards (the fixed squares stay for the table format); setup stays inside its time budget. · Source:
Shaun, 15 Nov 2026 · **Ruled; built in step 18o behind `setup.search` (`?setup=search`) and left off: played out,
it gives up 6.8 more points a possession than the setup as it was (2.8 to 10.7), because the engine has no reading
that can judge a setup (docs/reports/STEP18O_REPORT.md). Awaiting Shaun.**

**D-196. Shaun's rule for Fable: the pillars before the simulations.** "The computer simulations lie. If the computer
cannot set up the offence and defence properly and cannot do it based on goals then no play that comes from it can
be trusted. I let it set up as it wills and it left a clear lane through the middle for a layup with nothing in
between. That means the metrics vs real basketball are garbage." (1) Trust the design pillars more than the
computer simulation data: System Fidelity first; then Neutrality, Player Agency, Legibility and Accessibility may
bend but never break. (2) Fable's sole job is to plan, then fix in logical order, what the computer is poor at or
can't do at all. (3) Anything that clearly meets the whole design hierarchy stays on; if the data doesn't fit, the
starting assumption is always that the computer is wrong. (4) Fidelity is questioned only after proving the
computer is not wrong, and only after a factor for human error is accounted for. (5) Human error may be modelled on
elite chess engines measured against semi-pro chess players, because professional basketball relies heavily on
physical traits, not purely on basketball IQ. (6) The primary target is senior pro level; other levels are rolled
out as each part is locked in. (7) Use what is needed for proof, and no more. **In practice:** the FIBA comparison
is not a gate until the computer is proven to play properly; computer-against-computer play-outs are only proof
when both sides play the position properly (else: a stronger search for the side in question, or forced lines);
D-191, D-193 and D-194 stand, with Shaun's original contest ratings, and the Contest foul ratings are unchanged
(Shaun: "No"). The zone (D-167) goes on by default in the app; the old setup is made to keep its time;
`setup.search` stays off until the reading can judge a setup. The full text is at the top of
`docs/reference/SHAUN_PRINCIPLES.md`; the plan it asks for is `docs/plans/COMPUTER_FIX_PLAN.md`. · Source: Shaun,
15 Nov 2026 · **Ruled; step 18p.**

**D-197. The system of feedback loops: the scout informs the goals, the goals dictate play, for both sides.** "I'd
like to get to a point where the offence and defence reads are intelligent. Scouting informs goals. And goals
dictate intelligent play for both sides. For example, a constant defensive goal might be to limit future passing
options. Protecting access to the middle of the court might fall out from such goals. Fluid goals might be things
like 'deny all passes to O2' and 'if O2 gets the ball contain the three point shot and force a drive, pass or
contested two pointer'. Then you get a scout that informs the goals for both teams that informs decision making for
smart offensive and defensive computers. That's the goal. That's the system of feedback loops. And I need you to
map the full system to basketball fidelity and perfect it iteratively." With it Shaun agreed the three decisions of
the step 18p report: the race to the rim is built as a new part of the reading; design checks 7, 8 and 9 are
confirmed; the step 18o and 18p pull requests are merged. **In practice:** the map is `docs/plans/SYSTEM_MAP.md`. A
goal in the engine is a measure read off the board by the rules, a side that wants it up or down, and a source
(constant, or switched on by the scout): it never names a move (D-156). One measure is added or mended at a time,
proved by design checks on forced lines (D-196), and only then used by the layers above it. · Source: Shaun, 15 Nov
2026 · **Ruled; step 18q builds the first measure (the way to the rim, `eval.lane`, `?lane=1`).**

**D-198. Fouls and turnovers are priced in points, and play goes on; no shot from the rim square.** (1) Fouls and
turnovers are priced in points. A foul is +5 to the offence and play goes on. A steal is −5 to the offence and play
goes on: the possession doesn't end. "The steal is a lesson: 'keep showing me what you've got.' A team shouldn't
spend ten minutes on a possession only to end up on minus points because the defence got lucky." Every other
turnover is also −5 with play going on: an intercepted pass and the violations (three seconds, closely guarded, the
shot clock). (2) After any turnover the current phase ends and the next phase begins. After an intercepted pass the
passer gets the ball back and the defender goes back to the square and arrow he started the phase on. (3) A shooting
foul is +5 plus its free throws. (4) The +5 replaces step 18i's foul pricing, which priced a foul by how it brings
the penalty nearer; that pricing is retired. (5) Why: Playmaker is a game about shot quality. The teams swap and the
defence's aim is to beat the offence's shot quality score; after a turnover the pressure is on the offence to win
those points back with an even better shot; fouls must sting enough to really hurt a team's chance of winning the
possession battle, if the other team stays honest. (6) The risk tolerance must fall out, not be set by hand: a reach
should be a rare decision when the foul risk is bigger than the chance of a steal, and when a miss can get the
defender beaten and open up valuable driving lanes. (7) The rim square: no shot from directly under the rim; the
offence must choose a side to put the ball up, even for a reverse layup. **As built (the app only, as every ruling
since D-190; `rules.points_play_on`, `rules.no_rim_shot`):** with every foul priced at +5 there is no penalty for
team fouls (no free throws from the 5th), which is how point 4 is read; the defender who fouls on a steal is still
locked (D-179); a turnover in the last phase, and the shot clock running out, end the possession on what it has
banked, which can be below 0; the counts of three seconds and closely guarded start again after a turnover; in the
possession's first phase "where he started the phase" is where he stood when the defence's turn began. D-179's and
D-181's free throws in the penalty are replaced. · Source: Shaun, 16 Nov 2026 · **Ruled; built in step 18r.**

**D-199. The coverage map is the computer's reading for both sides.** Shaun's design (the blueprint,
`docs/reference/COVERAGE_MAP_BLUEPRINT.md`): "The defensive coverage map is the gold here. Where the zone of
influence lies, what it protects, and what weakens it. Regular snapshots reveal how it is weakening and where you
can attack it." "The goal of the offence becomes gaining the best possible shots (open layups are always high for
most players) by finding efficient strategies to weaken the defence's zone of influence and attack or pass the ball
to the zones that remain weak at the start of the next phase. So every phase looks to maximise the weakening of
defensive influence first and attack the created weakness such that the next phase begins with the defence in a
weaker position than the last. Exploiting matchup advantages and offball movement achieves that, with offball
movement and screens designed to weaken defensive influence for the ball-handler to attack the rim or pass, or
shoot with the defence in a weaker position this phase and next phase." "Conversely, the defence is trying to
maintain the strength of their zone of influence or improve it for the next phase. If we look at zone of influence
as the protection of high value areas and facilitation of low value areas something interesting may fall out. Rank
each of the court zones by value, with the short range green area highest, then three pointers, then mid-range and
long range 2 pointers last and have the zones of influence protect shot in those areas maximally and preferentially
and denying driving lanes through the middle may fall out." "We've already established that no decision making
involves a single attacker and a single defender. Defenders are covering multiple weaknesses at once. And attackers
need to understand who helps their defender when they gain a positional or trait-based advantage." **The one
refinement agreed:** a square's value is not ranked by hand; it comes from the cards of the attacker who could shoot
there. **Agreed with Shaun before the build (16 Nov, "Go"):** (1) "a defence can't cover two at once" is worked out
from the rules (what is left after the defence spends the tokens it has), not fitted; (2) the fitted map is kept out
of the coverage map's path, and anything fitted is fitted on forced lines; (3) two stops: first the map, the coach
view and design checks 1 to 6, in the fast engine, so Shaun can judge the map by eye before anything uses it; then
the search and setup read it, checks 7 to 9, and the port to the other engine; (4) the 18o closeout position is
replayed under D-198 before it is a check, and check 8 is pinned to named positions. · Source: Shaun, 16 Nov 2026 ·
**Ruled; stop one built in step 18s.**

**D-200. The speed budget is waived until the computer is smart enough.** "Speed budget be damned. I'll address
speed if it works." And: "I honestly don't care about speed yet. It is not a working app. It won't be for a while. We
need to find the right way to make it smart enough and then worry about speed at the end." Build it right first.
Speed is still reported, for the record; correctness is not traded for it and the timing test does not block the
work (it is not loosened either). Speed comes back once the map is proven. · Source: Shaun, 16 Nov 2026 · **Ruled.**

**D-201. Position at a phase's start: the rules stay as they are.** No new modifier, and no limit on the reaction.
"Positioning barely matters at the start of a phase. Correct. What matters is how you influenced the zones of
influence on the previous phase to gain advantages and impact the zone of influence on the next phase. The offence
always gets to move first, so the example is weak. If you didn't take advantage of the play in the previous phase
then you have to start fresh but hopefully in a better position. You were either trying to get a shot or trying to
improve your situation for the next phase, or both." A defender recovering during the shot is the offence stagnating
and indecisive, and the defence holding its shape. The strength measure (the addendum,
`docs/reference/COVERAGE_MAP_BLUEPRINT_ADDENDUM_STRENGTH.md`) is what captures it: design checks 3 and 5 are judged
by that measure, not by a defender's square at a phase's start. · Source: Shaun, 16 Nov 2026 · **Ruled.**

**D-202. The button reads "Coverage: shown / hidden".** It is Shaun's word (D-199). "coverage" comes off step 3n's
list of engine words a player never reads (`playmaker_engine/plain.py`): it was an engine word then; it is the
designer's own name for the map now. · Source: Shaun, 16 Nov 2026 · **Ruled; built in step 18s, stop two.**

**D-203. The heat map is fixed first and turned on for both sides, no matter what.** Shaun: "We fix the heat map first
and turn it on for both offense and defence, no matter what. It needs to account for the offence and defence's ability
to move and rotate arrows where applicable. It needs to map out gaps in the defence's coverage and when only one
defender can defend potential threats from multiple offensive players, it rates that highly." The map is on by default
for both sides at the end of step 20, whatever its checks say. Exam position 15, and any other check the map fails,
becomes an expected failure with the reason "Shaun, 17 Nov: the map is on; judged by his playtest". Every failure is
reported plainly. The speed budget stays waived (D-200); no rule or card value changes (D-190). · Source: Shaun, 17 Nov
2026 · **Ruled; built in step 20.**

**D-204. Each side's logic is the lasting gap.** Shaun: "Once we fix the whole phase assessment and logic of the heat map
the logic for each team falls out fidelity wise. Something like, the offence attempts to produce lasting gaps in the
defence's coverage such that no defender can cover a valuable scoring square, or one defender has to cover multiple
squares accessible to multiple offensive players. Conversely, the defence is trying to limit those scenarios as much as
possible, and if it has to allow such squares and scenarios to exist, it will aim to leave the lowest possible value
ones." The lasting gap is what the offence can still force after the defence's best answer: the best open threat, or the
threat an overloaded defender must leave, whichever is higher. It is the defence's strength (D-201): lower is stronger.
Nothing else is added to either side's logic (D-156). · Source: Shaun, 17 Nov 2026 · **Ruled; built in step 20.**

**D-205. Shaun's playtest is the gate, not the data.** Shaun: "Once we fix that system, we turn it on (I don't care if the
data suggests failures), and I test it to see if it plays more like real basketball." · Source: Shaun, 17 Nov 2026 ·
**Ruled.**

**D-206. Every move serves the lasting gap; the map reads each side as it really is.** Shaun: "Take the data and use it
to fix the errors in the application and logical use of the zone of influence map for both offence and defence.
Everything has a purpose to meet those goals." And: "I've noticed a few unusual things that don't happen in regular
basketball. An example is a beaten defender. Let's say X1 is beaten by a drive to the basket by O1 and a screen set by
O5. Other defenders help and cover O1, but X1 does not chase the driver, and it does not move logically to cover an
offensive threat left open. Instead, I witnessed it stay in no-mans land and settle for defending a passing lane to an
already closely defended O2 while the offence has a 3 on 2 advantage in and near the keyway." And: "So some logic is
having it take the local coverage it can reach this turn as opposed to assuming the offence won't shoot yet and
recovering the overall defensive coverage for future phases." Ruled on step 20's decision 1: the computer reads the
defence with what it actually has left this phase (its tokens and movement, who is locked or rushed, who has already
moved); a spent or beaten defender can't recover inside the phase, and the map says so. The reports keep the
like-for-like read for phase starts only, where both sides really are fresh. Overloads count numbers: a group of
defenders who are the only cover for more attackers than there are defenders (one on two, two on three, three on four),
worth the best look the defence's best assignment leaves. A pass in the air is read with the ball where it is and the
catch by the rules' own chance. No rule tells a defender to chase or recover (D-156): recovery must fall out of a
reading that counts what is left open. Read in step 21 as: the defence as it really is, the offence still with its full
turn to come (D-204's like for like, which the ruling leaves standing for the offence): with its tokens spent the offence
still moves first next phase, before the defence can answer again (step 21's B2 showed the map losing every look that
needs a pass next phase when the offence's spent tokens were read too). Shaun to confirm (STEP21_REPORT, decision 1).
· Source: Shaun, 17 Nov 2026 · **Ruled.**

**D-207. Rotation falls out of the map; no defender is tied to his man.** Shaun: "It should also be able to consider
defensive rotation. Though it needs to come logically from the way it reads zone maps and future phases. When one
defender is beaten, does the way the defenders read the map lead to defenders considering switching primary assignments
to more quickly cover the created holes in the zone maps. For example, the defender left in the open is 2 phases away
from reaching the defender in the gap, but X2 can get there now, while X1 is able to at least cover the passing lane to
O2 until the next phase. Defensive communication becomes organic." Defenders cover looks, not players: the defence's
answer matches all five defenders against every look, and the search always tries that answer's moves, so a switch is
simply the answer that leaves the least. · Source: Shaun, 17 Nov 2026 · **Ruled.**

**D-208. Variety at All-Star's setup.** Ruled on step 20's decision 2: the setup chooses among the placements within the
level's variety margin (All-Star: 2 points) each possession, as its turns already do. · Source: Shaun, 17 Nov 2026 ·
**Ruled.**

**D-209. The Screen rule stays as it is for now.** Ruled on step 20's decision 3: rerun S3 once by forced lines after the
map reads the defence as it really is. If the screen pays, the rule was right; if not, it is reported with the evidence
and Shaun decides. · Source: Shaun, 17 Nov 2026 · **Ruled.**

**D-210. The map reads the offence's whole first turn of the next phase.** Shaun: "Just ask it to fix it. Merge it. And
let me test it." The map used to read to the next phase's start plus one movement. It now also sets up looks a receiver
reaches with the next phase's first two actions (the move, then the catch or the next move), with the defence's answer
between them: the drive that draws help, the kick that finds the gap, the screen that pays after the move and the pass.
· Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22.**

**D-211. The three-second rule's -5 is counted in the map and the search.** An attacker in the key who can't move out
this phase owes the turnover's cost, so the offence stops giving it away. · Source: Shaun, 18 Nov 2026 · **Ruled; built
in step 22.**

**D-212. The offence's search tries the moves that make the map's looks.** The computer sometimes picked a move its own
map read as worse because the search judged the defence against offence replies that didn't include the moves that make
the map's best looks. The offence's candidates now always include, for each of the map's top looks and overloads, the move
or pass that makes it. · Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22.**

**D-213. The defence's setup is the map's own best answer to the offence's placement.** It starts from the hug and moves
any defender to any empty square with any arrow, the five read together, keeping each change that lowers the lasting gap
(the defence's answer during the phase counted), until nothing lowers it. The offence's setup is judged against that
defence, not a quick man-to-man, and the setup gets eight times the level's decision time in the digital format.
· Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22.**

**D-214. Position and arrows are judged by what they do.** Shaun (playtest, 18 Nov 2026): defenders still picked odd
spots and arrows, and the offence hesitated, drifted and set empty screens, because the map only scored the top look and
every other choice was a tie broken by list order. For every defender the map now records what his position and arrows
protect (the looks only he covers, the passing lanes his arrows cut, the paths his body stands on) and what they allow,
all from the map's own values (the cards, the rules' chances), never from a named zone, spot or direction (D-156).
· Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22b.**

**D-215. Ranked drivers for both sides, each deciding only when everything above it is level, no weights.** Defence: (a)
the lowest top look (the lasting gap); (b) the offence's least likely actions: its best looks need its riskiest actions
to reach, by the rules' own chances (a walled lane needing a dribble beats an open lane a sprint reaches every time);
(c) efficiency: the fewest defensive actions to recover or rotate; (d) no attacker's best action pulls two defenders onto
him. Offence, the mirror: (a) the highest top look; (b) the safest actions to reach it; (c) the fewest offensive actions
to make it; (d) one attacker's action pulls two defenders onto him. Used in setup, in each side's search and in the
map's reading. Shaun swapped (b) and (c) after the first build left the ball handler unguarded for efficiency's sake:
"X1 leaving the ball handler for E7 breaks basketball fidelity (D-196: the computer is presumed wrong): an unguarded
ball handler gets a free sprint into the paint, and the map can't yet see the collapse and kick-out that follow."
· Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22b.**

**D-216. Setup searches all five players on each side together, over every square and arrow.** · Source: Shaun,
18 Nov 2026 · **Ruled; built in step 22b.**

**D-217. The screen stops the path around it, for the body and the arrows alike.** Shaun: while a defender stands on a
screen's T square, any of his arrows pointing diagonally around the screener (the direction the screen already stops
him stepping) projects nothing: it walls no drive and jumps no passing lane that way. His other arrow, and all other
directions, work as normal. His contest is unchanged: he can still fully contest an immediate shot if square. The block
ends the moment he leaves the T square, wins a Challenge, the screener moves, or the phase ends. Built in both engines;
the board draws a blocked arrow dashed with a "blocked" mark. Cases these lines don't settle, read the way closest to
"the screen stops the path around it", are marked for Shaun in the step 22b report. · Source: Shaun, 18 Nov 2026 ·
**Ruled; built in step 22b.**

**D-217 (addendum).** Shaun, 18 Nov 2026: the four screen cases of the step 22b report stand as read. In particular, a
screened defender with his diagonal arrow blocked walls no drive at all, because a wall needs one arrow to catch and the
other to bar: a screened defender can't wall the ball handler, which is what a ball screen does. · **Ruled.**

**D-218. The defence's two responsibilities (Shaun's model).** Shaun: "The defender's primary responsibility is their
assigned player. Contain their player's options within an acceptable shot quality that evolves throughout the
possession. If your player is a poor shooter, passer, dribbler, then you care less about containing those things. Your
secondary objective is to protect high value zones of the court with poor coverage. Regardless of whether that position
can be reached in the next phase or actions. And it is ranked by the average shot quality of all the offensive players
compared to the square that would be left with no zone of influence. You are therefore deciding the pull between high
value squares with little to no zone of influence cover, and your player's immediate threat this phase. A beaten
defender loses their defender responsibility only once another defender takes that responsibility, so what they do
naturally is target the highest value gap in the defensive zone of influence, unless they pick up a new defensive
responsibility on the way." "A beaten defender only stops the chase once another defender takes responsibility or
switches responsibility for that player. At that point a defender with low to no player responsibility moves to fill
their new role while using their arrow directions to limit passing and driving lanes as normal. So they recalculate. I
must chase my assignment if no other defender takes the responsibility. Or if it is switched, I move to my new location
as quickly and as effectively as possible using my arrows to influence offensive options." "The Green zone naturally has
a very high, unguarded shot quality value, mid range lower and long range 2 lower until the 3 point line bumps value
back up. This naturally creates the pull of these zones stronger." "My player has the ball, he's X% my responsibility vs
ZOI gap coverage, up to 100% if a high value shot is available. A poor shooter might demand only 40% coverage at the 3
point line vs responsibility to cover the high value green squares that aren't protected. That all governs position.
The arrow direction then restricts offensive ball movement through passes or ballhandler movement to higher overall
weightings between those two aspects." Built as the defence's reading of a position, in both engines, in points from
the cards and the rules: (a) each attacker's best look as the defence stands, before it answers (value times reach by
the rules' chances; a wall he can only pass by winning a Dribble is priced at the Dribble's chance); (b) every
square's gap: the average of the five attackers' best open shot there, less what the best-placed defender's contest
takes off as he stands; a square nobody influences keeps its full value, whether or not anyone can reach it this
phase. · Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22b.**

**D-219. One list, settled across the team; it replaces ranked drivers b to d.** The attackers' looks and the squares'
gaps go into one list, largest first. The defence places all five together to leave the lowest highest item, then the
next, and so on (compared best first: no weights, no sums, no set percentages); efficiency (the fewest actions) breaks
any tie left; the offence reads the same list and plays to raise it. The settlement never turns on the order the
defenders are listed in (ties go to the square, the arrow, the card, never the defender's number). Used in setup (all
five over every square and arrow, nobody starting anywhere), in the map's own answer, in the turns the search reads as
level, and in the coverage view. **A choice Shaun's words didn't settle, made on the checks and marked for him:** what
leads the search's reading at the end of a line. With step 20's lasting gap leading (D-204), the defence drifted off the
shape its own setup chose and swapped men when nothing had changed; with the list's largest item leading, it held. So
the list leads (`eval.map_lead: "list"`; `"gap"` puts the lasting gap back). The lasting gap is still read and shown.
· Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22b; the lead is awaiting Shaun's playtest.**

**D-220. Assignments, chasing and switching.** Every defender has one assigned attacker, from setup's matchups. He keeps
him until the reading hands that man to another defender, which it does only after the defence's own actions and only
when it leaves strictly less uncovered; on a tie everyone keeps his man. Shaun: "There is also the disadvantages of
switching defenders. Moving them reduces your zone of influence. So switching defenders regularly weakens the defence.
Switching has to improve the overall defensive coverage to be worth it." A switch, like any repositioning, is judged
after the moves it takes: the search plays the real movements (the tokens, the Move used, the rushed rolls, the arrow a
Sprint leaves) before the list is read. Among turns that read level, the defence takes the one where each defender
alone contains his own man best (his first responsibility: this is what makes a beaten defender chase), then the one
with no switch, then the fewest actions. The coverage view names it: "X1 beaten: chasing O1." "Switch: X4 takes O1; X1
picks up O5." "X2 sags off O2 to cover the squares around I4." · Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22b.**

**D-221. Arrows are settled with positions.** Each placement the settlement reads in full is read with all eight
arrows, by the rules (the walls an arrow makes, the lanes it can jump, the contest it squares), never by a named
direction. · Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22b.**

**D-222. The map counts the reaction's own off balance.** A choice Shaun's words didn't settle, marked for him. A
contest a defender reaches standing or by one Move finds him set; one he needs a Quick Step or a Sprint for finds him
off balance by the rules (D-185: every roll 2 lower). The map used to read both the same, so a defender six squares
away covered a shot as well as one beside the shooter, and the settlement packed the paint. The map now applies the
rule, in both engines; it is no rule or card change (D-190). It moves the lasting gap's numbers too (Shaun's board:
18 before, 24 now). · Source: step 22b, for Shaun · **Built; awaiting Shaun.**

**D-223. Shaun's rulings on step 22b.** D-219 stands: the list leads the search, both sides; the lasting gap setting
stays available but off. D-222 stands: off balance is counted in the map (a contest reached by a Quick Step or Sprint is
rushed, by D-185). The other choices stand as read: walls count in reach, not in a square's gap; one defender per
contest; the map's reach for "this turn"; a lost Dribble costs nothing banked; assignments are read again only after
the defence acts. On check 1 (nobody guards the ball handler) Shaun accepts the settlement's logic on his board: "A rim
protector closely guarding a pass first point guard at the 3 point line is very susceptible to being beaten and then
protection for the drive is weak." · Source: Shaun, 18 Nov 2026 · **Ruled.**

**D-224. Stagnation is counted in the list.** Shaun: "Other than foul risk, the biggest factor is limiting ball handler
movement. Play stagnation. You're winding down the clock. Such that an offence with no good options that is stifled
everywhere else and the paint is clogged by a rim protector is right." "Pressure defence restricts movement. Movement
restricts access to clean passing lanes." Built in both engines, both sides, in points by the rules, no weights: (a)
**the Steal** as the defence stands, on whoever holds the ball on a square: a defender next to it with an arrow on him,
or one a Move takes next to it; kept on Dribble less Steal or under, else -5; a foul is +5 (D-198); the defence only
tries where that favours it, so it never counts above 0. (b) **The closely guarded count** (D-173): a ball handler who
holds where he stands, closely guarded when the phase ends, is one phase end nearer the -5: counted at how far along
the count's three that puts him (a third, two thirds, all of it); a live dribble isn't counted, as the rule has it. (c)
**The shot clock running down:** a square's gap, the long view, counts only while some attacker can still get there in
the phases the clock leaves, by the rules' movement (now part of the race, D-228); as the clock runs down the court the
offence can still use shrinks, so a position where nothing is open reads worse for the offence the later it is.
**Marked for Shaun:** his words asked for (c) from the game's own phase values. That table (step 3n, 16 self-play
possessions a level on a 12-second clock) rises with the phase, 24.9 at the first to 29.5 at the last, so counted as
written a late possession would read better. I counted the clock by the rules instead. Setup also tries every defender
on each square next to the ball handler with each of the eight arrows (the list read with bodies and walls counted, the
best read in full), since the quick re-read can't see what pressure takes: the Steal, the count, a wall across his way.
· Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22c; (b) and (c) ruled to stand (D-232).**

**D-225. A zone never blocks a pass (a clarification of the rules as the code already has them).** A defender's wedge
restricts the ball handler's movement only (D-170). A pass is stopped only by a Steal from the defender next to the
passer, an Intercept by a defender jumping the lane elsewhere, or denial next to the receiver. D-167's words "cannot
pass through your zone" mean move past, not throw through. No rule changed; the register, the help and two code comments
now say so. · Source: Shaun, 18 Nov 2026 · **Ruled.**

**D-226. Two defenders helping count as a takeover.** When teammates already cover a beaten defender's man between
them, his man is taken. Beaten: a Dribble won against him this phase, or locked, or his man has the ball nearer the rim
than he stands. The helpers are the teammates who take something off that man's best look; between them they must leave
him less than the beaten defender alone would. The beaten defender then picks up what the helpers left: one of their
own men, whichever leaves every defender covering his own man best. While the help still has his old man, the
assignments don't go back. The coverage view names it: "X4 and X5 have O1: X1 picks up O5." Assignments are read again
when the defence's turn is done and no pass is in the air, not after each of its actions.
· Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22c.**

**D-227. The Watch replay shows the new lines** (each defender's job, switches, takeovers, chases, sags), the same as the
live coverage view. · Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22c.**

**D-228. Zone gaps are a race.** Shaun, on X3 guarding an empty wing and X5 covering three looks from nowhere: "Is one
phase enough? A phase is only 2 seconds." A square is a gap only when an attacker can get there with the ball before
any defender can arrive to contest it. Both sides' phases are counted by the rules (movement, the pass, the reaction),
over as many phases as the race takes, up to the shot clock. Its value is that attacker's shot from the square at his
real chance of winning the race, less the contest the first defender to arrive brings. A square every attacker loses
the race to is not a gap, however valuable. This replaces D-218's "the average of all five regardless of reach". No
fixed horizon, no hand-set weights. Built in both engines: a defender who can be set on the square (standing, or one
Move) by the phase the attacker arrives wins the race; one who can only get a hand up off balance (the reaction's Quick
Step or Sprint, D-222) brings that contest; the ball handler has the ball at 1, anyone else at the pass's chance by the
rules as the defence stands, a lost pass -5 (D-198). **Marked for Shaun, choices his words didn't settle:** a tie in
phases goes to the defender (he is set as the shot goes up); bodies and walls on the way aren't counted in the long
race (nobody stands still for it), nor is a Dribble past a wall; the pass's chance is read as the defence stands now,
not as it will stand when the attacker arrives; the late contest is counted from in front.
· Source: Shaun, 18 Nov 2026 (a revision during step 22c) · **Ruled; built in step 22c.**

**D-229. A contest one Move away counts as set (D-222 stands).** Shaun: "Move is a controlled action. So it is set.
The offence only has to move away to where the defender can't reach though. A lazy offence that just shoots like that
deserves to be contested. That's why you have to create shots with advantages." No change. · Source: Shaun, 18 Nov 2026
· **Ruled.**

**D-230. A defender's man is named by who is nearest.** Shaun ruled on step 22c's choice 5: the attackers, in order of
the best look each has open, each take the nearest free defender who takes something off that look (a tie: the one who
leaves him less, then the lower square); an attacker nobody free takes anything off gets the nearest free defender. It
replaces naming whoever covers his most valuable look from afar. With assignments standing, a switch is still called
only when the named matchups cover more (D-220); the takeover (D-226) is unchanged. · Source: Shaun, 18 Nov 2026 ·
**Ruled; built in step 22d.**

**D-231. Sense checks 2 and 3 are measured by position.** Check 2: a defender stands in the key while a poor shooter has
nobody beside him. Check 3: the pass to the Sharpshooter is cut (its chance by the rules is below certain). They replace
the job lines' words. · Source: Shaun, 18 Nov 2026 · **Ruled; built in step 22d.**

**D-232. Step 22c's other choices stand as built:** the shot clock counted by the rules, not the phase-value table
(D-224 (c)); the closely guarded count in thirds (D-224 (b)); a tie in a race goes to the defender (D-228); setup's
longer last pass (D-200 waives speed). · Source: Shaun, 18 Nov 2026 · **Ruled.**

**D-233. The setup plan: the order.** Shaun: "First comes the scout for both teams." "Once we have the location and
matchup based scout locked for both teams, both teams can calibrate their phase by phase shot tolerance tailored to
those matchups to determine exactly what matchups they want to chase and avoid in preference order." "The offence sets
up first, assuming the defensive matchups that will be generated, by positioning the players in a way to create the
advantages needed to generate the first preference shot with backup shots planned for if that fails." "Then the defence
sets up. We keep everything that has been working for us." The design is `docs/reference/SETUP_PLAN_BLUEPRINT.md`. It
replaces setup's old order, where the defence's logic came first and the offence was judged against a quick defence.
· Source: Shaun, 19 Nov 2026 · **Ruled; built in step 24.**

**D-234. The game, and each side thinks alone.** Shaun: "You're managing attention, then creating holes, then
exploiting ways to access those holes. That's the game. The defence is trying to manage holes and constrain the offence
away from accessing them when they form." "Ideally, the defence and offence computers would be separate such that they
do not have access to each other's goals and thinking." Each side's computer uses public information (the board, the
rules, all ten cards) and its own scout, goals, plan and predictions. Where it needs the other side's reply it runs its
own model of that side. Built: each side's scout, plan and predictions are kept in that side's own memory; a test
changes one side's private plan and checks the other side's choice on the same board is the same.
· Source: Shaun, 19 Nov 2026 · **Ruled; built in step 24.**

**D-235. The scout.** The shot review: every attacker, shot type and defender, in every case the contest rules tell
apart: 14 for a jump shot, 22 for an inside shot (the blueprint's table; tested case by case against the rules). The
movement review: Shaun: "beating a defender with a dribble is more valuable where it provides the offence with more
passing and driving angles and space to create separation without going away from the hoop. Near the middle at the
three point line is great for that. In the green zone is poor." Measured, not ranked by hand: the two players alone,
the coverage map read before the Dribble and after a win; what the win is worth is how many of his squares get better
and by how much in all. **Marked for Shaun:** I measured "how much his options grow" as that sum over squares. His
best shot this phase is a different number and goes the other way (in the paint a win turns a contested layup into an
open one). · Source: Shaun, 19 Nov 2026 · **Built in step 24; the measure awaits Shaun.**

**D-236. Tolerance, the plan and the placement.** The bar for a phase is what playing on is worth from it: the lasting
gap read with the shot clock that phase would have, by the rules (D-232); nothing in the last phase. The acceptance
spec is the scout's cases at or above the bar. The plan is read from the map one phase ahead (the predicted defence and
its first answer): the look left after the defence's best answer, the defenders who could take it away and what holds
each, a screen on the ball handler's defender where one builds more, the branch (the map read again with the condition
failed), the backups. The placement's one measure is that plan's value at its real chance, then the rest of the list,
then efficiency. **Marked for Shaun, choices his words didn't settle:** (a) a candidate square is one where the
attacker's open shot is worth more than the offence can always get against one defender set in front of it; (b) the
plan holds one phase of conditions, measured again each phase, not a written three-phase path; (c) the variety margin
of the level applies to the placement as before (D-208). · Source: Shaun, 19 Nov 2026 · **Built in step 24.**

**D-237. The defence's matchup rule (step 23's item 1, built here because step 23 was not merged).** Everything that
works is kept: the settlement by the list. Then, among the ways of standing that leave no more than the level's
variety margin above it: the mismatch priced where it hurts (the chance each attacker's Dribble beats his defender
times what a win opens on his square), then like against like (by position), then matching numbers. **Marked for
Shaun:** I did not have step 23's prompt. The margin and the price are my reading of this step's words.
· Source: Shaun, 19 Nov 2026 · **Built in step 24; awaits Shaun.**

**D-238. In play and the scout's updates.** Shaun: "Think about if the defence does something silly and leaves an open
pass and driving lane. The layup's value might not be better than the open three, but it is guaranteed rather than
relying on a successful screen." Opportunities are compared by value at their real chance (the list's value times
reach). Each phase the offence measures its plan on the real board: still chasing it, taken away, or something worth
more. The plan only breaks ties between turns that read the same. Between possessions only a side's predictions of
the other side's choices change: the same unpredicted matchup two possessions running. **Marked for Shaun:** two. A
setup has no dice; one sighting can be the level's variety. · Source: Shaun, 19 Nov 2026 · **Built in step 24; the
count awaits Shaun.**

**D-239. The setup screen.** Shaun: "Also, implement in the game the UX and functionality to match. A clear button to
have the computers manage offensive setup and one for defensive setup is a must. At the moment I don't think it manages
offensive setup properly." "have it clear the annoying defensive zone of influence before the defence has even set up".
Built: "Computer sets up the offence" and "Computer sets up the defence" in every mode, each placing a draft the player
can change, and its next-best on a second press; the plan and the defence's read beside the board; role squares with
Coverage on; no defender, reach, zone or arrow drawn while the offence places; a side's plan shown to that side only.
· Source: Shaun, 19 Nov 2026 · **Ruled; built in step 24.**

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
Shaun, 9 Nov 2026: settled by the step 10 marks (1, 7 and 11 fixed; 10 kept).

**D-97.** Board 14 (variety): at depth 4 one first action wins every time, because the noise and the variety margin are
smaller than the value gaps a deeper search finds. The depth-6 run was not done.
Options: widen the variety margin; restate the board; accept it. Effect: how predictable the All-Star is.
Shaun, 9 Nov 2026: accepted; the judge is restated (see the step 10 marks).

**D-108.** Exam candidate (from Shaun's playtest reports): the defence denies an elite shooter's catch (the old
`test_deny_catch`). · Source: Shaun, step 6 prompt · **Open:** to be added as an exam board in step 12.
Shaun, 9 Nov 2026: keep (met in step 9).

**D-109.** Exam candidate (from Shaun's playtest reports): the offence prefers a clean pass to a contested one (the old
`test_passing`). · Source: Shaun, step 6 prompt · **Open:** to be added as an exam board in step 12.
Shaun, 9 Nov 2026: fix: rebuild so the clean pass is clean and the other contested (step 10).

**D-111.** Exam board 6 (catch window) is marked as an expected failure: Contest as an action (D-18) changed the
reading; re-based with the exam in step 12. · Source: Shaun, step 7 prompt · **Open:** step 12.
Shaun, 9 Nov 2026: keep, judged by D-94 (step 10).

**D-112.** The trainer test "an early cut is flagged with a legal reorder" is marked as an expected failure for the same
reason; re-based with the exam in step 12. · Source: Shaun, step 7 prompt · **Open:** step 12.
Shaun, 9 Nov 2026: keep; re-base after the goals step (still an expected failure).

**D-113.** The trainer test "the credit names the helper who answered the decoy" is marked as an expected failure for the
same reason; re-based with the exam in step 12. · Source: Shaun, step 7 prompt · **Open:** step 12.
Shaun, 9 Nov 2026: keep; re-base after the goals step (still an expected failure).

### Step 13: the phase table

**D-92.** The phase table rises from about 25 in phase 1 to about 29 in phase 6 at Senior Pro, and as the leaf's floor it
flattens marginal positions.
Options: use the table only where the board read has no look; blend it with the read; keep it. Effect: the computer's
sense of the clock and the trainer's flags (D-100).
Shaun, 9 Nov 2026: settled in step 13, with exam evidence.
Shaun, 10 Nov 2026: ruled: `relative` by default (see "the position value against the average", step 11).

### Step 14: the levels

**D-98.** The levels are closer than the old anchors assumed: All-Star beats Starter only a little (match score 0.47),
and the trainer can't tell the levels apart by decision quality (each loses about 0.8 points a decision).
Options: widen the profiles (D-67); grade with a searched reply; accept closer levels. Effect: what Rookie, Starter and
All-Star mean to a player.

### Step 15: the shot clock

**D-99.** Shot-clock expiries at the table: 10 per 100 possessions (`BASELINE.md`), against about 1 in basketball.
Step 18a (D-141): 9 in 100 before calibration; 3.5 in 100 (interval 1.7 to 7.0) with the calibrated reading and
the table's own map. Still open.
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
