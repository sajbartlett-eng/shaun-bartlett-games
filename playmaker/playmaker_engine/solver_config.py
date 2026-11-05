"""Every limit, width, depth, weight and verdict threshold the solver uses."""
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class SolverConfig:
    # ---- exact endgame solver ----
    endgame_tokens: int = 2          # N: positions in the final phase with <= N tokens per side go exact
    exact_node_cap: int = 4000       # give up on an exact solve after this many applies (fall back to guided)
    # ---- candidate generator ----
    top_k_raw: int = 8               # K: best raw actions (by evaluation) added to the concept plays
    raw_depth: int = 1               # add raw actions only this many plies from the root
    drive_k: int = 3                 # drive / drive-and-shoot squares per node
    relocate_k: int = 2              # off-ball relocations per node
    closeout_k: int = 4              # closeouts per node (outside the reaction to a shot)
    combo_k: int = 3                 # defence two-action combos built from the top single plays
    contain_k: int = 2               # the carrier's best step-then-shoot squares the defence plays to contain
    # ---- guided search ----
    beam: int = 6                    # plays kept per node below the root (ordered by evaluation)
    root_beam: int = 40              # plays kept at the root
    max_depth: int = 12              # iterative deepening limit, in turns
    # ---- evaluation ----
    eval_turns: int = 2              # the evaluation looks over the offence's next N turns (1 or 2)
    eval_setup_k: int = 4            # offence setup plays (pass / relocate / drive...) tried in turn 1
    eval_reply_k: int = 4            # defence replies tried to each setup
    # small positional terms (kept only if they improve agreement with the exact solver; see report)
    term_open_lane: float = 0.0      # per point of the best open-lane receiver's look above the carrier's
    term_zone: float = 0.0           # bonus if the carrier stands on a shooting zone (not plain wood)
    quiescence: bool = True          # a leaf where the defence is to move gets one more defence turn
    quiescence_beam: int = 12        # defence plays kept in that extra turn (ball-side plays only, no combos)
    kick_weight: float = 0.0         # value of the best teammate look (0 = carrier only); tested in the report
    inbound_kick_weight: float = 1.0 # during an inbound the ball must go in: use the best receiver's look
    # ---- budgets and confidence ----
    budgets_min: tuple = (2.0, 10.0) # time budgets per card, minutes
    seeds: int = 5
    unstable_spread: float = 2.0     # value spread (points) above which a card is unstable
    # ---- verdicts ----
    gift_p30: float = 0.75
    wall_p30: float = 0.15
    wall_look: float = 20.0
    plan_share: float = 0.90         # a plan counts if it reaches this share of the best value
    goal: int = 30


DEFAULT = SolverConfig()


def with_config(**kw):
    return replace(DEFAULT, **kw)
