# Playmaker

Playmaker is a two-player basketball board game: one side attacks, the other defends, one possession at a time.
This folder holds its rules engine, the app (hot-seat, remote or against the computer) and the printed game.

## Run it

Python 3.11 or later, standard library only (pytest for the tests). Run everything from this folder (`playmaker/`).

### The server version

```
python -m playmaker_web                 # serves http://localhost:8765 (add --port N to change it)
```

Open the page and pick a path: *Learn the rules*, *Play the computer* (Rookie, Starter or All-Star), *Play a friend*
(hot-seat or remote) or *Scenario cards*. Remote play needs this version. Everything runs on one port, so one tunnel is
enough (`cloudflared tunnel --url http://localhost:8765` or `ngrok http 8765`); send the other player the tunnel URL and
the game code.

### The link version (no install: laptop or phone)

**https://sajbartlett-eng.github.io/shaun-bartlett-games/playmaker/site/**

The same Python engine runs inside the browser (Pyodide from cdn.jsdelivr.net; about 10 MB the first time, cached
after). It plays hot-seat, against the computer, all 16 scenario cards and full matches. Remote play and the
solver-backed review need the server version.

`dist/playmaker.html` is a single self-contained file of the same thing (only Pyodide comes from the CDN), to share or
host anywhere.

How it is published: GitHub Pages serves this repository from `main`. Every push to `main` that touches `playmaker/`
runs the workflow *Build Playmaker playtest site* (`.github/workflows/playmaker-site.yml`). It rebuilds `site/` and
`dist/` and, if they changed, commits them to `main` as "Rebuild the Playmaker playtest site". To rebuild by hand:
`python -m playmaker_web.build_site`.

### Windows, without the link

1. Install Python from **python.org** (Downloads, Windows). In the installer, tick **Add python.exe to PATH**.
2. On the repository page on GitHub: **Code, Download ZIP**. Unzip it.
3. Open the unzipped folder, then the `playmaker` folder inside it. Click the address bar, type `powershell` and press
   Enter.
4. Type `py -m playmaker_web` and press Enter. Open **http://localhost:8765** in your browser.
5. Stop it with Ctrl+C in that window.

### Logs

- **Link version:** in the browser tab only. At the end of a game use **Download log** or **Copy log**. Closing the tab
  without downloading loses it.
- **Server version:** `playtest_logs/<date>_<code>.jsonl`, written as you play.
- Either log replays with `python -m playmaker_engine review <file>.jsonl`.

### The command line

```
python -m playmaker_engine show 6                                   # print scenario 6's board
python -m playmaker_engine play 6 --offence greedy --defence greedy --seed 1
python -m playmaker_engine review playtest_logs/<file>.jsonl        # where the solver disagreed
python -m playmaker_engine timer-stats                              # decision times from the logs
python -m playmaker_engine solve 13 --budget 2                      # solve one scenario card
python -m playmaker_engine test                                     # the test suite (read CLAUDE.md first)
python -m playmaker_engine.register                                 # write docs/rules_register.md
python -m playmaker_engine.register --rules                         # write RULES_CURRENT.md
```

Also: `soak`, `ceilings`, `matchups`, `solve-all` and `rule-health` (`python -m playmaker_engine --help`).

## How the folders are laid out

| Path | What it holds |
|---|---|
| `playmaker_engine/` | The rules engine, the computer opponent, the trainer and the rules register |
| `playmaker_engine/data/` | Cards, teams, scenario cards, court zones, levels, computer profiles, the phase table |
| `playmaker_web/` | The app: the server (`server.py`, `api.py`, `game.py`), the page (`static/`), the link build (`build_site.py`) |
| `site/`, `dist/` | The built link version, written by the workflow. Don't edit by hand |
| `tests/` | The test suite; `tests/data/` holds its fixed inputs, `tests/helpers.py` the helpers moved from retired modules |
| `tools/` | Measurement scripts: exam, timing, accuracy, anchors, self-play seeding, the phase table, JS equivalence |
| `reference/` | The printed game: rulebook, trackers, court, token sheet, cards, scenarios, levels sheet, first game guides |
| `docs/reports/` | One report per step |
| `docs/runs/` | Measured run outputs: `3m/`, `3n/` (with `3n_seed/`) and `solver/` |
| `docs/history/` | Superseded documents, word for word: the old README, the solver report, the PDF step reports |
| `docs/audit/` | The code-audit documents: game logic, computer offence, computer defence |
| `docs/` | Screenshots, the generated `rules_register.md`, the accessibility audit |
| `archive/` | Retired material: old reference PDFs, the old questions list, the old computer and unused modules, their tests |
| `playtest_logs/` | Logs from the server version |

### The engine in brief

| Module | What it does |
|---|---|
| `rules_config.py` | Every number in the rules and every ruling as a setting |
| `board.py`, `geometry.py` | Squares, zones, adjacency, arrows, pass lines, movement shapes, screens |
| `state.py`, `actions.py`, `resolve.py` | The game state, the legal actions, and applying an action with its dice |
| `scoring.py` | Rolls, contests, free throws, bands and the score |
| `scenarios.py`, `cards.py`, `levels.py`, `rosters.py` | Scenario cards, card data, playing levels and roster modes |
| `agent.py`, `search.py`, `decide.py`, `goals.py` | The computer: its search, its plans and its setup |
| `review.py`, `trainer.py`, `glicko2.py`, `labels.py` | Reviewing a game, grading decisions, ratings |
| `register.py` | The rules register, which writes `RULES_CURRENT.md` and `docs/rules_register.md` |
| `exam.py`, `selfplay.py` | The exam and engine self-play, used by `tools/` |
| `solver.py`, `solver_report.py` | The scenario-card solver and its runs |
| `jsbridge.py` | The bridge to the JavaScript port of the search (`playmaker_web/static/engine.js`) |

## Where things live

| What | Where |
|---|---|
| The rules as played | `RULES_CURRENT.md`, generated from the register |
| Every rule value, by format | `docs/rules_register.md`, generated |
| The printed rules | `reference/Playmaker_Rulebook.pdf` and the two trackers |
| Decisions: ruled, awaiting sign-off, open | `DECISIONS.md` |
| The state at the start of the clean-up | `BASELINE.md` |
| Step reports | `docs/reports/`: `STEP1_REPORT.md` onwards, and the earlier step 3m and 3n reports |
| Measured runs | `docs/runs/` |
| Earlier history (steps 1 to 3n) | `docs/history/README_history.md` |

## How a step works

Every change comes as a numbered step. `CLAUDE.md` sets the rules for each one: the sources of truth, what may and may
not change, when tests run, the branch and pull request, and the one-page report in `docs/reports/`. Shaun merges.
