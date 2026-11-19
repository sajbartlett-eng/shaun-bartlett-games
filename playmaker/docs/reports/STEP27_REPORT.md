# Step 27: the computer sets up the way it plays

1. **The offence now places by the same list the in-play search uses.** Placements are read against the defence's full setup and then ahead, and the table's spread squares are always read in full beside the winner. On all three boards it beats the table squares: 24 against 20, 28 against 18, and 24 against 21.
2. **No more bunching on High-Low.** Board 1 now puts one attacker in the key, not four. Candidate squares are no longer a rule. They are kept as a check.
3. **The computer reads as far ahead as the plan needs: up to three turns, both sides alike.** That is where screen then dive, the swing, the V-cut, the seal and Hesitate now show up. In play it re-reads every phase.
4. **Three seconds and the closely guarded count go by the rule.** There are no halves or thirds any more. After a three-second violation the count doesn't restart: still in the key at the next phase end, he is called again.
5. **Look for:** the offence setup button takes 102 to 109 seconds and the defence's 48 to 83, both under 2 minutes. A computer turn in play took 13.5 seconds. On two boards the Post Scorer C still starts in the corner. The table squares put him there, and the check flags it.

## 1. Changes to the printed game

None. The repeat three-second rule is for the app only (D-254).

## 2. What changed

- **`plan.py`:**
  - `horizon_read`, the read-ahead. It goes turn by turn: the offence's turn, the defence's turn by the list, then the phase end and its counts, all by the rules.
  - `place_offence` rebuilt: a quick search over every legal square, then full reads in the quick order. The table squares are always read. No `must` step.
  - `place_defence` reads its last ways of standing ahead the same number of turns.
  - `plan_status` re-reads ahead once a phase.
  - The screen finder judges by the list (an audit fix).
  - The "every attacker has a job" check, the alternative line, and the route line.
- **`agent.py`:** in play, when the list ties, the turn that takes the route read ahead wins, then the plan's worth.
- **`conditions.py`:** `ahead()` reads 8 conditions off the route. 37 are read now, 32 still aren't.
- **Both engines:**
  - three seconds by the rule (D-255);
  - closely guarded by the rule (D-256);
  - the repeat violation (D-254).
  - `engine.js` can also hand back the moves of its own best answer (`answer`).
- **Rules text:** `RULES_CURRENT.md`, the register, the help text, the IN KEY chip and the coach line all carry the repeat rule.
- **Records:** `CLAUDE.md` gets "Measures and concepts". `DECISIONS.md` gets D-254 to D-260, and D-240 is closed.
- **New files:** `tools/step_27.py` and `tests/test_step27.py`.

## 3. The board readings

These are single readings from `docs/runs/step27/checks.json`, using both buttons. **Like for like:** every worth below is the same reading. Each placement is read against the full defence the defence would set for it, then ahead to the same three-turn limit. The table squares get the same treatment.

**Board 1, High-Low v Shoot and Protect.**
- **Offence:** O1 I11 (ball, passer), O2 J3, O3 D7, O4 A3, O5 Q3 (screener and shooter). One in the key.
- **Plan:** a post shot for O5 on J4 after he screens X2 and rolls. Read ahead, it needs 2 turns: O1 swings to O2, and the board reads 24.
- **Line:** "Attention: O5 holds X1; O2 holds X2; O1 holds X3. Hole: J4, the green zone. Access: O5's screen, then the pass to O5."
- **Rejected:** O4 on J4 instead of A3 (two in the key). It lost because "its best look reads 21 against 24 once the full defence answers."
- **Worth:** 24, 22, 20, 20, 15. The table squares read 20, 18, 18, 15, 9.
- **Defence:** X1 D4, X2 G8, X3 J2, X4 M6, X5 K4. X3 and X5 stand inside, nearer the rim than the bigs, but the bigs start at A3 and Q3, so nobody stands between them and the rim. Avoided: X4 on O1 at the arc.
- **X4 and X5 no longer press the ball far out.** The nearest defender to the ball is X2, three squares off. By the list, the offence's best looks are inside (O5's roll, the swing), so its four ways of standing all hold the top item to 24 with X4 and X5 inside.
- **Checks:**
  - every attacker has a job;
  - every defender has a real job;
  - O5 is a body in the corner (flagged).
- **Times:** offence 102.8 s, defence 76.5 s.

**Board 2, Twin Towers v Lockdown.**
- **Offence:** O1 N7, O2 C9, O3 O9 (screener), O4 N10 (ball, passer), O5 I2 (shooter). One in the key.
- **Plan:** a post shot for O5 on G2 off O3's screen on X3. Read ahead, it needs 3 turns: O4 swings to O3, then O5 moves to J3.
- **Line:** "Attention: O5 holds X1; O1 holds X2; O3 holds X3. Hole: G2, the green zone. Access: O3's screen, then the pass to O5."
- **Rejected:** O5 on J3 instead of I2. Its best look reads 22 against 28.
- **Worth:** 28, 24, 22, 9, 5. The table squares read 18, 18, 16, 8.2, 6.
- **Defence:** X1 F7, X2 N4, X3 K5, X4 L10, X5 D5. Nobody stands between O5 and the rim: he is on I2, right under it.
- **Watching (the plans it means to deny):**
  - O1's cut behind the help to J3;
  - O1 attacking X2, its most foul-prone defender.
- **Check:** every attacker has a job.
- **Times:** offence 109.3 s, defence 48.2 s.

**Step 24's high-screen board.**
- **The setup buttons** (High-Low v Run and Gun) place O1 L5, O2 M4, O3 J2, O4 I11 (ball), O5 Q3.
- **Plan:** a post shot for O5 on G3 after he screens X3 and rolls. Read ahead, it needs 3 turns: O3 screens X3, then O1 V-cuts to N5.
- **Rejected:** the table squares. They lost 21 against 24.
- **Defence:** X1 K3, X2 M6, X3 J5, X4 H4, X5 F7.
  - It kept its matchup pick, which leaves 26 at the top of the list read ahead. Another way of standing leaves 24.
  - That is the All-Star's 2-point margin (D-208): within it, the matchup rule chooses.
- **Times:** offence 102.4 s, defence 83.2 s.
- **Does the corner dive appear?** On step 24's own board, yes. It is read at once: O3 from the corner to K3, worth 32, third on the list. Read ahead to four turns, nothing beats the 36 that is already on this turn, so the board pays now (`docs/runs/step27/ahead.json`). Screen then dive is read where it pays: on board 1's old setup, the screener's dive goes from 13.75 to 22 after the screen (a test).

**In play:** one All-Star offence turn on the high-screen board took 13.5 seconds, including the phase's read ahead (`turn.json`).

## 4. Lookahead, part by part

| Part | Before | After | Why | Time |
|---|---|---|---|---|
| Offence setup ranking | One turn against the defence's quick setup. Only the pick got the full setup. | The quick best, plus the table squares, read against the full setup and then ahead up to 3 turns. All read the same number of turns ahead. | Quick and full disagreed (step 26: 24 against 6). Entry passes, screen then dive and seals need 2 or 3 turns. | 102 to 109 s |
| Defence setup | The settlement and the matchup rule, one turn. | The same, then its last four ways of standing read ahead 3 turns. | Both sides read to the same horizon. | 48 to 83 s |
| In-play plan (once a phase) | The one-phase map. | Plus 3 turns ahead (12 s cap). The route's first turn breaks the search's ties, after the list. | Nothing is locked: it re-reads every phase. | 13.5 s a turn |
| In-play search | Rookie 1 to 2 moves in 0.3 s, Starter 2 to 3 in 1 s, All-Star 4 to 6 in 2.5 s. Each ends on the list's top item. | Unchanged. | It already reads turn by turn by the rules. Changing it moves all computer play and every golden value. | as before |
| Shot bar | Phase by phase to the end of the clock. | Unchanged. | It already reads to the horizon. | as before |
| Screen finder | One turn, judged by the lasting gap with a 0.5 margin. | One turn, judged by the list. | D-219. | as before |
| Conditions | One turn of the map. | Plus 8 read from the route ahead. | The two-step ones need a second turn. | inside the plan |
| Trainer and reports | One turn of the map. | Unchanged. | They grade and show the reading the search ends on. | as before |

**Why three turns:** every placement compared must be read the same number of turns ahead. A fourth turn adds about 8 seconds a placement and pushes setup past 2 minutes. A four-turn check of each board's top two placements is in `docs/runs/step27/four_turns.json` (see section 9).

## 5. The audit: every place the computer judges a board

| Where | Reading | How far | Costs counted | Stand-in? | Verdict |
|---|---|---|---|---|---|
| In-play search, where it stops | the list's top item, then the list on ties | its own moves ahead, then one turn | Steal, counts, lost pass | none | deliberate (D-219, D-223) |
| The map's own answer (`lasting`, both engines) | **the lasting gap first, then the list** | one turn | as above | stands in for "the list leads in the map's own answer" (D-219). No test fails if they differ. | **leftover, for Shaun:** fixing it moves the lasting gap everywhere in both engines |
| Offence setup | the list | 3 turns, full defence | as above | retired: "the best plan's value" no longer ranks placements | fixed (test: full read equals ranking) |
| Defence setup | the list, then the matchup rule within the level's margin | one turn, then 3 for the finalists | as above; the beat priced by summed squares (D-243) | the sum is Shaun's ruling | deliberate |
| Screen finder | was the lasting gap + 0.5 | one turn | as above | **a fixed margin standing in for "builds more"** | **fixed** (new test) |
| Read-ahead (new) | the list | up to 3 turns | as above, plus phase-end counts | **a pass lands its likeliest way, standing in for its chance**; the turns tried are screens, passes, Hesitate, and a move then Hesitate (not every legal turn) | listed for Shaun (pricing a chance into a list needs a design choice) |
| Read-ahead, the defence's turn | the list | one turn | holding costs a token (read as its Pause) | small | built that way, noted |
| Plan (`read_plan`) | the full map's look left after the answer | one turn | as above | its "Plan:" target is the one-turn plan; the route ahead is now its own line | listed for Shaun |
| Shot bar | the value of playing on | the clock | lost pass −5, lost Dribble 0 | none | deliberate (D-242) |
| Conditions ruled in | a look's worth against the bar | one turn against the clock | as above | different horizons by design, the same unit (points at real chance) | deliberate (D-242, D-244) |
| Every-attacker-has-a-job check | his own looks, roles, defenders drawn | one turn | none | a check, never a rule | noted |
| Old setup search (`setup.search`, off) | the lasting gap leads in its sweep | one turn | as above | leftover in a path nothing uses | listed |
| Reports, Watch, trainer | the map; phase starts read fresh | one turn | as above | none | deliberate (step 20) |

**The three seconds and closely guarded:** the halves and thirds were fixed fractions standing in for the rule. They are gone, and three tests now fail if they come back.

## 6. Conditions now read

**Read from the route ahead:**
- screen, then the dive;
- the off-ball seal;
- the V-cut;
- Hesitate;
- swing;
- extra pass;
- re-screen;
- relocate after passing.

37 are read in all.

**Still not read (32), each with its reason in `conditions.py`:**
- fronting, denial, backdoor, rejecting a screen, curl or fade: the board records no stance;
- stagger and screen the screener: two screens in a row;
- handoff;
- the L-cut;
- drift on a drive;
- transition, and the scenario-card ones.

## 7. The Sharpshooter question

This is the morning board's settlement as it stands. I changed nothing (`sharp.json`).

- **Who is left most open:** with three defenders able to reach the Sharpshooter's best look, the most open other attacker is O3. He has a three on Q7: it goes up every time, it is worth 24 open, and he is held to 15.
- **The Sharpshooter's own best look:** a three from I10, held from 33 to 21.
- **If the pass were cut instead** (X2 to D9, the pass lands 0 times in 100), the Sharpshooter's best is still that three from I10, 21: he relocates to catch there. O3's three on Q7 goes fully open at 24, and the list's top rises from 21 to 24.
- **So by the list, cutting the pass makes the defence worse.** That is why the sense check still fails. I left it failing.

## 8. Built differently from the prompt, and why

- **It reads ahead in turns, not phases.** A screen and the dive after it happen inside one phase. The phases crossed are reported too.
- **Speed filter:** none. The sweep skips only squares another piece stands on and, for the ball handler, squares off plain wood. The rules forbid both.
- **"Until the choice no longer changes":** the full reads go in the quick order. The table squares are always included, so a bunch that only reads well against the quick defence can't win. It stops once the leader has held through two more full reads, or at about 110 seconds. Three full reads fit on each board, and the leader never changed after its first full read.
- **The defence's turn ahead:** it is the turn its in-play search tries first: its map answer, each part of it, the settlement's moves, or holding. It is chosen by the list.

## 9. For Shaun to decide

1. **The map's own answer leads by the lasting gap** (both engines). D-219 says the list leads there too. Switching it changes the lasting gap everywhere. Switch it, or keep it?
2. **The read-ahead treats a pass as landing (or not) its likeliest way.** Pricing the chance in needs a rule for combining two lists. One option is to keep the likelier outcome unless the miss costs more than the catch gains.
3. **Should the route replace the "Plan:" line?** Today the plan is the one-turn plan and the route ahead is its own line. They can name different shooters.
4. **The three-turn cap** (D-258). The four-turn check is below.
5. **The Post Scorer C in the corner** on boards 1 and 3. The table squares put him on Q3, and nothing in the list moved him. The check flags it. A rule would steer, so that is your call.

**The four-turn check** (`four_turns.json`): see the note at the end of this report.

## 10. Tests

- **Pass:**
  - `test_rules_current`, golden, and engine equality (`test_step3n`): 47 pass, with the same 3 expected failures. The engines agree on all 40 random boards.
  - `test_step24` (the separate-thinking test included), `test_web`, `test_map_logic_21`, `test_step22`, `test_drivers_22b`, `test_coverage_18s`, `test_step26`, `test_step22c`, `test_points_play_on_18r`, `test_fiba_18i`.
- **New, `tests/test_step27.py`:**
  - the repeat violation;
  - three seconds cost nothing for a shot in time;
  - closely guarded by the rule;
  - the full-defence ranking equals a full read of every placement;
  - no attacker is forced onto a square;
  - screen then dive reads higher, for both sides' readings;
  - both sides read the same turns ahead;
  - the conditions read ahead;
  - screens judged by the list.
- **Re-recorded, each with a note:**
  - `test_step26` (no half);
  - `test_step22c` (no thirds);
  - `test_coverage_18s` (the layup's cost is 0);
  - `test_points_play_on_18r` (the count doesn't restart).
- **Fail, as before:**
  - `test_two_responsibilities_22b`, sense check 3 (section 7);
  - `test_setup_18o`, timing (speed waived, D-200).

## 11. Model for the next step

Claude Opus 5.5, effort high. Choices 1 and 2 touch both engines' readings.
