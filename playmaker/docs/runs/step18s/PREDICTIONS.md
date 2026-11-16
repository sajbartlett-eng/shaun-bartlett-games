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
