# Coverage map blueprint, addendum: the defence's strength (Shaun, 16 Nov 2026)

## The idea

The defence's position at the start of a phase matters little on its own: the offence moves first, and a fresh defender can recover. **What matters is what each phase did to the defence's zone of influence.** The offence is always trying to get a shot, or to start the next phase in a better position, or both. If it didn't use the last phase, it starts fresh, ideally in a better place.

## The three measures (at the start of every phase)

| Measure | What it is | Read from |
|---|---|---|
| **Strength** | The most the offence can force by the start of the next phase: the best weakness left on the map after the offence uses every action it has this phase (moves, screens, passes, dribbles, Hesitate) and the defence gives its best answers. **Lower is a stronger defence.** | The coverage map, at the end of the offence's best phase against the defence's best reply. |
| **Fragility** | How many separate ways the offence has to get near that strength. One can be covered; two at once usually can't. This is where one defender is stretched across two duties. | The same search: the distinct offensive lines whose result is close to the best. |
| **Broken** | The offence can force a shot worth more than playing on, which the defence can't take away. | The best shot now against the value of playing on from this phase (the game's own phase value). Not a hand-set number. |

## Reading a possession

| Possession | What happened |
|---|---|
| **Good** | Strength fell phase by phase and fragility rose, until the defence broke and the shot was taken. |
| **Weak** | Strength held or rose, and the defence never broke. |
| **Wasted** | A break was there and was not taken. The next phase starts fresh. |

The defence's version is the mirror image: it held, it was worn down, or it broke.

## What the computer does with it

- **The offence** chooses each phase to weaken the defence the most, or shoots when it's broken.
- **The defence** chooses to stay strongest.
- How strength and fragility combine into one reading is fitted to play.

## Setup plans the first phase (Shaun)

> "The setup becomes important. The offence sets up to create a good possession that weakens the defence from the start. It assumes matchups and puts the players in spots that will be able to execute actions to weaken the defence during the very first phase. That means a screener being close enough to move into position assuming the likely location the defender will set up. If the initial setup does not already have a plan to weaken the defence, it is highly likely that the first phase will be weak just to try and get into a better position. The coach should recognise consistently weak first phases on offence as needing more considered setup positions."

- **Offence setup:** judged by how far its first phase can weaken the defence, given the matchups it assumes and where the defence will likely stand.
- **Defence setup:** judged by how strong it stays through the offence's best first phase.
- **Feedback:** consistently weak first phases on offence mean the setup needs more thought. The trainer says so after a weak first phase, and the scout notes the pattern across possessions.

## The screen sequence, in Shaun's words

A design check, not an instruction (check S3):

> "The hesitate action is great for screens. Offball movement creates opportunities first if the defence wants to conserve options for later or commits to covering those positions, then the screen is moved in place and set (note that the helper defender also needs to move into place proactively or hold off), then the offence can take the screen if successful or hesitate to force the defence to commit to a movement. Then beat the screen based on what is left, which could be a driving lane or it could be a clean wing pass or it could be a move into an open shot. What matters is that the offence is using its entire arsenal to reduce the defence zone of influence enough prior to the big payoff (using the screen to gain advantage) and if the defence switches the help defender onto the ballhandler then that itself could become a better position for the offence to start the next phase in. And the pick and roll action that comes after could be part of the next phase with a weaker defence."

## New design checks

- **S1:** a screen or off-ball move that pulls a covering defender off his squares reads as weakening the defence. It counts most when it opens a driving lane or a good shooting spot for another player, and the offence takes it.
- **S2:** on a named possession, the line that weakens the defence every phase scores better by play than the line that keeps it level.
- **S3:** Shaun's screen sequence can be played under the rules. The strength measure falls through it, and the computer finds it or a line as good.
- **S4:** the offence's own setup leads to a first phase that weakens the defence by play, clearly more than the old setup's. The defence's setup holds up better against it.
