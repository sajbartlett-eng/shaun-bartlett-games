# Step 27: the computer sets up the way it plays

1. **The offence now places by the same list the in-play search uses.** Placements are read against the defence's full setup and then ahead, and the table's spread squares are always read in full beside the winner. On all three boards it beats the table squares: 26 and 22 against 26 and 18, then 27.6 against 21, then 24 against 18.
2. **High-Low no longer bunches four in the key.** Board 1 now puts two in the key, both with a job: O2 re-screens and O4 screens and dives. Candidate squares are no longer a rule. They are kept as a check.
3. **The computer reads as far ahead as the plan needs: up to three turns, both sides alike.** That is where screen then dive, the re-screen, the swing, the V-cut, the seal and Hesitate now show up. In play it re-reads every phase. Reading a fourth turn changes no choice on any of the three boards.
4. **Three seconds and the closely guarded count go by the rule.** There are no halves or thirds any more. After a three-second violation the count doesn't restart: still in the key at the next phase end, he is called again.
5. **Look for:** the offence setup button takes 85 to 111 seconds and the defence's 72 to 84, all under 2 minutes. A computer turn in play took 16.2 seconds. On two boards the Post Scorer C still starts in the corner. The table squares put him there, and the check flags it.

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

These are single readings from `docs/runs/step27/checks.json`, using both buttons. **Like for like:** every worth below is the same reading. Each placement is read against the full defence the defence would set for it, then ahead to the same three-turn limit. The table squares get the same treatment. Each worth is the list's first five items: the offence's best looks and gaps, largest first.

**Board 1, High-Low v Shoot and Protect.**
- **Offence:** O1 I11 (ball, passer), O2 J3 (re-screen), O3 D7 (spacing), O4 J4 (screen, then the dive), O5 Q3 (screener and shooter). Two in the key.
- **Plan:** a post shot for O5 on G2 after he screens X5 and rolls. Read ahead, it needs 3 turns: O4 screens X5 from I3, then O2 screens X5 from I2.
- **Line:** "Attention: O3 holds X1; O1 holds X3; O4 holds X5. Hole: G2, the green zone. Access: O5's screen, then the pass to O5."
- **Rejected:** the table squares. They lost because "its second look reads 18 against 22 once the full defence answers."
- **Worth:** 26, 22, 21, 18, 4.7 (a one-turn reading gave 21, 18, 18, 16, 4.7). The table squares read 26, 18, 18, 16, 15.
- **Defence:** X1 L3, X2 E6, X3 K4, X4 M7, X5 H3.
  - X5 on H3 stands between O4 (on J4) and the rim.
  - Nobody stands between O5 and the rim: he starts in the corner.
  - Avoided: X4 on O1 at the arc.
- **X4 and X5 no longer press the ball far out.** No defender is within three squares of the ball. By the list, the offence's best looks are inside (O4's screen and dive, the re-screen, O5's roll). Three of the four ways the defence read ahead hold the top item to 26 or less only with X4 and X5 inside.
- **Checks:**
  - every attacker has a job;
  - every defender has a real job;
  - O5 is a body in the corner (flagged).
- **Times:** offence 110.5 s, defence 71.6 s.

**Board 2, Twin Towers v Lockdown.**
- **Offence:** O1 N7, O2 C9 (screen, then the dive), O3 O9 (screener), O4 N10 (ball, passer), O5 J3 (shooter). One in the key.
- **Plan:** a post shot for O5 on G2 off O3's screen on X4. Read ahead, it needs 3 turns: O2 screens X2 from C6, then O5 screens X4 from H3.
- **Line:** "Attention: O4 holds X1; O2 holds X2; O3 holds X3. Hole: G2, the green zone. Access: O3's screen, then the pass to O5."
- **Rejected:** the table squares, 21 against 27.6.
- **Worth:** 27.6, 22, 20, 18, 9 (one turn: 18, 18, 18, 9, 5.6). The table squares read 21, 18, 18, 7.2, 6.
- **Defence:** X1 L5, X2 D7, X3 M6, X4 I4, X5 K4.
  - X4 stands beside O5 on the block, and X5 is next to him too.
  - Nobody is nearer the rim than O5: he is right under it.
- **Watching (the plans it means to deny):**
  - O1's flash cut to H5;
  - O1's floater over X4's contest.
- **Check:** every attacker has a job.
- **Times:** offence 85.3 s (two full reads: the leader held), defence 74.9 s.

**Step 24's high-screen board.**
- **The setup buttons** (High-Low v Run and Gun) place O1 L5 (re-screen), O2 M4, O3 J2 (screen, then the dive), O4 I11 (ball), O5 Q3 (screener and shooter). One in the key.
- **Plan:** a post shot for O5 on G3 after he screens X3 and rolls. Read ahead, it needs 3 turns: O3 screens X3 from H3, then O1 screens X2 from N5.
- **Rejected:** O3 on O9 instead of J2. It lost 21.75 against 24.
- **Worth:** 24, 22, 22, 22, 9 (one turn: 18, 14, 12, 11.75, 0). The table squares read 18, 16, 15, 15, 14.
- **Defence:** X1 K3, X2 M6, X3 J5, X4 H4, X5 F7. Of its four ways read ahead, it leaves the least: 21.75 at the top of the list.
- **Times:** offence 107.9 s and defence 84.4 s, timed on its own (`checks_high_screen_timed_alone.json`). The run beside the tests took 124.7 s, so I lowered the full-read cap to 95 s. The pick is the same either way: it came from the first full read.
- **Does the corner dive appear?** On step 24's own board, yes. It is read at once: O3 from the corner to K3, worth 32, third on the list. Read ahead to four turns, nothing beats the 36 already on this turn, so the board pays now (`ahead.json`). On the new setup the corner player is O3 on J2, and his screen then dive is the route's first turn.

**In play:** one All-Star offence turn on the high-screen board took 16.2 seconds, including the phase's read ahead (`turn.json`).

## 4. Lookahead, part by part

| Part | Before | After | Why | Time |
|---|---|---|---|---|
| Offence setup ranking | One turn against the defence's quick setup. Only the pick got the full setup. | The quick best, plus the table squares, read against the full setup and then ahead up to 3 turns. All read the same number of turns ahead. | Quick and full disagreed (step 26: 24 against 6). Entry passes, screen then dive and seals need 2 or 3 turns. | 85 to 111 s |
| Defence setup | The settlement and the matchup rule, one turn. | The same, then its last four ways of standing read ahead 3 turns. | Both sides read to the same horizon. | 72 to 84 s |
| In-play plan (once a phase) | The one-phase map. | Plus 3 turns ahead (12 s cap). The route's first turn breaks the search's ties, after the list. | Nothing is locked: it re-reads every phase. | 16.2 s a turn |
| In-play search | Rookie 1 to 2 moves in 0.3 s, Starter 2 to 3 in 1 s, All-Star 4 to 6 in 2.5 s. Each ends on the list's top item. | Unchanged. | It already reads turn by turn by the rules. Changing it moves all computer play and every golden value. | as before |
| Shot bar | Phase by phase to the end of the clock. | Unchanged. | It already reads to the horizon. | as before |
| Screen finder | One turn, judged by the lasting gap with a 0.5 margin. | One turn, judged by the list. | D-219. | as before |
| Conditions | One turn of the map. | Plus 8 read from the route ahead. | The two-step ones need a second turn. | inside the plan |
| Trainer and reports | One turn of the map. | Unchanged. | They grade and show the reading the search ends on. | as before |

**Why three turns:** every placement compared must be read the same number of turns ahead. A fourth turn adds about 8 seconds a placement and pushes setup past 2 minutes. **The four-turn check:** each board's top two placements, read four turns ahead, keep the same order on all three boards (`four_turns.json`). Board 1's winner reads 26, 22, 21, 18, 11.2 at four turns, against 26, 18, 18, 16, 15. Board 2's reads 28, 22, 20, 18, 9, against 22, 21, 18, 18, 8.

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
- **Turn time and setup time:** the full reads stop by 95 s, so a setup ends under 2 minutes.
- **Speed filter:** none. The sweep skips only squares another piece stands on and, for the ball handler, squares off plain wood. The rules forbid both.
- **"Until the choice no longer changes":** the full reads go in the quick order. The table squares are always included, so a bunch that only reads well against the quick defence can't win. It stops once the leader has held through two more full reads, or once the full reads reach 95 seconds. Two or three full reads fit on each board, and the leader never changed after its first full read.
- **The screens read ahead** are the best by the list that the screener can set this turn: from where he stands, or after his own one Move.
- **The defence's turn ahead:** it is the turn its in-play search tries first: its map answer, each part of it, the settlement's moves, or holding. It is chosen by the list.

## 9. For Shaun to decide

1. **The map's own answer leads by the lasting gap** (both engines). D-219 says the list leads there too. Switching it changes the lasting gap everywhere. Switch it, or keep it?
2. **The read-ahead treats a pass as landing (or not) its likeliest way.** Pricing the chance in needs a rule for combining two lists. One option is to keep the likelier outcome unless the miss costs more than the catch gains.
3. **Should the route replace the "Plan:" line?** Today the plan is the one-turn plan and the route ahead is its own line. They can name different shooters.
4. **The three-turn cap** (D-258). Four turns changed no choice here (section 4).
5. **The Post Scorer C in the corner** on boards 1 and 3. The table squares put him on Q3, and nothing in the list moved him. The check flags it. A rule would steer, so that is your call.


## 10. Tests

- **Pass:**
  - `test_step27`: all 9 on the final code.
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
