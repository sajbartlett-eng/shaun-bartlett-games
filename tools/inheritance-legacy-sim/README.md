# Family Legacy simulator

Plays whole six-estate Family Legacy campaigns with scripted siblings, many times, using the real game code in a headless browser. Nothing is reimplemented: every number comes from the game's own functions, and the siblings act only through the game's inputs and buttons.

```
cd tools/inheritance-legacy-sim
node simulate_legacy.js --runs 100 --profile all        # six profiles, 100 campaigns each, about 4 minutes
node simulate_legacy.js --runs 20 --profile aware,greedy --seed 7
```

Requires Node and Playwright with Chromium (the same setup the playtests use). Results go to `results/`: `RESULTS.md` (summary table and per-profile detail), `summary.json`, and `runs.json` (every campaign, every estate decision).

## Profiles

A sibling policy says how they build, invest, cut, choose, and which role they want when they win Rock, Paper, Scissors.

| Profile | Sibling A | Sibling B |
|---|---|---|
| greedy | random build, spend on the dearest piece, fairest straight cut by Property, take the higher-Property plot | same |
| aware | build beside productive partners, buy pieces that attach to a group, fairest straight cut by Property, take the plot worth more across the Legacy | same |
| mixed | aware | greedy |
| savers | aware builder and chooser, never buys | same |
| closer | aware builder, fairest straight cut by long-term value, takes the smaller plot when it costs 2 or less and the other sibling is behind | same |
| chaos | random build, buys developments when offered, random straight cut, random choice | same |

"Worth more across the Legacy" means Property plus every payment the plot's holdings would make (three per holding, and a Quarry's or Logging Operation's scheduled payments).

## What it measures

- How often the lower-Property plot is the better choice across the Legacy, and by how much.
- Whether the chooser took the long-term better plot, and how often a chooser took the smaller plot at all.
- Income as a share of final wealth.
- How often a sibling arrives at an investment phase with no Capital.
- How many productive groups on the board survive the fence.
- Whether the family's wealth gap closed, held or widened from after Estate 1 to the end.
- Which sibling ends wealthier.

The reading of the first full run is in `docs/inheritance/LEGACY_SIMULATOR_RESULTS.md`.
