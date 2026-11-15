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
| 7 | **New, for Shaun to confirm.** Stepping next to a ball handler who can't get away is worth more to the defence than standing off him. | 1, 2 |
| 8 | **New, for Shaun to confirm.** A defender who can reach the ball handler and reach for the ball is read the same wherever he starts from: the reading of a reach doesn't depend on which square he came from. | 1 |
| 9 | **New, for Shaun to confirm.** The same position reads the same for both sides: what the offence thinks a lane is worth is what the defence thinks it costs. (Neutrality.) | 1 |

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
