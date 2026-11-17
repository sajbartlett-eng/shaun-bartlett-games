# The system map: scout, goals, reads, play (step 18q)

Shaun, 15 Nov 2026: "Scouting informs goals. And goals dictate intelligent play for both sides. ... Then you get a
scout that informs the goals for both teams that informs decision making for smart offensive and defensive
computers. That's the goal. That's the system of feedback loops. And I need you to map the full system to
basketball fidelity and perfect it iteratively."

This is that map. It says what each part is in basketball, what already exists in the code, what is proven, what is
missing, and the order to perfect it. It works under D-196: the design pillars come before simulation data, and
every stage is gated by design checks, never by self-play averages.

## 1. The loop

```
 the cards and the rules
        |
        v
   1. THE SCOUT            who each player is, and what each matchup gives or gives up
        |
        v
   2. THE GOALS            what each team is trying to make happen, or stop, this possession
        |                  constant goals (always) and fluid goals (from the scout, the lineup, the clock)
        v
   3. THE READS            how far the board is from each goal, measured by the rules, in points
        |
        v
   4. THE DECISIONS        setup, then each turn: the search plays both sides against those reads
        |
        v
   5. WHAT HAPPENED        the shot, the stop, the habits each side showed
        |
        +--> back to 2 inside the possession (a goal is reached, lost, or the clock calls)
        +--> back to 1 between possessions (the scout learns what this opponent does)
        +--> back to 3 between versions (the reads are corrected where play proves them wrong)
```

Both teams run the same loop on the same reads. What the offence thinks a thing is worth is what the defence thinks
it costs (design check 9, Neutrality).

## 2. What a goal is here, so that it is never a rule of thumb

Shaun's goals design (signed off 10 Nov, `docs/reference/GOALS_DESIGN.md`) stands: a goal is an advantage to create,
keep and convert; the defence mirrors it (prevent, break, deny, concede, run the clock down).

To keep that honest under D-156 (no kind of move named or favoured, no hand-set weights), every goal in the engine
has the same three parts and nothing else:

| Part | What it is |
|---|---|
| **A measure** | A number read off the board by the game's own rules (movement, contests, passes, tokens, the clock). In points. |
| **A side** | The offence wants it up, the defence wants it down. |
| **A source** | Constant (it is there every possession) or fluid (the scout, the lineup or the clock switched it on, with a worth). |

A goal never says "sag", "deny" or "drive". It says what is being measured. The move that serves it falls out of the
search. That is how "it depends" stays true: the same goal produces different play on a different board.

### Constant goals (both sides, every possession)

| Basketball | The measure | State |
|---|---|---|
| **Protect the middle** (defence). **Attack the middle when it is open** (offence). | The ball handler's way to the rim: the best paint shot he can reach by the end of next phase, after the defence's best single step into it, each defender given the movement he has left. | **Built this step** (`eval.lane`). Shaun's "protecting access to the middle might fall out" is this measure. |
| **Limit future passing options** (defence). **Keep two ways to score alive** (offence). | For every teammate: the chance the pass arrives times what his look is worth after the catch, now and one pass further on. | **Half built.** The reading has each receiver's look after a catch and the pass's chance this turn. It does not look one pass further, and an arrow on a lane reads the same as an arrow on nothing (design check 3, off the ball). **Next iteration.** |
| **No look above what the possession is worth** (defence). **Find one** (offence). | Each attacker's best shot after the defence's best answer this turn. | Built (the reading since step 3m). Its known faults are in `COMPUTER_FIX_PLAN.md`. |
| **Use the clock** (both). | What an average position is worth at this phase, and the tokens left. | Built (the phase table). |

### Fluid goals (from the scout, for this opponent)

Shaun's examples, and what each is as a measure:

| Shaun's words | The measure the goal pushes | What must exist first |
|---|---|---|
| "Deny all passes to O2." | O2's worth after a catch, times the chance a pass reaches him. The defence pushes it to nothing. | The passing-options measure (above), and the scout naming O2 as the man whose catches cost most. |
| "If O2 gets the ball, contain the three and force a drive, pass or contested two." | With O2 on the ball: the worth of his three against the worth of his drive and of his passes. The defender's square and arrow decide which is left open. The goal is the lowest of the three being the one he is left with. | The lane measure (built), the square-defender contest (D-194, built), the passing measure (next). Then this falls out with no new rule: the search already picks the square that leaves the least. |
| "Attack their weakest defender." | The matchup's edge: the attacker's rating for a shot against that defender's contest of it, where it pays. | The scout's matchup table as numbers (exists for the team sheet: "hunt" and "protect"). The 'mismatch' advantage is built and switched off. |
| "Pull their rim protector away from the rim." | The lane measure with that defender out of reach of it. | Built this step: a defender who cannot get between no longer lowers the lane. |

A fluid goal is a constant measure aimed at one player with a worth from the scout. No fluid goal needs its own code.

## 3. Layer by layer: what exists, what is proven, what is missing

| Layer | In basketball | In the code now | Proven | Missing |
|---|---|---|---|---|
| **The scout** | The personnel report: who shoots from where, who can't, who to attack, who to hide. | `scouting.py`: each player's strengths and weaknesses from his card, team lines, the matchup table, "hunt" and "protect" (the largest shot edge by position), shot charts. The opponent's habits can already be fed to the search. | The words trace to the cards (step 3d tests). | It describes and stops there. It sets no goal. It needs to hand the goals numbers: each attacker's worth by spot against the man on him. |
| **The goals** | What the coach asks for this trip down the floor. | Step 16: the four advantages measured from the board (space, mismatch, numbers, a way into the paint), each with its stage and worth; the goal potential; goals ordering the search; holding a goal until another clearly beats it. All switched off. | The measures agree in both engines. | They were built on a reading that looked one turn ahead, so they could not see what they were for. They go back on, one at a time, as each read under them is proven. |
| **The reads** | What a coach sees when he freezes the film. | Each attacker's shots (now, after a move, after a catch), the defence's best answer to each, the phase table, the fitted map. New: the way to the rim a phase on. | See section 5. | One pass further on. What standing next to a ball handler is worth. Off-ball arrows. |
| **The decisions** | Setup, then the possession. | The search (both engines equal), the defence's open list (every legal action is read), setup by the old method (`setup.search` is off). | Speed budget on desktop. | Setup from goals. The step-and-reach after the ball handler. |
| **The feedback** | Adjusting during the game, and the next scout. | Goal switching inside a possession (off). A habit hook in the search. The fitted map between versions. | | The scout updating from what the opponent just did. |

## 4. The basketball fidelity map

What each piece of real half-court basketball is carried by in the rules, and whether the computer reads it.

| Basketball | Carried in the rules by | Read by the computer |
|---|---|---|
| Stay between the ball and the basket | Bodies stop movement; an arrow's line bars the ball handler who touches the other arrow (D-167, D-170). | **Yes, from this step** (the lane measure counts bodies and arrows that bar the way). |
| Help defence, protect the rim | A body on the way; a contest from in front. | **Yes, from this step.** One hole in the rules is flagged in the report: a shot from the rim square itself can never be faced square. |
| A square defender takes the jump shot away | D-194: in front with the arrow on him, the full contest; else 3 less. | Yes (since 18o). |
| Close out under control | D-151: a contest after a Quick Step or Sprint is 2 lower. | Partly. The All-Star still pauses where stepping next to the shooter wins the ball (open fault). |
| Attack before the help arrives | Tokens: a defence that has spent its tokens can't step in until the next phase. | **Yes, from this step** (the lane counts each defender's movement left). |
| Don't rush the finish | D-185: a shot straight after a Quick Step or Sprint is off balance, 2 lower. | **Yes, from this step** (a lane he must sprint down is worth less than one a Move away). |
| Deny a passing lane | An arrow along the lane; the Intercept; the pass's chance. | This turn only. Off-ball arrows all read alike (open: next iteration). |
| Drive and kick, help and recover | The helper's man is open for a catch when the helper steps in. | This turn only. The 'numbers' advantage is built, off. |
| Screens | The screen rule; a screened defender's movement is stopped. | The lane measure uses each defender's exact movement, so a screened helper can't get between. Untested. |
| Mismatch, post up | The cards' ratings and bands. | The 'mismatch' advantage: built, off. |
| Spacing | Where the other four stand: what each catch is worth, and which defenders it pulls out of the lane's reach. | In play: partly, from this step. In setup: no (open fault C). |
| Shot selection | Points times (rating less contest). | Yes. |
| The shot clock | Phases and tokens. | Yes. |
| Fouls and the bonus | The foul rolls, the bonus. | Yes. |
| Rebounding, the fast break | Not in the game: a possession is one half-court trip and ends with its shot. | Outside the design. |

## 5. The order to perfect it, one loop at a time

Each iteration adds or mends **one measure**, proves it by design checks on forced lines, and only then lets the
layers above use it. Nothing above is switched on over a read that fails its checks.

| # | Iteration | Design checks that gate it | State |
|---|---|---|---|
| 1 | **The middle.** The way to the rim as a measure, both sides. | 1, 2, 4, and the on-ball half of 3. | **This step.** Results in `docs/reports/STEP18Q_REPORT.md`. |
| 2 | **Passing options.** What each pass is worth now and one pass on; an arrow on a lane the offence wants. | 3 (off the ball), and new check 10. | Next. |
| 3 | **On the ball.** The defender's square and arrow against this ball handler: what he takes away and what he leaves. The step next to a ball handler who can't get away. | 7, 8, and new check 11. | After 2. |
| 4 | **The scout sets the fluid goals.** The scout's numbers switch goals on with a worth; goals order the search; every computer turn can say which goal it served (Legibility). | 6, and new check 12. | After 3. |
| 5 | **Setup from the goals.** | 5, 6; the 48 deals replayed. | After 4. |
| 6 | **The scout learns.** What the opponent did last possession changes the next goals. | A forced-line check per habit. | After 5. |
| 7 | Human error, then the comparison with real basketball, then the levels. | D-196, points 4 to 6. | Last. |

### New design checks, for Shaun to confirm

| # | Check |
|---|---|
| 10 | A defence that leaves the ball handler one safe pass is better placed than one that leaves him three, the shots after those passes being equal. |
| 11 | Against a ball handler who shoots the three well, the defence's best square for his man is closer to him than against one who can't. It falls out; it is not told. |
| 12 | When the scout marks one attacker as the man to stop, the defence gives up more to the others than it does with no mark, and less to him. |

## 6. How each iteration is proven (D-196)

- A named position, the candidates played by forced lines for the side in question, the reading against the played
  result. Never self-play averages alone.
- Both engines equal. The speed budget holds.
- Shaun's playtest is part of the proof.

## 7. The coverage map (D-199, step 18s)

Shaun's design of 16 November makes one object of section 2's measures: the coverage map. For every attacker and
square it holds value (from his card), reach, influence and weakness, who covers and who is next, and a snapshot each
phase. The constant goals are read off it: "protect the middle" is the weakness of the squares by the rim, "limit
passing options" is the reach and weakness of each teammate's squares, "no look above what the possession is worth" is
the largest weakness left after the defence's best answers. Stop one (step 18s) builds it and shows it to the coach.
Stop two has the search and the setup read it, in place of the lane measure of iteration 1 and the passing measure of
iteration 2. The order in section 5 stands from iteration 3 on.
