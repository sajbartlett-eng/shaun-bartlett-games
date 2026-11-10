# The speed budget

**Provisional** (Shaun, 10 Nov 2026, D-123). The measurements behind it are in `docs/SPEED_BUDGET_PROPOSAL.md`.

Each level must finish **1 team-turn pair** (its own turn and the reply) on at least 9 decisions in 10, within:

| Level | Desktop | Phone |
|---|---|---|
| Rookie | 0.3 s | 1.0 s |
| Starter | 1.0 s | 2.0 s |
| All-Star | 2.5 s | 3.0 s |

- **"Phone" is an assumed quarter of desktop speed.** No real phone has been measured. When one is, these numbers are
  checked again.
- **Desktop** is the machine the measurements run on, with a warm engine, as in a game.
- The All-Star uses what is left of its time on a second pair.

## Measuring a real phone (D-126)

Open the play link with `?speedtest=1` on the end, wait for the bar to fill (under 5 minutes), and tap **Copy
results**. No phone target changes until that result is in.

## How a change reports against it

Every change gives, for each level, on a desktop and at phone speed (CLAUDE.md, "Tests"):

- the time to finish 1 pair: the median, 9 in 10, and the slowest (`python3 tools/exam_13.py pairtime <setting> out.json`);
- the look-ahead it reaches on the clock (`python3 tools/exam_13.py levels <setting> out.json`).

A change that breaks the budget is reported first.

## Where the game stood when this was set

`like_with_like` and the reach map on (D-121), on the exam's 22 decisions. The 9-in-10 time to finish 1 pair, on a
desktop: see the table in `docs/reports/STEP13B_REPORT.md`, which measures the default game against these targets.
