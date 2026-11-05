# Family Legacy: what the economy does

Six hundred complete campaigns, one hundred for each of six sibling profiles, played by the real game code in a headless browser with scripted siblings. The tool is `tools/inheritance-legacy-sim/simulate_legacy.js`; its own output with every number is in `tools/inheritance-legacy-sim/results/`. This page reads the results against the plan.

## The table

| Profile | Lower-Property plot was better | Margin when it was (mean, max) | Chooser took the long-term better plot | Income share of final wealth | A sibling had no Capital at an investment phase | Holdings surviving the fence | Gap closed / held / widened | Mean final wealth gap |
|---|---|---|---|---|---|---|---|---|
| greedy (random builds, greedy choosers) | 11% of estates | 2.4, 8 | 87% | 5% | 32% of phases | 92% | 14 / 18 / 68 | 11 |
| aware (cluster builds, long-term choosers) | 21% | 6.0, 20 | 100% | 20% | 2% | 100%+ | 10 / 12 / 78 | 19 |
| mixed (aware against greedy) | 16% | 4.5, 17 | 91% | 15% | 6% | 98% | 11 / 20 / 69 | 16 |
| savers (aware, never buy) | 17% | 4.6, 16 | 100% | 16% | 2% | 100%+ | 5 / 23 / 72 | 21 |
| closer (concedes small plots when ahead) | 21% | 4.2, 17 | 93% | 19% | 2% | 100%+ | 13 / 8 / 79 | 21 |
| chaos (random everything) | 1% | 2.8, 4 | 51% | 6% | 32% | 94% | 20 / 5 / 75 | 85 |

"Holdings surviving the fence" above 100% means a straight fence occasionally splits one group into two that both still qualify.

## What it says

**S1. The central choice exists, and it is occasional.** The lower-Property plot is the better choice across the Legacy in about one estate in five when siblings build holdings deliberately (21%), one in nine when they build at random (11%), and almost never when they play at random (1%). When it happens the margin averages 2 to 6 points and reaches 20. A pair that plays the campaign as designed meets this decision a little more than once per six estates. That is a real tension, not a decorative one, and not yet a frequent one.

**S2. Knowing the long-term value barely pays.** An aware sibling against a greedy one wins 49% of campaigns. Greedy choosers still take the long-term better plot 87% of the time, because the two usually coincide. Under the current schedule of three payments per holding, seeing the holdings is worth a point or two per campaign. If the campaign's premise is to be felt, the payments have to matter more or the holdings have to appear more often.

**S3. Income is a fifth of wealth at best.** With holding-aware play, income is 20% of final wealth; with random builds, 5%. Property decides the Legacy. This is the number to move if the designer wants "Property now or income later" to be a question in most estates rather than some.

**S4. A sibling with no Capital is common for new players and rare for skilled ones.** At 32% of investment phases a sibling has nothing to spend when builds are random; at 2% when siblings build beside productive partners. The empty turn is a skill signal, not a flaw. It must be shown (plan item P4), and a Capital floor (P8) is not needed by the economy; it would only be a kindness to first campaigns.

**S5. Straight fences rarely destroy holdings.** 92% to 100% of productive groups on the board survive a fair straight cut. The cutter's lever on the other sibling's income is small in practice. A cutter who wanted to break a holding would have to draw a worse cut to do it.

**S6. The gap widens in about three campaigns in four, whatever the siblings do.** Even the profile that concedes the smaller plot whenever it costs 2 or less closes the gap in only 13% of campaigns, because estates swing 25 to 60 Property and a 2-point concession is lost in the noise. The one voluntary gap-closing act the rules allow is too small to tell a closing story. If the narrative engine is to record families that chose to close the gap, the rules need a lever large enough to do it.

## What this changes in the plan

- **P1 is done.** The numbers are the baseline for every later change; rerun the tool after any rule change and compare.
- **P16 (holdings visible at Choose) stands,** and S2 says it is necessary but not sufficient: the choice is visible one estate in five and worth a few points. Tuning decides whether that is enough.
- **P8 (Capital floor) is not justified by the economy.** Drop it unless first-campaign feel asks for it.
- **A new designer's decision: the gap-closing lever.** Candidates, each a real thing families do and each recordable in the chronicle as a fact: a sibling gives Capital to the other at an investment phase; a sibling pays for an addition and places it where the other is likely to inherit it, which the rules already allow but the roles hide; the Fairness Challenge returns inside the Legacy as a redraw the leading sibling can offer. The simulator can measure any of them before they are built.
- **A second designer's decision: the size of income.** More payments per holding, higher payments per grade, or holdings that form more easily. The simulator reports income share, bite frequency and gap arcs for any schedule within an afternoon.

## Caveats

Scripted siblings are not people: they never run out of time, never misread a value, and cut only straight fences. Real cuts will be worse and real choices more varied, so real campaigns will show wider gaps and more broken holdings than these numbers. The tool is for comparing rule changes against each other, which it does on the game's own code in four minutes per six hundred campaigns.
