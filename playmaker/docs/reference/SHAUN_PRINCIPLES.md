# Shaun's standing principles for Playmaker

These come from Shaun's own rulings, steps 1 to 16. They override any method's convenience. When a principle and an experiment's result conflict, report it; don't resolve it yourself.

## Shaun's rule for Fable (D-196, 15 Nov 2026). It comes before everything below.

> "The computer simulations lie. If the computer cannot set up the offence and defence properly and cannot do it based on goals then no play that comes from it can be trusted. I let it set up as it wills and it left a clear lane through the middle for a layup with nothing in between. That means the metrics vs real basketball are garbage."

1. **Trust the design pillars more than the computer simulation data.** System Fidelity first. Then Neutrality, Player Agency, Legibility and Accessibility may bend but never break.
2. **Fable's sole job is to plan, then fix in logical order, what the computer is poor at or can't do at all.**
3. **Anything that clearly meets the whole design hierarchy stays on.** If the data doesn't fit, the starting assumption is always that the computer is wrong.
4. **Fidelity is questioned only after proving the computer is not wrong,** and only after a factor for human error is accounted for.
5. **Human error** may be modelled on elite chess engines measured against semi-pro chess players. The reason: professional basketball relies heavily on physical traits, not purely on basketball IQ.
6. **The primary target is senior pro level.** Other levels are rolled out as each part is locked in.
7. **Use what is needed for proof, and no more.**

What this means in practice:

- **The FIBA comparison is not a gate** until the computer is proven to play properly. It is not reported as one.
- **Computer-against-computer play-outs are only proof when both sides play the position properly.** When one side's play is in question, the evidence comes from that side played properly: a stronger search for it, or forced lines. Self-play alone isn't enough.
- **The design checks** in `docs/plans/COMPUTER_FIX_PLAN.md` are the gate for every stage. They come from the pillars and basketball, not from the data. Each is a check, never an instruction or a weight in the engine (D-156).

## The standing principles

1. **The priority order:** System Fidelity (it plays like real basketball) > Neutrality (no side or level favoured by the system) > Player Agency (decisions matter) > Legibility (players can see why) > Accessibility. When unsure, fidelity wins.
2. **"It depends."** No fixed distances, no coaching rules of thumb, no fixed plays. Coaching guidance is vocabulary and a sanity check, never a rule. The tool should make the adjustments coaching manuals can't teach yet, case by case from these ratings, this reach, this clock and these tokens. Existing methods are options to weigh by one test: do they make case-by-case judgement better?
3. **An advantage is not the shot (D-94).** "An advantage is what creates a better shot, not the shot itself. A shot is an option, held against a standard that can differ for each team: the offence is satisfied when the look beats what its possession is worth now; the defence may deliberately offer looks below what it can live with." Never call a shot an advantage in player-facing words.
4. **Responsibility from coverage (D-95).** A defender's job is his allocation of limited capacity across threats, not a fixed man. Man-to-man is the case where every share is near 100% on one player; zone and help are splits.
5. **Mismatch by tier.**
   - **Offence:** two tiers up is a strong advantage; one, an advantage; level, a gamble worth it only for a high payoff; one down, poor or desperate.
   - **Defence:** close tier gaps first; a strong defender on a weak attacker is wasted.
   - **Tier informs, never dictates.**
6. **Simulations.** Shaun welcomes simulations that learn from data and make mistakes. He distrusts static simulations that state absolutes. Every number carries its uncertainty.
7. **No hand-set weights.** Numbers come from the rules, the cards, or data. Learned weights are data.
8. **Two formats, one game.** The tabletop game shares the rules, dice and penalties. Engine work must not change a rule. Any difference between formats is deliberate and approved.
9. **Legibility.** Anything a player sees uses plain basketball words: no internal names, codes or symbols. Reports to Shaun follow the same standard.
10. **Small steps Shaun can drive.** Report, don't decide design values. Everything new ships behind a switch, off by default. Shaun turns things on.
11. **Speed matters.** The app must answer within the speed budget, on a phone too.
12. **Long runs must earn their place:** predict the value, demonstrate it on a pilot, then scale, with a cap.
13. **If a fixed item looks like the problem, stop and flag it.** Don't work around it.
14. **What the app is (D-168).** "The app does not simulate full basketball games. It simulates the quality of single possessions. Then it gives the chance to switch roles and improve or beat your personal goals and each other's results." Every rule is scored within one possession, as the quality of a decision. Where a match situation matters (team fouls, possessions left), the scenario sets it as context.
