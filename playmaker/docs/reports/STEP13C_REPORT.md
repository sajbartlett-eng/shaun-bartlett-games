# Step 13C report: cheaper two-action squares, the Contest ruling, a phone speed test

## The speed-ups and their gains, against the speed budget

Three are built, in `engine.js`. Each gives the same choices and values on the 8 step 13 decisions and against the
unchanged Python search (section 3). Times are the 8 decisions at 1 pair ahead (`speed_*.json`).

| Speed-up | Measured in | Before | After | Gain |
|---|---|---|---|---|
| The two-action squares read straight from the paths and the pieces, not from a new position per first square | switch on | 12.50 s | 10.52 s | **1.19 times** |
| A two-action square is skipped when its most can't beat the looks already found | switch on | 10.52 s | 10.76 s | none |
| The squares that block an attacker's way worked out once per pair of squares | default game | 7.45 s | 7.00 s | **1.06 times** |

The two-action squares are now 12% of the search with the switch on, down from 25%.

Against the budget: the 9-in-10 time to finish 1 pair, in seconds (`pairtime_*.json`; phone is 4 times desktop, an
assumed quarter speed).

| Level | Target: desktop, phone | Default game, before | Default game, now | Switch on, before | Switch on, now |
|---|---|---|---|---|---|
| Rookie | 0.3, 1.0 | 0.20, 0.80 | 0.16, 0.65 | 0.28, 1.12 | 0.24, 0.96 |
| Starter | 1.0, 2.0 | 0.50, 1.99 | 0.53, **2.13** | 0.86, 3.43 | 0.78, **3.10** |
| All-Star | 2.5, 3.0 | 0.99, 3.95 | 0.98, **3.92** | 1.88, 7.52 | 1.70, **6.80** |

- **Everything fits a desktop.**
- **The default game on a phone:** the All-Star is still over (noted, not fixed, D-126). The Starter sits on its
  target: 1.99 last time, 2.13 this time.
- **The switch on a phone:** the Rookie now fits. The Starter and the All-Star don't.
- **Not built, because it would change results:** leaving the two-action squares out when the reading re-reads the
  ball handler's looks for a defender stepping into his way. That re-read is where most of the switch's extra time
  now goes. Its effect isn't measured.

## The Contest ruling's effect (D-125)

It changes nothing measurable on these boards (9 of the 30 minutes used).

| | Before the ruling | With the ruling |
|---|---|---|
| Board 16 pair: X2 fresh, against spent | +1.41 | +1.41 |
| Board 12 pair: the help near, against drawn away | +5.98 | +5.98 |
| Board 13 pair: O5 in the lane, against cleared | 0.0 | 0.0 |
| The exam with the switch on: 1 pair, the clock | 9, 10 of 19 | 9, 10 of 19 (the same boards) |
| The exam with the switch off: 1 pair, the clock | 9, 10 of 19 | 9, 10 of 19 |

The averages read under the switch moved by 0.07 at most. On these boards no reading rested on a defender sharing
himself between two shooters he already stood next to.

## How Shaun runs the speed test on his phone

It works from the play link once this pull request is merged and the site has rebuilt.

1. On the phone, open the play link with `?speedtest=1` on the end:
   `https://sajbartlett-eng.github.io/shaun-bartlett-games/playmaker/site/?speedtest=1`
2. Keep the screen on until the bar is full. It takes under 5 minutes.
3. Tap **Copy results** and paste them to us.

On this desktop it ran all 22 decisions in 192 s (`speedtest_desktop.png`). On a slower device it uses the 8 decisions
of boards 2, 7, 9, 10 and 16, and says so on screen.

## 1. Changes to the printed game

None.

## 2. What changed

- **Step 13 merged** (pull request 57). D-125, D-126 and D-127 are recorded.
- **Part 1:** the three speed-ups above. Each can be turned off by a tool, to time and prove it. The Python search
  keeps the plain way and stays the reference.
- **Part 2 (D-125),** inside `eval.coverage_budget` only, in `decide.py` and `engine.js`:
  - a Contest from where a defender stands counts in full on every look he is next to;
  - only answers that need a movement share his budget: a movement in the reaction to one attacker's shot, or one of
    his movement replies in the defence's turn;
  - after a movement reply his Contest is free from the new square, and the free ones from his old square are lost.
- **Part 3:** `playmaker_web/static/speedtest.js`, reached only by `?speedtest=1`. It runs the app's own search in its
  own worker and doesn't load the Python side. The site build writes `speedtest_positions.json` (50 KB) from the
  engine: the 22 decisions and each level's settings.
- **Part 4:** `tools/relative_average.py` takes `--out`. The averages under the switch are measured again and stored.
- **Tools:** `tools/check_speedtest.js` loads the page in a headless browser.

## 3. What it proves

- **The speed-ups change nothing:** JavaScript against the unchanged Python, 0 mismatches on 120 positions and 6 whole
  searches, with the defaults and with the switch on (`js_equivalence_speedups_*.json`). The same choices and values
  on the 8 decisions, default and switch on.
- **D-125 agrees in both engines:** 0 mismatches on 150 positions and 6 whole searches, the shares compared on 146
  (`js_equivalence_d125_budget_on.json`).
- **The defaults give the same results as step 13:** the same root values and choices on the 8 decisions, and the same
  exam boards.
- **The site builds and the page loads** (headless Chrome, desktop): no page errors, the Python loader doesn't start,
  the results and the Copy button appear. The build has the engine, its three data files and the positions.
- **Tests:** `test_rules_current`, `test_static`, `test_step3n`, `test_step3m` and `test_web`: 93 pass, 13 expected
  failures, 1 unexpected pass. The first four give step 13's numbers (78, 13 and 1).
  - One test failed first, and it was right again: my site build loaded the exam module in the same process, which
    the bundle check counts as something the game loads. The positions are now made in a process of their own.
- **The averages (part 4),** 2 of the 20 minutes:
  - **Default game:** Senior Pro moved by +0.12, -0.09, +0.39, -0.11, -0.13 and -0.67 for phases 1 to 6. Across every
    level the move is 0.22 on average and 0.78 at most. All are inside the margin of error (0.92 to 1.52).
  - **Under the switch:** 0.07 at most.

## 4. For Shaun to decide

- **Take the new default averages?** I measured them but didn't store them, because this step's defaults had to give
  step 13's results. Storing them moves default readings by up to 0.78, inside the margin.
  - Option: store them in the next step that changes the reading anyway.
- **The phone targets** wait for your phone's result (D-126).
- **This machine's Chrome is faster than my tool's numbers.** The speed test gave the default All-Star 0.63 s for the
  9-in-10 pair, where the tool, on Node, gives 0.98 s. The budget tables may be too gloomy for a browser. Your phone
  run settles it.

## 5. Noticed, not touched

- **The second speed-up gains nothing.** The looks already found are rarely good enough to rule a square out. It is
  proved and left in, switchable.
- **The dist single-file build** carries the speed test's positions too, 50 KB more.
- **On the local server the speed test can't run** (there is no built engine file). It says so on screen.
- **The exam book** is untouched.

## 6. Model for the next step

Stage 3 (advantages: create, keep and convert) is design work on the reading, with board 13 as its first test:
Claude Fable 5.2, effort high, for the design and both engines. A step that only measures on the bigger exam can run
on Claude Opus 5.5, effort medium.
