# Step 30 code audit: after the block, the two app-only cards, the fake read ahead

Everything this step touched, where it lives in each engine, and step 27's audit run again for the four step 29 rules
and the reset. Line numbers are at the step's final commit. The changed files are in full in `step30_code/`.

## 1. After a successful block (D-276)

| Part | Python | JavaScript |
|---|---|---|
| The line straight back from the basket (ties to the diagonal; none happen) | `board.push_dir` (84) | `pushDir` (660) |
| 3 squares along it, stopped by a player or the edge | `board.pushed` (99) | `pushed` (670) |
| "Within 3": the square count used for movement and reach | `rules_config.BLOCK_RESET` (465), Chebyshev | the same 3 in `resetActions` |
| The block: −5, a new phase, the shooter pushed, his count and pick-up cleared, the reset stage | `resolve.block_reset` (143), called from `contest_outcome` (337) | `blockReset` (682), from `contestOutcome` |
| The last phase: the possession ends on what it banked | `block_reset` (the clock check) | `blockReset` |
| The reset stage: the blocker's moves (any open square within 3, any arrow, or stay) | `actions.reset_actions` (745), `legal_actions` | `resetActions` (648), `legalActions` (693) |
| Playing the reset, then the offence's new phase | `resolve.apply` 'reset' | `apply` 'reset' (1113) |
| Whose turn: the defence | `search.actor`, `state.side` | `actor` (3522) |
| The new state field | `state.reset` (encoded, and in the zobrist key) | `St.reset`, `stateFrom`, `stateJSON`, `zobrist` |
| The resets the search reads: stay, and where the map's settlement sends him | `search.reset_candidates` (169), `candidate_actions` (213) | `resetCandidates` (3563), `candidateActions` (3588) |
| The reset at the horizon and when a shot is settled by the rules | `search.reset_choice` (196); `Searcher.value` (1099), `settle_node` (1013) | `resetChoice` (3582); `value` (4263), `settleNode` (4198) |
| The words | `game.consequences` (117: Shaun's line), `view.status_line` (393) | `app.js` (the reset picked like a Move: 1205, 1260, 1849), `play.js` (16), `tips.js` (27) |

## 2. The two app-only cards (D-277)

| Part | Where |
|---|---|
| The ratings | `data.BLOCK_RATINGS['APP-SW']`, `['APP-SC']` (the PF-3 values); `BLOCK_TYPE` `slsf`, `swc`; `BLOCK_STAND_IN` emptied |
| The sheet | `docs/reference/step29/BLOCK_RATINGS.csv`, rows APP-SW and APP-SC with the note |
| The cards | read through `data.block_of` as every other card (both engines get them through `ctx_json`) |

## 3. The fake in the setup's read ahead (item 3)

| Part | Where |
|---|---|
| Each fake open to the ball handler, the defence's reply by its own mix (a one-action reply ended as the rules end it), the list read again | `plan._fake_continuations` (1321), with `_key_of` (1295) and `_weigh` (1309) |
| Read alongside the other continuations, turn by turn | `plan.horizon_read` (1422) |
| The route's words, needs and roles for a fake | `plan.route_plan` (1462, 1477) |
| The conditions from the route (shot fake against a closeout, pass fake against a likely Intercept) | `conditions` (441) |

The defence's reply comes from `agent._mix_cols`, the same search and mix it plays with (`search.mix_game`), at
`plan.FAKE_LEVEL` (All-Star, the setup's level), from the board with the fake cleared.

## 4. Step 27's audit, run again: is each rule read one way, in full, everywhere?

| Rule | The rules (both engines) | The search in play | The setup's read ahead | The map (both engines) | The scout's shot review |
|---|---|---|---|---|---|
| The block (D-271) | one way | in full | in full (through the map's looks) | in full | in full |
| After a block (D-276) | one way | in full: the reset, the new phase, read as at the horizon | through the search's reading at the end of its look | **in part: stops at −5** | **in part: stops at −5** |
| Fakes (D-272) | one way | in full (the mix) | **in full from this step** | in part (the rushed closeout only, as step 29 reported) | not read |
| The pivot (D-273) | one way | in full | in full | in full | in full |
| Deep range (D-274) | one way | in full | in full | in full | in full |

The two places that still stop a block at −5 read it the same way as each other, with no second rule:
`decide.Read._block_value` (819) and its port `blockValue` (843); `plan.case_value` (113, the scout's shot review); and
`scoring.block_option`'s expected value (292), which only orders the defence's reply options. Why the map can't simply
read on is in the report, section 7.

## 5. The two engines side by side

| Rule | Board | What must match |
|---|---|---|
| The reset | the blocked shooter on the rim board, X5 to reset (the shooter off a Sprint, the others away and unable to move) | every reset's value |
| A block at the horizon | the same board, the reply to the layup | every reply's value: Contest, Block, End turn |
| Map equality | 40 random boards (`tools/step_22c.py equal 40 23`) | 40 of 40 |
