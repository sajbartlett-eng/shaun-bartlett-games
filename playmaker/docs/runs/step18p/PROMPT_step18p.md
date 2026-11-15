# Step 18p: fix what the computer can't do, in logical order

**Run with:** Claude Fable 5.2, effort high.

Follow `playmaker/CLAUDE.md` and `docs/reference/SHAUN_PRINCIPLES.md`. All paths are inside `playmaker/`.

## Shaun's rule for Fable (record first: D-196, "Shaun, 15 Nov 2026", and add it to the top of `SHAUN_PRINCIPLES.md`)

> "The computer simulations lie. If the computer cannot set up the offence and defence properly and cannot do it based on goals then no play that comes from it can be trusted. I let it set up as it wills and it left a clear lane through the middle for a layup with nothing in between. That means the metrics vs real basketball are garbage."

1. **Trust the design pillars more than the computer simulation data.** System Fidelity first. Then Neutrality, Player Agency, Legibility and Accessibility may bend but never break.
2. **Fable's sole job is to plan, then fix in logical order, what the computer is poor at or can't do at all.**
3. **Anything that clearly meets the whole design hierarchy stays on.** If the data doesn't fit, the starting assumption is always that the computer is wrong.
4. **Fidelity is questioned only after proving the computer is not wrong,** and only after a factor for human error is accounted for.
5. **Human error** may be modelled on elite chess engines measured against semi-pro chess players. The reason: professional basketball relies heavily on physical traits, not purely on basketball IQ.
6. **The primary target is senior pro level.** Other levels are rolled out as each part is locked in.
7. **Use what is needed for proof, and no more.**

**What this means in practice:**

- **The FIBA comparison is not a gate** until the computer is proven to play properly. Stop reporting it as one.
- **Computer-against-computer play-outs are only proof when both sides play the position properly.** 18o's help-defence checks were played against an offence that doesn't drive an open lane, so they couldn't show what help is worth. When one side's play is in question, get the evidence from that side played properly: a stronger search for it, or forced lines. Self-play alone isn't enough.
- **Rulings stand:** D-191, D-193 and D-194 (position decides the contest; the square defender); Shaun's original contest ratings; **Contest foul ratings unchanged** (Shaun: "No").

## Time

**No fixed limit, but proof-sized.** Before each stage, estimate it in `docs/runs/step18p/PREDICTIONS.md` and say what the compute buys. If a stage runs past twice its estimate, stop and report. Stop the moment a point is proved.

## Part 1: the plan (write it before fixing anything)

Write `docs/plans/COMPUTER_FIX_PLAN.md`: everything the computer is poor at or can't do, in the order it must be fixed (what depends on what), with the proof each fix needs. Start from what 18n and 18o found, and Shaun's playtests:

- **The reading is blind to defensive position.**
  - Every off-ball arrow reads the same.
  - X1 beside the ball handler reads better than X1 square in front.
  - The quick reading rates the packed lane best; play rates it worst.
  - The All-Star pauses on the closeout position where stepping next to the shooter wins the ball 9 times in 16.
- **The defence is rarely square, its arrows hug, and help almost never arrives.** 52 of 56 drives finished with no defender square in front.
- **The offence doesn't attack an open lane** after beating its man. It stepped aside 12 times in 16.
- **A forced straight drive into an empty lane scored about 1.0 a shot (18o, 20.2).** An open layup is worth about 1.8. Find out why: presume the computer is wrong.
- **Setup doesn't fit the players or any goal.**
  - Centres start on the three-point line.
  - Non-shooters' defenders stand next to them.
  - X1 left a clear lane to the rim, both in Shaun's game and in his latest one, where he let it set up as it wanted.
  - Nothing in setup comes from goals (the coach's goals and scouting work was held).
- **The block is never tried.** Check that's the cards' numbers working (it pays only for a Contest foul rating of 5 or lower from in front), not a search fault.
- **No mid-range shot, long two or dunk** in 400 possessions. Check whether that's correct play on these cards or a reading fault.
- **Human error,** after the computer plays properly.
- **The zone.** Turn it on by default (Part 2).
- **The levels,** after senior pro is locked.

Shaun's expected order, for you to confirm or correct with reasons:

1. The reading.
2. In-play defence and offence: square, help, walls, lanes, closeouts, attacking an open lane.
3. Setup from the players and the goals.
4. The human-error factor.
5. Only then, a comparison with real FIBA basketball at senior pro level, with fidelity questioned where a gap remains.
6. Levels.

**Design checks: the gate for every stage.** These come from the design pillars and basketball, not from the data. If a fix doesn't make them fall out, the computer is still wrong. Each one is a check, never an instruction or a weight in the engine (D-156).

- A clear lane from the ball handler to the rim, with no defender able to get between, is bad for the defence, and the offence takes it.
- A square, set defender in front is worth more to the defence than one beside or behind.
- An arrow that walls a drive, or covers a passing lane the offence wants, is worth more than one that covers nothing.
- An open layup in an empty lane is worth about what the card says.
- The offence places players where their cards are worth something; the defence answers the players in front of it.
- Setup and play follow the goal set for the possession.

Add any check the pillars clearly demand. Mark each one Shaun hasn't seen for him.

## Part 2: do now (these clearly meet the hierarchy)

- **The zone on by default in the app** (D-167, Shaun's design): it is the only version where a defender can be square to the shot and wall the drive at once (18o, check 4). Make the one-line bridge fix so the app plays the zone on the fast engine. Check the speed on a phone-sized budget.
- **The old setup keeps its time** (it overruns by 4 to 6 seconds a possession).
- `setup.search` stays off until Part 3 makes the reading able to judge a setup.

## Part 3: fix, in the plan's order

Work through the plan from the top, one stage at a time.

- **Each fix treats every move and placement alike** (D-156), with no hand-set weights.
- The learned reading is allowed: fit it to positions played out in bulk.
- **Fit on play from both sides played properly,** not on today's flawed self-play alone, or the fit learns the flaws. Choose and justify how.
- A stage is done when its design checks fall out, both engines agree, and the speed budget holds.
- Write a short stage report in `docs/reports/STEP18P_REPORT.md` as each stage finishes, then go on.

**Stop and hand over to Shaun for a playtest** when the reading, in-play play and setup stages are done (the first three in his order), or earlier if a stage needs a design decision. Shaun's playtest is part of the proof. Leave human error, FIBA and levels for the next step unless you finish early, inside the estimates.

## Fixed

The design pillars and the rulings above; no hand-set weights or distances; no kind of move or placement named or favoured; both engines equal; the speed budget; plain basketball words; uncertainty on every number. If a fixed item looks like the problem, stop and flag it.

## Checks

`tests/test_rules_current.py`; the tests for the files you changed; the equivalence and golden tests. No full suite. Don't loosen the timing test.

## Report

`docs/reports/STEP18P_REPORT.md`.

- **Start with five lines or fewer in plain words:** what the computer can now do that it couldn't, which design checks fall out, and what Shaun should look for in his playtest.
- Then the plan, each stage's report, and compute against each estimate.
- End with **at most three decisions for Shaun,** each with your recommendation, and your model advice.

## Done when

- D-196 is recorded.
- The plan is written.
- The zone is on by default, on the fast engine.
- The first three stages of the plan are done, or stopped with the reason.
- The pull request is open and not merged.
