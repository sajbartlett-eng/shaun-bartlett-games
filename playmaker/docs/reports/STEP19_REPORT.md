# Step 19: the UX, legibility and accessibility overhaul

**In five lines.**

- **Moving and acting is tap, tap, confirm.** Tap a player: every square he can reach lights up. Tap a square: a ghost. Tap it again, or Confirm. His turn-ending actions sit in a list under the board, each with its chance and one plain reason.
- **Advantages first.** Cards, actions, matchups and Coach Vision speak in the scout report's words ("O2 is dangerous from three, and X2 is slow to close out"). "Show the numbers" brings the ratings back.
- **Every phase is shown turn by turn,** with a line for each team, the coach's assessment at each phase end and at the end of the possession, and a report to download (HTML that prints to PDF, plus the data file).
- **The home screen is four choices and a Start button.** The first game teaches as you play, and Watch the computer plays both sides with play, pause, step and speed, plus a batch of up to 50 possessions.
- **Try first:** Watch the computer, then download a possession's report. Then play one game against the computer on a phone, with "Confirm each action" on and then off.

**Changes to the printed game:** none. Nothing in the engine changed (`git diff` on `playmaker_engine/` since step 18s is empty). Only the app's interface and the server's words moved.

**Branch:** `step-19-ux`, from the step 18s branch (PR 80), which wasn't merged yet. The pull request is open and not merged.

## Before and after (the capture, `tools/ux_capture.js`)

59 to 61 screens, laptop and phone, plus 200% zoom, dark-mode request and forced colours. Every capture's measures are in `docs/runs/step19/` (`compare.md`, and `summary.md` in each folder); the full screenshots are in the zip.

| | Before | After |
|---|---|---|
| Screens with an automated accessibility issue (axe, WCAG 2.2 AA) | 7 of 59 | **0 of 61** |
| Text under 14 px in play (share of characters, 16 in-play screens) | 67% | **27%** |
| Phone table height at tip-off (screen is 846 px) | 1,428 px | **852 px** |
| Words on the "Play the computer" set-up screen | 484 | **148** (34 in the set-up itself) |
| Sideways scroll on any screen, 200% zoom included | none | none |
| Targets under 44 px on a phone (average a screen) | 10.2 | 12.3 (see below) |

Stage by stage (`docs/runs/step19/compare.md`):

| Capture | axe issues | in-play text under 14 px | phone table (px) | set-up words |
|---|---|---|---|---|
| Baseline | 7 | 67% | 1,428 | 484 |
| 1 Moving and acting | 6 | 66% | 1,481 | 484 |
| 2 Advantages first | 5 | 55% | 1,529 | 484 |
| 3 Turn by turn | 5 | 54% | 1,529 | 484 |
| 4 Home screen | 5 | 54% | 1,529 | 133 |
| 5 The first game | 5 | 54% | 1,529 | 152 |
| 6 Watching | 4 | 53% | 1,529 | 152 |
| 7 The rest | 0 | 31% | 848 | 148 |
| Final (the finished branch) | **0** | **27%** | **852** | **148** |

- **A few more small targets on a phone, and why.** The lit squares are 20 px wide on a phone, and there are 15 to 30 of them when a player is selected. Each counts as a small target. Three things cover it:
  - a tap within a finger's reach snaps to the nearest legal square;
  - the ghost and the confirm catch a wrong snap;
  - every square is also a full-size button in "Or pick the square here".
- **The final capture** adds the last fixes after stage 7: 44 px small buttons on a phone, Coach Vision reading both sides, and a hidden table heading for the heading order.
- **The stage 4 capture** is short (41 screens): the old script couldn't open Advanced settings. The script was mended for stage 5 on.

**Text I couldn't get to 12 px.** The court's labels on a phone (the column letters, the zone labels, the numbers on defenders' squares) are 5 to 7 px. The board is 17 squares across a 380 px screen, so each square is 19 px; a 12 px label would cover its square. On a laptop the same labels are now 12 to 15 px.

## Taps and seconds for five common turns (`tools/ux_turns.js`)

Each turn is played in a browser from the same position. Seconds are an estimate from Fitts' law with typical touch values (0.2 s a tap plus 0.15 s for each doubling of distance over target size), plus 1 s for each scroll. They compare layouts; they are not a stopwatch.

| Turn | Before: taps (s) laptop · phone | After, confirm on | After, confirm on, arrow by drag | After, "Confirm each action" off |
|---|---|---|---|---|
| A move | 3 (2.8) · 3 (1.3) | 3 (0.8) · 3 (0.8) | same | **2 (0.6) · 2 (0.6)** |
| A move and a pass | 6 (6.5) · 6 (4.5) | 6 (4.2) · 6 (3.7) | same | **4 (3.8) · 4 (2.9)** |
| A screen | 3 (1.2) · 3 (1.5) | 3 (2.0) · 3 (2.3) | same | **2 (1.8) · 2 (1.7)** |
| A shot | 3 (1.3) · 3 (2.0) | 3 (2.1) · 3 (2.2) | same | **2 (1.8) · 2 (1.6)** |
| A defender's move with a new arrow | 4 (4.1) · 4 (1.9) | 4 (3.3) · 4 (1.9) | **3 (1.2) · 3 (1.3)** | **2 (0.9) · 2 (0.9)** |

- **With the confirm step, taps are the same as before; moves are faster.** Choosing Move, Quick Step or Sprint is gone (each square shows which it takes), and tapping the square again confirms where the finger already is.
- **A screen or a shot is about a second slower,** because the actions list sits under the board and needs a scroll. On a laptop the board alone fills a 900 px window.
- **With "Confirm each action" off, every turn takes fewer taps than before.** Undo still works until a roll, and a roll still asks first. This is decision 1.

## What changed, stage by stage

Before-and-after screens for each stage are in `docs/runs/step19/` (`baseline/` and `stage1/` to `stage7/`).

1. **Moving and acting** (`play.js`).
   - Tap a player and his squares light up: solid for a Move, dashed for a Quick Step, dotted for a Sprint. Tap a square for a ghost with its arrow. Confirm, or tap it again.
   - **The arrow:**
     - drag round the ghost;
     - or the 45° turn buttons;
     - or the arrow keys.

     Only the directions the rules allow.
   - **Turn-ending actions:** listed under the board. Tapping the player again, a double-tap, a hold or A puts their targets on the board. Choose one, then tap it again or Confirm.
   - **Keyboard:** Tab, Enter, arrow keys between squares, Enter, Enter, A, Escape.
   - **Screen readers:** every step is announced ("O1 to J9 by a Move, arrow north. Press Enter to confirm, Escape to cancel").
   - **No page zoom** on the court on a double-tap.
2. **Advantages first** (`advice.py`, `advice.js`).
   - **Every option's chance is the engine's own:**
     - the referee's dice tree;
     - the rules' pass chance (proved equal to the rules' own Intercept in 18s);
     - a shot's value against the best contest now.
   - **The why is one sentence in the scout report's own phrases,** picked by the band on the card. The test checks that the band named is the band on the card.
   - **Cards read as words.** The matchup panel and Coach Vision name the edge both ways: hunt, defence edge, help off.
   - **"Show the numbers"** brings back every "x versus y" line, remembered for each player.
3. **Turn by turn** (`report.py`, `report.js`).
   - **A turn is the offence's turn and the defence's answer:** a diagram and a line for each team.
   - **The lines come from the coverage map** at three moments: before the turn, after the offence, and after the answer. They use the measure ruled in D-201: the offence's best look by the next phase, and who now covers two attackers.
   - **The coach's assessment at each phase end,** for both sides, with what to look for next phase.
   - **At the end of the possession:**
     - the shot (its open value, what the contest took, what was left);
     - the best shot on offer;
     - the trend;
     - the verdict;
     - one thing to keep and one to change for each side.
   - **Download the report** (one HTML file that prints cleanly) and **the data** (JSON with every number and the settings played with), named by game code, possession and date.
4. **The home screen.** Four choices, good defaults, one Start, and a one-line summary of what Start does. Everything else is under Advanced settings, and every option is kept. The defaults, a line each:
   - **a digital match of 4 possessions each:** the app's format, at its shortest;
   - **senior pro, the prescribed teams:** the cards as printed;
   - **the Rookie computer:** its mistakes can be learned from;
   - **Scout level:** you make your own call, then see the report;
   - **you attack first:** you get the ball first;
   - **Watch defaults to two All-Stars:** the computer's best play is what's worth watching;
   - **a scenario card's default is the Rookie computer defending:** a card is a solo drill.
5. **The first game** (`tips.js`).
   - Learn level and the Rookie computer, with a tip at each new idea in your order: tap and move, the arrow, the pass, the colours, the shot, the contest, the screen, the phase and clock, the coverage view.
   - Each tip shows once and can be dismissed. "I know the rules" switches them off.
   - Coach Vision names the clearest advantage from the first possession.
   - The old course is "Rules, step by step" on the home screen.
6. **Watch the computer** (`watch.js`).
   - The setup comes first, as its own step, with a line on what each side planned, from the map. Then every action.
   - **Controls:** play and pause, next turn, slow, normal or fast, the coverage view, the report so far.
   - **The batch** (Advanced settings) plays 1 to 50 possessions unseen. It downloads every report in one file and one data file, with the switches the computer played with.
   - **The server now shows what the link version shows.** The coverage map runs in Node on the server, for the view and the reports only. The computer's search is untouched.
7. **The rest.**
   - **Text:** reading text at least 14 px in play.
   - **Phone layout:**
     - a compact top bar;
     - the side panels are drawers that start closed;
     - Board settings and the player list are folded;
     - the board stays in view while choosing.
   - **The coverage view** turns the zone colours off and shows a legend.
   - **The phase line reads your way:** "The offence's best look fell from 21 to 18: the defence got stronger."
   - **Coach Vision reads both sides in the same form,** whoever is to act ("Offence read: …", "Defence read: …"), as neutrality asks.
   - **Smaller fixes:**
     - the skip link appears only on the table;
     - Escape closes the end screen, and it stays closed;
     - heading order fixed;
     - forced-colours contrast fixed;
     - the handwriting font ships with the app (SIL Open Font License).

## Where I suggested otherwise than asked, and why

- **The actions list shows as soon as a player is selected,** under the board. Waiting for a double-tap cost a tap on every turn-ending action. The double-tap, the hold and A still work: they put the targets on the board.
- **A phone tap snaps to the nearest square, rather than zooming to his reach.** Zooming moves the board under the finger and hides the defence. The snap, the ghost and the confirm catch a wrong tap without either problem.
- **A shot shows its value ("worth 33, Excellent"), not a percentage.** Shots are never rolled, so the value is the engine's own number.
- **"Confirm each action" is a switch** (on by default, as you asked), because with it on no turn takes fewer taps than before. This is decision 1.
- **The batch makes one report file for all its possessions,** not one file each: 50 downloads at once is hard to keep.
- **Watching plays on its own only for a game started from Watch the computer.** Other computer-against-computer games get the same controls, paused. A scenario card has no setup step, because the card sets the board.
- **The first game starts with a setup tip,** because placing your side comes before the first move.
- **The new lines say "no danger from three"** where the scout report says "is no threat from three"; "threat" is on the banned-words list. This is decision 2.

## What it proves

- **Tests: 190 pass, 3 marked as expected failures before this step, 0 fail** (18 minutes). The files run:
  - `test_rules_current`, `test_ux_19` (new), `test_accessibility`, `test_web`, `test_static`;
  - `test_strength_18s`, `test_coverage_18s`, `test_coach_gate`, `test_levels_3l`, `test_step6`, `test_step3n` (the banned-words scan of the interface);
  - `test_scouting`, `test_placement_ui`, and `test_golden_and_regression` (the golden tests).

  axe reports 0 issues on every captured screen. No test was loosened.
- **New tests** in `tests/test_ux_19.py`:
  - every why names the band on the card, and every chance is the engine's (pass, dribble, intercept, challenge, steal, shot value);
  - plain words: one sentence, at most 20 words, no "x versus y", no banned term;
  - the new interface files use plain words;
  - the browser flows: tap and confirm, the fast path, the actions list kept off the board, double-tap, hold, drag and the turn buttons within the allowed arrows, the keyboard path with what it announces, the snap, the numbers switch;
  - the report: turn by turn, its numbers equal to the map's;
  - the home screen, watching (setup, pause, next turn), Escape on the end screen, the report download, and the batch.
- **Changed tests:**
  - four browser scripts (`test_accessibility`, `test_coach_gate`, `test_levels_3l`, `test_static`) open Advanced settings before choosing an option that now sits there;
  - `test_strength_18s` checks the phase line's new words.

  No assertion was loosened.
- **The engine is untouched**, so `tests/test_rules_current.py` and the golden tests run unchanged; the engines' equality isn't affected.

## For Shaun to decide (three)

1. **Confirm each action, on or off by default.**
   - With it on (as you asked), taps match today's.
   - With it off, every turn takes fewer: a move 2 taps instead of 3, a move and a pass 4 instead of 6. Undo still covers a move, and a roll still asks first.
   - **I recommend: off for movement, on for turn-ending actions.** A move can always be undone; a pass or a shot can't. It's a small change; say the word.
2. **The scout phrase "is no threat from three"** uses a banned word. It shows in the scout report as it has since step 3d; the new lines say "no danger from three". **I recommend rewording it in `scout_phrases.json`** ("can't shoot from three" or "no danger from three"), so the report and the new lines match.
3. **The why lines at Pro level.** They show at every level, because the bands they name are on the cards anyway, and the old "x v y" lines showed at Pro too. **I recommend keeping them.** If Pro should be cards only, they can be hidden there.

## Noticed, not touched

- **The defence's setup** still sets each arrow with a list, not the new drag and turn buttons.
- **The batch is slow with two All-Stars:** about a minute or more a possession on the server. Fifty can take most of an hour; use it in the background.
- **The coverage view on the server needs Node.** Without it, the button is hidden with a one-line note.
- **The dark-mode request leaves the page light.** Contrast still passes.

## Model for the next step

Claude Opus 5.5 at high effort. The next step is your playtest feedback on the interface, which is wide but shallow work. Use Claude Fable 5.2 if it turns back to the computer's play.
