"""Step 22c (D-223 to D-228, Shaun, 18 Nov 2026): stagnation in the list (the Steal, the closely guarded count, the shot
clock), zone gaps as a race, two helpers as a takeover, and the rules' clarification that a zone never blocks a pass."""
import os
import re
import shutil
import sys

import pytest

from playmaker_engine import board as B
from playmaker_engine import decide as D
from playmaker_engine import rules_config as RC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


@pytest.fixture(scope='module')
def js():
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    yield eng
    eng.close()


def board(xs=None, arrows=None, **kw):
    import step_22b as S
    s = S._board(xs, arrows)
    return s.with_(**kw) if kw else s


def cov(s, **opts):
    import step_22b as S
    return S._js(s, **opts)


def opts_of(s):
    r = D.Read(D.cov_off_fresh(s))
    return r, r.map_options()


def test_the_rulings_are_recorded_and_the_rules_text_says_a_zone_never_blocks_a_pass():
    text = open(os.path.join(ROOT, 'DECISIONS.md')).read()
    for d in ('D-223', 'D-224', 'D-225', 'D-226', 'D-227', 'D-228'):
        assert f'**{d}.' in text, d
    assert 'Play stagnation' in text and 'very susceptible to being beaten' in text and 'Is one\nphase enough? A phase is only 2 seconds.' in text
    assert 'never block a pass' in open(os.path.join(ROOT, 'docs', 'rules_register.md')).read()
    assert 'never a pass' in open(os.path.join(ROOT, 'playmaker_web', 'static', 'coach.js')).read()


# ---- item 1: stagnation, in points by the rules -------------------------------------------------------------------------

def strong_thief(s, j, steal=16, foul=1):
    """The same position with defender j a real thief (his card's Steal and steal-foul ratings changed)."""
    import copy
    ctx = copy.copy(s.ctx)
    card = copy.copy(s.ctx.dfn[j])
    object.__setattr__(card, 'r', dict(card.r, steal=steal, foul_steal=foul))
    object.__setattr__(ctx, 'dfn', tuple(card if k == j else c for k, c in enumerate(s.ctx.dfn)))
    return s.with_(ctx=ctx)


def test_the_steal_counts_at_its_chance_and_foul_risk_and_never_above_nothing():
    s = board(['I10', 'D8', 'O8', 'I6', 'P2'], [0, 7, 0, 0, 1])       # X1 in front of the ball handler, an arrow on him
    _, opts = opts_of(s)
    # by the cards this defence fouls more than it steals: a Steal favours the offence, so the defence doesn't try
    card, bh = s.ctx.dfn[0], s.ctx.off[0]
    pf = card.r['foul_steal'] / 20
    kept = (bh.r['dribble'] - card.r['steal']) / 20
    assert 5 * pf - 5 * (1 - pf) * (1 - kept) > 0
    assert all(o[9] == 0 for o in opts.values())
    # a real thief on him: holding the ball within his reach costs the chance of the -5, less the foul's +5
    t = strong_thief(s, 0)
    _, o2 = opts_of(t)
    pf2, kept2 = 1 / 20, (bh.r['dribble'] - 16) / 20
    ev = 5 * pf2 - 5 * (1 - pf2) * (1 - kept2)                        # one foul roll: +5 if fouled, else -5 unless he keeps it
    assert -5 < ev < 0
    costs = [o[9] for k, o in o2.items() if k[0] == 0]
    assert all(-5 <= c <= 0 for c in costs) and any(c == pytest.approx(ev) for c in costs)
    assert D.top_of(t) <= D.top_of(s) + 1e-9                          # the list can only read lower for it


def test_the_closely_guarded_count_is_counted_at_its_distance_from_the_violation():
    s = board(['I10', 'D8', 'O8', 'I6', 'P2'], [0, 7, 0, 0, 1])
    from playmaker_engine.actions import closely_guarded
    assert closely_guarded(s)
    for held in (0, 1, 2):
        t = s.with_(grd=2 | held << 2)                                # he has picked the ball up (he can only hold, pass or shoot), the count at `held`
        assert t.picked_up()
        _, opts = opts_of(t)
        mine = [o for k, o in opts.items() if k[0] == 0]
        assert mine and all(o[6] == t.o[0] and o[7] == 0 for o in mine)
        # Re-recorded in step 27 (D-256, the prompt's item 6: by the rule, no thirds): nothing until the phase end
        # where the count falls, then all of the -5 (it read a third, two thirds, all of it)
        assert all(o[9] == pytest.approx(-5 if held + 1 >= RC.GUARDED_ENDS else 0) for o in mine)
        free = s.with_(grd=held << 2)                                 # free to move: moving starts the count again, nothing owed
        _, opts = opts_of(free)
        assert all(o[9] == 0 for k, o in opts.items() if k[0] == 0)
    away = board().with_(grd=2 | 2 << 2)                              # the same count with nobody's arrow on him next to him: nothing owed
    if not closely_guarded(away):
        _, opts = opts_of(away)
        assert all(o[9] == 0 for o in opts.values())


# ---- the revision: zone gaps are a race (D-228) ---------------------------------------------------------------------------

PACKED = ['A1', 'B1', 'C1', 'D1', 'E1']                               # the defence bunched in one corner: the far side is there to be won
MID_O, MID_X = ['I9', 'H9', 'J9', 'I10', 'I8'], ['A1', 'B1', 'A2', 'B2', 'A3']     # the attackers bunched too: some races take two phases


def mid(**kw):
    import step_22b as S
    s = S._board(MID_X, [0, 0, 0, 0, 0], MID_O)
    return s.with_(**kw) if kw else s


def gaps_of(s):
    r = D.Read(D.cov_off_fresh(s))
    st = r._lg_root(r.map_options())
    return r, r._gap_info(), r._gap_vec(st)


def test_a_square_is_a_gap_only_when_an_attacker_gets_there_before_any_defender_is_set():
    s = mid()
    r, g, gv = gaps_of(s)
    rules, n = s.ctx.rules, s.clock // RC.PHASE_SECONDS - 1
    A = [D._phase_dist(rules, s.o[a], s.ctx.off[a].qs) for a in range(5)]
    arr = [D._arrive(rules, s.x[d], s.ctx.dfn[d].qs, 1) for d in range(5)]
    won = lost = far = 0
    for k, q in enumerate(g['sq']):
        if q in s.x:
            assert gv[k] == 0
            continue
        setp = min(z[0].get(q, D.INF) for z in arr)
        winners = [a for a in range(5) if max(1, A[a].get(q, D.INF)) <= n and setp > max(1, A[a].get(q, D.INF))]
        if not winners:
            assert gv[k] == 0                                         # every attacker loses the race: not a gap, however valuable
            lost += 1
            continue
        won += gv[k] > 0
        far += gv[k] > 0 and all(max(1, A[a].get(q, D.INF)) >= 2 for a in winners)
        assert gv[k] <= max(g['open'][k][a] for a in winners) + 1e-9  # never more than the winner's own shot there
    assert won and lost and far                                       # (and some are won only over two phases or more: no fixed horizon)
    # the ball handler has the ball for certain: a square he wins that no defender can reach at all in time is worth his shot there
    bh = s.ball
    his = [k for k, q in enumerate(g['sq']) if q not in s.x and max(1, A[bh].get(q, D.INF)) <= n
           and all(z[1].get(q, D.INF) > max(1, A[bh].get(q, D.INF)) for z in arr)]
    assert his and all(gv[k] >= g['open'][k][bh] - 1e-9 for k in his)
    # anyone else has it at the pass's chance by the rules, a lost pass -5 (D-198)
    for a in range(5):
        if a == bh:
            continue
        q = s.o[a]
        if q in g['idx'] and all(z[1].get(q, D.INF) > 1 for z in arr):
            ch = D.cov_pass(s, a, q)
            assert gv[g['idx'][q]] >= ch * g['open'][g['idx'][q]][a] - (1 - ch) * 5 - 1e-9


def test_a_square_every_attacker_loses_the_race_to_is_not_a_gap_however_valuable():
    s = board()                                                       # Shaun's board as it stood: a defender is set on every square in time
    r, g, gv = gaps_of(s)
    assert max(gv) == 0
    k = g['idx'][B.parse_sq('I3')]                                    # the green zone: the most valuable squares on the court
    assert max(g['open'][k]) >= max(max(row) for row in g['open']) - 1e-9 or max(g['open'][k]) > 30


def test_a_defender_who_only_gets_a_hand_up_off_balance_brings_that_contest():
    s = board(PACKED, [0, 0, 0, 0, 0])
    r, g, gv = gaps_of(s)
    rules, n = s.ctx.rules, s.clock // RC.PHASE_SECONDS - 1
    A = [D._phase_dist(rules, s.o[a], s.ctx.off[a].qs) for a in range(5)]
    arr = [D._arrive(rules, s.x[d], s.ctx.dfn[d].qs, 1) for d in range(5)]
    bh, seen = s.ball, 0
    for k, q in enumerate(g['sq']):
        t = max(1, A[bh].get(q, D.INF))
        if q in s.x or t > n or min(z[0].get(q, D.INF) for z in arr) <= t:
            continue
        late = [d for d in range(5) if arr[d][1].get(q, D.INF) <= t]
        if not late:
            continue
        w = min(r._gap_late(g, k, bh, d) for d in late)
        assert w <= g['open'][k][bh] and gv[k] >= min(w, g['open'][k][bh]) - 1e-9
        seen += w < g['open'][k][bh]
    assert seen                                                       # somewhere the late hand takes something off his shot


def test_as_the_shot_clock_runs_down_the_far_squares_stop_counting():
    early, late = mid(clock=12), mid(clock=4)
    r1, g, gv1 = gaps_of(early)
    r2, _, gv2 = gaps_of(late)
    assert r1._gap_race()['n'] == 5 and r2._gap_race()['n'] == 1      # the phases the clock leaves after this one
    n1, n2 = sum(v > 0 for v in gv1), sum(v > 0 for v in gv2)
    assert 0 < n2 < n1                                                # fewer squares can still be won
    A = [D._phase_dist(late.ctx.rules, late.o[a], late.ctx.off[a].qs) for a in range(5)]
    for k, q in enumerate(g['sq']):
        if gv2[k] > 0:
            assert any(A[a].get(q, D.INF) <= 1 for a in range(5))     # only what somebody reaches in the one phase left
        assert gv2[k] <= gv1[k] + 1e-9                                # nothing open reads worse for the defence the later it is
    assert D.top_of(late) <= D.top_of(early) + 1e-9
    assert D.lasting_of(late)['list'] != D.lasting_of(early)['list']


@needs_node
def test_both_engines_count_stagnation_the_same(js):
    s = board(['I10', 'D8', 'O8', 'I6', 'P2'], [0, 7, 0, 0, 1])
    packed = board(PACKED, [0, 0, 0, 0, 0])
    for t in (s, s.with_(grd=2 | 2 << 2), strong_thief(s, 0), board(clock=4), board(clock=6, grd=2 | 1 << 2), packed, mid(), mid(clock=4)):
        j = cov(t, only='lasting')
        g = D.lasting_of(t)
        assert j['L'] == pytest.approx(g['L'], abs=0.01) and j['top'] == pytest.approx(D.top_of(t))
        assert j['drivers']['list'] == pytest.approx(g['list'], abs=0.011)


# ---- item 2: two defenders helping count as a takeover -------------------------------------------------------------------

@needs_node
def test_a_beaten_defenders_man_the_help_already_covers_is_taken_over_and_stays_taken(js):
    import step_21 as T
    from playmaker_engine import plain as P
    b1 = T.b1()                                                       # O1 has driven to I4; X1 behind him on I8; X4 and X5 beside him
    prev = [0, 1, 3, 2, 4]
    fixed = cov(b1, only='roles', prev=prev, fixed=True)
    assert fixed['perm'] == prev and fixed['takeover'] is None        # only read: nothing is called
    ro = cov(b1, only='roles', prev=prev)
    # Re-recorded in step 28 (D-261: the contest is one of the reply's two actions, so each defender reaches less). The
    # help still takes O1 from the beaten X1, but the named matchups now cover more than the takeover's own pick, so
    # the read calls that switch at once (it used to call the takeover, "X4 and X5 have O1: X1 picks up O5", and then a
    # second read switched again). The read settles in one go: read again with nothing changed, it stands.
    t = ro['takeover']
    if t:
        assert t['x'] == 0 and t['man'] == 0 and sorted(t['helpers']) == [3, 4]
        assert ro['switched'] == f"X4 and X5 have O1: X1 picks up O{t['picks'] + 1}."
    assert ro['perm'].index(0) in (3, 4) and ro['perm'][0] != 0       # a helper has O1; the beaten X1 has another man
    assert ro['switched'] and not any(re.search(r'\b' + re.escape(w) + r'\b', ro['switched'], re.I) for w in P.BANNED)
    again = cov(b1, only='roles', prev=ro['perm'])                    # read again with nothing changed: it stands
    assert again['perm'] == ro['perm'] and again['switched'] is None


@needs_node
def test_nobody_is_taken_over_who_isnt_beaten(js):
    st = board(['G7', 'N5', 'H10', 'K7', 'G3'], [0, 0, 3, 0, 0])      # this step's settlement: O1 up top, nobody past his man
    free = cov(st, only='roles')
    kept = cov(st, only='roles', prev=free['perm'])
    assert kept['takeover'] is None and kept['perm'] == free['perm']


# ---- item 3: the Watch replay shows the lines ----------------------------------------------------------------------------

@needs_node
def test_the_watch_replay_shows_each_defenders_job_as_the_live_view_does():
    from playmaker_engine import agent as AG
    from playmaker_web.api import Manager, handle
    from playmaker_web.view import coverage_json
    from playmaker_web.server import coverage_engine, stop_coverage_engine
    assert coverage_engine()
    AG.SCALE['value'] = 1.0
    try:
        m = Manager()
        st, r = handle(m, 'POST', '/api/new', body=dict(mode='hotseat', match_format='digital', teams=['Five Out', 'High-Low'], seed=5,
                                                         level='pro', full=True, per_side=4, ai=dict(O='rookie', X='rookie')))
        g, tok = m.get(r['code']), r['token']
        shown = 0
        for e in g.feed:
            v = coverage_json(g, tok, n=e['n'])
            if not v or not v.get('roles'):
                continue
            shown += 1
            assert [q['x'] for q in v['roles']] == [0, 1, 2, 3, 4] and all(q['line'].startswith(f"X{q['x'] + 1}") for q in v['roles'])
        assert shown >= 2
        hist = g._assign_chain(1)['hist']
        assert len(hist) == len(g._trails[1]) and all(sorted(p) == [0, 1, 2, 3, 4] for p, _ in hist if p)
    finally:
        stop_coverage_engine()
