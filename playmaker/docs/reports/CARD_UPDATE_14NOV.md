# Card update, 14 November 2026 (D-184)

1. **Open jump shots and jump-shot contests are lower on all 75 cards,** layups for weak finishers rise to 85%, and
   dunks are barely changed by a defender now. The cards now match the FIBA audit.
2. **Two new player types are in the app only:** the Slashing Wing and the Switch Centre, three tiers each, plain
   ratings. The table keeps its 25 types and nothing was reprinted.
3. **One fix to your numbers, asked and answered:** the three-point map read 10→8 with 9 unchanged, which put 11
   A-tier cards below their B tier. You chose 10→9.
4. **Everything derived from the cards is regenerated:** the levels file, the site bundle, the one-file app, and the
   scouting team sheet. The JavaScript engine reads the cards from Python, so it has no copy to change.
5. **Seven fast tests fail, each on a value recorded from the old cards.** They are listed below. I did not mark them
   as expected failures: that edit was blocked by the session's safety check, so they are left for you or the refit.

## The ratings changed, by kind

| Rating | Cards changed |
|---|---|
| Three | 30 |
| Mid-range | 65 |
| Long two | 55 |
| Layup | 25 |
| Dunk | 1 |
| Three contest | 75 |
| Mid-range contest | 75 |
| Long-two contest | 75 |
| Floater contest | 75 |
| Dunk contest | 75 |
| Layup contest | 5 |
| **All** | **556 ratings on 75 cards** |

- The six contest maps reach every card, because every old value is in each map.
- **Bands:** the range table changed for the nine rescaled ratings, and every band on every card is recomputed from
  it. 29 of the 31 old chart-fix notes were for those ratings and are removed; 2 remain (`apgB` dunk, `apgB`
  layup contest).

**The checks you asked for all pass:** no dunk contest above the same card's layup contest; no open three above 11,
mid-range above 12, or long two above 11; tiers keep their order within every type, the new ones included.

## Every card, before and after

Ratings not shown are unchanged.

| Card | Type | Before → after |
|---|---|---|
| apgA | Attacking Point Guard A | three 10→9; mid-range 13→11; long two 11→9; three contest 4→2; mid-range contest 5→3; long-two contest 4→2; floater contest 5→4; dunk contest 7→3 |
| apgB | Attacking Point Guard B | mid-range 12→10; long two 10→9; three contest 3→2; mid-range contest 4→2; long-two contest 3→2; floater contest 4→3; dunk contest 5→2 |
| apgC | Attacking Point Guard C | mid-range 11→10; long two 9→8; three contest 2→1; mid-range contest 3→2; long-two contest 2→1; floater contest 3→2; dunk contest 4→1 |
| cgA | Combo Guard A | three 11→9; mid-range 13→11; long two 12→10; three contest 5→2; mid-range contest 6→3; long-two contest 5→3; floater contest 5→4; dunk contest 8→3 |
| cgB | Combo Guard B | three 10→9; mid-range 12→10; long two 11→9; three contest 4→2; mid-range contest 5→3; long-two contest 4→2; floater contest 4→3; dunk contest 6→2 |
| cgC | Combo Guard C | mid-range 11→10; long two 10→9; layup 16→17; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 4→1 |
| dpgA | Defensive Point Guard A | mid-range 11→10; long two 9→8; three contest 6→3; mid-range contest 7→4; long-two contest 6→3; floater contest 5→4; dunk contest 10→4 |
| dpgB | Defensive Point Guard B | layup 16→17; three contest 5→2; mid-range contest 6→3; long-two contest 5→3; floater contest 4→3; dunk contest 8→3 |
| dpgC | Defensive Point Guard C | layup 16→17; three contest 4→2; mid-range contest 5→3; long-two contest 4→2; floater contest 3→2; dunk contest 6→2 |
| spgA | Scoring Point Guard A | three 12→10; mid-range 15→12; long two 13→10; three contest 3→2; mid-range contest 4→2; long-two contest 3→2; floater contest 4→3; dunk contest 7→3 |
| spgB | Scoring Point Guard B | three 11→9; mid-range 14→11; long two 12→10; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 5→2 |
| spgC | Scoring Point Guard C | three 10→9; mid-range 13→11; long two 11→9; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 4→1 |
| ppgA | Pass-First Point Guard A | three 10→9; mid-range 13→11; long two 10→9; three contest 4→2; mid-range contest 5→3; long-two contest 4→2; floater contest 4→3; dunk contest 8→3 |
| ppgB | Pass-First Point Guard B | mid-range 12→10; long two 9→8; layup 16→17; three contest 3→2; mid-range contest 4→2; long-two contest 3→2; floater contest 3→2; dunk contest 6→2 |
| ppgC | Pass-First Point Guard C | mid-range 11→10; layup 16→17; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 4→1 |
| twA | Two-Way Shooting Guard A | three 11→9; mid-range 14→11; long two 12→10; three contest 6→3; mid-range contest 7→4; long-two contest 6→3; floater contest 5→4; dunk contest 10→4 |
| twB | Two-Way Shooting Guard B | three 10→9; mid-range 13→11; long two 11→9; three contest 5→2; mid-range contest 6→3; long-two contest 5→3; floater contest 4→3; dunk contest 8→3 |
| twC | Two-Way Shooting Guard C | mid-range 12→10; long two 10→9; layup 16→17; three contest 4→2; mid-range contest 5→3; long-two contest 4→2; floater contest 3→2; dunk contest 6→2 |
| tndA | Three-and-D Shooting Guard A | three 12→10; mid-range 15→12; long two 13→10; three contest 7→3; mid-range contest 8→4; long-two contest 7→4; floater contest 5→4; dunk contest 10→4 |
| tndB | Three-and-D Shooting Guard B | three 11→9; mid-range 14→11; long two 12→10; layup 16→17; three contest 6→3; mid-range contest 7→4; long-two contest 6→3; floater contest 4→3; dunk contest 8→3 |
| tndC | Three-and-D Shooting Guard C | three 10→9; mid-range 13→11; long two 11→9; layup 16→17; three contest 5→2; mid-range contest 6→3; long-two contest 5→3; floater contest 3→2; dunk contest 6→2 |
| pmsA | Playmaker Shooting Guard A | three 10→9; mid-range 13→11; long two 11→9; three contest 4→2; mid-range contest 5→3; long-two contest 4→2; floater contest 5→4; dunk contest 8→3 |
| pmsB | Playmaker Shooting Guard B | mid-range 12→10; long two 10→9; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 4→3; dunk contest 6→2 |
| pmsC | Playmaker Shooting Guard C | mid-range 11→10; long two 9→8; layup 16→17; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 4→1 |
| shsA | Sharpshooter Shooting Guard A | three 13→11; mid-range 16→12; long two 14→11; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 4→3; dunk contest 8→3 |
| shsB | Sharpshooter Shooting Guard B | three 12→10; mid-range 15→12; long two 13→10; layup 16→17; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 6→2 |
| shsC | Sharpshooter Shooting Guard C | three 11→9; mid-range 14→11; long two 12→10; layup 16→17; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 4→1 |
| bgsA | Bucket Getter Shooting Guard A | three 12→10; mid-range 15→12; long two 13→10; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 4→3; dunk contest 7→3 |
| bgsB | Bucket Getter Shooting Guard B | three 11→9; mid-range 14→11; long two 12→10; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 5→2 |
| bgsC | Bucket Getter Shooting Guard C | three 10→9; mid-range 13→11; long two 11→9; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 4→1 |
| dpfA | Defensive Power Forward A | mid-range 10→9; three contest 7→3; mid-range contest 8→4; long-two contest 8→4; floater contest 5→4; dunk contest 13→6; layup contest 11→10 |
| dpfB | Defensive Power Forward B | three contest 6→3; mid-range contest 7→4; long-two contest 7→4; floater contest 4→3; dunk contest 11→5 |
| dpfC | Defensive Power Forward C | layup 16→17; three contest 5→2; mid-range contest 6→3; long-two contest 6→3; floater contest 3→2; dunk contest 10→4 |
| arpfA | All-Rounder Power Forward A | mid-range 13→11; long two 11→9; three contest 5→2; mid-range contest 6→3; long-two contest 6→3; floater contest 5→4; dunk contest 12→5 |
| arpfB | All-Rounder Power Forward B | mid-range 12→10; long two 10→9; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 4→3; dunk contest 10→4 |
| arpfC | All-Rounder Power Forward C | mid-range 11→10; long two 9→8; layup 16→17; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 3→2; dunk contest 9→4 |
| pnpA | Pick-and-Pop Power Forward A | three 10→9; mid-range 14→11; long two 12→10; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 5→4; dunk contest 11→5 |
| pnpB | Pick-and-Pop Power Forward B | mid-range 13→11; long two 11→9; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 4→3; dunk contest 9→4 |
| pnpC | Pick-and-Pop Power Forward C | mid-range 12→10; long two 10→9; layup 16→17; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 8→3 |
| stpfA | Stretch Power Forward A | three 11→9; mid-range 15→12; long two 13→10; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 5→4; dunk contest 11→5 |
| stpfB | Stretch Power Forward B | three 10→9; mid-range 14→11; long two 12→10; layup 16→17; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 4→3; dunk contest 9→4 |
| stpfC | Stretch Power Forward C | mid-range 13→11; long two 11→9; layup 16→17; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 8→3 |
| pspfA | Post Scorer Power Forward A | mid-range 12→10; long two 9→8; three contest 5→2; mid-range contest 6→3; long-two contest 6→3; floater contest 5→4; dunk contest 12→5 |
| pspfB | Post Scorer Power Forward B | mid-range 11→10; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 4→3; dunk contest 10→4 |
| pspfC | Post Scorer Power Forward C | mid-range 10→9; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 3→2; dunk contest 9→4 |
| rpcA | Rim Protector Centre A | mid-range 10→9; three contest 6→3; mid-range contest 8→4; long-two contest 8→4; floater contest 7→5; dunk contest 14→6; layup contest 12→10 |
| rpcB | Rim Protector Centre B | three contest 5→2; mid-range contest 7→4; long-two contest 7→4; floater contest 6→5; dunk contest 12→5; layup contest 11→10 |
| rpcC | Rim Protector Centre C | layup 16→17; three contest 4→2; mid-range contest 6→3; long-two contest 6→3; floater contest 5→4; dunk contest 11→5 |
| stcA | Stretch Centre A | three 10→9; mid-range 15→12; long two 12→10; three contest 5→2; mid-range contest 6→3; long-two contest 6→3; floater contest 6→5; dunk contest 12→5 |
| stcB | Stretch Centre B | mid-range 14→11; long two 11→9; layup 16→17; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 5→4; dunk contest 10→4 |
| stcC | Stretch Centre C | mid-range 13→11; long two 10→9; layup 16→17; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 4→3; dunk contest 9→4 |
| pmcA | Playmaking Centre A | mid-range 13→11; long two 10→9; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 5→4; dunk contest 12→5 |
| pmcB | Playmaking Centre B | mid-range 12→10; long two 9→8; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 5→4; dunk contest 10→4 |
| pmcC | Playmaking Centre C | mid-range 11→10; layup 16→17; three contest 3→2; mid-range contest 3→2; long-two contest 3→2; floater contest 4→3; dunk contest 9→4 |
| pscA | Post Scorer Centre A | mid-range 11→10; three contest 4→2; mid-range contest 6→3; long-two contest 6→3; floater contest 5→4; dunk contest 13→6; layup contest 11→10 |
| pscB | Post Scorer Centre B | mid-range 10→9; three contest 3→2; mid-range contest 5→3; long-two contest 5→3; floater contest 4→3; dunk contest 11→5 |
| pscC | Post Scorer Centre C | three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 4→3; dunk contest 10→4 |
| rrcA | Rim Runner Centre A | mid-range 10→9; three contest 5→2; mid-range contest 7→4; long-two contest 7→4; floater contest 6→5; dunk contest 13→6; layup contest 11→10 |
| rrcB | Rim Runner Centre B | dunk 18→19; three contest 4→2; mid-range contest 6→3; long-two contest 6→3; floater contest 5→4; dunk contest 11→5 |
| rrcC | Rim Runner Centre C | three contest 3→2; mid-range contest 5→3; long-two contest 5→3; floater contest 4→3; dunk contest 10→4 |
| twsfA | Two-Way Small Forward A | three 10→9; mid-range 13→11; long two 11→9; three contest 6→3; mid-range contest 7→4; long-two contest 7→4; floater contest 5→4; dunk contest 11→5 |
| twsfB | Two-Way Small Forward B | mid-range 12→10; long two 10→9; three contest 5→2; mid-range contest 6→3; long-two contest 6→3; floater contest 4→3; dunk contest 9→4 |
| stsfA | Stretch Small Forward A | three 12→10; mid-range 14→11; long two 13→10; three contest 5→2; mid-range contest 6→3; long-two contest 5→3; floater contest 5→4; dunk contest 10→4 |
| stsfB | Stretch Small Forward B | three 11→9; mid-range 13→11; long two 12→10; layup 16→17; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 4→3; dunk contest 8→3 |
| dfsfA | Defensive Small Forward A | mid-range 11→10; long two 9→8; three contest 7→3; mid-range contest 8→4; long-two contest 8→4; floater contest 5→4; dunk contest 12→5 |
| dfsfB | Defensive Small Forward B | mid-range 10→9; three contest 6→3; mid-range contest 7→4; long-two contest 7→4; floater contest 4→3; dunk contest 10→4 |
| scsfA | Scoring Small Forward A | three 11→9; mid-range 15→12; long two 13→10; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 5→4; dunk contest 10→4 |
| scsfB | Scoring Small Forward B | three 10→9; mid-range 14→11; long two 12→10; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 4→3; dunk contest 8→3 |
| pfsfA | Point Forward Small Forward A | three 10→9; mid-range 13→11; long two 12→10; three contest 5→2; mid-range contest 6→3; long-two contest 6→3; floater contest 5→4; dunk contest 10→4 |
| pfsfB | Point Forward Small Forward B | mid-range 12→10; long two 11→9; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 4→3; dunk contest 8→3 |
| twsfC | Two-Way Small Forward C | mid-range 11→10; long two 9→8; layup 16→17; three contest 4→2; mid-range contest 5→3; long-two contest 5→3; floater contest 3→2; dunk contest 8→3 |
| stsfC | Stretch Small Forward C | three 10→9; mid-range 12→10; long two 11→9; layup 16→17; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 3→2; dunk contest 7→3 |
| dfsfC | Defensive Small Forward C | layup 16→17; three contest 5→2; mid-range contest 6→3; long-two contest 6→3; floater contest 3→2; dunk contest 9→4 |
| scsfC | Scoring Small Forward C | mid-range 13→11; long two 11→9; three contest 2→1; mid-range contest 3→2; long-two contest 3→2; floater contest 3→2; dunk contest 7→3 |
| pfsfC | Point Forward Small Forward C | mid-range 11→10; long two 10→9; layup 16→17; three contest 3→2; mid-range contest 4→2; long-two contest 4→2; floater contest 3→2; dunk contest 7→3 |

## The two new types (app only)

| Key | Type | QS | Offence | Defence |
|---|---|---|---|---|
| slsfA | Slashing Wing Small Forward A | 2 | 17H 14A 13L | 19H 19H 12A 11A 9A 8A 7L 16A | 9H 8H 8H 4H 7A | 8A 3A 4A 4A 3H 3H 2A 9A |
| slsfB | Slashing Wing Small Forward B | 2 | 16A 13L 12L | 18A 19H 11L 10A 8L 7L 6L 15A | 8H 7A 7A 3A 8A | 7A 3A 4A 3A 3H 3H 2A 10L |
| slsfC | Slashing Wing Small Forward C | 1 | 15A 12L 11L | 17L 18H 10L 9L 7L 7L 6L 14A | 7A 6A 6A 3A 9L | 6L 2L 3L 3A 2A 2A 2A 11L |
| swcA | Switch Centre A | 2 | 14A 13L 16A | 19H 19H 13A 9L 9A 7L 6L 14A | 9H 7A 8H 3A 6H | 8A 4A 6H 4A 3H 3H 3H 6H |
| swcB | Switch Centre B | 1 | 13L 12L 15A | 18A 19H 12A 8L 8L 7L 5L 13L | 8H 6A 7A 3A 7A | 7A 3A 5A 4A 3H 3H 2A 7H |
| swcC | Switch Centre C | 1 | 12L 11L 14A | 17L 18H 11L 8L 7L 6L 5L 13L | 7A 5L 6A 2A 8A | 6L 3A 4A 3A 2A 2A 2A 8A |

- **In `data.py`** as `APP_CARDS`, listed in `APP_ONLY`. `TABLE_CARDS` is the table's 75. The app's card list is
  all 81, so the new types appear in random deals, the draft, custom line-ups, and scouting.
- **Bands** come from the range table, not the prompt.
- **For you to check, one field:** the role names. I used **"Slashing Wing Small Forward"** and **"Switch Centre"**,
  following the existing pattern (type, then position). Shorter options: "Slashing Small Forward".
- **The ten prescribed teams are unchanged.**

## Other changes the new cards needed

- **Random deals count the real number of cards at each position and tier** (`rosters.py`). The count assumed 5;
  small forwards and centres now have 6 at each tier.
- **The four jobs** (creator, shooter, anchor, stopper, used for coherent random deals and the team read) were fixed
  numbers on the old scale: a shooter had a three of 10, an anchor a dunk contest of 11. With the new cards no team
  could field two shooters, so coherent deals failed. I carried the thresholds through the same maps: **a shooter now
  has a three of 9, an anchor a dunk contest of 5** (layup contest 10 unchanged). Because old 9s and 10s both land on
  9, **13 cards that were not shooters now are** (`apgB`, `cgC`, `dpgA`, `ppgB`, `twC`, `pmsB`, `arpfA`, `pnpB`,
  `stpfC`, `stcB`, `twsfB`, `pfsfB`, `scsfC`). No anchor changed. The same thresholds are in the data tools
  `teamtools.py` and `check_scenarios.py` (its "open look" layup cut moves 16→17 with the layup floor).
- **Two counts in tests were extended** as the prompt asked: the junior deck matches all 81 cards (and checks the table
  still has 75), and the matchup check covers every pair of the 81.
- **Old random-deal codes** now deal different teams: the pools behind each code are larger.

## Derived files regenerated

| File | How |
|---|---|
| `playmaker_engine/data/levels_data.py` | `tools/levels_generator.py` (regenerating it on the old cards first gave the committed file exactly) |
| `site/engine_bundle.json`, `site/speedtest_positions.json`, `dist/playmaker.html` | `python -m playmaker_web.build_site` |
| `docs/TEAM_SHEET_HUNT_PROTECT.md` | `scouting.team_sheet_markdown()` |
| `docs/levels_draft_board.png`, `docs/levels_junior_card.png` | rewritten by the test run; they show the new cards |

- **The JavaScript engine** has no copy of the cards: it takes them from Python with each position. A short agreement
  check on the new cards: 80 positions, 2 searches and 80 shot reactions, no differences.
- **No hand-written copy of the cards or the range table** was found in the app.
- **`tools/levels_generator.py` writes to an old path** (`engine_handoff/`) and imports `data` from its own folder,
  so it doesn't run as it stands. I ran it with those two paths pointed at `playmaker_engine/data`, without changing
  the tool.

## Print files that would change (not reprinted)

- `reference/Playmaker_Cards_U16_Junior.pdf` (the junior cards come from the pro cards)
- `reference/Playmaker_Playing_Levels.pdf` and `playmaker_web/static/docs/Playmaker_Playing_Levels.pdf`
- The printed pro cards (not in this repository)
- `reference/Playmaker_Scenarios.pdf` and `reference/Playmaker_Play1_High-Low.pdf`, if they show card numbers
- The trackers only if they quote contest values: `reference/Offence_tracker.pdf`, `reference/Defence_tracker.pdf`

## Now stale (for the refit)

- the calibrated maps (`learned_weights.json`), the phase table and the quick reading built on it;
- the foul-price numbers (`eval.fouls_per_possession`, `eval.play_on_value`);
- the sense-check set's played-out answers (every `tools/sense_set/answers*.json`);
- the exam answers and the exam book;
- the golden values in the tests below;
- the speed-test positions' recorded times;
- **step 18k's results** (pull request 72, still open), measured on the old cards.

## Fast checks that failed

Run: the card-data, levels, scouting, teams, rules-register and scenario tests (163 tests, about 2 minutes), and a
short engine agreement check. **155 passed, 8 failed, then 7 after the team sheet was regenerated.**

| Test | Why it fails |
|---|---|
| `test_levels_3l::test_junior_is_the_u16_card_and_matches_the_printed_sheet` | compares the junior cards with the printed U16 sheet (old cards) |
| `test_levels_3l::test_engine_shot_value_and_roll_targets_use_junior_ratings` | a shot value recorded from an old junior card (24, now 21) |
| `test_levels_3l::test_legal_roster_counts` | roster counts recorded with 25 types; the app now has 27 |
| `test_rolls_scoring::test_declared_negative_shot_floors_at_zero` | its set-up relied on a contest larger than the shot; with the lower three contest the shot now scores 9 |
| `test_scouting::test_typical_phrases_are_computed_from_the_cards` | the typical shooting guard now "knocks down the pull-up" |
| `test_scouting::test_golden_reads` | Pace and Space no longer reads "shooters to space the floor" |
| `test_scouting::test_board_advantages_on_the_golden_position` | the golden position's best look moves to another shooter |

None of these points at an engine fault: each compares with a value taken from the old cards.

## Model advice for the refit step

Claude Fable 5.2, effort high. The refit re-measures the maps, the foul price, the set's answers and the goldens on
the new cards: long runs and judgement about which old findings still hold. Re-record the seven tests above in the
same step.
