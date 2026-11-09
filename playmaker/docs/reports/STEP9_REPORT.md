# Step 9 report: evidence for every failing exam board

## 1. Changes to the printed game

None.

## 2. What changed

- **Step 8 merged** (pull request 52). Branch `step-09-exam-evidence` from `main`. Shaun's answers are applied:
  - **The rules check** now searches today's printed wording, and still tests the same numbers:
    - "Intercept or steal −5, lose 2 seconds";
    - "Intercepted: −5";
    - "Foul on a steal +5, play on";
    - "Foul: +5 to them".
  - **D-94** notes that the six advantage states (in `archive/engine/advantage.py`) are kept as the trainer's
    vocabulary for step 16, alongside the coverage shares (D-95).
  - **D-77** is ruled: scenario 10 plays with the card's numbers.
  - **The app's copy of the playing levels sheet** is replaced with `reference/Playmaker_Playing_Levels.pdf`. The old
    copy was identical to `archive/reference/Playmaker_Playing_Levels_pre9nov.pdf`, so it is already archived.
- **The searches.** New tools: `tools/exam_evidence.py` and `tools/exam_evidence.js`.
  - The JavaScript is the app's own search, which `tools/js_equivalence.py` proves equal to the Python search. It runs
    about ten times faster.
  - Each board lists every legal turn for the side to act and applies the board's own judge to each one.
  - The step 6 run didn't record how far ahead the computer looked on the clock, so I re-measured it with the same
    settings (Python, the All-Star's 2.5 seconds). Every board looked 1 move ahead, plus part of the next on most.
  - The searches then ran to 4 moves ahead, and to 5 and 6 while the board's 10 minutes lasted.
  - Raw numbers are in `docs/runs/step9/exam_evidence.json`.
- **Where a judge had to be split:**
  - **Two-copy boards** (5, 7, 11): each copy is judged by its half of the judge, copied word for word. A check on several
    hundred pairs per board found 0 disagreements with the whole judge.
  - **Board 2** compares its copies, so each copy is judged against the computer's own clock choice on the other copy.
  - **Board 4:** its first half is fixed by the board, not the move, so it is computed once.
  - **Board 16:** its own method (`drain_line`), traced turn by turn. Its first-turn part uses the trainer's reading of
    each move away from the ball.
  - **C1:** its lane check is read unchanged from the archived code.
- **The exam book:**
  - every listed board has an "Evidence" section: the result, the values table, then the facts;
  - the index carries each result;
  - the words live in `tools/exam_book_words.py`.

## 3. What it proves

- **The rules check** (`tests/test_rules_current.py`): 18 pass.
- **The results.** "Speed", "Valuation or board" and "Met" are the step's three answers. I added two more where
  neither fits:
  - **Level:** the choice and the accepted move read the same at every look, so the computer's tie-break decides.
  - **No move can meet the judge:** nothing the side to act does can pass it.

| Board | Result |
|---|---|
| 2 Sag by shooting | Level at 4 moves ahead. Met on this run's clock, failed in step 6: the choice moves with timing. |
| 3 Help the helper | Valuation or board: the choice is ahead by 3.4, 11.7 and 17.1 at 1, 4 and 5 moves ahead. |
| 4 Two jobs, one defender | No move can meet the judge: the computer doesn't see X5 as stretched. |
| 5 Closeout | A met; B valuation or board, by 9.0 at 4 and 5 moves ahead. |
| 6 Catch window | Speed, narrowly: level at 1 and 4 moves ahead, the accepted move 0.2 ahead at 5. Fragile. |
| 7 Clock | A met; B valuation or board, by 19.5 at 4 moves ahead. |
| 8 Backdoor | Valuation or board, by 5.1 at 4 moves ahead and 0.3 at 5. |
| 11 Contested pass | A met (the pass to O2 isn't legal); B valuation or board, by 0.5 at 4 moves ahead. |
| 13 Spacing | Level: every move reads 24.9 at every look. |
| 14 Variety | Valuation or board: O1 to K10 is best by 4.8 and 2.2 at 4 and 5 moves ahead, above the 2-point variety margin. |
| 16 Wearing out one defender | Valuation or board, by 5.1 at 4 moves ahead. |
| T1 An early cut | Fails: the better order is worth 0.75 against the bar of 3 (0 with today's phase table). |
| T2 The decoy | Fails: today X1 is the one who answers the lift, and the review names him. |
| C1 Deny the shooter's catch | Met: X1 and X3 cover the passes to O2. |
| C2 Prefer the clean pass | Met, but both passes arrive 40%: the clean pass isn't clean today. |

- **Speed accounts for none of the failures,** apart from board 6, which is fragile:
  - an earlier run of board 6 that by mistake went past the cap reached 6 moves ahead, where the computer's choice was
    5.9 ahead;
  - nothing else overtakes when the computer looks further.
- **Time:**
  - 133 minutes of board time, four boards at once: about 80 minutes of wall time;
  - 6 moves ahead finished on no board (5 is the deepest).
- **Over the cap:**
  - C1 took 12.5 minutes. Judging 1.2 million defensive turns took 11.8 of them.
  - Board 2 ran 40 minutes before I stopped it and cached its contest check (same answer, read once per case). It then
    took 10.3 minutes.
  - Board 4 was restarted once, with its fixed half computed once.
- No board, judge or engine value changed. The exam, self-play and games were not run.

## 4. For Shaun to decide

Each "valuation or board" board, with the fact most likely to settle it:

- **3:** X1, though beaten, can quick-step back beside O1 and hold his look to 22. If the low man X4 steps up instead,
  O1's look rises to 31. Is the help-the-helper rotation right here?
- **5 (B):** where O2 stands, X4 can close out from the corner and Contest (30). One square up, at B8, nobody can reach
  him: an open three worth 39. Is stepping up for the open three a wrong answer?
- **7 (B):** the last phase still holds 6 tokens, up to three offence turns. The phase table puts such a possession at
  29.3; the contested two is worth 10. Should the last phase mean "shoot now"?
- **8:** the backdoor pass arrives half the time (X1 or X2 can step into it), and a lost pass ends the possession at 0.
  The cut with the pass is worth 12.5; the cut alone 24.9.
- **11 (B):** the pass to O2 isn't legal: X2 stands next to O2 on the line and denies it. The board can't test the
  pass it describes.
- **14:** at 4 and 5 moves ahead one first move leads by more than the 2-point variety margin. This is D-97: widen the
  margin, restate the board, or accept it.
- **16:** the computer's line uses up X2's Move and Quick Step, but by then O2 has moved to the corner. With X2 spent
  and O2 on the wing, O2's catch is worth 39 against 30.

Not "valuation or board", but also for Shaun:

- **2 and 13 (level):** see section 5.
- **4:** no move can meet it; the pass to O5 is denied by X5.
- **6 (speed, narrowly):** the open corner three is worth 33 against 24.9 for the possession. The screen it chose adds
  nothing over the shot.
- **C2:** the "clean" pass is no longer clean under today's rules. Rebuild or drop it.
- **T1 and T2:** the tests' expectations predate Contest as an action.

## 5. Noticed, not touched

- **The phase table sets the floor of the computer's reading (D-92)** on most boards here:
  - one move ahead, many moves read exactly 24.9, the table's value for phase 1;
  - board 13 reads 24.9 everywhere, at every look;
  - T1's orders all read 24.9 with today's table.

  This is evidence for step 13.
- **On the clock the computer's choice is not always the search's best.** On board 3 it played X2 and X5's moves over
  X1's recovery. Its plan-keeping and its random pick among near-equal turns can override the search.
- **Two archived tests' boards** (C1 from the tabletop setup; C2 with O5 out of bounds as the inbounder) are measured
  as stored.
