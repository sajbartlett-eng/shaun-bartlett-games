"""Step 26 (Shaun, 19 Nov 2026): the defence feels the danger of the pass. One board for each item."""
import os
import shutil
import sys

import pytest

from playmaker_engine import board as B
from playmaker_engine import decide as D
from playmaker_engine import rules_config as RC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


def state(o, x, ar, ball=0, off='Twin Towers', dfn='Lockdown', **kw):
    import step_21 as T
    s = T._state(o, x, ar, ball=ball, off=off, dfn=dfn)
    return s.with_(**kw) if kw else s


def opts(s):
    return D.Read(D.cov_off_fresh(s)).map_options()


def test_the_ruling_no_screen_no_blocked_diagonal():
    # two attackers side by side (H5 and I4) don't stop the defender on I5 stepping diagonally to H4 between them
    s = state(['N12', 'H5', 'I4', 'A3', 'Q3'], ['I5', 'D8', 'O8', 'B4', 'P4'], [4, 0, 0, 0, 0])
    free, fixed = D.defender_map(s.with_(tok_x=RC.TOKENS_PER_PHASE), 0, exact=True)
    assert B.parse_sq('H4') in free


def test_in_time_uses_the_real_paths_around_bodies():
    # item 3: a defender above a bunch reaches the block only if a path goes around the bodies; standing on a square
    # walls it off. The same defender with the bunch gone reaches more contests.
    o = ['N12', 'G4', 'H4', 'I4', 'J4']
    s = state(o, ['H6', 'D8', 'O8', 'B9', 'P9'], [4, 0, 0, 0, 0])
    sN = D.cov_off_fresh(s).with_(screens=(), tok_x=RC.TOKENS_PER_PHASE, moved_x=0, qs_x=0, lock_x=0, rush_x=0, beaten=())
    body = D._body_cmap2(sN, 0, 1)
    geo = D._cmap2(s.ctx.rules, s.x[0], s.arrows[0], s.ctx.dfn[0].qs, 1)
    lost = [c for c, pair in geo.items() if pair[2] and not (c in body and body[c][2])]
    assert lost, 'the bunch walls off some contest the straight-line reach would claim'
    assert all(c in geo and (geo[c][2] & body[c][2]) == body[c][2] for c in body if body[c][2])      # never more than the open court
    empty = state(['N12', 'A12', 'B12', 'C12', 'D12'], ['H6', 'D8', 'O8', 'B9', 'P9'], [4, 0, 0, 0, 0])
    sE = D.cov_off_fresh(empty).with_(screens=(), tok_x=RC.TOKENS_PER_PHASE, moved_x=0, qs_x=0, lock_x=0, rush_x=0, beaten=())
    bodyE = D._body_cmap2(sE, 0, 1)
    assert sum(1 for p in bodyE.values() if p[2]) > sum(1 for p in body.values() if p[2])


def test_a_pass_counts_from_every_square_the_ball_handler_can_reach_this_turn():
    # item 2: a big on the block, the lane from where the passer stands denied; he can Move, Quick Step or Sprint to a
    # new angle and pass in the same turn
    s = state(['L7', 'G2', 'O9', 'A9', 'Q3'], ['K7', 'H3', 'O8', 'B8', 'P4'], [5, 6, 0, 0, 0])
    assert D.cov_pass(s, 1, s.o[1]) == 0                          # from L7 X2 on H3 denies it
    held = [o for (a, c, r), o in opts(s).items() if a == 1 and o[6] == s.o[1]]
    assert held and max(o[0] for o in held) > 0                  # from a square the passer reaches, it can land


def test_both_outcomes_of_a_pass_are_counted():
    # item 1: a receiver's look is worth its value at the chance the pass lands, less 5 at the chance it is stopped
    s = state(['L7', 'G2', 'O9', 'A9', 'Q3'], ['K7', 'H3', 'O8', 'B8', 'P4'], [5, 6, 0, 0, 0])
    seen = 0
    for (a, c, r), o in opts(s).items():
        if a == s.ball or not 0 < o[0] < 1:
            continue
        assert o[2] == pytest.approx(o[0] * (o[1] + o[9]) - (1 - o[0]) * o[8])
        assert o[8] == 5
        seen += 1
    assert seen


def test_the_three_seconds_are_counted_at_their_distance():
    # item 4: having the ball in the key when the next phase starts is half the -5; already in the key at the last
    # phase end, all of it. Outside the key, nothing.
    # Re-recorded in step 27 (D-255, the prompt's item 5: by the rule, no halves): having the ball in the key at the
    # next phase start costs nothing (his shot goes up before the violation can fall); already in the key at the last
    # phase end, he can't avoid it at this one: all of the -5. Outside the key, nothing, as before.
    s = state(['N12', 'F8', 'O9', 'A9', 'Q12'], ['M11', 'B13', 'O8', 'B8', 'P11'], [5, 0, 0, 0, 0])
    for bit, cost in ((0, 0.0), (1, -5.0)):
        t = s.with_(key_o=bit << 1)
        ks = [o for (a, c, r), o in opts(t).items() if a == 1 and B.in_key(o[6])]
        out = [o for (a, c, r), o in opts(t).items() if a == 1 and not B.in_key(o[6])]
        assert ks and all(o[9] == pytest.approx(cost) for o in ks)
        assert out and all(o[9] == 0 for o in out)


@needs_node
def test_both_engines_read_these_boards_the_same():
    from playmaker_engine.jsbridge import NodeEngine
    import step_22b as S
    eng = NodeEngine().install()
    try:
        for s in (state(['L7', 'G2', 'O9', 'A9', 'Q3'], ['K7', 'H3', 'O8', 'B8', 'P4'], [5, 6, 0, 0, 0]),
                  state(['N12', 'G4', 'H4', 'I4', 'J4'], ['H6', 'D8', 'O8', 'B9', 'P9'], [4, 0, 0, 0, 0]),
                  state(['N12', 'F8', 'O9', 'A9', 'Q12'], ['M11', 'B13', 'O8', 'B8', 'P11'], [5, 0, 0, 0, 0], key_o=2)):
            j = S._js(s, only='lasting')
            g = D.lasting_of(s)
            assert j['L'] == pytest.approx(g['L'], abs=0.01)
            assert j['drivers']['list'] == pytest.approx([round(v, 2) for v in g['list']], abs=0.011)
    finally:
        eng.close()
