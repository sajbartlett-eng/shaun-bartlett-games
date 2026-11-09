# Step 6 report: build the 9 November rulings (plan step 9)

## 1. Changes to the printed game

The rulings change the printed game. The app plays them now; the pages below need Shaun's update. The PDFs in
`reference/` are untouched.

- **Defence tracker:** a Contest action (one a phase, the last action of the reaction, a token). The reaction wording
  becomes "up to 2 actions from your tokens: Move, Quick Step, Sprint, Steal or Contest. No Contest: a contest of 0."
  (D-18)
- **Rulebook:**
  - Shooting: Contest as an action, and no Contest means 0 (D-18). A forced shot at clock 0 still has the contest choice
    (see 4).
  - Scoring: every steal foul is +5; in the bonus it also gives free throws and ends the possession (D-89). A turnover
    that scores the possession 0 scores 0 or the banked total, whichever is lower (D-82).
  - The steal-foul line ("First foul on a steal +5") and the words "clean miss" ("a Steal that misses without a foul",
    D-85). Plain wood (D-87).
- **Court:** the distance rings (D-84); plain wood.
- **Offence first game guide:** plain wood.
- **Playing levels sheet:** no growth tags at the table (D-88).

**D-81, measured only.** The existing tabletop runs hold 2 successful intercepts in 60 possessions
(`docs/runs/3n/3n_f5_tabletop.json`; the seed runs are all app format). Final results were 19 and 23. With the pass
caught instead, the engine's read gives 28 and 27 (the solver gives 30 and 8). Mean gap: −6.5 by the read, +2.0 by the
solver. Too few cases to say.

The smallest run that settles it needs no new games. At every pass in those 60 possessions that a defender could
intercept, compare the engine's read after a successful Intercept with the read if the pass is caught. Every
interceptable pass gives a pair, rolls aside. There are 134 passes, so expect a few dozen pairs, enough for a mean to
within about 2 points. New tabletop self-play would need about 900 possessions to reach 30 intercepts. Not run.

## 2. What changed

- **Step 5 merged.** Its answers are in `DECISIONS.md`: D-72 to D-74 retired, D-70 and D-94 restated, and the two
  exam candidates for step 12 (D-108, D-109). `docs/build_audit_docs.py` and `docs/audit/` moved to `docs/history/`.
- **Part 1 is recorded in `DECISIONS.md`.** D-82 to D-89, D-101, D-104 and D-107 are under Ruled. D-103 and D-105 are
  superseded. D-106 (coach's goals) and D-81 and D-86 stay open. D-18 and D-19 are built.
- **Contest as an action (D-18), both formats.** It lives in `rules_config`, `actions`, `resolve`, `decide`, `search`,
  `solver` and `engine.js`. A Contest is legal in the reaction for any defender next to the shooter while tokens
  remain. It spends a token, ends the reaction and resolves the shot. Ending the reaction without one gives a contest
  of 0, and a Steal reaction can't also Contest. Contest is now in the per-phase limits (1) and the turn-ending
  actions.

  The computer chooses it like any action. Its read counts a Contest as one of the reaction's actions, inside a
  reaction it counts the actions already taken, and the search now offers the closeouts (every movement that ends
  next to the shooter). The solver's reaction plays end with the Contest. The page offers Contest as a defender's
  action, and the reaction text and the turn bar name it.
- **Overtime in the app (D-19).** `game.py`: a tied app match adds one possession a side until a side leads after
  equal possessions. Team fouls carry on, and the table keeps its roll.
- **Turnover floor (D-82)** in `resolve`, `scoring` and `engine.js`, and in the computer's pricing.
- **Steal fouls (D-89).** +5 on every steal foul in both formats, plus free throws in the bonus. The foul price
  follows from the rule; no constant changed.
- **Growth (D-88).**
  - App format only: dealt at random as before, with no tag names, chips or badges. Coach Vision's two lines sit under
    the card.
  - The tabletop format plays the cards as printed.
  - Internally the tags are now early, typical and late.
  - The page no longer offers hand-set tags. The API keeps that option for hand-worked test positions.
- **Words and display.**
  - Distance rings, on by default, with a toggle.
  - "Pick-off", "picked off" and "clean miss" are replaced, and all three, plus "on time", are now banned terms.
  - The All-Star description adds the given line.
  - A step blocked by a screen shows greyed, with "Blocked by the screen" (`actions.screen_blocked`).
- **Old logs** replay under the old rules (`RC.PRE_9NOV`).
- **Register:** new rows for the three rulings, D-30, D-36 and junior growth. The growth split is approved and the
  tied match is built. `RULES_CURRENT.md` and `docs/rules_register.md` are regenerated.

## 3. What it proves

- **The one run.** `pytest -q`: 458 pass, 12 expected failures, 3 fail, out of 473, in 17 minutes 30 seconds.
  The 473 is step 5's 452, plus 14 new tests (`tests/test_step6.py`) and 7 restored ones.
  - All 3 failures pass with only `contest_action` off. Contest as an action changes the computer's reading of those
    boards.
  - `test_step3m` exam board 6 (catch window) now picks "O2 Move to A5; O2 Screen" and fails. It has no expected-failure
    marker.
  - `test_step3m` early cut: the reveal margin is 0.75 against 3.0.
  - `test_step3n` decoy credit: the helper credited isn't X3.
  - Not fixed: they go beyond the rulings (see 4).
- **`tools/js_equivalence.py --n 500`:** 0 mismatches out of 500 states, every check. Only 2 of the 500 states were
  in a reaction.
- **The computer's Contest choices.** In 12 All-Star games I compared each reaction to a declared shot with the exact
  best reaction of up to 2 actions. All 8 equal it (gap 0).
- **Tests changed to the new rules:**
  - D-18: `test_rolls_scoring` (the contest choice, a negative declared shot), `test_turns_phases`, `test_web`
    (contest through the API), `test_timer`, `test_defence`, and `test_solver` (one floor case).
  - D-18, pinned instead: the ceiling records (the `legacy_rules` fixture, two in `test_revalidated_live`, and the
    evaluation-vs-ceiling test). They run with the rules before 9 Nov, as step 3n did for its records.
  - D-89: `test_rolls_scoring`, `test_scenarios`.
  - D-88: seven in `test_levels_3l`.
  - D-18 and D-19 built: `test_rules_current`.
- **Restored:** the movement rules on live levels (5 cases), the computer's rolls reported, the setup log.
- **New:** Contest uses a token and is last; no Contest means 0; a Steal can't Contest; the forced shot is unchanged;
  overtime; the floor; +5 in both formats; growth words; banned terms; the rings toggle; the blocked step.

## 4. For Shaun to decide

- **The three failing tests**, all caused by D-18. Options: accept the new readings (update board 6 and the two trainer
  tests in step 12 with the exam); or look at the computer's contest read again in step 11.
- **A forced shot at clock 0** isn't declared, so it kept the free contest choice. Options: keep that; or no contest on a
  forced shot.
- **A Steal on a declared shot that fouls** now scores +5 as well as the shooting free throws ("every steal foul").
  Confirm, or keep it free throws only.
- **Junior growth in the app's tabletop format:** none, since it follows the table. Hand-set tags are gone from the page.
- **Words I had to write**, for your review:
  - The reaction's end button: "(no Contest: the shot goes up with a contest of 0)".
  - The turn bar and shot lines.
  - The growth box, age and roster texts.
  - "Distance rings: shown/hidden".
  - The intercept and turnover-floor wording.
  - "Tied: overtime, one more possession a side."
- **`analysis.py` ceilings** still model the free contest, so their records are pinned. Option: rewrite the tool for
  Contest as an action.
- **D-81:** run the paired read above, or leave it open.

## 5. Noticed, not touched

- D-107 (match and matchup) is recorded only; the app's strings weren't audited for it.
- A junior card's growth label was shared through a cache. It now records only early or late, which fixed a test that
  depended on build order.
- The test runs regenerate three `docs/levels_*.png` screenshots. They now show no growth badges.
