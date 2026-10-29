"""
Shared rules engine: shot values, contests and d20 action probabilities.
Every number used here comes from config.py.
"""
import pandas as pd

import config as C


def load_cards():
    return pd.read_csv(C.DATA_DIR / "cards.csv").set_index("card_id", drop=False)


def d20_le(target):
    """P(d20 <= target)."""
    return min(max(target, 0), 20) / 20.0


def d20_ge(target):
    """P(d20 >= target)."""
    return min(max(21 - target, 0), 20) / 20.0


def contest_value(defence_card, shot, state):
    """Contest subtracted from the shot rating for a contest state."""
    if state == "open" or defence_card is None:
        return 0
    full = defence_card["def_" + shot]
    if state == "full":
        return full
    return max(full - C.WEAK_SIDE_REDUCTION, C.WEAK_SIDE_FLOOR)


def shot_value(offence_card, defence_card, shot, state):
    """Shot value = points x (shot rating - contest). Expected points = value / 20."""
    eff = max(offence_card["off_" + shot] - contest_value(defence_card, shot, state),
              C.EFFECTIVE_RATING_FLOOR)
    return C.SHOT_POINTS[shot] * eff


def p_dribble(off, dfn):
    return d20_le(off["handles"] - dfn["pressure_def"])


def p_pass(off, dfn):
    return d20_le(off["pass"] - dfn["intercept"])


def p_screen(off, dfn):
    return d20_le(off["screen"] - dfn["screen_def"])


def p_steal_pdf(off, dfn):
    """PDF rule: steal succeeds on d20 >= Handles - Steal."""
    return d20_ge(off["handles"] - dfn["steal"])


def p_keep_printed(off, dfn):
    """Printed-card rule: carrier keeps the ball on d20 <= Handles - (Steal + 1)."""
    return d20_le(off["handles"] - (dfn["steal"] + C.PRINTED_STEAL_OFFSET))


def steal_attempt_outcomes(off, dfn, resolution=None):
    """Return P(foul), P(steal), P(nothing) for one steal attempt."""
    resolution = resolution or C.STEAL_FOUL_RESOLUTION
    foul_t = dfn["foul_stl"]
    steal_t = off["handles"] - dfn["steal"]
    if resolution == "two_rolls":
        pf = d20_le(foul_t)
        ps = (1 - pf) * d20_ge(steal_t)
    else:  # same roll, foul checked first
        pf = d20_le(foul_t)
        lowest_steal_roll = max(steal_t, foul_t + 1, 1)
        ps = d20_ge(lowest_steal_roll)
    return pf, ps, 1 - pf - ps


def ft_value(off):
    """Two free throws: 1 point x FT rating per throw (same x20 scale as shot value)."""
    return C.FREE_THROWS_PER_FOUL * off["off_ft"]
