# Step 3h: draft rulebook paragraphs (for the designer to choose from; not adopted)

These are drafts for the three settings tested in step 3h. The rulebook files are unchanged.

## The wedge (`arrow_mode = 'wedge'`)

**Arrows.** Each defender's arrow is a wedge: two arrow lines from the defender's square, 45° apart
(for example north and north-east). There are eight ways to set it, one for each pair of neighbouring
directions. Every rule that uses a defender's arrow line uses both lines:
- A pass that crosses either line can be intercepted by that defender.
- The ball carrier can't move across either line of a defender next to them, unless they have beaten
  that defender with a Dribble this phase.
- A Steal needs the ball carrier on one of the lines.

**Turning.** A Move may set the wedge any way. A Sprint leaves one edge pointing the way the defender
ran; the defender chooses which side the other edge goes. A Quick Step keeps the wedge as it was, and
a locked defender can't turn it. In the reaction to a declared shot, the defender may turn as now.

## Contest position by the wedge (`contest_geometry = 'wedge_mirror'`; needs the wedge)

**Who may contest.** A defender next to the shooter may contest only if the shooter is on one of
their arrow lines, after any reaction. A defender whose lines miss the shooter can't contest at all.

**How well.** Look at where the basket (the rim square, I2) lies:
- **Front:** the basket is in the wedge turned round to point behind the defender. The defender is
  between the shooter and the basket. Full contest.
- **Behind:** the basket is inside the defender's own wedge, in front of them, so they are chasing.
  The contest needs a foul roll (the defender's Foul (contest) rating) and takes −3.
- **Side:** neither. The contest needs a foul roll.

A square on the edge of a wedge counts as inside it. This replaces the −3 for being further from the
rim than the shooter: Behind is now the only −3.

## Contest position by distance to the rim (`contest_geometry = 'rim_distance'`)

**Who may contest.** As above: the shooter must be on one of the defender's arrow lines, after any
reaction.

**How well.** Count each square's distance to the rim square I2 in king moves (a diagonal step counts
as one), the same count the −3 rule uses now:
- **Front:** the defender is closer to the rim than the shooter. Full contest.
- **Side:** the same distance. The contest needs a foul roll.
- **Behind:** further from the rim. The contest needs a foul roll and takes −3.

A shooter on the rim square can never meet a Front contest: no defender is closer to the rim.
