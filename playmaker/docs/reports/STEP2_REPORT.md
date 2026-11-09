# Step 2 report: one page of current rules

## 1. Changes to the printed game

None. The new printed rules were filed in `reference/`; nothing in them was changed.

## 2. What changed

- **Step 1 merged** (pull request 45). The tag `baseline-3n` is left for Shaun: in this session `gh` is only available
  for search, so `gh release create` wasn't tried.
- **`reference/`:** the new rulebook and both trackers replace the old ones, which are in `archive/reference/`. New:
  `Court_A3.pdf`, `Token_sheet.pdf`, `Offence_first_game_guide.pdf`, `Defence_first_game_guide.pdf`. The other files
  stay where they were.
- **`playmaker_engine/register.py`:** each register row now carries its rule in plain words, its value in words for
  each format, the section of the rulebook it belongs to, and where it is printed. Stale rows fixed (see 4). New rows for
  rules the register didn't name: Lock tokens (8), Setup placement, Phase reset, Dribble, Intercept roll, Hold for One
  cards, Late Clock results, Tie-break roll, Tied match. `python3 -m playmaker_engine.register --rules` writes
  `RULES_CURRENT.md`; without `--rules` it writes `docs/rules_register.md`, as before.
- **`RULES_CURRENT.md`:** every rule the game plays by, in the rulebook's 13 sections, then Digital only, Split by
  format, and the rules no printed page states. 4 pages printed, not counting the last section.
- **`tests/test_rules_current.py`:** new. No rule value, setting or engine behaviour changed.

## 3. What it proves

- `tests/test_rules_current.py` (the only test run): 16 pass, 0 expected failures, 0 fail, 0.2 seconds. Every Shared
  number is in the printed text with the same meaning: 6 action tokens, phases of 2 seconds, shot clock 12 and down 2,
  8 lock tokens, −5 (rulebook and offence tracker), +5 (rulebook and defence tracker), −3 (rulebook and defence tracker),
  free throws × 2 and × 3, Move 3 straight or 2 diagonal (both trackers). `RULES_CURRENT.md` is what the generator
  writes now. Every register row has its value in words.
- Not run: `tests/test_step3n.py`, which also checks the register. Its conditions were checked directly: 68 Shared
  rows, all identical in both formats; every setting named; `docs/rules_register.md` equals what the module writes.

## 4. For Shaun to decide

- **Mismatches between the printed rules and the register:** none. Every Shared number matched.
- **A split nobody approved:** a tied match. At the table each player rolls for their final shot; the app leaves a tied
  digital match as a tie. Found in the code (`playmaker_web/game.py`). Recorded as Split, marked "not approved".
  Options: approve it as is; or have the app break ties the table's way (an engine change, a later step).
- **Fixes I made that may be more than record-keeping:**
  - Match length: the register said 2 to 8 possessions a side; the app allows 4, 8 or 12. Fixed to match the code.
  - Lock tokens: now 8, covered (as asked).
  - Quick Step marker: the register said none was printed; the new trackers give each player a Quick Step slot, so the
    token in it marks a used Quick Step. Marked covered. Not in the step's list of fixes.
  - Tie-break roll: marked Tabletop only, because the app has none (see the split above).
- **Rules the engine plays that the rulebook doesn't state:** 18, plus 5 printed only on the scenario rules sheet. All
  18 have an `OPEN_QUESTIONS.md` row. They are the last section of `RULES_CURRENT.md`, for step 3.

## 5. Noticed, not touched

- The defence tracker says a reaction is "with a Move or a Steal" and adds "Move to face them, then Quick Step in". The
  engine also allows a Sprint and up to 2 actions in any order (row 6). Listed as an engine-only rule.
- The rulebook says a forced shot below 0 scores 0. The engine applies the same to declared shots (row 5). Listed.
- The scenario rules sheet still comes from before this step; it agrees with the engine on inbounds and Coach's Call.
- `OPEN_QUESTIONS.md` row 32 still gives the old reasoning for lock tokens (4, at most 4 a phase).
- The register's "Splits for the designer" note about the phase table is engine data, not a rule; left as written.
