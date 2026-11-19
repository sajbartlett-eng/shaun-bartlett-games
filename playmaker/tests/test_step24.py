"""Step 24 (Shaun, 19 Nov 2026): the setup plan. The scout's case table against the contest rules; each side thinks
alone; the plan's parts."""
import itertools
import os
import shutil
import sys
from fractions import Fraction

import pytest

from playmaker_engine import board as B
from playmaker_engine import geometry as G
from playmaker_engine import plan as PL
from playmaker_engine import rules_config as RC
from playmaker_engine import scoring as SC
from playmaker_engine.scenarios import game_state

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')
RULES = RC.with_rules(digital=True, zone='on')
FAR_O = ['A14', 'B14', 'C14', 'D14']
FAR_X = ['N14', 'O14', 'P14', 'Q14']


def _spot(zone):
    """A square of the zone with a square in front (nearer the rim), beside (level) and behind (further) next to it."""
    for x in range(B.W):
        for y in range(2, B.H + 1):
            c = (x, y)
            if not B.on_board(c) or B.zone(c) != zone or c == RC.RIM:
                continue
            nb = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0) and B.on_board((x + dx, y + dy))]
            f = [q for q in nb if B.dist_rim(q) < B.dist_rim(c)]
            s = [q for q in nb if B.dist_rim(q) == B.dist_rim(c)]
            h = [q for q in nb if B.dist_rim(q) > B.dist_rim(c)]
            if f and s and h:
                return c, f[0], s[0], h[0]
    raise AssertionError(zone)


def _engine(off, dfn, i, j, t, where, how, s_rushed, d_rushed, front=True):
    """The case's value by the game's own rules (scoring), on a board built for it."""
    c, f, s, h = _spot(PL.SHOT_ZONE[t])
    if where == 'open':
        dq, arrow = B.parse_sq('M14'), 0
    else:
        dq = f if (where == 'square' or (where == 'side' and front)) else s if where == 'side' else h
        rules = RULES
        on = [a for a in range(8) if G.faces(rules, G.stance(rules, a, False), dq, c)]
        off_ = [a for a in range(8) if a not in on]
        arrow = on[0] if (where == 'square' or dq != f) else off_[0]
    o = [B.sq(c) if k == i else FAR_O.pop(0) if False else None for k in range(5)]
    spare_o, spare_x = list(FAR_O), list(FAR_X)
    o = [B.sq(c) if k == i else spare_o.pop(0) for k in range(5)]
    x = [B.sq(dq) if k == j else spare_x.pop(0) for k in range(5)]
    st = game_state(off, dfn, o, x, [arrow if k == j else 0 for k in range(5)], ball=i, rules=RULES, check=False)
    st = st.with_(rush_o=(1 << (2 * i)) if s_rushed else 0, rush_x=(1 << (2 * j)) if d_rushed else 0)
    if where == 'open' or how == 'hand':
        opt = SC.soft_option(st, i, t)
        assert (opt.defender == j) == (where != 'open')
        return Fraction(opt.ev), opt
    opt = next(q for q in SC.contest_options(st, i, t) if q.defender == j)
    plus5 = RC.STEAL_FOUL_BONUS if RC.app_rule(RULES, 'points_play_on') else 0
    return Fraction(opt.ev) + opt.p_foul * plus5, opt


def test_the_scouts_case_table_is_14_cases_a_jump_shot_and_22_an_inside_shot():
    for t in RC.JUMP_SHOTS:
        assert len(PL.cases_for(t)) * 2 == 14
    for t in PL.INSIDE:
        assert len(PL.cases_for(t)) * 2 == 22
    assert set(PL.INSIDE) == {'layup', 'dunk', 'post', 'floater'} and set(PL.SHOT_ZONE) == set(PL.INSIDE) | set(RC.JUMP_SHOTS)


@pytest.mark.parametrize('off,dfn', [('Five Out', 'High-Low'), ('Shoot and Protect', 'Lockdown'), ('High-Low', 'Run and Gun')])
def test_every_case_in_the_table_matches_the_contest_rules(off, dfn):
    from playmaker_engine.cards import TEAMS
    ocards, dcards = TEAMS[off], TEAMS[dfn]
    seen = 0
    for i, j in itertools.product(range(5), range(5)):
        for t in PL.SHOT_ZONE:
            rows = PL.shot_review(ocards[i], dcards[j], t, RULES)
            assert len(rows) == (14 if t in RC.JUMP_SHOTS else 22)
            for r in rows:
                s_r, d_r = r['shooter'] == 'rushed', r['defender'] == 'rushed'
                if r['where'] == 'side' and r['how'] == 'block':
                    for front, key in ((True, 'value_front'), (False, 'value_beside')):
                        v, opt = _engine(off, dfn, i, j, t, 'side', 'block', s_r, d_r, front)
                        assert v == r[key], (i, j, t, r, front)
                        assert opt.rolls == (1 if front else 2)
                else:
                    v, opt = _engine(off, dfn, i, j, t, r['where'], r['how'], s_r, d_r)
                    assert v == r['value'], (i, j, t, r)
                    if r['how'] == 'block':
                        assert opt.rolls == 2
                    if r['where'] != 'open':
                        assert opt.contest == r['contest'] >= 1          # D-193: every contest takes at least 1
                seen += 1
    assert seen == 25 * (3 * 14 + 4 * 22)


def test_a_square_defender_on_an_inside_shot_never_fouls_and_a_jump_shot_has_no_block():
    from playmaker_engine.cards import TEAMS
    c, f, s, h = _spot('K')
    on = next(a for a in range(8) if G.faces(RULES, G.stance(RULES, a, False), f, c))
    st = game_state('Five Out', 'High-Low', [B.sq(c)] + FAR_O, [B.sq(f)] + FAR_X, [on, 0, 0, 0, 0], ball=0, rules=RULES, check=False)
    assert all(q.defender != 0 for q in SC.contest_options(st, 0, 'layup'))     # in front with the arrow on him: no Contest action, no foul
    c3, f3, _, _ = _spot('3')
    st3 = game_state('Five Out', 'High-Low', [B.sq(c3)] + FAR_O, [B.sq(f3)] + FAR_X, [0] * 5, ball=0, rules=RULES, check=False)
    assert [q.defender for q in SC.contest_options(st3, 0, 'three')] == [-1]
    assert all(r['how'] in (None, 'hand') for r in PL.shot_review(TEAMS['Five Out'][0], TEAMS['High-Low'][0], 'three', RULES))
