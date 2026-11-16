"""Step 18s, stop two (Shaun, 16 Nov 2026): D-201 (position at a phase's start: the rules stay), D-202 (the button
reads "Coverage"), and part 1: the reading's pass chance is the rules' own. A defender takes a pass through his square,
or after one straight movement along an arrow line to where it meets the pass, never from next to the passer. Before,
any defender who could step onto any square of the pass's line counted, the on-ball defender included."""
import json
import os
import random
import subprocess
import sys

import pytest

from playmaker_engine import board as B
from playmaker_engine import decide as D
from playmaker_engine import plain
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, mti_approach
from playmaker_engine.resolve import ChanceNode, apply
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import p_success, rolled

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = RC.with_rules(digital=True, zone='on')                    # the app's rules
O_ = ['I11', 'C9', 'O9', 'A3', 'Q3']                              # Shaun's board of 15 November
X_ = ['J10', 'D8', 'O8', 'B4', 'P2']
A_ = ['NW', 'NW', 'N', 'SW', 'NE']
_TEAMS = []


def teams():
    if not _TEAMS:
        from playmaker_engine import levels as LV, rosters as R
        from playmaker_engine.cards import register_cards
        d = R.deal('senior', 'pro', True, seed=3351)
        _TEAMS.extend(register_cards(f'shaun 18s2 {w}', LV.team(d['rosters'][k], 'senior', None)) for k, w in enumerate('OX'))
    return _TEAMS


def board(x=None, arrows=None, o=None, **kw):
    off, dfn = teams()
    s = game_state(off, dfn, list(o or O_), list(x or X_), list(arrows or A_), ball=0, rules=RULES, check=False, team_fouls=2, quarter_left=8)
    s.ctx.levels_key = ('senior', 'pro')
    return s.with_(**kw) if kw else s


def with_x(j, sq, arrow, **kw):
    return board(X_[:j] + [sq] + X_[j + 1:], A_[:j] + [arrow] + A_[j + 1:], **kw)


@pytest.fixture
def old_reading():
    D.CONFIG['eval']['pass_rules'] = False
    D._LP.clear()
    yield
    D.CONFIG['eval']['pass_rules'] = True
    D._LP.clear()


def rules_pass(s, i):
    """The chance a pass arrives, from the rules' own actions (None: the pass isn't legal)."""
    st = s.with_(side='O', stage='play', turn_n=0, tok_o=max(1, s.tok_o), pending=None)
    a = Action('pass', 'O', s.ball, target=i)
    if a not in legal_actions(st):
        return None
    nxt = apply(st, a)
    if isinstance(nxt, ChanceNode) or nxt.stage != 'play' or nxt.side != 'X' or not nxt.pending:
        return 1.0
    worst = 0.0
    for b in legal_actions(nxt):
        after = nxt if b.kind == 'intercept' else apply(nxt, b) if b.kind in ('move', 'qs', 'sprint') and mti_approach(nxt, b) else None
        if after is None or isinstance(after, ChanceNode) or not after.pending:
            continue
        worst = max(worst, 1 - float(p_success(rolled(after, 'O', s.ball, 'pass') - rolled(after, 'X', b.piece, 'intercept'), s.ctx.rules)))
    return 1.0 - worst


# ---- the rulings -------------------------------------------------------------------------------------------------------

def test_the_rulings_are_recorded_and_coverage_is_shauns_word():
    text = open(os.path.join(ROOT, 'DECISIONS.md'), encoding='utf-8').read()
    assert 'D-201' in text and 'D-202' in text
    assert 'Positioning barely matters at the start of a phase' in text
    assert 'coverage' not in plain.BANNED and 'threat' in plain.BANNED            # one word came off the list, and only that one
    assert plain.check('Coverage: shown') == [] and plain.check('the threat') == ['threat']
    js = open(os.path.join(ROOT, 'playmaker_web', 'static', 'app.js'), encoding='utf-8').read()
    assert "'Coverage: shown' : 'Coverage: hidden'" in js
    assert os.path.exists(os.path.join(ROOT, 'docs', 'reference', 'COVERAGE_MAP_BLUEPRINT_ADDENDUM_STRENGTH.md'))


# ---- part 1: the pass chance by the rules ------------------------------------------------------------------------------

def test_on_shauns_board_two_passes_cant_be_intercepted_and_the_third_is_a_lane_jump():
    s = board()
    assert [round(D._lane_p(s, a, s.o[a]), 3) for a in (1, 2, 4)] == [0.3, 1.0, 1.0]
    assert [rules_pass(s, a) for a in (1, 2, 4)] == [pytest.approx(0.3), 1.0, 1.0]
    assert D.pass_by_rules(RULES) and D.CONFIG['eval']['pass_rules'] is True


def test_the_old_reading_priced_every_one_of_them_at_one_in_four(old_reading):
    s = board()
    assert [round(D._lane_p(s, a, s.o[a]), 3) for a in (1, 2, 4)] == [0.25, 0.25, 0.25]


def test_who_can_take_a_pass_is_the_rules_answer():
    s = board()
    pa, pc = s.o[0], s.o[1]                                      # the pass from O1 (I11) to O2 (C9)
    passer = rolled(s, 'O', 0, 'pass')
    occ = set(s.o) | set(s.x)
    pi = lambda st, j, p, arrow, cm=True, ql=1: D.icpt_pi(st, pa, pc, j, B.parse_sq(p), B.DIR_NAMES.index(arrow) if isinstance(arrow, str) else arrow,
                                                         cm, ql, occ, passer)
    assert pi(s, 0, 'J10', 'NW') == 0.0                          # the on-ball defender: no arrow line of his meets the pass
    assert pi(s, 0, 'H10', 'N') == 0.0                           # on the pass's line but next to the passer: never
    jump = pi(s, 1, 'D8', 'NW')
    assert jump == pytest.approx(0.7)                            # X2 steps along his arrow to where it meets the pass
    assert pi(s.with_(tok_x=1), 1, 'D8', 'NW') == 0.0            # the movement and the Intercept are two tokens
    assert pi(s, 1, 'D8', 'E') == 0.0 and pi(s, 1, 'D8', 'S') == 0.0      # an arrow off the lane
    through = pi(s.with_(tok_x=1), 1, 'F10', 'S')                # standing on the line, away from the passer: one token is enough
    assert through == pytest.approx(jump)
    assert pi(s, 1, 'D8', 'NW', cm=False, ql=0) == 0.0           # no movement left to him
    # a Quick Step gets him there off balance (D-185): rolled 2 lower than after a Move
    assert pi(s, 1, 'D8', 'NW', cm=False, ql=1) < jump
    blocked = set(occ) | {B.parse_sq('D9'), B.parse_sq('C9')}    # a body on the square where his line meets the pass
    assert D.icpt_pi(s, pa, pc, 1, B.parse_sq('D8'), s.arrows[1], True, 1, blocked | {B.add(B.parse_sq('D8'), B.DIRS[s.arrows[1]])}, passer) == 0.0


def test_the_reading_equals_the_rules_on_random_positions():
    sys.path.insert(0, os.path.join(ROOT, 'tools'))
    import js_equivalence as E
    keep = dict(E._ZONE), dict(E._FIBA), dict(E._CONTROL)
    E._ZONE['v'] = 'on'
    E._CONTROL['size'] = 'app'
    E._FIBA.update(three_seconds='on', closely_guarded='on', fiba_fouled_shot='on', soft_contest='on', fiba_steal_foul='on', off_balance='on',
                   position_contest='on')
    try:
        rng = random.Random(18)
        seen = jumps = 0
        while seen < 400:
            s, _ = E.random_state(rng)
            if s.stage != 'play' or s.pending or not all(B.on_board(q) for q in s.o + s.x):
                continue
            for i in range(5):
                want = None if i == s.ball else rules_pass(s, i)
                if want is None:
                    continue
                seen += 1
                jumps += want < 1
                assert D._lane_p_calc(s, i, s.o[i]) == pytest.approx(want, abs=1e-9), (i, s)
        assert jumps > 40                                         # the sample holds passes that can be taken
    finally:
        E._ZONE.clear(), E._ZONE.update(keep[0]), E._FIBA.clear(), E._FIBA.update(keep[1]), E._CONTROL.update(keep[2])


def test_both_engines_agree_on_the_pass_chance():
    out = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'js_equivalence.py'), '--soft', '--fiba', '--off-balance', 'on',
                          '--position-contest', 'on', '--zone', '--n', '40', '--search', '2'], cwd=ROOT, capture_output=True, text=True, timeout=900).stdout
    rep = json.loads(out[out.index('{'):])
    assert rep['mismatches'] == 0 and rep['states'] == 40


def test_the_proof_is_kept_beside_the_run():
    rep = json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step18s', 'pass_proof.json')))
    assert rep['passes'] >= 6000 and rep['the_new_reading_equal_to_the_rules'] == rep['passes']
    assert rep['the_old_reading_equal_to_the_rules'] < 0.6 * rep['passes']


# ---- part 2: the defence's strength, phase by phase ---------------------------------------------------------------------

import shutil

needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


@pytest.fixture(scope='module')
def cov():
    from playmaker_engine import agent as AG
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    yield AG.coverage
    NodeEngine.uninstall()
    eng.p.kill()


@needs_node
def test_strength_fragility_and_broken_are_read_off_the_map(cov):
    his = cov(board())
    helped = cov(board(['J10', 'D8', 'O8', 'H5', 'J5'], ['NW', 'NW', 'N', 'N', 'N']))
    # strength: the most the offence can force by the next phase's start, the defence's best answers counted
    assert his['strength'] == max(his['left_worth'], his['dribble']['worth'] if his['dribble'] else 0)
    assert helped['strength'] < his['strength']                  # help in the lane is the stronger defence (lower)
    # fragility: the separate attackers who hold a way worth at least what is left
    assert his['fragility'] == len(his['ways']) and 1 <= helped['fragility'] <= his['fragility'] <= 5
    for c in (his, helped):
        best = {}
        for a, squares in enumerate(c['squares']):
            best[a] = max((v['worth'] for v in squares.values()), default=-99)
        assert c['ways'] == [a for a in range(5) if best[a] > 0 and best[a] >= c['left']['worth'] - 1e-6]
    # broken: a shot now worth more than playing on (the phase table); the point guard on plain wood has no shot
    assert his['shot_now'] is None and his['broken'] is False and 24 < his['carry_on'] < 30


@needs_node
def test_broken_is_a_shot_now_worth_more_than_playing_on(cov):
    from playmaker_engine import agent as AG
    lay = board(o=['I3'] + O_[1:], x=['J10', 'D8', 'O8', 'B4', 'P2'])              # the point guard alone at the rim
    r = AG.coverage(lay, only='break')
    assert r['broken'] and r['shot']['kind'] in ('layup', 'dunk') and r['shot']['open'] and r['shot']['worth'] > r['carry_on']
    three = AG.coverage(board().with_(ball=4), only='break')                       # the centre's three, his man on him
    assert three['shot']['kind'] == 'three' and not three['broken'] and three['shot']['worth'] < three['carry_on']
    assert AG.coverage(board().with_(side='X'), only='break')['shot'] is None      # the defence to act: no shot is going up


@needs_node
def test_every_finished_phase_gets_a_line_and_the_possession_gets_one(cov):
    from playmaker_engine import agent as AG
    from playmaker_web.game import Game
    from playmaker_web.view import coverage_json
    keep = AG.SCALE['value']
    AG.SCALE['value'] = 0.2
    try:
        g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], seed=3, full=True, level='pro', match_format='digital', place=True, per_side=4,
                 ai=dict(A='rookie', B='rookie'))
        n = 0
        while g.state.stage != 'over' and n < 300:
            n += 1
            g._run_ai()
        sc = g.phase_scores()
    finally:
        AG.SCALE['value'] = keep
    assert sc['over'] and sc['possession'] == 1 and sc['lines']
    assert [ln['phase'] for ln in sc['lines']] == list(range(1, len(sc['lines']) + 1))
    for ln in sc['lines']:
        assert ln['text'].startswith(('Defence weakened from', 'Defence strengthened from', 'Defence held at', 'The defence was broken', 'The shot went up',
                                      'The possession ended without a shot')), ln
        assert plain.check(ln['text']) == []
    assert sc['verdict'].startswith(('A good possession', 'A weak possession', 'A wasted possession')) and plain.check(sc['verdict']) == []
    assert coverage_json(g, None)['scores'] == sc                 # the view carries them once the possession is over
    table = Game(mode='hotseat', teams=['Five Out', 'High-Low'], seed=3, full=True, level='pro')
    assert table.phase_scores() is None                           # the app only


def test_the_app_shows_the_phase_lines_under_the_board():
    js = open(os.path.join(ROOT, 'playmaker_web', 'static', 'app.js'), encoding='utf-8').read()
    assert "id: 'covScores'" in js and '`Phase ${ln.phase}: ${ln.text}`' in js and 'sc.verdict' in js
