# Playmaker goal library: offence goals and defence objectives

This is the reference for step 3i's goal-directed computer. Every entry is a real half-court basketball action, translated into Playmaker's legal actions. **No rule changes:** where an action can't be expressed by the current rules, it says so.

Put this in config (`goal_library.json` or similar) as data, so the designer can add, remove and reword entries without touching code.

## How to read an entry

- **Edge:** what the cards and board must offer for the goal to be worth ranking.
- **Conditions:** what must be true at the finish, so the planner can work backwards.
- **Chain:** the typical steps, in Playmaker actions. Any step may be replaced by another that meets the same condition.
- **Finish:** the action that cashes the advantage.
- **Answers:** the defence objectives that counter it, and what each answer gives up. A goal whose answer gives something else up is a dilemma, which is the point.

## Playmaker mechanics the library relies on

- **Screen.** A Screen sets a T. A defender's diagonal step that starts on the T square, or cuts its corner, is banned. Only the defender standing on the T square may Challenge, rolling Screen − Challenge:
  - **the screen holds:** that defender is locked;
  - **the Challenge succeeds:** that defender beats the screen, and may cross the T square but not stop on it.

  A screen lasts through the defence's turn and the offence's next turn. Limit: 2 Screens per side per phase.
- **Seal** is a Screen in the post, with the T aimed so the defender can't step between the post player and the entry passer.
- **Switch.** There's no switch rule. A switch happens when one defender is locked or out of reach, so a different defender has to be the one able to reach, contest or wall the attacker. The defence decides who.
- **Ball screen** (pick and roll). An off-ball player Screens with the T on the ball carrier's defender, so the carrier's next movement or Dribble goes past them. The screener then rolls (moves toward the rim) or pops (moves to the three-point line).
- **Arrow lines** wall drives (the carrier can't cross an adjacent defender's line without winning a Dribble) and threaten passes (on the line, or arrow across it plus one movement).
- **Capacity limits that make movement matter:**
  - Move: once per player per phase;
  - Quick Step: once per player per phase, 2 per side;
  - a Quick Step can't turn the arrow;
  - a Sprint faces the way it ran;
  - 6 tokens per side per phase, 2 actions per turn;
  - Pass, Dribble, Screen, Intercept, Steal and Challenge: 2 each per side per phase;
  - Pause and Hesitate: 1 each per team per phase.
- **Out of scope:** rebounds, transition and deliberate fouling. The nearest thing to a deliberate foul is the Steal on a declared shot (see the defence's on-ball objectives).
- **Handoffs don't use the Screen mechanic.** The passer's body blocks the chasing defender by occupying a square (D7).

---

# Part 1. Offence goals

## A. Use an existing edge (finish what the cards already give)

**A1. Post entry**
- **Edge:** a ▲ post scorer against a ▼ post contest (or a size gap after a switch).
- **Conditions:**
  - the post player holds a seal on their defender;
  - a passer has a clean entry lane;
  - the passer has the ball.
- **Chain:**
  1. Move the post player to the block.
  2. Seal (Screen, T on the defender).
  3. If the entry lane isn't clean, swing the ball to the side with the clean angle (A1a below).
  4. Enter.
- **Finish:** a post shot, or a kick-out if help comes (C3).
- **Answers:**
  - **front the post:** the defender stands between the ball and the post, arrow to the ball. This gives up the lob over the top or a high-low entry (A2);
  - **three-quarter front;**
  - **dig with a guard** (help from the entry passer's defender). This gives up a kick-out to that guard's player.
- **A1a. Re-entry angle.** When the post is fronted on one side, swing the ball twice to the far wing so the entry lane is clean, and re-seal from that side. Each swing pass must itself be clean: the receivers move first (B1, B2).

**A2. High-low**
- **Edge:** a post player sealing low, with a teammate at the high post or elbow who can pass (Pass ▲ preferred).
- **Conditions:**
  - the high player has the ball;
  - the low player holds a seal on the side away from the high player;
  - the lane between them is clean.
- **Chain:**
  1. Enter to the high post.
  2. Seal low, on the far side of the defender.
  3. Pass down.
- **Finish:** a post shot or a layup.
- **Answers:**
  - **front or three-quarter front low,** which gives up a lob, or the high player's own shot or drive;
  - **sink the high player's defender,** which gives up the high player's mid-range or long-two shot.

**A3. Isolation**
- **Edge:** the carrier's Dribble beats an adjacent defender's Agility, and a ▲ shot is reachable past them, with no help in reach.
- **Conditions:**
  - the carrier is adjacent to the defender they're attacking;
  - help defenders are spent or far (C1);
  - space beyond the arrow line is empty.
- **Chain:**
  1. Clear the side: move teammates away, taking their defenders with them (B4).
  2. Dribble.
  3. Move into the zone.
- **Finish:** a shot.
- **Answers:**
  - **wall the drive** with the arrow line;
  - **help early** (a gap or nail defender), which gives up the helper's player;
  - **load to the ball side,** which gives up the weak-side three.

**A4. Spot-up three**
- **Edge:** a ▲ three-point shooter, with their defender out of clean reach.
- **Conditions:**
  - the shooter stands on a three square;
  - a clean pass lane to the shooter exists;
  - no defender can reach a clean contest in the reaction, or only a Behind contest or a foul-roll contest.
- **Chain:** whichever of C1 to C4 empties the closeout, then the pass.
- **Finish:** a three.
- **Answers:**
  - **stay home** (don't help off the shooter), which gives up the drive or the post;
  - **top-lock or deny** the shooter's catch, which gives up the back cut (B3).

**A5. Mid-range or floater in the gap**
- **Edge:** the carrier's ▲ mid-range or floater rating, where defenders drop to protect the rim.
- **Conditions:** the carrier reaches a mid-range square with the nearest contest only from Behind or with a foul roll.
- **Chain:** a ball screen (D1), with the screener's defender dropping, then the step into the gap.
- **Finish:** a mid-range shot or a floater.
- **Answers:**
  - **at the level or hedge,** which gives up the roll to the rim;
  - **a switch,** which gives up a mismatch.

## B. Get open (off-ball movement that spends defenders)

**B1. V-cut**
- **Edge:** a receiver's defender who will follow.
- **Conditions:** the defender has spent their Move this phase following the cut in, or stays put and gives up the inside.
- **Chain:** Move in (this phase), then Move out to the catch spot (next phase). A Quick Step out is optional.
- **Finish:** a clean pass to the receiver, then that receiver's next goal.
- **Answers:**
  - **don't follow, sag:** keeps capacity, but gives up the inside cut;
  - **follow and recover next phase:** spends the Move.

**B2. L-cut**
- **Edge:** the same as B1, at the elbow or wing.
- **Chain:** Move up the lane line, then out to the wing.
- **Finish:** a clean catch.
- **Answers:** as B1.

**B3. Backdoor cut**
- **Edge:** a defender whose arrow faces the ball or the passing lane (denying or overplaying).
- **Conditions:** a path behind that defender to the rim zone, and a lane for a pass there that the defender can't answer.
- **Chain:** Move toward the ball (the defender denies), then Move or Sprint behind them to the rim.
- **Finish:** a layup.
- **Answers:**
  - **play off the catch** rather than denying, which gives up a clean catch on the wing;
  - **help-side tag at the rim,** which gives up the helper's player.
- **B3a. Dribble-at backdoor:** the carrier moves toward an overplaying defender, pushing them back, and the receiver goes behind.

**B4. Shift away (lift, drift, flare)**
- **Edge:** a ▲ three-point shooter whose defender is the nearest help on the ball.
- **Conditions:** the defender must now choose between following (losing help reach) and helping (losing the closeout).
- **Chain:** Move the shooter away from the ball, along the arc.
- **Finish:** the ball attacks that defender's help job (A3, D1), or the shooter catches (A4).
- **Answers:** this is the dilemma (C2). The defence must hand one of the jobs to a defender with capacity left (a rotation).

**B5. Baseline cut, corner to corner** (Iverson-style along the baseline)
- **Edge:** a defender who must chase through traffic.
- **Conditions:** at the end of the cut, the chaser is Behind or facing away, and can't answer the pass on the far side.
- **Chain:** Move along the baseline under the rim, then Move out to the far corner next phase. Screens on the way (E2) strengthen it.
- **Finish:** a corner three, or a layup if the chaser trails.
- **Answers:**
  - **switch or bump the cutter** to a defender already on that side, which gives up that defender's player;
  - **trail and recover,** which spends capacity.

**B6. Face cut (give and go)**
- **Edge:** the passer's defender relaxes or turns their arrow to the ball after the pass.
- **Conditions:** a path in front of that defender to the rim zone.
- **Chain:** Pass, then Move to the rim (next turn).
- **Finish:** a return pass and a layup.
- **Answers:** **jump to the ball** (move toward the ball after the pass), which spends a Move.

**B7. Shallow cut or replace**
- **Edge:** the carrier needs the side cleared, and a teammate can relocate to an open lane behind them.
- **Chain:** Move inside the carrier, out to the corner or wing.
- **Finish:** space for A3, or a clean safety pass.
- **Answers:** **stay connected**, at a capacity cost.

**B8. 45 cut, into the gap**
- **Edge:** the help-side defender is occupied by a ball screen or a baseline drive.
- **Chain:** Move into the gap behind the defence, timed with D1 or A3.
- **Finish:** a layup or floater, from a pass.
- **Answers:** **the low man rotates,** which gives up the weak-side corner.

**B9. Veer cut**
- **Edge:** a defender who reacts to approach.
- **Chain:** Move toward the defender, then Move away the next phase.
- **Finish:** a clean catch.
- **Answers:** as B1.

## C. Bend the help (make the defence choose)

**C1. Drain the closeout, then shoot**
- **Edge:** a ▲ shooter with exactly one defender able to close out cleanly.
- **Conditions:** that defender's Move is spent, or the defence's tokens are down to the point where the reaction can't reach.
- **Chain:** ball reversals, cuts (B1, B4) or drives that make that defender, or the pool, spend.
- **Finish:** the pass and the three.
- **Answers:**
  - **rotate a fresh defender** onto the shooter;
  - **hold a reaction in reserve** (keep a token, keep that defender's Move).

**C2. Two-job defender (the dilemma)**
- **Edge:** one defender is the only answer to two threats this phase: the help on the drive and the closeout on their shooter, or two passing lanes.
- **Conditions:** the offence can attack either threat after seeing the defence's choice.
- **Chain:** B4 or B5 to create it, then attack whichever job the reply leaves open.
- **Finish:** a drive, or a shot by the shooter.
- **Answers:** **a rotation that hands one job to a defender with capacity left,** which moves the problem one player along (C3).

**C3. Drive and kick, and the extra pass**
- **Edge:** the carrier's drive pulls help from a ▲ shooter's defender.
- **Conditions:** the helper has committed (moved off their player) and can't recover cleanly. The kick lane is clean.
- **Chain:** A3 or D1 to the paint, then a kick to the helper's player. If that player's defender rotates, an extra pass to the next player along.
- **Finish:** a three, or a closeout attacked again (A3).
- **Answers:**
  - **stunt and recover** (fake help, then return), which costs capacity;
  - **X-out rotation,** which needs two defenders with capacity left.

**C4. Skip pass**
- **Edge:** the defence has shrunk to the ball side.
- **Conditions:** a clean lane to the weak side over the top: no arrow across it that a defender can answer.
- **Chain:** the receivers move first to open the lane (B1, B4), then the skip.
- **Finish:** a three, or an attack on the closeout.
- **Answers:** **the weak-side defender plays the lane** (arrow across it), which gives up their own player's cut.

**C5. Overload one side**
- **Edge:** more offence threats on one side than defenders who can still reach them.
- **Chain:** move three attackers to one side, so the defence must commit help.
- **Finish:** an open player on the overloaded side, or a skip to the far side (C4).
- **Answers:** **zone the far side** (one defender covers two weak-side players), which gives up the skip.

## D. Ball screens (pick and roll and its family)

**D1. Pick and roll**
- **Edge:** a carrier who can attack (Dribble or a ▲ mid-range/floater/layup), and a screener who can finish at the rim (▲ layup or dunk).
- **Conditions:** the screen holds on the carrier's defender (locked), or that defender beats it but loses position. The screener's defender must choose between the ball and the roll.
- **Chain:**
  1. Move the screener next to the carrier's defender.
  2. Screen, with the T on that defender.
  3. Carrier: Move or Dribble past.
  4. Screener: roll (Move toward the rim) next turn.
- **Finish:** the carrier's shot, the pass to the roller, or a kick (C3).
- **Answers** (the coverages), each expressed with positions and arrows:
  - **drop:** the screener's defender stays deep near the rim, arrow up the lane. Gives up the pull-up, the floater and the pop (D2);
  - **at the level:** the screener's defender steps up level with the screen, with an arrow-line wall on the drive. Gives up the roller, unless a weak-side defender tags him;
  - **hedge or show:** the screener's defender steps out to wall the carrier, then recovers. Gives up the roll for a beat, and needs a tag;
  - **blitz or trap:** both defenders adjacent to the carrier, arrows on, threatening a Steal. Gives up the screener in space and leaves the defence 3 on 4 behind;
  - **switch:** the defender who can reach takes the carrier, and the other takes the screener. Gives up a mismatch (E1);
  - **ice or down:** the on-ball arrow walls the drive toward the screen and forces the carrier to the sideline. Gives up the long two and the pop.

**D2. Pick and pop**
- **Edge:** a screener with ▲ three-point or long-two shooting.
- **Chain:** as D1, but the screener moves to the three-point line.
- **Finish:** a catch-and-shoot three.
- **Answers:**
  - **switch;**
  - **at the level and recover,** which needs capacity.

**D3. Slip**
- **Edge:** the screener's defender commits early (hedge or blitz posture).
- **Chain:** the screener moves to the screen spot, then, instead of screening, Moves or Sprints to the rim.
- **Finish:** a pass and a layup.
- **Answers:** **a weak-side tag at the rim.**

**D4. Ghost screen**
- **Edge:** as D3, for a popping shooter.
- **Chain:** approach as if to screen, then Move out to three.
- **Finish:** a three.
- **Answers:** **stay home with the screener,** which gives up the ball side.

**D5. Spain pick and roll**
- **Edge:** a D1 position where the roller's defender drops.
- **Chain:** D1, plus a second Screen (the side's second of the phase) by a third player on the dropping defender, as the roller goes.
- **Finish:** the roll, or the back-screener popping to three.
- **Answers:** **switch the back screen,** which gives up a mismatch.

**D7. Handoff (dribble handoff)**
- **Edge:** a receiver who can attack or shoot off a catch on the move, and a passer whose piece can stand in the receiver's defender's path.
- **Conditions:** the passer is adjacent to the receiver, and the short pass between them is clean. The passer's square lies across the path the receiver's defender needs to follow.
- **Chain:**
  1. The carrier Moves next to the receiver.
  2. Pass to the adjacent receiver: a short lane, normally clean.
  3. The receiver Moves or Sprints past the passer's piece. The chasing defender must go round the occupied square.

  No Screen action is used.
- **Finish:** a drive (A3), a pull-up (A5) or a three (A4). Or the passer rolls (Moves) to the rim next turn.
- **Answers:**
  - **switch the handoff:** the passer's defender takes the receiver, which gives up the passer rolling;
  - **jump the handoff:** a defender steps into the short lane to threaten it, which gives up the back cut by the receiver.

**D6. Re-screen and change direction**
- **Edge:** the on-ball defender beat the first screen by going over it in one direction.
- **Chain:** reset, then Screen again from the other side, the next turn or phase.
- **Finish:** as D1.
- **Answers:** as D1.

## E. Create mismatches

**E1. Screen to switch, then exploit the size or speed gap**
- **Edge:** the switch would leave a ▼ defender on a ▲ attacker: a small defender on a post scorer, or a slow big on a quick guard.
- **Conditions:** the screen holds or forces the other defender to take the attacker. Then the attacker has the matching edge (A1 against the small defender, A3 against the slow one).
- **Chain:** D1, or an off-ball screen (E2) aimed to make the right defender pick up. Then reposition: post up the smaller defender (A1), or isolate the slower one (A3).
- **Finish:** A1 or A3.
- **Answers:**
  - **switch back** (a re-switch), which needs a defender with capacity left;
  - **a dig or double on the mismatch** (C3 follows).

**E2. Off-ball screens**
- **Edge:** a ▲ shooter or cutter whose defender can be screened.
- **Conditions:** the screen holds (that defender is locked) or diverts them, so the cutter catches before a clean contest is reachable.
- **Chain:** a Screen with the T on the cutter's defender, then the cutter moves off it. Variants:
  - **down screen:** a screener comes down to the post; the shooter cuts up to the wing;
  - **pin-down:** a down screen from the wing toward the baseline;
  - **flare:** screen away from the ball; the shooter fades to the far wing;
  - **back screen:** screen behind the defender; the cutter goes to the rim;
  - **UCLA:** a back screen at the high post for the passer, after the entry pass to the wing;
  - **stagger:** two screens in sequence. That's the side's two Screens for the phase;
  - **double:** two screeners side by side. Also both Screens;
  - **floppy:** the shooter starts under the rim with screens on both sides. It needs three screens, so it runs over two phases: two Screens in the first phase, the third in the next;
  - **cross screen:** one post screens across for the other;
  - **zipper:** a screen for a guard coming up from the block;
  - **corner pin:** a flat screen along the baseline for the corner;
  - **screen the screener:** the screener's defender screened next.
- **Finish:** A4, A1 or B3.
- **Answers:**
  - **chase over the top,** with a Challenge from the T square, a Move and a lost facing;
  - **shoot the gap** (go under), which gives up the curl;
  - **switch,** which gives up E1;
  - **top-lock** (deny the curl side), which gives up the back cut.

**E3. Speed against slow feet**
- **Edge:** an attacker with Quick Step 2 against a defender with Quick Step 0.
- **Chain:** a Sprint or a straight-line burst to a square the defender can't reach in a reaction.
- **Finish:** a shot or a catch.
- **Answers:** **help from a faster defender,** which gives up that defender's player.

## F. Clock and situation goals

**F1. Late clock: the best available.** With one phase left, rank goals only by what can finish now. The patience curve governs the shot.

**F2. Need a Three.** Only goals that finish in a three score. A1 and A5 drop out unless they kick to a three.

**F3. Coach's Call.** The secret target's goals get the bonus value from the card. The defence doesn't see the target, so its objectives treat every attacker as a possible target.

**F4. Inbounds.** The defence answers the inbound pass with its full turn. Goals for the first pass are B1, B2, B3 and E2 into a clean lane, then a normal goal once the phase resets.

---

# Part 2. Defence objectives

The defence ranks these each turn by the value to the offence of what they stop, weighted by how close the board is to that goal (read only from what it can see), and spends capacity on the top ones.

## On the ball

- **Contain:** arrow-line walls on the carrier's best drive, away from their ▲ zones. Counters A3 and D1. Gives up the opposite direction.
- **Force sideline or baseline** (ice): wall the middle. Counters D1 toward the middle. Gives up the long two and the baseline.
- **Pressure:** arrow on the carrier, threatening a Steal. Counters slow ball movement. Risks a foul (Steal foul roll) and the drive past.
- **Trap or blitz:** two defenders adjacent and on. Counters a star carrier. Gives up the open fifth player.
- **Reach on the shot** (the nearest thing to a deliberate foul): a Steal after the shot is declared. A foul gives the free throws or the open shot, whichever is higher, so the foul never helps the defence. A successful steal ends the possession at −5. Use it only when P(no foul) × P(steal) × the shot's value beats the foul risk, against a ▼ ball-handler.

## Ball screens

- **Choose a coverage per action** (drop, at the level, hedge, blitz, switch, ice), by the screener's threat:
  - drop against a roller who isn't a shooter;
  - switch or at-level against a popper;
  - blitz against a ▲ carrier with a ▼ screener.
- **Challenge from the T square** when the screen's hold chance is low (Screen − Challenge).

## Off the ball

- **Deny** (arrow across the passing lane): counters A4 and C4 for that receiver. Gives up the backdoor (B3).
- **Face-guard** (arrow on the receiver, body in the lane): counters a ▲ shooter's catch. Gives up the backdoor and help.
- **Top-lock:** counters curls off E2. Gives up the back cut.
- **Sag or sink:** gives help on the ball and keeps capacity. Gives up the shooter's catch. That's the comfort-line choice: concede it when the shooter is ▼.
- **Gap or nail help:** stands between the ball and the rim off a ball-side player. Counters A3. Gives up the kick (C3).
- **Tag the roller:** a weak-side defender steps to the rim. Counters D1's roll. Gives up the weak-side corner.
- **Stunt and recover:** step toward the ball, then back, across a turn or phase. It slows a drive while keeping the closeout, at a capacity cost.

## Rotations

- **Help the helper:** when a defender helps, the next defender takes their player. Counters C2 and C3.
- **X-out:** two defenders swap assignments after a skip. Counters C4. Needs both to have capacity.
- **Switch back** (a re-switch): restores a matchup after E1. Needs capacity.
- **Bump:** a defender already on the far side takes a cutter (B5).

## The post

- **Front:** between the post and the ball, arrow to the ball. Counters A1. Gives up the lob and the high-low (A2).
- **Three-quarter front:** on the high or low side. Counters the entry from one side. Gives up the other side (A1a).
- **Dig:** a guard helps on the post catch. Counters A1. Gives up a kick-out.

## Capacity management (every turn)

- **Keep a reaction in hand:** at least one token, and the likely closeout defender's Move.
- **Don't chase every cut:** follow only when the cutter's threat beats the help that following gives up.
- **Watch the clock:** with the offence's chain short of time, sit in the best-value coverage and let the clock work. With a lot of clock left, prefer coverages that keep capacity.

---

## Levels (how much of the library each level uses)

| | Offence goals | Defence objectives |
|---|---|---|
| **Rookie** | A1 to A4 directly, no chaining | On the ball (contain, pressure); post front; no rotations |
| **Starter** | A, B1 to B4, C1, C3, D1, D2, E2 (one condition deep) | Adds the coverages and deny/sag, plus help the helper |
| **All-Star** | Everything, chained fully | Everything, including rotations and capacity management |

## Sources

These are the basketball definitions the entries are translated from:
- [Basketball Cuts – 18 Different Types (The Hoops Geek)](https://www.thehoopsgeek.com/basketball-cuts)
- [17 Basketball Screens (Breakthrough Basketball)](https://www.breakthroughbasketball.com/play.asp?id=8135)
- [How to Identify Pick-and-Roll Coverages (The Basketball Action Dictionary)](https://medium.com/thebasketballactiondictionary/how-to-identify-pick-and-roll-coverages-a1e8dffe54e9)
- [Advantage Basketball (Taylor Jannsen)](https://taylorjannsen.substack.com/p/advantage-basketball)
- [Advantage Creation (Sportplan)](https://www.sportplan.net/drills/Basketball/trends/advantage-creation-attacking-rotations-2025-07.jsp)
