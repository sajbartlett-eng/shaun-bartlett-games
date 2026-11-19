# The setup plan: scout, tolerance, the offence's plan, then the defence (Shaun, 19 Nov 2026)

## Shaun's design, in his words

> "First comes the scout for both teams. I imagine that this includes a review of every shot type for every offensive player. Example: O1 three pointer in the blue zone: open, rushed open, controlled and fully contested by X1, rushed and fully contested by X1, controlled and contested from behind by X1. I'll need you to generate the full list. Court zone specific shooting by matchup and weighted to the court zone. For example, beating a defender with a dribble is more valuable where it provides the offence with more passing and driving angles and space to create separation without going away from the hoop. Near the middle at the three point line is great for that. In the green zone is poor. That's why slow centers can guard fast guards sufficiently in the paint compared to out at the three point line."

> "Once we have the location and matchup based scout locked for both teams, both teams can calibrate their phase by phase shot tolerance tailored to those matchups to determine exactly what matchups they want to chase and avoid in preference order."

> "The offence sets up first, assuming the defensive matchups that will be generated, by positioning the players in a way to create the advantages needed to generate the first preference shot with backup shots planned for if that fails. This could be to use a combination of speed advantage, offball movement, passing and screens to create the advantages and separation over a multiphase plan. It could be 'create an open three for O2, rushed accepted, contested by X2, X3, X4, X5 not accepted. These shots also accepted...'"

> "The offence is then set in order to stretch and challenge the defences zone of influence as much as possible while also setting up efficient execution of its goal. You want to engage defensive responsibility to players so that the defence cannot focus on closing the gaps in its zone of influence. This means that a poor shooting centre is a threat in the post or setting up a screen rather than just sitting on a corner three where the defence can cover higher value squares."

> "Then the defence sets up. We keep everything that has been working for us."

## The game, in one line (Shaun, 19 Nov)

> "This is really the offence predicting the split of responsibility between the defender and zone coverage. So the offence is trying to maximise every defender's attention to a single player while minimising their coverage of gaps in the team zone of influence. Then in play, take advantage of their existing and created advantages to be able to gain separation into a high value shot scenario with poor or no zone of influence. You're managing attention, then creating holes, then exploiting ways to access those holes. That's the game. The defence is trying to manage holes and constrain the offence away from accessing them when they form."

- **The offence:** manage attention, then create holes, then exploit the ways to access them.
- **The defence:** manage the holes, and keep the offence away from them when they form.

Both use the same model of a defender: the pull between his man and the gaps (step 22b). The offence predicts that split; the defence lives it.

## Each side thinks alone (Shaun, 19 Nov)

> "Ideally, the defence and offence computers would be separate such that they do not have access to each other's goals and thinking."

**What each side knows:**
- the board, the rules and all ten cards (what a real scout knows);
- its own scout, goals, plan and predictions.

**What it never sees:** the other side's goals, plan, scout updates or chosen preferences.

**How it reads the other side:** wherever a side's search needs the other side's reply, it uses its own model of that side, the other side's logic run on public information and its own predictions of their choices. It never uses their real goals or plan. So the offence's search predicts the defence's settlement without the defence's private goals, and the defence's search never knows the offence's plan; it sees only what the offence does.

## Stage 1: the scout (both teams, before setup)

### 1a. The shot review

For every attacker, every shot type the rules allow, and every square (grouped by zone: green, mid-range, long two, three), against every defender on the other team, apply the contest rules exactly as they stand (D-191, D-193, D-194, D-198, the screen rule).

**The shooter's state:**
- **Set:** his last movement this phase was a Move, or he has made none.
- **Rushed:** Quick Step or Sprint, or locked; his shot is 2 lower.

**Each defender case, taken for both shooter states:**

| Defender when the shot goes up | Jump shot (mid-range, long two, three) | Inside shot (layup, dunk, post, floater) |
|---|---|---|
| Nobody can contest | Open | Open |
| Square in front, arrow on him, set | Full contest rating | Full, never a foul |
| Square in front, arrow on him, rushed | Full −2 | Full −2, never a foul |
| In front with arrow off, or beside, set | −3 | Hand up −3; or the block: full, 1 foul roll in front, 2 beside |
| Same, rushed | −5 | Hand up −5; or the block: full −2, same rolls |
| Behind, set | −6 | Hand up −6; or the block: full −3, 2 foul rolls |
| Behind, rushed | −8 | Hand up −8; or the block: full −5, 2 foul rolls |
| On a screen's T square, the arrow on the shooter blocked | As not square | As not square |

**Applied throughout:**
- Every contest takes at least 1 (D-193).
- Only the best contest counts.
- No shot from the rim square (D-198).
- A foul is +5 plus the free throws, or +5 plus the and-one.
- The block's value includes its foul rolls at the defender's Contest foul rating.

That makes 14 cases per jump shot and 22 per inside shot. Each case's value is the points times the chance, on the game's scale.

### 1b. The movement review: where a won Dribble is worth something

For every attacker against every defender, on every square:
- **The chance he beats him:** Dribble against Agility, by the rules, with his Quick Steps for speed.
- **What a win is worth there:** how much the offence's options grow after it (driving lanes, passing angles, room to separate without going away from the hoop), measured by the coverage map before and after. Nothing is ranked by hand. Shaun's expectation, as a check: large at the top of the key near the middle, small in the green zone.

That is why a slow centre can guard a fast guard in the paint and not at the arc. It must fall out.

### 1c. The matchup table

For every attacker against every defender:
- the best value from 1a in each zone;
- the dribble beat from 1b in each zone;
- the pass, the screen and the post-up where the cards make them matter.

Each team's scout holds both its offence's table and its defence's table. The scout report shows it in plain words, with the numbers on tap.

## Stage 2: shot tolerance and preferences, phase by phase

- **Shot tolerance:** a shot is acceptable in a phase when its value beats what playing on is worth from that phase. Use the shot clock by the rules (D-226), never a number set by hand. The bar falls as the clock runs down.
- **Matchups to chase and to avoid:** from the table, each side ranks the matchups by how much they clear or miss the bar, in preference order.
  - **Offence:** which attacker against which defender, in which zone, gives the best acceptable shots.
  - **Defence:** which matchups it must avoid, and which it can afford.

## Stage 3: the offence's plan (the offence sets up first)

- **Assume the defence's matchups:** predict the defence's settlement using the defence's own setup logic (stage 5).
- **A first-preference shot and its acceptance spec.** The spec is not written by hand: it falls out of the stage 2 bar applied to the scout's cases (which contests leave the shot above the bar in its phase). Shown in Shaun's form, for example:
  - "Create a three for O2 on the left wing: open accepted; rushed open accepted; contested by X2, X3, X4 or X5 not accepted."
  - Then backups in order, each with its own spec, for example: "O5 posting X2 after a switch; O1's drive at X5 at the top."
- **A multi-phase route to it, found by search, not named** (D-156): the combination of speed advantage, off-ball movement, passing and screens that creates the separation. The plan is the offence's preference only when values are level: whatever is worth most at its real chance of happening wins (stage 6). It is never compared ahead of a better opportunity.

### Building the plan: candidate squares, conditions and branches (Shaun, 19 Nov)

Shaun: "The computers need to be smart about how many turns and phases are needed to look ahead to achieve their goal. Creating an open layup off a high pick and roll play could well be a three phase execution path. Because the shot is actually for the corner player diving to the basket while his defender commits to the rolling big."

Shaun: "I think we have enough from the offensive setup position logic to set a number of possible starting positions for each player and rule out others. Start from there. Then follow your conditions logic to get to outcomes and lock in positions. For example, for the screen, roll and draw defender for an open layup scenario to work, the screener needs to occupy one of these squares. Then you can also have conditional logic, like if the screen fails, swing the ball to O2 on the wing and isolate his potential drive by screening away for O3. These are just examples. Conditional logic works from the scout and it is recognised that there are multitudes of ways to achieve goals, including bigs sealing smaller players and creating passing lanes to them."

**Why conditions and not predicted positions:** predicting exact squares phases ahead compounds error. A plan is held as conditions, relationships that the map can measure on any board. Prediction only reaches one phase ahead, where the search is reliable.

1. **Candidate squares for each player.** From the scout and the placement logic, keep for each attacker the squares where his card makes him a real threat that holds a defender's attention, or gives him a role in creating access: a shooter's spots, a post scorer's post squares, a screener's squares within reach of the ball handler's likely defender, a cutter's spots behind help. Rule out the rest. The short lists come from the cards and the map, never from a named spot.
2. **Scenarios as conditions.** Each scoring scenario in the scout that clears the bar (best first; any cap stated and flagged) is held as:
   - **a target condition:** for example, "O3's defender pulled toward the roller, and O3 has a route to the rim nobody can contest in time";
   - **the conditions that build it, by attention, holes and access:** for example, "the ball handler's defender screened; the roller's defender committed; X3's pull toward the roll greater than his pull to O3";
   - **the roles those conditions need,** each satisfied by some of the candidate squares. For example, the screener must start on one of the squares from which phase 1 can set the screen on the ball handler's likely defender.

   Bigs sealing smaller defenders and passing lanes into them, off-ball screens, cuts, speed against slow defenders: there are many ways, and each is a set of conditions from the scout. None is a named play (D-156).
3. **Branches, from the scout.** For each scenario, the conditions that would mean it has failed (the screen beaten, X3 staying home), and the scenario whose conditions are closest to true when that happens. For example: "if the screen fails, swing to O2 on the wing and screen away for O3 to isolate his drive." Branches are found by asking which scenario the failure makes most available. They are not written by hand.
4. **Lock in the placement.** Choose the squares, from the candidates, that satisfy the roles of the scenario worth most at its real chance against the predicted defence (predicted one phase ahead: its setup and its first answer), while also keeping its branches' roles available and every defender engaged. That one measure is stage 4's.
5. **In play: measure, push, branch.** At each phase start, read the conditions on the actual board.
   - **Still building:** the search pushes them further. Each phase's progress is how far it moves the target's conditions, valued at what the rest of the scenario is worth from there.
   - **Failed:** move to the branch the scout gave, or to whatever the defence opened.
   - **Always:** a better opportunity at its real chance wins (stage 6).

   Prediction never reaches beyond the next phase. The three-phase play emerges because each phase pushes the same conditions further.
6. **The defence never sees the plan** (each side thinks alone). It reads the conditions it sees forming (a big near the ball, a corner defender drifting toward a roll) with its own model, and manages the hole before it opens.

## Stage 4: the offence's placement

**One measure:** the value of the offence's best plan, at its real chance, against the defence's predicted best setup to that placement. That value has three parts, all read from the predicted settlement:
- **attention:** how strongly each defender is pulled to his man, by his man's threat there;
- **holes:** the gaps left uncovered because the defenders are pulled;
- **access:** the offence's routes into those holes (speed, off-ball movement, passes, screens, at the rules' chances). Then efficiency (the fewest actions to make the first phase's gain) breaks ties.

Stretching the defence is inside that one measure, not a second one: a defender with no real responsibility is a defender free to close the plan's gaps, so a placement that leaves one idle scores lower. That is how Shaun's two aims fall out together:
1. execute the plan efficiently;
2. stretch the defence's zone of influence by engaging every defender.

**Checks, not instructions:**
- every defender is pulled to a real responsibility;
- a poor-shooting centre ends up a post or screening threat, not a body in the corner the defence can leave (Shaun's expectation).

If either fails, report why. Don't place him by rule.

## Stage 5: the defence sets up (keep what works)

1. **Its scout goals,** from its own scout (the matchups it must avoid, in order), the mirror of the offence's plan (Neutrality).
2. **The list** (the attackers' threats, including the mismatch priced where it hurts; zone gaps as a race; stagnation).
3. **Within the margin:** like against like, then matching numbers.
4. **Efficiency.**
5. **Variety** (All-Star), among what's still level.

## Stage 6: in play, and back into the scout

- **The offence runs its plan phase by phase.** It leaves the plan when the first preference is denied, or **when an equal or better opportunity appears.** Shaun: "Think about if the defence does something silly and leaves an open pass and driving lane. The layup's value might not be better than the open three, but it is guaranteed rather than relying on a successful screen."
  - **Compare opportunities by value at their real chance of happening,** not by the shot's open value. The planned three counts at the chance its route succeeds: the screen holding, the pass arriving, the defender not recovering. An open lane to a layup counts at the near-certainty of getting there.
  - **The offence takes whichever is worth more now.** A sure layup can beat a better shot that depends on a screen working.
  - The chances come from the rules (the list's value times reach), so this falls out without a new number.
- **The defence plays the list,** as now: sticky assignments, switches only when they pay for their moves, the chase and the takeover.
- **After each possession, the scout updates.** The shot and movement values are exact from the rules and never change. What updates is the prediction of the other side's choices: which coverages they use, which matchups they hunt, how they answer a screen.
  - Change a prediction only on repeated evidence.
  - How much evidence is a number. State it, justify it from the dice (more than chance would explain), and flag it for Shaun.

## Shown to the player (Legibility)

- **The offence's plan,** in plain words at setup: "Plan: an open three for O2 on the left wing. Backups: O5 in the post if X2 switches; O1 driving at X5."
- **The defence's read:** "Matchups: X1 on O1 (same speed), X5 on O5. Avoid X5 on O1 at the arc."
- **The phase score** says which preference the possession is chasing.
