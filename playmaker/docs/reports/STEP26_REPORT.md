# Step 26: the defence feels the danger of the pass, then is the offence still bunching?

1. **The defence can no longer contest through bodies.** A defender standing above a bunch no longer counts a contest on the block he could only reach through the attackers' bodies. His paths go around them, as the rules have them.
2. **Passes are priced from wherever the ball handler can get to this turn,** not just where he stands. A lane he can open with a Move, Quick Step or Sprint counts.
3. **The three seconds count against every look in the key:** half the -5 for a player who will have the ball in the key at the next phase start, all of it if he was in the key at the last phase end. A defender who can't reach his man's look now reads "sags off".
4. **Board 2 (Twin Towers v Lockdown) now defends the post:** X3 stands beside O5 on the block and the entry pass reads as denied. The offence there puts two in the key, not four.
5. **Look for:** on High-Low the offence still puts four in the key. The cause is in how the offence places, and I left that alone as the step asks. The options are below.

## 1. Changes to the printed game

None. No rule or card changed. Your ruling "no screen, no blocked diagonal" is how the code already worked (D-248).

## 2. What changed

- **Both engines** (`engine.js`, `decide.py`):
  - the map's contest reach follows the real paths (D-249);
  - a receiver's pass chance is the best from any square the ball handler reaches this turn (D-250);
  - the three seconds are counted on each look in the key (D-251).
- `plan.py`: the defence's matchup read says "sags off" when he can't contest his man's look this turn (D-252).
- `tools/step_26.py`, `tests/test_step26.py`: the board readings and one test per item.
- `DECISIONS.md`: D-248 to D-253.
- `docs/reference/step26_boards/`: your screenshots.

## 3. The board readings

Each is one reading, with both computer setup buttons (`docs/runs/step26/checks.json`).

**Board 1, High-Low v Shoot and Protect:**
- **Offence:** O1 J3, O2 H3, O3 G4, O4 I4 (four in the key), O5 N12 with the ball.
  - Plan: a three for O1 on Q2 after he screens X1 and rolls.
  - Worth 6.1 against the defence's full setup. The table squares read 18.
- **Defence:** X1 J6, X2 K5, X3 M6, X4 O12, X5 M11.
  - Nobody stands between the bunch and the rim. The defence stands in the passing lanes instead: the pass to O4 lands 35 times in 100.
  - Read: "X3 sags off O3 to guard O1's look"; "X4 sags off O2 to guard O5's look".
- **The bar:** 17.1, 16.3, 14.9, 12.5, 8.1, 0.

**Board 2, Twin Towers v Lockdown:**
- **Offence:** O1 J3 and O5 H3 in the key, O2 C9, O3 O9, O4 A8 with the ball.
  - Plan: a post shot for O5 off O1's screen on X1. Worth 19.1; table squares 18.
- **Defence:** X1 G4, X2 D7, X3 H4, X4 K8, X5 E3.
  - **Post defence: X3 plays beside O5 on the block, and the pass to O5 reads as denied (0 in 100).** That is the side position, with the lane cut: the cheapest way to stop the entry where both outcomes are counted. It didn't front (nobody to back it up against the lob from there), and it didn't play behind (the pass could be denied).
  - Read: "X5 sags off O1, standing in his way rather than on him."
- **The bar:** flat at 19.1 until the last phase. Nothing on this board is worth more at a chance below certain.

**Does the offence still bunch?** On board 2, no: two in the key, three spread to the arc. On board 1, yes: four in the key. Two parts of the offence's placement decide it:
1. **The candidate squares.** For High-Low, four of the five have candidate squares only in the green zone. Their open shot beats what the offence can always get (24) only on layups, so the rule moves them there.
2. **It ranks placements against a quick defence.** Each placement is read against the defence's quick setup, and only the chosen one against the full setup.
   - The four-in-the-key placement reads 24 against the quick defence, but 6.1 against the full setup the defence really uses.
   - The quick setup doesn't use the full reads that put a body beside the block.

The "best plan only" measure you suspected is not what decides it here.

## 4. Your questions

- **"Plan worth" and "table squares worth":** both are the same reading, the lasting gap: the offence's first turn of the next phase and the defence's best answer, one phase ahead. But "plan worth" is read against the defence's full setup for that placement, and "table squares worth" against its quick setup. They are not like for like.
- **"Every defender has a real job":** passes on both boards after the fix.

## 5. For Shaun to decide (the offence, not changed in this step)

1. **Rank placements against the full defence.** Ranking only the best few by the quick read, then reading those against the full setup, would stop the bunch reading 24 when it is really 6. The cost is about a minute per offence setup (the loading screen covers it).
2. **Drop the candidate-square rule (D-240).** Every square then stays open to every attacker and the one measure places them. On board 1 the table squares already read 18 against the bunch's 6.
3. **Score the whole list, not just the best plan.** Every attacker's look would count, so spacing the other four would matter even when it doesn't change the one plan. Its effect is smaller here than 1 and 2.
4. **The three seconds on a big's post shot** (D-251): it is counted at half the -5 even though the shot goes up before the second phase end. Keep, or count it only for those who don't shoot?

## 6. Tests

- **Pass:** `test_rules_current` (18), golden (8), engine equality (`test_step3n`, 21, with 3 expected failures). The two engines agree on all 40 random positions.
- **Pass:** the separate-thinking test and the rest of `test_step24`; `test_step26` (6 new: the ruling, the real paths, passes from a new angle, both outcomes of a pass, the three seconds, both engines on these boards).
- **Pass:** `test_coverage_18s`, `test_map_logic_21`, `test_step22`, `test_step22c`, `test_drivers_22b`, `test_web`.
- **Re-recorded, each with a note in the test:**
  - three coverage tests (each square now shows the cost of holding the ball there, and the open layup carries half the three-second -5);
  - the bar test's board (the morning board's settled shape is now flat, so the test reads board 1);
  - the drivers test (it now accepts "his own man");
  - the step 22b pinned settlement (now D5, O5, L6, G7, I4);
  - the step 24 read-line test (accepts "sags off").
- **Fails, a finding I left as it is:** `test_two_responsibilities_22b`, sense check 3. On your morning board's new settlement the pass to the Sharpshooter is no longer cut: it lands every time. The defence lets him catch and holds his look to 21 with X1 on him and X4 and X5 helping; it spends its bodies inside instead. Your check says the pass should be cut. Tell me whether the check or the defence is wrong here.
- **Fails, as before:** the setup timing test (`test_setup_18o`). Speed is waived (D-200).

## 7. Noticed, not touched

- Setup takes longer now: about 19 seconds for the defence and 25 to 45 for the offence on these boards.
- On board 1, X4 and X5 stand far out (O12, M11) near O5 with the ball. That is pressure on the ball, but it leaves two defenders for the four in the key.

## 8. Model for the next step

Claude Opus 5.5, effort high: the offence's placement choices above touch both engines' readings.
