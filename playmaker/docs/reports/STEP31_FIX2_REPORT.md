# Step 31, fix 2 of 7: later answers cost actions in every phase. Report

**Built in both engines, on branch `step-31`. Not merged, as asked. The exam was not run.**

The rule now holds phase after phase. Before, only this phase limited the defence's answer: each look faced only the movements the defence could make before its shot. Every later phase faced the whole answer for free. Now every phase gets the same limit.

On D2's board it works where the closeout is an answer movement. X3 starts off the Sharpshooter, closes out, and the rotation behind him no longer comes free in later phases. But **D2 itself won't pass from this fix**. In the setup's own shape, X3 covers O2 from B7 inside the shot's reply (Move then Contest), not with an answer movement, and that is untouched here. Fix 3 prices it. Section 4 has the detail.

## 1. Changes to the printed game

None.

## 2. What was built

1. **Every later phase reads like this one (both engines).** The value reads every phase left on this board. Each later phase now starts as a phase does: the offence acts first. A look faces only the defence's movements that come before its shot, two for each turn the offence hands over on the way. A pass, a Dribble or a Screen ends its turn; so does its second action.
   - Before, the later phases faced every movement of the answer at once. A defender who closed out, and every rotation behind him, came free in each of them, however little time the shot left.
2. **This phase is unchanged.** It still counts what's left of the defence's own turn first (D-302). When the defence is mid-turn, this phase and the later ones get different counts, so each keeps its own copy of the contests.
3. **The shortcuts from fix 1 hold the new limit too.** The quick reading and the full reference reading both apply it, and the test that holds one to the other passes.
4. **A lasting test of the proof board.** `tests/test_fix2_every_phase.py`, both engines.
5. **The record.** D-305 added. D-302 now notes that its later phases changed.

## 3. The proof board, before and after

D2's board (E2), with the setup's shape (X1 F10, X2 M8, X4 D4, X5 I5). The reading is the possession's value: this phase first, then each phase after it.

| X3 stands | Before: value, phases | Before: the answer | After: value, phases | After: the answer |
|---|---|---|---|---|
| **C10**, off O2 (the closeout case) | 16; later phases 15 | X3 closes out to B8, X1 to F11, **X2 rotates to M7** | 16; every phase 16 | X3 closes out to B8, X1 to F11 |
| **B12**, off O2 | 16; later phases 15 | X3 to B8, X1, **X2 to M7** | 16; every phase 16 | X3 to B8, X1 |
| **C8**, tight on O2 | 16; later phases 15 to 15.68 | X3 to A7, X1, **X2 to M7** | 16; every phase 16 | X3 to A7, X1 |
| **B7**, the setup's own shape | 15; every phase 15 | X1 to F11, X2 to M7 | 15; every phase 15 | X1 to F11, X2 to M6 |

**What moved.** A closeout used to buy a free rotation in every later phase. X2's step to M7 counted against looks whose shot goes up before the defence has time for a third movement. Now the closeout uses one of the movements the shot allows, phase after phase, and the rotation is gone. Across all 320 shapes with X3 within 3 squares of O2 (every arrow):
- 196 answers got shorter.
- 185 read higher in the later phases.
- 11 read higher overall. None read lower.

**What didn't move, and why.**
1. **X3 at B7 needs no answer movement.** He reaches O2 inside the shot's own reply (Move then Contest, D-261), and every phase gives him that reply fresh. That's the closeout D2 is about, and this fix doesn't touch it. What makes it cost something is the offence punishing it: a shot fake, then the drive past a defender who has used his Move. That's fix 3 (the closeout, then the fake or the drive, as one route).
2. **The 15 isn't only O2's.** O3's look at Q4 and O5's at Q2 also read 15 after the answer. Standing tighter on O2 can't take the number below them.

**The setup search on E2 now picks a different shape:** X1 G10, X2 B7, X3 M6, X4 G4, X5 D6, reading 17.6. The old shape still reads 15 under the new number, so the search ended on a worse shape. Its base positions come from the number too, they moved, and its one-at-a-time climb stopped higher up. This is the search missing a better shape, not the number being wrong. The fix is fix 6: every legal shape on the candidate list, or a cut that provably can't change the answer. A cheaper interim fix: also start the climb from the last shape it chose. E1's setup also changed shape at the same value, 14 (a tie; fix 5 settles ties).

## 4. Times, before and after

One at a time, nothing else running, the engine held to 256 MB:

| Thinking | Before | After |
|---|---|---|
| D2's defence setup (E2) | 32.9 s | 25.5 s |
| D1's defence setup (E1) | 34.9 s | 22.9 s |
| A turn with a shot and blocks in it (E13) | 13.8 s | 12.0 s |

It got faster: with the later phases limited, extra movements pay off less often, so the answers are shorter and fewer candidates get read in full.

## 5. What it proves

| Check | Result | Time |
|---|---|---|
| The proof board (above): 320 shapes, old engine against new | as in section 3 | about 1 min |
| `tests/test_fix2_every_phase.py`: the closeout case, both engines | passed | 6 s |
| The quick reading against the full one, every candidate both ways (`tests/test_fix1_difference.py`) | passed: 0 different, under the new limit | 67 s |
| Engine equality (`tools/js_equivalence.py`, 40 random states) | 0 mismatches | 47 s |
| The rules and the memory tests | 25 passed | 34 s |
| The golden game | 8 passed, no value moved, nothing re-recorded | 81 s |
| The value's own guards (`tests/test_exam.py`: every movement read in full, the memory against a fresh reading, the mix in both engines, both engines on five boards) | 10 passed | 66 s |
| The setups and the turn, timed (section 4) | as above | 2 min 23 s |

These ran in about 6 minutes of wall time. Two Python readings of E2, used to find the cause, added about 3 minutes, about 10 in all. **Not run:** the exam (as asked) and the rest of the suite.

## 6. What in the design couldn't be built as written

- **"Each side's later answer gets only the actions it will really have."** One case of this sits inside a single phase, and it isn't built. A defender who spends his Move in the answer still gets a Move then Contest in his reply, but the rules give each player one Move a phase. The fix: after an answer movement by Move, read that defender's reply as a Quick Step (rushed, if he has one left) or a contest where he stands. It changes decisions, so I left it for you to say, or to fold into fix 3, which reads the closeout and what follows as one route.
- **"Then its next turns as the clock allows."** Built as the reading already worked: the later phases are read on this board, not on the board the offence would leave behind. Each now gets its own count of the defence's movements, but the offence's men don't move on between phases. Reading the real next board is what the look-ahead does (D-268), at a turn's cost per level.
- **The offence's side of the rule** was already built in every phase: its routes are limited by the actions it has (D-294).

## 7. For Shaun to decide

1. Whether a defender who used his Move in the answer should lose his reply Move (section 6). I'd build it with fix 3.
2. Whether the setup search should also start from its last chosen shape while fix 6 is pending (section 3).

## 8. Noticed, not touched

- The answer now stops earlier on many boards: shorter answers on 196 of the 320 E2 shapes. The Coverage view's answer arrows will show fewer moves.

## 9. Model for the next step

Claude Opus 5.5, effort high. Fix 3 (two-step routes, and fakes read inside the number) is the one that moves D2, and it touches both engines' route sum.
