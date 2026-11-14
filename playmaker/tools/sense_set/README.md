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

- `sources/`: what the set is built from: the play harvested for it (`harvest.json`), the two worst misses of step
  18f's reply list (`reply_miss.json`), and step 18e's two Steal positions.

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

## The set keeps its own copy of the cards (found in step 18l)

Each position in `positions.json` carries the two teams' cards as they were when the position was made. The 19
scored positions were made before the card update (D-184, D-186), so every answer file here was played on the cards
before it.

- `answers_18l_cards_before_d184.json`: the set replayed under step 18l's rules (the six rules of the app,
  `rules.off_balance` on) **on those older cards.** It is not the re-record on the new cards that step 18l was asked
  for: the mistake was found too late in that step's compute to play it again.
- **To re-record on the new cards:** replace each card in each position's `ctx` by the card of the same key as it is
  now (a card is found by its old ratings: `docs/runs/step18l/work/set_on_new_cards.py` does it for the searches),
  then play the set. About 2.2 core-hours.
- The self-play pool (`docs/runs/step18/pools.json`, not kept in the repository) keeps its own copy of the cards too.
  Rebuild it after any card change: `python3 tools/step_18.py pools`. `tools/step_18l.py` now refuses a pool whose
  cards are not today's.
