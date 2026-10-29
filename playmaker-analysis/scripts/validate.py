"""
Task 2: check every rating against the PDF's own ranges, colour bands and
tier rules. Nothing is changed; problems are listed.

Output: output/validation_issues.csv, output/validation_summary.csv
"""
import csv
from collections import Counter, defaultdict

import pandas as pd

import config as C

# Position-specific colour bands the PDF gives for layup defence only.     [PDF]
DEF_LAYUP_POSITION_BANDS = {
    "PG": {"green": (10, 10), "orange": (7, 9), "red": (5, 6)},
    "SG": {"green": (10, 10), "orange": (7, 9), "red": (5, 6)},
    "SF": {"green": (10, 12), "orange": (8, 9), "red": (6, 7)},
    "PF": {"green": (11, 12), "orange": (9, 10), "red": (7, 8)},
    "C":  {"green": (11, 12), "orange": (10, 10), "red": (8, 9)},
}

# The PDF's example card (page 42) for PG-5 Slasher Tier A, read from the image.
EXAMPLE_CARD = {
    "values": dict(height=5, strength=6, speed=10, handles=19, pressure_def=8, pass_=14, intercept=9,
                   screen=15, screen_def=8, foul_stl=6, steal=4, foul_blk=7, block=7,
                   off_layup=19, off_dunk=19, off_post=13, off_floater=14, off_mid=10, off_long2=9,
                   off_three=8, off_ft=14, def_layup=10, def_dunk=13, def_post=6, def_floater=6,
                   def_mid=4, def_long2=3, def_three=3),
    # colour printed behind each stat on the example card
    "colours": dict(height="red", strength="orange", speed="green", handles="green",
                    pressure_def="green", pass_="orange", intercept="green", screen="orange",
                    screen_def="green", foul_stl="orange", steal="green", foul_blk="orange",
                    block="orange", off_layup="green", off_dunk="green", off_post="red",
                    off_floater="orange", off_mid="orange", off_long2="orange", off_three="orange",
                    off_ft="orange"),
}

# Stated relationships between a player's own shot ratings.                [PDF]
WITHIN_CARD_RULES = [
    ("off_layup", "off_dunk", 0, 1, "Layup generally 0-1 higher than dunk"),
    ("off_mid", "off_long2", 0, None, "Long-2 generally lower than mid-range"),
    ("off_long2", "off_three", 0, None, "Long-2 generally higher than 3-point"),
    ("off_mid", "off_floater", 0, None, "Mid-range generally higher than floater"),
    ("off_layup", "off_post", 1, None, "Post move generally lower than layup"),
]

# Inconsistencies inside the PDF text itself (found while reading it).
DOC_ISSUES = [
    ("speed", "Speed section says SF range 6-8 but lists SF tiers 9-10/9-10/8-9; conclusion says 'whole number scale from 4 to 10' while the scale is 6-12."),
    ("speed", "Speed section says speed = movement points (lateral 2, diagonal 3 per square) yet the brief says speed is scouting only. The two cannot both drive QS."),
    ("height", "Height colour bands leave 7.5 and 5.6-5.9 unclassified (green 8-10, orange 6-7, red 5-5.5)."),
    ("foul_stl", "Foul (Steal) bands overlap: green 4-6, orange 6-8, red 8-11 (6 and 8 are in two bands)."),
    ("foul_blk", "Foul (Block) bands overlap at 7 and 9, and the range minimum 4 sits below the green band (5-7)."),
    ("screen_def", "Screen Defence bands overlap at 6 (orange 6-7, red 4-6)."),
    ("steal", "Steal red band is written as both 'Roll <=1' and 'Roll 1'."),
    ("intercept", "Intercept red band is written as both 'Roll 5' (25%) and '<=5' (<30%)."),
    ("def_layup", "Layup defence range is 5-12 but the narrative quotes PF Defender 13 and C Rim Protector 14."),
    ("def_layup", "Layup defence has per-position colour bands (e.g. C orange = 10 only) that differ from the global bands."),
    ("pressure_def", "'Ratings maintain a 1-point difference between tiers' vs 'The 5-point range (10 to 5 for guards...)'; consistent, noted only."),
    ("tiers", "Intercept narrative says Tier B 'above-average', Tier C 'average to below-average', but the brief maps B to average (orange) and C to below average (red)."),
    ("steal_rule", "Example card resolves a steal attempt in two steps (1st <= Foul(Stl), 2nd >= Handles-Steal); the PDF table and brief do not say whether this is one roll or two."),
    ("free_throw", "Rating scale says FT minimum 11 (55%) but C-5 Rim Runner Tier C has FT 10."),
]


def band_colour(bands, value):
    hits = [c for c, (lo, hi) in bands.items()
            if (lo is None or value >= lo) and (hi is None or value <= hi)]
    return "/".join(hits) if hits else "none"


def main():
    cards = pd.read_csv(C.DATA_DIR / "cards.csv")
    issues = []

    def add(card_id, stat, value, check, expected, severity, note=""):
        issues.append(dict(card_id=card_id, stat=stat, value=value, check=check,
                           expected=expected, severity=severity, note=note))

    by_type = {t: g.set_index("card_tier") for t, g in cards.groupby("type_code")}

    for _, r in cards.iterrows():
        for key, spec in C.STATS.items():
            v = r[key]
            # 1. global range
            if v < spec["lo"] or v > spec["hi"]:
                add(r.card_id, key, v, "out_of_range", f"{spec['lo']}-{spec['hi']}", "high")
            # 2. position range
            pr = C.POSITION_RANGES.get(key, {}).get(r.position)
            if pr and (v < pr[0] or v > pr[1]):
                add(r.card_id, key, v, "out_of_position_range", f"{r.position} {pr[0]}-{pr[1]}", "medium")
            # 3. band coverage
            tier = r[key + "_tier"]
            if tier == "gap":
                add(r.card_id, key, v, "no_colour_band", str(spec["bands"]), "low")
            elif "/" in str(tier):
                add(r.card_id, key, v, "ambiguous_colour_band", str(spec["bands"]), "low")
        # layup defence position bands
        pb = DEF_LAYUP_POSITION_BANDS[r.position]
        pos_col = band_colour(pb, r.def_layup)
        if pos_col != r.def_layup_tier:
            add(r.card_id, "def_layup", r.def_layup, "position_band_disagrees",
                f"global={r.def_layup_tier}, {r.position} band={pos_col}", "low")
        # within-card shot relationships
        for a, b, min_gap, max_gap, note in WITHIN_CARD_RULES:
            gap = r[a] - r[b]
            if gap < min_gap or (max_gap is not None and gap > max_gap):
                add(r.card_id, f"{a}-{b}", f"{r[a]}-{r[b]}", "shot_relationship",
                    note, "low" if gap >= min_gap - 1 else "medium")
        if r.off_floater > r.off_layup or r.off_three > r.off_mid:
            add(r.card_id, "shot_order", "", "shot_relationship", "harder shot rated above easier", "medium")

    # 4. tier monotonicity and step rules
    for t, g in by_type.items():
        for key, spec in C.STATS.items():
            a, b, c = g.loc["A", key], g.loc["B", key], g.loc["C", key]
            sign = 1 if spec["better"] == "high" else -1
            if sign * (b - a) > 0:
                add(f"{t}B", key, f"A={a} B={b}", "lower_tier_better", "Tier B should not beat Tier A", "medium")
            if sign * (c - b) > 0:
                add(f"{t}C", key, f"B={b} C={c}", "lower_tier_better", "Tier C should not beat Tier B", "medium")
            if spec["group"] == "athletic" and abs(a - c) > 2.5:
                add(f"{t}", key, f"A={a} C={c}", "large_tier_gap", "athletic gap > 2.5 between A and C", "low")
            rule = C.TIER_STEP_RULES.get(key)
            if rule:
                ab, ac = sign * (a - b), sign * (a - c)
                if not (rule["ab"][0] <= ab <= rule["ab"][1]):
                    add(f"{t}B", key, f"A={a} B={b}", "tier_step_A_to_B", rule["note"], "low")
                if not (rule["ac"][0] <= ac <= rule["ac"][1]):
                    add(f"{t}C", key, f"A={a} C={c}", "tier_step_A_to_C", rule["note"], "low")
                if "floor" in rule and c < rule["floor"]:
                    add(f"{t}C", key, c, "below_floor", f">= {rule['floor']}", "high")

    # 5. PDF narrative values vs cards
    for key, table in C.NARRATIVE_VALUES.items():
        for t, vals in table.items():
            actual = tuple(int(by_type[t].loc[tier, key]) for tier in "ABC")
            if actual != tuple(vals):
                diff = [f"{tier}:{x}->{y}" for tier, x, y in zip("ABC", vals, actual) if x != y]
                add(t, key, "/".join(map(str, actual)), "narrative_mismatch",
                    "PDF text says " + "/".join(map(str, vals)), "medium", ", ".join(diff))

    # 6. example card vs PG-5A
    pg5a = cards.set_index("card_id").loc["PG-5A"]
    for k, v in EXAMPLE_CARD["values"].items():
        key = "pass" if k == "pass_" else k
        if pg5a[key] != v:
            add("PG-5A", key, pg5a[key], "example_card_differs", f"example card shows {v}", "medium")
    for k, col in EXAMPLE_CARD["colours"].items():
        key = "pass" if k == "pass_" else k
        v = EXAMPLE_CARD["values"][k]
        band = band_colour(C.STATS[key]["bands"], v)
        if col not in band.split("/"):
            add("EXAMPLE", key, v, "example_colour_vs_band", f"printed {col}, PDF band says {band}", "medium")

    # 7. document-level inconsistencies
    for stat, note in DOC_ISSUES:
        add("DOC", stat, "", "document_inconsistency", "", "info", note)

    C.OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = pd.DataFrame(issues)
    out.to_csv(C.OUT_DIR / "validation_issues.csv", index=False)
    summ = out.groupby(["check", "severity"]).size().reset_index(name="count")
    summ.to_csv(C.OUT_DIR / "validation_summary.csv", index=False)
    print(summ.to_string(index=False))
    return out


if __name__ == "__main__":
    main()
