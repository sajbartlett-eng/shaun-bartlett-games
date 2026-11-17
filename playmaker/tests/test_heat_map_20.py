"""Step 20 (Shaun, 17 Nov 2026): the heat map fixed and on for both sides (D-203, D-204, D-205).

The lasting gap: what the offence can still force after the defence's best answer, the best open threat or the threat
an overloaded defender leaves, read like for like (a fresh phase's view: the offence's full turn to come, whatever
either side has spent). The defence's answer is found by search over its real moves (each defender one movement,
arrows turned included) and leaves the lowest highest threat. An overload: a defender who is the only cover for
threats from two attackers; it is worth the threat left once he takes the bigger one. The search reads the lasting
gap at the end of every line, for both sides. The report's ruler reads it too, so a phase ending can't move it by
itself, every roll and every plus or minus 5 is named, and a claim the numbers can't support is never printed. Each
possession gets fresh dice unless a seed is set."""
import json
import os
import random
import re
import shutil
import sys

import pytest

from playmaker_engine import agent as AG
from playmaker_engine import board as B
from playmaker_engine import decide as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


def boards():
    import step_18s as T
    import step_18d as T18
    return [('shaun', T.board()), ('screen', T.screen_board()), ('closeout', T18.closeout_board())]


@pytest.fixture(scope='module')
def cov():
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    yield AG.coverage
    NodeEngine.uninstall()
    eng.p.kill()


# ---- part 0: the rulings ----------------------------------------------------------------------------------------------

def test_the_rulings_are_recorded_and_the_map_is_on_for_both_sides():
    text = open(os.path.join(ROOT, 'DECISIONS.md')).read()
    for d in ('D-203', 'D-204', 'D-205'):
        assert f'## {d}' in text or f'**{d}' in text or f'{d} ' in text, d
    assert 'Shaun, 17 Nov 2026' in text
    cfg = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')))['eval']
    assert cfg['map'] is True                                         # both sides, every level, by default
    assert len(os.listdir(os.path.join(ROOT, 'docs', 'reference', 'reports_4E81CC'))) == 8


# ---- part 1: the map -------------------------------------------------------------------------------------------------

@needs_node
def test_the_lasting_gap_is_what_is_left_after_the_defences_best_answer(cov):
    s = boards()[0][1]
    c = cov(s)
    assert c['lasting'] < c['before']                                # the answer takes something off
    assert c['strength'] == c['lasting']                             # one number is the defence's strength (D-201)
    movers = [a['x'] for a in c['answers']]
    assert len(movers) == len(set(movers)) <= 5                      # each defender one movement at most
    top_ov = max([v['value'] for v in c['overloads']], default=0.0)
    assert c['lasting'] == pytest.approx(max(c['left']['worth'] if c['left'] else 0.0, top_ov), abs=0.01)
    assert c['words'].startswith("The defence's best answer: ")


@needs_node
def test_the_shading_after_the_answer_agrees_with_the_words(cov):
    for name, s in boards():
        c = cov(s)
        darkest = max(v['worth'] for d in c['squares_after'] for v in d.values())
        assert darkest == pytest.approx(c['left']['worth'], abs=0.01), name
        assert f"on {c['left']['sq']}, worth {round(c['left']['worth'])}" in c['words'], name


@needs_node
def test_an_overload_is_one_defender_the_only_cover_for_two_attackers(cov):
    c = cov(boards()[2][1])                                          # the closeout board names three
    assert c['overloads']
    # re-recorded in step 21 (D-206): overloads count numbers (a group of one, two or three defenders, the only cover for
    # more attackers than there are of them), worth the best look the defence's best assignment leaves open
    for v in c['overloads']:
        attackers = {t['o'] for t in v['threats']}
        assert len(attackers) > len(v['xs'])
        assert 0 < v['value'] <= max(t['worth'] for t in v['threats']) + 1e-9
        if len(v['xs']) == 1 and len(attackers) == 2:                # one on two: what's left once he takes the bigger
            a, b = v['threats'][:2]
            assert B.cheb(B.parse_sq(a['sq']), B.parse_sq(b['sq'])) >= 3
            assert v['value'] == pytest.approx(min(a['worth'], b['worth']), abs=0.01)
        if len(v['xs']) == 1:
            assert re.fullmatch(rf"X{v['x'] + 1} is the only cover for O\d's .+ on [A-Q]\d+ and O\d's .+ on [A-Q]\d+: whichever he takes, "
                                r"the other is open \(worth \d+\)\.", v['line']), v['line']
        assert v['line'] in c['words']


@needs_node
def test_the_answer_turns_arrows_and_moves_within_one_movement(cov):
    for name, s in boards():
        c = cov(s)
        for a in c['answers']:
            assert 0 <= a['x'] < 5 and (a['arrow'] == -1 or 0 <= a['arrow'] < 8)


def test_the_measure_is_like_for_like():
    """Re-recorded in step 21 (D-206): the like-for-like read is now the reports' read of a phase start (fresh=True);
    the computer reads each side as it really is (tests/test_map_logic_21.py). Like for like, the same squares and
    arrows read the same whatever either side has spent, in any phase but the last."""
    s = boards()[0][1]
    L = D.lasting_of(s, fresh=True)['L']
    for kw in (dict(tok_o=1, moved_o=3, qs_o=1), dict(tok_x=0, moved_x=31), dict(phase=s.phase + 1, clock=s.clock - 4)):
        assert D.lasting_of(s.with_(**kw), fresh=True)['L'] == pytest.approx(L), kw
    assert D.lasting_of(s.with_(clock=2), fresh=True) is None         # the last phase has no next phase


@needs_node
def test_both_engines_agree_on_the_lasting_gap_the_answer_and_the_overloads(cov):
    import js_equivalence as E
    from playmaker_engine import jsbridge
    keep = dict(E._ZONE), dict(E._FIBA), dict(E._CONTROL)
    E._ZONE['v'] = 'on'
    E._CONTROL['size'] = 'app'
    E._FIBA.update(three_seconds='on', closely_guarded='on', fiba_fouled_shot='on', soft_contest='on', fiba_steal_foul='on', off_balance='on',
                   position_contest='on')
    try:
        rng = random.Random(11)
        seen = 0
        while seen < 8:
            s, meta = E.random_state(rng)
            if s.stage != 'play' or not meta['digital'] or s.clock <= 2:
                continue
            js = json.loads(AG.JS['coverage'](json.dumps(dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), options=dict(only='lasting')))))
            g = D.lasting_of(s)
            assert js['L'] == pytest.approx(g['L'], abs=0.006) and js['before'] == pytest.approx(g['before'], abs=0.006)
            assert js['overloads'] == g['ov'] and js['moves'] == g['moves']
            seen += 1
    finally:
        E._ZONE.clear(), E._ZONE.update(keep[0]), E._FIBA.clear(), E._FIBA.update(keep[1]), E._CONTROL.update(keep[2])
    run = json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step20', 'lasting_equal.json')))
    assert run['positions'] == run['equal'] >= 60


# ---- part 3: the computer plays from it, both sides -------------------------------------------------------------------

def test_the_search_reads_the_lasting_gap_at_every_lines_end_for_both_sides():
    s = boards()[0][1]
    keep = D.MAP_ME[0]
    try:
        for me in ('O', 'X', None):
            D.MAP_ME[0] = me
            r = D.Read(s)
            banked = D.foul_externality(s)
            assert r._map_leaf() == pytest.approx(banked + max(r.map_shot(), r.map_lasting()))
        assert D.Read(s, k=0, looks_per=3)._map_leaf() is None       # the quick look that orders the list keeps its own
    finally:
        D.MAP_ME[0] = keep


def test_a_game_plays_with_the_map_on_unless_it_asks_otherwise():
    from playmaker_web.game import Game
    keep = D.CONFIG['eval'].get('map')
    try:
        kw = dict(mode='hotseat', teams=['Five Out', 'High-Low'], seed=3, full=True, level='pro')
        Game(match_format='digital', **kw)
        assert D.CONFIG['eval']['map'] is True
        Game(match_format='digital', map_read='off', **kw)              # ?map=0
        assert D.CONFIG['eval']['map'] is False
        Game(match_format='digital', **kw)                               # the next game: the file's own setting
        assert D.CONFIG['eval']['map'] is True
    finally:
        D.CONFIG['eval']['map'] = keep


# ---- part 2: fresh dice and the report's ruler ------------------------------------------------------------------------

def _next(g):
    g.state = g.state.with_(stage='over')
    g.next_possession(g.tokens['both'])


def test_each_possession_gets_fresh_dice_and_a_seed_replays_them():
    from playmaker_web.game import Game
    kw = dict(mode='hotseat', match_format='digital', teams=['Five Out', 'High-Low'], full=True, level='pro', map_read='off')
    a, b = Game(seed=7, **kw), Game(seed=7, **kw)
    first = a.rng.random()
    assert b.rng.random() == first
    _next(a), _next(b)
    second = a.rng.random()
    assert second == b.rng.random()                                   # a seed: the same game replays, roll for roll
    assert second != first and second != random.Random(7).random()   # but each possession has its own dice
    c, d = Game(**kw), Game(**kw)
    _next(c), _next(d)
    assert c.rng.random() != d.rng.random()                           # no seed: fresh dice
    # and the computer's own variety: fresh each possession (it restarted from the game's seed every possession, so the
    # same teams in the same seats replayed a possession whenever the dice fell the same: game 4E81CC, 4 and 6)
    e, f = Game(seed=7, **kw), Game(seed=7, **kw)
    one = e._policy('O', 'allstar').rng.random()
    e.possession = f.possession = 3
    three = e._policy('O', 'allstar').rng.random()
    assert three != one and three == f._policy('O', 'allstar').rng.random()


@needs_node
def test_the_report_names_every_roll_and_every_5_and_never_contradicts_itself():
    from playmaker_engine.plain import check
    from playmaker_web.api import Manager, handle
    from playmaker_web import report as R
    from playmaker_web.server import coverage_engine, stop_coverage_engine
    assert coverage_engine()
    AG.SCALE['value'] = 1.0                       # the rookies at their own budget: this game has dribbles and screens
    try:
        m = Manager()
        st, r = handle(m, 'POST', '/api/new', body=dict(mode='hotseat', match_format='digital', teams=['Five Out', 'High-Low'], seed=4,
                                                         level='pro', full=True, per_side=4, ai=dict(O='rookie', X='rookie')))
        g = m.get(r['code'])
        rolls = 0
        for p in range(1, 9):
            if p > 1:
                handle(m, 'POST', '/api/next', body=dict(code=g.code, token=r['token']))
            assert g.state.stage == 'over'
            rep = R.build(g, p)
            assert rep['checks'] == []
            lines = [t['offence'] + ' ' + t['defence'] for t in rep['turns']]
            joined = ' '.join(lines)
            assert 'best look' not in joined and not re.search(r'X\d now has', joined)
            for (pp, i), e in g._trail_entries.items():
                if pp != p:
                    continue
                a = g._trails[p][i][1]
                w = R.roll_words(a, e)
                if w:
                    rolls += 1
                    assert f'({w})' in joined, w                        # every roll, with its result, in its line
                for x in R.points_words(e):
                    assert x in joined, x                               # every plus or minus 5, in its line
            for t in rep['turns']:                                      # every number is the lasting gap at that moment
                c0 = t['numbers']['maps']['before']
                if c0:
                    assert t['numbers']['before'] == (None if c0['last'] else round(c0['L']))   # the last phase: no next phase
            su = rep['setup']
            if su.get('numbers') and su['numbers']['left'] and round(su['numbers']['left']['worth']) > 0:
                assert f"worth {round(su['numbers']['left']['worth'])}" in su['offence']   # the after-the-answer number
            sm = rep['summary']
            texts = lines + [x for p_ in rep['phases'] for x in p_['offence'] + p_['defence']] + [x for x in (sm['verdict'], sm['score'], sm['best'], sm['trend']) if x]
            for x in texts:
                assert not check(x), x
        assert rolls >= 1
    finally:
        stop_coverage_engine()


def test_the_roll_words_follow_the_rules_labels():
    from playmaker_engine.actions import Action
    from playmaker_web import report as R
    e = lambda *p: dict(rolls=[dict(picked=x) for x in p])
    assert R.roll_words(Action('dribble', 'O', 0, target=1), e('success')) == 'the dribble beat X2'
    assert R.roll_words(Action('dribble', 'O', 0, target=1), e('failure')) == 'X2 stopped the dribble'
    assert R.roll_words(Action('intercept', 'X', 2), e('failure')) == 'the pass was intercepted'
    assert R.roll_words(Action('intercept', 'X', 2), e('success')) == 'the pass got through'
    assert R.roll_words(Action('steal', 'X', 0), e('no foul', 'stolen')) == 'the steal won the ball'
    assert R.roll_words(Action('steal', 'X', 0), e('no foul', 'kept')) == 'the steal missed'
    assert R.roll_words(Action('steal', 'X', 0), e('foul')) == 'fouled on the steal'
    assert R.roll_words(Action('challenge', 'X', 0, target=3), e('success')) == 'the screen held'
    assert R.roll_words(Action('challenge', 'X', 0, target=3), e('failure')) == 'the challenge beat the screen'
    out = dict(outcomes=[dict(tone='bad_O', text='Pass intercepted: −5. The ball goes back to the passer.'), dict(tone='info', text='New phase: clock 8.')])
    assert R.points_words(out) == ['Pass intercepted: −5']


def test_the_consistency_check_catches_a_weaker_phase_no_turn_weakened():
    from playmaker_web import report as R
    turn = dict(phase=1, turn=1, rose=0, answered=0, shot=None)
    rep = dict(phases=[dict(phase=1, start=18, end=22, offence=['The lasting gap went from 18 to 22 this phase: the defence got weaker.'], defence=[])],
               turns=[turn], summary=None)
    assert R.consistency(rep)
    lines = R.phase_assessment(None, 1, [dict(turn, numbers=dict(before=18, after_offence=18, after_defence=18), words={})],
                               dict(L=18), dict(L=22), None)
    assert 'weaker' not in ' '.join(lines['offence'])                  # rewritten as what the number did
