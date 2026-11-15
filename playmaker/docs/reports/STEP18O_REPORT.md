# Step 18o report: the square defender, the setup, help defence, and the test with and without the zone

## In five lines

1. **A square defender takes the jump shot away, as you saw in the NBL game.** With the zone off only 6 of 89
   threes went up over a square, set defender, and never over one whose contest is 4 or more. With the zone on,
   none in 79. Faced with one, the ball handler moves first. Built in both engines, on in the app.
2. **The setup: built as you ordered, and switched off, because it plays worse.** It gives up 6.8 more points a
   possession than the old setup (2.8 to 10.7). The engine has no reading that can judge a setup: it reads every
   off-ball arrow exactly the same. So the setup does not yet fit the players. This is flagged below.
3. **Help defence: on your board it did not play out best.** After the point guard beats X1, X4 and X5 next to the
   post scorers give up 18.3 (11.9 to 24.7); in the lane they give up 27.0 (23.0 to 31.0). But in the test 52 of 56
   drives finished inside met no square defender, and the computer's offence does not drive the lane as you did.
4. **Check 4 is confirmed: with the zone off, a defender whose arrow is on the ball handler can't wall his drive.**
   So arm A can't be compared with real basketball on drives. Arm B is the comparison that counts.
5. **Against real FIBA basketball (about 1.0 a possession):** arm A scores 1.20 (1.13 to 1.27), arm B 1.09 (1.01 to
   1.17). 18n was 1.28. Fouls at the rim are 0 in both: the block was never tried. Compute: 11.8
   core-hours of the 14 allowed.

## Stopped and flagged: the setup, as ordered, plays worse

This is the part of the step that is not done the way the prompt asked, so it comes before anything else.

- **I built the setup you ordered** (D-195): both sides, every level, and the proposal shown to a human. It starts
  from no placement, can put any player on any square with any arrow, shortlists by the quick reading, and judges
  the shortlist by the search's own played-out reading. It keeps to the setup's time at every level (Part 5).
- **Played out, it is clearly worse.** The same 48 deals, All-Star against All-Star, the same dice:

  | The setup | Points a possession | Against the old setup, deal by deal |
  |---|---|---|
  | As it was (the stored starts every step has played from) | 22.2 (18.8 to 25.6) | |
  | Each defender simply next to his man, against the old offence | 22.1 (18.6 to 25.6) | 0.1 lower (4.0 lower to 3.8 higher) |
  | The search, both sides | 29.0 (27.2 to 30.7) | **6.8 higher (2.8 to 10.7)** |

- **So I left it switched off** (`setup.search` in `ai_profiles.json`; `?setup=search` in the address plays it).
  The played-out answer decides (D-156), and new things ship off until you turn them on (principle 10).
- **Why it fails: the engine has no reading that can judge a setup.** Three facts, all measured on your board:
  - Your game's defence and the search's first pick play 7 points apart. One turn ahead the search reads them 0.2
    apart; two turns ahead it reads them the same.
  - The quick reading ranks them backwards: it rates four defenders packed round the lane best, and that
    placement played worst (29.1 against 22.2 for your game's defence).
  - **Every arrow of every off-ball defender reads exactly the same** (25.17 for all eight directions, all four
    defenders). The search can't tell an arrow on a man from an arrow on a passing lane.
- **What that means for your two questions.**
  - *Why do the arrows hug their men?* Not because the reading prefers it. The reading has no preference at all.
    They hug because the old setup starts each arrow on its man and only ever tries two directions: at the
    nearest attacker and at the ball handler.
  - *Why did X4 and X5 stand next to non-shooters?* The same cause: the old setup starts every defender next to his
    man and moves him only where the quick reading says another square near an attacker is better.
- **What it costs to do it properly:** a real play-out takes about 25 core-seconds, and it takes about 50 for each
  of two placements to tell them 5 points apart. That is about 40 core-minutes for one comparison, against a setup
  time of 0.1 to 1.0 seconds. No form of "judged by play" fits inside the setup's time. Decision 1 at the end is
  about this.

## Part 0: merged, ruled, and the cards

- **Merged:** step 18n (pull request 75). Branch `step-18o-square-setup`.
- **`DECISIONS.md`:** D-194 (the square defender, with the two things not taken from 18n and the open case that
  stands) and D-195 (the setup must fit the players, as you ruled it). D-192 is marked as replaced.
- **The cards:** the mid-range, long two and three contests are back at your original values on all 81 cards, with
  their first ranges and chart fixes. A test checks all seven contests on every card against the cards before D-184,
  and that no other defence rating differs from them. Level files and the team sheet are regenerated.
- **The rule, in both engines:** one contest table for every shot. Square (in front, his arrow on the shooter): the
  full rating. In front with the arrow off, or beside: 3 less. Behind: 6 less. Rushed: 2 more off. Never under 1.
  Jump shots have no Contest move and no foul. Inside shots keep the block for a defender who isn't square.
- **In the app:** the shot's explanation now says where the defender stood, for example "X1 was square in front of
  O1, so the three was contested (25% off)" or "X1 was in front of O1 with his arrow off him". The help line and
  the rules text carry the new sentence.
- **The two engines agree** on every check: 150 positions and 8 searches; 200 shot reactions; 100 positions and 4
  searches with the zone on; 60 with a broken zone; 40 with the three search switches on; 60 with the position rule
  off; and 30 the way Starter and Rookie settle a shot. No differences.

## Part 2: the sense checks on your board

Your board, built on today's cards: the offence on I11 (ball), C9, O9, A3, Q3. O4 and O5 are the Post Scorer Power
Forward and Post Scorer Centre, A tier. The other eight cards come from the coherent deal that holds those two
(SPC-0002L3): a C-tier Defensive Point Guard with the ball, a Sharpshooter and a Bucket Getter on the wings. Every
candidate got 16 play-outs, All-Star against All-Star, the same dice.

**Read every number below with its range.** 16 play-outs leave about 6 points either way, so only gaps of about 8
points or more are clear.

**The sense checks were played before the refit,** on step 18n's maps. The refit moved the All-Star's map little
(about 1 to 1.7 points lower in the first three phases), so I did not replay them.

### Check 4 first: the straight drive, from the code

**Confirmed, with one correction.** With `rules.zone` off:

- **An arrow on the ball handler stops nothing.** A defender's arrow bars the squares along it up to the first
  player in the way. Pointed at the man next to him, that first player is the ball handler, so it bars no square.
  X1 on J10 facing O1, as in your game: O1 can reach 36 squares in one movement and Sprint straight down to I6.
- **X1 square on I10 only moves the drive one square sideways.** His body is in the way; his arrow still bars
  nothing. O1 Sprints to E7 or M7 instead.
- **The correction: an arrow across his path does wall him.** X1 on J10 facing W (or on H10 facing E) bars the row
  in front of O1. O1 then reaches 27 squares and gets no nearer than 8 from the rim in one movement, against 4.
  The price is that X1 is not square, so he contests O1's three 3 lower.
- So with the zone off the defence must choose: square to the shot, or a wall against the drive. One defender
  can't do both.

With `rules.zone` on (two arrows):

- X1 on J10 facing O1, as in your game, still doesn't wall him: his second arrow points away from the lane.
- X1 on H10 facing O1 does: his second arrow runs across the lane. So does J10 facing W, which under the zone is
  also an arrow on O1. Under the zone a defender can be square and a wall at once, on one side.

**Played out,** with O1 made to take his straight drive first:

| X1 stands | Zone off | Zone on |
|---|---|---|
| J10, arrow on O1 (your game) | 22.3 (15.5 to 29.1) | 20.4 (14.3 to 26.5) |
| I10, arrow on O1 (square) | 21.2 (14.9 to 27.4) | 16.3 (8.9 to 23.7) |
| J10 facing W (the wall) | 24.8 (19.7 to 29.8) | 19.8 (12.9 to 26.6) |
| Where the search rates him best: J11, beside O1, facing E | 25.2 (20.2 to 30.3) | 26.4 (22.4 to 30.4) |

- **No placement of X1 is clearly better than another with the zone off.** The drive from your game's setup scores
  22.3, the same as the offence's own choice from that setup (22.2).
- **The search's favourite square for X1 plays worst,** and with the zone on it is nearly clear of the square
  defender (26.4 against 16.3). The search reads J11 as 6 points better for the defence than any other square
  (18.8 against 24.2 to 25.8). That is a fault in the search's reading, reported and not fixed.

### Checks 1 and 3: your board at setup

| The defence | Zone off | Zone on |
|---|---|---|
| As in your game: X4 and X5 next to O4 and O5, arrows on | 22.2 (16.7 to 27.8) | 18.0 (10.7 to 25.3) |
| The same, X1 square on I10 | 21.2 (14.9 to 27.5) | 17.5 (11.5 to 23.5) |
| X1 square, X4 and X5 in the lane (H5, J5) | 22.8 (18.3 to 27.4) | 21.2 (15.4 to 27.0) |
| Your game, off-ball arrows turned along the passing lanes | 24.9 (18.5 to 31.3) | 18.8 (11.3 to 26.2) |
| The search's first pick (J10, E4, K7, M6, D4: packed round the lane) | **29.1 (27.3 to 30.8)** | 19.9 (13.7 to 26.2) |
| The search's second pick (L7, D3, N3, I10, I5) | 24.7 (19.7 to 29.7) | not played |
| The search at Starter (H12, N5, I7, F2, N3) | 26.1 (24.5 to 27.7) | not played |

- **Your game's defence is level with the best of them.** Nothing plays out clearly better than X4 and X5 next to
  the two post scorers.
- **Help in the lane is no better at setup:** 22.8 against 21.2 with the zone off, 21.2 against 17.5 with it on.
- **Arrows along the passing lanes are no better than arrows on men** (24.9 against 22.2; 18.8 against 18.0).
  I chose those arrows myself, because the search rates every arrow level and so names none to try.
- **The search's own first pick is the one clear loser** with the zone off.

### Checks 2 and 3: after the point guard beats X1

The same board after O1 wins his Dribble against X1. The defence answers as it chooses.

| X4 and X5 stand | Zone off | Zone on |
|---|---|---|
| Next to their men, as in your game | 18.3 (11.9 to 24.7) | 18.9 (11.3 to 26.6) |
| In the lane (H5, J5), facing the ball | **27.0 (23.0 to 31.0)** | 22.9 (18.4 to 27.5) |
| Where the search put them (M6, D4) | 22.8 (17.0 to 28.5) | 21.6 (16.3 to 27.0) |

- **Next to their men plays out better than in the lane,** nearly clear with the zone off. With X4 and X5 in the
  lane the offence got 7 inside shots, against 2, and lost the ball once, against 5 times.
- **What the defence did next** (X4 and X5 next to their men): the beaten X1 reached for a Steal 16 times in 16. X4
  and X5 stepped into the key 0 times in 16.
- **What the offence did next: it did not drive.** O1 stepped one square to the side 12 times in 16. So I played
  the drive itself, after X1's reach misses:

| X4 and X5 stand | The offence plays on as it chooses | O1 takes his straight drive |
|---|---|---|
| Next to their men | 26.9 (25.1 to 28.6) | 20.2 (14.3 to 26.2) |
| In the lane | 25.4 (22.7 to 28.1) | 24.3 (19.3 to 29.3) |

- **The straight drive is not the offence's best line.** What the computer chose scored more, with X4 and X5 next
  to their men (26.9 against 20.2, nearly clear).
- **Once X1's reach has missed, the lane is level with next to their men** (25.4 against 26.9).

### What the sense checks say about help defence

- **On your board, help positions did not play out best.** So there is no search fault to report of the kind you
  asked about ("help plays out best and the computer doesn't choose it").
- **But your picture of it is right in one way.** Across every placement, an inside finish almost never met a
  square defender: 1 of 11, 0 of 11, 3 of 11. The defence doesn't get square to a finisher, wherever it starts.
- **And the computer's offence is not the offence you played.** It doesn't drive the open lane after a beat; you
  did. These checks measure the defence against the computer's offence, not against yours.
- **Three faults in the search's reading turned up,** all reported, none fixed:
  1. It reads every off-ball arrow the same.
  2. It reads X1 beside the ball handler as far better than in front of him; play says the reverse.
  3. Its quick reading rates the packed lane best at the start; play rates it worst.

## Part 3: the refit

Each level's own self-play on today's cards and rules, as in 18h. The setup is the old one (the search is off), so
the starts are the stored ones every step has played from, rebuilt on today's cards.

| | Possessions | Positions | Lines of its own | Points a possession | As real points |
|---|---|---|---|---|---|
| All-Star | 200 | 4,178 | phases 1 to 4 both sides, 5 on offence | 24.1 (22.6 to 25.6) | 1.21 |
| Starter | 90 | 1,032 | phases 1 and 2 | 21.8 (19.9 to 23.7) | 1.09 |
| Rookie | 120 | 1,193 | phases 1 and 2 | 20.5 (19.0 to 22.1) | 1.03 |

- **Every line slopes the right way.**
- **The All-Star's map moved down** by about 1 to 1.7 points in the first three phases.
- **The Rookie scores more than in 18n** (1.03 against 0.89). I did not test why. The likely cause: its defenders
  are seldom square, and a defender who isn't square now takes 3 less off a jump shot.
- **The foul-price numbers,** from the All-Star's run: 0.33 fouls a possession (0.24 to 0.42) and 24.1 a possession
  (22.6 to 25.6). They were 0.22 and 25.8.
- **Golden values re-recorded, each with the reason "D-194" in the test:** the two ceilings in
  `test_golden_and_regression.py`, seven tests that held a contest value or a scouting read built on one, and one
  trainer board in `test_step3m.py`. The 18n card-table test now checks the cards against your originals.

**The sense-check set.** The rule can move almost every position in it, because almost every one turns on a shot's
contest. I replayed the ones where a jump shot's contest decides, and your game:

| Position | Best by play | The computer |
|---|---|---|
| Closeout, the shooter cannot move | X3 Quick Steps next to him: 8.0 (2.4 to 13.7) | **Pauses: 27.9 (26.7 to 29.2). 19.9 behind (13.9 to 25.9)** |
| The same, your order (X3 Quick Steps, X2 to B6) | | 12.9 (5.2 to 20.6): level with the best |
| Closeout, the shooter can move | every turn level, 27 to 30 | Pauses: level |
| Closeout, step 2 | X3 Moves next to him, then a Steal: 16.0 (9.6 to 22.5) | the same turn |
| Game EB3F5B | see below | level |

- **A clear miss, and new.** On the first closeout position the All-Star now does nothing, and it costs about 20
  points. In 18n every turn there was level. Stepping next to a shooter who can't move wins the ball 9 times in
  16 now; the search doesn't see that. I report it and did not fix it. It is the same blind spot as the setup's:
  the reading doesn't count what standing next to a ball handler is worth.
- **Not replayed, 29 of the 33 positions:** the two Steal positions, "Contest or not" 1 to 4, "before an open
  shot" 1 to 3, "shoot now or play on" 1 to 4, "move, then shoot" 1 and 2, boards 1, 3, 8 and 9, and "two turns
  before an open shot" 1 to 10. Their answers on file are step 18n's.

## Part 4: the test, in two arms

All-Star against All-Star, 200 possessions each, the final default. **Arm A:** `rules.zone` off. **Arm B:**
`rules.zone` on. Arm B plays on the All-Star's own map: the engine holds no separate map for the zone, and its play
did not differ enough to need one built (possessions of the same length and shape). A map and a second run of
the arm would have cost about 2.5 core-hours more.

**The setup in both arms is the old one,** because the search is off. So the tables below show the old setup's
squares, not a setup that fits the players.

**The game rolls no make or miss.** It scores a shot by its chance: rating less contest, in 20. "Made" in a cell is
that chance added up.

**Arm A (zone off): every three, shooter against the contest that counted.** Each cell: taken (made).

| The shooter's open three | Open | Contest 1 | Contest 2 | Contest 3 | All |
|---|---|---|---|---|---|
| 11 | 3 (1.4) | 1 (0.5) |  | 3 (1.2) | 7 (3.1) |
| 10 | 7 (3.4) | 10 (4.5) | 3 (1.2) |  | 20 (9.1) |
| 9 | 28 (12.6) | 12 (4.8) |  | 1 (0.2) | 41 (17.6) |
| 8 | 18 (7.2) |  |  |  | 18 (7.2) |
| 7 | 3 (1.0) |  |  |  | 3 (1.0) |
| **All** | 59 (25.6) | 23 (9.8) | 3 (1.2) | 4 (1.4) | 89 (38.0) |

- **Arm A (zone off), mid-range shots:** 1 taken: open rating 10: open 1 (0.5).
- **Arm A (zone off), long twos:** 0 taken.

**Arm B (zone on): every three, shooter against the contest that counted.** Each cell: taken (made).

| The shooter's open three | Open | Contest 1 | Contest 2 | All |
|---|---|---|---|---|
| 11 | 1 (0.6) | 2 (1.0) | 1 (0.5) | 4 (2.1) |
| 10 | 5 (2.5) | 10 (4.5) | 1 (0.4) | 16 (7.4) |
| 9 | 25 (11.2) | 15 (6.0) | 1 (0.3) | 41 (17.5) |
| 8 | 13 (5.2) | 2 (0.7) |  | 15 (5.9) |
| 7 | 1 (0.3) | 1 (0.3) |  | 2 (0.6) |
| 6 | 1 (0.3) |  |  | 1 (0.3) |
| **All** | 46 (20.1) | 30 (12.5) | 3 (1.2) | 79 (33.8) |

- **Arm B (zone on), mid-range shots:** 0 taken.
- **Arm B (zone on), long twos:** 0 taken.

**Contested threes, by where the defender stood.** Taken, and points a shot.

| The defender | Arm A (zone off) | Arm B (zone on) |
|---|---|---|
| Square in front, set | 6, 1.1 a shot | 0 |
| Square in front, rushed | 3, 1.3 a shot | 12, 1.24 a shot |
| Not square (in front with his arrow off, or beside) | 17, 1.27 a shot | 17, 1.23 a shot |
| Behind | 4, 1.28 a shot | 4, 1.35 a shot |
| Nobody: open | 59, 1.31 a shot | 46, 1.31 a shot |

**Threes by the shooter's open rating.** Taken, contested, and over a square defender.

| Open three | Arm A (zone off) | Arm B (zone on) |
|---|---|---|
| 11 | 7 taken, 4 contested, 3 over a square defender | 4 taken, 3 contested, 1 over a square defender |
| 10 | 20 taken, 13 contested, 5 over a square defender | 16 taken, 11 contested, 4 over a square defender |
| 9 | 41 taken, 13 contested, 1 over a square defender | 41 taken, 16 contested, 6 over a square defender |
| 8 | 18 taken, 0 contested, 0 over a square defender | 15 taken, 2 contested, 1 over a square defender |
| 7 | 3 taken, 0 contested, 0 over a square defender | 2 taken, 1 contested, 0 over a square defender |
| 6 | 0 | 1 taken, 0 contested, 0 over a square defender |

**Faced with a square, set defender on a jump-shot square, at the start of his turn.**

| | Arm A (zone off) | Arm B (zone on) |
|---|---|---|
| Turns it happened, in 200 possessions | 13 | 22 |
| First: Dribble at him | 1 | 5 |
| First: Move away | 3 | 10 |
| First: Quick Step away | 5 | 3 |
| First: Sprint away | 1 | 1 |
| First: passed | 2 | 2 |
| First: waited, or only others moved | 1 | 1 |
| His Dribble at him: tried, won | 1, 1 | 5, 3 |
| After his move: no square defender on him | 4 | 13 |
| After his move: a square defender, but rushed | 3 | 3 |
| After his move: still square and set | 0 | 0 |
| After his move: he gave the ball up | 3 | 1 |
| After his move: the ball was lost | 0 | 2 |

**Inside shots, by where the defender stood.** Shots, the makes the cards give, the block tried, fouls.

| The defender | Arm A (zone off) | Arm B (zone on) |
|---|---|---|
| Square in front, set | 4 shots, 2.3 made (57 in 100), block 0, fouls 0 | 5 shots, 2.8 made (56 in 100), block 0, fouls 0 |
| Square in front, rushed | 8 shots, 5.0 made (62 in 100), block 0, fouls 0 | 7 shots, 4.0 made (57 in 100), block 0, fouls 0 |
| Not square | 13 shots, 9.5 made (73 in 100), block 0, fouls 0 | 9 shots, 6.1 made (68 in 100), block 0, fouls 0 |
| Behind | 43 shots, 32.0 made (74 in 100), block 0, fouls 0 | 45 shots, 32.8 made (73 in 100), block 0, fouls 0 |
| Nobody: open | 15 shots, 12.8 made (85 in 100), block 0, fouls 0 | 12 shots, 10.7 made (89 in 100), block 0, fouls 0 |
| **All** | 83 shots, 61.5 made (74 in 100), block 0, fouls 0 | 78 shots, 56.4 made (72 in 100), block 0, fouls 0 |

**The block, by the defender's Contest foul rating** (inside shots where he wasn't square, so he could go for it): could, tried, fouled.

| Contest foul rating | Arm A (zone off) | Arm B (zone on) |
|---|---|---|
| 5 | 3, 0, 0 | 0 |
| 6 | 2, 0, 0 | 5, 0, 0 |
| 7 | 6, 0, 0 | 14, 0, 0 |
| 8 | 9, 0, 0 | 10, 0, 0 |
| 9 | 17, 0, 0 | 15, 0, 0 |
| 10 | 5, 0, 0 | 3, 0, 0 |
| 11 | 7, 0, 0 | 3, 0, 0 |
| 12 | 7, 0, 0 | 4, 0, 0 |

**Help: drives that reached the key and finished inside.**

| At the finish | Arm A (zone off) | Arm B (zone on) |
|---|---|---|
| Drives finished inside | 56 | 47 |
| No defender square in front | 52 | 42 |
| Only his own defender square in front | 2 | 1 |
| Another defender square in front (help) | 2 | 4 |

**Where the defenders of non-shooters started** (a non-shooter: his three is below average on his card; the starts are the same in both arms): of 415, 365 next to their man, 2 in the key, 48 elsewhere.

**Setup: where each type started, on offence.**

| Type | Beyond the line | The three-point line | Long two | Mid-range | The key |
|---|---|---|---|---|---|
| Point Guard | 200 | 0 | 0 | 0 | 0 |
| Shooting Guard | 12 | 129 | 23 | 27 | 9 |
| Small Forward | 20 | 121 | 29 | 25 | 5 |
| Power Forward | 24 | 115 | 31 | 22 | 8 |
| Centre | 12 | 121 | 27 | 31 | 9 |

**Setup: where each type started, on defence.**

| Type | Next to his man | In the key | Elsewhere |
|---|---|---|---|
| Point Guard | 190 | 4 | 6 |
| Shooting Guard | 165 | 2 | 33 |
| Small Forward | 178 | 0 | 22 |
| Power Forward | 165 | 0 | 35 |
| Centre | 168 | 2 | 30 |

**Arrows off the ball, at every defence turn.**

| The off-ball defender's arrow pointed | Arm A (zone off) | Arm B (zone on) |
|---|---|---|
| At his man | 1014 (37 in 100) | 1034 (39 in 100) |
| At the ball handler | 142 (5 in 100) | 145 (5 in 100) |
| Along a passing lane | 446 (16 in 100) | 407 (15 in 100) |
| Toward the rim | 7 (0 in 100) | 7 (0 in 100) |
| Somewhere else | 1167 (42 in 100) | 1087 (41 in 100) |
| Passes thrown | 273 | 226 |
| Intercepts tried | 0 | 2 |
| Intercepts won | 0 | 1 |

**What the tables say.**

- **A square, set defender takes the three away.** With the zone off 6 of 89 threes went up over one, and never
  over one whose contest is 4 or more. With the zone on, none in 79. In 18n, 13 of 90 went up over a set defender
  in front.
- **Faced with one, the ball handler moves first.** 22 turns with the zone on: 14 moved away, 5 went at him with a
  Dribble (3 won), 2 passed. After the move he was never still facing a square, set defender: free 13 times, facing
  a rushed one 3 times.
- **But it is rare.** A ball handler on a jump-shot square started his turn facing a square, set defender 13 times
  in 200 possessions (zone off) and 22 times (zone on). The defence is seldom square to begin with.
- **Contested threes still go to the good shooters:** shooters rated 8 or less took 21 threes with the zone off,
  none contested.
- **Possessions got shorter:** 19 decisions each, from 28 in 18n. 8 shots in 10 now come in the first two phases.
- **The inside shot is still the generous part:** 74 makes in 100 (zone off), 72 (zone on). Only a square defender
  brings it down, to about 56 to 62.
- **The block was never tried:** 0 times in 56 chances (zone off) and 54 (zone on), whatever the defender's Contest
  foul rating. No shooting foul was called in either arm.
- **Help:** of 56 drives that finished inside, 52 met no square defender (zone off); 42 of 47 (zone on). A second
  defender got square in front 2 times and 4 times.
- **Arrows off the ball:** on his man 4 times in 10, along a passing lane about 1 in 6. No Intercept was tried with
  the zone off in 273 passes; 2 with it on, 1 won.
- **The old setup does not fit the players, as you said.** Centres started on the three-point line 121 times in
  200 and in the key 9 times. The defenders of non-shooters started next to their man 365 times in 415 and in the
  key twice.

### Beside FIBA

| Measure | Real FIBA | Arm A (zone off) | Arm B (zone on) | 18n |
|---|---|---|---|---|
| Points a possession | about 0.95 to 1.0 | **1.20** (1.13 to 1.27) | **1.09** (1.01 to 1.17) | 1.28 |
| Shooting fouls at the rim, in 100 rim shots | about 20 to 30 | 0 of 71 (0 to 5) | 0 of 60 (0 to 6) | 0 |
| Blocks, in 100 twos | about 6 | 0 of 84: the block was never tried | 0 of 78 | 0 |
| Turnovers a possession | about 0.15 | 0.13 (0.08 to 0.18) | 0.21 (0.14 to 0.27) | 0.09 |
| Steals tried a possession | report | 0.51 (0.41 to 0.61) | 0.80 (0.67 to 0.92) | 0.47 |
| Steal fouls a possession | report | 0.24 (0.17 to 0.30) | 0.33 (0.25 to 0.41) | 0.20 |
| Shots: threes, rim shots, other twos | report | 89, 71, 13 | 79, 60, 18 | 90, 78, 14 |
| Shots contested, in 100 | | 57 (49 to 64) | 63 (55 to 70) | 55 |
| Threes contested, in 100 | | 34 (25 to 44) | 42 (32 to 53) | 41 |

- **Arm B is the nearer of the two to real basketball on scoring,** and it is the one that counts on drives (check
  4). It is still above the band.
- **Turnovers are now in the band** with the zone off, and a little over it with the zone on. All were reaches,
  but for one Intercept and one three-second call in arm B.
- **The zone brings more reaching:** steals tried rise from 51 to 80 in 100 possessions, steal fouls from 24 to 33.
- **Fouls at the rim and blocks are the two measures furthest from real basketball,** as in 18n. Both are 0.
- Nothing was changed to move any of these numbers.

### Your game EB3F5B

The pass to O4 in the corner is in the air; what the defence does now. 16 play-outs each.

| The defence | Arm A (zone off) | Arm B (zone on) |
|---|---|---|
| Pauses (what happened in your game) | 22.2 (18.7 to 25.7) | 21.0 (16.5 to 25.5) |
| X4 Moves to C4, facing him | 24.5 (22.4 to 26.6) | 26.8 (22.8 to 30.7) |
| X4 Quick Steps to E4 | 27.0 (the same every time) | 27.0 (the same every time) |
| The computer's choice | X2 moves to B7: 25.3 (24.0 to 26.6) | X4 Sprints to B4, then reaches: 18.4 (11.1 to 25.8) |

- **What the defence does now:** with the zone off it moves X2 to B7, as in 18n. That is 3.1 behind pausing (0.3
  ahead to 6.6 behind): level. With the zone on it Sprints X4 to the catcher and reaches for the ball, which is
  the best of the four and wins the ball 6 times in 16.
- **Rushing out to him is the worst of them, every time.** X4's Quick Step to E4 leaves him rushed and not square,
  so O4's three goes up at once for 27. Under D-194 a closeout only pays if he arrives set and square.
- **Pausing, as in your game, is level with the best in both arms.**

## Part 5: speed

**Play.** The time to finish 1 pair on 9 decisions in 10, in seconds, two rounds, 18n's code timed in turn with
this step's on a quiet machine.

| Level | Target | 18n's code | This step | This step, zone on (one round) |
|---|---|---|---|---|
| Rookie | 0.3 | 0.23, 0.24 | 0.24, 0.28 | 0.30 |
| Starter | 1.0 | 0.76, 0.77 | 0.82, 0.81 | 0.92 |
| All-Star | 2.5 | 1.76, 1.88 | 2.03, 1.88 | 2.25 |

- **Every level fits its target.**
- **This step is a little slower than 18n's code:** about 6 in 100 at Starter, and on the All-Star's middle
  decision 1.5 to 1.6 seconds against 1.3 to 1.4. The search itself did not change; the cards, the contest rule and
  the maps did, and they change how many turns it weighs.
- **With the zone on there is little room:** the Rookie is at its target.

**Setup.** Seconds a side, over 12 deals, against the setup's time (0.4 of a decision's).

| Level | Its time | The search (off): offence, defence | The old setup (the default): offence, defence |
|---|---|---|---|
| Rookie | 0.12 | 0.13, 0.14 | **1.4, 2.3** |
| Starter | 0.4 | 0.36, 0.37 | **1.3, 2.7** |
| All-Star | 1.0 | 0.77, 0.81 | **3.7, 2.6** |

- **The search keeps its time** (the Rookie's is over by 0.01 to 0.03 seconds: it finishes the reading it has begun).
- **The old setup runs far over its time, and did before this step.** It only looks at the clock between one
  defender and the next, and one defender's sweep is 28 readings in the slow engine. On this machine a possession
  waits 4 to 6 seconds for the two setups; in a browser it will be longer. I did not change it: making it keep
  its time changes where the computer sets up, and that belongs with decision 1.

## What it proves

- **The two engines agree** on the rule (Part 0).
- **The cards:** all seven contests on every card match your originals, by a test. No other rating changed.
- **Tests:** `tests/test_rules_current.py` passes. The 29 named test files: 477 passed and 1 failed, the
  timing test (2.4 seconds on one decision against a limit of 1.7), as since 18f. Not loosened. `tests/test_static.py`,
  run on its own: 11 passed. 14 tests are marked as known failures, the same ones as before.
- **The site tests caught a fault of mine.** My first build of the new engine call broke the browser version's
  start-up line. Fixed, and the 11 site tests pass.
- **One more file, `tests/test_computer.py`,** which tests the setup code I changed: 2 passed, 1 failed. That one
  replays a stored game from before D-184 and already fails on 18n's code. Not touched.
- **The exam at the All-Star:** as in 18n. Position 1 passes; 2, 3, 5, 6, 8, 9, 11, 13, 14 and 16 are listed open.
- **What it does not prove:**
  - Anything about a human's play. Every play-out is the computer against itself.
  - Help defence in general. The sense checks are one board, 16 play-outs a candidate.
  - Starter and Rookie against FIBA: the arms are the All-Star's.

## Compute

| | Core-hours |
|---|---|
| Sense checks on your board (9 groups of play-outs, and the search's own readings) | 4.0 |
| The test: arm A and arm B | 2.2 |
| The refit: self-play at three levels | 1.9 |
| Tests, on one core | 1.0 |
| The setup: the same 48 deals set up three ways and played out | 0.9 |
| The set's closeout positions and game EB3F5B in each arm | 0.8 |
| Agreement checks of the two engines, on one core | 0.4 |
| A preparation run stopped after 18 minutes (the slow engine under the zone) | 0.3 |
| Speed and setup time | 0.2 |
| **Total, as tallied** | **11.8** |

- **The estimate was 12.5 and the hard stop 14.**
- **About 0.9 of the 11.8 is time counted twice.** Twice I let two runs share the four cores, and the tally counts
  each run's own clock. The All-Star's refit run used 1.27 core-hours by its processor time and is tallied at
  1.73. The true total is about 10.9.
- **More than planned:** the sense checks (4.0 against 2.7), because I added the drive after the beat and the
  arrows check. **Less than planned:** the two arms (2.2 against 3.7), because possessions are a third shorter now.
- The line by line tally is at the foot of `docs/runs/step18o/PREDICTIONS.md`.

## Noticed, not touched

- **Three faults in the search's reading** (Part 2). Each is a reason the computer's defence stands where it does.
  1. Every off-ball arrow reads the same, so nothing in the search turns an arrow onto a passing lane.
  2. X1 beside the ball handler reads 6 points better than in front of him. Play says the reverse.
  3. The quick reading rates a packed lane best at the start. Play rates it worst.
- **With the zone on, the app plays on the slow engine.** The bridge between the two engines only passes a game to
  the fast one when every rule is at its usual setting, and `rules.zone` on is not. So `?zone=1` in the app thinks
  on the Python engine, many times slower. The fast engine does play the zone, and the two agree. It is a
  one-line change, left for you because it changes what the app does under a switch you own.
- **The computer's offence does not drive the lane after it beats its man.** It steps to the side 12 times in 16.
  By play that was the better choice against the computer's own defence (Part 2), so it is not a fault I can
  show. It is the main way its offence differs from yours.
- **The defence is seldom square.** A ball handler on a jump-shot square starts his turn facing a square, set
  defender about once in 9 to 15 possessions. D-194 rewards being square, and the search has not learned to be.
- **The All-Star no longer closes out on a shooter who can't move** (Part 3, the set). It pauses and gives up
  about 20 points more than stepping next to him. In 18n the turns there were level.
- **No mid-range shot or long two is taken** (1 in 400 possessions), and no dunk.
- **The timing test still fails** as it has since 18f. Not loosened.
- **Predictions.** Jump shots: right that fewer go up over a set defender in front (13 to 6); wrong that
  contested threes would fall under 30 in 100 (34). Scoring in arm A: right, at the edge (1.20). The setup: right
  that the readings can't tell placements apart; wrong that play couldn't either: the search's picks were clearly
  worse. Help: right that the lane would not be clearly better; I did not expect it to be worse. The straight
  drive: confirmed, with the correction about an arrow across the path; wrong that X1 on I10 walls it under the
  zone (he closes one side). Arm B: right (0.11 lower, fewer rim shots). Speed in play: wrong by a little (a few
  in 100 slower than 18n's code, inside the targets). Setup inside its time: right for the search, and the old
  setup turned out not to be.

## For Shaun to decide (three)

1. **The setup.** *Recommend: keep the old setup for now, and give the setup a step of its own that learns it
   from play.* Why: the setup you ordered is built and is 6.8 points a possession worse by play (2.8 to 10.7),
   because the engine has no reading that can judge a setup. The old one plays level with everything I tried
   against it, though it does not fit the players (centres start on the three-point line). The rival that would
   work: play out starts in bulk offline, record what each went on to earn, and fit a setup reading on that, the
   way the map is fitted. That is the learned-weights work you kept out of this step. The other choice is to turn
   the search on as it is (`setup.search`), which I don't recommend. While the old setup stays I would also make
   it keep its time (Part 5): each possession would start 4 to 6 seconds sooner, and by play a defender simply
   next to his man is level with what the old setup finds (22.1 against 22.2).
2. **The zone as the app's default.** *Recommend: yes, as the next step, after the one-line bridge fix and a speed
   check on a phone.* Why: check 4 confirms that with the zone off a square defender can't wall a drive, so the
   defence must choose between the shot and the drive. With the zone on it scores 1.09 a possession against 1.20,
   nearer real basketball, and one defender can be square and a wall. What it costs: more reaching (steals tried
   80 in 100 possessions against 51, steal fouls 33 against 24) and turnovers a little over the FIBA band (0.21).
   On this machine the zone still fits the speed targets on the fast engine, with little room (Part 5).
3. **Fouls at the rim.** *Recommend: leave the rule, and decide whether to lower the Contest foul ratings.* Why:
   the block was never tried, 0 times in 110 chances over the two arms, so no shooting foul is ever called (FIBA:
   20 to 30 in 100 rim shots). You kept the block as a live choice for low-foul defenders who get in front. By the
   numbers it is live in one case only:

   | The defender is | Foul rolls | The block pays when his Contest foul rating is | Cards that low |
   |---|---|---|---|
   | In front, arrow off | 1 | 5 or lower | 4 of 81 |
   | Beside | 2 | 2 or lower | none |
   | Behind | 2 | 3 or lower | none |

   (A layup of 18 against a contest of 9, free throws 15: the hand up leaves 24, the block 18 or 41 if fouled, so it
   pays under a foul chance of 26 in 100.) The lever that stays inside your rulings is the rating itself: with
   every Contest foul rating 3 lower, the block from in front pays for 31 of the 81 cards. That is a card value,
   so it is yours (D-190), and I have not tested it.

## Model for the next step

Claude Fable 5.2, effort high, for either next step.

- **If the zone becomes the default (decision 2):** a small step. The bridge fix, the All-Star's map refitted
  under the zone, the same test, and the speed check. About 8 core-hours.
- **If the setup is learned from play (decision 1):** a bigger step, and the cost is play-outs: about 2,000 starts
  played out to fit on is 12 core-hours before any test. Budget 20.
