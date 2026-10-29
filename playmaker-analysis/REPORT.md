# Playmaker ratings audit: outcome percentages vs real basketball

Every rating pairing in Playmaker resolves to an exact percentage. This audit computes all of them (75 offence cards x 75 defence cards) and puts them beside real outcome rates. No simulation and no win rates. Source documents were read only, never edited.

Two inputs were missing. The design framework document was not supplied, so I applied the requirement hierarchy as written in the brief. No prescribed teams were supplied, which doesn't affect a percentage audit.

---

## The five most important findings

### 1. Dunks never beat layups, so the dunk is a dead option *(ordering error, Fidelity)*
- **The cards:** every card's Dunk rating is at or below its Layup rating (75 of 75). Most cards' Dunk contest is at or above their Layup contest (61 of 75).
- **Result:** a dunk beats a layup in 254 of 16,875 pairing-states (1.5%), so there's no reason to ever dunk.
- **Real basketball:** the dunk is the highest-percentage shot in the game (source DUNK, medium confidence on the ordering; no public league dunk % exists).
- **The PDF agrees with reality:** it says dunks are "harder to block".
- **How far apart:** a tier A big's full contest takes an average dunk to **20%** but an average layup to **38%**.
- **Worst case:** C-2A Rim Protector holds 56% of all shooters to 10% or less on dunks.

### 2. An open mid-range jumper is worth exactly as much as an open three *(ordering error, Fidelity)*
- **Average (orange) shooter, open look:** mid-range 60% x 2 = **1.21 points**; three 40% x 3 = **1.21 points**.
- **Real basketball:** threes beat mid-range by about 0.2 points a shot.
  - All attempts: three 1.09 vs mid-range 0.86 (high confidence).
  - Open looks: wide-open three 1.13-1.16 (medium) vs open mid-range about 0.9-1.0 (derived, low).
- **By card:** 40 of 75 cards (23 of the 54 genuine shooters) get as much or more from an open mid-range shot as from an open three.
- **It contradicts your own board:** the overview's colour zones (green rim and three, yellow mid-range) teach the real order; the ratings undo it.
- **Where the gap is:** open mid-range runs 56-65% by tier. Real all-attempt mid-range is 41.5-44.3%, and real open shots run only a few points above the all-attempt average (wide-open threes are about 2 points above all threes).

### 3. Steals succeed about 3x, and intercepts about 2x, as often as the PDF says *(Fidelity and Legibility)*
- **The PDF's stated odds:**
  - Intercept: green 40-50%, orange 30-35%, red 25%.
  - Steal: green 20-25%, orange 10-15%, red under 10%.
- **What the dice give:** those stated odds only come out of the dice formula when the attacker is rated 19-20. At typical ratings the formula gives:
  - Average steal success per attempt: **46%**, up to 75%. The cards' own bands average 14%, so that's 3.2x.
  - A challenged pass picked off on average **65%** of the time, against a band average of 34% (1.9x).
- **Real basketball points the same way** (low confidence, as no per-attempt data exists):
  - Steals end about 8% of possessions.
  - At most about 2.5% of passes are intercepted.
  - Even the league's best disruptor turns only about half his deflections into steals.

### 4. The best rim protectors are stronger than any real one *(Fidelity)*
- **Full contest at the rim:** tier A bigs hold an average finisher (Layup 18) to **38%**; C-2A holds him to **30%**.
- **Real basketball:** the NBA's best rim protectors allow **46-54%** at the rim (Gafford 46.0%, Wembanyama 48.9%, Gobert 51.8%; medium confidence).
- **Knock-on effect:** an open three beats a fully contested rim attempt for **45% of below-average three-point shooters**. In reality a 30-35% shooter's open three (0.9-1.05 points) is no better than attacking even an elite rim protector (about 1.0 point).

### 5. On threes, a weak-side contest barely matters and a full contest matters twice as much as a real tight one *(relationship error, Fidelity and Legibility)*
- **Real basketball:** going from wide open to tight (2-4 ft) costs about **8 points** (38.4% to 30.1%, medium confidence).
- **In the game:**
  - Weak-side contest costs **1-4 points**, because "Contest minus 3" zeroes most three-point contests (3-point contest ratings are only 2-6).
  - Full contest costs **15-19 points**.
- **Overall:** the average lands about right, but the two contest levels don't mean what they look like.
- **Extreme cases:** SG-3A and SF-5A take 49% of all shooters to 10% or less on a full contest.

---

## Recommended changes

The smallest change per problem, each checked on the full 5,625-pairing table (`output/whatif_candidates.csv`).

| # | Change | Evidence | Serves | Touches | Bends or breaks | Measured effect |
|---|---|---|---|---|---|---|
| R1 | **Cap each card's Dunk contest at its Layup contest minus 1** | Dunk is the highest-% shot (DUNK); PDF says dunks are harder to block | Fidelity; Agency (dunk becomes a real choice); Legibility (card matches its own text) | Dunk contest on 61 cards; PDF dunk-defence range text | None | Dunk beats layup in 6.6% of pairing-states. That covers the 36 cards whose Dunk is within 1 of their Layup (every big plus athletic guards and wings such as PG-5A, SG-5A, SF-1A) and never weaker dunkers. C-2A no longer holds anyone under 10% on dunks |
| R2 | **Shift the Mid-range scale down 2** (9-16 becomes 7-14) | All mid-range 41.5-44.3% (CTG, NBA.com, high); wide-open threes only about 2 pts above all threes | Fidelity; restores the board's colour lesson | Mid-range on all 75 cards; PDF mid-range bands (14-16/11-13/9-10 become 12-14/9-11/7-8); prototype cards O1-O5 | Contested mid-range drops to 24% for an average shooter, which no public data can confirm or rule out | Open mid-range 50% (real 44-49%); open mid / open three points = 0.84 (real about 0.80) |
| R3 | **Lower the Layup contest scale by 3** (5-12 becomes 2-9), applied together with R1 | Best real rim protectors allow 46-54% (medium) | Fidelity; Agency (attacking a set big becomes a real option again) | Layup contest on all 75 cards; PDF layup-defence ranges and position bands; R1 then caps Dunk contest at the new Layup contest minus 1 (150 values in total) | None | C-2A vs an 18 finisher: 45% (Gafford 46%); tier A bigs 53%. Poor shooters prefer the open three over a contested rim attempt in 10% of pairings, down from 45% |
| R4 | **Add +6 to the attacker's side of the Pass and Steal rolls.** Pass: succeeds on d20 ≤ Pass − Intercept + 6. Steal (PDF form): steal on d20 ≥ Handles − Steal + 6. Printed card form: keep the ball on d20 ≤ Dribble − printed Steal + 6, with the printed Steal still the PDF value plus 1 | The PDF's own stated odds; real disruption is rare (low confidence) | Fidelity; Legibility (dice match the printed bands) | No ratings; one constant in two rules | Accessibility bends slightly (one extra number in two rules). Agency risk: see note below | Steal success averages 16% (PDF bands 10-25%); pass success averages 65% |
| R5 | **Weak-side contest = Contest minus 2** (was minus 3) | Tight threes cost about 8 pts (medium) | Fidelity; Legibility (weak and full contests read as two real steps) | No ratings; one rule constant; every shot type | Depends on how far one square is in real life (question Q3) | Weak-side three drop 6.9 pts (real about 8). With R3, weak-side rim drop is 20 pts (was 30) |

**Agency note on R4.** Foul (Steal) stays at 20-55% per attempt, and no public data on fouls per steal attempt exists. After R4 an average steal attempt is 39% foul and 16% steal. Whether steals stay worth attempting then depends on the foul penalty, which is a rule decision. I haven't changed foul odds because I have no evidence to set them.

**Not recommended (evidence too thin to justify a change):**
- **Dribble vs Agility** averages 41% per attempt (52% green vs red, 32% red vs green). The only real figure is 58-61% of defended drives beaten, from tiny Finals samples with a disputed definition.
- **Screen vs Challenge** averages 40%. Bigs' screens hold 51-55% and guards' 29-32%, which is the right order. No public rate of defenders caught on screens exists.
- **Post-ups.** The open post-up (63%) beats the open three, but an unguarded post-up barely exists in real play. Contested post-ups (37% full, 52% weak) bracket the real 42-47% equivalent, and contested post-ups tie contested threes in both the game and reality.

---

## Questions for you before I resolve anything

Each of these changes a finding, so both readings are computed and nothing is resolved.

- **Q1. Steal and foul: one d20 or two?** The example card says "1st ≤ Foul (Stl), 2nd ≥ Handles − Steal".
  - One roll (foul checked first): steal 45%, foul 39%, nothing 16% per attempt.
  - Two rolls: steal 28%, foul 39%, nothing 33%.
  - Finding 3 shrinks from 3.2x the PDF's steal odds to about 2x under two rolls.
- **Q2. Weak-side contest below zero.** 17 card ratings are under 3. I floored "Contest minus 3" at 0. Left unfloored, a weak-side "contest" would raise make % by up to 5 points.
- **Q3. How far is one board square?** I mapped no adjacent defender to wide open (6+ ft), weak side to tight (2-4 ft) and full contest to very tight (0-2 ft). R5 depends on this.
- **Q4. Does the board have corner-three squares?** Real corner threes go in 38.8-39.4% against 35.3-35.5% above the break (CTG, high). One three rating can't show that unless the board does.
- **Q5. PG-5A Block 9 / Foul (Block) 4.** Both are outside the PDF's PG ranges (Block 4-7, Foul (Block) 7-12). They clash with PG-5B/C (5/10, 4/11) and with the example card (7/7). I suspect a typo. No current rule uses Block, so it's flagged and not acted on.
- **Q6. Tier mapping.** I treated Tier A/B/C as green/orange/red. The PDF's Intercept section calls Tier B "above average", which would shift the tier breakdowns.

---

## Detail

### Task 1: Ingest
- **What I extracted:** all 75 cards from PDF pages 43-57, read column by column and checked against page images.
- **File:** `data/cards.csv`, one row per card. It holds every offence and defence rating, a colour tier per stat (from the PDF's bands), position, type and card tier.
- **Parse quality:** no missing fields and no unparsed lines.
- **Logged in `data/ingest_log.csv`:**
  - No card has a Quick Step rating (the prototype cards do).
  - Every Wildcard Trait is "?".
  - The tier mapping above is an assumption.
  - 71 stat values fall in overlapping PDF bands. I labelled these e.g. "green/orange" rather than guessing.

### Task 2: Validation (`output/validation_issues.csv`)

| Check | Count | Notes |
|---|---|---|
| Outside the PDF's own range | 28 | 20 are centres' Three (4-5, PDF minimum 6) and Long 2 (4-5, minimum 7). Those values are realistic for non-shooting bigs, so **fix the PDF range, not the cards**. Also: C-2C and C-5C Free Throw 10 (minimum 11); SG-3A, SF-5A, PF-3A and C-2A Mid-range contest 8 (top band 6-7); PG-1C Height 4; C-1C Vertical 5.0; PG-3C Post 8 |
| Outside the PDF's position range | 22 | Includes PG-5A Block/Foul (Block) (Q5); PF-3A/B Steal 4 (PF range 1-3) |
| Lower tier better than higher tier | **0** | Tiers are cleanly ordered on every stat |
| Layup never below 17 / Dunk never below 14 | 0 breaks | |
| PDF narrative vs card values | 34 | E.g. 7 of the 10 Post ratings the narrative quotes are 1 higher than the cards; Foul (Steal) for SG-2/SG-3 is 5/6/7 against the text's 4/5/6; C-2 Layup contest is 12/11/9 against 14/12/10. Cards are the source of truth, so **update the narrative** |
| Example card (p.42) vs PG-5A | 18 values, 5 colours | E.g. Dunk contest 13 vs 7, Mid-range 10 vs 13; Floater 14 is printed orange but the band says green |
| Band gaps and overlaps | 82 | Height 7.5 has no band (11 cards); Foul (Steal) bands overlap at 6 and 8; Foul (Block) at 7 and 9; Screen Defence at 6 |
| Tier-step "typically" rules | 154 (low) | Soft rules: e.g. Intercept often steps 6/6/5 where the text says 1 point per tier |

Other notes:
- SG-3B/C Speed drops to 7, against Tier A's 10.
- No card has a Three above 11, although the PDF's elite band runs to 13.

### Task 3: Benchmarks (all in `scripts/benchmarks.py`, listed in `output/sources.csv`)

| Action | Best real figure | Confidence |
|---|---|---|
| Rim, all attempts | 65-67% (CTG, NBA.com, DataDunk) | high |
| Rim, open | about 85-90% (one older study) | low |
| Rim vs elite protector | 46-54% (NBA tracking via Stat Defender, Sportskeeda) | medium |
| Floater / short mid | 43-45% (CTG, NBA.com) | high |
| Mid-range | 41.5-44.3% (CTG, NBA.com) | high |
| Long 2 | 41.5-42.3% (CTG) | high |
| Corner 3 / above the break | 38.8-39.4% / 35.3-35.5% (CTG) | high |
| All threes | 36.2-36.6% (CTG, NBA.com) | high |
| Wide-open / tight three | 37-38.6% / 30.1% (NBA tracking via McCormick, CBS); EuroLeague catch-and-shoot 37.6%, pull-up 32.3% | medium |
| Post-up | 0.85-0.93 PPP (Synergy reports) | medium |
| Free throw | 75.5% (FIBA World Cup 2023) | high |
| Isolation | 0.78-0.90 PPP, 47% eFG; EuroLeague 0.78-0.98 | medium |
| Drive success | defenders beaten on 58-61% of drives (Finals samples) | low |
| Pick-and-roll | ball handler 0.85-0.93 PPP, about 11% turnovers; EuroLeague 0.94-1.01 | low-medium |
| Steals, turnovers | about 8% / 14% of possessions (NBA 2024-25) | medium |
| Pass interception | at most about 2.5% of passes; about 5-7% deflected | low |
| Fouls per steal attempt | **no public data** | none |
| Defender caught on a screen | **no public data** | none |
| Dunk % | **no public figure**; sources agree it is the highest-% shot | none (ordering medium) |
| Contested 2-pt jumpers | **no public open/contested split**; open values derived from the three-point gap | low |

FIBA data is used where it exists (free throws, two-point and turnover context, EuroLeague shooting and pick-and-roll). Shot tracking by zone and defender distance is only public for the NBA. Two hosts (FIBA's PDF server and Basketball-Reference) are blocked in this environment, so FIBA figures come from search excerpts of FIBA's own report.

### Task 4: Outcome tables
- **`output/outcome_table_shots.csv`:** make % for 7 shot types at open, weak-side and full contest, all 5,625 pairings.
- **`output/outcome_table_actions.csv`:** Dribble, Pass, Screen, Steal (PDF rule and printed-card rule), Foul (Steal), and the combined steal-attempt outcome under both readings of Q1.
- **Steal conversion check:** the printed-card rule (keep on ≤ Dribble − (Steal + 1)) gives exactly the PDF rule's odds in all 220 integer cases and all 5,625 card pairings (`output/steal_conversion_check.csv`). It holds at the clamps too: when Handles − Steal ≤ 1 both rules always steal; when it exceeds 20 neither ever does.

### Task 5: Game vs real, by tier and position (`output/benchmark_comparison.csv`)

Shots, by shooter tier (contested by realistic defenders: bigs at the rim, anyone on jumpers):

| Shot | State | Green | Orange | Red | Real | Verdict |
|---|---|---|---|---|---|---|
| Layup | open | 92 | 90 | 86 | 75-90 (low) | aligned |
| Layup | full | 47 | 45 | 41 | 46-54 vs elite (medium) | aligned on average; too strong vs green bigs (38) |
| Dunk | full | 33 | 28 | 25 | highest-% shot | **reversed vs layup** |
| Mid-range | open | 65 | 60 | 56 | 44-49 (low, derived); 41.5-44.3 all | **12-16 pts high** |
| Long 2 | open | 48 | 45 | 40 | 43-47 (low, derived) | aligned |
| Three | open | 43 | 40 | 37 | 37-38.6 (medium) | green 4 pts high, others aligned |
| Three | weak | 41 | 38 | 35 | 30-33 tight (medium) | 2-8 pts high |
| Three | full | 26 | 23 | 21 | no data (below 30 expected) | plausible |
| Free throw | | 78 | 73 | 68 | 75.5 (high) | aligned; C 64%, SG 81% (the right order) |

Actions, offence tier vs defence tier (mean % per attempt):

| Action | Green vs red | Orange vs orange | Red vs green | Same position (PG / C) | Real |
|---|---|---|---|---|---|
| Dribble | 52 | 41 | 32 | 49 / 38 | 58-61% of defended drives (low) |
| Pass | 44 | 35 | 27 | 44 / 31 | interceptions rare (low) |
| Screen | 53 | 40 | 29 | 29 / 55 | no data |
| Steal (PDF rule) | 38 | 47 | 53 | 37 / 53 | PDF bands 10-25%; steals about 8% of possessions |
| Foul (Steal) | by defender tier: 34 / 39 / 44 | | | 35 / 44 | no data |

### Task 6: Relationships (`output/rel_*.csv`)

- **Zone ordering, average shooter, open look (points per shot):**
  - Game: layup 1.80 > dunk 1.63 > post 1.26 > mid-range 1.21 = three 1.21 > floater 0.97 > long 2 0.90.
  - Real, all attempts: rim 1.32 > three 1.09 > post 0.89 ≈ floater 0.88 > mid-range 0.86 > long 2 0.84.
  - Two errors: the dunk/layup reversal (finding 1) and the mid-range/three tie (finding 2). Rim first and long 2 last match.
- **Contest size:**
  - Rim: full contest removes 37-52 pts (by defender tier) against about 31-44 real from open to elite-contested. Too strong at the top end (finding 4).
  - Dunk: full contest removes 47-62 pts, the most of any shot. Reality has the dunk as the least contestable shot.
  - Threes: see finding 5.
- **Tier separation:**
  - Green vs red within a type is cleanly ordered.
  - The gaps are small on Three (1.1 rating points, 5.6 pts of make %), Steal (1.1) and three-point contest (0.9, with 6 types showing no gap).
  - On threes a full contest moves make % 3x more than the shooter's tier. In real basketball elite shooters sit about 8-10 pts above average (medium), about the same as a tight contest (8). Worth a look once R5 is settled.
- **Position:** handles, passing, screens, pressure defence, post moves and rim protection all rise or fall by position in the real direction.
  - One exception: centres contest mid-range (5.5) better than guards (4.6-5.1).
  - The prototype X5 Rim Protector contests Long 2s at 7, the highest value anywhere.
  - Real tactics have bigs in drop coverage conceding pull-ups, but I found no tracking number to size it. Flagged, not recommended.

### Task 7: Dominant pairings (`output/dominant_pairings.csv`)

- **Actions:** no action reaches near-certainty or near-zero outside extreme mismatches.
  - The range is 5-80%, and fewer than 1.5% of pairings sit at 10% or below or at 75% or above.
  - The extremes are real-world extremes: PG-1A dribbling past C-1C 80%; PF-1C dribbling past PG-3A 5%.
  - One exception: a Steal of 75% on poor-handling bigs (PF-1C vs PG-3A), which real steal rates don't support (finding 3).
- **Shots near zero:**
  - C-2A takes 56% of all shooters to 10% or less on dunks (fixed by R1 and R3) and 55% on floaters. Floater specialists (13-15) keep 30-40%, so floaters stay viable for the players who use them.
  - Elite wings take 49% of all shooters to 10% or less on threes. 25 defenders produce at least one 0% three, all against 12 bigs rated 4-6 on threes (9 of them below the PDF's own minimum of 6).
  - Real basketball has no defender who holds any zone near zero.

### Prototype cross-check (`output/prototype_matches.csv`, `output/prototype_differences.csv`)

| Prototype | Nearest PDF card | Differences |
|---|---|---|
| O1 Combo PG (avg) | PG-4B | Long 2 11 vs 9; Three 10 vs 9 |
| O2 Two-Way Guard (avg) | SG-2B | Pass 15 vs 14; Long 2 11 vs 10; Three 10 vs 9 |
| O3 Point Forward (avg) | SF-4B | Long 2 11 vs 10 |
| O4 All-Rounder (above avg) | PF-4A | Long 2 11 vs 10 |
| O5 Playmaker C (below avg) | C-4C | Three 6 vs 8; FT 13 vs 14 |
| X1 Attacker/Slasher | PG-5B | identical |
| X2 Sharp Shooter | SG-1B | Mid-range contest 3 vs 4 |
| X3 Scoring Machine | SF-1B | Long 2 contest 4 vs 3 |
| X4 Pick 'n' Pop | PF-5B (PF-2B equally close) | Mid-range contest 4 vs 5; Long 2 contest 4 vs 3 |
| X5 Rim Protector | C-2B | **Long 2 contest 7 vs 4**; Three contest 5 vs 4 |

- **Matches:** every prototype matches its named type, and the offence tiers match the stated tiers. The defence cards are all Tier B equivalents.
- **QS:** prototype QS equals the Speed mapping I logged (11-12 → 2, 9-10 → 1, 8 or below → 0) on all 10 cards. The PDF can carry QS as a derived stat.
- **Patterns:**
  - The prototypes raise Long 2 to 11 on all four guards and forwards. Open Long 2 jumps to 55% and drifts away from the real 41.5-42.3%.
  - X5's Long 2 contest of 7 is outside the PDF's band (green 5-6) and runs against the real role of a rim protector.
- **Foul (Block):** printed on every prototype defence card but used by no rule. If a shooting-foul rule used it the way the PDF describes (roll ≤ Foul (Block) on a block attempt), X5's 5 would mean a 25% foul chance against 50% for the others. There's no real data to check either figure.

### Limits
- Open and contested benchmarks for two-point jumpers are derived, not measured. Their verdicts carry low confidence.
- The contest-state mapping (Q3) is my assumption.
- Action benchmarks are proxies: real data counts per possession or per pass, while the game rolls per attempt.
- A -5 turnover is a quarter of the value of a real possession (about 1.0-1.1 points, or about 20 game units). That's a rule choice ("play continues"), outside a ratings audit, so it's noted and left alone.

---

## Files

- `data/cards.csv`: all 75 cards
- `data/ingest_log.csv`: ambiguities found during extraction
- `output/outcome_table_*.csv`: every pairing's percentages
- `output/benchmark_comparison.csv`: game vs real by tier and position
- `output/pdf_stated_vs_formula.csv`: the PDF's printed odds vs its dice rule
- `output/rel_*.csv`: relationship checks
- `output/dominant_pairings.csv`
- `output/whatif_candidates.csv`: each recommendation measured
- `output/validation_*.csv`
- `output/prototype_*.csv`
- `output/sources.csv`
- `scripts/`: every assumption in `config.py`, every source in `benchmarks.py`. Run `PLAYMAKER_PDF=/path/to/pdf python3 scripts/run_all.py`.

## Sources

| Key | Source |
|---|---|
| CTG | [Cleaning the Glass, league shooting by location](https://cleaningtheglass.com/stats/league/shots) |
| NBA_ZONES_2022 | [NBA.com, Stats leaders: top rim protectors (Dec 2022)](https://www.nba.com/news/stats-leaders-top-rim-protectors-dec-2022) |
| NBA_SURVEY_2024 | [NBA.com, 2023-24 stats survey](https://www.nba.com/news/2023-24-nba-stats-survey-league-scoring-averages) |
| NBA_MID_2023 | [NBA.com, offensive efficiency rising](https://www.nba.com/news/2023-24-storylines-no-10-offensive-efficiency-rising) |
| WIDE_OPEN_3 | [B. McCormick, Increasing offensive spacing](https://brianmccormick.substack.com/p/increasing-offensive-spacing); [CBS Sports, wide-open 3s](https://www.cbssports.com/nba/news/wide-open-3s-and-ranking-how-each-nba-team-fared-at-making-defenses-pay) |
| EL_3PT | [EuroLeague, threes and the EuroLeague](https://www.euroleaguebasketball.net/euroleague/news/stats-review-threes-and-the-euroleague) |
| RIM_PROTECT | [Stat Defender, DFG% at the rim 2024-25](https://x.com/statdefender/status/1885751774134607878); [Sportskeeda DPOY tracker 2023-24](https://www.sportskeeda.com/basketball/nba-defensive-player-year-dpoy-rankings-2023-24-top-5-candidates-week-22-ft-bam-adebayo) |
| RIM_LEAGUE_2026 | [DataDunk, rim protection](https://datadunknba.substack.com/p/nba-rim-protection-2026-27-all-30-teams) |
| OPEN_10FT | [The Spax, expected eFG%](https://www.thespax.com/nba/shooting-efficiency-reimagined-expected-effective-field-goal-percentage/) |
| POSTUP_PPP | [Nylon Calculus, Synergy play types](https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/); [The Ringer, post-ups](https://www.theringer.com/2019/12/02/nba/post-up-dead-nba-brooklyn-nets-joel-embiid) |
| FIBA_WC23 | [FIBA, World Cup 2023 scouting report](https://assets.fiba.basketball/image/upload/documents-corporate-studies-and-facts-fiba-scouting-report-fiba-basketball-world-cup-2023.pdf) |
| ISO_PPP | [Best Ball Stats, isolation 2016-21](https://bestballstats.com/2021/06/13/isolation-basketball-an-inefficient-yet-necessary-offense/); [Bleacher Report](https://bleacherreport.com/articles/1988354-in-defense-of-the-nba-isolation-play) |
| EL_ISO_PNR | [EuroLeague, pick-and-roll trends](https://www.euroleaguebasketball.net/news/stats-review-pick-and-roll-trends); [JHSE end-of-game play types](https://www.jhse.ua.es/article/view/efficacy-different-play-types-endgame-close-euroleague-games) |
| PNR_TEAM | [FantasyTeamAdvice, 76ers play types 2023-24](https://fantasyteamadvice.com/nba/teams/philadelphia-76ers/playtypes/2023) |
| BLOWBY | [EssentiallySports, Finals blow-bys](https://www.essentiallysports.com/nba-active-basketball-news-victor-wembanyama-posting-worse-numbers-than-luka-doncic-in-category-lakers-star-gets-criticized-for-los-angeles-lakers-san-antonio-spurs-new-york-knicks/) |
| PACE_2025 | [SportsEthos, 2025 pace report](https://sportsethos.com/top-posts/fantasy-basketball-draft-guide-2025-pace-report/) |
| PASSES | [NBA.com team stats](https://www.nba.com/stats/teams); [TeamRankings steals](https://www.teamrankings.com/nba/stat/steals-per-game) |
| DEFLECT | [NBA.com, 2024-25 standout stats](https://www.nba.com/news/5-standout-stats-2024-25-season); [Inquirer, Sixers deflections](https://inquirer.com/sixers/sixers-lead-nba-deflections-nick-nurse-doc-rivers-toronto-raptors-20231229.html) |
| DUNK | [Wikipedia, Slam dunk](https://en.wikipedia.org/wiki/Slam_dunk); [RunRepeat, dunk stats](https://runrepeat.com/82-stats-on-dunks-in-the-nba) |
| THREE_LEADERS | [Wikipedia, NBA annual 3P% leaders](https://en.wikipedia.org/wiki/List_of_NBA_annual_3-point_field_goal_percentage_leaders) |
