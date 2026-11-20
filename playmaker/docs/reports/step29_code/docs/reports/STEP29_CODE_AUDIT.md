# Step 29 code audit: the block, fakes, the pivot and deep range

For each ruling and each place the computer reads it: where it lives in each engine (file, function, lines as of the merge), how setup and play use it, the test that fails if it is wrong, and anything that still reads it a second way. Every changed file is in `docs/reports/step29_code/`, in full, in the repo's layout, and zipped as `docs/reports/step29_code.zip`.

## 1. The cards: Block and Foul (Block) (D-269, D-270)

- **Python:** `playmaker_engine/data/data.py` `BLOCK_TYPE`, `BLOCK_RATINGS`, `BLOCK_STAND_IN`, `block_of` (lines 185 to 225); `playmaker_engine/cards.py` `Card.__init__` (lines 46 to 51) puts `block` and `foul_block` in every card's ratings, with bands from `data.band`.
- **JavaScript:** no copy. The cards reach `engine.js` from Python (`jsbridge.card_json`, every rating), so the two engines can't hold different values.
- **Source:** `docs/reference/step29/BLOCK_RATINGS.csv` (Shaun's), with PG-5 Slasher A at 6 and 9 (D-270).
- **Used by:** the block (section 2), the map's block price, the scout's shot review, the cards on screen (`view.card_json`, the "Block" group).
- **Tests:** `test_step29.py::test_the_blocks_position_and_rushed_reductions` reads each defender's Block from the card.
- **Read a second way:** none.

## 2. The block (D-271)

| Part | Python | JavaScript |
|---|---|---|
| The rule switch | `rules_config.block_rule` (413), `BLOCK_SIDE`, `BLOCK_BEHIND` (465) | `makeCtx` `block:` (ctx flag) |
| The option: foul rolls, Block roll, contest on a miss | `scoring.block_terms`, `block_option` (266 to 300); called from `_contest_actions` (246) | `blockOption` (807); called from `contestActions` (779) |
| Fouls, then the Block, then the shot | `resolve.contest_outcome` (315 to 322: the Block roll; the foul rolls below it wrap it) | `contestOutcome` (945 to 950) |
| A successful block is a turnover | `resolve._turnover` (D-198: −5, the phase ends, the same possession, the ball with the shooter where he stands, as after a won Steal) | `playOn` with `tos + 1` (946 to 948) |
| The map's price (the race) | `decide.Read._block_value` (804 to 832), used in `_vals` (750) for every contest kind he reaches, every shot | `blockValue` (791), used in `_valsCalc` (2197) |
| The scout's shot review | `plan.BLOCK_CASES`, `cases_for`, `block_left`, `case_value` (36 to 115) | (Python only: the setup's scout runs in Python) |

- **How the computer uses it:** in play the search tries Contest and Block as legal replies and reads each by the rules (the foul rolls, the Block roll, the turnover, the shot). The map prices a defender's best reply from each square he reaches as the lower of his Contest and his Block, so the race, the setup's placements, the read-ahead and the shot bar all see the block through the same reading. The scout's table has the block from every position for every shot (26 cases).
- **No floor (Shaun, 20 Nov):** a look where a block is possible can be worth less than nothing (down to the turnover's −5), in both maps, so the computer sees a likely block and avoids the shot. The shot's own floor (OQ-5) stays where nothing below 0 can happen. One reading took it badly: the coverage test's "what's left of the look is never below 0" (re-recorded, with a note). The coverage view shows such a square as no look (its shading starts above 0) and its words round the number.
- **One convention to know:** the map prices a block's turnover at −5 and stops there, the same way it prices a lost pass in a look (step 26, D-250). The search plays the turnover out (the next phase is read), so in play a block is weighed against what the offence's next phase is worth. That is why, on the check board, the computer contests rather than blocks a layup it would hold to 12 (section "Checks" in the report).
- **Tests:** `test_step29.py`: one contest or block per shot; the block on every shot, threes included; the position and rushed reductions; the order (foul, block, contest on a miss); a successful block is a turnover; `test_both_engines_make_the_same_decision[block]`. Re-recorded: `test_step24` (the table), `test_step28` (the block on threes), `test_fiba_18i`.
- **Read a second way:** none found. The old hard Contest stays in the engine behind `block: off` (the table's rules are on hold).

## 3. Shot and pass fakes (D-272)

| Part | Python | JavaScript |
|---|---|---|
| The rule switch | `rules_config.fakes_rule` (418) | `makeCtx` `fakes:` |
| When a fake is open | `actions.fake_open` (743) | `fakeOpen` (620) |
| The fake actions (arrow 1 on Shot or Pass) | `actions._offence_actions` (799) | `offenceActions` (612) |
| The declaration (public `decl`, hidden `fake`) | `resolve.apply` 'shot' and 'pass' | `apply` 'shot' and 'pass' |
| The reveal: the count back, Hesitate or fake used, picked up after movement, not made active | `resolve.unmask` (143), `reveal` (158) | `unmask` (889), `reveal` (896) |
| The defence's reply ends: the shot fake shown | `resolve.resolve_shot` (265) | `resolveShot` (925) |
| An honest Contest does nothing; a block locks and rolls an ordinary foul | `resolve.apply` 'contest', `fake_block` (171) | `apply` 'contest' (1072), `fakeBlock` (901) |
| A Steal on a shot fake is an ordinary Steal | `resolve.apply` (747) | `apply` (1165) |
| The pass fake: Intercept or Steal locks; a movement keeps it in the air; anything else shows it | `resolve.apply` (557 to 576), `end_turn` (464) | `apply` (1078), `endTurn` (1039) |

- **The defence never reads the hidden choice.** The agent blinds the state before the defence decides (`agent.choose`, line 119: `s.with_(fake=0)`). The search never reads `s.fake` either: at a declaration it builds both worlds itself from the public state (`search.worlds`, 118; `engine.js` `worlds`). No reading module touches it: `test_no_reading_reads_the_hidden_choice` checks the source of `decide`, `plan`, `conditions`, `goals` and `scouting`, and every line of `engine.js` that mentions it.
- **Hidden on screen:** the game logs a fake as the declaration it looks like, and shows it only once the defence has replied (`game._apply`, `fake_reveal_lines`); the state sent to the page carries no fake (`pub.encode()`); the offence's mix note is kept until the possession is over.
- **Tests:** the reply is the same to a real or fake shot and pass (legal actions, and the state less its hidden bit); the defence's computer replies the same in both engines (`test_the_defence_reply_never_reads_the_hidden_choice`, and `..._in_javascript`); the reply to a fake is the defence's turn; a block on a fake locks and rolls the ordinary foul (+5, no free throws, the block's geometry), an honest contest doesn't lock; a pass fake locks a Steal or Intercept, a held lane costs nothing; no fake when rushed; one Hesitate or fake a phase; a fake after movement picks the ball up, from a standstill it doesn't; a fake doesn't keep him active.
- **Read a second way:** see section 7 (the map).

## 4. The mixed choice (D-272)

| Part | Python | JavaScript |
|---|---|---|
| The game: the offence's p, the defence's mix | `search.mix_game` (123) | `mixGame` (3486) |
| Inside the search, at every declaration that could be a fake | `Searcher.mixed` (1129), called from `value` (1057) | `Searcher.mixed` (4296), from `value` |
| Each column a whole reply (both actions), one real-or-fake choice | `Searcher.reply_cols` (1147) | `replyCols` (4309) |
| The defence's reply at the root, both worlds | `Searcher._root_mix` (1349) | `_rootMix` (4327); `search()` returns `mix` |
| The draws, by the game's seed | `agent._mix_cols` (237), `_reply_mix` (259), `_maybe_fake` (283) | (the agent is shared: Python, in the browser through Pyodide) |
| Fakes are read as the mix, not tried as moves | `search.candidate_actions` | `candidateActions` |

- **How it is worked out:** at a shot or pass that could be a fake, every reply the defence would try is played against the real declaration and against the fake, each read by the search as deep as it reads anything. A fake with chance p makes each reply worth (1 − p) × its real value + p × its fake value; the defence takes the reply that leaves the offence least; the offence takes the p that leaves it most. The defence's mix is the one that makes the offence's real and fake worth the same. No weights: only the values.
- **Fixed during the step (Shaun's question about 27 against 18):** a reply of one action left the defence mid-reply, and the search solved a fresh mixed game there, as if the offence could choose real or fake again after seeing the defender's first step. Each column is now the defence's whole reply, so the offence's choice is made once, before the reply, as the rule says.
- **Each side its own model:** the offence's p comes from the offence's own search (its profile, `_maybe_fake`); the defence's mix from the defence's own search (`_reply_mix`).
- **Tests:** `test_the_mix_by_hand`; `test_the_fake_mix_cant_be_beaten_by_a_fixed_habit_on_a_small_board` (on a real board, neither side gains by a fixed habit against the other's mix); `test_both_engines_make_the_same_decision[fake]` (the same per-reply values in both engines).
- **Read a second way:** none in play. The setup's read-ahead doesn't run the search, so it reads the fake only through the rushed closeout (section 7).

## 5. The pivot (D-273)

| Part | Python | JavaScript |
|---|---|---|
| The switch, and whether it is open | `rules_config.pivot_rule` (423), `pivot_open` (428), `state.pivoted` | `makeCtx` `pivot:`, `pivotOpen` (320) |
| One square, the card's Quick Step needed | `actions.pivot_len` (269), `can_move_kind` (339) | `pivotLen` (496), `canMoveKind` |
| Still picked up, the count runs on, once a pick-up | `resolve.apply` movement (593); `phase_counts` (396) | `apply` (1091); `phaseCounts` (998) |
| The map's reach | `decide._caps` (104), `attacker_reach` | `caps`, `attackerReach`, `attackerReachExact` (1425) |
| The count after a pivot, in the map | `decide` phase starts (1454) | `guardAt` (4927) |

- **Tests:** the pivot Quick Step (one square, still picked up, rushed, then only pass or shoot); no pivot without a Quick Step; `test_both_engines_make_the_same_decision[pivot]`. Re-recorded: `test_fiba_18i` (picked up: no Quick Step but the pivot), `test_step22c` (the closely guarded count reads his pivot square too).
- **Read a second way:** fixed in this step. The map's reach let a picked-up ball handler move as if he hadn't picked up; it now gives him only his pivot.

## 6. Deep range (D-274)

| Part | Python | JavaScript |
|---|---|---|
| The deep squares (Shaun's board) | `board.deep` (84) | `DEEP` table built in `init` (102) |
| Rows by playing level; no level is Senior Pro | `rules_config.deep_rows_for`, `deep_open`, `DEEP_ROWS` (441 to 462); `game.deep_rows_for_offence` (each team its own) | `deepRowsFor` (144); `makeCtx` `deep:` (165), from `ctx_json` `deep_rows` |
| The shot zone and the rating | `scoring.zone_at`, `shot_zone`, `deep_cut`, `card_shot` (60 to 95), `shot_rating` (99) | `szone`, `deepCut`, `cardShot` (151 to 153), `shotRating` (187) |
| Legal shots, forced shots | `actions._offence_actions` (768), `legal_actions`; `resolve.resolve_shot` | `offenceActions`, `legalActions`, `resolveShot` |
| The map: looks, gaps, the phase away, shot paths | `decide` (883, 739, 1837 and the phase-away reading) | `build`, `pre`, `_valsCalc`, `gapInfo`, `gapLate`, `shotPaths` (4775) |
| The display and words | `view.deep_squares`, `shot_chips` ("Deep three: 2 off") | `notation.court` (the number with Show the numbers on), `app.pieceLabel` (the words when tapped and for screen readers) |

- **Tests:** deep range by square (Shaun's board, square for square), by level (pro to junior: legal shots and the rating), the playing levels' rows and each team's own; `test_both_engines_make_the_same_decision[deep]`. Re-recorded: `test_coverage_18s` (I11 is a deep three at pro).
- **Read a second way:** none. The map, the scout and the rules all go through `shot_zone` and `card_shot` (Python) or `szone` and `cardShot` (JavaScript).

## 7. Integration points

- **The race and the map:** the contest and the block cost one of the reply's actions (D-261's one movement); the block's chance and foul risk by position (section 2); deep squares by level (section 6); the pivot (section 5). **The fake in the map:** the map reads a shooter's fake only through what the rules already price: a defender who must close out with a Quick Step or Sprint arrives rushed (2 off his contest and his block). The fake's full value (the defence's wasted reply, the drive past a rushed defender) is read by the search at every declaration, as the mixed game. So in play the computer fakes and fears fakes; in setup it sees them only as the rushed closeout. This is the one place the step's rules are read two ways; the report sets out the option to close it.
- **The scout:** Block and Foul (Block) per defender, who can pivot, deep threes by level, who can fake (`view.scout_table_json`); the block in every case of the shot review (`plan.case_value`).
- **Both setups and the matchup rule:** no new step. Block and Foul (Block) reach the matchup rule only through the map's price of each defender's best reply (section 2), and the deep squares through the looks (section 6).
- **The search and the read-ahead:** the fake, the pivot and the block are legal moves in the search; the mix sits inside it (section 4). The read-ahead (`plan.horizon_read`) reads them through the map.
- **The conditions list:** `conditions.read` reads the five proposed additions (58 to 62) from the map's own looks, the same measure as the rest; `PROPOSED` marks them; 32 (attack the closeout) was already read and is marked so in `docs/reference/OFFENCE_CONDITIONS_19NOV.md`.
- **The shot bar and the coach's lines:** the reply line ("Contesting or blocking is one of them"), the Contest and Block options with their chance and foul risk, the deep chip, the fake reveal line, the Coach's tip for the fake.

## 8. The two engines side by side

Each rule has an engine-equality case in `tests/test_step29.py::test_both_engines_make_the_same_decision`, which runs the Python search and the JavaScript search on the same board, reading the same number of turns ahead, and asks for the same values for every turn (and, for the fake, the same real and fake values for every reply):

| Rule | Board | What must match |
|---|---|---|
| The block | O5 lays it up from H4; X5 square in front, X4 beside (the other defenders locked so the replies are few) | every reply's value, Contest and Block |
| The fake and its mix | O1's three from C9, X1 behind him | every reply's value, and each reply's real and fake values |
| The pivot | O1 picked up on C9 | every turn's value, his one-square pivots among them |
| Deep range | O1 on A10, three squares past the arc, at Senior Pro | every turn's value, the deep three among them |

All four pass. The 40 random boards of `tools/step_22c.py equal` also agree, 40 of 40.
