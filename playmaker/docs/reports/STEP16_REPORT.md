# Step 16 report: advantages, and goals that steer the search

**Reported first, because it breaks the desktop speed budget:** with `eval.coverage_budget`, `eval.advantages` and
`search.goals` all on, the Rookie needs 0.41 s for 1 pair (target 0.3 s) and the Starter 1.20 s (target 1.0 s).
Goals without the budget fit a desktop.

## The checkpoint (D-130), stated plainly

**Goals on their own change no exam board.** With the budget on as well, 1 board more passes (board 5).

| Setting | 1 pair | The clock |
|---|---|---|
| Off (today's default) | 9 of 19 | 10 of 19 |
| `eval.advantages` only | 9 of 19 (the same boards) | 10 of 19 (the same boards) |
| `eval.advantages` with `search.goals` | 9 of 19 (the same boards) | 10 of 19 (the same boards) |
| `eval.coverage_budget` | 9 of 19 | 10 of 19 |
| The budget with advantages only | 9 of 19 | 10 of 19 |
| The budget with advantages and goals | **10 of 19** (board 5 gained) | **11 of 19** (board 5 gained) |

Failing in every setting: boards 1, 3, 6, 8, 9, 10, 11 and 13 (and 7 at 1 pair).

**The uncertainty:** the gain is 1 board of 19, and it needs both new readings on. One board is no more than earlier
steps saw a board move between two runs of the same setting (boards 7 and 16). Step 14's bigger exam hasn't merged, so
there's no second sample. The All-Star, `exam_*.json`.

## The board 13 pair

The reading doesn't move: 0.0 with goals off and on, with and without the budget (`pairs.json`).

**The advantage list does read differently.** The ball handler's best paint square next phase:

| | O5 in the lane | O5 cleared |
|---|---|---|
| Square he can reach next phase | G2 | I2 |
| The look there | 10 (a defender gets to a Contest) | 16 (nobody does) |
| What it adds to the possession | 0 | 0 |

By his card the look at the rim is worth 16 at most, and he already has a free three worth 24 from K10. So clearing
the lane buys nothing the possession doesn't already have, and the computer isn't paid to do it.

The other two pairs, the reading alone and then with the goal potential added:

| Pair | Reading | With the potential |
|---|---|---|
| Board 16: X2 fresh, against spent | +0.96 | +0.78 |
| Board 12: the help near, against drawn away | +6.55 | -0.26 |

On board 12 the potential cancels the reading's gap: with the help near, the reading is low but a free paint look next
phase is worth 12 more; with the help drawn away, the reading already has most of it.

## Tactical integrity

Measured on the search's own best turn, 1 pair ahead (`integrity.json`):

| Case | Result |
|---|---|
| A better shot exists now | 2 of 2 still shoot (board 7's last phase, and the same board with the shooter free in the paint) |
| The goal is no longer worth chasing (the same board in the last phase) | 6 of 6 have no set-up goal left; the 4 with nothing left choose exactly as without goals |
| The defence breaks the plan (a defender put on the target square) | 6 of 6 move on: 3 drop the goal, 3 turn to another square |
| A chance no top goal named | 13 of 22 choices are the same as without goals. The other 9, valued by the search without goals, cost 2.8 at most; 2 cost more than the margin of error (boards 2 B and 13) |

**The check found a fault, now fixed.** When no offence turn is left before the clock runs out, the position reads 0,
and every look counted as a goal. On board 11's last phase that cost 15.7. Nothing can be built once no turn is left,
so no goal is read there.

## Speed

Goals don't help speed. They cost it.

The 9-in-10 time to finish 1 pair, in seconds (`pairtime_*.json`; phone is the assumed quarter speed):

| Level | Target: desktop, phone | Off | Advantages only | With goals | Budget with goals |
|---|---|---|---|---|---|
| Rookie | 0.3, 1.0 | 0.18, 0.73 | 0.18, 0.74 | 0.25, 1.01 | **0.41**, 1.64 |
| Starter | 1.0, 2.0 | 0.47, 1.89 | 0.49, 1.98 | 0.78, 3.10 | **1.20**, 4.81 |
| All-Star | 2.5, 3.0 | 0.82, 3.29 | 0.88, 3.50 | 1.03, 4.10 | 1.71, 6.82 |

- Advantages only costs nothing in the search: it reads once per decision.
- With goals, every position read also reads its goals: 26% to 66% more time. The ordering doesn't win that back.
- On the clock with goals, 20, 22 and 22 of 22 decisions finish 1 pair on a desktop (`levels_goals.json`).

**Stability** (boards 2, 7, 9, 10 and 16, 8 decisions, all reached 4 team turns): the first action changes from 1 to 3
on 4 of 8 with goals off and 4 of 8 on; from 2 to 4 on 2 of 8 off and 3 of 8 on (`stability_*.json`).

## The design choices and their rivals

**What an advantage is worth.** The look it leads to, after the defence's best answer, read the way the position value
reads a look, less what the possession is worth now. At or below zero it isn't a goal. That is also how "a location
where the edge pays" is decided: by the look's value there against the possession, with no list of zones.
A look the position value already counts is worth 0 as a goal, so nothing is counted twice.

**The chance of reaching conversion.**

| Option | Cost | Accuracy |
|---|---|---|
| **Built:** the reading's own chances. The pass's chance for a catch or a cut; the ball handler's own movement is certain; and a race from the reach map: a defender who can get to a Contest in time lowers the look, one who can't leaves it free. Next phase, any defender within two movement actions of a Contest counts | Advantages only: none in the search. With goals: 26% to 66% | The pieces as they stand. It doesn't see the defence's reply after the offence's next move |
| A short search for each goal | A search per goal per position: far over the budget | The defence's real replies |
| A table of how often each kind converts, by phase | Almost none | Needs games played with goals to measure. None exist |

**The four kinds, each from the board:**

- **Separation:** a look no defender can Contest in time.
- **Mismatch:** a contested look where the attacker's band for that shot is above the best contester's band for that
  Contest. The cards carry the bands (high, average, low), so two apart is strong and one is an advantage.
- **Numbers:** an attacker the defence's best shares leave above its full cover. It needs `eval.coverage_budget`.
- **Penetration:** the ball handler's way into the paint. This phase by his looks there; next phase from any square
  he can reach this phase plus one movement, teammates in the way included.

**The potential** is each attacker's best advantage, summed, and 0 once the possession ends. The search adds it to
every position it reads and takes the starting position's off at the end.

**No new hand-set number.** The bands are the cards'. The paint is the rules' zone for layups, dunks and post shots.
Two movement actions is a Move and a Quick Step, a defender's phase.

## Three worked examples

**Board 13, the crowded lane.** Your point guard has the ball at the top with a free three, and your centre is
standing in the lane.
- Goals found: the three is ready now (24). His way to the rim next phase only reaches the left block for a contested
  10, because the centre is in the way. Your shooting guard has a two-band mismatch on the wing (30 if the pass
  arrives, half the time).
- Stage: the three converts now; the other two would have to be kept.
- None is worth more than the possession already is. With goals on, the centre sets a screen; without, the wings
  relocate.
- A trainer would say: "He already has his best shot. The lane isn't worth clearing for a player who finishes at 16."

**Board 16, the spent defender.** Your point guard has the ball at the top, and nobody stands between him and the
paint.
- Goals found: he can be in the paint next phase for a 20 nobody can get to (worth 3.8 more than the possession
  now, still to set up). Your shooting guard has a free corner three if the pass arrives.
- The move: the shooting guard slides to the corner, and the point guard steps to H10, the middle, not to J10.
- A trainer would say: "Good. You kept the middle open for the drive while the corner pulled his man out."

**Board 9, the kick-out.** Your point guard can get to the rim this turn, with his man on him.
- Goals found: the rim look is ready now (22, contested). Both wings have a two-band mismatch.
- The move: he steps to the rim and your forward cuts to the block beside him; his look goes up 10 and the
  forward's 7.
- A trainer would say: "You made the help choose. But the board wanted the kick to the corner, and that still isn't
  found."

## 1. Changes to the printed game

None. Both switches are off.

## 2. What changed

- **Step 13C merged** (pull request 58). D-128, D-129 and D-130 are recorded. The re-measured averages are stored,
  so default readings moved by up to 0.78.
- **`eval.advantages`** (off), in `decide.py` and `engine.js`: `Read.advantages` and the potential. Each decision
  records its top goals, their stages, the goal the computer is on, the event (ready, lost, switched, clock), the
  defence's mirror answer (prevent, break, deny, concede, run down) and which looks the chosen turn raised or lowered.
- **`search.goals`** (off; needs `eval.advantages`), in `search.py` and `engine.js`: the potential in the search, and
  turns that work on a top goal searched first.
- **Cards carry their bands** to the JavaScript engine.
- **Tools:** `tools/goals_16.py` (the pairs and the integrity checks); `tools/js_equivalence.py` takes `--advantages`
  and `--goals`; `tools/exam_13.py` has the settings.

## 3. What it proves

- **Advantages only changes no choice:** the same values and choices on the 8 decisions
  (`advantages_only_same.json`), and the same exam boards.
- **The engines agree, 0 mismatches,** run after the fix above:
  - goals on: 100 positions and 5 whole searches, the advantage list, every worth and the potential compared on 96
    (`js_equivalence_goals.json`);
  - goals and the budget on: 100 positions and 4 whole searches, the list compared on 91
    (`js_equivalence_goals_budget.json`);
  - the default game: 150 positions and 6 whole searches (`js_equivalence_default.json`).
- **Tests, switches off:** `test_rules_current`, `test_static`, `test_step3n`, `test_step3m`: 78 pass, 13 expected
  failures, 1 unexpected pass. The same as step 13, with the same exam boards failing.
- **Caps:** about 37 of the 60 minutes.

## 4. For Shaun to decide

- **The checkpoint (D-130).** The numbers are above. Goals alone: no board. With the budget: 1 board.
- **Why goals change so little, and the choice it opens.** A goal is only worth what it adds to the possession now.
  Looks the reading already sees add nothing, so nearly all the potential comes from the ball's way to the paint next
  phase.
  - Option: read the other three kinds two phases ahead too (a shooter who will be free next phase, a mismatch a
    switch will make). That is where screens and cuts would start to pay.
  - Option: keep it as it is and wait for the bigger exam.
- **Board 13.** By the cards the lane isn't worth clearing. If it should be, the board needs a ball handler who
  finishes better at the rim than he shoots.
- **Switching and the three events** govern the record and the search order, not the value. The value is the
  potential alone. Say if the goal the computer is on should weigh more than the others.
- **Speed.** Goals fit a desktop on their own. With the budget they break it for the Rookie and the Starter.

## 5. Noticed, not touched

- **Two phases ahead is built for the ball handler's way to the paint only.**
- **The defence's mirror goals are recorded, not searched on their own.** The defence already gains by lowering the
  offence's potential.
- **Step 14's boards aren't on `main`,** so the informal run on them wasn't done.
- **The computer's pick adds noise and a pick among near-equal turns.** Measured that way, 14 of 22 picks differ
  between goals off and on; on the search's own best turn, 9 do.
- **The exam book** is untouched.

## 6. Model for the next step

Claude Fable 5.2, effort high. The next step is the rethink the checkpoint asks for, or widening two phases ahead to
the other kinds: both are design work across the two engines.
