"""Step 3k: the computer's setup, offence and defence (no rule changes). The offence places first from the cards alone
and anticipates the defence's best response; the defence sees the offence's placement, searches all 120 matchups and
gives each defender a job, then checks the whole defence. Scenario cards keep their fixed setups."""
import inspect
import time

import pytest

from playmaker_engine import board as B
from playmaker_engine import computer as C
from playmaker_engine import setup as SU
from playmaker_engine.actions import denier, movement_dests
from playmaker_engine.cards import TEAMS
from playmaker_engine.scenarios import game_state, scenario_state, setup_errors

PAIRINGS = [('Five Out', 'High-Low'), ('Twin Towers', 'Pace and Space'), ('Iron Wall', 'Bucket Brigade')]
TABLE = [B.parse_sq(q) for q in SU.TABLE_O]


def maker(off, dfn):
    return lambda o_sq, ball, xs, ar: game_state(off, dfn, [B.sq(q) for q in o_sq], [B.sq(q) for q in xs], list(ar), ball=ball, check=False)


def defend(off, dfn, level, o_sq=TABLE, ball=0, seed=1):
    make = maker(off, dfn)
    comp = C.Computer('X', level, seed=seed, habits=[])
    r = SU.defence_setup(comp, o_sq, ball, lambda xs, ar: make(o_sq, ball, xs, ar))
    return r, make(o_sq, ball, r['xs'], r['arrows'])


def attack(off, dfn, level, seed=1):
    return SU.offence_setup(C.Computer('O', level, seed=seed, habits=[]), maker(off, dfn), seed=seed)


# ---- matchups ------------------------------------------------------------------------------------------------------

def test_all_star_and_starter_put_the_best_three_point_defender_on_o2_rookie_does_not():
    dfn = TEAMS['High-Low']
    best = max(dfn[j].con('three') for j in range(5))
    closers = {j for j in range(5) if dfn[j].con('three') == best}
    for level in ('allstar', 'starter'):
        r, _ = defend('Five Out', 'High-Low', level)
        assert r['perm'].index(1) in closers, (level, r['perm'])
        assert any(line.startswith(f"Put X{r['perm'].index(1) + 1} on O2") for line in r['reasons'])
    r, _ = defend('Five Out', 'High-Low', 'rookie')
    assert r['perm'] == (0, 1, 2, 3, 4) and r['perm'].index(1) not in closers


def test_the_matchup_search_covers_all_120_assignments():
    perm, cost = SU.best_matchups(TEAMS['Five Out'], TEAMS['High-Low'])
    from itertools import permutations
    worst = min(max(cost[p[j]][j] for j in range(5)) for p in permutations(range(5)))
    assert max(cost[perm[j]][j] for j in range(5)) == worst


def test_the_defence_setup_starts_the_matchup_record():
    from playmaker_web.game import Game
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], ai={'X': 'allstar'}, place=True, seed=3, level='pro')
    g._place_side('O', TABLE, 0, None, actor='human')
    g._auto_place()
    rec = [r for r in _log(g) if r.get('type') == 'computer' and r.get('event') == 'setup' and r.get('side') == 'X']
    assert rec and rec[-1]['matchup'] and g.placing is None
    comp = g.policies['X']
    comp._track_matchups(g.state)
    assert list(comp.matchups) == [int(m.split('O')[1]) - 1 for m in rec[-1]['matchup']]


def _log(g):
    import json
    with open(g.log_path) as f:
        return [json.loads(l) for l in f]


# ---- the ball handler and variety ---------------------------------------------------------------------------------

def test_all_star_offence_starts_the_ball_with_the_best_creator_at_least_sometimes():
    off = TEAMS['Twin Towers']
    cr = SU.creator(off)
    assert cr != 0                                         # the best creator isn't O1 on this team
    rs = [attack('Twin Towers', 'Pace and Space', 'allstar', seed) for seed in range(1, 11)]
    with_him = [r for r in rs if r['ball'] == cr]
    assert with_him, [r['ball'] for r in rs]
    assert all(f'O{cr + 1}' in r['reasons'][0] and 'Started the ball with' in r['reasons'][0] for r in with_him)


def test_all_star_offence_varies_its_setup_within_its_margin():
    rs = [attack('Five Out', 'High-Low', 'allstar', seed) for seed in range(1, 11)]
    assert len({(tuple(r['squares']), r['ball']) for r in rs}) >= 3
    top = max(r['value'] for r in rs)
    assert all(r['value'] >= top - 1.5 for r in rs)


def test_rookie_offence_uses_the_fixed_formation_with_the_ball_on_the_best_creator():
    r = attack('Twin Towers', 'Pace and Space', 'rookie')
    cr = SU.creator(TEAMS['Twin Towers'])
    assert r['ball'] == cr and set(r['squares']) == set(TABLE) and r['squares'][cr] == B.parse_sq('I11')


# ---- legality ------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('off,dfn', PAIRINGS)
def test_every_setup_is_legal(off, dfn):
    make = maker(off, dfn)
    for level in ('rookie', 'starter', 'allstar'):
        for seed in (1, 2, 3):
            r = attack(off, dfn, level, seed)
            assert SU.ball_legal(r['squares'][r['ball']]), (level, seed, r)
            d, s = defend(off, dfn, level, r['squares'], r['ball'], seed)
            assert not setup_errors(tuple(r['squares']), tuple(d['xs']), r['ball']), (level, seed)
            assert all(0 <= a < 8 for a in d['arrows'])


def test_scenario_cards_keep_their_fixed_setups():
    from playmaker_web.game import Game
    for n in (1, 6, 13):
        g = Game(mode='hotseat', scenario=n, ai={'X': 'allstar'}, place=True, seed=1)
        assert not g.place_on and g.placing is None
        assert g.state.encode() == scenario_state(n, rules=g.rules).encode()


# ---- jobs ----------------------------------------------------------------------------------------------------------

def test_a_down_three_point_shooters_defender_sags_and_can_recover():
    # Twin Towers' O4 (Three 6▼) in the corner, O5 on the left block, against an All-Star Pace and Space defence
    o_sq = [B.parse_sq(q) for q in ('I11', 'C9', 'O9', 'Q3', 'G3')]
    r, s = defend('Twin Towers', 'Pace and Space', 'allstar', o_sq)
    j = r['perm'].index(3)
    assert r['jobs'][j] == 'sag', r['jobs']
    assert B.cheb(s.x[j], s.o[3]) == 2
    assert any(B.adjacent(q, s.o[3]) for q in movement_dests(s, 'X', j, 'move', s.ctx.rules))      # recovers in one Move


def test_an_up_shooters_defender_denies():
    r, s = defend('Five Out', 'High-Low', 'allstar')
    j = r['perm'].index(1)                                 # O2 (Three 13▲) on C9, the ball with O1 on I11
    assert r['jobs'][j] == 'deny' and denier(s, 0, 1) == j


def test_an_up_post_scorer_is_fronted():
    # High-Low's O5 (Post 18▲) on the left block, the ball on the left wing
    o_sq = [B.parse_sq(q) for q in ('D10', 'O9', 'Q3', 'I11', 'G3')]
    r, s = defend('High-Low', 'Five Out', 'allstar', o_sq)
    j = r['perm'].index(4)
    assert r['jobs'][j] == 'front', r['jobs']
    assert B.adjacent(s.x[j], s.o[4]) and B.cheb(s.x[j], s.o[0]) < B.cheb(s.o[4], s.o[0])


# ---- coherence -----------------------------------------------------------------------------------------------------

@pytest.mark.parametrize('off,dfn', PAIRINGS)
def test_no_all_star_defence_leaves_the_rim_unprotected(off, dfn):
    for seed in range(1, 6):
        r = attack(off, dfn, 'allstar', seed)
        d, s = defend(off, dfn, 'allstar', r['squares'], r['ball'], seed)
        problems, notes = SU.coherence(s, d['perm'], d['jobs'], s.ctx.off)
        assert 'rim' not in problems, (seed, [B.sq(q) for q in d['xs']])
        assert any('reserve is intact' in n for n in notes)


# ---- no hidden information, speed, the review ----------------------------------------------------------------------

def test_the_offence_setup_never_sees_a_defence_placement():
    params = list(inspect.signature(SU.offence_setup).parameters)
    assert params == ['comp', 'make', 'seed', 'budget_s', 'anticipate']          # cards and its own boards only
    seen = []
    base = maker('Five Out', 'High-Low')

    def make(o_sq, ball, xs, ar):
        seen.append(tuple(xs))
        return base(o_sq, ball, xs, ar)
    a = SU.offence_setup(C.Computer('O', 'allstar', seed=4, habits=[]), make, seed=4)
    b = SU.offence_setup(C.Computer('O', 'allstar', seed=4, habits=[]), base, seed=4)
    assert (a['squares'], a['ball']) == (b['squares'], b['ball'])                # a function of the cards and the seed


def test_setup_decisions_are_quick():
    for off, dfn in PAIRINGS:
        t = time.time()
        r = attack(off, dfn, 'allstar')
        defend(off, dfn, 'allstar', r['squares'], r['ball'])
        assert time.time() - t < 5.0


def test_the_review_explains_the_setup():
    from playmaker_engine.review import computer_facts
    recs = [dict(type='setup', computer=dict(O=dict(name='All-Star', habits=[], concepts_off=[]),
                                             X=dict(name='All-Star', habits=[], concepts_off=[]))),
            dict(type='computer', side='O', event='setup', possession=1,
                 text=['Started the ball with O3 (best creator) for a pick and roll for O3; four out, one in.']),
            dict(type='computer', side='X', event='setup', possession=1,
                 text=["Put X1 on O2: X2 couldn't close out on him (three contest 3 against 5).", 'X5 sagged off O5.'])]
    lines = computer_facts(recs)
    assert any('Started the ball with O3 (best creator)' in l for l in lines)
    assert any("Put X1 on O2: X2 couldn't close out on him" in l and 'X5 sagged off O5' in l for l in lines)


def test_setup_through_the_web_is_quick_and_places_only_the_humans_side_for_them():
    """A quick game against the computer: the computer places its own side within 5 seconds (the request the browser
    makes), and the standard-setup shortcut places only the human's side."""
    import json
    import urllib.request
    from playmaker_web.server import start_background
    srv, base = start_background()

    def post(path, body):
        req = urllib.request.Request(base + path, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
        t = time.time()
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read()), time.time() - t
    try:
        # the computer attacks first: it places the offence while the game is created
        g, t_new = post('/api/new', dict(mode='hotseat', teams=['Twin Towers', 'Pace and Space'], ai=dict(A='allstar'), place=True, seed=5, level='pro'))
        assert t_new < 5.0
        s = json.loads(urllib.request.urlopen(f"{base}/api/state?code={g['code']}&token={g['token']}").read())
        assert s['placing'] and s['placing']['side'] == 'X' and s['placing']['mine']
        r, t = post('/api/place', dict(code=g['code'], token=g['token'], preview=True))     # my side only
        assert r['state']['placing'] is None and t < 5.0
        # the human attacks first: the computer places the defence after the human's offence
        g, _ = post('/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], ai=dict(B='allstar'), place=True, seed=6, level='pro'))
        r, t = post('/api/place', dict(code=g['code'], token=g['token'], preview=True))
        assert r['state']['placing'] is None and t < 5.0
        xs = [p['sq'] for p in r['state']['x']]
        assert xs != ['I10', 'D8', 'N8', 'G4', 'N4']                                    # the computer's own placement
        for level in ('rookie', 'starter', 'allstar'):                                  # every level places, quickly
            for seat in ('A', 'B'):
                g, _ = post('/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], ai={seat: level}, place=True, seed=7, level='pro'))
                r, _ = post('/api/place', dict(code=g['code'], token=g['token'], preview=True))
                assert r['state']['placing'] is None, (level, seat)
                # the setup decision itself (the request also carries the computer's first turn of play)
                from playmaker_web.game import LOG_DIR
                import glob, os
                path = sorted(glob.glob(os.path.join(LOG_DIR, f"*_{g['code']}.jsonl")))[-1]
                with open(path) as f:
                    recs = [json.loads(l) for l in f]
                setups = [x for x in recs if x.get('type') == 'computer' and x.get('event') == 'setup']
                assert setups and all(x['seconds'] < 5.0 for x in setups), (level, seat, [x.get('seconds') for x in setups])
    finally:
        srv.shutdown()
