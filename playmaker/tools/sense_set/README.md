# The sense-check set (D-162)

A fixed set of positions whose answers are measured by playing them out by the rules with common dice. It is the
main gate for changes to the computer's judgement; the head to head is a backstop.

## What is here

- `positions.json`: each position (state and context), what it is, and its candidate turns. A candidate is a turn
  somebody expected, a board's move, or the choice some setting of the computer made when it was scored.
- `answers.json`: for each candidate, what the offence went on to score in each play-out. Four copies of 16
  play-outs; play-out i of copy k has the same dice for every candidate of a position, whenever it is played. So
  any two candidates are compared play-out for play-out.
- `reference_weights.json`: the map the answers were measured with. Every play-out is continued by one fixed
  engine (the All-Star at the start of step 18h), so the answers don't move when the default does.

## Scoring a setting

    python3 tools/sense_18h.py choices <name> [switch=true ...]    its choices, no play-outs (seconds)
    python3 tools/sense_18h.py score <name> [switch=true ...]      scored against the answers

- A choice the set has no answer for is added to `positions.json` and played out once (two copies, 32 play-outs),
  about 0.05 core-hours each from early in a possession.
- **Matched:** the choice is the played-out best, or its paired interval against the best includes 0.
- **Points lost a position:** the mean over positions of the choice against the best, paired.
- Read the points lost first. With 32 play-outs a paired interval is 4 to 8 points wide either way.

## The gate

A change to the reading must improve the set clearly (fewer points lost, more matched) and break none that passed.
Then a short backstop head to head. Where the computer disagrees with an expected move, the played-out answer
decides.

## Adding positions

`python3 tools/sense_18h.py build` rebuilds the set from its sources and keeps every answer whose candidate is still
there. `python3 tools/sense_18h.py play 0,1` plays whatever lacks an answer on copies 0 and 1; `play 2,3` brings
candidates up to 64 play-outs.
