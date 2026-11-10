## The design (Shaun's goals design, signed off 10 November)

You can't open Shaun's design doc, so here it is in full where it matters.

**A goal is an advantage to create, keep and convert, in a place where it pays.** Tactics are the means: screen, pick and roll, cut, seal, swing pass, relocate, screen away, drive, drain a defender. The shot is the outcome. An open shot is not an advantage (D-94): the offence wants a look above what its possession is worth now, and the defence may concede looks below what it can live with.

**Four kinds of offensive advantage**, each computed from the board, never assumed:

| Advantage | It exists when |
|---|---|
| **Mismatch** | The attacker's tier for an action is above his defender's tier for the answer, in a location where that edge pays, or where using it lets him move freely into one. Two tiers higher is a strong advantage; one tier, an advantage; the same tier, a gamble worth it only for a high payoff; a lower tier, a poor or desperate choice. Tier informs, never dictates: location, coverage and the possession's worth still decide. A locked or spent defender, or a switch that puts a big on a guard, makes one. |
| **Numbers** | An area holds more threats than the defensive capacity allocated to it (the coverage budget). |
| **Separation** | A receiver or shooter has space and time: no defender can Contest or deny him in time (the reach map). |
| **Penetration** | The ball can get into the paint or to the rim (the reach map, blockers included, over two phases). |

**Every goal has three stages, each measured on its own:**

1. **Create:** is the advantage established?
2. **Keep:** can it be held against the defence's answers while the offence works the ball?
3. **Convert:** can it be turned into a look that beats the possession's worth?

**The four questions behind every goal, looking two phases ahead:**

1. Which action sets give me an advantage and force the defence to choose between two bad options, or take risks?
2. Where on the court should they happen?
3. What spacing keeps the defence's commitments and lets me execute?
4. What actions and timing stop the defence nullifying it?

**Success** is seeing it through to a shot, unless the defence thwarts it or the clock demands otherwise. **Failure** is a new goal, chosen with the clock in mind. **Goals chain:** Shaun's pick and roll creates a switch (goal 1, a mismatch), then the big seals the smaller defender while the ball swings to open the passing angle (goal 2, kept over several phases), then the post entry converts.

**The defence mirrors the offence:** prevent the advantage forming, break it before it converts, deny the conversion, concede (choose what to give up, computed), run them down (the clock). On matchups the defence works the reverse way: it closes tier gaps before using its own edges, and a strong defender on a weak attacker is wasted.

**What a goal is worth,** in plain expected points with nothing counted twice. Goal worth = the converted look's expected points (after the defence's best answers) × the chance of creating and keeping it in the phases left (the defence replying), minus what the possession is worth without it.

**How goals steer the computer:**

- **Goals order the search.** Moves that advance a top goal are searched first; others are admitted after, so a better move is never ruled out.
- **Progress shows as a change in potential, not a prize.** A move earns (the goal potential after) minus (before). The potential is 0 when the possession ends, so the bonuses cancel over a possession and can't change which move is best in the long run (potential-based shaping, Ng, Harada and Russell, 1999). With a short search that isn't a guarantee, so it's tested.
- **One advantage, counted once.** The converted look is already in the position's value; the goal adds only the progress term.
- **Three separate events:**
  - advantage ready: execute, unless something better exists now;
  - advantage lost: drop it, pick the best new goal for the time left;
  - clock calls: convert the best look available.
- **Switching** only when another goal beats finishing the current one by more than the measured margin of error. No sunk-cost term (D, ruled 10 November).
- **The computer holds as many goals as the board offers.** The limit of one or two is only what the coach shows a player (a later stage).

**"It depends":** no fixed distances, no coaching rules of thumb, no fixed plays. Goal types are vocabulary; whether one applies, where and how big is computed from this board every time.

