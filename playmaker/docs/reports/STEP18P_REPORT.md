# Step 18p report: the plan, a correction, the zone on, and the reading's first fix stopped with its reason

## In five lines

1. **A correction to 18o, and it goes your way.** I filed 18o's sense-check play-outs under the wrong candidates.
   Filed properly, the straight drive into the empty lane scores 27.8 (26.4 to 29.2), not 20.2; help in the lane
   brings it down to 22.2; and the computer's own offence gets only 22.2 from the same spot. Your read of your
   playtest was right: the lane is worth a lot, help matters, and the computer does neither.
2. **Done now:** the zone is on by default in the app and runs on the fast engine. The old setup keeps its time (it
   ran 4 to 6 seconds over; it is now within about 0.2 seconds).
3. **Why the computer plays this way, shown on your board:** its reading looks one turn ahead. After the Sprint
   into the open lane it reads the position as worse than before. It gives every square X1 could stand on, and
   every arrow, exactly the same number.
4. **The reading's first fix failed its gate, so I stopped, as the plan says.** Fitting the reading's parts to play
   does not make one design check fall out. What a lane is worth is a race by the movement rules, and nothing the
   reading measures today sees a race. The next fix is a new part of the reading: decision 1.
5. **For your playtest:** only the zone and the faster setup are new to feel. The computer still leaves the lane,
   still doesn't help and still hugs with its arrows. None of the design checks falls out yet.

## A correction to step 18o

**What went wrong.** The play-out tool hands the possessions to four cores and gathers them core by core. I filed
the results by the order I had sent them. With more than one candidate in a group, each "candidate" in 18o's Part 2
was a mix of all of them. Each row carries its own name, so I refiled them: no new compute, and the tool now
files by name and checks the counts. 18o's report is marked at its top.

**Not affected:** the 48 deals (the search setup is 6.8 worse), both arms and all their tables, the refit, the set's
closeout positions and game EB3F5B, the code readings of check 4, speed, and the tests.

**The corrected tables.** Your board, 16 play-outs each, All-Star against All-Star. Read every number with its
range: 16 play-outs leave about 6 points either way.

*After the point guard beats X1 and X1's reach misses (the zone off):*

| X4 and X5 stand | The offence as it chooses | O1 made to Sprint into the lane |
|---|---|---|
| Next to their men (the lane open) | 22.2 (16.3 to 28.1) | **27.8 (26.4 to 29.2)**: 13 layups in 16 |
| In the lane | 24.6 (20.5 to 28.8) | 22.2 (18.0 to 26.5): 4 layups in 16 |

- **The open lane is worth about 1.4 points a possession,** and the computer's offence leaves about 5 points of it
  on the table. 18o said the reverse (20.2 against 26.9).
- **Help in the lane takes the drive from 27.8 to 22.2.** 18o said help did not play out best.

*After the beat, the defence answering as it chooses (the zone off):*

| X4 and X5 stand | Was reported | Corrected |
|---|---|---|
| Next to their men | 18.3 | 18.1 (11.5 to 24.8) |
| In the lane | 27.0 | 24.2 (19.6 to 28.9) |
| Where the search put them | 22.8 | 25.7 (20.6 to 30.8) |

*Your board at setup:*

| The defence | Zone off: was, corrected | Zone on: was, corrected |
|---|---|---|
| As in your game | 22.2, 23.1 (16.2 to 29.9) | 18.0, 15.9 (8.6 to 23.3) |
| The same, X1 square on I10 | 21.2, 24.5 (18.4 to 30.6) | 17.5, 21.9 (15.8 to 28.0) |
| X1 square, X4 and X5 in the lane | 22.8, 21.9 (17.4 to 26.5) | 21.2, 14.9 (8.9 to 21.0) |
| The search's first pick | **29.1**, 25.4 (22.1 to 28.7) | 19.9, 23.8 (19.2 to 28.4) |
| The search's second pick | 24.7, 26.1 (24.9 to 27.4) | not played |
| The search at Starter | 26.1, 25.1 (21.7 to 28.6) | not played |

- **"The search's first pick played worst (29.1)" was wrong.** On your board nothing separates the placements at
  setup. The 48 deals still show the search setup is worse.

*The straight drive from setup, by where X1 stands:*

| X1 stands | Zone off: was, corrected | Zone on: was, corrected |
|---|---|---|
| J10, arrow on O1 (your game) | 22.3, 23.1 (17.4 to 28.8) | 20.4, 25.2 (21.6 to 28.9) |
| I10, arrow on O1 (square) | 21.2, 22.9 (16.1 to 29.8) | 16.3, **10.8 (3.6 to 17.9)** |
| J10 facing W (the wall) | 24.8, 21.8 (15.2 to 28.3) | 19.8, 20.9 (13.7 to 28.1) |
| J11 beside him (the search's favourite) | 25.2, 25.8 (21.9 to 29.6) | 26.4, 26.0 (22.4 to 29.6) |

- **With the zone on, the square defender in front is clearly best** (10.8: the ball is won 9 times in 16) and the
  search's favourite square is clearly worst (26.0: 15 layups in 16). That is design check 2, shown by play, and
  it supports turning the zone on.

## The plan

`docs/plans/COMPUTER_FIX_PLAN.md`. In short:

- **Your order is confirmed, with one change.** Two faults you listed under the reading are search faults (the
  defender who doesn't step after the ball handler and reach; the block), so they sit in stage 2.
- **The order:** 0 do now (the zone, the setup's time); 1 the reading; 2 in-play; 3 setup from the players and the
  goals; 4 human error; 5 the FIBA comparison; 6 levels.
- **The design checks are the gate.** Your six, and three I added for you to confirm (7, 8, 9: decision 2).
- **Why the reading is first:** the search can only choose what the reading tells it is better.

## Stage 0: done

- **The zone is on by default in the app** (`?zone=0` in the address turns it off). The table's rules don't change.
- **It runs on the fast engine.** The bridge now passes a game under the zone to the fast engine. The two engines
  were checked equal under the zone in 18o.
- **The old setup keeps its time.** It now reads the clock before every reading.

  | Level | Its time a side | Before: offence, defence | Now: offence, defence |
  |---|---|---|---|
  | Rookie | 0.12 | 1.4, 2.3 | 0.28, 0.32 |
  | Starter | 0.4 | 1.3, 2.7 | 0.58, 0.55 |
  | All-Star | 1.0 | 3.7, 2.6 | 1.14, 1.17 |

  It is still over by about 0.2 seconds: one reading in the slow engine takes 0.1 to 0.15 seconds, and it finishes
  the one it has begun. At Rookie that leaves time for one or two readings, so its setup is close to "the table's
  squares, each defender next to his man".
- **`setup.search` stays off.**
- **Speed with the zone on:** the time to finish 1 pair on 9 decisions in 10, in seconds, two rounds. The engines
  did not change in this step, so 18o's code and this step's are the same game; I give 18o's two rounds, timed on a
  quiet core (this step's second round ran beside the site tests).

  | Level | Desktop target | The zone on | At phone size (4 times slower), against its target |
  |---|---|---|---|
  | Rookie | 0.3 | 0.25, 0.19 | 1.0, 0.7 against 1.0 |
  | Starter | 1.0 | 0.66, 0.61 | **2.6, 2.4 against 2.0** |
  | All-Star | 2.5 | 1.65, 1.55 | **6.6, 6.2 against 3.0** |

  - **Every level fits a desktop with the zone on.**
  - **At phone size Starter and All-Star are over, and were before the zone** (18o, the zone off: 3.2 and 7.5 to 8).
    The phone targets are an assumption: no real phone has been measured (D-126).

## Stage 1, the reading: found, tried, stopped

### What is wrong, by four exact checks on your board

No play-outs: the search and the reading asked directly.

| Check | What the computer says | What is true |
|---|---|---|
| The Sprint into the open lane | Reading before 21.6; after it 13.8. One part of the reading does see the layup ("the ball handler's best paint look next phase": 34). It isn't used. | Played, the position after the Sprint scores 27.8. |
| The same, given 35 times its thinking time | Still the drive at 24.0 and stepping aside at 25.4. | All 4 turns it looks ahead fall inside the same phase; the layup is in the next. |
| The fitted map | Turns 10 points of reading into 2 to 4. With the map off the search reads the drive at 17.7, worse still. | The map hides the fault; it isn't the cause. |
| Where X1 stands, and every arrow | The reading is 21.0 for every square and every arrow, on the ball and off it. | Play separates them (the table above). |

### The first fix: each part of the reading given its own worth, fitted to play

- **How the fit avoids learning the flaws (the plan's method):** in the play it learns from, at most once a
  possession a turn is drawn at random from all the turns the search weighed, so lines the computer never chooses
  are played. Only positions after the drawn turn are used.
- **The play:** 320 possessions, All-Star against All-Star, the zone on. A turn was drawn in 253. 4,360 usable
  positions.
- **The fit:** it predicts what a position goes on to earn 0.19 points better than the old reading straightened
  (9.85 against 10.04, held out by possession). Almost nothing.
- **"The layup next phase" is given almost no worth:** 0.01 to 0.05 a point. A 34-point layup counts for about 1.

**The design checks with the fitted reading:**

| Check | Old reading | Fitted reading | Falls out? |
|---|---|---|---|
| 1. The offence takes the open lane | It screens; the Sprint reads 1.5 lower | It steps aside; the Sprint reads 1.0 lower | **No** |
| 4. The open layup is worth about the card (34) | After the Sprint: 20.7 | 22.5 | **No** |
| 2. Square in front beats beside and behind | 21.0, 21.0, 21.0 | 21.1, 22.0, 22.3 | The right order, by 1 point. Not enough to choose by. |
| 3. An arrow that walls or covers a lane beats one that covers nothing | 21.0 for all | 21.1 for all | **No** |
| 7. Stepping next to a ball handler who can't get away | Not read | Not read | **No** |

### Why it failed, and why I stopped

- **The fit is told the lane is worth little, because it is, the way the computer plays it.** What a position "went
  on to earn" is the computer's own play from there, and the computer doesn't finish the drive.
- **And a second round would not cure it.** The first fit doesn't change what the offence chooses, so the second
  round's play would be the same as the first.
- **The deeper reason: what a lane is worth is a race.** A player who Sprints can't move again until the next
  phase. In your board's position the defence still has up to 5 actions in that phase to get a man between him
  and the rim. Whether it can is settled by the movement rules, square by square. No part of the reading
  measures that: "the layup next phase" is read against the defenders where they stand, as if none would move.
- **So the reading needs a new part.** The plan says I stop and ask before adding one, because it is a choice
  about what the computer looks at. That is decision 1.

**Where that leaves the fitted weights:** in `learned_weights.json`, off (`eval.learned`). The game plays on the old
reading. Nothing a player sees changed in stage 1.

**The baseline for the next step** (the zone on, the old reading, 16 play-outs each):

| X4 and X5 stand | The offence as it chooses | O1 made to Sprint into the lane |
|---|---|---|
| Next to their men (the lane open) | 25.1 (20.1 to 30.0). It chose the Sprint 0 times in 16. | 26.9 (21.6 to 32.1) |
| In the lane | 22.5 (18.0 to 27.0) | 23.4 (19.9 to 26.9) |

### Stages 2 and 3: not started

They depend on stage 1. The search fault found for stage 2 (the defender who doesn't step after the ball handler
and reach) is written up in the plan.

## What it proves

- **Tests:** `tests/test_rules_current.py` passes. The 30 named test files: 481 passed and 1 failed, the
  timing test (2.0 seconds on one decision against a limit of 1.7), as since 18f. Not loosened.
  `tests/test_static.py`, run on its own: 11 passed. `tests/test_computer.py`: 2 passed, 1 failed, the stored game
  from before D-184 that already failed on 18n's code.
- **Exam position 1 is open again, and it is design check 1.** It asks the defence to put a man on the line from
  the ball to the rim when the straight drive is worth 34. The computer doesn't; its choice there changes from
  run to run among turns it reads the same. In 18n I let it pass by accepting the turns that "played out level"
  in self-play. Under D-196 that is not proof, so I count it as failing. I did not change the exam.
- **The two engines:** no change to either engine's play in this step. The bridge change sends games under the zone
  to the fast engine, which 18o checked equal under the zone.
- **What it does not prove:** that any design check falls out. None does yet.

## Compute against the estimates

| Stage | Estimate | Used | |
|---|---|---|---|
| 0: do now | 0.3 | 0.13 | Speed and the setup's time |
| 1: the reading | 8.0 | 2.6 | Stopped after the first fit: the four checks 0.3, the play for the fit 1.9, the design checks and the baseline 0.4, a forced line dropped 0.04 |
| Tests | | 0.44 | |

- **The second round of play (2.6) was not run.** The first fit showed it could not help, so I stopped the moment
  that was proved.
- The line by line tally is at the foot of `docs/runs/step18p/PREDICTIONS.md`.
- **Predictions:** 1, the layup next phase gets a clear worth: wrong. 2, the search then chooses the Sprint: wrong. 3, the
  defence then gets between: not reached. 4, the fit beats the old reading by under 1 point: right (0.19). 5, the
  closeout isn't cured by the fit: right. 6, speed would be the hard gate: not reached; the checks were.

## For Shaun to decide (three)

1. **The reading's new part: the race to the rim.** *Recommend: build it.* When the ball handler has a way to the
   rim, the reading plays the race out by the movement rules: his movements against every defender's, phase by
   phase, to the shot, the way a declared shot's reaction is already played out. No weight and nothing named: if a
   defender can get between in time the layup is worth what that defender's contest leaves; if none can, it is
   worth what the card says. Then the map is refitted on play where lanes are taken. It is the one fix I can see
   that makes checks 1, 3 and 4 fall out, and it gives arrows and help their worth, because a wall or a helper is
   exactly what wins the race. The rival is to fit harder on forced lines without a new part; the first fit says
   that fails.
2. **Three design checks I added (7, 8, 9 in the plan).** *Recommend: confirm all three.* 7: stepping next to a ball
   handler who can't get away is worth more than standing off him. 8: a reach reads the same whichever square the
   defender came from. 9: a position reads the same for both sides.
3. **The order of the open pull requests.** *Recommend: merge 76 (step 18o) and then this one.* This prompt did not
   say to merge 76, so I left it open and built this step on top of it. This pull request is against 18o's
   branch, so it shows only this step's changes.

## Model for the next step

Claude Fable 5.2, effort high.

- **The next step is one thing: the race to the rim** (decision 1), in both engines, then the map refitted on play
  where lanes are taken, then the design checks by forced lines. The gate is checks 1, 3 and 4.
- **Budget about 12 core-hours:** the build and its agreement checks 2, two rounds of play for the refit 5, the
  checks played by forced lines 2, speed and tests 3.
- **A shorter prompt would do.** The plan and the checks are in the repository now.
