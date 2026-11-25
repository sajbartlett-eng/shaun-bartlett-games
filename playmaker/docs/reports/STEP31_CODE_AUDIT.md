# Step 31: code audit

For each part of the design: where it lives in each engine, how setup and play use it, and the test that guards it. Line numbers are as of this commit.

| Part of the design | JavaScript engine (the app's) | Python engine | Used by | Guarded by |
|---|---|---|---|---|
| The one number: the possession's value | `possRead` (engine.js 6297), `possParts` (engine.js 6554), `routeT` (engine.js 6256), `possValue` (engine.js 7028) | `poss_read` (value.py 114), `poss_parts` (value.py 358), `_route_t` (value.py 55), `poss_value` (value.py 386) | Setups: every stance and placement is ranked by it (`stanceRead`, `offenceSetup`). Play: the end of every line the search reads (`_mapLeaf`), the quick reading that orders the lists (`quickLeaf`). | test_exam: O1, O1 fails without, G5, B2 (5 boards), the brute guard |
| The defence's answer inside the number, with its exact cuts | `possRead` (engine.js 6297) (the greedy movements, `runCand`, `bears`, `BOUND_LOOKS`) | `poss_read` (value.py 114) | The same everywhere the value is read. | test_exam: the answer is the same with every movement read in full |
| Take the good shot: shot now against playing on | `_mapLeaf` (engine.js 3192), `mapShotOrNone` (engine.js 3147) | `_map_leaf` (decide.py 2187), `map_shot_or_none` (decide.py 2169) | Play: the end of every line. | test_exam O1 |
| The shot clock running out is minus 5 | `possRead` (engine.js 6297) (the first bar) | `poss_read` (value.py 114) | Both. | test_exam: the shot clock running out |
| The block read past minus 5 | `blockLine` (engine.js 873), `_valsCalc` (engine.js 2265) (split) | `_block_c1` (decide.py 838), `_vals` (decide.py 709) | Inside the value and the weight map. | B2 on BLK1 |
| Three seconds from entry, counted once | `threeSecondsLeave` (engine.js 7032), `threeSecondsStuck` (engine.js 6213) | `three_seconds_leave` (value.py 26), `three_seconds_stuck` (value.py 41) | Inside the value (the actions a route may use). | exam O2 (fails: see the report) |
| Worth right now | `ctx.worth` (engine.js 176) | `worth_now` (rules_config.py 484); `jsbridge.py` passes it | Every shot value in both engines. | exam D7; B2 on E8 |
| The segments | `segInit` (engine.js 6594); `data/segments.json` | `segments` (weight.py 26) | The weight map, the base positions, the offence's scout. | the segments trial (docs/runs/step31/segments_trial.json) |
| The weight map, layers 1 to 3, the centre, the lumps | `weightMap` (engine.js 6612), `weightBase` (engine.js 6683), `weightJSON` (engine.js 6709) | `weight_map` (weight.py 51), `weight_base` (weight.py 161), `weight_json` (weight.py 217) | Setups: the defence's base positions. The app: the Coverage view (`view.py`, `app.js`). | tools/step_31.py bothweight (46 boards, both engines) |
| The defence's setup: base positions, the joint search, pairs | `stanceBase` (engine.js 6797), `stanceSearch` (engine.js 6833), `stanceRead` (engine.js 6739), `stanceLess` (engine.js 6758), `stanceQuick` (engine.js 6917) | `place_defence` (setup31.py 60) asks the JavaScript engine (`agent.coverage(only="stances")`); `defender_lines` (setup31.py 32) | Setup only. `plan.place_defence` hands over under the value. | exam D1 to D12, G1 to G4, A1 to A16 (many fail: see the report) |
| The offence's setup: scout, ball handler's start, positions, improvement, finalists | `offenceSetup` (engine.js 6928) | `place_offence` (setup31.py 78) asks the JavaScript engine (`only="offence_setup"`) | Setup only. `plan.place_offence` hands over under the value. | exam O3, O4, O9 |
| The levels: a fixed look-ahead, no clock | `search` (engine.js 4714) (deadline = Infinity); `ai_profiles.json` look_ahead | `look_ahead` (agent.py 33); `agent._choose` (budget None) | Play. | test_exam B3 runs the app's agents with no clock |
| Level turns in one order; standing still first (D-300) | `tieCmp` (engine.js 4664) | `tie_key` (search.py 87), `tie_cmp` (search.py 96); `agent._driver_order` steps aside under the value | Play, at the root of the search. | tools/js_equivalence.py (40 of 40) |
| The mix: hold when holding is level (D-298) | `mixGame` (engine.js 3585) | `mix_game` (search.py 142) | Play, every fake. | test_exam A12, A13, the mix in both engines |
| The whole state is the memory's key | `zobrist` (engine.js 3553); `MAP_MEMO` keys PV, WM, SR | `zobrist` (search.py 68); `memo.py` | Every reading inside one think. | test_step30b; test_exam: after each legal action the memory equals a fresh reading |
| What the player sees | `covValueOf`, `covWeightOf` in the coverage answer | `view.py` (value, weight), `app.js` (captions, the centre marker) | The Coverage view. | none (display) |

**Tools and tests added:** `tests/exam_boards.py` (the boards), `tests/test_exam.py` (the exam), `tools/step_31.py` (one reading of any board in either engine), `tools/step_31_exam.py` (read, extra, judge, segments, caps, b4).

**Run files:** `docs/runs/step31/`: `exam_readings.json`, `exam.json`, `exam.md`, `both_value.json`, `both_weight.json`, `segments_trial.json`, `caps_trial.json`, `b4.json`, `look_ahead.json`, `tests.json`.

**Every changed or added file** is in `docs/reports/step31_code/` in the repo's own layout, and zipped as `docs/reports/step31_code.zip`.
