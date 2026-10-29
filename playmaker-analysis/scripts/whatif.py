"""
Candidate rating changes, re-scored on the same percentage checks.
No simulation: each candidate edits ratings (or one rule constant) and the
exact d20 percentages are recomputed for all 5,625 pairings.

Output: output/whatif_candidates.csv
"""
import itertools

import numpy as np
import pandas as pd

import config as C
import core

CANDIDATES = {
    "current ratings": dict(),
    "Dunk contest capped at Layup contest - 1": dict(dunk_cap=1),
    "Mid-range -2 (scale 9-16 -> 7-14)": dict(add={"off_mid": -2}),
    "Mid-range -3 (scale 9-16 -> 6-13)": dict(add={"off_mid": -3}),
    "Layup contest -3 (scale 5-12 -> 2-9)": dict(add={"def_layup": -3}),
    "Layup contest -3 + dunk cap": dict(add={"def_layup": -3}, dunk_cap=1),
    "Weak-side reduction 3 -> 2": dict(weak=2),
    "Attacker +6 on Pass and Steal rolls": dict(pass_bonus=6, steal_bonus=6),
    "Recommended set (dunk cap, mid -2, layup contest -3, weak-side 2, +6)":
        dict(add={"off_mid": -2, "def_layup": -3}, dunk_cap=1, weak=2, pass_bonus=6, steal_bonus=6),
}


def apply(cards, spec):
    c = cards.copy()
    touched = 0
    for k, v in spec.get("add", {}).items():
        new = (c[k] + v).clip(lower=0)
        touched += int((new != c[k]).sum())
        c[k] = new
    if "dunk_cap" in spec:
        new = np.minimum(c.def_dunk, (c.def_layup - spec["dunk_cap"]).clip(lower=0))
        touched += int((new != c.def_dunk).sum())
        c["def_dunk"] = new
    return c, touched


def pct(off, dfn, shot, state, weak):
    contest = 0
    if state == "full":
        contest = dfn["def_" + shot]
    elif state == "weak":
        contest = np.maximum(dfn["def_" + shot] - weak, 0)
    return np.clip(off["off_" + shot] - contest, 0, 20) * 5


def score(cards, spec):
    weak = spec.get("weak", C.WEAK_SIDE_REDUCTION)
    pairs = pd.DataFrame(list(itertools.product(cards.index, cards.index)), columns=["o", "d"])
    O = cards.loc[pairs.o].reset_index(drop=True)
    D = cards.loc[pairs.d].reset_index(drop=True)
    bigs = D.position.isin(["C", "PF"]).values
    tierA_bigs = bigs & (D.card_tier == "A").values
    out = {}
    lay = {s: pct(O, D, "layup", s, weak) for s in C.CONTEST_STATES}
    dnk = {s: pct(O, D, "dunk", s, weak) for s in C.CONTEST_STATES}
    out["dunk beats layup (% of pairing-states)"] = np.mean(
        np.concatenate([(dnk[s] > lay[s]).values for s in C.CONTEST_STATES])) * 100
    out["layup full vs tier A bigs (real elite 46-54%)"] = lay["full"][tierA_bigs].mean()
    c2a = (D.card_id == "C-2A").values
    out["layup full vs C-2A, layup-18 finisher"] = lay["full"][c2a & (O.off_layup == 18).values].mean()
    out["dunk full vs tier A bigs"] = dnk["full"][tierA_bigs].mean()
    out["share of dunk pairings vs C-2A at <=10%"] = (dnk["full"][c2a] <= 10).mean() * 100
    Bsh = (O.card_tier == "B").values
    mid_open = pct(O, D, "mid", "open", weak)[Bsh].mean()
    three_open = pct(O, D, "three", "open", weak)[Bsh].mean()
    out["open mid % (avg shooter; real ~44-49)"] = mid_open
    out["open mid pts / open three pts (real ~0.80)"] = (mid_open * 2) / (three_open * 3)
    out["mid full % (avg shooter)"] = pct(O, D, "mid", "full", weak)[Bsh].mean()
    t_open = pct(O, D, "three", "open", weak).mean()
    out["three: weak-side drop, pts (real tight ~8)"] = t_open - pct(O, D, "three", "weak", weak).mean()
    out["three: full drop, pts"] = t_open - pct(O, D, "three", "full", weak).mean()
    out["layup: weak-side drop vs bigs, pts"] = (lay["open"] - lay["weak"])[bigs].mean()
    # open three vs fully contested rim by C/PF, red three-point shooters
    red = (O.off_three <= 7).values
    rim_full = np.maximum(lay["full"], dnk["full"]) / 100 * 2
    open3 = pct(O, D, "three", "open", weak) / 100 * 3
    out["red 3pt shooters: open three beats contested rim (%)"] = (open3 > rim_full)[red & bigs].mean() * 100
    # disruption
    pb, sb = spec.get("pass_bonus", 0), spec.get("steal_bonus", 0)
    out["pass success vs Intercept, mean %"] = np.clip(O["pass"] - D.intercept + pb, 0, 20).mean() * 5
    steal_t = O.handles - D.steal + sb
    out["steal success per attempt, mean % (PDF bands 10-25)"] = np.clip(21 - steal_t, 0, 20).mean() * 5
    out["foul on steal attempt, mean %"] = D.foul_stl.mean() * 5
    return out


def main():
    cards = core.load_cards()
    rows = []
    for name, spec in CANDIDATES.items():
        c, touched = apply(cards, spec)
        r = dict(candidate=name, ratings_changed=touched)
        r.update(score(c, spec))
        rows.append(r)
    df = pd.DataFrame(rows).set_index("candidate")
    df.round(2).to_csv(C.OUT_DIR / "whatif_candidates.csv")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(df.round(2).T.to_string())
    return df


if __name__ == "__main__":
    main()
