# Family Legacy: what the economy does

First run: six hundred complete campaigns, one hundred for each of six sibling profiles, played by the real game code in a headless browser with scripted siblings. The tool is `tools/inheritance-legacy-sim/simulate_legacy.js`; its own output with every number is in `tools/inheritance-legacy-sim/results/`. This page reads the results against the plan.

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
- **The gap-closing lever is play, not transfers (designer's ruling after this run).** A cutter can favour the other plot; a chooser can take the smaller plot; an investor can place purchases where the other will inherit them. The second run below shows these work when measured to the lead. The record screen states each as a fact.
- **The size of income is the time scale (designer's ruling after this run).** Payments are real yields over the years between estates; the default of five reproduces every existing number, and ten doubles them. One number, stated in the rules. The second run below measures it.

## Caveats

Scripted siblings are not people: they never run out of time, never misread a value, and cut only straight fences. Real cuts will be worse and real choices more varied, so real campaigns will show wider gaps and more broken holdings than these numbers. The tool is for comparing rule changes against each other, which it does on the game's own code in four minutes per six hundred campaigns.

## Second run: the time scale, and keeping the family in check

The designer's two rulings after the first run: payments must be proportional to reality, with the years between estates as the only lever; and the gap is closed by play at the next estate, not by transfers. Both were put into the game and the simulator and measured.

### Real yields

What productive property returns in cash each year, as a share of its value:

- Farmland: cash rent is about 2.8% of land value (US cropland price-to-rent ratio of 36, farmdoc daily, January 2026, from USDA NASS data); the farm sector's return on assets from current income has averaged about 2% over ten years, with total returns near 7.5% only because of land appreciation. Sources: [USDA ERS rent-to-value](https://ers.usda.gov/data-products/charts-of-note/75780), [farmdoc daily](https://farmdocdaily.illinois.edu/wp-content/uploads/2026/01/fdd010926.pdf), [Farm Bureau on USDA ERS returns](https://www.fb.org/market-intel/usdas-early-look-at-2019-farm-income), [Purdue, farm sector financial performance](https://ag.purdue.edu/commercialag/home/wp-content/uploads/2022/11/20221101_Langemeier-USFarmSectorFinancialPerformance.pdf).
- Timberland: income return about 4% a year (1992 to 2020), total return 6 to 11% with appreciation. Sources: [AcreTrader on NCREIF timberland income](https://acretrader.com/learn/acretrader-101/whats-the-return-on-timber-investments), [Manulife, U.S. timberland returns](https://www.manulifeim.com/institutional/at/en/viewpoints/private-markets/strong-income-and-appreciation-gains-for-u-s--timberland-in-2023).
- Vineyards and orchards: 1.5 to 3% as land, about 5% as a target operating return, with much higher internal rates of return only for successful operations. Sources: [ma-propriete.fr on vineyard returns](https://ma-propriete.fr/en/blog/quelle-est-la-rentabilite-dun-vignoble), [Perennia, Nova Scotia wine grape cash flow](https://www.perennia.ca/wp-content/uploads/2018/04/ns-wine-grape-cost-of-production-and-cash-flow-analysis.pdf).
- Quarries: an aggregates producer reports a return on invested capital of about 16% a year. Source: [Vulcan Materials, Form 10-K FY2024](https://www.sec.gov/Archives/edgar/data/1396009/000139600925000005/vmc-20241231.htm).

So productive holdings yield about 4% of their value a year and a quarry about 15% of the capital put in. At one year between estates, a grade C holding (score 5) would pay 0.2 Capital: nothing. At five years it pays 1, grade B 2, grade A 3, and a Quarry 3 twice: exactly the campaign's existing table. The existing numbers were already real-world yields; what was unstated was the time they covered.

### What was built

The game now carries the time scale as a rule. Each estate is settled a set number of years after the last (default 5, so every existing payment is unchanged), a holding's payment is its score times 4% times those years, a Quarry's or Logging Operation's payment scales the same way, the campaign rules state it, and the save format records it. Logging stays as it was (2 Capital three times at five years, about 13% a year on its value), which is above a timberland income return; it is the one figure a stricter reading would halve. The simulator takes `--years`.

### The time scale

Deliberate play (`aware`) and naive play (`greedy`), 100 campaigns each:

| Years between estates | Legacy spans | Lower-Property plot was better | Margin when it was | Income share of final wealth | Mean final wealth gap |
|---|---|---|---|---|---|
| 5 (current) | about 30 years, one generation | 13% (naive) to 21% (deliberate) of estates | 3 to 6 points, max 23 | 5% to 19% | 10 to 21 |
| 10 | about 55 years | 19% to 28% | 6 to 13 points, max 50 | 10% to 32% | 14 to 37 |
| 15 | about 80 years | 22% to 35% | 10 to 21 points, max 81 | 16% to 41% | 20 to 59 |

The lever is clean: every measure moves in proportion. At five years the Legacy is one generation and income is a modest layer. At ten, income is a third of a deliberate family's wealth and the choice between Property now and income later bites in about one estate in four with margins worth caring about. That is the designer's choice to make, and it is now one number.

### Keeping the family in check

Siblings who deliberately lose an estate once they are ahead, modelled two ways. Blunt: as cutter, the most lopsided straight fence; as chooser, the worse plot. Measured: as cutter, the fence whose long-term gap is about the size of the lead; as chooser, the smaller plot only when the loss does not exceed the lead.

| Profile (5 years) | Estates conceded | Gap closed / held / widened | Mean final wealth gap |
|---|---|---|---|
| aware, no conceding | 0% | 11 / 13 / 76 | 21 |
| blunt, concede when 10 ahead | 35% | 8 / 14 / 78 | 36 |
| blunt, concede whenever ahead | 100% | 73 / 4 / 23 | 51 |
| measured, concede when 10 ahead | 28% | 20 / 21 / 59 | 13 |
| measured, concede whenever ahead | 80% | 18 / 31 / 51 | 12 |
| measured against a greedy sibling | 11% | 10 / 28 / 62 | 14 |

Blunt concession flips the lead and overshoots: handing over a whole lopsided estate to fix a ten-point lead makes a thirty-point swing, the other sibling concedes back, and the family oscillates with a larger final gap than if nobody had tried. Measured concession works: the final gap falls by about 40% (13 against 21) and the share of families that hold steady or close more than doubles. The levers the rules already give, a chosen cut and a chosen plot, are enough to keep a family in check, provided the sibling can see what they are giving up. The simulator's cutters only draw straight fences; a person drawing freely can measure a concession more finely still.

Two consequences for the plan. P16, holdings visible at Choose, is what makes a measured concession possible for the chooser; without it a sibling conceding is guessing. And the record screen (E2) should state concessions as facts the system can see: a cutter's fence that favoured the other plot by N, a chooser who took the smaller plot by N, and whose purchases ended up in the other sibling's plot. Those are the acts the chronicle will remember.
