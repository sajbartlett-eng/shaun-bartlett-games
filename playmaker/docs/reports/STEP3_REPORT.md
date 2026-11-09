# Step 3 report: one decisions log

## 1. Changes to the printed game

None yet. Two rulings change it when step 9 builds them: Contest as an action (the defence tracker gains a Contest slot;
the rulebook's Shooting section changes) and overtime in the app (no printed change; the table keeps its roll).

## 2. What changed

- **Step 2 merged** (pull request 46). Branch `step-03-decisions` from the updated `main`.
- **`DECISIONS.md`:** new. 105 entries, D-1 to D-105, each with its old OQ number where it had one, then an index from
  OQ numbers to D numbers.
  - Ruled: 61. Built 40; ruled, not built 2 (D-18 Contest as an action and D-19 overtime, both step 9); built, not
    printed 19 (D-1 to D-17, the 9 Nov approvals; D-30 steal-foul free throws; D-36 the fouled Excellent three).
  - Engine defaults awaiting sign-off: 19 (D-62 to D-80).
  - Open: 25. Step 9: 8. Step 10: 2. Step 11: 5. Step 12: 2. Step 14: 1. Step 15: 1. Step 16: 1. Not placed: 5.
  - All seven items from Shaun's sessions are in: angle check D-84, clean miss D-85, All-Star scouting D-101, shot-clock
    expiries D-99, the digital bonus D-89, lock count measurement D-102, old exam boards D-96.
  - Row 32 (D-35) now gives the current reasoning: 8 printed, worst case 6 a phase since failed Steals lock.
- **`OPEN_QUESTIONS.md`:** moved to `archive/`. A one-line stub at the root points to `DECISIONS.md`.
- **`register.py`:** the † list is now two lists, "Ruled, not yet printed" (17 lines, each "See D-n") and "Ruled, not
  yet built" (Contest as an action, D-18; overtime, D-19). The reaction rule it replaces is marked ‡ in the body. The
  scenario-sheet list keeps its place under its own heading. Tied match: "Split by format, approved; overtime not yet
  built". `RULES_CURRENT.md` and `docs/rules_register.md` regenerated.
- **`CLAUDE.md`:** the "Decisions:" line only, as given.
- **`tests/test_rules_current.py`:** two new checks (below). No code behaviour changed.

## 3. What it proves

- `tests/test_rules_current.py` (the only test run): 18 pass, 0 fail, 0.2 seconds. The 16 from step 2 still pass. New:
  both ruled lists exist, have 17 and 2 lines, and each line points to one D number that exists in `DECISIONS.md`
  (D-1 to D-17 in order; D-18, D-19); `RULES_CURRENT.md` no longer cites `OPEN_QUESTIONS.md`; the Tied match row reads
  as ruled.
- Not run: `tests/test_step3n.py`. Its register conditions were checked directly: 68 Shared rows identical in both
  formats, every setting named, `docs/rules_register.md` equals what the module writes.
- `git diff --stat main` touches only the files the step allows.

## 4. For Shaun to decide

- **Item numbers.** Your ruling calls Contest "item 15". In `RULES_CURRENT.md` the reaction rule was item 15 and
  "next to him" was item 11 of 18, so the numbers don't line up with the text. I followed the text: every rule you named
  as approved is D-1 to D-17, and the reaction rule (old item 15) is the one Contest replaces. Confirm.
- **Entries placed with less confidence:**
  - D-60 (tied table game, roll for the final shot): recorded as ruled because the rulebook prints it; no ruling names it.
  - D-61 (`CLAUDE.md` stays in the Playmaker folder): a working rule, not a game rule. Kept so nothing is decided
    elsewhere.
  - D-30 (steal-foul free throws use the ball carrier's rating) and D-36 (a fouled three of 30 or more counts as
    Excellent): built, not printed, but not in the `RULES_CURRENT.md` lists, because the register has no row for
    either. Adding rows is a register change for a later step.
  - D-76 (solver findings with nothing to decide) and D-78, D-79 (Coach Vision at Learn only; the decision timer): put
    under "awaiting sign-off"; they could be ruled already if a step prompt counts.
  - D-88 (growth tag markers) under step 9, D-98 (level gaps) under step 14, D-103 (Coach's Call worth nothing against
    best defence) left unplaced.

## 5. Noticed, not touched

- Code comments and docstrings still cite OQ numbers, as the step says; the index in `DECISIONS.md` maps them.
- `README.md` still points to `OPEN_QUESTIONS.md`; the stub catches the link. Not in the step's list of files.
