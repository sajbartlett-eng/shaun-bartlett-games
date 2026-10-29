"""
Playmaker ratings audit: every assumption lives in this file.

Change a value here and re-run `python3 run_all.py` to see its effect.
Real-world sources live in benchmarks.py.
Each assumption is tagged with where it comes from:
  [PDF]       Playmaker_Rating_System_and_Player_Ratings.pdf
  [OVERVIEW]  Playmaker_Overview.docx
  [BRIEF]     the rules summary in the analysis brief
  [ASSUMED]   my modelling choice where the documents are silent
  [AMBIGUITY] the rules allow two readings; both are computed, not resolved
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "output"

# ---------------------------------------------------------------------------
# 1. Source document
# ---------------------------------------------------------------------------
# The PDF is NOT stored in this folder. Point to it with an env var or edit.
PDF_PATH = Path(os.environ.get(
    "PLAYMAKER_PDF", ROOT.parent / "Playmaker_Rating_System_and_Player_Ratings.pdf"))
CARD_PAGES = range(43, 58)            # [PDF] pages 43-57 hold the 75 cards
EXAMPLE_CARD_PAGE = 42                # [PDF] PG-5 Slasher example card image
# Card pages are 4 text columns; x bounds in PDF points.
COLUMN_BOUNDS = [(0, 190), (190, 310), (310, 432), (432, 595.32)]

POSITIONS = ["PG", "SG", "SF", "PF", "C"]
TIER_TO_COLOUR = {"A": "green", "B": "orange", "C": "red"}   # [BRIEF] green above avg, orange avg, red below

# ---------------------------------------------------------------------------
# 2. Stat definitions: range and colour bands exactly as the PDF states them
# ---------------------------------------------------------------------------
# lo/hi: allowed range. bands: inclusive (lo, hi) per colour. better: "high"/"low".
# None in a band means "no bound stated". Overlapping bands are kept as written
# so the validator can report them.
STATS = {
    # Athletic profile (scouting only, no mechanical effect)                   [PDF]
    "height":     dict(label="Height", group="athletic", lo=5.0, hi=9.5, better="high",
                       bands={"green": (8, 10), "orange": (6, 7), "red": (5, 5.5)}),
    "strength":   dict(label="Strength", group="athletic", lo=5.5, hi=10, better="high",
                       bands={"green": (8, 10), "orange": (6.5, 7.5), "red": (5.5, 6)}),
    "speed":      dict(label="Speed", group="athletic", lo=6, hi=12, better="high",
                       bands={"green": (11, 12), "orange": (9, 10), "red": (6, 8)}),
    "vertical":   dict(label="Vertical", group="athletic", lo=5.5, hi=10, better="high",
                       bands={"green": (8, 10), "orange": (6.5, 7.5), "red": (5.5, 6)}),
    # Offence skills                                                          [PDF]
    "handles":    dict(label="Handles", group="off_skill", lo=1, hi=20, better="high",
                       bands={"green": (17, 20), "orange": (14, 16), "red": (None, 13)}),
    "pass":       dict(label="Pass", group="off_skill", lo=11, hi=20, better="high",
                       bands={"green": (17, 20), "orange": (14, 16), "red": (11, 13)}),
    "screen":     dict(label="Screen", group="off_skill", lo=11, hi=20, better="high",
                       bands={"green": (17, 20), "orange": (14, 16), "red": (11, 13)}),
    # Defence skills                                                          [PDF]
    "pressure_def": dict(label="Pressure Defence", group="def_skill", lo=3, hi=10, better="high",
                       bands={"green": (8, 10), "orange": (6, 7), "red": (None, 5)}),
    "intercept":  dict(label="Intercept", group="def_skill", lo=1, hi=10, better="high",
                       bands={"green": (8, 10), "orange": (6, 7), "red": (None, 5)}),
    "screen_def": dict(label="Screen Defence", group="def_skill", lo=4, hi=10, better="high",
                       bands={"green": (8, 10), "orange": (6, 7), "red": (4, 6)}),
    "steal":      dict(label="Steal", group="def_skill", lo=1, hi=5, better="high",
                       bands={"green": (4, 5), "orange": (2, 3), "red": (None, 1)}),
    "foul_stl":   dict(label="Foul (Steal)", group="def_skill", lo=4, hi=11, better="low",
                       bands={"green": (4, 6), "orange": (6, 8), "red": (8, 11)}),
    "block":      dict(label="Block", group="def_skill", lo=4, hi=10, better="high",
                       bands={"green": (8, 10), "orange": (6, 7), "red": (4, 5)}),
    "foul_blk":   dict(label="Foul (Block)", group="def_skill", lo=4, hi=12, better="low",
                       bands={"green": (5, 7), "orange": (7, 9), "red": (9, 12)}),
    # Offensive shooting (out of 20 = make probability x 20)                  [PDF]
    "off_layup":  dict(label="Layup", group="off_shot", lo=17, hi=19, better="high",
                       bands={"green": (19, 19), "orange": (18, 18), "red": (17, 17)}),
    "off_dunk":   dict(label="Dunk", group="off_shot", lo=14, hi=19, better="high",
                       bands={"green": (18, 19), "orange": (16, 17), "red": (14, 15)}),
    "off_post":   dict(label="Post Move", group="off_shot", lo=9, hi=18, better="high",
                       bands={"green": (15, 18), "orange": (12, 14), "red": (9, 11)}),
    "off_floater": dict(label="Floater", group="off_shot", lo=8, hi=15, better="high",
                       bands={"green": (13, 15), "orange": (10, 12), "red": (8, 9)}),
    "off_mid":    dict(label="Mid-range", group="off_shot", lo=9, hi=16, better="high",
                       bands={"green": (14, 16), "orange": (11, 13), "red": (9, 10)}),
    "off_long2":  dict(label="Long-2pts", group="off_shot", lo=7, hi=14, better="high",
                       bands={"green": (12, 14), "orange": (9, 11), "red": (7, 8)}),
    "off_three":  dict(label="3-Pointer", group="off_shot", lo=6, hi=13, better="high",
                       bands={"green": (11, 13), "orange": (8, 10), "red": (6, 7)}),
    "off_ft":     dict(label="Free Throw", group="off_shot", lo=11, hi=19, better="high",
                       bands={"green": (17, 19), "orange": (14, 16), "red": (11, 13)}),
    # Defensive shot impact (contest)                                         [PDF]
    "def_layup":  dict(label="Layup", group="def_shot", lo=5, hi=12, better="high",
                       bands={"green": (10, 12), "orange": (7, 9), "red": (5, 6)}),
    "def_dunk":   dict(label="Dunk", group="def_shot", lo=4, hi=14, better="high",
                       bands={"green": (11, 14), "orange": (7, 10), "red": (4, 6)}),
    "def_post":   dict(label="Post Move", group="def_shot", lo=2, hi=8, better="high",
                       bands={"green": (6, 8), "orange": (4, 5), "red": (2, 3)}),
    "def_floater": dict(label="Floater", group="def_shot", lo=3, hi=7, better="high",
                       bands={"green": (6, 7), "orange": (4, 5), "red": (3, 3)}),
    "def_mid":    dict(label="Mid-range", group="def_shot", lo=1, hi=7, better="high",
                       bands={"green": (6, 7), "orange": (4, 5), "red": (None, 3)}),
    "def_long2":  dict(label="Long-2pts", group="def_shot", lo=1, hi=6, better="high",
                       bands={"green": (5, 6), "orange": (3, 4), "red": (None, 2)}),
    "def_three":  dict(label="3-Pointer", group="def_shot", lo=1, hi=6, better="high",
                       bands={"green": (5, 6), "orange": (3, 4), "red": (None, 2)}),
}

# Position-specific ranges the PDF states on top of the global range.     [PDF]
POSITION_RANGES = {
    "height":       {"PG": (5.0, 6.5), "SG": (5.5, 6.5), "SF": (6.5, 7.5), "PF": (7.0, 8.5), "C": (7.5, 9.5)},
    "strength":     {"PG": (5.5, 7.0), "SG": (5.5, 7.0), "SF": (6.0, 8.0), "PF": (7.0, 9.0), "C": (7.0, 9.5)},
    "pressure_def": {"PG": (5, 10), "SG": (5, 9), "SF": (5, 9), "PF": (4, 8), "C": (3, 7)},
    "steal":        {"PG": (2, 5), "SG": (1, 5), "SF": (2, 5), "PF": (1, 3), "C": (2, 4)},
    "foul_stl":     {"PG": (4, 9), "SG": (4, 9), "SF": (5, 9), "PF": (5, 10), "C": (7, 11)},
    "screen":       {"PG": (11, 16), "SG": (11, 16), "SF": (12, 17), "PF": (14, 19), "C": (14, 19)},
    "block":        {"PG": (4, 7), "SG": (4, 8), "SF": (5, 10), "PF": (5, 10), "C": (5, 10)},
    "foul_blk":     {"PG": (7, 12), "SG": (7, 12), "SF": (6, 11), "PF": (5, 11), "C": (4, 11)},
    "off_post":     {"PG": (9, 13), "SG": (10, 14), "SF": (11, 16), "PF": (13, 17), "C": (14, 18)},
    "def_layup":    {"PG": (5, 10), "SG": (5, 10), "SF": (6, 12), "PF": (7, 12), "C": (8, 12)},
    "def_dunk":     {"PG": (4, 10), "SG": (4, 10), "SF": (6, 12), "PF": (8, 13), "C": (9, 14)},
    "def_post":     {"PG": (2, 5), "SG": (2, 5), "SF": (3, 7), "PF": (4, 7), "C": (5, 8)},
}

# Tier-step rules the PDF states (Tier A -> B -> C).                         [PDF]
# (min_drop, max_drop) from A to B and from A to C. floor = never below.
TIER_STEP_RULES = {
    "off_layup":   dict(ab=(0, 1), ac=(1, 2), floor=17, note="B 0-1 below A; C 1-2 below A, never below 17"),
    "off_dunk":    dict(ab=(1, 1), ac=(2, 2), floor=14, note="B generally 1 below A; C usually 2 below A, never below 14"),
    "off_post":    dict(ab=(1, 2), ac=(2, 4), note="typically 1-2 points between tiers"),
    "off_mid":     dict(ab=(1, 2), ac=(2, 4), note="usually 1-2 point differences between tiers"),
    "off_long2":   dict(ab=(1, 2), ac=(2, 4), note="usually 1-2 point differences between tiers"),
    "off_three":   dict(ab=(1, 2), ac=(2, 4), note="usually 1-2 point differences between tiers"),
    "pass":        dict(ab=(1, 1), ac=(2, 2), note="consistent 1-point drops between tiers"),
    "pressure_def": dict(ab=(1, 1), ac=(2, 2), note="maintain a 1-point difference between tiers"),
    "intercept":   dict(ab=(1, 1), ac=(2, 2), note="difference between tiers is typically 1 point"),
    "screen_def":  dict(ab=(1, 1), ac=(2, 2), note="most types see a 1-point decrease per tier"),
    "def_layup":   dict(ab=(2, 2), ac=(4, 4), note="typically 2-point difference between tiers"),
    "def_dunk":    dict(ab=(2, 2), ac=(4, 4), note="typically 2-point difference between tiers"),
    "def_post":    dict(ab=(1, 1), ac=(2, 2), note="typically 1-point difference between tiers"),
}

# Specific per-type values the PDF's narrative quotes (A/B/C).               [PDF]
# The validator compares these against the actual cards.
NARRATIVE_VALUES = {
    "pressure_def": {"PG-1": (8, 7, 6), "PG-2": (7, 6, 5), "PG-3": (10, 9, 8), "PG-4": (8, 7, 6), "PG-5": (8, 7, 6),
                     "SG-1": (7, 6, 5), "SG-2": (9, 8, 7), "SG-3": (9, 8, 7), "SG-4": (7, 6, 5), "SG-5": (7, 6, 5),
                     "SF-1": (7, 6, 5), "SF-2": (9, 8, 7), "SF-3": (7, 6, 5), "SF-4": (7, 6, 5), "SF-5": (9, 8, 7),
                     "PF-1": (6, 5, 4), "PF-2": (6, 5, 4), "PF-3": (8, 7, 6), "PF-4": (7, 6, 5), "PF-5": (6, 5, 4),
                     "C-1": (5, 4, 3), "C-2": (7, 6, 5), "C-3": (6, 5, 4), "C-4": (5, 4, 3), "C-5": (7, 6, 5)},
    "pass": {"PG-1": (20, 19, 18), "PG-2": (16, 15, 14), "PG-3": (15, 14, 13), "PG-4": (18, 17, 16), "PG-5": (15, 14, 13),
             "SG-1": (14, 13, 12), "SG-2": (15, 14, 13), "SG-3": (13, 12, 11), "SG-4": (18, 17, 16), "SG-5": (13, 12, 11),
             "SF-1": (15, 14, 13), "SF-2": (15, 14, 13), "SF-3": (14, 13, 12), "SF-4": (18, 17, 16), "SF-5": (13, 12, 11),
             "PF-1": (13, 12, 11), "PF-2": (14, 13, 12), "PF-3": (12, 11, 11), "PF-4": (15, 14, 13), "PF-5": (14, 13, 12),
             "C-1": (13, 12, 11), "C-2": (11, 11, 11), "C-3": (14, 13, 12), "C-4": (17, 16, 15), "C-5": (11, 11, 11)},
    "steal": {"PG-3": (5, 5, 4), "PG-1": (3, 3, 3), "PG-4": (3, 3, 3), "SG-3": (5, 4, 3), "SG-1": (2, 2, 1),
              "SF-5": (5, 4, 4), "SF-3": (3, 2, 2), "SF-4": (3, 2, 2), "PF-3": (3, 3, 2), "C-3": (4, 3, 2),
              "C-1": (2, 2, 2), "C-2": (2, 2, 2)},
    "foul_stl": {"PG-3": (4, 5, 6), "PG-5": (6, 8, 9), "SG-2": (4, 5, 6), "SG-3": (4, 5, 6), "SG-5": (8, 9, 9),
                 "SF-5": (6, 6, 7), "SF-4": (7, 8, 9), "PF-3": (5, 5, 7), "PF-1": (8, 8, 10), "C-2": (7, 8, 9),
                 "C-4": (7, 8, 9), "C-1": (9, 10, 11)},
    "intercept": {"PG-3": (9, 8, 7), "SF-5": (9, 8, 7), "PF-3": (9, 8, 7), "SG-2": (9, 8, 7), "SF-2": (9, 8, 7),
                  "PG-5": (8, 7, 7), "C-2": (9, 8, 7), "C-5": (8, 7, 6), "PF-1": (6, 6, 5), "C-1": (6, 6, 5),
                  "SF-3": (6, 6, 5), "PF-2": (6, 6, 5), "C-3": (6, 6, 5)},
    "screen_def": {"PG-3": (10, 9, 8), "SG-5": (6, 5, 4), "SG-2": (9, 8, 7), "SG-3": (9, 8, 7), "SF-5": (10, 9, 8),
                   "SF-4": (8, 7, 6), "PF-4": (8, 7, 6), "SF-3": (7, 6, 5), "PF-2": (7, 6, 5), "C-2": (8, 7, 6),
                   "C-1": (5, 4, 4), "C-3": (7, 6, 5), "C-4": (7, 6, 5)},
    "block": {"PG-3": (7, 6, 5), "SG-2": (8, 7, 6), "SG-1": (6, 5, 4), "SF-5": (10, 9, 8), "SF-3": (7, 6, 5),
              "PF-3": (10, 9, 8), "PF-2": (7, 6, 5), "C-2": (10, 9, 8), "C-1": (9, 8, 7)},
    "foul_blk": {"PG-3": (7, 8, 9), "PG-2": (9, 10, 11), "PG-5": (9, 10, 11), "SG-2": (7, 8, 9), "SG-5": (11, 12, 12),
                 "SF-5": (6, 7, 8), "SF-1": (9, 10, 11), "PF-3": (5, 6, 7), "PF-1": (8, 9, 10), "C-2": (4, 5, 6),
                 "C-1": (6, 7, 8)},
    "off_post": {"PG-2": (13, 12, 11), "PG-1": (11, 10, 9), "SG-5": (14, 13, 12), "SG-3": (12, 11, 10),
                 "SF-1": (16, 15, 14), "SF-3": (14, 13, 12), "PF-1": (17, 16, 15), "PF-2": (15, 14, 13),
                 "C-1": (18, 17, 16), "C-5": (16, 15, 14)},
    "def_layup": {"PG-3": (10, 8, 6), "PG-2": (7, 6, 5), "SG-2": (9, 8, 7), "SG-5": (7, 6, 5), "SF-5": (12, 10, 8),
                  "SF-1": (8, 7, 6), "PF-3": (13, 11, 9), "PF-2": (9, 8, 7), "C-2": (14, 12, 10), "C-3": (10, 9, 8)},
    "def_dunk": {"PG-3": (10, 8, 6), "PG-2": (7, 5, 4), "SG-2": (10, 8, 6), "SG-5": (7, 5, 4), "SF-5": (12, 10, 8),
                 "SF-1": (10, 8, 6), "PF-3": (13, 11, 9), "PF-2": (11, 9, 7), "C-2": (14, 12, 10), "C-3": (12, 10, 8)},
    "def_post": {"PG-3": (5, 4, 3), "PG-2": (4, 3, 2), "SG-2": (5, 4, 3), "SG-5": (4, 3, 2), "SF-5": (7, 6, 5),
                 "SF-1": (5, 4, 3), "PF-3": (7, 6, 5), "PF-2": (5, 4, 3), "C-2": (8, 7, 6), "C-3": (6, 5, 4)},
}

# ---------------------------------------------------------------------------
# 3. Resolution rules                                                       [BRIEF]
# ---------------------------------------------------------------------------
SHOTS = ["layup", "dunk", "post", "floater", "mid", "long2", "three"]
SHOT_POINTS = {"layup": 2, "dunk": 2, "post": 2, "floater": 2, "mid": 2, "long2": 2, "three": 3}
SHOT_ZONE = {"layup": "rim", "dunk": "rim", "post": "post", "floater": "paint",
             "mid": "mid", "long2": "long2", "three": "three"}
WEAK_SIDE_REDUCTION = 3            # [BRIEF] the 5 non-basket-side squares use contest - 3
WEAK_SIDE_FLOOR = 0                # [ASSUMED] weak-side contest never goes below 0
EFFECTIVE_RATING_FLOOR = 0         # [ASSUMED] shot rating - contest never below 0 (a shot can't be worth < 0)
CONTEST_STATES = ["open", "weak", "full"]
PENALTY_FAILED_PASS = 5            # [BRIEF] failed pass: -5 to offence final score
PENALTY_STEAL = 5                  # [BRIEF] successful steal: -5
FREE_THROWS_PER_FOUL = 2           # [BRIEF]

# Steal rule.                                                               [PDF] p41
# PDF: steal succeeds on d20 >= (Handles - Steal).
# Printed cards: carrier keeps ball on d20 <= (Handles - (Steal + 1)).
PRINTED_STEAL_OFFSET = 1

# How the foul check combines with the steal check.                         [AMBIGUITY]
#  "same_roll": one d20. Roll <= Foul(Steal) is a foul (checked first, per the
#               example card's "1st"). Otherwise roll >= Handles-Steal is a steal.
#  "two_rolls": roll 1 for the foul; only if no foul, roll 2 for the steal.
STEAL_FOUL_RESOLUTION = "same_roll"

# Weak-side contest below zero: a defender with Contest 2 on the weak side
# would give 2 - 3 = -1. The brief does not say whether that floors at 0.  [AMBIGUITY]
# (WEAK_SIDE_FLOOR above; set to None to let it go negative.)

# Quick Step is printed on prototype cards but absent from the PDF. Speed is the
# closest PDF stat; this mapping is used only to compare prototype QS values.
QS_FROM_SPEED = {12: 2, 11: 2, 10: 1, 9: 1, 8: 0, 7: 0, 6: 0}

# Realistic contesters by zone, for "typical defender" summaries in the audit.
# Rim shots are usually contested by bigs; jump shots by the matched defender.
CONTESTERS = {
    "layup": ["C", "PF"], "dunk": ["C", "PF"], "post": ["C", "PF"],
    "floater": ["C", "PF", "SF"], "mid": POSITIONS, "long2": POSITIONS, "three": POSITIONS,
}
TIER_LABEL = {"A": "above average (green)", "B": "average (orange)", "C": "below average (red)"}
