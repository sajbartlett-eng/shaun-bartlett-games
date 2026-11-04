"""Pair-by-pair closeout check: every offence card against every defence card, every shot type.

For each pairing the shooter stands on a square of the right zone with the defender adjacent,
nearer the rim (so no -3), and the engine's own contest code (scoring.contest_options) values:
  * no contest          : the open look, points x rating
  * clean closeout      : arrow on the shooter (a Move), points x (rating - contest), no foul roll
  * side-on closeout    : arrow off (a Quick Step or Sprint), foul roll first

Checks, for every pairing:
  1. A foul is never worth less to the offence than the open look (the and-one rule), so
     fouling a good look can never help the defence.
  2. A clean closeout is never worse for the defence than no contest.
Reports the share of pairings where a side-on closeout pays (lower expected value than no
contest), and why it doesn't where it doesn't.
"""
from fractions import Fraction

from . import board as B
from . import rules_config as RC
from .cards import CARDS
from .scoring import contest_options
from .state import Context, GameState

# shot type -> (shooter square, defender square): defender directly below, nearer the rim
SPOTS = {
    'layup': ('I4', 'I3'), 'dunk': ('I4', 'I3'), 'post': ('I4', 'I3'),
    'mid': ('I6', 'I5'), 'floater': ('I6', 'I5'),
    'long': ('I8', 'I7'),
    'three': ('I10', 'I9'),
}
SHOT_TYPES = tuple(SPOTS)
FILL_O = ('A14', 'C14', 'E14', 'G14')
FILL_X = ('K14', 'M14', 'O14', 'Q14')


def pairing(oc, dc, shot_type, rules=None):
    """Values for one pairing: dict(open, clean, side_on_ev, foul_points, p_foul)."""
    spos, dpos = (B.parse_sq(q) for q in SPOTS[shot_type])
    assert B.dist_rim(dpos) <= B.dist_rim(spos)
    ctx = Context([oc] * 5, [dc] * 5, rules)
    o = (spos,) + tuple(B.parse_sq(q) for q in FILL_O)
    x = (dpos,) + tuple(B.parse_sq(q) for q in FILL_X)
    on_arrow = B.dir_between(dpos, spos)
    clean_state = GameState(ctx=ctx, o=o, x=x, arrows=(on_arrow, 0, 0, 0, 0), ball=0)
    off_state = clean_state.with_(arrows=((on_arrow + 2) % 8, 0, 0, 0, 0))      # side-on
    none_opt = [opt for opt in contest_options(clean_state, 0, shot_type) if opt.defender == -1][0]
    clean = [opt for opt in contest_options(clean_state, 0, shot_type) if opt.defender == 0][0]
    side = [opt for opt in contest_options(off_state, 0, shot_type) if opt.defender == 0][0]
    return dict(open=none_opt.value, clean=clean.value, side_on_ev=side.ev, foul_points=side.ft,
                p_foul=side.p_foul, points=3 if shot_type == 'three' else 2)


def closeout_report(rules=None):
    cards = list(CARDS.values())
    total = foul_breaks = clean_breaks = pays = 0
    not_paying = not_paying_not_excellent = not_paying_three = 0
    examples = []
    for oc in cards:
        for dc in cards:
            for t in SHOT_TYPES:
                v = pairing(oc, dc, t, rules)
                total += 1
                if v['foul_points'] < v['open']:
                    foul_breaks += 1
                    if len(examples) < 10:
                        examples.append(f'{oc.key} {t} v {dc.key}: foul {v["foul_points"]} < open {v["open"]}')
                if v['clean'] > v['open']:
                    clean_breaks += 1
                if v['side_on_ev'] < v['open']:
                    pays += 1
                else:
                    not_paying += 1
                    if v['open'] < RC.SCENARIO_GOAL:
                        not_paying_not_excellent += 1
                    elif t == 'three':
                        not_paying_three += 1
    share = Fraction(pays, total)
    summary = (f'closeout matchups: {total} pairings ({len(cards)} offence x {len(cards)} defence x '
               f'{len(SHOT_TYPES)} shot types). Foul worth less than the open look: {foul_breaks}. '
               f'Clean closeout worse than none: {clean_breaks}. Side-on closeout pays in {pays} '
               f'({float(share):.1%}); of the {not_paying} where it does not, {not_paying_not_excellent} '
               f'({not_paying_not_excellent / max(1, not_paying):.0%}) are open looks under 30 and '
               f'{not_paying_three} more are Excellent threes.')
    return dict(total=total, foul_breaks=foul_breaks, clean_breaks=clean_breaks, pays=pays, share=share,
                not_paying=not_paying, not_paying_not_excellent=not_paying_not_excellent,
                not_paying_three=not_paying_three, examples=examples, summary=summary)
