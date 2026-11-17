# The coverage map: blueprint (Shaun, 16 Nov 2026)

The design behind step 18s. It is the centre of the computer's reading for both sides, and the "reads" layer of the system map (`docs/plans/SYSTEM_MAP.md`, D-197).

## 1. Shaun's design, in his words

> "The defensive coverage map is the gold here. Where the zone of influence lies, what it protects, and what weakens it. Regular snapshots reveal how it is weakening and where you can attack it."

> "The goal of the offence becomes gaining the best possible shots (open layups are always high for most players) by finding efficient strategies to weaken the defence's zone of influence and attack or pass the ball to the zones that remain weak at the start of the next phase. So every phase looks to maximise the weakening of defensive influence first and attack the created weakness such that the next phase begins with the defence in a weaker position than the last. Exploiting matchup advantages and offball movement achieves that, with offball movement and screens designed to weaken defensive influence for the ball-handler to attack the rim or pass, or shoot with the defence in a weaker position this phase and next phase."

> "Conversely, the defence is trying to maintain the strength of their zone of influence or improve it for the next phase. If we look at zone of influence as the protection of high value areas and facilitation of low value areas something interesting may fall out. Rank each of the court zones by value, with the short range green area highest, then three pointers, then mid-range and long range 2 pointers last and have the zones of influence protect shot in those areas maximally and preferentially and denying driving lanes through the middle may fall out."

> "We've already established that no decision making involves a single attacker and a single defender. Defenders are covering multiple weaknesses at once. And attackers need to understand who helps their defender when they gain a positional or trait-based advantage."

**The one refinement agreed:** a square's value is not ranked by hand. It comes from the cards of the attacker who could shoot there. Shaun's order (short range, then threes, then mid-range, then long twos) falls out for most players, and changes where it should:
- a non-shooter's three is worth little, so helping off him falls out;
- a sharpshooter's corner is worth nearly a layup, so staying attached to him falls out;
- a post scorer near the rim is worth more than a guard there.

## 2. What the map is

One map per phase, built from the board, the cards and the rules. For every square `s` and every attacker `a`:

| Layer | Meaning | Built from |
|---|---|---|
| **Value** `V(a, s)` | What `a`'s best legal open shot from `s` is worth. | Points × his open rating for the shot the rules allow there, on the game's own scale (an open two at 15 is 30). No shot from the rim square (D-198). |
| **Reach** `R(a, s)` | The chance `a` can be shooting from `s` with the ball at the start of the next phase. | The movement rules (bodies, the two-arrow zone, tokens, Dribble against Agility, rushed), the pass rules (the pass line, who can jump it, Pass against Intercept), and the turnover rules (−5, the phase ends; D-198). For the ball handler, by moving or dribbling. For the other four, by moving, then a pass. |
| **Influence** `I(a, s)` | What the best defender who can get there takes off `a`'s shot from `s`. | The contest rules exactly as they stand: square in front with the arrow on him gets the full rating; in front with the arrow off, or beside, 3 less; behind, 6 less; rushed, 2 more off; never under 1 (D-191, D-193, D-194). Inside shots, the block option as now. Each defender's movement left this phase and next, and where his arrows can turn. |
| **Weakness** `W(a, s)` | What the offence can actually get there. | `R × points × (rating − influence)`, on the same scale, with the foul and turnover points of D-198 where the rules put them. |

**Who covers what.** For each square, record which defender supplies the influence, and the next best. One defender covers many squares and several attackers at once. That record is the help chain: if the covering defender leaves to help, his squares fall to the next best, or to nobody.

**The snapshot.** At the start of every phase, keep the map: the weakness on every square, by attacker; the covering defender and the next best; and the change since the last phase. The snapshots are the feedback:
- inside the possession, they show where the defence is weakening;
- between possessions, they feed the scout (the areas this defence keeps leaving weak).

## 3. What each side wants, one phase ahead

**The offence:** finish each phase so the next one starts with the most weakness it can reach, then attack it:
- **Off-ball movement and screens** pull covering defenders off high-value squares, turn their arrows, or stretch one defender across two duties.
- **The ball** goes to the square that stays weak: drive it, pass to it, or shoot from it.
- **Shoot now** when the shot available now is worth more than what the next phase is likely to give (the clock counts).
- **Matchups** fall out: an attacker whose card beats his defender's on a square makes that square weak.

**The defence:** finish each phase with the least weakness the offence can reach:
- protect the highest-value squares first, and concede the lowest;
- keep each square covered by someone who can get there square;
- help only where the help chain still covers what the helper leaves.

Walling the middle, helping off non-shooters, staying attached to shooters and closing out under control should all fall out. **None of them may be written in** (D-156).

**Neutrality:** both sides read the same map. What the offence values a square at is what the defence values protecting it at.

## 4. How the search uses it

- **The map is the reading at the end of a line.** The search plays one turn or one phase ahead, as now, and reads the map where it stops.
- **How the map is summarised into one number** is fitted to played-out results, the way the calibrated map is fitted, never set by hand. The plain starting point: the best reachable weakness, plus how many separate options sit close to it (a defence can't cover two at once). The fit decides what else matters.
- **It replaces, or absorbs, the reads it covers:** the lane measure (18q) is the ball handler's reach to the short-range squares; "keep two ways to score alive" and "limit future passing options" are the reach of the other four after a pass; "no look above what the possession is worth" is the best weakness now. Keep any of those that the map doesn't cover, and say which.
- **Setup is judged by the same map** (the offence places to make weakness; the defence places to cover value).
- **Goals are measures on the map** (D-197). A fluid goal aims a measure at one player: "deny O2" is O2's reach after a pass pushed to nothing; "attack their weakest defender" is the squares he covers.

## 5. Design checks (the gate; D-196)

Each one must fall out. If one doesn't, the computer is presumed wrong. Prove each by forced lines for the side in question, not by self-play alone.

1. **Shaun's board (15 Nov):** the clear lane from O1 to the rim reads as a large weakness. The defence's own best placement reads it smaller, and plays out smaller.
2. **A non-shooter's corner three reads as low value.** His defender in the lane covers the short-range squares and costs little.
3. **A sharpshooter's three reads as high value.** His defender leaving him to help reads as a large weakness.
4. **Arrows matter:** two arrow directions that cover different squares read differently.
5. **Square in front reads stronger than beside, and beside stronger than behind,** square by square.
6. **A screen that stops a covering defender** shows the squares he covered going weak.
7. **The offence takes an open lane** when the map says the lane is the weakest high-value path. The defence's best answer is the one that leaves the least weakness, by play.
8. **Each phase the offence chooses leaves the next phase's weakness higher than the alternatives,** and the defence's choice leaves it lower, by play.
9. **The system map's checks 10 to 12 (15 Nov):** fewer safe passes is better defence; a good three-point shooter is guarded tighter than a poor one; a scouted man to stop gets less while the others get more.

## 6. What it is not

- Not a playbook. No play, action or placement is named or favoured.
- Not a fixed ranking of court zones. Values come from the cards.
- Not hand-set weights. Anything combined is fitted to play.
- Not one attacker against one defender. Every square is read against all five defenders.
