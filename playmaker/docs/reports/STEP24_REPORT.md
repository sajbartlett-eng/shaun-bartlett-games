# Step 24: the setup plan (scout, tolerance, the offence's plan, then the defence)

1. **Before tip-off the computer now works in your order.** It scouts both teams, sets a shot bar for each phase, plans a first-choice shot with backups, places the offence for that plan, then sets the defence. Each side does this alone, from the board, the rules and the cards.
2. **Two buttons at setup, in every mode:** "Computer sets up the offence" and "Computer sets up the defence". Each puts that side's pieces on the board as a draft. Move any piece, press again for its next-best setup, or confirm.
3. **The plan sits beside the board,** never over it: the target, what it needs, the branch if that fails, the backups, and one line on attention, holes and access. The defence shows its matchups and the ones it avoided. In play one line says what is being chased.
4. **No defence on the board while the offence places.** No defenders, reach, zones or arrows until the defence has set up. With Coverage on, tap an attacker to see his candidate squares.
5. **Look for:** the offence now bunches inside more than a coach would, and the buttons take 20 to 45 seconds for the offence and 10 to 18 for the defence. Both are in "For Shaun to decide".

## 1. Changes to the printed game

None. No rule or card changed.

## 2. What changed

- `playmaker_engine/plan.py` (new): the scout, the shot bars, the plan, the offence's placement, the defence's matchup rule, the plan in play.
- `playmaker_engine/agent.py`: setup goes through the plan wherever the fast engine runs. Each computer keeps its own plan and scout.
- `playmaker_web/game.py`, `view.py`, `api.py`: the two buttons, each side's own setup thinking kept apart, the matchup scout.
- `playmaker_web/static/app.js`, `index.html`, `style.css`, `tips.js`: the buttons, the plan panel, role squares, the matchup scout, no defence drawn before it sets up.
- `playmaker_web/static/engine.js`: the offence's square sweep can take a list of squares and a quick read. Nothing else in the engines changed.
- `DECISIONS.md`: D-233 to D-239, with your words.

**What was wrong with the old offence setup:**
- It tried the table's squares plus 24 placements drawn at random from anywhere on the court. Nothing came from the cards.
- "Accept the proposed setup" gave it 2.5 seconds. That was enough to screen a handful, so it nearly always handed back the table's squares.
- It was judged against a quick defence, and it had no plan: nothing said what a placement was for.
- A human's starting draft was always the table's squares, with the previous defenders and their reach drawn over it.

It is replaced in all three places it was called: the buttons, the computer's own setup, and Watch.

## 3. What it proves

All checks are single readings of one board (`docs/runs/step24/checks.json`, from `tools/step_24.py`).

**The dribble beat** (guard O1, Dribble 17, against centre X5, Agility 5; 60 in 100 anywhere):

| Where | Squares that get better | His options grow by |
|---|---|---|
| Top of the key (I11) | 12 | 109 |
| Wing (C9) | 13 | 130 |
| Elbow (I7) | 6 | 41 |
| Green zone (I4) | 2 | 19 |

Large at the top, small in the paint, as you expected.

**Shoot and Protect v Lockdown (19 Nov):**
- **Placed:** O3 (Stretch SF) I11 with the ball, O1 (Pass-First PG) G6, O2 F7, O4 A3, O5 (Rim Protector C) G4.
- **Plan:** a three for O3 on C9, off O1's screen on X1. If the screen fails: O3's floater on H6. Backups: O2's three on I10, O1's floater on G7.
- **Spec, in your form:** "Create a three for O3: open accepted; rushed open accepted; contested by X1 accepted; contested by X2 accepted; contested by X3 square in front (only if he is rushed) or from the side or from behind accepted, otherwise not; contested by X4 square in front (only if he is rushed) or from the side or from behind accepted, otherwise not; contested by X5 accepted."
- **Defence:** X1 on O3, X2 on O2 (same position), X3 on O4, X4 on O5 (same speed), X5 on O1. Avoided: X5 on O3 at the arc.
- **Centre on a point guard at the arc?** No. X5 has O1, but O1 stands in mid-range.
- **Poor-shooting centre in a corner?** No. O5 is on G4 in the green zone.

**High-Low v Run and Gun (18 Nov):**
- **Placed:** O2 (Playmaker SG) I11 with the ball, O1 (Combo Guard) I7, O3 A5, O4 G3, O5 (Post Scorer C) G2.
- **Plan:** a floater for O1 on F7. Needs X4 a step late and the pass from O2 (50 in 100). If X4 stays home: O1's three on G10. Backups: O2's three on O9, O5's post shot on K4.
- **Defence:** X1 on O1, X2 on O2, X5 on O5 (all same position), X3 on O4, X4 on O3. Avoided: X5 on O2 at the arc. The matchup rule moved it from no like-for-like pairs to three.
- **Centre on a point guard at the arc?** No. **Poor-shooting centre in a corner?** No.

**A high screen with the corner player free to dive** (High-Low; O1 I11 with X1 on him, O5 K12, O3 in the corner):
- **Plan:** a post shot for O5 on H3, after he screens X1 and rolls. Screener's squares: H10, H9, I9, J10 or J9.
- **Branch:** if the screen fails, O4's post shot on H3.
- **Phase 1:** O1 Quick Steps to I12 and O5 moves to J10, one of the screener's squares. Its line: "Chasing: O5's post shot on H3, off O5's screen on X1 (still to be set)."
- The map freed the roller here, not the corner player. Later phases turn on the dice, so I did not play them.

**A big guarded by a smaller defender:** yes, a seal and feed appears. "Plan: a post shot for O5 on H2. Needs: the pass from O1 to O5 arrives."

**An open lane mid-plan:** the planned three was worth 12 at its real chance. The offence took the lane: O1 moved to I3.

**Tests** (about 20 minutes in all):
- `test_rules_current.py`: 18 pass. Golden: 8 pass. Engine equality (`test_step3n.py`): 21 pass.
- `tests/test_step24.py` (new, 10 tests): every case in the scout's table against the contest rules for three pairs of teams (25 matchups, 7 shots, 14 or 22 cases each); the separate-thinking test; the buttons; the plan's words.
- Other changed files: `test_web` 15, `test_setup_18o` 7, `test_step22c` 11, `test_map_logic_21` 10, `test_coverage_18s` 14, and five more files, all pass.
- Not run: `test_step3m.py` went past five minutes because it plays whole games.

## 4. For Shaun to decide

1. **Candidate squares cost the offence by its own measure.** I ruled a square in when the attacker's open shot there beats what the offence can always get against one set defender. That takes the centre out of the corner, as you wanted. But the table's spread squares read higher: 15 against 13.9, and 18 against 14. Options: keep the rule; drop it and let the one measure place everyone; or keep it only as a check.
2. **The offence bunches inside.** Three or four attackers end up within a few squares of the key. The map reads that as worth more than spacing. If that is wrong basketball, the fault is in what the map values, not in the placement search.
3. **The shot bar barely falls.** It is the same every phase until the last, where it is zero. So nearly every contested shot is "accepted". If you expected a bar that drops phase by phase, the clock needs counting differently.
4. **How the dribble beat is measured.** I used how much his squares improve. His best shot this phase goes the other way: in the paint a win turns a contested layup into an open one (18 to 34).
5. **The plan holds one phase of conditions,** measured again every phase. It is not a written three-phase path, and it only sees a screen on the ball handler's defender.
6. **The matchup rule** is my reading of this step's words, since step 23 was not merged: within the level's margin, the dribble mismatch priced where it hurts, then like against like, then matching numbers.
7. **Evidence to change a prediction:** the same unexpected matchup two possessions running. A setup has no dice, and one sighting can be the level's variety.
8. **Speed.** The offence button takes 20 to 45 seconds and the defence 10 to 18, longer on a phone. The computer's own setup keeps to its level's time.

## 5. Noticed, not touched

- "Play story" can show the computer's setup words during a game. That may leak its plan to the human playing it.
- With variety on, the All-Star offence can pick a placement up to 2 points below its best.
- The defence's read says "the nearest defender who takes something off his look" for most matchups. It is true but says little.

## 6. Model for the next step

Claude Fable 5.2, effort high. The open choices above go to the heart of what the map values, and that needs careful reading of both engines.
