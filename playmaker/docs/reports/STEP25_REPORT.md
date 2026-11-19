# Step 25: Shaun's rulings on step 24, the conditions, the falling bar, loading screens

1. **Bunching no longer reads as hard to defend.** A defender now covers every look he can still reach in time. Only looks the offence creates one after another, out of his reach, count against him. The offence's setups spread out more.
2. **The shot bar now falls with the clock.** It barely drops early, then faster, to nothing in the last phase. That shape appears where the board offers a better look at a chance; where it doesn't, the bar stays flat until the last phase.
3. **The plan is built from the conditions list.** Each one is read from the board and ruled in or out by the bar. The plan names the ones it uses ("Built from: ..."), and the defence names the ones it watches.
4. **No more two-possession rule.** Each possession's setup predicts fresh. Play story hides the computer's setup thinking from the human playing it until the possession ends; Watch shows both sides.
5. **Look for:** a loading panel with a moving bar and the scouting notes whenever a setup takes more than a second, a "thinking" cue by the side that's thinking, and offences that spread to the arc instead of piling into the key.

## 1. Changes to the printed game

None. No rule or card changed.

## 2. What changed

- **Both engines** (`engine.js`, `decide.py`): a defender covers every look he can reach in time (D-241), and the bar is the value of playing on (D-242).
- `playmaker_engine/conditions.py` (new): 29 conditions from the list read off the map; the other 40 are listed with the reason each isn't read yet.
- `plan.py`: the beat measured as the whole map before and after (D-243); the plan built from the conditions; off-ball screens and the dive after a screen; no carried predictions.
- `app.js`, `style.css`: the loading panel and the thinking cue.
- `report.py`, `report.js`, `api.py`: Play story keeps each side's plan private.
- `DECISIONS.md`: D-240 to D-247.
- `docs/reference/OFFENCE_CONDITIONS_19NOV.md` added.

## 3. What it proves

Each check is one reading of one board (`docs/runs/step25/checks.json`, `tools/step_25.py`).

**Shaun's two boards: does the offence still bunch?** Less. The candidate squares still read lower than the table's spread squares.

| Board | Placed (ball) | Average squares apart | By the key | Plan worth | Table squares worth |
|---|---|---|---|---|---|
| Shoot and Protect v Lockdown, step 24 | G6 F7 I11 A3 G4 | | | 13.9 | 15 |
| Shoot and Protect v Lockdown, now | E9 C9 O9 **I11** I4 | 6.4 | 1 | 11.9 | 15 |
| High-Low v Run and Gun, step 24 | I7 I11 A5 G3 G2 | | | 14 | 18 |
| High-Low v Run and Gun, now | A2 G4 O9 **I11** H4 | 7.2 | 2 | 7.6 | 18 |

The table squares are 9.6 apart with nobody by the key. Neither board puts a centre on a point guard at the arc or a poor-shooting centre in a corner.

**The bar, phase by phase (phase 1 to phase 6):**
- Shoot and Protect v Lockdown: 19.2, 18.3, 17.0, 15.0, 11.9, 0. Drops of 0.9, 1.3, 2.0, 3.1, then all of it.
- High-Low v Run and Gun: 15.1, 14.2, 12.9, 10.8, 7.6, 0. Drops of 0.9, 1.3, 2.1, 3.2, then all of it.
- Your morning board as it stood: 24 every phase, then 0. The board offers nothing better than 24 at any chance below certain, so playing on can't improve on the sure look.

**The dribble beat** (guard against centre, 60 in 100 anywhere), everything the offence threatens before and after:

| Where | Squares better | Total gain | Largest single gain |
|---|---|---|---|
| Top of the key | 12 | 109 | 30 |
| Wing | 13 | 130 | 30 |
| Elbow | 6 | 41 | 15 |
| Green zone | 2 | 19 | 15 (his own layup) |

**Conditions the computer used:**
- **Shoot and Protect v Lockdown:** a three for O2 off O1's screen on X1. Built from cut behind help (O2 dives to G4 while the defence turns to the screen), an on-ball screen and an off-ball screen.
- **High-Low v Run and Gun:** a post shot for O5 off O1's screen on X4. Built from cut behind help (O5 dives to I3 as X4 turns to the screen) and an off-ball screen.
- **The high screen board:** a post shot for O5 after he screens and rolls. Built from off-ball and on-ball screens.

**Does the corner player's dive now appear?** Yes, as a basket cut: O3 from the corner to K3, worth 32, ruled in. It is not the plan's first choice. The screen doesn't make his cut better, because it is already open before the screen. After the defence's best answer the roller reads worth more, so the plan picks him.

**Tests:**
- `test_rules_current` 18, golden 8, engine equality 21: all pass. The two engines agree on 39 of 40 random positions, as before (the other prints 18.625 two ways).
- `tests/test_step24.py`, 14 tests, all pass. New for this step: the cover rule (bunched covered, spread not), the falling bar in both engines, the beat measured whole, the conditions ruled by the bar. Also the separate-thinking test.
- Other changed files' tests pass, except the setup timing test (`test_setup_18o`), which runs over its time limit as in step 24. Speed is waived (D-200).
- Re-recorded, each with a note in the test: the step 21 overload test (Shaun's 3-on-2 near the key is now covered; the same numbers spread across the court still overload), and step 22b's pinned settlement (X3 now faces N).

## 4. For Shaun to decide

1. **The candidate-square rule now costs more.** The plan reads 11.9 against the table's 15, and 7.6 against 18. With bunching fixed, the gap widened rather than closed. Options: drop the rule and let the one measure place everyone, or keep it.
2. **The dive appears but isn't chosen.** The corner player's basket cut is open before any screen, so the screen adds nothing for him and the roller wins on value. If you want the screen-then-dive sequence, the map would need to read two phases, not one.
3. **A flat bar on some boards.** Where nothing on the board is worth more at a chance than the sure look, playing on can't beat it, so the bar stays flat.
4. **Conditions not yet read** (40 of them, each with its reason in `conditions.py`): mostly those needing two phases (V-cut, swing, re-screen, stagger) or a stance the board doesn't record (fronting, denial, cheating over).
5. **"Every defender has a real job" failed once.** X5 was left with nothing to do on the Shoot and Protect board.

## 5. Noticed, not touched

- The defence's read still names most matchups "the nearest defender who takes something off his look". It is true, but says little.
- The offence's setup button takes 25 to 45 seconds on these boards. The loading panel now covers the wait.

## 6. Model for the next step

Claude Opus 5.5, effort high. The open choices are about what the one-phase map can see, which needs care in both engines.
