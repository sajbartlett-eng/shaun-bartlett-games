# Step 28: the contest costs an action, one reading everywhere, and the defender's stance

## 1. Changes to the printed game (for Shaun to approve)

The printed game already makes the Contest an action, the reply's last (D-18). Shaun's ruling (D-261) is Shared, so the pages below need only plain wording that the reply is one turn of 2 actions for the whole team, with the Contest one of them. I have not edited the printed files.

| Page | Now | Drafted wording |
|---|---|---|
| Rulebook, page 2, "Shooting" | "Declare a Shot. The defence reacts with up to 2 actions from its tokens. The last may be a Contest: 1 token, one defender next to the shooter. Sprint, then Contest, closes out." | "Declare a Shot. The defence replies with one turn of up to 2 actions, shared by the whole team. Contesting is one of them, and the last: 1 token, by one defender next to the shooter. So the most the defence can do is one movement and the Contest. Sprint, then Contest, closes out. Nobody contests: the shot is open (contest 0)." |
| Defence tracker, page 1, "CONTEST AN ACTION: 1 TOKEN" | "Shot declared: react with up to 2 actions from your tokens... Contest is the last action: one defender next to the shooter. Close out: Sprint, then Contest. No Contest: contest 0." | "Shot declared: one reply turn of up to 2 actions for your whole team. The Contest is one of them, the last, by one defender next to the shooter. Close out: one movement, then the Contest. Spend both on movement and nobody contests: the shot is open." |
| Offence tracker, page 1 | "Defence reacts: up to 2 actions, Contest last." | "The defence replies: 2 actions for the team, the Contest one of them. At most one movement and the Contest, as you get one movement and the shot." |
| Defence first-game guide, page 1, "DEFEND THE SHOT" | "After their Shot: up to 2 actions. The last can be a Contest by one defender next to the shooter (you pick who). Sprint, then Contest..." | "After their Shot: one reply turn of up to 2 actions for your whole team. The Contest is one of them, the last, by one defender next to the shooter (you pick who). Two movements and nobody contests. Sprint, then Contest, closes out." |
| Offence first-game guide, page 1 | "A Shot is a declaration. The defence reacts first: up to 2 actions, a Contest last." | "A Shot is a declaration. The defence replies first with one turn of up to 2 actions for the team. The Contest is one of them, so it gets one movement and the Contest at most, as you get one movement and the shot." |

The table's contest values don't change. The normal and hard Contest on inside shots stays an app rule (Split), as D-191 to D-194 made it.

## 2. In five lines

1. **The contest costs an action, in the app as at the table.** After a shot the defence has one reply turn of 2 actions. Contesting is one of them, so it gets one movement and the Contest at most. Nobody presses Contest: the shot is open.
2. **Inside shots offer a choice.** The normal Contest (the hand up, never a foul) or the hard one (the block, at the full rating with its foul rolls). Jump shots keep the position table.
3. **One reading everywhere.** The map's own answer now leads by the list. The read-ahead counts both outcomes of a pass. The Plan line is the route the computer actually chases. It reads four turns ahead.
4. **The defender's stance is read from his square and arrows:** front, three-quarter, deny, behind, cheating over or going under a screen. That opens the post entry against the front, backdoor, reject the screen, curl or fade, stagger and screen the screener.
5. **Look for:**
   - the Contest button on every shot, with the hard Contest offered inside;
   - shots going up open when the defence spends its two actions moving;
   - the Plan line naming the route's turns, and setups of about 50 to 112 seconds.

## 3. What changed

- **Both engines** (`engine.js`, `decide.py`, `scoring.py`, `resolve.py`, `actions.py`, `search.py`):
  - the Contest as an action (`rules.contest_costs`, D-261), with its normal and hard options;
  - no free hand-up;
  - one movement before the contest everywhere the map reads the race;
  - the map's answer led by the list (D-262; `eval.answer_lead: "gap"` puts the gap first);
  - the takeover settles in one read.
- **`plan.py`:**
  - both outcomes of a pass read ahead (D-263);
  - `route_plan`: one plan on screen (D-264);
  - the job search (D-265);
  - four turns ahead (D-268);
  - the leader and the table squares always read in full.
- **`conditions.py`:** the stances and the 11 conditions they unlock (D-267). The defence names its stances.
- **The app:**
  - the reply-turn line, the Contest buttons with "contests hard (the block)", the help text, the coach line and the tip;
  - `RULES_CURRENT.md` and the register.
- **Tests:** sense check 3 rewritten to test the outcome (D-266).
- **Records:** `DECISIONS.md` D-261 to D-268.
- **New files:** `tools/step_28.py` and `tests/test_step28.py`.

## 4. The board readings

These are single readings with both buttons (`docs/runs/step28/checks.json`, `morning.json`). Every worth is the same reading: each placement is read against the full defence the defence would set for it, then four turns ahead.

**Board 1, High-Low v Shoot and Protect.**
- **Offence:** O1 J3 (screener), O2 C9, O3 I11 (ball), O4 G1 (screener), O5 H3 (the shooter). Three in the key, but O1 and O4 are screeners.
- **Plan (the route, 4 turns):** O1 screens X5 from I4; then O3 swings to O2; then O4 screens X2 from G3 (a stagger); then a post shot for O5 on G2.
- **Worth:** 34, 30, 30, 23.6, 15. The table squares read 24, 20, 15.6, 15, 15.
- **Defence:** X1 I10, X2 N7, X3 G4, X4 D6, X5 I5. X1 plays behind O3, the ball handler.
- **Between the bigs and the rim:** nobody. O5 is on H3 under it; O4 is on the baseline at G1.
- **Best shooter:** O1 (three 9), screening from J3. X5 on I5 is two squares off.
- **Post Scorer in the corner?** No: he is on H3.
- **Times:** offence 81.0 s, defence 67.7 s.

**Board 2, Twin Towers v Lockdown.**
- **Offence:** O1 J3 (shooter), O2 J4, O3 K4 (screener), O4 I13 (ball), O5 Q3. Three in the key.
- **Plan (2 turns):** O3 screens X5 from J6; then a floater for O1 on M2.
- **Worth:** 30, 28, 28, 18, 5.2. The table squares read 24, 15, 14, 6, 0.3.
- **Defence:** X1 F5, X2 N7, X3 I10, X4 I6, X5 I7. No stance beyond sagging.
- **Between the bigs and the rim:** nobody. O4 is up top with the ball; O5 is in the corner.
- **Best shooter:** O2 (three 9) on J4. X5 on I7 is his man; X4 is two squares off.
- **Post Scorer in the corner? Yes, O5 on Q3.** Why by the list: the wider search tried him rolling to K4 (27.6 on the quick reading), spacing on Q7 (24) and screening from L3 (28), and none beat the leader's 30. His corner three holds X2 on him (X2 is named on O5).
- **Times:** offence 111.7 s, defence 74.3 s.

**Board 3, High-Low v Run and Gun.**
- **Offence:** O1 Q3, O2 C9, O3 O9 (screener), O4 G2 (shooter), O5 I11 (ball). One in the key.
- **Plan (3 turns):** O3 screens X5 from N7; then O4 moves to J2 and O5 hesitates; then a post shot for O4 on G2.
- **Worth:** 24, 21, 16, 12, 9. The table squares read 18, 15.6, 15, 12, 9.
- **Defence:** X1 H10, X2 D6, X3 M3, X4 M6, X5 H4. X1 plays behind O5, the ball handler.
- **Between the bigs and the rim:** X1 on H10 for O5. Nobody for O4.
- **Best shooter:** O1 (three 9) in the corner on Q3. X3 on M3 is four squares off.
- **Post Scorer in the corner?** No: he is the passer up top.
- **Times:** offence 71.1 s, defence 48.9 s.

**The morning board.**
- **The defence settles on** K4, M6, H10, D7, E3 in 11.2 s.
- **The list:** 21, 18, 18, 15, 15.
- **The Sharpshooter** O2 on C9: the pass to him lands 60 in 100. His best look is a three from G10, held from 33 to 21 with X4 covering it.
- **The bigs** are on A3 and Q3, the corners; nobody is between them and the rim.
- **The route:** 2 turns, O3 screening X2 from M7.

**Does the defence still stand off the best shooters?** Yes, on all four boards: two to four squares off. By the list, these teams' best threes are rated 9, so their open threes are worth less than the looks inside. On board 3, the 24 at the top of the list is O4's post shot. The defence holds the looks that top the list.

**Shaun's case (a test).** O1 shoots a three from C9, with X1 on H11. No single movement gets X1 next to him; a Quick Step and a Move do, but that spends the reply, so the shot goes up with no contest. The map reads it open: nobody can contest it in time. Moved to E7, one Move from him, X2 can step in and press Contest.

**In play:** one All-Star turn took 13.0 seconds, the phase's read-ahead included (`turn.json`).

**Item 2.1: boards whose answer changed.** None of the four (`answer.json`). On each board's final position the map's own answer is the same with the list leading as with the gap leading. The two leads differ only where two answers tie on the gap and differ on the list, or the reverse. None of these positions has that.

**Item 2.4: two screens in a row.**
- Board 1 reads a stagger (O1's screen, a swing, O4's screen).
- At three turns its route read a screen the screener.
- The four-turn check (`four_turns.json`): on boards 1 and 3, the top two placements swap order at four turns.
- So I set four turns (D-268). The guard holds because the full reads stop by 95 seconds and the defence reads three ways ahead, not four.

## 5. Stances and conditions now read

**Stances, read from his square and arrows, against his man, the ball and the rim:**

| Stance | Reading |
|---|---|
| Front | Between his man and the ball on the line, arrow on him or the ball. |
| Three-quarter (paint) or deny (elsewhere) | The ball's side, one direction off the line, nearer the ball. |
| Behind | Nearer the rim and further from the ball. |
| Over or under a screen | The screener's high side, or between the screener and the rim. |

**Conditions now read (11):**
- post entry against the front (2), and over the top of it (2b);
- post entry against the three-quarter denial (3);
- backdoor (14), and dribble at to force it (19c);
- reject the screen (21);
- curl or fade reading the chase (24);
- from the route ahead: stagger (25), screen the screener (26), and a back screen on the roller's defender (27).

Each is worth its look at its real chance, ruled in by the bar. The defence reads the same with its own model. 47 conditions are read in all.

**Still not read (23), each with its reason in `conditions.py`:**
- the L-cut and drift: the movement that makes them isn't recorded;
- the handoff and hold or pin: read inside the pass and the screens;
- traps (retreat dribble), probe, skip over the shift;
- the cross screen between two bigs;
- transition;
- the scenario-card ones;
- several read inside another condition: separation, skip, entry angle, pocket pass, baseline drive, the double-team, force a switch, attack the helper.

## 6. Built differently from the prompt, and why

- **The square defender's Contest on an inside shot has no hard option.** His normal Contest is already the full rating with no foul, so the block would add only a foul risk.
- **The table's engine is unchanged.** It already made the Contest the reply's action. Its contest values have no normal and hard split, which stays the app's (Split).
- **Both outcomes of a pass are weighed item by item.** Each item of the list is its chance it lands times the caught board's item, plus the chance it's stopped times the stopped board's item less 5. That is how each look's worth is weighed. No threshold.
- **The route's plan is read on the board the route leads to.** Its needs list each turn: the screens hold, the passes land (with their chance), the cuts get there.
- **The job search reads every job variant the quick way.** Only the best one is read in full, beside the leader and the table squares, to keep inside the time guard.
- **Four turns ahead, not three (D-268).** The four-turn check changed the choice on two boards.
- **A takeover now settles in one read.** On step 21's board the named matchups covered more than the takeover's pick, so the next read switched again. Now the read calls that switch at once.

## 7. For Shaun to decide

1. **The printed wording** in section 1.
2. **Whether the table also gets the normal or hard choice on inside shots.** At the table there is one Contest today.
3. **Board 2 puts three in the key with O5 in the corner.** By the list it beats the table squares 30 to 24. He judges it in play.
4. **The stance definitions** in section 5: whether front, three-quarter and deny match what he means.

## 8. Tests

- **Pass:**
  - `test_rules_current` and golden;
  - engine equality (`test_step3n`): 47 pass with the same 3 expected failures, after two re-recordings below. The two engines agree on all 40 random boards.
  - the separate-thinking test and the rest of `test_step24`;
  - `test_step27`, `test_step26`, `test_step22c`, `test_coverage_18s`, `test_two_responsibilities_22b` (all 10, sense check 3 included), `test_web`, `test_points_play_on_18r`, `test_fiba_18i`, `test_map_logic_21`, `test_step22`, `test_drivers_22b`.
- **New, `tests/test_step28.py` (14):**
  - two movements leave no contest (Shaun's case), and the old rule's free hand-up is gone;
  - a teammate one movement away can still contest;
  - the contest costs an action, jump and inside, normal and hard;
  - after a movement and a second movement the reply is spent;
  - the map reads Shaun's shot as open;
  - each stance read on one board, and the conditions they unlock;
  - the map's answer leads by the list;
  - both outcomes of a pass in the read-ahead;
  - the Plan line is the route;
  - the wider search reaches the post.
- **Rewritten:** sense check 3 now tests the outcome (D-266), and passes.
- **Re-recorded, each with a note in the test:**
  - the morning board's pinned settlement (now K4, M6, H10, D7, E3);
  - the off-balance contest square;
  - two `test_step3n` foul tests and `test_fiba_18i` (the block is the hard Contest);
  - the scout-table helper and the square-defender test in `test_step24` (every shot has a Contest action now);
  - `test_points_play_on_18r` (the hard Contest fouls);
  - three `test_coverage_18s` checks (no token left means no contest; the answer may use all five; 32 where it read 30);
  - the step 22c takeover (the switch is called at once and stands);
  - the step 27 screen-then-dive test.
- **Not run:** the setup timing test (`test_setup_18o`). Speed is waived (D-200); the time guard was measured on the boards instead.

Nothing was simulated. Shaun's playtest is the test.

## 9. Model for the next step

Claude Opus 5.5, effort high. The playtest's findings on the contest rule will touch both engines.
