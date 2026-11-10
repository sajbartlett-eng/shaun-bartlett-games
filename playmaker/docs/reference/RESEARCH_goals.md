# Research: goals for Playmaker's decision engine (10 November 2026)

This is the first research session, which shaped the goals design (`GOALS_DESIGN.md`) and steps 12 to 16. It's given here so the reasoning behind today's readings is available. The fit assessments are reasoning by analogy; no source tested these methods in a turn-based basketball game.

## Bottom line

Goals should be a computed layer that creates candidate moves and progress terms inside one value function, not a separate planner on top of the search. The design should have:

- a strong evaluation computed from the board;
- search narrowed to moves that pursue a goal;
- evaluation only at quiet points;
- explanations taken from the terms the engine actually used.

## Q1. Computing advantage from positions

| Method | What it computes | Evidence | Weakness | On Playmaker's grid |
|---|---|---|---|---|
| EPV (Cervone, D'Amour, Bornn, Goldsberry) | Expected points of a possession from all 10 players and the ball, macro transitions (pass, shot, turnover) plus micro movement | A Miami Heat example: EPV starts near 1.0 and peaks at 1.276 at the shot | Needs huge tracking data; credits off-ball players only indirectly | Playmaker has the transition model in its rules; its structure (value = Σ action probability × value after) is what the continuation approximates |
| Pitch control and OBSO (Spearman 2018) | Per location: P(ball goes there) × P(attackers control it on arrival) × P(score from there) | Used by Liverpool FC | Physics fitted on limited data; weak far from goal | Very cheap: arrival time becomes a count of Moves and Quick Steps per square (the reach map) |
| Space occupation and generation (Fernández and Bornn 2018) | Space quality = control × value; "space generation gain" credits dragging defenders away | Top players occupy higher-value space; based on a single game | Gaussian influence, continuous | Cheap: the change in team-controlled value when a defender moves. The direct fix for "clearing the lane reads as standing still" |
| Shot quality (qSQ/ESQ, Chang, Maheswaran et al., Sloan 2014) | Expected value of a shot by an average shooter, separate from skill (EFG+ = EFG − ESQ) | Best paper, Sloan 2014 | Proprietary features | Keep the separation: look quality (position) against finisher (card) |
| Gravity (STATS/ESPN 2014; WNBA 2026) | Defensive pressure an attacker draws against what's expected for the spacing | WNBA: 25 pairwise defender-attacker relationships, 25 times a second, against an expected baseline, on a −100 to 100 scale | Descriptive; the baseline encodes league habits | Cheap: coverage shares assigned to him minus his fair share given his threat |
| Who's-guarding-whom HMM (Franks, Miller, Bornn, Goldsberry 2015) | A defender's spot = γ₀·offender + γ_b·ball + γ_h·hoop; "attention" = 5 units shared among 5 attackers | Annals of Applied Statistics; separated defenders who reduce efficiency from those who reduce frequency | The γ weights are league averages: the "sag 70%" kind of rule | No need to infer: compute coverage share directly from who can Contest or deny each threat with his remaining moves |
| Commit or linger (corner-3 paper, arXiv 2105.12785) | Drive-and-kick help as a small game | "The Nash Equilibrium supports either committing to the corner shooter or to the drive… not lingering between the two" | Stylised 2-option game | Cheap (a 2×2 or 3×3 matrix game per help decision). Replaces "sag X%" with an exact answer. Shaun ruled: commit or split is computed, not forbidden |

**Assessment.** Analytics must estimate reach and assignment; Playmaker knows both exactly. Every off-ball idea becomes a change in a reach map and a threat-coverage matrix:

- **clearing the lane:** fewer defenders can reach the drive path in time;
- **drawing help:** coverage share moves from the mismatch to the decoy;
- **draining moves:** a defender's reach set shrinks, but only if reach depends on *remaining* moves;
- **stretching:** one defender's coverage across two threats exceeds what he can deliver.

## Q2. From goal to steps

| Option | Evidence | Chained plan with dice and a replying opponent? | Re-planning | Cost and legibility |
|---|---|---|---|---|
| GOAP (Orkin, F.E.A.R., 2006) | Celebrated squad behaviour from a 3-state FSM plus A* over symbolic states | Weak: deterministic effects, no opponent inside the plan | Re-plan when a precondition breaks | Cheap, legible |
| HTN (Killzone 2/3; Bridge Baron) | Killzone 3: HTN at commander, squad and bot levels; the bot "reruns the planner at a fixed rate and replaces the current plan if it finds one which is better". Bridge Baron won the 1997 World Bridge Computer Challenge | Good for structuring chains; brittle if hand-authored (Bridge Baron: 91 task names, 400+ methods) | Fixed-rate re-planning with "continue" conditions | Cheap, very legible |
| Goal-based adversarial search (Lisý et al. 2009) | Searches "only the branches… consistent with pursuing player's goals"; "a substantial search reduction with only a minor negative impact" | Yes: the closest precedent | Goals have initiation conditions; branching at goal completion | Far fewer leaves |
| Options / hierarchical RL (Sutton, Precup, Singh 1999) | Formal temporally extended actions (initiation, policy, termination); the interruption theorem: switching to a higher-value option never hurts | Yes in principle (semi-MDP, composes with dice) | Switch when continuing is worth less than switching | Learning options is slow; hand-specified ones are cheap |
| Behaviour trees, utility AI | Industry standard | Poor at multi-turn chains against a reply | Re-evaluated every tick, with a risk of dithering | Better for execution than goals |
| AlphaStar, OpenAI Five | Superhuman RTS and MOBA | Implicitly | Implicit | Huge compute; no legible goals |

## Q3. Search that knows what it's doing

- **Backgammon:** 21 distinct rolls and often up to 20 moves per roll. Star1/Star2 extend alpha-beta to chance nodes (Ballard; Hauk, Buro and Schaeffer); Star2 let programs search depth 5 instead of 3.
- **gnubg's move filters:** keep a fixed number of candidates plus any within e equity of the best by a 1-ply evaluation. It trained against 110,000+ positions where depth-1 and depth-5 disagree, "so its depth=1 evaluations more closely resemble a depth=5 search".
- **TD-Gammon:** learned by self-play; later versions added hand-crafted features and a selective 2-ply search.
- **Stochastic MuZero (ICLR 2022):** models dice via afterstates and chance nodes; matched AlphaZero in backgammon. Neural nets plus many simulations: not viable on phones.
- **Double progressive widening:** limits a node's children to kN^α; works best "when a set of preferred actions was tried first".
- **Odd-even effects:** well documented. MTD(f) guidance for programs with "a pronounced odd/even oscillation" seeds from two iterations back. Nau showed deeper minimax can make decisions worse on some trees.
- **Diagnosis for Playmaker:** mid-turn evaluation, side-to-move parity, unresolved chance. A noisy evaluation makes all three worse.
- **The rule proposed** (built in steps 12 to 13: `like_with_like` is on; the others were measured):
  1. quiet points;
  2. play on while pending;
  3. like with like, plus a tempo term;
  4. change only for a clear reason;
  5. later: train on shallow and deep disagreements.

## Q4. Opposing goals

- **Plan recognition as a game:** adversarial plan recognition "should be modeled in the game theoretic framework" (Lisý et al., ECAI 2012).
- **Goal-restricting opponent models** prune further.
- **Safe exploitation** (Ganzfried and Sandholm): deviate from equilibrium only while "worst-case exploitability remains below the total amount of profit won through gifts". A naive "risk what you've won" rule is unsafe.
- **For Playmaker** (perfect information): the defence computes the offence's top goals with the same generator. A small matrix of offensive against defensive goals, each cell a short search, solved as a zero-sum game. Concede-the-low-look and make-them-beat-you-with-their-worst-shooter then fall out as results. Shaun ruled: the grid is a guide, and the search decides.

## Q5. Showing goals to people

- **Model reconciliation** (Chakraborti et al.): suggest the minimal changes to the human's model that make the engine's plan look optimal. Users understood such explanations well in a study.
- **The XAIP survey** (IJCAI 2020): contrastive "why not my plan?" questions are central.
- **Step-level tutoring** nearly matches human tutors: d = 0.76 against 0.79 (VanLehn 2011).
- **For Playmaker:**
  - the explanation is the goal's own terms;
  - contrastive feedback answers the learner's alternative;
  - judge choice, execution and dice separately, with only the first two feeding the rating;
  - beginners get assigned goals with automatic replacement; advanced players preset their own.

## Q6. Learning (superseded by `RESEARCH_learned_judgement.md`)

Start with a linear or small additive model over named features, fitted from play, with bootstrap uncertainty. Move to a small network only if the additive model plateaus, keeping the additive terms as the explanation layer. Gate every update on the fixed exam.
