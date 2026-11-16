"""Step 18s, stop one (Shaun, 16 Nov 2026), D-199: the coverage map. For every attacker and square: what the look is
worth open (value), the chance he has the ball there next phase (reach), what the defence takes off it (influence) and
what is left (weakness); who covers it and who is next; the defence's best answers inside the tokens it has; and one
line of words. Built in the fast engine from the game's own rules. Nothing in the computer's play reads it yet. Design
checks 1 to 6 of the blueprint (docs/reference/COVERAGE_MAP_BLUEPRINT.md) on Shaun's board of 15 November."""
import os
import shutil

import pytest

from playmaker_engine import agent as AG
from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import legal_actions
from playmaker_engine.decide import _lane_p
from playmaker_engine.resolve import ChanceNode, apply
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import score
from playmaker_web.game import Game
from playmaker_web.view import coverage_json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = RC.with_rules(digital=True, zone='on')                    # the app's rules
O_ = ['I11', 'C9', 'O9', 'A3', 'Q3']                              # Shaun's board of 15 November
X_ = ['J10', 'D8', 'O8', 'B4', 'P2']
A_ = ['NW', 'NW', 'N', 'SW', 'NE']
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')
_TEAMS = []


def teams():
    """Shaun's cards: the coherent Senior Pro deal whose 4 and 5 are the post scorers (seed 3351)."""
    if not _TEAMS:
        from playmaker_engine import levels as LV, rosters as R
        from playmaker_engine.cards import register_cards
        d = R.deal('senior', 'pro', True, seed=3351)
        _TEAMS.extend(register_cards(f'shaun 18s {w}', LV.team(d['rosters'][k], 'senior', None)) for k, w in enumerate('OX'))
    return _TEAMS


def board(x=None, arrows=None, o=None, ball=0, **kw):
    off, dfn = teams()
    s = game_state(off, dfn, list(o or O_), list(x or X_), list(arrows or A_), ball=ball, rules=RULES, check=False, team_fouls=2, quarter_left=8)
    s.ctx.levels_key = ('senior', 'pro')
    return s.with_(**kw) if kw else s


def with_x(j, sq, arrow, **kw):
    return board(X_[:j] + [sq] + X_[j + 1:], A_[:j] + [arrow] + A_[j + 1:], **kw)


@pytest.fixture(scope='module')
def cov():
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    yield AG.coverage
    NodeEngine.uninstall()
    eng.p.kill()


def best_of(c, a):
    return max(c['squares'][a].values(), key=lambda v: v['worth'])


def shot_now(st, kind='three'):
    """What a shot going up now is worth by the rules' own resolution: the expected score over the dice."""
    st = st.with_(side='O', turn_n=0)
    a = next(a for a in legal_actions(st) if a.kind == 'shot' and a.shot == kind)

    def ev(n):
        if isinstance(n, ChanceNode):
            return sum(float(p) * ev(sub) for p, _, sub in n.outcomes)
        return float(score(n).total)
    return ev(apply(st, a))


def pass_arrives(st, target):
    """The chance a pass arrives, by trying every answer the rules give the defence once it is in the air."""
    st = st.with_(side='O', turn_n=0)
    n = apply(st, next(a for a in legal_actions(st) if a.kind == 'pass' and a.target == target))
    worst = 1.0
    for a in legal_actions(n) if not isinstance(n, ChanceNode) and n.pending else []:
        if a.kind == 'intercept':
            n2 = apply(n, a)
        elif a.kind in ('move', 'qs', 'sprint'):
            m = apply(n, a)
            ic = [] if isinstance(m, ChanceNode) or not m.pending else [b for b in legal_actions(m) if b.kind == 'intercept' and b.piece == a.piece]
            if not ic:
                continue
            n2 = apply(m, ic[0])
        else:
            continue
        if isinstance(n2, ChanceNode):
            worst = min(worst, float(next(q for q, lab, sub in n2.outcomes if lab == 'success')))
    return worst


# ---- the decisions, and where the map lives ---------------------------------------------------------------------------

def test_the_decisions_are_recorded():
    text = open(os.path.join(ROOT, 'DECISIONS.md'), encoding='utf-8').read()
    assert 'D-199' in text and 'D-200' in text
    assert os.path.exists(os.path.join(ROOT, 'docs', 'reference', 'COVERAGE_MAP_BLUEPRINT.md'))


def test_there_is_no_coach_view_without_the_fast_engine():
    """The coach's map (every square, the words) is the fast engine's. Since stop two the search reads the map's lean
    form, which both engines hold (tests/test_strength_18s.py)."""
    assert AG.JS.get('coverage') is None
    assert AG.coverage(board()) is None


# ---- the four numbers --------------------------------------------------------------------------------------------------

@needs_node
def test_every_square_carries_value_reach_influence_and_weakness(cov):
    s = board()
    c = cov(s, 0)
    assert len(c['squares']) == 5 and all(c['squares'])
    cards = s.ctx.off
    for a, squares in enumerate(c['squares']):
        for name, v in squares.items():
            assert 0 < v['reach'] <= 1 and 0 <= v['weakness'] <= v['value'], (a, name, v)
            assert v['influence'] == v['value'] - v['weakness'], (a, name, v)
            assert abs(v['worth'] - (v['reach'] * v['weakness'] - (1 - v['reach']) * 5)) < 0.51       # a lost ball is -5 (D-198)
            assert (v['cover'] == -1) == (v['influence'] == 0) and (v['cover'] == -1 or v['next'] != v['cover'])
    # value comes from the cards and nothing else: an open three is 3 times the rating
    assert 'I11' not in c['squares'][0]                         # the ball handler stands on plain wood: no shot there
    for a in range(1, 5):
        v = c['squares'][a][O_[a]]
        assert v['shot'] == 'three' and v['value'] == 3 * cards[a].shot('three') and not v['rushed']
    assert 'I2' not in c['squares'][0]                          # no shot from the rim square (D-198)


@needs_node
def test_the_pass_chance_is_the_rules_own(cov):
    """A pass can be intercepted only by the rules' own answers. At stop one the reading's pass chance (decide._lane_p)
    let the on-ball defender take every pass on this board; stop two mended it (tests/test_strength_18s.py)."""
    for arrow in ('NW', 'E'):
        s = with_x(1, 'D8', arrow)
        c = cov(s, 0)
        assert c['passes'][0] is None and c['passes'][3] is None      # the ball handler; O4 is out of his range
        for a in (1, 2, 4):
            assert abs(c['passes'][a] - pass_arrives(s, a)) < 0.002
    assert cov(board(), 0)['passes'][1] < 0.5 and cov(with_x(1, 'D8', 'E'), 0)['passes'][1] == 1
    s = board()
    assert [_lane_p(s, a, s.o[a]) for a in (2, 4)] == [1.0, 1.0]  # stop two: the reading's own is now the rules' too (it read 0.25)


# ---- the design checks -------------------------------------------------------------------------------------------------

@needs_node
def test_check_1_the_clear_lane_is_a_large_weakness_and_the_defences_best_answer_makes_it_smaller(cov):
    c = cov(board())
    top = c['best']
    assert (top['o'], top['shot'], top['cover']) == (0, 'layup', -1) and top['sq'] in ('I3', 'H3', 'J3', 'H2', 'J2')
    assert top['worth'] >= 30                                    # the point guard's open layup, nobody able to contest it
    assert 1 <= len(c['answers']) <= 3 and c['left_worth'] <= top['worth'] - 8
    assert {a['x'] for a in c['answers']} & {3, 4}               # a big comes into the lane
    leaves = [a['leaves'] for a in c['answers']]
    assert leaves == sorted(leaves, reverse=True)                # each answer leaves less than the one before
    # the same placement read from the start reads the same: the map has no memory
    again = cov(board(c['after']['x'], c['after']['arrows']), 0)
    assert again['left_worth'] == c['left_worth']
    assert 'Nobody can get there to contest it' in c['words'] and "The defence's best answer" in c['words']


@needs_node
def test_checks_2_and_3_leaving_the_non_shooter_costs_less_than_leaving_the_sharpshooter(cov):
    s = board()
    cards = s.ctx.off
    three = [3 * c.shot('three') for c in cards]
    non, sharp = 4, 1                                            # the Post Scorer Centre, the Sharpshooter
    assert three[non] == min(three) and three[sharp] == max(three) and three[sharp] - three[non] >= 6
    stay = cov(s, 0)
    off_non = cov(with_x(non, 'I4', 'N'), 0)                     # his defender in the lane
    off_sharp = cov(with_x(sharp, 'I4', 'N'), 0)
    assert stay['squares'][non]['Q3']['value'] < stay['squares'][sharp]['C9']['value']
    assert off_non['left_worth'] <= stay['left_worth'] - 6       # helping off the non-shooter pays
    assert off_sharp['left_worth'] >= off_non['left_worth'] + 2  # helping off the sharpshooter pays less
    assert off_sharp['squares'][sharp]['C9']['weakness'] > stay['squares'][sharp]['C9']['weakness']


@needs_node
def test_check_4_arrows_matter(cov):
    rich = lambda c: sum(1 for v in c['squares'][0].values() if v['worth'] >= 30)
    his, across, away = cov(board(), 0), cov(with_x(0, 'J10', 'W'), 0), cov(with_x(0, 'J10', 'E'), 0)
    assert len(across['squares'][0]) < len(his['squares'][0]) <= len(away['squares'][0])      # the arrow across his way bars squares
    assert rich(across) < rich(his) == rich(away)
    assert best_of(across, 0)['rushed'] and not best_of(his, 0)['rushed']                    # and what is left he must rush
    # an arrow down a passing lane lets the defender jump it; an arrow off the lane does not
    assert his['passes'][1] < 0.5 and cov(with_x(1, 'D8', 'S'), 0)['passes'][1] == 1


def test_checks_4_and_5_by_the_rules_a_shot_going_up_with_no_token_left():
    """Square in front beats beside, and beside beats behind; and in front, the arrow on him beats the arrow off him.
    With a token left the reaction lets a fresh defender next to the shooter get square, so the map reads all three
    alike at a phase's start (stated in the report)."""
    c9 = B.parse_sq('C9')
    worth = {}
    for name, (dx, dy) in (('in front', (0, -1)), ('beside', (1, 0)), ('behind', (0, 1))):
        q = (c9[0] + dx, c9[1] + dy)
        worth[name] = shot_now(with_x(1, B.sq(q), B.dir_between(q, c9), ball=1, tok_x=0))
    assert worth['in front'] + 3 < worth['beside'] < worth['behind']
    on = B.dir_between(B.parse_sq('C8'), c9)
    assert shot_now(with_x(1, 'C8', on, ball=1, tok_x=0)) + 3 < shot_now(with_x(1, 'C8', (on + 4) % 8, ball=1, tok_x=0))


@needs_node
def test_check_5_at_a_phases_start_the_reaction_gets_a_fresh_defender_square(cov):
    c9 = B.parse_sq('C9')
    seen = set()
    for dx, dy in ((0, -1), (1, 0), (0, 1)):
        q = (c9[0] + dx, c9[1] + dy)
        seen.add(cov(with_x(1, B.sq(q), B.dir_between(q, c9), ball=1), 0)['squares'][1]['C9']['weakness'])
    assert len(seen) == 1


@needs_node
def test_check_6_a_body_on_the_helpers_way_leaves_more(cov):
    """The defence with one token has one answer. With O4 standing on the helper's way that answer is gone and more is
    left. The Screen action itself stops no helper on this board (it bars only a diagonal step): in the report."""
    off = cov(board(o=O_[:3] + ['C5', 'Q3'], tok_x=1))
    on = cov(board(o=O_[:3] + ['C4', 'Q3'], tok_x=1))
    assert [a['x'] for a in off['answers']] == [3] and len(on['answers']) <= 1
    assert on['left_worth'] >= off['left_worth'] + 1
    assert [a['x'] for a in on['answers']] != [3]


# ---- the answers stay inside the rules ---------------------------------------------------------------------------------

@needs_node
def test_the_answers_stay_inside_the_defences_tokens(cov):
    for tok in (0, 1, 2):
        c = cov(board(tok_x=tok))
        assert len(c['answers']) <= tok and c['after']['tokens_left'] == tok - len(c['answers'])
    assert 'no token left' in cov(board(tok_x=0))['words']
    assert cov(board(tok_x=0))['left_worth'] == cov(board(tok_x=0))['best']['worth']


@needs_node
def test_the_last_phase_has_no_next_phase(cov):
    c = cov(board(clock=2))
    assert c['best'] is None and 'last phase' in c['words']


# ---- the coach's view --------------------------------------------------------------------------------------------------

@needs_node
def test_the_view_is_kept_for_each_phase_and_only_in_the_app(cov):
    kw = dict(mode='hotseat', teams=['Five Out', 'High-Low'], seed=3, full=True, level='pro')
    table = Game(**kw)
    assert table.coverage_snapshot() is None and coverage_json(table, None) == {}
    g = Game(match_format='digital', place=True, **kw)
    assert g.placing and g.coverage_snapshot() is None           # nothing while the pieces are being placed
    g.place(g.tokens['both'], dict(preview=True))
    assert not g.placing
    v = coverage_json(g, None)
    assert v['phase'] == g.state.phase and v['possession'] == g.possession and v['change'] is None and v['words']
    assert len(v['attackers']) == 5 and v['all'] and len(v['passes']) == 5
    row = v['all'][0]
    assert {'sq', 'x', 'y', 'o', 'worth', 'value', 'reach', 'weakness', 'shot', 'cover', 'next', 'rushed'} <= set(row)
    assert B.sq((row['x'], row['y'])) == row['sq']
    by_sq = {}
    for layer in v['attackers']:
        for r in layer:
            by_sq[r['sq']] = max(by_sq.get(r['sq'], -99), r['worth'])
    assert all(by_sq[r['sq']] == r['worth'] for r in v['all'])   # "all five" is the best of the five on each square
    assert g.coverage_snapshot() is g.coverage_snapshot()        # the phase's snapshot is kept, not read again


def test_the_app_has_the_toggle_and_the_static_site_wires_the_map():
    js = open(os.path.join(ROOT, 'playmaker_web', 'static', 'app.js'), encoding='utf-8').read()
    assert "'Coverage: shown' : 'Coverage: hidden'" in js and "localStorage.getItem('pm_covmap') === '1'" in js      # hidden unless asked for
    assert "/api/covmap" in js and "/api/covmap" in open(os.path.join(ROOT, 'playmaker_web', 'api.py'), encoding='utf-8').read()
    assert "_AG.JS['coverage'] = js.PMEngine.coverageJSON" in open(os.path.join(ROOT, 'playmaker_web', 'static', 'pyodide-adapter.js'), encoding='utf-8').read()


# ---- the reading: a shooting foul carries its +5 (D-198) ---------------------------------------------------------------

def test_the_reading_prices_a_shooting_foul_with_its_plus_5():
    src = open(os.path.join(ROOT, 'playmaker_engine', 'decide.py'), encoding='utf-8').read()
    assert 'ft += RC.STEAL_FOUL_BONUS' in src
    js = open(os.path.join(ROOT, 'playmaker_web', 'static', 'engine.js'), encoding='utf-8').read()
    assert 'pf * (ft + (ctx.ppo ? 5 : 0))' in js
