"""
Task 4: the game's exact success % for every offence card vs every defence card
(75 x 75 = 5,625 pairings).

Outputs:
  output/outcome_table_actions.csv   Dribble, Pass, Screen, Steal, Foul (Steal) per pairing
  output/outcome_table_shots.csv     make % for 7 shot types x open / weak-side / full contest
  output/steal_conversion_check.csv  proof the printed-card steal rule equals the PDF rule
"""
import itertools

import pandas as pd

import config as C
import core


def main():
    cards = core.load_cards()
    shot_rows, act_rows = [], []
    for oid, did in itertools.product(cards.index, cards.index):
        off, dfn = cards.loc[oid], cards.loc[did]
        base = dict(off_card=oid, off_pos=off.position, off_tier=off.card_tier,
                    def_card=did, def_pos=dfn.position, def_tier=dfn.card_tier)

        srow = dict(base)
        for shot in C.SHOTS:
            for state in C.CONTEST_STATES:
                eff = off["off_" + shot] - core.contest_value(dfn, shot, state)
                srow[f"{shot}_{state}_pct"] = min(max(eff, 0), 20) * 5
        shot_rows.append(srow)

        pf_same, ps_same, pn_same = core.steal_attempt_outcomes(off, dfn, "same_roll")
        pf_two, ps_two, pn_two = core.steal_attempt_outcomes(off, dfn, "two_rolls")
        act_rows.append(dict(
            base,
            dribble_pct=core.p_dribble(off, dfn) * 100,
            pass_pct=core.p_pass(off, dfn) * 100,
            screen_pct=core.p_screen(off, dfn) * 100,
            steal_pct_pdf_rule=core.p_steal_pdf(off, dfn) * 100,
            keep_pct_printed_rule=core.p_keep_printed(off, dfn) * 100,
            foul_on_steal_attempt_pct=core.d20_le(dfn["foul_stl"]) * 100,
            same_roll_foul_pct=pf_same * 100, same_roll_steal_pct=ps_same * 100, same_roll_nothing_pct=pn_same * 100,
            two_rolls_foul_pct=pf_two * 100, two_rolls_steal_pct=ps_two * 100, two_rolls_nothing_pct=pn_two * 100,
        ))
    shots = pd.DataFrame(shot_rows)
    acts = pd.DataFrame(act_rows)
    C.OUT_DIR.mkdir(parents=True, exist_ok=True)
    shots.to_csv(C.OUT_DIR / "outcome_table_shots.csv", index=False)
    acts.to_csv(C.OUT_DIR / "outcome_table_actions.csv", index=False)

    # Steal conversion: check every integer gap, not just the card pairs.
    rows = []
    for handles in range(1, 21):
        for steal in range(0, 11):
            p_pdf = core.d20_ge(handles - steal)
            p_keep = core.d20_le(handles - (steal + C.PRINTED_STEAL_OFFSET))
            rows.append(dict(handles=handles, steal_pdf=steal, steal_printed=steal + C.PRINTED_STEAL_OFFSET,
                             steal_pct_pdf=p_pdf * 100, steal_pct_printed=(1 - p_keep) * 100,
                             identical=abs(p_pdf - (1 - p_keep)) < 1e-12))
    conv = pd.DataFrame(rows)
    conv.to_csv(C.OUT_DIR / "steal_conversion_check.csv", index=False)
    card_ok = ((acts.steal_pct_pdf_rule + acts.keep_pct_printed_rule - 100).abs() < 1e-9).all()
    print(f"steal conversion exact for all {len(conv)} integer cases: {conv.identical.all()}; "
          f"for all 5,625 card pairings: {card_ok}")
    return shots, acts


if __name__ == "__main__":
    main()
