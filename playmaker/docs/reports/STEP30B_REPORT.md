# Step 30b: speed foundations

## 1. Changes to the printed game

None.

## 2. In five lines

1. **No decision changed.** Every setup, arrow, coach's line, move, value and mix odds is the same before and after, on all three boards and on the three exam boards checked. All 8,421 recorded requests give the identical answer.
2. **It is a little faster, not a lot.** The same work takes about 6% less time overall; the lasting readings (the part most repeated) take 16% less, and repeated requests inside a think are gone.
3. **Why so little:** almost all the time is honest thinking or parts step 31 replaces. Only about 5 to 10% of it was work done twice.
4. **What Shaun will notice:** setups about 5 to 15 seconds shorter (2 minutes or so instead of 2 and a quarter). Turns the same or slightly shorter. The page already never freezes (the computer thinks off the main thread since step 3m).
5. **The straight answer:** step 31 as planned would be 4 to 9 minutes a setup and 1 to 3 minutes a turn on this work. That is not playable. Section 8 lists what could close the gap without thinking about less, with sizes.

## 3. Where the time went before

Measured on the JavaScript engine (the one Shaun plays), All-Star, one offence setup, one defence setup and one computer turn, on three boards: Twin Towers against Lockdown (board 2), High-Low against Run and Gun (step 30's board 3), and Five Out against Iron Wall (step 29's block board). Files: `docs/runs/step30b/before.json` (with the clocks, as the app plays) and `before_fixed.json` (fixed look-ahead).

| Board | Offence setup | Defence setup | One turn |
|---|---|---|---|
| Twin Towers v Lockdown | 151 s | 150 s | 31 s |
| High-Low v Run and Gun | 154 s | 143 s | 26 s |
| Block board | 141 s | 144 s | 47 s |

**The three-way split** (per setup, from the timed calls and a CPU profile of the block board):

| Share | What it is | Seconds a setup | This step |
|---|---|---|---|
| **Work done twice** | The same request sent again inside one think (78 to 199 a setup, 4 to 8 seconds); the same map built twice inside one reading (once for the lasting gap, once for the top of the list, again at the end of every search line) | about 10 to 15 s (7 to 10%) | Fixed |
| **Parts step 31 replaces** | The defence's settlement for setup (`settleSetup`, 50 to 55 s in the offence setup, 16 to 18 s in the defence setup), the offence's placement sweep (4 s), the lasting gap as the leading measure (42 to 67 s), the quick reading that orders the search (about 14% of the CPU) | about 90 to 110 s (60 to 70%) | Left alone |
| **Honest thinking** | The searches: each side's real look-ahead, including the read-ahead of the fake's mixes (32 to 73 s a setup, nearly all of the block board's turn) | about 35 to 75 s (25 to 50%) | Left alone, never to be cut |

The lasting gap's share is counted as "replaced" because step 31 replaces the lasting gap as the leading measure. The memory built here sped it up anyway (it is generic, section 4), and will serve step 31's readings the same way.

Board handling (copying a board, applying an action, working out the legal actions) is small: no such function is among the top costs, and the largest is under 4% of the CPU. Garbage collection is 19%; the top costs around it are the map's own work (building the map 9.5%, reading values 8.9%, gaps 6.7%, overloads 6.1%).

## 4. What was built, what was skipped, and why

**Built**

- **A memory that lasts one think, in both engines.** It opens when a side starts deciding (a computer turn, an offence setup, a defence setup, a plan reading) and is thrown away when that side has decided. It stores readings, never choices.
  - *JavaScript* (`engine.js`): every coverage, search, goals and reads request opens one. Inside it, a map built for a board is kept, keyed by the whole state written out (every field, built from the state itself, not a hand-picked list) plus the side reading it and the reading's settings. Only the plain map is kept; the maps that read the defence's answers are always built fresh.
  - *Python* (`memo.py`, `decide.map_read`, `agent.coverage`): the same map memory, keyed by the whole state (Python's own equality covers every field) and the game; and a repeated request to the JavaScript engine inside one think is answered once. Each caller gets its own copy.
  - *Proof* (`tests/test_step30b.py`, 6 tests, 23 seconds): a remembered reading equals a fresh one on 12 boards; changing any one field of a state changes its key; nothing survives the think; a repeat is answered once and each caller gets its own copy.
- **The one rule for all speed work** in `playmaker/CLAUDE.md`, and D-283 in `DECISIONS.md`.
- **The measuring tool** `tools/step_30b.py` (profile, record, replay, exam).

**Skipped, and why**

- **Facts once per game.** They already exist: the engine keeps each game's card values (shot, contest, block, foul by square) and the board's distances, lines and zones from the first request of the game, built from the cards as they are then. They show under 1% in the profile. Nothing is shipped as stored data.
- **Cheaper board handling.** No board-handling function is a top cost, so not worth the risk now. The pattern for step 31: build its new readings to update only the players an action touched, and reuse working lists rather than making new ones for every board (the map's lists are the likely source of the 19% garbage collection).
- **Several cores.** The app's thinking runs Python (Pyodide) in one worker, which calls the engine directly and waits for each answer. Spreading readings over several workers needs either shared memory (which needs server headers a single-file site can't set) or rewriting that Python to wait for answers in a different way. Neither fits this step without touching the parts step 31 replaces. Listed in section 8.
- **A head start.** With one worker, starting the computer's next setup early would block the human's own coach readings while it runs. The setup's thinking is run by the Python side, so a second worker means a second copy of Python in the page (tens of MB more and several seconds to start). Listed in section 8.
- **Off the main thread.** Already done (step 3m): the computer thinks in a Web Worker, the page never freezes, and `dist/playmaker.html` stays one file.

## 5. Times before and after

Fixed look-ahead (one turn ahead), so both sides do the same thinking. Files: `before_fixed.json`, `after_fixed.json`.

| Board | Offence setup | Defence setup | One turn |
|---|---|---|---|
| Twin Towers v Lockdown | 132 → 143 s* | 117 → 113 s | 28 → 23 s |
| High-Low v Run and Gun | 139 → 122 s | 132 → 123 s | 27 → 39 s** |
| Block board | 134 → 127 s | 131 → 114 s | 49 → 49 s |

\* This run shared the machine with another job for its first two minutes. \*\* The plan's read-ahead runs on a 12-second clock; the faster engine got further inside it (6 searches instead of 1), so this turn did more thinking, not the same thinking. The decision was the same.

**The clean comparison: the same work replayed.** All 8,421 requests from the "before" run sent again to the old engine and the new one, one at a time:

| | Before | After |
|---|---|---|
| All requests | 896 s | 846 s (−6%) |
| Lasting readings (7,726) | 371 s | 312 s (−16%) |
| Searches (94) | 281 s | 292 s (same within noise) |
| Setup settlement (104) | 216 s | 213 s |

On top of that, repeats inside a think no longer reach the engine at all: 78 to 199 fewer requests a setup (4 to 8 seconds).

## 6. The same-decisions check

| Board | Offence setup (squares, ball, plan line) | Defence setup (squares, arrows, reads) | Turn (move, value, how far ahead, mix odds, replies) |
|---|---|---|---|
| Twin Towers v Lockdown | Same | Same | Same (O2 Quick Step to D10) |
| High-Low v Run and Gun | Same | Same | Same (O1 Move to C12) |
| Block board | Same | Same | Same (X5 contests) |

- **Every recorded request:** 8,421 of 8,421 give the identical answer (coverage text exactly; searches exactly, apart from their own timing).
- **Step 31's exam boards** that can be read today, one and two turns ahead, old engine against new (`exam_depth1.json`, `exam_depth2.json`): E13 (the cutter under the rim), E24 (a man the ball can't reach) and E28 (two lanes or one): same move and value at both. The plan leaves some arrows open; I set them facing the basket on both engines.
- **Why a fixed look-ahead:** with the clocks on, a faster engine reads deeper and can decide differently. That is the clock cut-off itself (section 7), not this step changing a decision. So decisions were compared with the look-ahead fixed.
- **Same on any device:** no several-core work was built, so there is nothing to combine in a different order. The same board on two engines, at a fixed look-ahead, gave the same decision every time.
- **Engine equality, golden game, rules test, separate thinking:** all pass with nothing re-recorded (section 6b).

## 6b. Tests run

| Test | Result | Time |
|---|---|---|
| Rules test (`test_rules_current.py`) | 18 passed | 1 s |
| The memory (`test_step30b.py`) | 6 passed | 23 s |
| Golden game (`test_golden_and_regression.py`) | 8 passed, no value moved | 92 s |
| Separate thinking (`test_step24`, each side thinks alone) | 1 passed | 13 min 47 s |
| Engine equality (`step_22c.py equal 40 23`) | 40 of 40 positions equal | 73 s |

Nothing was re-recorded. Not run (over the limit): the rest of the suite for the changed files (`agent.py`, `plan.py`, `decide.py`, `engine.js` are read by most test files; the step 27 and 28 files alone run well past 10 minutes).

## 7. Every place the engine already narrows its thinking

Not changed; listed for a ruling. "Clock" means the answer can depend on how fast the device is.

**The search (both engines: `engine.js` searchJSON, `search.py`)**

| What | Where | What it cuts |
|---|---|---|
| Thinking clock: Rookie 0.3 s, Starter 1.0 s, All-Star 2.5 s | `ai_profiles.json` time_budget_s | How deep it reads. In practice only one turn ahead is sure; a faster device reads deeper |
| Deepest look-ahead 2, 3, 6 | `ai_profiles.json` | Lines past that |
| Even look-aheads only (like with like) | search | An odd look-ahead that finished is thrown away |
| First move cut off 3 turns past the deadline | search | The rest of the first move's options |
| A small-budget root under 0.8 s | search | A simpler first step when time is short |
| Beam 8, 16, 24 and expand counts | search | Options kept at each step |
| With more than 12 legal actions: top 3 looks, one move away, 4 screens | search candidate lists | The rest of the offence's options |
| Defence's open list (K and F) | search | The rest of the defence's options |
| Settled reaction read twice (All-Star only) | search | Further rounds |
| Reset after a block: stay, or the settlement's square | search | The other 300 or so squares inside the look-ahead |
| Top 8; ties reordered within the first 8 | agent | Turns past the eighth |
| Variety margin 0, 1, 2 | agent | Picks a turn within the margin at random |
| Fake mixes read as far as finished | agent | Deeper lines (clock) |
| One-step stages (contest, pick, target) | agent `_small` | No look-ahead |
| The read-ahead's clock checked only between continuations | plan horizon_read | It runs over its clock; how far it gets depends on speed |

**The offence's setup (`plan.py` place_offence; replaced in step 31)**

| What | What it cuts |
|---|---|
| Setup clock 8 × the thinking clock; quick reading 2 to 12 s | Placements tried (clock) |
| 3 sweep rounds; keep 4 after the sweep | Further rounds, other placements |
| The quick defence with no evaluations | The real defence's answer during the sweep |
| Start points from the team's own squares | Other starts |
| Job variants up to the quick time + 25 s | Variants (clock) |
| Full read capped at 95 s; "held two readings" | Later candidates (clock) |
| Full read 240 evaluations, then the read-ahead 60 s and 4 turns | More (clock and count) |

**The defence's setup (`plan.py` place_defence; replaced in step 31)**

| What | What it cuts |
|---|---|
| 240 evaluations; 10 starts; refine 12 then 6 | Placements tried |
| Pressure 8 rounds, 16 candidates; 4 swap rounds | Further rounds |
| Read ahead the first 3 only | The rest of the pool |

**The read-ahead (`plan.py` horizon_read)**

| What | What it cuts |
|---|---|
| Clock: 12 s in play, 60 s in setup | How far ahead (clock; seen in this step's High-Low turn) |
| 4 turns | Further turns |
| One line only, the best each time | Other lines |
| 3 screens, screen reach 3, one square per teammate | Other screens and squares |
| The defence's turn: first 6 candidates | The rest |
| Fake replies by a 2.5 s All-Star search | Deeper replies (clock) |

**The map (both engines: covBuild, lastingOf, settleMoves)**

| What | What it cuts |
|---|---|
| Lasting: beam 3, wide 3, head 6; groups of 3 | The defence's other answers |
| Settle moves: 2 rounds | Further rounds |
| Top 3 dangers; 3 answers per defender | Others |
| 6 looks per attacker (3 in the quick reading) | Others |
| Attention 2 and 4 | Players read in full |
| No map in the last phase | The map there |
| Next-turn reach of 2 movements | Further reach |
| Goal switch margin 8, 4, 1; top 3 overloads | Goal changes; other overloads |

**Trainer:** its own clocks per grading.

## 8. The straight answer on playability

**How much is honest thinking.** Before this step a setup was about 140 seconds, of which about 10 to 15 was work done twice, 90 to 110 parts step 31 replaces, and 35 to 75 honest searching. A turn was 26 to 47 seconds, nearly all searching. After this step, the work done twice is gone; the rest is unchanged.

**Readings per think, and their cost** (measured here, on one laptop-class core; phones are commonly 2 to 4 times slower, not measured):

| | Requests | One request takes |
|---|---|---|
| A setup | 1,000 to 1,600 (about 1,000 to 1,500 of them lasting readings) | a lasting reading 48 ms on average before, 40 ms after (the replay); a search 1.5 to 4 s |
| A turn | 2 to 400 | the same |

Each lasting reading reads several boards inside it (the defence's answers to each danger); the count per request was not measured.

**Step 31.** Its plan estimates a setup of 4 to 10 minutes and a turn of 1 to 3 minutes. This step takes perhaps 5 to 10% off that: **about 4 to 9 minutes a setup and 1 to 3 minutes a turn. That is not playable** (the goal is about a minute a setup and 20 seconds a turn).

**What could close the gap without thinking about less** (rough sizes; not built, Shaun chooses):

| Option | Rough gain | Notes |
|---|---|---|
| **Reading by difference** in step 31: after an action, update only the players it touched | 3 to 10 times on the readings | Biggest single lever; must be built into step 31's new readings from the start |
| **Several cores in the app**: the Python that orchestrates waits for answers asynchronously, and several engine workers read side by side, combined in a fixed order | 2 to 4 times on phones and laptops with 4 to 8 cores | Needs the orchestration rewritten; no server headers needed |
| **WebAssembly for the engine's core** (the map and search) | 1.5 to 3 times | A port of the core; the same-decisions checks apply in full |
| **Thinking during the human's turn**: start the computer's next setup while the human reads the result, and read its likely replies while the human plans | Hides 30 to 90 seconds a possession | Needs a second worker (memory) or the async rewrite above |
| **A server** that thinks for the app | 3 to 10 times (a desktop-class machine, all its cores) | Needs hosting and a connection; the static single-file site would no longer stand alone |

Together, reading by difference and several cores (6 to 40 times between them) would bring a step 31 setup to about 15 to 90 seconds and a turn to 2 to 30 seconds.

## 9. Noticed, not touched

- **The clocks already make decisions depend on the device.** In this step's own run, the faster engine got further inside the plan's 12-second read-ahead. With the thinking clocks on, a fast laptop and a slow phone can choose differently. The rule now says no clock cut-offs; section 7 lists each one for a ruling.
- **The engine's long-lived reading store** (`READS`, 3,000 entries) is keyed by the board's hash without the game's cards, so in principle a reading could carry from one game to another with different cards if two boards hash the same. The one-think memory built here does not use it. Worth fixing in step 31.
- **The board's hash** (`zobrist`) is built from a hand-picked list of fields, so a new field can be left out by mistake. The new memory uses the whole state instead.
- **The two engines break exact ties differently.** On E13 and E28, one turn ahead, Python picked a different move from JavaScript with the same value (O4 to H3 against O1 to J10; X1 to H10 against X5 staying on I9). Main does the same, so this is not from this step. Step 31's B2 comparisons should compare values and sets of tied moves, not a single pick.
- **Python B2 comparisons (step 31's section 6).** One turn ahead, the Python engine decides E24 and E28 in about 8 seconds each and E13 in about 70 seconds, so those three fit. Two turns ahead, the JavaScript engine takes 30 to 140 seconds a board and Python is roughly 10 times slower, so two turns or more in Python does not fit the limit for any of them. E23 (three readings) was not built here.

## 10. Model for the next step

Claude Opus 5.5 at high effort for step 31: a large rebuild across both engines that has to be built by difference from the start.
