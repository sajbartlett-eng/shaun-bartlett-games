# Step 18d: the compute estimate, and predictions written before each run

## The estimate (written before any run)

**About 8 core-hours** on this machine (4 cores). The app's rules only.

| Work | Core-hours | Why |
|---|---|---|
| Self-play with every action kept: today's rules and sizes 1, 2 and 3, 200 possessions each | 3.0 | about 0.55 a setting at step 18b's speed; possessions may run longer under the rule |
| Boards 1 and 3 under each size (defence boards: about 8 core-minutes a pass) | 1.2 | 2 boards, 4 settings |
| Boards 6, 8 and 9, Shaun's closeout line, the archetype check | 0.3 | offence boards take seconds; the archetypes come from the self-play logs |
| The agreement checks at each size, speed at each size | 0.8 | |
| A refit of the calibrated map for one size and a second self-play run, only if its error rises clearly | 2.5 | |

## 1. Self-play under today's rules and each size (200 possessions each)

- Cost: 0.6 to 0.8 a setting.
- **Shots:** under today's rules about a fifth to a third of shots follow a Quick Step or Sprint. Under the rule that
  share falls as the size grows, to under a tenth at size 3: the computer learns to Move last.
- **Closeouts:** under today's rules most contested shots are contested by a defender who moved in the reaction. I
  expect the share of rushed Contests (after a Quick Step or Sprint) to be small already, because a defender with
  his Move unused closes out with it. So the rule changes the Contest side less than the shot side.
- **Points a possession:** down by 0 to 1.5 from today's 29 to 30 at sizes 1 and 2; size 3 no lower than 27.
- **Shot timing:** little change: 65% to 78% of shots in phases 1 and 2.
- **The calibrated map's error:** no clear rise at size 1; a small rise at size 3, not enough to need a refit.
