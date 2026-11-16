# Step 18s, stop one: estimates, written before measuring (16 Nov 2026)

Agreed with Shaun (D-199): two stops. This is stop one: the map, the coach view and design checks 1 to 6, in the
fast engine. The search and the setup don't read the map yet, so nothing in play changes at this stop.

| Part | What the compute buys | Estimate (core-hours) |
|---|---|---|
| 1 | The map built in the fast engine and read on named positions (no play-outs). | 0.3 |
| 2 | Design checks 1 to 6 by the map. Check 1 also by play: Shaun's defence against the placement the map reads smallest, 16 play-outs a line. | 1.5 |
| 3 | The coverage view in the app; the named tests and the site tests. | 1.0 |
| **Total** | | **2.8** (stop at 5.6) |

What I expect: checks 1, 2, 3 and 5 fall out of the map as built. Check 4 (arrows) falls out where an arrow decides
who is square. Check 6 (a screen) falls out through the defender's stopped movement. The one most at risk is check
2, if a non-shooter's defender in the lane leaves his man a catch worth more than the map thinks.

## Compute used
- check 1 played (check1) (2 positions, 16 each, the lane reading {'O': False, 'X': False}): 0.42 (running total 0.42)
- part 1: the map read on named positions, built and rebuilt (no play-outs): 0.1 (running total 0.52)
- part 2: design checks 1 to 6 by the map, run five times as the checks were corrected: 0.1 (running total 0.62)
- part 3: the named tests (32 minutes), the site tests, the three files run again, the timing test alone: 0.71 (running total 1.33)
- part 3: the two engines compared (300 positions with 8 searches, 200 shot reactions), two cores: 0.32 (running total 1.64)
- part 3: the view in the browser, screenshots: 0.03 (running total 1.68)

# Stop two: estimates, written before measuring (16 Nov 2026)

Shaun's prompt of 16 November (D-201, D-202, the addendum on the defence's strength). Order: part 1, 2, 3, 4.

| Part | What the compute buys | Estimate (core-hours) |
|---|---|---|
| 1 | The pass chance by the rules in both engines, checked against the rules' own actions on random positions; forced lines on 18r's help position and on Shaun's board, 16 play-outs a line. | 2.0 |
| 2 | The map in a fast form for the search; strength, fragility and broken; the combination fitted on forced lines; the search and the setup reading it; the trainer's phase lines. | 6.0 |
| 3 | Checks 7, 8, 9 (18o's closeout position replayed first), S1 to S4, the Screen evidence, game EB3F5B. | 6.0 |
| 4 | The map and the measures in the other engine, the two compared; the named tests. | 2.0 |
| **Total** | | **16.0** (stop at 32) |

What I expect: part 1 makes the offence pass more and drive and kick against help, by 2 to 5 points on 18r's
position. Part 2 is the part most at risk: the map costs about 1.5 seconds a position today, and the search needs
it in a few thousandths. If it can't be made that fast without changing what it says, I stop there and report.

## Compute used, stop two
- part 1: the pass chance against the rules on 300 random passes: 0.0 (running total 1.68)
- part 1: the pass chance against the rules on 6002 random passes: 0.01 (running total 1.69)
- part 1: the pass chance against the rules on 1502 random passes: 0.01 (running total 1.69)
- part 1 forced lines (pass, the old pass chance) (6 positions, 16 each, {'O': {'pass_rules': False}, 'X': {'pass_rules': False}}): 0.97 (running total 2.66)
- part 1 forced lines (pass, the rules' own) (6 positions, 16 each, {'O': {'pass_rules': True}, 'X': {'pass_rules': True}}): 1.88 (running total 4.54)
- part 1 forced lines (cross, the offence alone on the rules' own) (3 positions, 16 each, {'O': {'pass_rules': True}, 'X': {'pass_rules': False}}): 0.64 (running total 5.17)
- part 1: the pass chance against the rules on 6002 random passes: 0.01 (running total 5.19)
- part 2: play for the fit (a, 128 possessions, a drawn turn at rate 0.125): 1.97 (running total 7.15)
- part 3: the closeout positions, the computer's own pick (closeout) (3 positions, {'pass_rules': True}): 0.0 (running total 7.16)
- part 3: the closeout positions replayed under D-198 (closeout) (12 lines on 3 positions, 16 each, {'O': {'pass_rules': True}, 'X': {'pass_rules': True}}): 1.11 (running total 8.26)
- part 2: play for the fit (c, 128 possessions, a drawn turn at rate 0.125): 2.22 (running total 10.49)
- part 3: check 7, a run lost to a worker out of memory after 11 minutes (the map kept with every reading; mended): 0.7 (running total 11.19)
- part 2: play for the fit, two runs stopped part-way when the map was corrected (a broken zone and a screen end with the phase; the answers judged on the best six options): 0.45 (running total 11.64)
- part 3: check 7 by forced lines, the map read (check7) (6 positions, 16 each, {'O': {'pass_rules': True, 'map': True}, 'X': {'pass_rules': True, 'map': True}}): 1.83 (running total 13.47)
- part 3: check 7, the defence alone on the map (check7x) (4 positions, 16 each, {'O': {'pass_rules': True, 'map': False}, 'X': {'pass_rules': True, 'map': True}}): 1.04 (running total 14.51)
- part 3: check 8, the turns weighed (check8) (1 positions, {'pass_rules': True, 'map': True}): 0.0 (running total 14.51)
- part 3: check 8, the turns weighed, the defence (check8) (1 positions, {'pass_rules': True, 'map': True}): 0.0 (running total 14.51)
- part 3: check 8 and S2 by forced lines (check8) (5 lines on 2 positions, 16 each, {'O': {'pass_rules': True, 'map': True}, 'X': {'pass_rules': True, 'map': True}}): 1.68 (running total 16.2)
- part 3: S3, the offence's own pick (s3) (1 positions, {'pass_rules': True, 'map': True}): 0.0 (running total 16.2)
- part 3: S3, the defence's own pick after the screen (s3) (1 positions, {'pass_rules': True, 'map': True}): 0.0 (running total 16.2)
- part 3: S3 by forced lines (s3) (6 lines on 2 positions, 16 each, {'O': {'pass_rules': True, 'map': True}, 'X': {'pass_rules': True, 'map': True}}): 2.55 (running total 18.75)
- part 3: S4, one core: the setups searched for 4 deals (s4): 0.01 (running total 18.76)
- part 3: S4 by play (12 setups, 6 each, the map read) (s4): 0.8 (running total 19.56)
- part 3: S4, one core: the setups searched for 4 deals (s4): 0.01 (running total 19.57)
- part 3: S4 by play (12 setups, 6 each, the map read) (s4): 0.88 (running total 20.45)
- part 4: the named tests, twice in full (43 minutes each) and once part-way; the site tests: 1.74 (running total 22.18)
- part 4: the two engines compared (the searches with the map off, on and on for the offence; the map's numbers on 600 positions): 0.72 (running total 22.91)
