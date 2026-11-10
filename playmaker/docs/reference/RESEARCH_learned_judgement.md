# Research: giving Playmaker strong positional judgement (10 November 2026)

This report is from a research session run for Shaun, given here because this session can't reach outside websites. Claims about other engines come from primary or near-primary sources. Statements about Playmaker itself (compute, sample sizes, fit) are estimates and are marked as such. Treat it as a strong recommendation, not a script.

## Bottom line

Keep the rule-derived readings Playmaker already computes, but stop hand-combining them: fit their weights from data. The recommended route:

- a phase-specific additive model (linear, or GA2M-style), trained on whole-possession rollout outcomes mixed with deeper-search values;
- a cheap learned move-ordering prior, so moves like the kick-out make it into the search.

This has the best evidence for a game that searches 1 to 2 team-turn pairs, must answer in under a second in JavaScript, and must explain itself.

## Key findings

1. **The strong dice-game engines got their judgement from learned evaluation, not deeper search.**
   - TD-Gammon 2.1: 1.5 million self-play training games, 80 hidden units, 2-ply search. It finished −1 point over 40 games against Bill Robertie.
   - GNU Backgammon's (gnubg) contact network: 250 inputs, 128 hidden units, 5 outputs.
   - eXtreme Gammon (XG): its author said XG2's retraining "required the analysis of 73 trillion positions… several months" on up to 8 cores.
   - Hauk, Buro and Schaeffer: with good evaluation functions, good backgammon play "does not require deep searches".
2. **Linear models over good features are enough to reach top strength.**
   - Logistello beat Othello world champion Takeshi Murakami 6-0 in August 1997. Its evaluation was linear over pattern tables: about 1.2 million weights across 13 game stages, fitted by sparse linear regression to about 17 million labelled positions.
   - Meep (chess): a linear evaluation, 1,812 features with about 100 active per position, trained from random weights by TreeStrap self-play. It scored 1950 to 2197 in ICC blitz and 13.5/15 against International Masters (Veness et al., NeurIPS 2009). TreeStrap learned effective weights "in just a thousand training games" (internal Elo 2157±31, against 1068±36 for TD-Leaf).
3. **Labels from rollouts and deeper search beat pure self-play on efficiency.**
   - gnubg's recipe: collect positions where the 0-ply and 2-ply choices disagree, roll them out, train supervised.
   - A hobbyist (not peer-reviewed) report: 400k rollout-labelled positions matched a net trained on 3 million self-play games.
4. **Team sports and multi-unit games: domain knowledge still wins, and naive search or RL is weak.**
   - In Bot Bowl (Blood Bowl AI: turn-based, grid, dice, team sport), scripted bots won four of five competitions. GrodBot (scripted) went 34 of 40 in 2019, and the A2C RL agent won none.
   - The one learned winner (MimicBot, 2021) started by imitating a scripted bot, then used RL.
   - MCTS bots played better *without* random rollouts, because random Blood Bowl actions are risky.
5. **Additive, decomposed value models can be accurate and legible.**
   - GA2M/EBM models "substantially close the accuracy gap" to black-box models (Lou, Caruana, Gehrke, Hooker).
   - Decomposed EPV in basketball (Cervone et al.) and soccer (Fernández, Bornn, Cervone) is built for interpretation, with calibrated components.
   - Linear probes find many human chess concepts inside AlphaZero's network (McGrath et al., PNAS 2022). Probes show correlation, not cause.

## Q1. How the reference engines got their judgement

| Engine | Features | Learning target | Data | Form | At play | Dice |
|---|---|---|---|---|---|---|
| TD-Gammon | Raw board (198); later versions added expert features (hit chance, blockade strength) | Game outcome by TD(λ) self-play (λ about 0.7) | 200k games (raw net); 300k (v1.0); 800k (v2.0); 1.5M (v2.1) | 1 hidden layer, 40 to 80 units | 1-ply (v1.0), 2-ply (v2.x) | Expectation over the 21 rolls; random dice make self-play explore |
| gnubg | 250 inputs; separate nets for contact, crashed and race | TD first, then supervised on rollout labels, focused on 0-ply against 2-ply disagreements | About 100k benchmark positions held out | 250-128-5 MLP | 0-ply in fractions of a millisecond | Plies average over rolls; rollouts with variance reduction |
| XG | Not published | Retraining with heavy search and rollouts | 73 trillion positions analysed | Neural net | 3-ply standard | Rolls plus truncated rollouts |
| BGBlitz | Not published | Self-play RL | Over a dozen nets, about 2 months each, over 90M games | Several nets | About 2.8M positions per second | Rolls |
| Logistello | Pattern tables plus parity | Game results / disc differentials | About 17M positions, 13 stages | Linear (sparse regression) | 280k nodes per second | n/a |
| NNUE (Nasu 2018, Stockfish) | Sparse piece-square (HalfKP) | Search scores at moderate depth, blended with result | Millions, later billions | 41024→256×2→32→32→1, quantised | Incremental first layer | n/a |

Pollack and Blair matched TD-Gammon-like play with simple hill-climbing. They concluded that the dice-driven setup, not TD itself, was key: dice smooth the value function and force exploration. That's good news for Playmaker.

**Fit for Playmaker (reasoning):**

- **Best fits:**
  - Logistello-style per-phase linear regression: cheap, legible, low data;
  - gnubg's rollout plus disagreement labelling: a possession is short and ends in exact points.
- **Poor fit: NNUE's incremental trick.** A team turn moves several pieces and changes coverage globally. Playmaker's cost is computing features, not combining them.
- **Later challenger: a TD-Gammon-sized net (40 to 128 hidden units).** A few thousand multiply-adds in JavaScript, well under 1 ms, but less legible.

## Q2. Learning targets

| Target | Evidence | For | Against | Data (Playmaker estimate) |
|---|---|---|---|---|
| TD(λ) self-play | TD-Gammon; KnightCap "was unable to learn effectively from games of self-play" (per Veness et al.) | No labels needed | Slow, noisy, can lock in the engine's blind spots | 10⁵ to 10⁶ possessions |
| Search bootstrapping (RootStrap, TreeStrap) | Meep: linear, from random weights, to master level | Uses every node of the existing search | Only as good as the deeper search, which uses the same evaluation | Comes free with search; thousands of games |
| Monte Carlo rollouts | gnubg, XG; the 400k parity claim | Unbiased with respect to the rollout policy; true points; "learns from data and makes mistakes" | Noisy (dice); biased by the rollout policy's mistakes | 100 to 1,000 rollouts per position; 10⁴ to 10⁵ positions |
| Disagreement mining | gnubg: "if move_0ply != move_2ply → store both resulting positions", roll out, train | Spends compute on exactly the blind spots | Needs a deeper oracle; skewed to hard cases | A few thousand per round |
| Human games | Neurogammon was surpassed by TD-Gammon; MimicBot shows imitation is a good warm start | Brings in basketball sense quickly | Little Playmaker data exists | Probably unavailable |

**Uncertainty:**

- a bootstrap ensemble (refit the linear model on about 20 resamples): the spread shows which explanations are reliable;
- Bayesian linear regression: predictive variance per position, giving "clearly better" against "close call";
- rollout standard errors on each label, with labels weighted by inverse variance.

## Q3. Keeping it explainable

- **Additive models over named features (recommended core).**
  - A linear model, or a GA2M/EBM with shape functions per feature and a few pairwise interactions, explains itself exactly: each contribution is weight × (value − average).
  - Playmaker's features are already basketball concepts.
- **Decomposed EPV as the template.** Playmaker's look = arrival × release × shot value is already a decomposition. Learning should fit how the pieces combine and correct each one, not replace the structure.
- **Networks with attribution:** SHAP and integrated gradients can be unstable. If a net is used, distil it back into a GA2M.
- **Fit with Shaun's rules:** weights come from data, so no hand-set numbers. Per-phase weights, shape functions and interactions give case-by-case judgement ("it depends") without fixed distances.

## Q4. Learning which moves to consider

- **The candidate problem.** If the kick-out or backdoor cut is pruned or ranked low, no evaluation fix finds it. That's the likely cause of failures that persist in every setting (reasoning).
- **Evidence:**
  - Churchill and Buro's Hierarchical Portfolio Search builds team moves from per-unit partial scripts, then searches combinations. Prismata's AI reached the top 25% of the human ladder.
  - Ontañón's naive sampling treats a multi-unit move as a combinatorial bandit (one local bandit per unit plus a global one). It beat other samplers as branching grew.
  - Ontañón's Informed MCTS used learned Naive Bayes action models and "significantly outperform[ed]" the previous best in µRTS.
  - Gumbel AlphaZero (Danihelka et al., 2022) guarantees policy improvement when the visited actions are evaluated correctly, and improves "planning with few simulations". Gumbel-top-k with sequential halving at the root fits a tiny budget.
- **Proposal (reasoning):** a factorised linear policy scoring each player's candidate action (cut, drive, kick-out pass, screen, Contest) from the same named features, trained to imitate deeper search or the rollout-best turn. Use it to:
  - guarantee each player's top-k actions appear among the candidates;
  - order moves for pruning;
  - sample root candidates Gumbel-style.

## Q5. Multi-unit team turns

- **Bot Bowl:**
  - I (2019): scripted GrodBot won, 34 of 40; the A2C agent won none.
  - II: scripted Minigrod won. Gotebot (A2C, self-play, curriculum, plus two scripted rules) took the ML prize.
  - III (2021): MimicBot won, learned by behavioural cloning of a scripted bot, then RL. Its author notes the Bot Bowl II A2C bot "could win only 70% of the time against a random bot".
  - IV and V: scripted Drefsante won, even after MCTS bots entered.
  - The MCTS tutorial: MCTS did better without rollouts on medium and large boards.
- **Lesson:** domain-knowledge evaluation plus structured actions beats naive search or RL. Learning helps most when started from that knowledge. Playmaker's readings are that knowledge.

## Q6. Practical plan (estimates; measure before relying on them)

- **Compute:**
  - A possession is 12 to 24 decisions. With a cheap rollout policy (10 to 20 ms per decision in Node), one possession costs well under a second: roughly 5,000 to 20,000 per core-hour.
  - Labelling 50,000 positions × 200 rollouts is 10⁷ possessions. Cut that with variance reduction (common random numbers across a position's candidate moves; the current evaluation as a control variate).
- **Data size:** with 50 to 300 features (per-phase weights), 20k to 100k rollout-labelled positions should be ample for a linear or GA2M model. A small net needs 10⁵ to 10⁶.
- **Validation:**
  - The exam: with 19 boards, 10 to 11 passes is within noise. Grow it to 150 to 300 positions whose answers come from deep rollouts with standard errors. Keep the 19 hand boards as a teaching set, and roll them out too: a hand label can be wrong.
  - Head-to-head: paired possessions on the same starts and dice seeds, engines swapped. Report the mean points-per-possession difference with a 95% CI. n ≈ (1.96·σ_d/δ)²; for σ_d about 1.2 and δ = 0.05, n is about 2,200 pairs. Add win rate with a Wilson interval and SPRT early stopping.
- **Speed:** a linear model over 100 to 300 features takes microseconds. The cost is computing the features (reach maps, the coverage LP): cache, update incrementally, warm-start the LP.
- **Two engines, one set of weights:**
  - one versioned JSON weight file (feature names, phase, weights, knots, normalisation, hash);
  - golden tests that Python and JS give identical features and evaluations within 1e-9 on about 1,000 positions;
  - float64 with a fixed summation order in both;
  - fail on any feature-name mismatch.

## Q7. Rival approaches

- **Better search alone.** Star2 pruning took backgammon from depth 3 to 5 (Hauk et al.). Monte Carlo *-Minimax (sampling dice outcomes) beat classic versions in every case tested (Lanctot et al.). But strong evaluation made deep search unnecessary, and Playmaker's own data (odd/even swings, no gain from depth) agrees. Worth having as a cheap supplement, not the main lever.
- **Better hand features.** The goal layer added nothing measurable; the problem is weighting and combining. New features are cheap to test once weights are learned: a useless one gets a near-zero weight.
- **Full AlphaZero-style network plus MCTS.** Most compute, least explainable, weakest team-sport evidence. Not now.
- **Best-evidenced:** a hybrid of learned additive evaluation, a learned candidate prior, and modest search additions.

## Recommendations

- **(a) Form:** V(s) = phase average + Σ phase-specific wᵢ·fᵢ(s), plus a few learned pairwise interactions. Features:
  - the continuation readings (each attacker's look, arrival and release chances, shot value, reach counts, coverage-LP slack per threat, tempo);
  - each advantage at each stage;
  - the potential deltas.

  A small MLP only as a later challenger.
- **(b) Target:** λ·(depth-2 search value) + (1−λ)·(mean points over N rollouts), with λ chosen by validation. Sample from self-play with move noise; oversample 1-pair against 2-pair disagreements; add TreeStrap updates.
- **(c) Integration:** replace the hand-combined continuation with the learned V at the horizon, search unchanged at first. Goal and advantage readings become features. A near-zero weight is evidence, not failure.
- **(d) Explanations:** explain each move by the top 3 contribution changes between the chosen move and the runner-up. The prior adds "why this candidate was considered".
- **(e) Uncertainty:** a 20-model bootstrap ensemble or Bayesian linear regression. "Close call" when the top two intervals overlap; flag explanations whose sign flips across the ensemble.
- **(f) Stages:**
  - **Stage 0:** the rollout-labelled exam (150 to 300 positions) and the paired head-to-head harness; re-score the current engine. Checkpoint: a baseline with CIs.
  - **Stage 1:** linear per-phase weights fitted to rollout labels. Checkpoint: beats the current engine on the expanded exam (non-overlapping bootstrap CI) and wins head-to-head at p < 0.05.
  - **Stage 2:** disagreement mining, TreeStrap, the factorised prior, candidate guarantees. Checkpoint: the kick-out, backdoor and strong-drive boards pass; head-to-head gains again.
  - **Stage 3:** GA2M interactions against a small MLP; adopt the MLP only if it wins clearly *and* a distilled GA2M keeps most of the gain.
- **(g) For an AI coding agent:**
  1. **First:** the rollout labeller with variance reduction and the expanded exam; ridge regression per phase on the existing features. *Stop* if at about 50k labels the held-out R² on rollout values fails to beat the hand-combined continuation. The features are missing information: go to feature work.
  2. **Second:** the disagreement-mining loop plus the per-player action prior. *Stop* when a round adds under 1% on the exam and no significant head-to-head gain, two rounds running.
  3. **Third:** GA2M interactions, an MLP challenger, Star2 or sparse-sampling search. *Stop* when the paired CI includes zero at about 2,000 pairs, or the JS evaluation passes 1 ms on the phone profile.

## Caveats

- The Playmaker compute rates, data sizes and λ are estimates, not measurements.
- The 400k parity result and some XG and BGBlitz details are non-peer-reviewed or vendor sources.
- Rollout labels inherit the rollout policy's blind spots: if the rollout policy never kicks out, rollouts undervalue the kick-out. Iterate the policy, add exploration noise, and check key boards by hand.
- The Bot Bowl evidence comes from a small field (about 5 bots a year). Treat it as directional.

## Main sources (titles, for searching)

- Tesauro, "Temporal Difference Learning and TD-Gammon".
- GNU Backgammon manual and the bug-gnubg mailing list (training on disagreements).
- Buro, "The Evolution of Strong Othello Programs"; Logistello logs.
- Veness, Silver, Uther, Blair, "Bootstrapping from Game Tree Search" (NeurIPS 2009).
- Pollack and Blair, "Why did TD-Gammon work?" (NeurIPS 1996).
- Lou, Caruana, Gehrke, Hooker, "Accurate Intelligible Models with Pairwise Interactions" (KDD 2013); InterpretML EBM docs.
- McGrath et al., "Acquisition of chess knowledge in AlphaZero" (PNAS 2022).
- Churchill and Buro, "Hierarchical Portfolio Search in Prismata" (Game AI Pro 3).
- Ontañón, "Combinatorial Multi-armed Bandits for Real-Time Strategy Games"; "Informed Monte Carlo Tree Search for Real-Time Strategy games".
- Danihelka et al., "Policy improvement by planning with Gumbel" (ICLR 2022).
- Justesen et al., the Bot Bowl I to V pages and papers.
- Hauk, Buro, Schaeffer, "*-Minimax performance in backgammon".
- Lanctot et al., "Monte Carlo *-Minimax Search".
- Stockfish, "Introducing NNUE evaluation".
