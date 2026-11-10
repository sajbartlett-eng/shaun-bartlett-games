# Step 13, part B report: cover as a budget

**Reported first, because it breaks the speed budget (D-123):**

- **The switch (`eval.coverage_budget`, off) breaks the phone budget at every level.** It fits a desktop.
- **Today's default game (D-121) is already over on a phone for the All-Star:** 3.9 s against 3.0 s. That comes from
  the reach map, not from this part.

The 9-in-10 time to finish 1 pair, in seconds (`pairtimeB_*.json`; phone is 4 times desktop):

| Level | Target: desktop, phone | Default game: desktop, phone | With the switch on: desktop, phone |
|---|---|---|---|
| Rookie | 0.3, 1.0 | 0.20, 0.80 | 0.28, **1.12** |
| Starter | 1.0, 2.0 | 0.50, 1.99 | 0.86, **3.43** |
| All-Star | 2.5, 3.0 | 0.99, **3.95** | 1.88, **7.52** |

On the clock, of 22 decisions that finish 1 pair (`levelsB_*.json`):

| | Rookie | Starter | All-Star |
|---|---|---|---|
| Default game: desktop, phone | 21, 7 | 22, 4 | 22, 16 |
| Switch on: desktop, phone | 17, 2 | 19, 4 | 21, 8 |

Where the switch's time goes (`profile_budget.json`): the ball handler's two-action squares are 25% of the search. The
allocation itself is 6%, and solving it 2%.

## The exam: off against on

"Off" is the default game (`like_with_like` and the reach map, D-121). The All-Star, 9 of the 45 minutes used.

| Board | Off: 1 pair | Off: clock | On: 1 pair | On: clock |
|---|---|---|---|---|
| 1, 3, 5, 6, 8, 9, 10, 11, 13 | F | F | F | F |
| 7 | F | P | F | P |
| 2, 4, 12, 14, 15, 16, 17, C1, C2 | P | P | P | P |
| **Passes** | **9 of 19** | **10 of 19** | **9 of 19** | **10 of 19** |

No board changes. With the switch on, board 10 finishes only 1 team turn on the clock.

## The sensitivity pairs

The reading's difference between the two positions of each pair (`sensitivity_budget.json`). The margin of error is
0.92.

| Pair | Off | On |
|---|---|---|
| Board 16: X2 fresh, against X2 spent | +0.96 | **+1.41** |
| Board 12: the help near the mismatch, against drawn away | +6.43 | +5.98 |
| Board 13: O5 in the lane, against O5 cleared | 0.0 | 0.0 |

- **The X2 pair grows,** by half. Fresh, X2 has to split himself: 83% on O2 and 17% on O4, and the offence is held to
  15.75. Spent, he can answer neither, X3 takes over, and it is 16.5.
- **Board 13 doesn't move.** From I9 the rim is three actions away with or without O5. In the two actions of a team
  turn, O5 only blocks I5 and I6, and neither gives a look better than the three from K10 (24).

## The allocation method chosen, and its rivals

**The rule built.** In one team turn a defender attends one attacker: he ends on one square and makes one Contest.
The defence splits each defender across the attackers he can answer, in shares that add to 1 at most. A share is the
chance he is the one there. On any one look only one answer counts, and answers that need a movement share the
defence's movement actions next turn. The offence's value is its best look after the defence's best shares.

Every number is an existing one: each look's value with nobody near, with one defender's Contest, the pass's chance,
and the squares each defender's replies already use.

Compared on 547 positions (the 22 exam decisions and every position one action later, `allocation_methods.json`):

| Method | Accuracy | Cost per reading (Python) |
|---|---|---|
| **Exact small linear program (built)** | exact | 1.29 ms |
| Greedy: lower the best look with the strongest answer, again and again | equal on 342 of 547; above by 0.50 on average, 7.2 at worst; beyond the margin on 75 (14%) | 0.10 ms |
| Precomputed table | not built | not measured |

- **The greedy's gap, proved one way:** every step stays inside the same limits, so its answer is one the defence
  could really choose. It can never be below the exact value, only equal or above. How far above has no bound I can
  prove; it is measured.
- **Why the exact one:** solving is 2% of the search time, so the greedy would save almost nothing and be wrong beyond
  the margin on 1 position in 7.
- **Why no table:** a reading has about 30 looks and 18 answers, each a number. There is no small set of cases to
  store.

## 1. Changes to the printed game

None. The switch is off.

## 2. What changed

- **Rulings recorded:** D-121 to D-124. `like_with_like` and the reach map are on by default in both engines.
  `docs/SPEED_BUDGET.md` is written.
- **`eval.coverage_budget`** (off), in `decide.py` and `engine.js`:
  - **B1:** the allocation above (`Read.budget`). It replaces only the "best look the cover leaves" inside the
    position value. The ordering's quick reading is unchanged.
  - **B2 (D-115):** the ball handler's looks also count the squares he reaches in two actions. Each action follows the
    movement rules from where the first leaves him, so teammates in the way block him.
  - **The averages** the position value is read against were measured again under the switch
    (`eval.relative_average_budget`, `tools/relative_average.py --budget`): 17.0 to 22.9 by phase, against 15.6 to
    20.5.
- **B3:** `Read.look_split` gives each look's finisher (the card) and quality (the position). The two multiply to the
  look's value. Reporting only.
- **The Python search keeps each defender's exact movement per position,** as the JavaScript does. No result changes.
- **Tools:** `tools/coverage_13.py` compares the methods; `tools/exam_13.py` has the settings `base` and `budget` and
  the sensitivity pairs.

## 3. What it proves

- **The engines agree, 0 mismatches:** 200 positions and 6 whole searches with the default game, and the same with
  the switch on. With it on, the allocation (value, what each attacker is left, every share) and each look's two
  parts are compared on 193 positions (`js_equivalence_default_200.json`, `js_equivalence_budget_on_200.json`).
- **Tests, default game, switch off:** `test_rules_current`, `test_static`, `test_step3n`, `test_step3m`: 78 pass, 13
  expected failures, 1 unexpected pass.
  - **One test failed first, and it was right:** with the reach map on, the game loads `reach.py`, which wasn't in
    the browser bundle. It is added to `playmaker_web/build_site.py`, and the test passes.
  - The new defaults move two exam-board tests on the Python search's clock: board 2 now passes and board 16 is now
    an expected failure. What the tests check is unchanged.
- **Caps:** 9 of the 45 minutes.

## 4. For Shaun to decide

- **Switch it on? Not yet.** It moves the X2 pair the right way, changes no exam board, and breaks the phone budget.
  - Option: keep it off until the two-action squares are made cheaper, then measure on the bigger exam (step 14).
- **The default game is over the phone budget for the All-Star** (3.9 s against 3.0 s).
  - Option: set the All-Star's phone target to 4.0 s.
  - Option: build the root window (D-124), 15 to 19%, which brings it to about 3.3 s.
  - Option: leave it until a real phone is measured.
- **Board 13 needs a look further than one team turn.** The reach map already holds where each player can be next
  phase. Counting looks from there needs a ruling on how such a look is marked down. Today's `later_p` is the only
  number of that kind.
- **One Contest per defender per team turn** is how I read "limited". The rules let a defender next to two shooters
  Contest whichever shoots. If that should stay free, the split applies only to answers that need a movement.
- **`tempo` and `play_on`** are still to be measured again on the bigger exam (D-122).

## 5. Noticed, not touched

- **The first averages (`eval.relative_average`) were measured before the reach map was on by default.** They weren't
  measured again for D-121.
- **B2 covers the ball handler only.** The other attackers' cuts still use movement geometry without blockers.
- **A movement answer comes from the replies the reading already keeps** (`responses_per_defender`), not from every
  square a defender can reach.
- **In my first build of the rulings `like_with_like` was still off in the settings file.** The whole-search checks
  and every measurement above were run after it was fixed.
- **The exam book** is untouched (step 14's session owns it), so it doesn't show these results.

## 6. Model for the next step

Claude Fable 5.2, effort high. The next engine work is making the two-action squares cheap without changing a result,
then reading the bigger exam: both need care across the two engines.
