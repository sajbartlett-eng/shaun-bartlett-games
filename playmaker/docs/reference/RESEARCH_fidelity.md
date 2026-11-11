# Playmaker System Fidelity Audit: What Makes a Half-Court Position Valuable, and What the Computer Must Read

The value of a half-court position is set less by the shots available now than by two things one move later: whether a defender can still get to each potential shooter in time to contest, and how much the defence gives up elsewhere when it answers the ball's threat. The computer reads the first only roughly and the second hardly at all. That gap fits all three of its known failures.

## TL;DR

- **The biggest measured factor is contest geometry, not the shot menu.** The source data used here put the gap between tightly guarded and wide-open three-point attempts at about 0.28 points per shot (0.88 vs 1.16). Corner threes beat above-the-break threes mainly because over 90% of them are assisted and less contested. Distance to the rim explains only part of the gap. The computer needs an exact "can anyone contest this, from the rim side, in time" reading for every potential shooter. It should be built from tokens, reaction actions, unused Moves and Quick Steps, locks and arrows. The current single-cover estimate is not enough.
- **The advantage chain is real but is not measured link by link.** Possessions with a paint touch score far more than those without (ShotTracker, across twelve high-Division I college programmes: 1.061 vs 0.706 points per possession; Jay Triano: +0.25 in the NBA half court). Expected-possession-value tracking shows an unused advantage disappearing within about a second. No public study measures how fast advantages decay. The computer should value "the best look one pass after the defence's best response" as a quantity. Counting factors cannot capture it. This is the most likely reason fitting weights to played-out games found no signal.
- **Taking 72% of shots in the first two of six phases is plausible only if continuing is risky.** In Skinner's optimal-stopping model with one look per phase, an NBA-like turnover risk (about 2.7% per passed-up look) gives roughly 50% of shots in the first third, and a risk of about 10% gives roughly 69%. Missing rebounds would push shots later, not earlier. Measure the game's real risk of continuing: if it is low, the calibration has absorbed the computer's own inability to find kick-outs and backdoor cuts.

## Key Findings

1. **Being open is the dominant shot-quality factor, and it behaves like a threshold.** League three-point percentage by closest-defender distance (2022-23, as reported by Breakthrough Basketball from NBA tracking): 0-2 ft 29.3%, 2-4 ft 29.4%, 4-6 ft 34.6%, 6+ ft 38.6%. In points per shot that is 0.88 / 0.88 / 1.04 / 1.16. The curve is flat inside 4 ft and rises steeply beyond it. In other words, a contest that arrives works almost as well as a tight one, and a contest that is late is worth almost nothing. This is exactly the binary that Playmaker's adjacency-based Contest models. A 2024 Hard2Guard summary gives 30.1% (tight) vs 38.4% (wide open) for threes and 45.3% for wide-open mid-range, which agrees. Sandy Weil's "The Importance of Being Open" (MIT Sloan Sports Analytics Conference 2011, STATS SportVU data from about 60 games) estimated that tight defence cuts shooting by about 12 percentage points after controlling for shot type, distance and shooter. It also found that "a quick catch-and-shoot has value on top of its influence on defender proximity." Confidence: high for direction and size; moderate for exact bins, because the subagent could not pull current figures straight from NBA.com, which loads its data with JavaScript.
2. **Shots set up by a pass beat self-created shots.** League catch-and-shoot effective field-goal percentage (eFG%) was 54.1%, against 45.6% on pull-ups (NBA.com, 2022-23). In 2013-14 the figures were 51.6% and 40.4%. Pelechrinis and Goldsberry (2021, tracking data from 750 games): corner threes went in at 38.8%, above-the-break threes at 34.7%. Distance alone explains about 1.8 points of that 4.1-point gap. Over 90% of corner threes are assisted, against just over 70% of above-the-break threes, and the closest defender averages about 6.5 ft away. Their wider estimate: an assisted shot is worth about 0.16 expected points more than an unassisted one. Confidence: moderate to high; this is observational, but a natural experiment with FIBA's different line geometry backs it up.
3. **Getting into the paint raises possession value, but the size of the effect is confounded.** A ShotTracker study of twelve high-Division I college programmes (college data, not NBA) found that possessions with no paint touch and no ball reversal scored 0.706 points per possession (PPP) with 27% turnovers. Paint touch only: 1.061. Reversals only: 0.937. Two or more reversals plus a paint touch: 1.189, but this "only occurred 4% of the time". Jay Triano (NBA): half-court possessions score about 0.25 PPP more when the ball touches the paint. One team's figures, charted by Alabama coach Nate Oats and reported in Brent Tipton's "The Paint Touch" via Breakthrough Basketball: 0.88 PPP with no paint touch, 1.26 with two, 1.5 with three. Confidence: moderate on direction, low on size. Possessions that reach the paint are partly selected for already having an advantage, so these are correlations, not causal effects.
4. **Cuts are the most efficient half-court play type; isolations and post-ups are the least.** Synergy averages (Nylon Calculus, around 2016-17): cut 1.246 PPP, putback 1.084, spot-up 0.999, off-screen 0.943, hand-off 0.916, post-up 0.885. Isolation was about 0.91 (2017-18 to 2020) and 0.85 (2014-15). Older figures: pick-and-roll ball handler about 0.79 and roll man about 0.97. Cuts are a small share of possessions: for example 5.4% of Boston's in 2025-26, at 1.358 PPP. Confidence: moderate. Synergy credits the play type that finished the possession, so a cut's PPP includes the advantage that earlier actions created.
5. **Turnovers cost more than the lost possession when the ball stays live.** In 2018-19 the opponent scored 1.28 PPP after a live-ball turnover and 1.08 after a dead-ball one. Inpredictable gives 1.25 and 1.06. The 2017-18 half-court average was 0.926 PPP. Skinner (PLoS ONE, 2012) measured an NBA turnover about every 100.2 seconds of possession and concluded that "NBA players tend to wait too long before shooting and undervalue the probability of committing a turnover." Confidence: high.
6. **Defence works through shot frequency and shot efficiency separately.** Franks, Miller, Bornn and Goldsberry (Annals of Applied Statistics, 2015) show that individual defenders can cut how often opponents shoot in an area without cutting how well they shoot, and the reverse. For position judgement, a defence "conceding a look by design" (low frequency of good shots, acceptance of poor ones) is a separate, measurable mechanism. Confidence: high for the framework.
7. **Defenders who hover between two threats are making a measurable mistake.** In drive-and-kick situations, NBA corner defenders stood on average 12.3 ft from the corner shooter (Pelechrinis and Goldsberry, 2016-17 tracking data from 750 games). That puts them between shooter and rim, covering both threats partly. The observed distances "resemble a normal distribution around the average instead of the bi-modal mixed Nash equilibrium strategy". The game-theoretic solution has an expected distance close to 13 ft but says the defender should commit fully to the shooter or fully to the drive, mixing between the two, rather than splitting. Lucey et al. (Sloan 2014, 19,386 three-point attempts; STATS SportVU data from 600 games in 2012-13; "open" meaning the closest defender is at least 6 ft away at release): defensive "role swaps" in the 3 seconds before a shot predict an open look. Confidence: moderate. The game theory is stylised, though the tracking observations are solid.
8. **Shot quality falls through the clock, and NBA teams wait too long.** Points per 100 possessions by elapsed shot-clock segment (82games): 0-10 s 112.3, 11-15 s 102.3, 16-20 s 100.6, 21+ s 91.8. Skinner (arXiv 1107.5793) estimates that at 15 seconds remaining a team has about a 4% chance per second of shooting, against an optimal 12%. Optimal shooting would raise efficiency from 0.86 to 0.91 PPP. Goldman and Rao, using a different structural model, find NBA lineups roughly dynamically efficient: the worst shot they accept falls steadily as the clock runs down. Confidence: moderate. The models disagree on how far from optimal NBA teams are, but not on direction.

## 1. Ranked Factor Table

How to read the table: "Effect" is the measured real-basketball effect. "Reads now?" uses the computer's current reading list. The last column is what the computer must calculate case by case from ratings, positions, arrows, reach, tokens, locks and the clock, with no fixed distances. Ranking blends effect size, how often the situation arises and how much of it is unread. That blend is my judgement.

| # | Factor | Measured effect (real basketball) | Confidence | Tabletop mechanic | Reads now? | What the computer must compute |
|---|---|---|---|---|---|---|
| 1 | Contest feasibility per shooter ("closeout reach") | 3P% 29.3 → 38.6 from tight to wide open; 0.88 → 1.16 points per shot; about 12 percentage points from tight defence | High | Contest: costs a token, needs adjacency, is the last of at most 2 reaction actions; −3 if contesting from further from the rim; arrow off the shooter = foul roll; free contest on a forced shot | Partly ("shot gets off before a contest" after best single cover) | For each potential shooter and square: the fewest reaction actions any defender needs to be adjacent, using remaining defence tokens, unused Move/Quick Step, locks, screens and arrow turns. Record whether he arrives rim-side (no −3) and whether his arrow is on the shooter (foul risk). Output a probability distribution of contest values, not a single cover. |
| 2 | Value after the help commits (second pass, drive-and-kick) | Assisted shot about +0.16 expected points; corner three worth 1.14 expected points (Pelechrinis and Goldsberry), about 12 points per 100 shots more than above-the-break threes; about half of corner threes come from a shooter anchored ≥4 s who receives a kick-out, and almost a third of passes to the corner come from the basket area, deep paint and baseline | Moderate–high | Pass (Intercept if an arrow covers the lane), receiver denial, Dribble beats a defender → help must move | No (search horizon too short; looks valued after one cover only) | For each threat the ball can make (drive lane, post, roll), find the defence's cheapest stopping response, then re-read factor 1 for every other attacker. The value is the best catch-and-shoot look created minus the interception risk on that pass lane. This is a max over offensive options after a min over defensive responses. |
| 3 | Penetration threat of the ball handler | Paint touch about +0.25 PPP in the half court; ShotTracker (college) 1.061 vs 0.706; NBA drives 0.48 points scored + 0.35 created by passing per drive (small 2013 sample); rim attempts off drives about 1.13 PPP | Moderate | Dribble contest (Dribble vs defender), arrow zone blocks drives, locks, paint tiles | Partly ("ball handler's paint look next phase") | Win probability of the Dribble against each defender whose arrow zone blocks a lane. Lock state of the on-ball defender. Whether he is in front of, beside or behind the carrier relative to the rim. Then the rim-tile reach of every helper before the shot resolves, and who would be left. |
| 4 | Defensive coverage allocation (capacity across threats) | Corner defenders average 12.3 ft from the shooter, distributed normally around that mean rather than committing; the equilibrium says commit; role swaps predict open shots | Moderate | Arrows, positions, reach | Switched off | Turn on the budget: each defender splits his reach across threats, with the cost of each split priced through factors 1 and 3. Penalise "between two threats" splits that arrive in time for neither. |
| 5 | Turnover and steal risk of the current state | Live-ball turnover → opponent 1.25–1.28 PPP vs 1.06–1.08; 27% turnovers on possessions with no paint touch | High | Steal (needs arrow on carrier; keep ball on roll ≤ Dribble − Steal; locks on miss), Intercept, denial | Partly ("chance the pass arrives") | Per-phase risk of holding: which defenders can turn an arrow onto the carrier and Steal with remaining tokens, and at what Dribble − Steal margin. Per-lane interception probability. Denial on each receiver. |
| 6 | Mismatch where it pays | Not directly measured in public data; isolation about 0.85–0.91 PPP shows that one-on-one creation without a scheme is a weak base | Low–moderate | Rating tiers A/B/C (+1/0/−1) | Yes, as counts | Mismatches weighted by whether the mismatched defender is the one who must act next (contest, stop the drive, deny). A two-tier gap at a square nobody can reach is worth little. |
| 7 | Cutting behind a defender (backdoor) | Cut 1.246 PPP, the most efficient half-court type; low volume | Moderate | Move/Quick Step, arrows (facing), receiver denial, Intercept | No (reach map ignores which side of the arrow the path runs) | Paths whose squares lie outside the defender's arrow zone and that end on a rim tile this phase. The pass lane must not be covered by any arrow. The low helper's reach to the rim tile must be counted. A denying defender whose arrow faces the ball is the trigger. |
| 8 | Screens (who is screened; the screener's next threat) | Coverages putting two defenders on the ball fell from 26.6 to 15.7 per 100 possessions in about a decade, while offences' PPP against them rose from 0.88 to 0.97 (Second Spectrum via theScore); roll man about 0.97 PPP | Moderate | Screen blocks squares; Challenge beats it; screener's later Move | No | Re-run the reach map with screen squares blocked. Compute the screener's look after roll or pop (factor 1). Compute what each coverage response costs, given the defenders' Challenge and reach. |
| 9 | Gravity and spacing | NBA has published gravity stats since 2025-26; shooting skill drives a player's gravity; corner defenders lean toward help | Moderate (concept), low (effect size) | Implicit: shooter ratings and tile values | No | A shooter's "cost to leave" = his look value if the pass arrives × (1 − probability a contest is achieved), from factor 1. This sets how far each helper can safely stray. Gravity then needs no rule. |
| 10 | Shot clock state | 112.3 → 91.8 points per 100 from early to late; Skinner thresholds fall as fewer looks remain | Moderate | 6 phases, forced shot with free contest | Yes (phase) | Continuation value by phase, recalibrated once factors 1–3 exist (see section 6). |
| 11 | Post position and seals | Post-up 0.885 PPP as a finishing type; counting the passes it leads to, post-ups were the most efficient half-court type in one Second Spectrum season (theScore) | Low–moderate | Post shot type; position closer to rim; Screen | No | Whether the post player stands rim-side of his defender (that defender's contest is from further out, so −3). Whether help can reach. The value of passing out of the post (factor 2). |
| 12 | Fouls and bonus | Not measured in sources gathered here | Low | +5 per steal foul; free throws in the bonus or on a second foul | No | Foul count, bonus state, and each defender's foul-roll exposure (arrow off, level or behind). Adds a deterrent to Steal and Contest. |

## 2. The Advantage Chain: Evidence by Link

**Evidence:**
- **Link 1 (beat the first defender or force help).** A paint touch is associated with +0.25 to +0.36 PPP (Triano in the NBA; ShotTracker in college). In Cervone et al.'s expected-possession-value example, value climbs from about 1.0 to 1.34 as the ball handler drives into the lane.
- **Link 2 (help creates an open man).** Pelechrinis and Goldsberry: "Approximately half of all the C3s in our data, involved a shooter who was anchored at the corner for at least 4 seconds prior to the shot and received a kick out pass", and "almost one third of the passes come from the area around the basket (basket area, deep paint and baseline)". Lucey et al. found that defensive role swaps in the last 3 seconds predict open threes.
- **Link 3 (the pass and the catch).** Assisted and catch-and-shoot attempts outscore self-created ones (catch-and-shoot 54.1% eFG vs pull-up 45.6%; assisted about +0.16 expected points per shot). 82games' charting found more touches did not raise PPP, but more touches per second did, and fouls and turnovers fell as touches rose.
- **Link 4 (closeout and the next action).** The contest curve is a threshold (point 1 above), so a closeout that arrives in time cancels most of the value of the kick-out. That is why the extra pass after a closeout pays.
- **Advantage decay.** The one direct quantitative trace is Cervone et al.'s example possession. Value peaks at 1.34 when the driver is in front of the rim, falls to 0.77 within moments as he carries the ball past the rim with defenders chasing, then resets to 1.00 when he passes out. Skinner's fit to NBA data implies a new shot opportunity about every 2.8 seconds. I found no public study measuring advantage durability (a "half-life") systematically. Coaching phrases such as "0.5 seconds" are vocabulary for this mechanism, not measurements.

**Reasoning (mine):** In Playmaker an advantage has a precise lifetime: it lasts until the defence has the tokens and the unused Moves or Quick Steps to restore contest reach (factor 1) on the open man. Locks clear at the end of the phase. So an advantage created late in a phase, after the defence has spent its tokens, survives only until the next phase starts. One created early can be erased within the same phase. The measurable warning signs that an advantage is about to be lost:
- defence tokens left ≥ the reaction actions needed to reach the open man;
- the beaten defender's lock expiring at the phase end;
- a helper whose Move is still unused;
- an offensive turn that cannot both pass and shoot before the defence acts.

The computer should read "advantage = look value that the defence cannot restore before the offence can convert", computed from these terms. Counts of open looks do not capture it.

## 3. Defensive Mechanisms

**Evidence:**
- Contest proximity is the main way a defence cuts shot value, with a threshold near 4 ft (point 1 above).
- Defenders change shot frequency and shot efficiency separately (Franks et al.). Rim protection can show up as fewer attempts rather than lower percentages, so judging a defence only by the looks it permits misses part of its value.
- Help placement between two threats is common in the NBA and, in a stylised game model, worse than committing to one (Pelechrinis and Goldsberry).
- Pick-and-roll coverage trade-off: coverages that put two defenders on the ball force a third defender to rotate early. Their use fell from 26.6 to 15.7 per 100 possessions as offences' PPP against them rose from 0.88 to 0.97 (Second Spectrum via theScore). Elite pull-up shooters punish drop coverage; one reported example is Damian Lillard at 1.373 PPP against drop.
- Tracking-era models describe defensive state mainly by distance; Cervone et al. counted a player as "defended" if a defender was within 5 ft.
- **Gap:** I found no public quantitative evidence on how a defender's facing, stance or "ball-you-man" position affects drive or passing lanes. Tracking data record positions, not orientation, and one 2025 gravity analysis notes that attention has to be inferred from geometry.

**Reasoning:** Playmaker's arrows are an explicit, discrete model of orientation, something real analytics has to infer. That is a fidelity strength, but it means the computer must read arrows directly: real-world data cannot calibrate them. Mechanically, an arrow does three things:
1. It blocks a drive lane.
2. It defines the interception lane.
3. It sets the foul cost of stealing or contesting from the wrong angle.

Each has to enter factors 1, 3, 5 and 7 as a case-by-case term. "Conceding by design" corresponds to a defence that holds contest reach on its high-value threats and deliberately leaves the lowest look-value attacker unreached. The coverage budget (factor 4) is exactly the tool for computing that.

## 4. The Three Failing Situations

**(i) The defence ignores a strong drive.**
- *Real read:* the on-ball defender is beaten (hip-to-hip or behind), the driver's skill exceeds his, and the lane to the rim is open. Help must come from the man whose departure costs least.
- *Evidence:* paint touches add about 0.25–0.36 PPP. Rim attempts off drives are about 1.13 PPP, and drives produce about 0.83 points per drive counting kick-outs (small 2013 sample).
- *What the computer must read:* the Dribble win probability against the on-ball defender (tier gap). Whether that defender is locked, and whether he is in front of, beside or behind the carrier relative to the rim. Whether any arrow zone covers the lane. Each helper's reach to the rim tiles within the reaction window. The cost of each help option through factor 9.
- *Likely cause:* the computer judges each attacker's look after the best single cover, so a drive that becomes dangerous only after the Dribble resolves is undervalued. The defence then never pays the help cost early.

**(ii) The offence misses the drive-and-kick to the open corner.**
- *Real read:* the helper's commitment, meaning his distance from the corner and whether he can still close out once the ball is passed, plus a clean lane for the pass.
- *Evidence:* most corner threes are assisted (over 90%), and Pelechrinis and Goldsberry value a 22-ft corner three at 1.14 expected points (1.16 points per shot for wide-open threes in the 2022-23 defender-distance data). Approximately half involve a shooter anchored in the corner for at least 4 seconds who receives a kick-out, and almost a third of passes to the corner come from the basket area, deep paint and baseline.
- *What the computer must read:* factor 2 as a computed value. After the drive, which defenders will spend tokens or moves to stop the rim look? Then, can the corner defender reach adjacency rim-side with what is left? Is the pass lane free of every arrow? Drive, pass and shot take three offensive actions across two offensive turns, plus a defensive reaction, so a one-turn-each search horizon cuts the chain off. The leaf evaluation must contain the second-pass value itself.

**(iii) The guaranteed backdoor cut is not taken.**
- *Real read:* the cutter's defender is denying or facing the ball (overplaying), there is space behind him, the passer has a lane, and the low helper cannot reach the rim in time.
- *Evidence:* cuts are the most efficient half-court play type (1.246 PPP average, around 2016-17; team values of 1.36 in 2025-26).
- *What the computer must read:* paths behind the defender's arrow, an uncovered pass lane, and help reach to the rim tile (factor 7). The current reach map counts squares but not which side of the defender's facing they lie on, so "behind his defender" is invisible. Cut, pass and shot is also a three-action chain, so the same horizon problem as (ii) applies.

## 5. What the Tabletop Omits: Rules Questions for the Designer

These are rules questions, not computer features.
- **Offensive rebounding.** The NBA offensive rebound rate was 22.3% in 2017-18, then an all-time low; Houston reportedly led at 38.8% in 2025-26 (secondary source). Skinner estimates each percentage point of offensive rebound rate is worth about 0.62 points per 100 possessions. Putback possessions score about 1.14 PPP and an offensive rebound is worth about 1.08–1.09 points. Without rebounds, every miss is a total loss. That lowers the value of shooting relative to continuing, especially for low-percentage shots near the rim, and makes rim-protector box-out positioning irrelevant. It is a real fidelity gap, though it scales all shots roughly alike.
- **Transition after turnovers.** Live-ball turnovers give the opponent 1.25–1.28 PPP against 1.06–1.08 after a dead ball, while the half court averages about 0.93. The table's −5 and 2 seconds for an interception, against the app ending the possession, are two different incentive systems. The designer should check that −5 sits in proportion to the game's shot-value scale. I cannot verify this from the description, because shot value is "tile points × roll target".
- **Catch-and-shoot bonus.** Real catch-and-shoot attempts outperform pull-ups beyond what defender distance explains. Playmaker models openness through contest geometry only, so it does not separately reward shooting straight off the catch.
- **Fatigue and the defensive three-second rule.** I gathered no effect sizes. NBA rules stop a defender camping in the paint, but Playmaker's help defenders can stay in the paint indefinitely. That may over-strengthen rim protection compared with the NBA, though not compared with FIBA or NCAA, which have no such rule.

## 6. Shot Timing

**Evidence:**
- Efficiency falls across the shot clock: 112.3 points per 100 possessions at 0-10 s elapsed down to 91.8 at 21+ s. Inpredictable finds a slow decline from about 7 to 21 s, then a sharp drop.
- Skinner (arXiv 1107.5793): the optimal cutoff for shooting equals the expected value of keeping the ball. Turnover risk lowers that cutoff and moves shooting earlier. NBA players appear to undershoot early, and the gap is explained largely by underweighting turnovers. His model is stylised (independent, uniformly distributed shot quality; opportunities arriving at random).
- Goldman and Rao find NBA reservation thresholds falling steadily as the clock runs down and roughly matching continuation value. Their reading is closer to "efficient" than Skinner's.
- Sandholtz and Bornn's simulations show that suppressing one shot type without improving others raises turnovers and shot-clock violations.

**Reasoning, my own calculation with Skinner's recursion:** I assumed one shot look per phase (6 looks), quality uniformly distributed, and a fixed chance of a turnover each time a look is passed up.
- No turnovers: about 42% of shots fall in the first two phases. With two looks per phase, about 47%.
- NBA-like risk of 2.7% per look (Skinner's 100.2 s between turnovers and 2.8 s between opportunities): about 50%.
- 10% per look: about 69%.

So 72% is consistent with basketball logic only if continuing really is that dangerous in Playmaker, or if early looks really are better than late ones. The missing rebound cannot explain it: it makes shooting relatively less attractive, which should push shots later.

**Decision test:**
1. Measure, in played-out games between the best available policies, the probability of a turnover or steal in each phase the offence continues.
2. If it is near 10%, the early shooting is rational. Any fidelity problem then lies in the rules: interception and steal risk higher than basketball's.
3. If it is near 3%, the calibration has absorbed the computer's own weakness. Self-play continuation is worth little because the computer cannot find kick-outs and backdoor cuts, so calibrating against self-play turns that weakness into "shoot early".
4. In that case, recalibrate after adding readings 1–3 below, or against human expert play.

## 7. Prioritised Readings to Close the Gap

1. **Contest reach per potential shooter** (factor 1). It has the largest measured effect, and its threshold shape matches the adjacency rule. Every other reading depends on it.
2. **Value after the help commits** (factor 2). This is the single missing "one pass later" term. It directly addresses failure (ii) and is the likely cause of the null weight-learning results, because it is an interaction no linear count can represent.
3. **Penetration threat with help cost** (factor 3, priced with factor 9). This addresses failure (i). Without it the defence cannot see why it should pay to help.
4. **Paths behind arrows plus denial state** (factor 7). This addresses failure (iii). It is cheap to compute from the arrows and the reach map.
5. **Coverage budget switched on** (factor 4), fed by readings 1–3 as threat prices. This lets the defence concede by design and stop hovering between two threats.
6. **Turnover and steal risk of the current state** (factor 5). It is needed both for judgement and for the shot-timing test in section 6.
7. **Recalibrate continuation value by phase** after readings 1–6, not before. Otherwise the calibration keeps fitting the old blind spots.
8. **Screen state** (factor 8). It matters, but in this engine it mostly works through readings 1 and 3 by blocking squares.

**Why this order (reasoning):** The weight-learning failures suggest the problem is the representation, not the weights. Most of the missing readings are max-over-options and min-over-responses quantities. Giving them to the evaluator as computed expected values (expected points after the defence's best reply) instead of counts should let calibration find a signal.

## Caveats

- **Data quality.** Many effect sizes come from NBA tracking and Synergy figures relayed by secondary analysts, often from different seasons (2013-14 to 2025-26). The subagent could not pull current league-wide figures from NBA.com directly. Treat exact decimals as ±0.02–0.05 PPP.
- **Correlation, not causation.** Paint-touch, assist and play-type effects are observational and partly selection effects. Possessions that reach the paint or end in cuts already had advantages.
- **Unmeasured mechanisms.** No public quantitative evidence was found on facing and stance, on advantage half-life, or on mismatch value by rating gap. For those, the recommendations rest on the game's mechanics and my reasoning.
- **Uncheckable scale.** The shot-timing calculation is a stylised model (independent, uniform shot quality; one look per phase). It indicates a range, not a prediction. The tabletop's point scale (−5 and +5 against tile points × roll target) could not be checked against basketball proportions from the description alone.

## Sources

- breakthroughbasketball: https://www.breakthroughbasketball.com/training/openshooting23data
- Substack: https://brianmccormick.substack.com/p/increasing-offensive-spacing
- nba: https://www.nba.com/news/top-scorers-pull-up-shots-2022-23-so-far
- FanSided: https://fansided.com/2014/07/25/freelance-friday-catch-and-shoot-vs-pull-ups/
- arxiv: https://www.arxiv.org/pdf/2105.12785
- theconversation: https://theconversation.com/data-reveals-the-value-of-an-assist-in-basketball-113893
- basketballimmersion: https://basketballimmersion.com/wp-content/uploads/2021/10/Jay-Triano-Incorporating-Analytics-into-your-Basketball-Offense.pdf
- FanSided: https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/
- Bleacher Report: https://bleacherreport.com/articles/2744786-metrics-101-nbas-10-best-isolation-scorers
- FanSided: https://fansided.com/2015/02/16/play-types-varying-importance/
- Yahoo Sports: https://sports.yahoo.com/nba-offenses-numbers-234100285--nba.html
- fantasyteamadvice: https://fantasyteamadvice.com/nba/teams/boston-celtics/playtypes/2025
- darrylblackport: https://darrylblackport.com/posts/2019-05-02-basketball-stats-i-wish-people-would-stop-using/
- thenbaunderground: https://thenbaunderground.com/analytics/not-all-possessions-are-created-equal
- nateduncannba: https://nateduncannba.com/podcast-episodes/offensive-rebounding-transition-defense-evolving-tradeoff/
- grantland: https://grantland.com/features/department-of-defense/
- lukebornn: http://www.lukebornn.com/papers/franks_aoas_2015.pdf
- 82games: http://www.82games.com/clock.htm
- 82games: http://www.82games.com/comm32.htm
- arxiv: https://arxiv.org/pdf/1107.5793
- researchgate: https://www.researchgate.net/publication/228699670_Allocative_and_Dynamic_Efficiency_in_NBA_Decision_Making
- theScore: https://www.thescore.com/nba/news/2614859
- ESPN: https://www.espn.com/nba/story/_/id/11744634/explaining-gravity-basketball
- nbastuffer: https://www.nbastuffer.com/analytics101/gravity/
- arxiv: https://arxiv.org/html/1408.0777v3
- iainm: http://www.iainm.com/assets/pdf/Lucey-2014.pdf
- 82games: https://www.82games.com/dribbles.htm
- Substack: https://mikeprada.substack.com/p/dropping-drop-coverage
- Substack: https://hardscreenherald.substack.com/p/an-incomplete-theory-of-gravity
- harvardsportsanalysis: https://harvardsportsanalysis.org/2013/11/drive-monta-drive-using-player-tracking-to-analyze-drives-in-the-nba/
- stevenliao: https://stevenliao.me/post/offensive_rebounding_strategy/
- sportsorca: https://sportsorca.com/nba/preseason-offensive-rebounding-rates-small-ball/
- wordpress: https://gravityandlevity.wordpress.com/2016/01/05/the-value-of-improved-offensive-rebounding/
- inpredictable: https://www.inpredictable.com/2015/03/team-pace-and-efficiency-by-possession.html
- lukebornn: http://www.lukebornn.com/papers/sandholtz_ssac_2018.pdf
