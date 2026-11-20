# Step 30: after the block, the two app-only cards, and the fake read in full

## 1. Changes to the printed game (for when the table resumes)

The block reset is an app rule (Split in the register), as the table's rules are on hold (D-146). I have not edited the
printed files. These are the pages it would change, with wording drafted for the table. The first row replaces the
block sentence drafted in step 29.

| Page | Step 29's draft | Drafted wording |
|---|---|---|
| Rulebook, page 2, "Shooting" (the block) | "A block is a turnover: −5, the phase ends, the ball stays with the shooter." | "A block is a turnover: −5, the phase ends (in the last phase the possession ends on what it has). **The shooter is forced back 3 squares** along the row, column or diagonal that points most directly away from the basket, stopping on the last open square before a player or the court's edge (if the first square is taken, he stays). **Then the blocker** may move to any open square within 3 squares of where he stands and set his arrow, or stay. Everyone else stays. The new phase starts with the shooter holding the ball as if he had just caught it: his dribble is alive and his closely guarded count starts again." |
| Defence tracker, page 1, "CONTEST AN ACTION: 1 TOKEN" | "... Block: Foul (Block) rolls first, then the Block roll (a turnover)." | "... Block: Foul (Block) rolls first, then the Block roll (a turnover). After a block, push the shooter 3 back from the basket, then move your blocker up to 3 squares." |
| Player cards, defence side: Slashing Wing | (none: the app-only card had no Block) | Block 9 / 8 / 7, Foul (Block) 11 / 12 / 12 (A, B, C). |
| Player cards, defence side: Switch Centre | (none) | Block 10 / 9 / 8, Foul (Block) 5 / 6 / 7 (A, B, C), the Defensive PF's values. |
| First-game guides, "Defend the shot" | "A Block can win the ball back, but it risks a foul, and against a fake it locks him." | "A Block wins the ball back and pushes the shooter 3 squares away from the basket, then your blocker gets a free reset of up to 3 squares. It risks a foul, and against a fake it locks him." |

## 2. In five lines

1. **After a block** the shooter is pushed 3 squares straight back from the basket (stopped short by a player or the edge), then the blocker resets anywhere within 3 squares, then a new phase starts with the shooter holding the ball fresh.
2. **The two app-only cards** have their own block ratings now: Switch Centre plays the Defensive PF's, Slashing Wing has Block 9 / 8 / 7 with Foul (Block) 11 / 12 / 12.
3. **The computer's setup reads the fake** turn by turn: the ball handler fakes, the defence replies by its own mix, the list is read again.
4. **The computer still contests rather than blocks** on step 29's block board: by its list, the new phase after a block is worth more to the offence than a contested layup. Contest leaves the offence about 8; a block leaves it about 17, because the new phase after it reads 29 even after the −5.
5. **Look for:**
   - the line after a block: "Blocked by X5. O1 is forced back to E7; X5 resets to H6.";
   - when you block, picking your blocker's square and arrow like a Move;
   - the computer's routes that start with a fake (the elite board's now does);
   - the wait: setups and turns take longer (section 6).

## 3. After a successful block: how it is built (D-276)

- **The line back.** From the shooter's square, the one direction of the eight (row, column or diagonal) that points most directly away from the basket: the largest step away, a diagonal step counted at its true length (1.41 squares). Then up to 3 squares along it.
- **Stopped short.** He stops on the last open square before a player or the court's edge; if the first square is taken, he stays.
- **Ties.** Shaun asked for a tie between a straight line and a diagonal to take the diagonal, with every such square flagged. On this board none exists: a tie needs the basket's offset to be in an irrational ratio, which whole squares never are. The closest any square comes is a gap of 0.05 between its best two directions. The rule is built (it would take the diagonal) and a test checks every square.
- **Examples:** H4 goes north-west to E7; I4 north to I7; J2 east to M2; M6 north-east to P9; C9 north-west, two steps to A11 (the sideline); A3 stays (the edge is the first square).
- **"Within 3 squares"** counts the way the game counts squares for movement and reach: across, down or diagonally, each 1 (the most of the two distances). So the blocker can reach a 7 by 7 box around him, any open square in it.
- **The order.** The shooter is pushed first; the defence sees where he ended up, then resets the blocker (any open square within 3, any arrow, or stays). Everyone else stays.
- **The new phase.** −5 and a new phase as for any turnover (D-198), every count reset. The shooter starts it as if he had just caught the ball: dribble alive, closely guarded count from nothing (the reading Shaun asked to have flagged). In the last phase the possession ends on what it has banked.
- **The computer's reset** is chosen by its search, reading ahead, like any other turn. At its own turn it reads every square and arrow within 3 (on the block board it put X5 on H6, between the shooter and the rim). Inside its look-ahead it reads two: staying, and where the map's own settlement for the new phase sends him (or the open square within 3 nearest that). Reading all 300 or so inside the look-ahead took minutes a block, because each is a new board the map reads afresh; this is the same narrowing every Move gets inside the search.
- **On screen.** "Blocked by X5: a turnover, −5. O1 is forced back to E7; X5 resets next (any square within 3)." Then, after the reset: "Blocked by X5. O1 is forced back to E7; X5 resets to H6." and "The new phase begins: O1 has the ball as if he had just caught it." The status line and the Coach's tip explain the reset; it is picked like a Move (square, then arrow).

## 4. The two app-only cards (D-277)

| Card | Tier A | Tier B | Tier C | Shaun |
|---|---|---|---|---|
| Switch Centre (Block / Foul (Block)) | 10 / 5 | 9 / 6 | 8 / 7 | "It's a defensive job." (the Defensive PF's values) |
| Slashing Wing | 9 / 11 | 8 / 12 | 7 / 12 | "built but probably indisciplined on defence": the Two-Way SF's block, the Bucket Getter's foul control |

Both are in `BLOCK_RATINGS.csv` (rows APP-SW and APP-SC, with a note) and on the cards; the stand-ins are gone.

## 5. The checks (one reading each)

**Step 29's block board** (Five Out against Iron Wall: O1 lays it up from H4; X5, the Rim Protector Centre, square in front on H3):

| | Off a Sprint (rushed: no fake) | In control (a fake is open) |
|---|---|---|
| X5's block | 45 in 100 (Block 9, no foul roll: square, arrow on him) | the same |
| His contest if he misses, and the honest Contest | 11, 11 | 11, 11 |
| After a block | O1 forced back to E7; the computer resets X5 to H6 | the same |
| The list for the offence's new phase (X5 staying) | 27.4, 18.9, 16, 15.6 | the same |
| The computer's reply | **Contest** (step 29: Contest) | **Contest**, all of its mix (step 29: Contest) |

**Why it contests, by the list (the search's own values, off a Sprint):**
- **Contest:** the layup goes up against his 11; the offence is left about **8**.
- **Block:** 45 in 100 he blocks it, and then the offence's new phase is worth **29** to it, even after the −5 (its best look 27.4, with a fresh set of actions, O1 holding the ball on E7 and four of the five defenders still where the drive left them). 55 in 100 he misses and the layup goes up against the same 11 (about 8). In all: 0.45 × 29 + 0.55 × 8, about **17**.
- So a block costs the defence about 9 points here against a contest. It would pay only if the new phase after a block were worth less to the offence than the contested layup (under about 8, after the −5).
- **In control** the answer is the same: the defence's mix puts all its weight on the Contest, so the offence gains nothing by faking (its fake chance is 0).
- **What would change it (Shaun's call):** the rule as built resets only the blocker. "The defence is fully reset" would mean a reset for all five (or a phase that starts with fewer of the offence's actions); either would bring the new phase's 29 down. I haven't changed the rule (D-190).

**Step 29's sag board** (the elite shooter O1 on I11, in control): the setup now stands **exactly where step 29's code stands** (I5, G9, N5, B8, M10; run on step 29's code for the comparison). X2 on G9 is 2 squares from him, sagging off O2 "to guard O1's look (worth 33 without him there)". Reading the full fake didn't move anyone here. Why, from the read-ahead on that board:
- **The shot fake reads 22** against 21 standing still: the defence's mix answers it with X2 closing out (a Move to H10), and when the fake is shown O1 has gained 1.
- **A pass fake to O4 reads 34:** X1 steps to F5 to cut it off, the fake is shown, and the board is better for the offence. That is the route the read-ahead takes.
- Standing closer to the shooter does nothing about the pass fake, so no other setup reads better than this one.

**Boards 1 to 3, the elite board and the morning board:**

| Board | The best shooter | His nearest defender now | Step 29 | Fakes and blocks in the setup's one reading |
|---|---|---|---|---|
| 1 (High-Low v Shoot and Protect) | O1, Combo Guard, three 9, on N6 | X1, 2 squares off | the same (same squares) | 1 fake (a pass fake to O5 that draws X1's Intercept), 0 blocks |
| 2 (Twin Towers v Lockdown) | O2, Two-Way SG, three 9, on C9 (step 29: on J4) | X2 on D7, 2 squares off | X1, 1 off, a different offence setup | 1 fake (a pass fake that draws X2's Intercept), 0 blocks |
| 3 (High-Low v Run and Gun) | O1, Combo Guard, three 9, on C9 (step 29: on N7) | X1, 3 squares off | X2, 1 off, a different offence setup | 1 fake (a pass fake to O4 that draws X1's Intercept), 0 blocks |
| Elite shooter (Lockdown) | O1, Sharpshooter SG, three 11, on O9 | X3 on M8, 2 squares off | X2, 1 off (X5 the matchup, 14 off) | 1 fake (a pass fake to O1 that draws X3 across to N9), 0 blocks |
| Morning (the Sharpshooter check) | O2 on C9 | X4 on D7, 2 squares off | the same (same squares) | (the defence's setup only) |

What changed: **every offence setup's best route now uses a pass fake.** On boards 1 to 3 it draws an Intercept from the defence's own mix, which locks that defender for the phase; on the elite board it draws X3 across. On boards 2 and 3 that changed where the offence sets up, so the best shooter stands somewhere else and the defence's distances aren't like for like. No route uses a block: the setup's reading never reached a shot into one.

## 6. Times

Speed is set aside (Shaun). No time guard was added. Each time is one reading on this machine, with other work
running beside it, so read them as a rough size.

| Check | Step 30 | Step 29 |
|---|---|---|
| Board 1 setups (offence, defence) | 151 s, 202 s | 96 s, 90 s |
| Board 2 | 155 s, 144 s | 103 s, 91 s |
| Board 3 | 140 s, 132 s | 107 s, 83 s |
| Elite board | 149 s, 87 s | 86 s, 77 s |
| Sag board, the defence's setup | 164 s | 142 s (step 29's code, run today) |
| Morning board, the defence's setup | 14 s | 13 s |
| The block board, the computer's reply | 37 s, 39 s | 5 s, 4 s |
| The computer's reset after a block | 4.5 s | (no reset) |
| One computer offence turn (Shaun's high screen board) | 86 s | 21 s |

**What takes the time:**
- **Reading the fakes in the setup.** One defence setup on the sag board read 7 fake turns, 15 reply mixes, 60 of its 175 seconds. Each reply mix is the All-Star's own search at the declaration (2.5 seconds a reply on its clock, more with the work around it).
- **Reading past a block.** Every block the search meets now opens a new phase it reads (the push, the reset, the new board), where step 29 stopped at a board it already had. The offence turn's first look took 26 s against step 29's 4 s for the same 1,627 positions; the rest of the 86 s is reading the plan.
- **Python is far slower** at both (about 10 seconds a fresh board): it is what made several tests slow (section 9). The app runs the JavaScript engine.

## 7. The audit (step 27's, run again for the step 29 rules and the reset)

Full table in `STEP30_CODE_AUDIT.md`. Every rule is read one way, the same in both engines. What still reads in part:

- **The map stops a block at −5.** The search in play reads what follows a block in full (the push, the reset, the new phase), and the setup's read-ahead reads it through the search's reading at the end of its look. The map (`_block_value` and its port) and the scout's shot review still price a block as −5 and stop.
- **Why the map can't simply read on (this is where I stopped, as the prompt allows).** The map prices each look once for a defender and a square and keeps that price for every board where the same defender could reach the same square. That is what lets it read every square of every board fast enough. What follows a block depends on the whole board: where the others stand decides where the shooter is pushed to, where the blocker can reset and what the new phase is worth. So a price that reads past the block can't be kept that way, and changing that touches every reading built on the map in both engines.
- **The options:**
  1. **A second pass (my pick).** After the map is built, take the few looks at the top of the list where a block is possible, read the board after the block for each (the push, the reset by the map's settlement, the new phase) and correct their price. It reads past the block where it decides the list and keeps the map's speed elsewhere. Both engines, with its own two-engine test.
  2. **Drop the kept price for any look a block can reach.** Exact everywhere, but each is a fresh map reading (half a second in JavaScript): hundreds a board, minutes a reading.
  3. **Keep −5.** The search already reads past the block wherever the computer actually chooses, so the map's price only shapes the order it looks at things and the setup's first reading.
- **The fake in the map** is still read through the rushed closeout only (as step 29 reported); item 3 asked for the read-ahead, which now reads it in full.

## 8. Built differently, and why

- **The reset inside the look-ahead reads two squares, not every square** (section 3). At the computer's own turn it reads every square.
- **A shot settled by the rules reads the reset the same way.** The search settles a declared shot by the rules; it reached the reset and tried every square there, each with a full reading, and never finished. It now reads the reset as at the end of its look, in both engines.
- **A one-action reply to a fake ends the defence's turn there.** The defence's mix can reply with one action (a closeout); the read-ahead first read that board with the defence still to act and dropped it, so it read only pass fakes. It now ends the reply as the rules end it, shows the fake and reads on; the checks were rerun after the fix.
- **The fake's reply in the read-ahead uses the All-Star's search** (`plan.FAKE_LEVEL`), the level the setup reads at, with its own clock (2.5 seconds a reply). Under the tests' fixed look it has no clock, so the tests read it with a shorter look.
- **Two tests use a smaller board.** Each board after a block is a new phase the map reads afresh (about 10 seconds a reading in Python), so the two-engine block tests in `test_step30` use the rim board with the shooter off a Sprint and only X5 near him. The rules are the same; there are fewer replies to read.

## 9. Tests

- **Pass:**
  - `test_rules_current` (18);
  - engine equality, 40 of 40 (`tools/step_22c.py equal 40 23`);
  - all of `tests/test_step30.py` (23): the push along a column, a row and a diagonal, stopped by a player and by the edge, no square with a tie; the blocker's resets (every open square within 3, any arrow, staying), after the shooter; the new phase as if he had just caught it; a block in the last phase ending the possession; Shaun's line word for word; the reset and a block at the end of the look read the same in both engines; the read-ahead reading the fake, from the public board; the two new cards and the sheet;
  - all of `tests/test_step29.py` (30), one re-recorded (below). Its four two-engine tests took 41 minutes in Python, the block board 26 of them;
  - the golden game test, `test_golden_and_regression` (8 of 8, 81 seconds, no value moved);
  - `test_step24` (14), the separate-thinking test among them: it ran 14 minutes, because its two defence setups read every fake at a fixed look with no clock.
- **Re-recorded, with a note in the test:**
  - `test_step29.test_a_successful_block_is_a_turnover`: the ball no longer stays where he shot; the new phase opens on the blocker's reset, the shooter forced back (D-276).
- **Not built, so not tested:** "the map reads past a block the same as the search" (section 7: the map still stops at −5).
- **Over the time limit.** The prompt's 10 minutes went on the tests it lists: each board after a block is a new phase the map reads afresh, about 10 seconds a reading in Python, so step 29's two-engine tests and the separate-thinking test ran long. Not run, for Shaun to check by playing: `test_web`, `test_step22c`, `test_step3n`, `test_step27`, `test_step28` and `test_map_logic_21`.

## 10. Choices his words didn't settle

- **The shooter starts the new phase as if he had just caught the ball** (dribble alive, closely guarded count from nothing), as the prompt read it. Flagged for Shaun.
- **"Most directly away"** is the direction whose step points most along the line from the basket to the shooter, a diagonal step counted at its true length. Counting a diagonal step as 1 (as the game counts reach) would push more players diagonally: say if you want that.
- **No square ties**, so the diagonal rule never acts. If the basket is ever moved to a half square, ties appear and the rule is built.
- **The shooter on the rim's own square** (no shot is allowed from it, D-198) has no "away": he would stay.
- **The blocker resets onto any open square**, including the shooter's own line or the key; nothing in the rule bars him from standing where the shooter was pushed from.
- **The reset happens before the new phase's clock starts**, so it uses none of the defence's actions.
