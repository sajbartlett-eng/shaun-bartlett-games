"""
Prototype cross-check: match each of the 10 prototype cards on the table to its
nearest PDF card and list every difference.

Matching: the named type and stated tier first ("name match"); then the
numerically nearest PDF card over the printed stats ("nearest by numbers"),
so a mislabelled card would show up.

Output: output/prototype_matches.csv, output/prototype_differences.csv
"""
import numpy as np
import pandas as pd

import config as C
import core

OFF_FIELDS = ["handles", "pass", "screen", "off_layup", "off_dunk", "off_post", "off_floater",
              "off_mid", "off_long2", "off_three", "off_ft"]
DEF_FIELDS = ["pressure_def", "intercept", "screen_def", "steal", "foul_stl", "def_layup", "def_dunk",
              "def_post", "def_floater", "def_mid", "def_long2", "def_three", "foul_blk"]

# Values exactly as given in the brief.
PROTO_OFF = {
    "O1 Combo Point Guard":     dict(tier="B", name_match="PG-4", qs=1, vals=[15, 17, 13, 18, 16, 10, 11, 12, 11, 10, 15]),
    "O2 Two-Way Guard":         dict(tier="B", name_match="SG-2", qs=1, vals=[14, 15, 14, 18, 16, 11, 10, 13, 11, 10, 15]),
    "O3 Point Forward":         dict(tier="B", name_match="SF-4", qs=1, vals=[16, 17, 15, 18, 16, 14, 10, 12, 11, 9, 15]),
    "O4 All-Rounder Forward":   dict(tier="A", name_match="PF-4", qs=1, vals=[15, 15, 18, 19, 18, 16, 9, 13, 11, 9, 15]),
    "O5 Playmaker Center":      dict(tier="C", name_match="C-4", qs=0, vals=[14, 15, 15, 17, 16, 14, 9, 11, 8, 6, 13]),
}
PROTO_DEF = {
    "X1 Attacker/Slasher":      dict(tier=None, name_match="PG-5", qs=2, vals=[7, 7, 7, 3, 8, 6, 5, 3, 4, 4, 3, 3, 10]),
    "X2 Sharp Shooter":         dict(tier=None, name_match="SG-1", qs=1, vals=[6, 6, 6, 2, 8, 7, 6, 3, 3, 3, 3, 3, 10]),
    "X3 Scoring Machine":       dict(tier=None, name_match="SF-1", qs=1, vals=[6, 7, 6, 2, 8, 7, 8, 4, 4, 4, 4, 3, 10]),
    "X4 Pick 'n' Pop Forward":  dict(tier=None, name_match="PF-5", qs=0, vals=[5, 6, 6, 2, 9, 8, 9, 4, 4, 4, 4, 3, 10]),
    "X5 Rim Protector":         dict(tier=None, name_match="C-2", qs=0, vals=[6, 8, 7, 2, 8, 11, 12, 7, 6, 7, 7, 5, 5]),
}


def nearest(cards, fields, vals, restrict=None):
    pool = cards if restrict is None else cards[cards.type_code == restrict]
    d = np.sqrt(((pool[fields].values - np.array(vals)) ** 2).sum(axis=1))
    order = np.argsort(d)
    return pool.index[order[0]], d[order[0]], pool.index[order[1]], d[order[1]]


def main():
    cards = core.load_cards()
    matches, diffs = [], []
    for side, protos, fields in (("offence", PROTO_OFF, OFF_FIELDS), ("defence", PROTO_DEF, DEF_FIELDS)):
        for name, p in protos.items():
            # name match: stated tier if given, otherwise the nearest tier of the named type
            if p["tier"]:
                named = f"{p['name_match']}{p['tier']}"
                nd = float(np.sqrt(((cards.loc[named, fields].values - np.array(p["vals"])) ** 2).sum()))
            else:
                named, nd, _, _ = nearest(cards, fields, p["vals"], restrict=p["name_match"])
            near, dist, second, dist2 = nearest(cards, fields, p["vals"])
            ref = cards.loc[named]
            matches.append(dict(side=side, prototype=name, stated_tier=p["tier"] or "not printed",
                                name_match=named, name_match_distance=round(nd, 2),
                                nearest_by_numbers=near, nearest_distance=round(dist, 2),
                                runner_up=second, runner_up_distance=round(dist2, 2),
                                prototype_qs=p["qs"], pdf_speed=ref.speed, qs_derived_from_speed=ref.qs_derived,
                                n_stats_different=int(sum(v != ref[f] for f, v in zip(fields, p["vals"])))))
            for f, v in zip(fields, p["vals"]):
                if v != ref[f]:
                    pct_effect = (v - ref[f]) * 5
                    diffs.append(dict(prototype=name, pdf_card=named, stat=f, prototype_value=v,
                                      pdf_value=ref[f], diff=v - ref[f],
                                      effect_on_success_pct=(f"{pct_effect:+d} pts on every roll or shot that uses it"
                                                             if f not in ("foul_stl", "foul_blk") else
                                                             f"{pct_effect:+d} pts foul chance")))
            if p["qs"] != ref.qs_derived:
                diffs.append(dict(prototype=name, pdf_card=named, stat="QS (prototype) vs Speed-derived",
                                  prototype_value=p["qs"], pdf_value=ref.qs_derived, diff=p["qs"] - ref.qs_derived,
                                  effect_on_success_pct="not a % stat; PDF has no QS rating"))
    m, d = pd.DataFrame(matches), pd.DataFrame(diffs)
    m.to_csv(C.OUT_DIR / "prototype_matches.csv", index=False)
    d.to_csv(C.OUT_DIR / "prototype_differences.csv", index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20); pd.set_option("display.max_rows", 200)
    print(m.to_string(index=False))
    print(d.to_string(index=False))
    return m, d


if __name__ == "__main__":
    main()
