"""
Tasks 5-7: compare the game's percentages with real benchmarks, check the
relationships between them, and flag dominant pairings.

Reads output/outcome_table_*.csv (from matchups.py) and data/cards.csv.
Outputs:
  output/benchmark_comparison.csv      game % beside real %, by tier and by position
  output/pdf_stated_vs_formula.csv     the PDF's own stated odds vs what its dice rule produces
  output/rel_zone_order.csv            expected points per shot by zone, game vs real
  output/rel_contest_effect.csv        points of make % a contest removes, game vs real
  output/rel_tier_separation.csv       gap between green and red cards, per stat
  output/rel_position.csv              position averages and expected orderings
  output/dominant_pairings.csv         actions/shots near 0% or near-certain
  output/ambiguity_effects.csv         how much each open rules question moves the numbers
  output/sources.csv                   every source with confidence
"""
import itertools

import numpy as np
import pandas as pd

import benchmarks as B
import config as C
import core

TIERS = ["A", "B", "C"]


def summarise(series):
    s = pd.Series(series)
    return dict(game_mean=s.mean(), game_p10=s.quantile(0.1), game_p90=s.quantile(0.9),
                game_min=s.min(), game_max=s.max(), n_pairings=len(s))


def verdict(mean, lo, hi, tol=3.0):
    """Direction and size of the gap between a game mean (%) and a real range (fractions)."""
    if lo is None:
        return "no benchmark", np.nan
    lo, hi = lo * 100, hi * 100
    if mean > hi + tol:
        return "game higher", mean - hi
    if mean < lo - tol:
        return "game lower", mean - lo
    return "aligned (within 3 pts)", 0.0


def shot_comparison(cards, shots):
    rows = []
    for shot in C.SHOTS:
        contest_pos = C.CONTESTERS[shot]
        typical = shots[shots.def_pos.isin(contest_pos)]
        bench = B.SHOT_BENCHMARKS[shot]
        for state in C.CONTEST_STATES:
            col = f"{shot}_{state}_pct"
            lo, hi, src, conf, note = bench.get(state, (None, None, [], "none", "no benchmark for this contest level"))
            groups = [("all shooters", typical)]
            groups += [(f"shooter tier {t}", typical[typical.off_tier == t]) for t in TIERS]
            groups += [(f"shooter {p}", typical[typical.off_pos == p]) for p in C.POSITIONS]
            if state != "open":
                groups += [(f"defender tier {t}", typical[typical.def_tier == t]) for t in TIERS]
            for label, g in groups:
                s = summarise(g[col])
                d, gap = verdict(s["game_mean"], lo, hi)
                rows.append(dict(metric="shot make %", item=shot, state=state, group=label,
                                 contesters="+".join(contest_pos), **s,
                                 real_low=None if lo is None else lo * 100, real_high=None if hi is None else hi * 100,
                                 direction=d, gap_pts=gap, confidence=conf, sources=" ".join(src), note=note))
        # all-attempt benchmark: real average should sit between the game's open and full values
        if "all" in bench:
            lo, hi, src, conf, note = bench["all"]
            for t in TIERS:
                g = typical[typical.off_tier == t]
                o, w, f = (g[f"{shot}_{st}_pct"].mean() for st in C.CONTEST_STATES)
                if lo is None:
                    d = "no benchmark"
                elif f > hi * 100 + 3:
                    d = "game higher (real all-attempt rate is below the game's FULL contest)"
                elif o < lo * 100 - 3:
                    d = "game lower (real all-attempt rate is above the game's OPEN look)"
                else:
                    d = "real all-attempt rate falls inside the game's open-to-full range"
                rows.append(dict(metric="shot make %", item=shot, state="all attempts (real)",
                                 group=f"shooter tier {t}", contesters="+".join(contest_pos),
                                 game_mean=(o + w + f) / 3, game_min=f, game_max=o,
                                 real_low=None if lo is None else lo * 100, real_high=None if hi is None else hi * 100,
                                 direction=d, confidence=conf, sources=" ".join(src),
                                 note=f"game open {o:.0f}% / weak {w:.0f}% / full {f:.0f}%. {note}"))
    # free throws
    lo, hi, src, conf, note = B.SHOT_BENCHMARKS["ft"]["all"]
    for label, g in [("all shooters", cards)] + [(f"shooter tier {t}", cards[cards.card_tier == t]) for t in TIERS] \
            + [(f"shooter {p}", cards[cards.position == p]) for p in C.POSITIONS]:
        s = summarise(g.off_ft * 5)
        d, gap = verdict(s["game_mean"], lo, hi)
        rows.append(dict(metric="free throw %", item="ft", state="uncontested", group=label, **s,
                         real_low=lo * 100, real_high=hi * 100, direction=d, gap_pts=gap,
                         confidence=conf, sources=" ".join(src), note=note))
    return rows


def action_comparison(acts):
    rows = []
    spec = [("dribble", "dribble_pct"), ("pass", "pass_pct"), ("screen", "screen_pct"),
            ("steal", "steal_pct_pdf_rule"), ("foul_stl", "foul_on_steal_attempt_pct")]
    for name, col in spec:
        b = B.ACTION_BENCHMARKS[name]
        lo, hi = b["usable_range"] if b["usable_range"] else (None, None)
        groups = [("all pairings", acts)]
        groups += [(f"offence tier {t}", acts[acts.off_tier == t]) for t in TIERS]
        groups += [(f"defence tier {t}", acts[acts.def_tier == t]) for t in TIERS]
        groups += [(f"offence {t1} vs defence {t2}", acts[(acts.off_tier == t1) & (acts.def_tier == t2)])
                   for t1, t2 in itertools.product(TIERS, TIERS)]
        groups += [(f"offence {p}", acts[acts.off_pos == p]) for p in C.POSITIONS]
        groups += [(f"defence {p}", acts[acts.def_pos == p]) for p in C.POSITIONS]
        groups += [(f"same position ({p} v {p})", acts[(acts.off_pos == p) & (acts.def_pos == p)]) for p in C.POSITIONS]
        for label, g in groups:
            s = summarise(g[col])
            d, gap = verdict(s["game_mean"], lo, hi) if lo is not None else ("see note", np.nan)
            rows.append(dict(metric="action success %", item=name, state="per attempt", group=label, **s,
                             real_low=None if lo is None else lo * 100, real_high=None if hi is None else hi * 100,
                             direction=d, gap_pts=gap, confidence=b["confidence"], sources=" ".join(b["sources"]),
                             note=f"{b['real']}. {b['note']}"))
    return rows


def pdf_stated_vs_formula(cards):
    """The PDF prints percentages next to some ratings. Compare them with the dice rule."""
    med_pass = int(cards["pass"].median())
    med_handles = int(cards.handles.median())
    rows = []
    for band, rng, stated in [("green", (8, 10), (40, 50)), ("orange", (6, 7), (30, 35)), ("red", (5, 5), (25, 25))]:
        for i in range(rng[0], rng[1] + 1):
            rows.append(dict(rating="Intercept", value=i, band=band, pdf_stated_pct=f"{stated[0]}-{stated[1]}",
                             formula=f"P(intercept) = 1 - (Pass - Intercept)/20, at median card Pass {med_pass}",
                             formula_pct=100 - core.d20_le(med_pass - i) * 100,
                             formula_pct_vs_opponent_20=100 - core.d20_le(20 - i) * 100,
                             formula_pct_vs_opponent_11=100 - core.d20_le(11 - i) * 100))
    for band, rng, stated in [("green", (4, 5), (20, 25)), ("orange", (2, 3), (10, 15)), ("red", (1, 1), (0, 9))]:
        for s in range(rng[0], rng[1] + 1):
            rows.append(dict(rating="Steal", value=s, band=band, pdf_stated_pct=f"{stated[0]}-{stated[1]}",
                             formula=f"P(steal) = P(d20 >= Handles - Steal), at median card Handles {med_handles}",
                             formula_pct=core.d20_ge(med_handles - s) * 100,
                             formula_pct_vs_opponent_20=core.d20_ge(20 - s) * 100,
                             formula_pct_vs_opponent_11=core.d20_ge(11 - s) * 100))
    for band, rng, stated in [("green", (4, 6), (20, 30)), ("orange", (6, 8), (30, 40)), ("red", (8, 11), (40, 55))]:
        for f in range(rng[0], rng[1] + 1):
            rows.append(dict(rating="Foul (Steal)", value=f, band=band, pdf_stated_pct=f"{stated[0]}-{stated[1]}",
                             formula="P(foul) = P(d20 <= Foul)", formula_pct=f * 5))
    for shot, bands in [("Mid-range contest", [("green", (6, 7), (30, 35)), ("orange", (4, 5), (20, 25))]),
                        ("Long-2 contest", [("green", (5, 6), (25, 30)), ("orange", (3, 4), (15, 20))]),
                        ("3-point contest", [("green", (5, 6), (25, 30)), ("orange", (3, 4), (15, 20))])]:
        for band, rng, stated in bands:
            for v in range(rng[0], rng[1] + 1):
                rows.append(dict(rating=shot, value=v, band=band, pdf_stated_pct=f"-{stated[0]} to -{stated[1]}",
                                 formula="points of make % removed = contest x 5", formula_pct=-v * 5))
    df = pd.DataFrame(rows)
    df["note"] = ""
    df.loc[df.rating.isin(["Intercept", "Steal"]), "note"] = (
        "Stated odds match the dice rule only when the opposing rating is 19-20; "
        "at typical opposing ratings the rule gives about 2x (Intercept) to 3x (Steal) the stated odds.")
    return df


def zone_order(shots):
    # real expected points per attempt (all attempts) from the sourced make %
    real = {"layup": 0.66 * 2, "post": 0.89, "floater": 0.44 * 2, "mid": 0.43 * 2,
            "long2": 0.42 * 2, "three (corner)": 0.391 * 3, "three (above break)": 0.354 * 3, "three": 0.364 * 3}
    rows = []
    for t in TIERS:
        for shot in C.SHOTS:
            typical = shots[shots.def_pos.isin(C.CONTESTERS[shot]) & (shots.off_tier == t)]
            r = dict(shooter_tier=t, shot=shot)
            for st in C.CONTEST_STATES:
                r[f"exp_pts_{st}"] = typical[f"{shot}_{st}_pct"].mean() / 100 * C.SHOT_POINTS[shot]
            r["real_exp_pts_all_attempts"] = real.get(shot)
            rows.append(r)
    df = pd.DataFrame(rows)
    # ordering checks among average (B) shooters, open looks, against real all-attempt order
    inv = []
    b = df[df.shooter_tier == "B"].set_index("shot")
    for x, y in itertools.permutations(C.SHOTS, 2):
        rx, ry = b.loc[x, "real_exp_pts_all_attempts"], b.loc[y, "real_exp_pts_all_attempts"]
        if rx is None or ry is None or pd.isna(rx) or pd.isna(ry):
            continue
        if rx - ry >= 0.10:
            for st in ("open", "full"):
                gx, gy = b.loc[x, f"exp_pts_{st}"], b.loc[y, f"exp_pts_{st}"]
                status = None
                if abs(gx - gy) < 0.05:
                    status = "tied in game (real gap lost)"
                elif gx < gy:
                    status = "ORDER REVERSED"
                if status:
                    inv.append(dict(check=f"{x} should beat {y} ({st} vs {st}, average shooters)",
                                    real=f"{rx:.2f} vs {ry:.2f}", game=f"{gx:.2f} vs {gy:.2f}", status=status))
    # Dunk vs layup: real basketball says the dunk is the higher-percentage finish.
    tot = better = 0
    for st in C.CONTEST_STATES:
        d, l = shots[f"dunk_{st}_pct"], shots[f"layup_{st}_pct"]
        tot += len(d); better += int((d > l).sum())
    inv.append(dict(check="dunk should be the higher-percentage finish than layup (any state)",
                    real="dunk is the highest-percentage shot (DUNK); PDF: dunks 'harder to block'",
                    game=f"dunk beats layup in {better} of {tot} pairing-states",
                    status=f"ORDER REVERSED in {100 - 100 * better / tot:.1f}% of pairing-states"))
    # Contested rim vs open three, by the shooter's three-point tier
    cards = core.load_cards()
    rim = shots[shots.def_pos.isin(["C", "PF"])].copy()
    rim["rim_full_pts"] = rim[["layup_full_pct", "dunk_full_pct"]].max(axis=1) / 100 * 2
    rim["open3_pts"] = rim["three_open_pct"] / 100 * 3
    rim["shooter_three"] = rim.off_card.map(cards.off_three)
    for lab, lo, hi in [("red three (<=7)", 0, 7), ("orange three (8-10)", 8, 10), ("green three (11+)", 11, 20)]:
        g = rim[(rim.shooter_three >= lo) & (rim.shooter_three <= hi)]
        share = (g.open3_pts > g.rim_full_pts).mean()
        inv.append(dict(check=f"open three vs fully contested rim attempt (by C/PF), {lab} shooters",
                        real=("real: elite-contested rim ~1.0 pts (46-54%), open three 0.9-1.05 for 30-35% shooters, "
                              "1.2+ for 40%+ shooters"),
                        game=f"open three is better in {share:.0%} of pairings",
                        status="matches direction" if (lo >= 8 and share > 0.8) else
                               ("too favourable to the three" if share > 0.4 else "matches direction")))
    return df, pd.DataFrame(inv)


def contest_effect(shots):
    rows = []
    for shot in C.SHOTS:
        typical = shots[shots.def_pos.isin(C.CONTESTERS[shot])]
        for t in TIERS:
            g = typical[typical.def_tier == t]
            o, w, f = (g[f"{shot}_{st}_pct"].mean() for st in C.CONTEST_STATES)
            zone = "rim" if shot in ("layup", "dunk") else ("three" if shot == "three" else None)
            bench = B.CONTEST_DROP_BENCHMARKS.get(zone)
            game_drop = None
            if bench:
                game_drop = (o - f) if bench[5] == "full" else (o - w)
            rows.append(dict(shot=shot, defender_tier=t, contesters="+".join(C.CONTESTERS[shot]),
                             open_pct=o, weak_pct=w, full_pct=f, weak_drop_pts=o - w, full_drop_pts=o - f,
                             compare_state=bench[5] if bench else None,
                             real_drop_low=bench[0] * 100 if bench else None,
                             real_drop_high=bench[1] * 100 if bench else None,
                             real_basis=bench[4] if bench else "no direct benchmark",
                             confidence=bench[3] if bench else "none",
                             ratio_game_to_real_mid=game_drop / ((bench[0] + bench[1]) * 50) if bench else None))
    return pd.DataFrame(rows)


def tier_separation(cards):
    rows = []
    for key, spec in C.STATS.items():
        if spec["group"] == "athletic":
            continue
        by = cards.pivot_table(index="type_code", columns="card_tier", values=key)
        gap = (by["A"] - by["C"]) * (1 if spec["better"] == "high" else -1)
        rows.append(dict(stat=key, label=spec["label"], mean_A_minus_C=gap.mean(), min_gap=gap.min(),
                         max_gap=gap.max(), gap_in_pct_pts=gap.mean() * 5,
                         types_with_no_gap=int((gap <= 0).sum())))
    df = pd.DataFrame(rows)
    # Compare shooter-tier gap with what one full contest takes away (same shot)
    return df


def positions(cards):
    keys = [k for k, s in C.STATS.items() if s["group"] != "athletic"]
    pos = cards.groupby("position")[keys].mean().reindex(C.POSITIONS).T
    expectations = [
        # (stat, ordering that real basketball implies, basis)
        ("handles", ["PG", "SG", "SF", "PF", "C"], "guards handle more; convention"),
        ("pass", ["PG", "SG", "SF", "PF", "C"], "PDF's own stated hierarchy PG > SG/SF > PF > C"),
        ("off_three", ["SG", "PG", "SF", "PF", "C"], "guards/wings shoot threes best; convention"),
        ("off_ft", ["SG", "PG", "SF", "PF", "C"], "bigs shoot free throws worst; convention"),
        ("off_post", ["C", "PF", "SF", "SG", "PG"], "PDF positional ranges"),
        ("screen", ["C", "PF", "SF", "SG", "PG"], "PDF: screen ratings rise from guards to centres"),
        ("def_layup", ["C", "PF", "SF", "SG", "PG"], "rim protection rises with size"),
        ("def_dunk", ["C", "PF", "SF", "SG", "PG"], "rim protection rises with size"),
        ("pressure_def", ["PG", "SG", "SF", "PF", "C"], "PDF: ratings decrease from guards to frontcourt"),
        ("def_three", ["SG", "SF", "PG", "PF", "C"], "perimeter defenders contest threes best; convention"),
        ("def_mid", ["SG", "SF", "PG", "PF", "C"], "bigs in drop coverage concede pull-up mid-range; convention"),
    ]
    rows = []
    for stat, order, basis in expectations:
        vals = pos.loc[stat]
        actual = list(vals.sort_values(ascending=False).index)
        # count pairwise inversions against expected order (ties ignored)
        inv = 0
        pairs = []
        for i, a in enumerate(order):
            for b in order[i + 1:]:
                if vals[a] < vals[b] - 0.25:
                    inv += 1
                    pairs.append(f"{b}>{a}")
        rows.append(dict(stat=stat, expected_order=">".join(order), game_order=">".join(actual),
                         **{p: round(vals[p], 2) for p in C.POSITIONS},
                         inversions=inv, inverted_pairs=", ".join(pairs), basis=basis))
    return pos, pd.DataFrame(rows)


def dominant(shots, acts):
    rows = []
    for col, name in [("dribble_pct", "Dribble vs Agility"), ("pass_pct", "Pass vs Intercept"),
                      ("screen_pct", "Screen vs Challenge"), ("steal_pct_pdf_rule", "Steal (PDF rule)"),
                      ("foul_on_steal_attempt_pct", "Foul on steal attempt")]:
        v = acts[col]
        top = acts.loc[v.idxmax()]
        low = acts.loc[v.idxmin()]
        rows.append(dict(kind="action", item=name, share_ge_75pct=(v >= 75).mean(), share_le_10pct=(v <= 10).mean(),
                         max_pct=v.max(), max_pairing=f"{top.off_card} v {top.def_card}",
                         min_pct=v.min(), min_pairing=f"{low.off_card} v {low.def_card}"))
    # defenders who reduce a zone to near zero at full contest (shooters of any tier)
    for shot in C.SHOTS:
        col = f"{shot}_full_pct"
        g = shots.groupby("def_card")[col]
        share_le10 = g.apply(lambda s: (s <= 10).mean())
        share_zero = g.apply(lambda s: (s <= 0).mean())
        worst = share_le10.idxmax()
        rows.append(dict(kind="shot, full contest", item=shot,
                         share_le_10pct=(shots[col] <= 10).mean(), share_zero=(shots[col] <= 0).mean(),
                         max_pct=shots[col].max(), min_pct=shots[col].min(),
                         defenders_with_any_zero=int((share_zero > 0).sum()),
                         worst_defender=worst, worst_defender_share_le_10pct=share_le10.max()))
        # same, restricted to the shooters who would really take this shot (tier A/B specialists)
    return pd.DataFrame(rows)


def ambiguity_effects(cards, acts):
    rows = []
    # 1. steal + foul on one roll or two
    for res in ("same_roll", "two_rolls"):
        rows.append(dict(question="Steal and foul: one d20 or two?", reading=res,
                         mean_steal_pct=acts[f"{res}_steal_pct"].mean(), mean_foul_pct=acts[f"{res}_foul_pct"].mean(),
                         mean_nothing_pct=acts[f"{res}_nothing_pct"].mean()))
    # 2. weak-side contest below zero
    n_aff, worst = 0, 0
    for shot in C.SHOTS:
        neg = cards["def_" + shot] < C.WEAK_SIDE_REDUCTION
        n_aff += int(neg.sum())
        worst = max(worst, int((C.WEAK_SIDE_REDUCTION - cards.loc[neg, "def_" + shot]).max() if neg.any() else 0))
    rows.append(dict(question="Weak-side contest below 0: floor at 0 or add to the shot?",
                     reading=f"{n_aff} card-shot ratings are below 3",
                     mean_steal_pct=np.nan, mean_foul_pct=np.nan, mean_nothing_pct=np.nan,
                     note=f"If not floored, a weak-side 'contest' would raise make % by up to {worst * 5} points."))
    return pd.DataFrame(rows)


def main():
    cards = core.load_cards()
    shots = pd.read_csv(C.OUT_DIR / "outcome_table_shots.csv")
    acts = pd.read_csv(C.OUT_DIR / "outcome_table_actions.csv")

    comp = pd.DataFrame(shot_comparison(cards, shots) + action_comparison(acts))
    comp.round(2).to_csv(C.OUT_DIR / "benchmark_comparison.csv", index=False)
    pdfv = pdf_stated_vs_formula(cards)
    pdfv.to_csv(C.OUT_DIR / "pdf_stated_vs_formula.csv", index=False)
    zo, inv = zone_order(shots)
    zo.round(3).to_csv(C.OUT_DIR / "rel_zone_order.csv", index=False)
    inv.to_csv(C.OUT_DIR / "rel_zone_order_checks.csv", index=False)
    ce = contest_effect(shots)
    ce.round(2).to_csv(C.OUT_DIR / "rel_contest_effect.csv", index=False)
    ts = tier_separation(cards)
    ts.round(2).to_csv(C.OUT_DIR / "rel_tier_separation.csv", index=False)
    pos, posx = positions(cards)
    pos.round(2).to_csv(C.OUT_DIR / "rel_position_means.csv")
    posx.to_csv(C.OUT_DIR / "rel_position.csv", index=False)
    dom = dominant(shots, acts)
    dom.round(3).to_csv(C.OUT_DIR / "dominant_pairings.csv", index=False)
    amb = ambiguity_effects(cards, acts)
    amb.round(2).to_csv(C.OUT_DIR / "ambiguity_effects.csv", index=False)
    pd.DataFrame(B.source_table()).to_csv(C.OUT_DIR / "sources.csv", index=False)

    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_rows", 200); pd.set_option("display.max_colwidth", 70)
    key = comp[(comp.group.isin(["all shooters", "all pairings"])) | comp.state.eq("all attempts (real)")]
    print(key[["metric", "item", "state", "group", "game_mean", "game_min", "game_max", "real_low", "real_high",
               "direction", "gap_pts", "confidence"]].round(1).to_string(index=False))
    print(inv.to_string(index=False))
    print(ce.round(1).to_string(index=False))
    print(ts.round(2).to_string(index=False))
    print(posx[["stat", "expected_order", "game_order", "inversions", "inverted_pairs"]].to_string(index=False))
    print(dom.round(3).to_string(index=False))
    print(amb.to_string(index=False))
    print(pdfv[pdfv.rating.isin(["Intercept", "Steal"])].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
