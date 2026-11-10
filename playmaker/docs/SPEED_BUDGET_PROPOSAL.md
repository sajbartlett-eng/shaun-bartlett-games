# The speed budget: a proposal (step 13, part A)

Shaun sets the budget. This is the proposal and the measurements behind it. Once set, it becomes
`docs/SPEED_BUDGET.md`, and every later change reports against it (CLAUDE.md, "Tests").

## The proposal

Each level must finish **1 team-turn pair** (its own turn and the reply) on at least 9 decisions in 10, within:

| Level | Look-ahead it must finish | Desktop | Phone |
|---|---|---|---|
| Rookie | 1 pair | 0.3 s | 1.0 s |
| Starter | 1 pair | 1.0 s | 2.0 s |
| All-Star | 1 pair, then as much of a second as the time allows | 2.5 s | 3.0 s |

Why these numbers:

- **1 pair is the look-ahead the exam is marked on** (D-118). A level that doesn't finish the reply plays into
  Contests it could have seen.
- **The desktop times are today's** (`ai_profiles.json`, `time_budget_s`). Every level already finishes 1 pair inside
  them, with room to spare.
- **The phone times are what today's game needs at phone speed, rounded up:** 0.6 s, 1.6 s and 2.7 s for the three
  levels. At the desktop times a phone finishes 1 pair on only 8, 10 and 19 of 22 decisions.
- **2 pairs is out of reach for now.** It takes 30 to 96 s on a desktop (`stability_off.json`), about 30 times the
  All-Star's time. It isn't proposed as a target.

"Phone" means a quarter of this machine's speed, the same assumption as steps 10 and 12. A real phone hasn't been
measured.

## What was measured

All on the JavaScript search (the app's own), on the exam's 22 decisions (boards 1 to 16, every copy, and C2), with one
warm engine, as in a game.

### The time to finish 1 pair, with no limit (seconds on a desktop: median / 9 in 10 / slowest)

| Setting | Rookie | Starter | All-Star |
|---|---|---|---|
| Off (today's game) | 0.10 / 0.16 / 0.28 | 0.28 / 0.41 / 0.53 | 0.48 / 0.67 / 0.93 |
| Cheap (`quiet_points`, `like_with_like`, `tempo`) | 0.63 / 1.93 / 2.06 | 2.88 / 8.03 / 9.66 | 2.39 / 6.26 / 7.48 |
| Cheap with `play_on` | 0.52 / 1.58 / 2.04 | 2.42 / 6.93 / 9.25 | 1.92 / 6.13 / 6.54 |
| Cheap with the reach map | 0.43 / 1.56 / 1.78 | 3.40 / 8.03 / 9.98 | 2.83 / 7.96 / 9.75 |
| Rest: all but `quiet_points` and `clear_reason`, with the reach map | 0.11 / 0.16 / 0.24 | 0.38 / 0.54 / 0.57 | 0.64 / 0.90 / 0.99 |
| Light (`like_with_like`, `tempo`) | 0.08 / 0.13 / 0.19 | 0.29 / 0.39 / 0.43 | 0.45 / 0.65 / 0.74 |

Source: `docs/runs/step13/pairtime_*.json`. Phone time is 4 times these.

### On the clock: decisions that finish 1 pair, of 22 (and the median look-ahead in team turns)

| Setting | Rookie, desktop | Starter, desktop | All-Star, desktop | Rookie, phone | Starter, phone | All-Star, phone |
|---|---|---|---|---|---|---|
| Off | 22 (2) | 22 (2) | 22 (2) | 8 (1) | 10 (1) | 19 (2) |
| Cheap | 7 (1) | 6 (1) | 14 (2) | 1 (1) | 1 (1) | 1 (1) |
| Cheap with `play_on` | 6 (1) | 5 (1) | 13 (2) | 1 (1) | 1 (1) | 1 (1) |
| Cheap with the reach map | 6 (1) | 3 (1) | 9 (1) | 1 (1) | 1 (1) | 1 (1) |

Source: `docs/runs/step13/levels_*.json`. Desktop times used are today's (0.3, 1.0 and 2.5 s); the phone column gives
each a quarter of that on this machine. Every decision used its whole time (median 0.31, 1.01 and 2.51 s), except the
Rookie with everything off, which stops at its 2 team turns after a median 0.09 s.

## What each setting would need to fit

How many times faster its "9 in 10" time must get to meet the proposed target (1.0 or less means it fits now):

| Setting | Rookie: desktop, phone | Starter: desktop, phone | All-Star: desktop, phone |
|---|---|---|---|
| Off | fits (0.5), fits (0.6) | fits (0.4), fits (0.8) | fits (0.3), fits (0.9) |
| Light | fits (0.4), fits (0.5) | fits (0.4), fits (0.8) | fits (0.3), fits (0.9) |
| Rest | fits (0.5), fits (0.6) | fits (0.5), 1.1 | fits (0.4), 1.2 |
| Cheap | 6.4, 7.7 | 8.0, 16 | 2.5, 8.3 |
| Cheap with `play_on` | 5.3, 6.3 | 6.9, 14 | 2.5, 8.2 |
| Cheap with the reach map | 5.2, 6.2 | 8.0, 16 | 3.2, 11 |

- **Everything except `quiet_points` fits,** or comes within 20% on a phone.
- **`quiet_points` is the whole overrun.** It reads 7.5 times as many positions at the same look-ahead
  (`profile_cheap.json`: 35,140 against 4,687). The speed-ups in this step that change no result give it 2%. The two
  that would change results give 1.05 and 1.5 times (STEP13A_REPORT, section 4). It needs 8 to 16 on a phone.
- **To make "rest" fit a phone exactly,** either set the phone targets at 2.2 s (Starter) and 3.6 s (All-Star), or
  take the root window (15 to 19% faster, same choices on 8 of 8 decisions, STEP13A_REPORT section 4).

## Not measured

- A real phone.
- The first decision after the engine loads. On a fresh engine 1 pair takes about twice as long (0.8 to 1.5 s for the
  All-Star with everything off, `stability_off.json`).
- "Rest" and "light" on the clock per level. They have the pair times above, and the exam on the clock (the All-Star).
