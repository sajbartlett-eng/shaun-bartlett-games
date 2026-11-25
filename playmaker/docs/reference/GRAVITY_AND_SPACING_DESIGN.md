# Playmaker: Gravity and Spacing Design

Nov 25, 2026 · @Shaun Bartlett

## How to read this document

This is the design for how both of Playmaker's computer players think: where the defence stands and faces, and how the offence sets up and plays. It assumes no knowledge of the conversations that produced it. Where it names a decision (D-number) or a build step, those live in the repo's `DECISIONS.md` and `docs/reports/`.

### The game in brief

Playmaker is a FIBA half-court basketball game on a grid of squares: columns A to Q, rows 1 to 14, the rim at I2. Five attackers (O1 to O5) play five defenders (X1 to X5). Each player is a card with ratings out of 20; a roll at or under the rating succeeds. The repo's RULES\_CURRENT.md is the authority on every rule. This glossary is a guide to the terms: where it differs from the rules, the rules win and the build report says so.

| Term | Meaning |
| --- | --- |
| Phase | About 2 seconds of shot clock. The shot clock sets how many phases a possession has. |
| Turn | One side's go within a phase: 1 or 2 actions, out of the 6 the side has for the phase. Sides alternate. |
| Actions | Move (controlled), Quick Step and Sprint (which leave the player rushed), Dribble, Pass, Screen, Shoot, Hesitate or Pause, fakes, Contest, Block, Steal, Intercept. Each phase has limits on how many of each. |
| Rushed | After a Quick Step or Sprint, every roll is 2 worse until the player Moves. |
| Locked | No Move, Sprint, Dribble or arrow turn for the rest of the phase, and rushed. A Quick Step is still allowed. |
| Arrows | Each defender has two. Each points at one of the eight neighbouring squares, and the two always point at neighbouring directions, 45 degrees apart, so a defender chooses among eight pairs. They set his contest, the drive he walls, and the lane he can jump. |
| Wedge | The area between a defender's arrows. It stops the ball handler moving through. It never blocks a pass. |
| Zone of influence | A defender's square plus what his arrows reach. |
| T square | Where a screener stands. A defender on it loses the arrow pointing diagonally round the screener. |
| The race | Who can reach a square first, by the movement rules. |
| Closely guarded count | A ball handler held tightly at phase ends moves toward a violation. |
| Three seconds | An attacker in the key at two phase ends commits a violation. |
| Turnover | 5 points off, the phase ends, the possession goes on (D-198). |
| Foul | 5 points to the offence, play on; shooting fouls add free throws (D-198). |
| The scout | Each card's shot values on every square against every defender, worked out before play. |
| The shot bar | What the offence can still expect from the phases left. A shot is worth taking when it beats this. |
| The list | The offence's looks, ranked best first. This design keeps it and prices it in points. |
| Separate thinking | Each computer side sees only the board, the rules and the cards, plus its own plans. It never sees the other side's. |

### The parts, in order

1. The one number both sides read, and how it is computed.
2. The defence: the team's weight map and its centre of gravity, each defender's decision, the arrows.
3. Advantages as gaps: speed, the dribble, the pass.
4. The offence: the same number from the other end.
5. A worked example.
6. What the engine keeps and replaces, what the player sees, the checks, and the ledger of everything agreed.

## Why this design

Both computers should play for points, measured the same way on both sides. The defence stands where its presence saves the most points. The offence sets up and acts to open points the defence cannot afford to cover. Everything else in this document follows from that.

The playtest of 20 November showed what goes wrong without it. A cutter caught the ball under the rim and did not shoot. Two attackers were called for three seconds. Screens were set with no purpose. The point guard stood two squares past the arc all possession. The cause was a stand-in: the computer was ranking positions by the defence's weakest point (the list, and before it the lasting gap) and not by points. It stretched the defence and forgot to score.

Three rules hold throughout:

- **One currency.** Every comparison is in points at their real chance. No hand-set weights (D-156).
- **It depends.** Nothing here is a play or a tactic to run. Packed keys, traps, stacks and spread floors must fall out of the numbers, case by case.
- **Every claim has a board check** that fails if the claim is not true in the build (CLAUDE.md, Measures and concepts). The checks are listed at the end.

## The one number both sides read

Everything in this design is one number seen from two ends:

> **The possession's value.** Take every look the offence can get, best first. Each has a chance of being open in time. The offence takes the best one that opens. Take off the risks (a turnover, a violation), add the fouls drawn, and read ahead over the phases left.

The offence acts to raise it. The defence acts to lower it.

Two things are computed to get it, and both are real parts of the engine, not just explanations:

1. **The team's weight map** (part 1): where the offence's looks are and what each is worth right now. This is the defence's picture of the floor, and it is what keeps defenders on the right side of their men.
2. **What the defence's five stances take off it** (parts 2 and 3): each look's value after the contest, wall, lane threat and help it now faces.

The number is what is left. The link rule, the arrow effects, the trap and the offence's variables describe what that number should produce. They are checked against it, and they are not separate mechanisms that could drift apart.

This is the old list, kept and priced. The list ranked the offence's looks best first, which is right, because the offence only takes one shot. What it lacked was a value in points, so the computer could not tell when to stop building and score.

### Computing the number

**One look** is a shot one attacker could take: who, from which square, which shot. Its value is on the game's own scale: his shot rating less the contest rating he faces, times the points the shot is worth right now. This is the scale this document calls 1 to 39. By the rules, a contest is always at least 1 and a shot that works out below 0 scores 0; on today's cards the top is 38. Turnovers (−5) and fouls (+5) are on the same scale. Nothing in the computer converts to a different scale, such as expected points per shot. Its chance of happening is the chance the attacker and the ball both get there before that defence closes it, by the race and the ball's reach.

**Combining looks.** Sort the looks best first. The offence takes the first one that opens:

```
V = p1*v1 + (1-p1)*p2*v2 + (1-p1)*(1-p2)*p3*v3 + ... + (chance nothing opens) * V_later
```

where v is a look's value and p its chance of opening this phase. If nothing opens, the offence plays on, worth the shot bar for the phases left (V later). Looks that share a cause (the same screen frees two men) are not counted as independent: they are read as one route with its outcomes.

**Costs and gains** are added at their chance: a turnover (−5 and the phase), a violation, a foul drawn (+5).

**Tries cost actions.** The sum lets the offence fall back from one look to the next. In the game each route costs actions, and a turn has 1 or 2. So the offence can only fall back through as many routes as its actions allow, counted by the rules and nothing by hand.

**Later answers cost actions too.** Inside the number, each side's later answer gets only the actions and time it will actually have: what is left of its turn, then its next turns as the clock allows. Neither side is ever read as free to fix everything afterwards. Otherwise waiting always reads as good as acting, and a defender never turns an arrow, closes out early or comes to trap, because the number assumes he can do it later for nothing (found in step 31).

**Reading ahead.** The number is read as far ahead as the plan needs, up to four turns (D-268, 19 November), with each side's best answer by its own model. Past that, the shot bar stands in for the rest.

### How each side chooses

**The defence**, each time it sets up or takes a turn:

1. Build the weight map (part 1) and its centre.
2. Place every defender on his base position: on the line between his man and the part of the weight he would help, at the depth the link rule gives (part 2). This is the goal-side starting shape.
3. Improve it: try moving and turning one defender at a time, keeping any change that lowers the number, until none does.
4. Check the result against the link rule and the goal-side checks. A defender off his line must be explained in the report.

**The offence**, at setup, follows the setup order (the offence section). In play, each turn:

1. Shoot if the best shot now is worth more than playing on.
2. Otherwise choose the actions (1 or 2 a turn) that raise the number most, read ahead.
3. A fake is chosen as a mix with the real thing (step 29), so the defence cannot read a habit.

**Separate thinking.** Each side computes the number with its own model of the other side's answer. The defence never sees the offence's plan or a hidden fake, and the offence never sees the defence's private choices.

**The computer's levels** (Rookie, Starter, All-Star) differ in how far and how widely they search. How far is a fixed number of turns for each level, never a clock, so the same board gives the same decision on every device (Shaun, 25 November). They use the same number and the same rules. Shaun's human-error factor for lower levels (D-196) is a separate, later step.

## The defence, part 1: the team's weight

The team's weight is a map of where a defender's presence saves the most points right now. It tells the whole defence where it should be. It is built in three layers.

### Layer 1: the points a contest saves

For each attacker and each shot zone (short range, mid-range, long two, three, and the deep squares his level allows), the pull is:

> what the shot is worth uncontested, less what it is worth against the best answer a defender can give there.

- **The shot's worth** is on the game's 1 to 39 scale, the same scale as the −5 for a turnover and the +5 for a foul. Uncontested, it is his shot rating times the points the shot is worth right now. Contested, it is his rating less the contest rating he faces, times those points (a contest is always at least 1, and a shot never scores below 0). The points are normally two or three. When a team must have a three to tie, a two is worth nothing (the Need a Three card: only a three scores), and the map moves to the arc by the same sum.
- **The best answer** is whatever the rules allow from there: the honest contest by position, the block where it pays (with its foul risk), a rushed closeout, and the fake threat against a shooter in control.
- Defenders are drawn to where they save the most, not to where shots are worth the most. A great look that a contest barely changes pulls less than a good look a contest ruins.

Laying these out for the five attackers gives the base map: every look, with what a defender saves there. Adding up these weights across all five attackers gives the base centre of gravity, as Shaun set out: it is where the weight balances. That adding is for finding where the defence should be. It is different from the possession's value, which is not a total, because the offence takes one shot: covering one of two equal looks saves nothing while the other is open. Its depth sits somewhere between the rim and the three-point line.

**Whose contest.** For the team's map and its centre, the weight at a look uses the best contest any of the five defenders could give there. For one defender's own base position, it uses what he, with his card, would save there, because the link rule compares what he saves.

### Layer 2: occupation

The segments are set out square by square in "Rulings of 25 November" near the end of this document.

Split each zone into segments: the green zone as one, mid-range in three, the long two in four, and five beyond the arc (two corners, two wings, the top). Leave out any segment no attacker can reach this phase. If the offence loads one side, the weight shifts toward it. This is usually a small adjustment.

### Layer 3: can the ball get there

Discount each segment by the chance the ball reaches it before the defence recovers. That depends on:

- where the ball is;
- the passing angles open from there, including the boundaries;
- the room to use a skill advantage;
- how fast the ball handler can get there himself.

A valuable square the ball cannot reach in time pulls little right now. Layers 2 and 3 together are one reachability factor: can a player get there, and can the ball get there before the defence does.

### The map, and its centre

- **The map leads; the centre is its summary.** One point misleads when the weight has two lumps. A great shooter at the arc and a big at the rim average out to mid-range, where nobody is. Defenders move toward the weight itself.
- **Covered weight pulls less.** Once a defender is on a threat, the map the others read carries only what his stance leaves of it: little after a set contest in front, more after a loose or rushed one. This stops five defenders chasing the same thing.
- **The map moves every turn.** The ball moves, players move, the clock runs down and the shot bar falls. The map is read again each time, and ahead as far as the plan needs (step 27).

### The centre of gravity keeps the defence goal-side

The centre of gravity is where the map's weight sits. Because the most valuable looks are near the rim, it normally sits between the offence and the hoop, and that is what puts each defender on the right side of his man.

- **A defender's base position is on the line between his man and the part of the weight he would help. That is the heaviest weight he can reach in time that no teammate is already covering, never the empty average between lumps.** From there he can do both jobs: contest his man, and reach the weight if he has to help. How far along that line he stands is the link rule: close to a strong threat, deep toward the weight when his man's threat is small.
- **Normally the weight is at the rim, so that line is the line to the hoop.** That is goal-side defence, and it is a result of where the points are.
- **When the weight moves, the right side moves with it.** If a three is all that matters, the weight is at the arc and defenders play on top of their men. If the ball cannot reach a post player except by an entry pass, the lane carries the weight and his defender plays beside or in front of him.
- **The search starts from this shape.** The defence's five stances begin on these lines and are then improved. It never starts from nowhere and hopes to find goal-side by trial. Steps 24 to 26 showed what happens otherwise: defenders stood above their men and left the rim open.
- **The ball shades it.** Each defender leans a little toward the ball along that line, because the ball is where the next threat comes from.

## The defence, part 2: each defender's decision

The map says where the team should be. This part says who can afford to be there.

Each defender has three jobs inside the team shape:

- **His assignment:** the immediate threat he is responsible for.
- **The ball:** pressure and containment on the ball handler.
- **Gaps:** driving and passing lanes, covered by the whole team through position and arrows, given the offence's angles and room.

### The link rule

Every turn, each defender makes the same comparison:

> Leave your man to move toward the team's weight only when the points you would save by helping are more than the points your man would cost if left.

Both sides are counted at their real chance:

- **Staying** is worth what his man would score if left, taken from the map. The map's value already includes the chance the ball reaches him in time (layer 3), so it is not discounted again.
- **Helping** is worth the points saved at the weight, times the chance he gets there in time to matter.

A defender with no immediate threat moves toward the weight, now or where it is heading. A defender guarding a real threat stays attached until the comparison flips.

### Why no weighting is needed

Both sides of the comparison are in points, so the bigger number wins. A weighting between team and individual would only be needed if they were measured differently.

### Three things that keep it honest

1. **Who covers the man he leaves.** If a teammate can rotate onto him in time, leaving costs less. The rotation chain is read as part of the same comparison.
2. **The cost of getting back.** Moving away and returning takes actions. That cost is counted, so defenders do not flip back and forth each turn. It is the moves it takes, never a number set by hand.
3. **Threats that come one after another.** Helping on a drive can create the next threat, the pass to the man he left. That is counted as part of the cost of helping (step 25).

### Solved together, counted once

- **The five stances are chosen together,** as the set that leaves the offence the least. Five defenders each applying the link rule alone could all leave, or none. The link rule describes the answer for each defender and is used to check it.
- **Cover comes in degrees.** A set contest in front takes more off a look than a rushed one from the side. A look is never switched off as covered: its value is whatever is left after the stances it faces.
- **Switching men** happens when the swap leaves the offence less, counting the moves it takes.
- **Some answers need two defenders to move together.** A switch or a trap can't show its gain if only one defender is tried at a time. The search also tries pairs: two defenders swapping men, and a second defender going to the ball with his own man read as left.
- **The ball's reach is counted once.** It is in the map (layer 3). The link rule uses the map's values and does not discount them again.

## Advantages are gaps: speed, dribble and pass

An attacker's edge over his defender is a gap, and it is priced like any other gap: the points it leads to, times the chance he gets there before the defence does.

| The edge | What it gives the attacker | Where it shows in the sum |
| --- | --- | --- |
| Speed | He reaches squares his defender cannot reach in time | The race: every square he wins is his to shoot or catch on |
| Dribble against Agility | He gets past the wall | The value behind the defender, at the chance the Dribble wins |
| Passing | The ball arrives where a defender cannot | Layer 3: the ball's reach |

No edge has a value of its own. A fast player in a place where speed leads nowhere has no gap. The same player with open floor in front of him has a large one. So the scout does not rate speed: it reads where each edge leads to points on this board.

### How an edge is contained

The defence has three tools, and each is judged by the points it takes off that gap:

- **Distance.** Giving ground cancels a speed edge, because the defender no longer has to win the race from level. It costs a looser contest on the shot. Stand off a fast non-shooter; stay tight on a fast shooter and get help.
- **Direction.** The wedge decides which way he can go. Send him where his edge is worth least.
- **Help.** A second defender's weight behind the first, where the link rule allows it.

The matchup rule already prices this at setup: the edge is counted where it hurts (step 23). This section applies the same thing every turn.

### The pass makes gaps as well as using them

A pass is not only worth the look the receiver has when it lands. It is also worth what it does to the defender who had to react to it. Every outcome is counted at its real chance:

- **The pass lands and forces a closeout.** A defender who arrives with a Quick Step or Sprint is rushed until he Moves: his contest is weaker and he is easier to drive past. The gap is the shot over him plus the drive behind him.
- **A defender goes for the ball and misses.** Each is read by its own rule: a missed Intercept leaves him on the lane with his Move used, and a missed Steal locks him. The gap is what the receiver gets with that defender limited in that way, not what he would get against a set defence.
- **A defender is sold on a fake.** One who went for the ball on a pass fake is locked for the rest of the phase. One who tried to block a shot fake is locked too, and may have fouled (step 29). The gap is everything he was guarding.
- **The pass is stopped.** A turnover: 5 off and the phase lost (D-198).

The same holds from the defence's side. Going for the ball is only worth it when the points it saves by winning are more than the points it gives up by missing or by being faked. Denying by position, with an arrow on the lane, risks none of that. So a gamble should appear when the ball handler is a weak passer, rushed or cannot fake, and should disappear against a passer in control with a good look waiting behind the defender.

Board checks for this:

- **A11:** a helper who must Sprint to close out on a skip pass: the receiver's value includes the drive past the rushed closeout, not only the shot.
- **A12:** a defender who can try an Intercept with a strong look behind him: the report gives the points for winning, missing and being faked, and his choice matches the larger side.
- **A13:** the same defender against a rushed ball handler who cannot fake: he gambles more readily than against one in control.

## The defence, part 3: the zone of influence and the arrows

A defender saves points through his zone of influence: his square and his two arrows, 45 degrees apart. So the thing the computer chooses is never a square alone. It is a square and a pair of arrows together, judged by the points that whole stance saves.

### What the arrows do, by the rules

- **They wall a drive.** The wedge between the arrows stops the ball handler moving through it. A wall needs both arrows. It never blocks a pass (D-167, D-170).
- **They decide the contest.** In front with an arrow on the shooter is the full contest. Arrow off, or beside him, is 3 less. Behind is 6 less.
- **They decide the block's foul risk.** No foul roll in front with the arrow on, one with it off, two from the side or behind.
- **They threaten the pass.** A defender jumps a lane his arrow points down. The other ways to stop a pass are a Steal beside the passer and denial beside the receiver.
- **A screen takes one away.** A defender on the T square loses the arrow that points diagonally round the screener, so he walls no drive and jumps no lane until he gets free.

### How the arrows are chosen

Each stance is worth the points it saves across everything it does at once, each at its real chance:

- the contest it gives on his man's best look;
- the drive it walls;
- the pass it threatens, and what the receiver gets if the pass lands anyway (step 26);
- the help it can still reach in time.

The arrows go wherever that sum is largest. This is the link rule again, at a finer scale: one arrow on his man and one on the lane is a defender splitting himself between his assignment and the team's weight.

### Three things the arrows weigh

Arrows exist to take as much value off the offence as possible. Three effects are in that one sum, and none needs its own rule.

1. **Close the lane with the weakest cover behind it.** A lane that leads to a teammate's help costs the offence little even if it is taken. A lane that leads to open floor costs a lot. The arrows go to the second kind. This is forcing the ball toward the help.
2. **Send the ball where it can do least.** In the middle, the ball handler has the full circle of passing angles and every area within reach. Toward a sideline or a corner, the boundaries cut his angles and his room, so the value he can reach falls (layer 3). A stance that walls the middle and leaves the sideline takes more off the offence than the reverse. That is why defences push the ball to the corners, and here it is a result, not a rule. Where the sideline holds the bigger threat, the same sum sends him the other way.
3. **Two smaller passes against one bigger pass.** Two arrows can threaten two lanes. The comparison is the points each choice saves at its real chance: the value of each pass, times how much the arrow lowers its chance of landing. Denying two modest passes wins when their saved points add up to more than the single big one, and loses when they do not.

All three are the same reading: for each stance, what can the offence still reach, and what is it worth. The stance that leaves the least wins.

### What should fall out

- **On the ball:** both arrows toward the ball handler's best drive, walling it, unless his shot is the bigger threat.
- **One pass away:** one arrow on his man, the other toward the passer, cutting the lane.
- **Far from the ball:** both arrows toward the team's weight, because his man's threat is small right now.
- **Beside a post player:** one arrow on the lane, one on the man, so the entry is threatened and the contest is still there if it lands.
- **In a trap:** the two defenders' wedges together close the ball handler's way out, and their arrows cover his nearest passing lanes.
- **Hugging disappears:** arrows pointed at a man who cannot get the ball save nothing, so they turn to a lane or to the weight.

### When denial pays

Denying a pass is a stance like any other. It is chosen only when it leaves the offence less, read ahead, never as a habit.

**What denial gains:** the pass to his man, at its real chance, and that man's look if it lands.

**What denial costs**, each counted at its real chance over the next turn or two:

- **The backdoor cut.** A defender on the ball side has his back to the rim. A man with a speed edge, or a defender caught leaning, gets the cut behind him for a look at the rim. Its value depends on who is behind to help.
- **Help taken away.** A denier is not in help. Denying several men at once can leave the drive or the paint open. The offence may want this: spreading its threats so the defence denies, then attacking the space it left.
- **The ball handler moves.** A dribble or a step changes the angle, and a lane that was denied opens.
- **The offence's other answers:** a V-cut, a seal on the ball side, a screen on the denier, a handoff, or a pass to someone else that changes the angle (step 25's conditions list).

So denial should appear against a strong threat one pass away when help behind covers the backdoor, and fade against a fast cutter with an empty paint behind him, or when the defence needs that defender in help. Each counter is the offence's ordinary actions, read ahead, not a special rule.

Checks for this part:

- **A14:** a strong shooter one pass away, a helper near the rim: his defender denies.
- **A15:** the same shooter with a speed edge over his defender and nobody near the rim: his defender does not deny, or the report shows the backdoor priced and still worth conceding.
- **A16:** the offence spreads so that denying all its threats empties the paint: the defence denies fewer, or the offence's next turn attacks the empty paint.
- **A17:** a denied man runs a V-cut, a seal or comes off a screen: the defence's next stance is read against it, and the number shows the change.

### Its effect on the offence

The zone of influence is what the offence is working against. Help distance is measured to where a defender's zone can reach, not just to his square. A screen is worth the arrow it removes: the wall or the lane that defender can no longer hold. An attacker stepping off the line of an arrow opens a passing angle. These are counted in the setup value, through access and pin.

### Board checks for this part

- **A1:** a defender one pass away has one arrow on his man and one cutting the lane to him.
- **A2:** a defender whose man cannot be reached by the ball has neither arrow on him.
- **A3:** the on-ball defender's wedge covers the drive that is worth most to the ball handler.
- **A4:** a screened defender on the T square is read as walling nothing and jumping no lane.
- **A5:** in the corner trap (check D8), the two wedges leave no square the ball handler can move to.
- **A6:** turn every arrow on a board to the next best direction, and the points saved go down. If they do not, the arrows were not chosen by points.

* **A7:** a fast non-shooter against a slower defender: the defender gives ground. A fast shooter against the same defender: he stays tight and help shades toward him.
* **A8:** a ball handler at the top with equal threats either side: the wedge sends him toward the sideline. Put the best shooter in that corner, and it sends him the other way.
* **A9:** two modest passes and one big pass open from the ball: the report gives the points saved by each choice of arrows, and the stance matches the larger.
* **A10:** a lane with help behind it and a lane with none: the arrows close the one with none.

## What should fall out for the defence

None of these is a rule. Each is what the map and the link rule should produce on their own. If the build does not produce one, either the build is wrong or the cards say otherwise, and the report says which.

| What we expect to see | Why it should fall out |
| --- | --- |
| A packed key against poor shooters | Their weight at the arc is light, so the map sits near the rim. |
| A box-and-one against one great shooter | His weight is heavy and his defender never leaves. Once he is covered, the other four read a map with little of his weight left on it. |
| Mid-range conceded | Only if a contest there saves little on Shaun's cards. To be checked against the cards, not assumed. |
| Sagging off a non-shooter far from the ball | His threat is small and the ball is unlikely to reach him in time. |
| Face-guarding an elite shooter | His threat is worth more than any help his defender could give. |
| Tight guarding on a shooter in control | A closeout from distance arrives rushed, and the fake punishes it (step 29). |
| A defender following a shooter past the arc | At Senior Pro his deep squares still carry weight. |
| The whole defence at the arc when a three is needed | A two is worth nothing right now, so the paint's weight drops. |
| A trap | See below. |

### The trap

Shaun's theory: when the defence has closed the offence's lanes, angles and room, several defenders can attach to the ball handler.

It follows from layer 3. When the ball cannot reach the other attackers, their threats are worth little right now, so their defenders lose little by leaving. The one threat the ball can certainly reach is the ball handler. Two defenders go to him.

The trap prices its own risk. If a pass gets out, the offence has four against three. That is counted as the receivers' threats at the chance the pass escapes, which depends on the lanes and on his passing rating.

- **Where it should appear:** the corner, the sideline, a dead dribble after the pick-up, a poor passer, a pick-and-roll ball handler whose roller cannot be fed.
- **Where it should not:** the top of the key with open lanes and a good passer.

The trap is judged with the trapper gone from where he was: his own man's look, and the best escape pass, are read as if he has left. Reading them with him still in place would count him twice and make every trap look cheap. The trap itself closes lanes, through pressure, the closely guarded count and the steal threat. So the defence judges it as a position it could take, reading the board as it would be with two on the ball.

## The offence: the same sum from the other end

The offence wants the points the defence cannot afford to cover. It places and moves its players so the link rule fails for as many defenders as possible, then attacks the weight they had to leave.

> The value of a setup is the gap it can open, times the chance that at least one route to it is open in time.

### The variables

There are six inputs, and they depend on each other. The number of actions run at once is where they balance.

| Variable | What it is | What it does |
| --- | --- | --- |
| Threat | What each attacker can score from his square: shooting, the rim, the glass, a screen. From the scout. | Sets how much weight he carries. |
| Pin | How firmly that threat holds his defender. | A pinned defender cannot help without giving up more than he saves. |
| Help distance | How far a pinned defender must travel to close the gap, and to get back. | The further, the longer the gap stays open. |
| Time | The phases the action needs at that spacing, against the phases left. | Close players act sooner. Spread players open more. |
| Access | Whether the defence sits between the ball and the receivers, by geometry or by pressure. | Low access means one action rarely opens a lane. |
| Room | The space and angles around the ball, set by the boundaries and by crowding. | Every screen and cut needs space to work. |

### The push and the pull

- **Push (space):** threats spread apart pin their defenders further from the gap. Gaps in the key are worth the most, because the shot they give is worth the most.
- **Pull (time):** a screen, a short pass or a cut only happens quickly if the players are close.
- **The balance:** as spread as possible while the plan still happens inside the phases available.

Three principles follow, and each is a cost that is counted, not a rule:

1. **Get out of each other's way.** An attacker standing where a teammate needs to drive, cut, pass or shoot removes part of that teammate's threat.
2. **Two threats close together pin one defender, not two.** The second threat is wasted unless an action needs them close.
3. **A non-shooter on the arc pins nobody.** His defender sits in the key for nothing. At the dunker spot or as a screener, his threat is real and his defender is held.

### How many actions at once

Three forces pull on this number:

- **Less time pushes it up.** With one go, one dice roll is fragile. Several different actions at once raise the chance that at least one works.
- **Less access pushes it up.** When lanes are blocked, more tries are needed to open one.
- **Less room pushes it down.** Each action needs space. In a cramped spot, run fewer, in sequence: a primary option and a fall-back.

With plenty of time, access and room, one cut or one screen is usually enough, and the rest of the offence stays spread.

## The offence's setup, in order

1. **Scout.** Each attacker's zones where his shot is average or better: these are the places that demand a defender. Also where his dribble, his screens and his rim threat are worth most. And the defence: who helps, who sags, who to target.
2. **The ball handler's start.** Where the ball begins fixes access and room for everyone else.
3. **Possible positions.** Each attacker's best segments by threat. Two attackers in the same segment waste a pin, and that cost is counted: it is not a rule. Segments narrow the search and explain the placement. Distance between them is kept large, measured by the help distance it creates, not by distance for its own sake.
4. **Secondary skills break ties.** Between equal segments, choose where his dribble or his screen creates the most: space, a passing angle, an advantage to take, a gap in the defence's weight.
5. **The plan's conditions.** The route to the best gap, how many phases it needs, how many actions run at once, and the fall-back.
6. **Adjust to meet the plan.** Bring players into adjacent segments only where the plan needs them close, and only as close as lets it run with no wasted phase.

The ball handler's position and the defence's weight change every turn, so steps 3 to 6 are read again in play. A setup is a prediction. The computer adapts on the fly (step 25).

### The same sum in five situations

| Situation | Access | Room | Time | What should fall out |
| --- | --- | --- | --- | --- |
| Baseline inbound, under the rim | Low: the defence's weight is across the lanes | Some, to the sides | Very short | Pack the paint, several screens and sprints at once, exploding outward |
| Corner inbound | Good: away from the weight | Low: a quarter of the angles, little space | Short | Spread out, one primary action, then a fall-back |
| Sideline near half court | Good | Plenty | Some | One cut or one screen |
| The top, full clock | Good | Plenty | Long | Spread wide, one action at a time, in sequence |
| The top, last phase | Good | Plenty | One go | Closer together, several actions at once |
| Full denial, anywhere | Low: pressure on every receiver | Plenty | Varies | Spread wide, several actions at once, far enough apart not to clog |

Full denial and the baseline inbound are the same case for access: the defence is between the ball and the receivers. They differ in room and angles, which is why one packs and the other spreads.

Two illustration pages show these trade-offs with sliders and a court: Playmaker Push and Pull, and Playmaker Lanes and Gravity. Both are sketches with made-up numbers. This document is the design. The sketches take shortcuts the engine must not copy: they price the backdoor cut, fronting and the trap with hand-built terms because they cannot read ahead. In the engine, each of these must come from the ordinary actions (a cut, a lob, a pass out of two defenders), the race and the cards, read ahead. A special term for any of them is a stand-in, and the build report must list any it finds.

## What this changes in the engine

### Replaced

- **The list as the leading measure (D-219).** Today both sides rank positions by the defence's worst hole first, then the next. This design keeps the list's order, best look first, and prices it as the possession's value, on the game's 1 to 39 scale. Shaun agreed to this on 25 November. The list can stay as a display and as a tie-break.
- **The defence's settlement by the list.** It becomes: build the weight map, start every defender on his goal-side line, then improve the five stances by the possession's value. The link rule describes and checks the result.
- **The offence's placement search by the list.** It becomes the setup order above, scored by the setup value.
- **"Spacing will fall out."** Spacing is now counted directly: crowding, wasted pins and help distance are costs in the sum.

### Kept, and used as inputs

- The scout's shot review, movement review and matchup table (step 24). One scale throughout: shot rating less contest rating, times points, 1 to 39, with turnovers and fouls at 5 on that scale. Any place in the engine that uses another scale is a leftover to fix.
- The race: who can reach what in time (steps 22 to 26).
- The danger of the pass: both outcomes counted (step 26).
- The read-ahead, four turns, both sides alike (step 27; four by D-268).
- The shot bar falling with the clock (step 25).
- The three seconds and the closely guarded count, by the rule (step 27), with one fix below.
- The contest as an action, the block, fakes, the pivot and deep range (steps 28 to 30).
- Separate thinking: each side uses only what it can see and its own model of the other (step 24).

### Fixes that come with it

1. **Take the good shot.** A shot is taken when its value beats the value of playing on. The playtest's cutter under the rim should shoot.
2. **The three seconds.** Today there is no cost if he can still get out in time, so the computer kept planning to leave and never did. The cost of the action he must spend to leave is counted from the moment he enters the key.
3. **No action without a purpose.** A screen or a cut is chosen only if it raises the setup value. The far-side screens in the playtest should disappear.

### Still Shaun's to decide

- **Catch and finish.** A cut, a catch and a layup take three actions, so the defence gets a turn between the catch and the shot. Should a cutter who catches in the green zone be able to finish in the same motion? This is a rule question, not a computer fix.

## A worked example

One board, start to finish, to show how the parts fit. The build will produce its own values from the cards; this shows the reasoning.

**The board.** The offence: O1, a guard with the ball at the top (I11). O2, an elite shooter in the right corner. O3, an average shooter on the left wing. O4, a non-shooting big at the left dunker spot. O5, a big at the right high post. Full shot clock.

**1. The weight map.** O2's corner three is the heaviest look at the arc: a contest there takes a lot off it. O4's dunker spot carries rim weight, but only if the ball gets to him, and from the top it has to go past the paint. O1's drive carries rim weight. O3's three is modest. The centre sits in the paint, shaded right toward O2.

**2. Base positions.** X2 is on the line from O2 to the weight and close to him, because O2's threat is worth more than any help X2 could give. X4 drops deep toward the paint: O4 is no threat unless the ball reaches him, and the ball is far away. X3 sits between O3 and the paint, a little toward the weight. X1 is on O1, goal-side. X5 is between O5 and the rim.

**3. Arrows.** X1's wedge walls the middle and sends O1 toward O3's side, where the help is. X4 has one arrow on the lane to O4 and one toward O1's drive. X3 has one arrow on O3 and one on the skip lane to O4.

**4. The number.** O1's drive is walled toward help. O2's corner three is tightly guarded. The best looks left are O3's three on a swing pass and O4's dump-off if O1 drives left. The number is modest.

**5. The offence's answer.** It wants a look the defence cannot cover. O5 screens for O1 going right, toward O2. Now X2 must choose: help on the drive, or stay on O2. The link rule says stay, because O2's three is worth more than the help. So the drive has a cleaner path, and the number rises. If X2 helps instead, the kick-out to O2 is open.

**6. What it shows.** The defence's shape came from the weight. The offence's action came from the link rule it could break. Each choice moved one number. Nothing was a named play.

## What the player sees

The player should be able to see why, in basketball words, with the numbers on tap (step 19's rules).

- **The weight map** as a Coverage view: where a defender's presence saves the most right now, as shading with a pattern, and the centre of gravity marked.
- **Each defender's line:** his man, the weight, and where he stands between them. "X4 sags toward the rim: O4 is no threat from the corner while the ball is on the far side."
- **The offence's line:** attention, holes and access, as now, with the gap it is attacking and how many routes it is running. "Three screens at once: one go, and the lanes are blocked."
- **The number itself** as the phase score: what the possession is worth now, and what changed it.
- **Coaching for a human:** the same lines as tips, switchable off. The fundamentals checks double as training situations.

Separate thinking holds on screen: a human never sees the other side's plan (step 24).

## Board checks

Each check is one reading of one board, taking seconds. Each must fail if its principle is missing from the build. Together they are the fundamentals exam: every later step must pass all of them before anything new is built.

### The defence

| # | Board | Passes when |
| --- | --- | --- |
| D1 | A poor-shooting five | The defence's weight sits in the key and the defenders pack it |
| D2 | One elite shooter, four weak ones | One defender stays attached to him, and the other four sag |
| D3 | A mid-range shooter open at the elbow | The report says whether Shaun's cards concede it, and the defence acts to match |
| D4 | A non-shooter in the far corner, ball on the other side | His defender leaves him to help |
| D5 | An elite shooter in control, his defender three squares off | The defender closes to where he can contest with a Move |
| D6 | An elite shooter two squares past the arc at Senior Pro | His defender follows him out. At Junior, he does not |
| D7 | The offence needs a three to tie, last phase | The weight moves to the arc and the paint is left |
| D8 | Ball handler in the corner, dribble dead, lanes closed | A second defender comes to trap |
| D9 | Good passer at the top, lanes open | No trap |
| D10 | A helper leaves his man to stop a drive | Counted with the pass to the man he left, and a teammate rotates if that pays |
| D11 | Two bigs under the rim, entry pass possible | Each big near the rim is denied or defended: fronted or three-quartered in the passing lane when that lowers the number (he is still near the rim to help), or played behind or beside with the lane cut. Never left with no defender while the ball can reach him |
| D12 | Any board | No defender is guarding empty space with nothing to save there |

### The offence

| # | Board | Passes when |
| --- | --- | --- |
| O1 | A cutter catches under the rim, one late defender | He shoots |
| O2 | Two attackers in the key at a phase end | Both are out, or shooting, before the violation |
| O3 | Five attackers, full clock, ball at the top | No two share a segment, and none stands where he pins nobody |
| O4 | A non-shooting big | He starts at the dunker spot, the post or as a screener, not on the arc |
| O5 | A teammate in the driver's lane | He moves out of it, or the placement never puts him there |
| O6 | Baseline inbound under the rim, rim protected | Packed, several actions at once, outward |
| O7 | Corner inbound | Spread, one primary action and a fall-back |
| O8 | Sideline near half court | One cut or one screen |
| O9 | The top, last phase | Several actions at once |
| O10 | Full denial at the top | Spread wide, several actions at once |
| O11 | Any screen or cut the computer chooses | It raises the setup value. Remove it, and the value drops |
| O12 | The point guard two squares past the arc with no threat there | He moves to where he carries weight, or the report says what he gains by staying |

### Both sides

| # | Check | Passes when |
| --- | --- | --- |
| B1 | One reading everywhere | Setup, play, the coach's lines and the phase score all use points, with no second measure left leading anywhere |
| B2 | Both engines | Python and JavaScript give the same answer on every board above |
| B3 | Separate thinking | Changing one side's private plan does not change the other side's choice |
| B4 | The 20 November possession, replayed from its setup | None of its failures recur |

### Goal-side and the centre of gravity

- **G1:** on a normal board, every defender stands on the hoop side of his man, on the line to the weight, unless the report names what he gains elsewhere (a denial, a front with help behind).
- **G2:** the weaker his man's threat right now, the further along that line toward the weight he stands. Swap a shooter for a non-shooter and his defender drops.
- **G3:** move the weight (the need-a-three case) and the defenders' side of their men moves with it.
- **G4:** the defence's search, started from the goal-side shape and from a random shape, ends in the same place. If it does not, the search is too short to be trusted without the starting shape.
- **G5:** covering one of two equal looks leaves the number unchanged. Covering both lowers it.

Several checks above overlap (the trap, tight guarding, the five setup situations). Checks that share a situation may share one test board, but none is dropped: the build reports every check by its number.

## What was agreed, and where it is

Every point Shaun set out or agreed between 21 and 25 November, with where it sits in this document and the check that guards it. Nothing agreed is to be removed or weakened without a line here saying what changed and why. The build prompt carries this table, and Claude Code reports against it row by row.

| # | Agreed | Where | Guarded by |
| --- | --- | --- | --- |
| 1 | Each player's zones of average or better shooting are the places that demand a defender | Setup order, step 1 | O3, O4 |
| 2 | Sub-zones: green as one, mid-range in three, long two in four, five beyond the arc | Layer 2; setup step 3 | O3 |
| 3 | Players should not share a section while maximising their threat | Push and pull; setup step 3 (as a counted cost) | O3 |
| 4 | Distance kept large unless the plan needs players close, with no wasted phase | Setup steps 3 and 6 | O3, O6 to O10 |
| 5 | Secondary skills (dribble, screens) break ties, placed where they create the most | Setup step 4 | O11 |
| 6 | Order: scout, ball handler's start, possible positions, plan conditions, adjustments | Setup order | B4 |
| 7 | Get out of each other's way | Push and pull, principle 1 | O5 |
| 8 | Gaps in the key are worth the most | Push and pull | D11, O1 |
| 9 | Spread threats so each defender is pinned to one man | Variables: pin | O3, D4 |
| 10 | Push and pull between space and time; one formula for the stack and the spread | The offence | O6 to O10 |
| 11 | Little time means several actions at once, to spread the odds | How many actions at once | O6, O9 |
| 12 | Where the ball starts against the defence's centre of gravity decides access | Five situations table | O6 to O8 |
| 13 | Room and angles are a separate constraint from access; the corner inbound spreads | Variables; five situations table | O7 |
| 14 | Full denial is the same access case as being behind the centre of gravity | Five situations table | O10 |
| 15 | The team centre of gravity, built in three layers | Part 1 | D1, G1 to G3 |
| 16 | Layer 1: rating out of 20, open and contested, times points; the pull is the difference | Layer 1 | D3, G2 |
| 17 | Add the weights across five attackers for the base centre, between the hoop and the arc | Layer 1; centre of gravity section | D1 |
| 18 | Poor shooters give a packed key; one shooter gives a box-and-one; mid-range conceded | What should fall out | D1, D2, D3 |
| 19 | Layer 2: occupation, usually a small shift | Layer 2 | D4 |
| 20 | Layer 3: the ball's reach; one reachability factor with occupation | Layer 3 | D4, D8 |
| 21 | Individual assignments: the threat, the ball, the gaps | Part 2 | D10, D12 |
| 22 | The link rule: leave only when helping saves more than his man would cost | Part 2 | D4, D5, G2 |
| 23 | Defenders with no immediate threat move to the centre, now or projected | Part 2 | D12 |
| 24 | The centre of gravity keeps defenders on the right side of their men and the hoop | Centre of gravity section | G1, G3, G4 |
| 25 | A defender, or the whole team, can shift its weight: one player, or the three late | What should fall out | D2, D7 |
| 26 | No weighting between team and individual: both in points | Why no weighting is needed | G2 |
| 27 | The trap appears when lanes, access and angles are contained | The trap | D8, D9, A5 |
| 28 | The zone of influence and arrows are chosen with the square | Part 3 | A1 to A6 |
| 29 | Arrows maximise value reduction: weakest cover, angles and area toward the corners, two smaller passes against one bigger | Three things the arrows weigh | A8, A9, A10 |
| 30 | Speed is a gap like a dribble edge, contained under the same values | Advantages are gaps | A7 |
| 31 | The pass counts closeouts, failed intercepts and fakes | The pass makes gaps | A11 to A13 |
| 32 | Worth right now; the best legal contest; both sides at real chance; the map leads | Layer 1; the map and its centre | D7, D5 |
| 33 | The list kept, best look first, priced as the possession's value on the 1 to 39 scale | The one number | G5, B1 |
| 34 | Take the good shot; three seconds counted from entry; no action without purpose | Fixes that come with it | O1, O2, O11 |
| 35 | A fundamentals exam every step must pass | Board checks | all |

### Changed from what was first written, and why

| What | Change | Reason |
| --- | --- | --- |
| "No two players in the same section" as a rule | Now a counted cost, with segments as an aid | A fixed rule is the candidate-squares mistake; a stack needs players close |
| "Maximise distance" | Measured by help distance | Research: coaches stretch the help, not the gaps between teammates |
| Covered weight as a switch | Cover in degrees | A rushed contest covers less than a set one |
| The link rule as each defender's own method | The five solved together; the rule describes and checks the answer | Five separate decisions can all leave or none |
| The ball's reach in both layer 3 and the link rule | Counted once, in the map | It was counted twice |

### Rulings of 25 November

These came from Claude Code's step 31 plan and from step 30b. Where an older sentence in this document differed, it has been corrected in place.

| What | Now | Why | Standing |
| --- | --- | --- | --- |
| The read-ahead | Four turns, not three | D-268 (19 November) already set four | Agreed |
| A turn | 1 or 2 actions, from 6 a phase | The rules | The rules |
| Locked | A Quick Step is still allowed | The rules | The rules |
| A missed Intercept and a missed Steal | Each read by its own rule | The rules treat them differently | The rules |
| The low end of the scale | A shot never scores below 0; the contest is always at least 1 | The rules | The rules. Shaun to confirm he wants no change |
| Need a Three | A two is worth 0 | The card says only a three scores | Agreed |
| Whose contest in layer 1 | The best of the five for the team's map; his own for a defender's base position | The link rule compares what he saves | Agreed |
| Falling back through looks | Limited by the actions available | Tries aren't free in the game | Agreed |
| The defence's search | Also tries two defenders together | A switch or trap needs two | Agreed |
| The levels | How far ahead is a fixed number of turns, never a clock | The same board must give the same decision on every device | Agreed (Shaun, 25 November) |
| Speed | Only from never doing the same work twice, cheaper machinery, and using the whole device. Never from thinking about less | Speed and fidelity without dictating or restricting decisions | Agreed (D-283) |
| The block's reset | Not ruled yet | To be ruled once the new value shows what a phase after a block is worth | Open |
| The segments | The map below | Claude Code's proposal | **Provisional. Shaun has not ruled** |
| Later answers inside the number | Each side's later answer gets only the actions and time it will actually have | Step 31 read the answer as free later, so the defence waited instead of acting | Agreed (Shaun, 25 November) |

**The segments, square by square (provisional).** G: the green zone. ML, MM, MR: mid-range left, middle, right. LL and LR: the long two along each baseline. Ll and Lr: the long two above each elbow. CL and CR: the corners. WL and WR: the wings. T: the top. Deep squares count with the segment they sit behind. Two things are not settled: which side I8 and I9 belong to (marked ?), and whether the corner ends at row 5. Until Shaun rules, I8 and I9 count as in both Ll and Lr, so the board stays the same left and right, and the corner ends at row 5.

```
     A  B  C  D  E  F  G  H  I  J  K  L  M  N  O  P  Q
12   WL WL WL WL WL T  T  T  T  T  T  T  WR WR WR WR WR
11   WL WL WL WL WL T  T  T  T  T  T  T  WR WR WR WR WR
10   WL WL WL WL WL T  T  T  T  T  T  T  WR WR WR WR WR
 9   WL WL WL WL WL Ll Ll Ll ?  Lr Lr Lr WR WR WR WR WR
 8   WL WL WL Ll Ll Ll Ll Ll ?  Lr Lr Lr Lr Lr WR WR WR
 7   WL WL Ll Ll Ll ML MM MM MM MM MM MR Lr Lr Lr WR WR
 6   WL LL LL LL ML ML MM MM MM MM MM MR MR LR LR LR WR
 5   CL LL LL ML ML ML MM MM MM MM MM MR MR MR LR LR CR
 4   CL LL LL ML ML ML G  G  G  G  G  MR MR MR LR LR CR
 3   CL LL LL ML ML ML G  G  G  G  G  MR MR MR LR LR CR
 2   CL LL LL ML ML ML G  G  G  G  G  MR MR MR LR LR CR
```

### Still to be audited

Principles settled before 21 November (the danger of the pass, the contest as an action, deep range, fakes, separate thinking, and the rest in "Kept") each need a check that proves they are in the build. The build prompt asks Claude Code to list each one with its test, and to add a test where there is none.

## Open questions and limits

- [ ] **Catch and finish:** Shaun to rule (see above).
- [ ] **Mid-range:** is it conceded on the cards as they stand? Check D3 answers this.
- [ ] **How "worth right now" is set outside scenario cards.** In a normal possession it is the points. The need-a-three case needs the game or the scenario to say so.
- [ ] **Reaction rules after the first action** (drift to the corner, lift, fill behind the ball). They may fall out of reading the same sum every turn. To be checked on a drive-and-kick board before any rule is written.

### Not covered by this design

- **A safety player** above the ball for the release pass and for getting back. The game has no transition, so getting back has no value yet. The release pass is covered by access.
- **Who crashes the glass.** The game has no rebounds.
- **Computing time.** Set aside until the rules and the reading work (Shaun, 20 November). The weight map and the scout are the kind of data that can be cached later.
- **The table.** These are how the computer reads the game. No rule or card changes here.

### Sources for the established practice

The research of 21 November compared an earlier draft of this model with coaching and tracking sources. Its main finding is built in: coaches space to stretch the help, measured from the ball, not to maximise distance. Non-shooters belong at the dunker spot, the short corner, the high post or in a screening role, because FIBA has no defensive three seconds and their defender can sit in the key. The full report and its sources are in the project conversation of that date.
