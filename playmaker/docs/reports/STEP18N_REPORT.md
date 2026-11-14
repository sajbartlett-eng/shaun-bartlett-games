# Step 18n report: jump shots contested by position, the new contest ratings, the refit and the test

## In five lines

FIVE_LINES

## Parts 0 and 1: merged, ruled, and the cards

- **Merged:** step 18l (pull request 74). There was no 18m pull request, so the restore was done here.
- **`DECISIONS.md`:** D-189 (contests restored), D-190 (no card or rule change without your agreement), D-191
  (position only), D-192 (the new jump-shot contest ratings), D-193 (nothing is zero).
- **The cards match the table.** All 81 cards, all seven contests, checked against
  `docs/reference/JUMP_CONTESTS_14NOV.md` by a test. Nothing but contest ratings changed on any card.
  - Inside contests are back at your original values, with their ranges and three floater chart entries.
  - Mid-range, long two and three contests are the map on your originals. Their range: average from 2, above
    average from 3.
  - The two new types take the Scoring Small Forward's and the Defensive Power Forward's contests, and keep their own
    foul ratings.
- **Levels:** contest ratings are the same at every level. The level files are regenerated.
- **One thing that had to follow the restore:** the anchor job's dunk-contest threshold. D-184 had carried it from 11
  to 5 with the rating. It is 11 again, or nearly every card would be an anchor.

## Part 2: the rule, built

- **Jump shots** (mid-range, long two, three). Every defender next to the shooter contests with no action, at his
  card's contest rating: 3 less from behind, 2 less if he is rushed. His arrow changes nothing. There is no Contest
  action and no shooting foul.
- **Inside shots** (layup, dunk, post, floater). A hand up next to the shooter is automatic: the rating less 3, 3
  less again from behind, never a foul. From in front with his arrow on the shooter the full rating is automatic and
  never a foul. From anywhere else he may go for the block, a Contest action: one foul roll from in front with the
  arrow off, two from the side or behind.
- **Only the best contest counts. A contesting defender always takes at least 1 off** (D-193).
- **The switch:** `rules.position_contest`, on in the app, off at the table. `?positioncontest=0` turns it off.
- **The sentence,** in the help and the rules text, as you wrote it.
- **The explanations:** "X2 was beside O4, so the three was contested (20% off)." Inside: "X5's hand up from
  behind: 1 off", "X5 went straight up in front of O1 with his arrow on him: 8 off, and no foul", "X5 went for the
  block from the side: 8 off".
- **The computer's search has no jump-shot Contest move.** Its reading of a look counts any defender who can get
  next to the shooter in the reaction, by position.
- **The foul price no longer touches jump shots.** It prices steal fouls and fouls on inside shots only.
- **Derived files regenerated:** the JavaScript engine, `site/engine_bundle.json`, the level files, the one-file app,
  the team sheet, `RULES_CURRENT.md` and the rules register.

**Cases the lines don't settle. I read each the way closest to "position decides". Marked for you.**

1. **Both of the reaction's actions can now be movements on a jump shot.** A contest needs no action, so a defender
   can Quick Step in and then Move to be set, or come from two movements away. The reaction rule itself is unchanged.
2. **Beside the shooter counts in full on a jump shot.** Your lines name only "from behind" as a reduction.
3. **Inside, a rushed defender straight up in front still contests in full, 2 lower.** Rushed takes 2 off every
   contest.
4. **The block is held at 1 too.** A defender who goes for it from behind while rushed takes at least 1 off.
5. **The computer's reading of a declared shot plays a second movement only after a first that ends next to the
   shooter.** A closeout from two movements away is seen when the defence is the one moving, and by the reading of a
   look, but not inside the offence's own look-ahead at a declared shot.

**Nothing is zero: the other rolls (D-193, listed, not changed).**

- **A rushed defender's Steal.** 35 of the 81 senior cards have a Steal of 2 or less. Rushed, that is 0 or less.
  (The roll is the ball handler's Dribble less the defender's Steal.) At youth level 6 cards; at junior none.
- **A shot after its contest.** The rating a shot is rolled at is the shooter's rating less the contest, held at 0.
  - With the shooter set, one senior pair reaches 0: a post shot of 8 against a post contest of 8.
  - With the shooter rushed as well, more do: 172 senior shooter-and-defender pairs on a three, 123 on a floater,
    122 on a dunk, 77 on a post shot, 11 on a long two.
  - At junior level it is common: 223 pairs on a three with the shooter set.
- **Nothing else reaches 0.** Dribble, Pass and Screen never fall under 9. Agility, Intercept and Challenge never
  fall under 1, rushed.
- The full list by level is in `docs/runs/step18n/zero_ratings.txt`.

## Part 3: the refit and the re-recording

REFIT_TEXT

## Part 4: the test, player against player

All-Star self-play, 200 possessions, on the final default: today's cards, the rule on, the refitted maps in.

**Does the computer shoot contested threes with everyone, or mainly with its great shooters? Mainly with its good
ones.** 35 of its 37 contested threes were taken by shooters rated 9 or more. Shooters rated 8 or less took 13
threes, and 2 of those were contested.

**Every three: the shooter's open rating against the contest that counted.** Each cell is shots taken, then in
brackets the makes the cards give them. (The game scores a shot by its chance, rating less contest in 20. It rolls
no make or miss, so "made" is that chance added up.)

| Shooter's open three | Open | Contest 1 | Contest 2 | Contest 3 | Contest 4 | All |
|---|---|---|---|---|---|---|
| 11 | 6 (3.1) | 3 (1.5) | 3 (1.4) |  |  | 12 (6.0) |
| 10 | 8 (3.9) | 14 (6.3) | 1 (0.4) |  |  | 23 (10.6) |
| 9 | 28 (12.6) | 5 (2.0) | 7 (2.2) | 2 (0.6) |  | 42 (17.4) |
| 8 | 9 (3.6) |  | 1 (0.3) |  |  | 10 (3.9) |
| 7 | 1 (0.3) |  |  |  |  | 1 (0.3) |
| 6 | 1 (0.3) |  |  | 1 (0.1) |  | 2 (0.4) |
| **All** | 53 (23.8) | 22 (9.8) | 12 (4.3) | 3 (0.7) | 0 (0.0) | 90 (38.6) |

- **90 threes in 200 possessions; 37 contested (41 in 100, 32 to 51).** Before this step 25 in 100 were.
- **Shooters rated 10 and 11 took 35 threes and 21 of them were contested.** They shoot over a defender.
- **Shooters rated 9 took 42 and 14 were contested.** They mostly wait for the open one.
- **Shooters rated 8 or less took 13, all but 2 open.**
- **No three met a contest of 4, and only 3 met a contest of 3.** 22 of the 37 contests took just 1 off.

**Mid-range and long twos: none were taken.** Not one in 200 possessions. An open mid-range shot is worth at most
12 in 20 for 2 points; the computer always finds a three or a rim shot worth more.

**Where the contested threes came from.**

| Shooter | Contested threes |
|---|---|
| Stretch Small Forward A (three 10) | 8 |
| Sharpshooter A (three 11) | 6 |
| Scoring Point Guard A (three 10) | 6 |
| Scoring Small Forward A (three 9) | 4 |
| Stretch Small Forward B (three 9) | 3 |
| Bucket Getter B, Combo Guard A (three 9) | 2 each |
| Sharpshooter C, Two-Way Shooting Guard A, Three-and-D B (three 9), Three-and-D A (three 10) | 1 each |
| Scoring Small Forward B (three 8), Post Scorer Centre A (three 6) | 1 each |

| Where the defender stood | Contested threes | Points a shot |
|---|---|---|
| In front, set | 13 | 1.00 |
| In front, rushed | 9 | 1.33 |
| Beside, set | 4 | 1.20 |
| Beside, rushed | 9 | 1.32 |
| Behind | 2 | 1.43 |
| Nobody (open) | 53 | 1.35 |

- **Half the contests (18 of 37) were rushed:** a defender who got there on a Quick Step or a Sprint. Rushed, most
  defenders take 1 off, and a three contested that way scores what an open one does.
- **Only a set defender in front brings a three down to FIBA's level:** 1.00 a shot.

**Inside shots.** 92 in 200 possessions: 78 layups, 8 floaters, 6 post shots, no dunks.

| Shooter's open rating | Open | Contest 1 | Contest 2 | Contest 3 | Contest 4 | Contest 5 | Contest 6 | Contest 8 | Contest 9 | All |
|---|---|---|---|---|---|---|---|---|---|---|
| 19 | 7 (6.4) | 4 (3.3) | 1 (0.8) | 6 (4.5) |  | 4 (2.8) | 1 (0.7) |  |  | 23 (18.5) |
| 18 | 14 (12.0) | 3 (2.4) | 6 (4.8) | 6 (4.4) | 9 (6.2) | 5 (3.2) |  | 1 (0.5) | 1 (0.5) | 45 (34.0) |
| 17 | 2 (1.6) | 3 (2.3) | 4 (3.0) | 5 (3.5) |  |  |  |  |  | 14 (10.4) |
| 16 |  |  |  |  |  |  | 1 (0.5) |  |  | 1 (0.5) |
| 15 | 2 (1.3) | 1 (0.7) |  |  |  |  |  |  |  | 3 (2.0) |
| 14 | 2 (1.4) | 1 (0.7) |  |  |  |  |  |  |  | 3 (2.1) |
| 13 |  | 1 (0.6) |  |  |  |  |  |  |  | 1 (0.6) |
| 11 | 2 (1.0) |  |  |  |  |  |  |  |  | 2 (1.0) |
| **All** | 29 (23.7) | 13 (10.0) | 11 (8.6) | 17 (12.4) | 9 (6.2) | 9 (6.0) | 2 (1.2) | 1 (0.5) | 1 (0.5) | 92 (69.1) |

| Where the defender stood | Inside shots | Went for the block | Fouls | Made, in 100 |
|---|---|---|---|---|
| Nobody (open) | 29 | | | 82 |
| Behind | 41 | 0 | 0 | 74 |
| In front | 16 | 1 | 0 | 67 |
| Beside | 6 | 0 | 0 | 68 |

- **The defence went for the block once in 92 inside shots, and fouled nobody.**
- **Why: on these cards the block is a bad bet.** A Contest foul rating of 10 is a foul half the time on one roll, and
  three times in four on the two rolls from the side or behind. A fouled layup then scores more than an open one.
- **Most inside shots are taken with the defender behind** (41 of 63 contested ones). The hand up from behind takes 1
  to 3 off a layup of 17 to 19.
- **Straight up from in front with the arrow on him happened once** (a contest of 9). The other in-front contests
  were hands up with the arrow off.

**Beside FIBA.** Nothing was tuned to these.

| Measure | Real FIBA | The game now | Before this step |
|---|---|---|---|
| Points a possession | 0.95 to 1.0 | **1.28** (1.22 to 1.34) | 1.36 (1.30 to 1.42) |
| Shooting fouls on threes | 1 in 100 | none, by rule | 0 of 89 |
| Shooting fouls at the rim | 20 to 30 in 100 | **0 of 78** (0 to 5 in 100) | 1 of 89 |
| Blocks | 6 in 100 twos | the game has none; the block was tried once in 92 | |
| Turnovers a possession | 0.15 | 0.085 (0.045 to 0.125), all from a reach | 0.08 |
| Steals tried a possession | not tracked | 0.47 (0.37 to 0.56) | 0.48 |
| Fouls on a Steal a possession | 0.05 to 0.08 | 0.20 (0.14 to 0.26) | 0.21 |

- **Scoring came down by 0.08 of a point and is still above FIBA by more than a quarter.**
- **Shots contested rose from 33 in 100 to 55** (48 to 62).
- **Possessions run longer:** 28 decisions each, where it was 19. Shots by phase 1 to 6, in 100: 22, 38, 16, 11,
  10, 3. Before: 39, 37, 16, 6, 3, 0.
- **The shot mix:** 90 threes, 78 at the rim, 14 other twos.

**Game EB3F5B, the pass to O4 in the corner.** Played out on today's cards and rules, 16 times each.

| What the defence does | The offence goes on to score |
|---|---|
| The computer's choice: X2 moves to B7 | 26.6 (24.5 to 28.7) |
| X4 Quick Steps to E4 | 26.6 (24.8 to 28.4) |
| The defence pauses, as in your game | 26.6 (25.9 to 27.4) |
| X4 Moves to C4, facing him | 26.9 (24.7 to 29.1) |

- **Nothing separates the four.** O4's corner three is a 9 now, worth about what the possession is worth anyway.

**Shooting that looks too generous, player against player. Listed, not changed.**

1. **An inside shot with the defender on the shooter's back: 74 in 100.** 41 shots. The hand up from behind is the
   rating less 6, so a contest of 8 or 9 takes 2 or 3 off an 18. European league rim shooting, most of it contested,
   is about 64 in 100 (your card audit).
2. **Open inside shots, and layups in all: 82 and 77 in 100.** FIBA's 20 to 30 fouls in 100 rim shots are missing
   too. A layup here is worth 1.54 points, and every inside shot 1.50.
3. **A three contested by a rushed defender: 44 in 100,** the same as an open one. 18 shots. Rushed takes 2 off a
   contest of 2 or 3, and D-193 holds it at 1.
4. **A three with a set defender beside the shooter: 40 in 100.** 4 shots, so thin.
5. **Open threes for shooters rated 9: 45 in 100, 28 shots.** That is the card, and the audit's "elite" line. It is
   also the single biggest cell in the table.
6. **Good shooters over a contest:** a 10 or 11 with 1 off still scores 45 to 50 in 100. 17 shots.

## Part 5: speed

SPEED_TEXT

## What it proves

PROVES_TEXT

## Compute

COMPUTE_TEXT

## Noticed, not touched

NOTICED_TEXT

## For Shaun to decide (three)

DECISIONS_TEXT

## Model for the next step

MODEL_TEXT
