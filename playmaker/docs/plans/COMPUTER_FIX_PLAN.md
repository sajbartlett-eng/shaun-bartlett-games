# The computer fix plan (step 18p, D-196)

Written before any fix, from what steps 18n and 18o found, Shaun's playtests, and four exact checks run for this plan
(`docs/runs/step18p/`). It lists everything the computer is poor at or can't do, in the order it must be fixed.

## The rule this plan works under (D-196)

- **The design pillars come before the simulation data.** If the data doesn't fit, the computer is presumed wrong.
- **Computer against computer is only proof when both sides play the position properly.** Where one side's play
  is in question the proof is a forced line or a stronger search for that side.
- **The FIBA comparison is not a gate** until the computer is proven to play properly.

## The design checks: the gate for every stage

From the pillars and basketball, not from the data. Each is a check on what comes out, never an instruction or a
weight in the engine (D-156). A stage is done when its checks fall out, both engines agree and the speed budget
holds.

| # | Check | Stage that must make it fall out |
|---|---|---|
| 1 | A clear lane from the ball handler to the rim, with no defender able to get between, is bad for the defence, and the offence takes it. | 1 (read), 2 (played) |
| 2 | A square, set defender in front is worth more to the defence than one beside or behind. | 1, 2 |
| 3 | An arrow that walls a drive, or covers a passing lane the offence wants, is worth more than one that covers nothing. | 1, 2 |
| 4 | An open layup in an empty lane is worth about what the card says. | 1 |
| 5 | The offence places players where their cards are worth something; the defence answers the players in front of it. | 3 |
| 6 | Setup and play follow the goal set for the possession. | 3 |
| 7 | **Confirmed by Shaun, 15 Nov 2026.** Stepping next to a ball handler who can't get away is worth more to the defence than standing off him. | 1, 2 |
| 8 | **Confirmed by Shaun, 15 Nov 2026.** A defender who can reach the ball handler and reach for the ball is read the same wherever he starts from: the reading of a reach doesn't depend on which square he came from. | 1 |
| 9 | **Confirmed by Shaun, 15 Nov 2026.** The same position reads the same for both sides: what the offence thinks a lane is worth is what the defence thinks it costs. (Neutrality.) | 1 |

How each check is tested: a named position on Shaun's board of 15 November (and its mirror on other cards), the
candidates played by **forced lines** for the side in question, and the reading compared with the played result.
Never by self-play averages alone.

## What is wrong, with the proof so far

### A. The reading (what the computer thinks a position is worth)

| Fault | Proof |
|---|---|
| **It looks one turn ahead and no further.** A drive that finishes next phase reads as nothing. | Shaun's board after the point guard beats X1. Before the Sprint into the empty lane the reading is 21.6; after it, 13.8. Played out, that position scores 27.8 (26.4 to 29.2). The reading holds a part that sees the layup ("the ball handler's best paint look next phase": 34) and doesn't use it. |
| **A longer search doesn't cure it.** | Asked to look 4 turns ahead (88 seconds, 35 times its normal time) the search still reads the drive at 24.0 and stepping aside at 25.4. All 4 turns fall inside the same phase. |
| **The fitted map flattens every difference.** It is fitted on the computer's own play, where good and bad positions end up scoring alike because the computer doesn't press them. | The All-Star's map turns 10 points of reading into 2 to 4 points in the first three phases. With the map off the same search reads the drive at 17.7: worse, not better. So the map hides the fault; it doesn't cause it. |
| **Every off-ball arrow reads the same.** | 18o: all 8 directions of all 4 off-ball defenders read 25.17 at the start. Follows from the first fault: an arrow only matters to a pass or drive more than one turn away. |
| **X1 beside the ball handler reads 6 points better than in front.** | Run for this plan: once the offence waits, a reach by X1 reads the same from every square (18.6 to 18.9). The difference is in the search: after the ball handler moves away it does not weigh the defender stepping after him and reaching, except from that one square. A search fault, stage 2. |
| **The All-Star pauses on the closeout** where stepping next to the shooter wins the ball 9 times in 16. | 18o's set. Nothing in the reading counts what standing next to a ball handler is worth (check 7). |
| **The quick reading rates a packed lane best.** | 18o's 48 deals: the setups it picks give up 6.8 more (2.8 to 10.7). That number stands. |

### B. In-play

| Fault | Proof |
|---|---|
| **The offence doesn't take an open lane.** | Shaun's board after the beat, X4 and X5 next to their men: by its own choice the offence scores 22.2 (16.3 to 28.1); made to Sprint into the lane it scores 27.8 (26.4 to 29.2). After the Sprint it still takes 2 to 4 turns to finish. |
| **The defence doesn't help, and isn't square.** | With X4 and X5 in the lane the same drive scores 22.2 (18.0 to 26.5): help is worth about 5.6. In 18o's test 52 of 56 drives finished with no square defender, and X4 and X5 never stepped into the key. |
| **The search doesn't follow the ball handler with a step and a reach.** | Fault A5 above. |

(The first two rows correct step 18o's report, which filed its sense-check play-outs under the wrong candidates.
The corrected tables are in `docs/reports/STEP18P_REPORT.md`.)

### C. Setup

- Centres start on the three-point line (121 of 200), non-shooters' defenders next to them (365 of 415), X1 leaves the
  lane open. Nothing in setup comes from goals.
- The setup built in 18o (searched from nothing, judged by the reading) is 6.8 worse by play, because of fault A.
- The old setup ran 4 to 6 seconds over its time (fixed in this step, Part 2).

### D. To check, not yet shown to be faults

- **The block is never tried.** By the cards it pays only from in front with a Contest foul rating of 5 or lower.
  To check that the search weighs it when it does pay. Stage 2.
- **No mid-range shot, long two or dunk in 400 possessions.** To check against forced lines whether that is right
  on these cards. Stage 2.

### E. Later

- Human error (after the computer plays properly). The zone is on from this step. The levels follow senior pro.

## The order, and why

Shaun's expected order is confirmed, with one change: **two faults he listed under the reading are search faults**
(the step-and-reach, the block), so they sit in stage 2.

| Stage | What | Depends on | Proof it needs |
|---|---|---|---|
| **0** | Do now: the zone on by default on the fast engine; the old setup keeps its time. | nothing | Speed on a phone-sized budget; the two engines agree under the zone. |
| **1** | **The reading.** Each part of the reading keeps its own worth, fitted to what positions went on to earn, in place of "the best single look this turn" and the flattening map. The parts already include the layup next phase, the looks after the defence's cover, and who has moved. | 0 | Checks 1, 2, 3, 4, 7, 9 on forced lines: the reading of each named position against its played result. |
| **2** | **In-play.** The offence takes the lane; the defence gets square, helps, walls and closes out. Most of it should fall out of stage 1. What doesn't is a search fault: the step-and-reach, and whatever the checks show. Then D (the block, the missing shots). | 1 | Checks 1, 2, 3, 7, 8 played, with the side in question forced or given a stronger search. |
| **3** | **Setup,** from the players and the goals. `setup.search` goes on once the reading can judge a setup; then the goals work that was held. | 1, 2 | Checks 5 and 6; the 48 deals replayed. |
| **4** | Human error. | 1 to 3 | |
| **5** | The comparison with real FIBA basketball at senior pro, fidelity questioned where a gap remains. | 4 | |
| **6** | Levels. | 5 | |

**Why the reading is first:** the search can only choose what the reading tells it is better. Every other fault here
is either caused by the reading (the lane, the arrows, help, setup) or can't be shown to be fixed while it is blind.

## How stage 1 fits the reading without learning the flaws (D-196, "choose and justify how")

Fitting to the computer's own play learns its flaws: it never drives, so a lane is never seen to pay. Two things
break that circle.

1. **Play that the computer wouldn't choose is put into the data.** In the play the fit learns from, a share of the
   turns are drawn at random from all the turns the search weighed, not only its first choice. Nothing is named or
   favoured: every weighed turn is as likely as another. So the Sprint into the lane, the step next to the shooter
   and the arrow on a lane are all played and their results recorded. A position is only used once no drawn turn
   follows it, so what it "went on to earn" is the computer's own play from there.
2. **The fit is repeated.** Each fit changes how both sides play from every position, so the play is run again
   with the new reading and fitted again, until the design checks hold and the reading stops moving. The first
   fit learns "the lane pays"; the second learns what the lane is worth once the defence, reading the same thing,
   starts to close it.

The weights are data (principle 7): fitted, with their uncertainty, never set by hand.

**What would make me stop and ask:** if the checks can't be made to fall out with the parts the reading already
has, the reading needs a new part (for example what standing next to a ball handler is worth). A new part is a new
measurement from the rules, not a weight, but it is a design choice about what the computer looks at, so I will
name it and ask before building more than one.

## After stage 1's first attempt (15 Nov 2026)

The plan's method for stage 1 was tried and failed its gate (`docs/reports/STEP18P_REPORT.md`). What changes:

- **Fitting the parts the reading already has is not enough.** With a turn drawn at random in the play, 320
  possessions and 4,360 positions, the fit gives "the layup next phase" almost no worth, and no design check falls
  out. A second round would play the same way as the first, so it was not run.
- **The missing part is the race to the rim.** A player who Sprints can't move again until the next phase, and the
  defence may still have up to 5 actions in that phase. Whether a defender gets between the ball and the rim in
  time is settled by the movement rules. The reading measures the layup against the defenders where they stand,
  as if none would move.
- **Stage 1 now reads:** (1) add the race to the rim as a part of the reading, played out by the movement rules
  the way a declared shot's reaction is; (2) refit the map on play where lanes are taken; (3) the design checks
  by forced lines. This waits on Shaun's word (decision 1 of the step 18p report), because it changes what the
  computer looks at.
- **Exam position 1 is design check 1,** the defence's side of it: a man on the line from the ball to the rim when
  the straight drive is worth 34. It fails. Its pass in 18n rested on self-play and is not counted.
- **The baseline the next attempt must beat** (the zone on, 16 play-outs each): with the lane open the offence by
  its own choice scores 25.1 (20.1 to 30.0) and chooses the Sprint 0 times in 16; made to Sprint it scores 26.9
  (21.6 to 32.1); with help in the lane, 22.5 and 23.4.

## After stage 1's second attempt (step 18q, 15 Nov 2026)

Shaun agreed the race to the rim as a new part of the reading and confirmed checks 7 to 9 (D-197). The whole system
this plan serves is now mapped in `docs/plans/SYSTEM_MAP.md`; this plan is its order of work.

**Built (off by default, `eval.lane`, `?lane=1`):** the way to the rim, from the movement rules. The ball handler's
movement this phase and one movement the next, against each defender's movement left this phase and the reaction;
bodies and barring arrows as they stand; what is left after the defence's best single step into it; the chance a
Dribble takes the on-ball defender out of the race; and the off-balance finish.

| Check | By the reading | By play (forced lines) |
|---|---|---|
| 1, the defence's half: a clear lane is bad for the defence | Holds: 25.1 against 23.2 with help. | Holds: help costs the offence 3.8 and 6.7 (16 play-outs a line; before, 2.6 and 3.5). |
| 1, the offence's half: the offence takes it | The sprint no longer reads as nothing (25.1 before and after). | **Fails:** made to sprint 27.8, by its own choice 22.0. |
| 2: in front beats beside or behind | Holds: 24.2 against 25.1. | Not played. |
| 3: an arrow that covers | Not shown (what the search shows is the reach). | Not played. |
| 4: an open layup is worth about the card | Holds only off the rim square (see below). | |
| 9: both sides read the same | Holds (one measure). | |

**What changes in this plan:**

- **Help must come from the setup.** On Shaun's board no big can get behind the on-ball defender in one turn, so
  nothing the defence does in play changes the reading. Stage 3 (setup from the goals) is now the next stage, judged
  by the lane ("who is behind the on-ball defender").
- **The offence's half of check 1 needs the drive's effect on the other four defenders.** Thirteen of sixteen forced
  sprints ended in a kick-out three. The reading sees the lane; it does not yet see what collapsing the defence
  opens. This is the passing measure (iteration 2 of the map), and it is built with stage 3.
- **Two things that are not the computer, for Shaun to rule** (step 18q report, decisions 1 and 2):
  - **The reach** wins the ball 1 time in 4 and is the defence's best turn by about 5 points whenever a defender
    stands next to the ball handler with his arrow on him. No defensive goal outweighs it.
  - **The rim square** (I2) can never be faced square: every contest there counts as from behind.
- **The lane stays off by default** until the setup uses it and the offence's half of check 1 holds.

## After the agreed rules (step 18r, 16 Nov 2026)

Shaun ruled D-198 and set the order: the agreed rules first, then the offence takes an open lane (with what a drive
opens for the other four), then the lane read inside the speed budget, then setup judged by the lane, then passing
options and the rest of the map.

**Built:** fouls and turnovers in points with play going on, the phase ending after a turnover, no shot from the
rim square, 18i's foul pricing retired (the app only; `docs/reports/STEP18R_REPORT.md`).

**What the rules settled without a ruling:**

- **The reach.** 0.80 a possession before, 0.07 after, with nothing set by hand. On Shaun's board it is no longer the
  defence's best turn.
- **The rim square.** No shot from it, so the contest that could never be square is gone.

**The baseline every later stage is judged on** (Shaun's board after the beat, forced lines, 16 a line, the lane
reading off):

| Line | Points |
|---|---|
| Lane open, the offence as it chooses | 27.3 (25.0 to 29.7) |
| Lane open, made to sprint into it | 27.1 (25.2 to 29.1) |
| Help in the lane, the offence as it chooses | 19.9 (16.4 to 23.3) |
| Help in the lane, made to sprint into it | 24.8 (22.7 to 26.8) |

- **Design check 1, the defence's half, holds by play:** help is worth 7 points and the ranges are apart.
- **The offence's fault is now exact:** against help it settles for a three 16 times in 16 and scores 19.9; made to
  drive and kick it scores 24.8. It doesn't read what a drive opens for the other four.

**What is new on the list:**

- **Speed under the new rules.** A steal or an intercepted pass no longer ends the line the computer reads, and its
  slow decisions run over at every level. First in the next step, with the lane's speed.
- **The refit makes the reading flatter.** Refitted on play under the new rules, the maps fail exam position 12 and
  were not kept. The flattening map (fault A3) is now in the way of any refit; it goes with the reading work of
  the offence stage.

## After the coverage map, stop one (step 18s, 16 Nov 2026)

Shaun's design (D-199): the coverage map is the reading for both sides. Agreed before the build: two stops. Stop one
is the map, the coach's view and design checks 1 to 6, in the fast engine, so the map can be judged by eye before
anything plays from it. Speed is waived for now (D-200).

**Built:** `engine.js coverage`: for every attacker and square, what the look is worth with nobody on it (value, from
his card), the chance he has the ball there when the next phase starts (reach, by the rules' own pass and movement),
what the defence takes off it (influence) and what is left (weakness); who covers it and who is next; the defence's
best answers inside the tokens it has; one line of words. A snapshot is kept for each phase. In the app:
"Defence map: shown / hidden" (the name is a decision in the report). Nothing in the computer's play reads it yet (`docs/reports/STEP18S_REPORT.md`).

**What the map is built from, and what it leaves out.** The game's own movement, pass, contest and reaction rules.
No fitted map is in its path. Three approximations, stated in the code: an off-ball attacker gets one movement before
the catch; an arrow's bar is taken at its present length, and a defender who steps bars his new arrow's first square
only; the defence's answers are chosen one action at a time, each the best left.

**Design checks by the map (Shaun's board):** 1 to 5 fall out. 6 falls out for a body on the helper's way and not for
the Screen action (it bars only a diagonal step; the helpers on this board travel straight).

**Three things the map showed that the reading has wrong or lacks:**

- **The reading's pass chance is not the rules'.** `decide._lane_p` (and the fast engine's twin) lets any defender who
  can step onto any square of the pass's line take the pass, the on-ball defender next to the passer included. On
  Shaun's board it reads every pass at 1 in 4. By the rules the passes to O3 and O5 can't be intercepted, and the one
  to O2 arrives 3 times in 10. This is likely the root of "the offence against help settles for a three" (18r) and
  of passes being undervalued everywhere. The map uses the rules' own chance. The reading is mended at stop two, in
  both engines, with its own proof.
- **At a phase's start, where a defender stands next to a shooter hardly matters.** The reaction gives a fresh
  defender two actions, enough to get square in front from beside or behind. Position and arrows count through
  reach, an arrow's bar, a lane he can jump, and when the tokens are gone (in front 12, beside 21, behind 24 for the
  sharpshooter's three).
- **The reading priced a shooting foul without D-198's +5.** Mended in both engines (they agree).

**Stop two, in order:** the search and the setup read the map (and the reading's pass chance is replaced by the
rules'); checks 7 to 9 on forced lines, the 18o closeout position replayed under D-198 first and check 8 on named
positions; then the port to the other engine. Whatever must be fitted (the cost of waiting a phase) is fitted on
forced lines only.
