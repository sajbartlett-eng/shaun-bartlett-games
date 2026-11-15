"""Step 18p (Shaun, 15 Nov 2026), D-196. Part 2: the zone (D-167) is on by default in the app and runs on the fast
engine; the setup as it was keeps its time. The reading's fix is not in this file: stage 1 stopped with its reason
(docs/reports/STEP18P_REPORT.md)."""
import os
import time

from playmaker_engine import agent as AG
from playmaker_engine import board as B
from playmaker_engine import jsbridge
from playmaker_engine import rules_config as RC
from playmaker_engine.decide import CONFIG
from playmaker_engine.scenarios import game_state
from playmaker_web.game import Game

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KW = dict(mode='hotseat', teams=['Five Out', 'High-Low'], seed=3, full=True, level='pro')


def test_the_zone_is_on_by_default_in_the_app_and_only_there():
    zone = lambda g: g.state.ctx.rules.zone
    assert zone(Game(match_format='digital', **KW)) == 'on'
    assert zone(Game(match_format='digital', zone='off', **KW)) == 'off'            # ?zone=0
    assert zone(Game(match_format='digital', zone='0', **KW)) == 'off'
    assert zone(Game(**KW)) == 'off'                                                # nothing for the table
    assert RC.Rules().zone == 'off'


def test_the_fast_engine_plays_a_game_under_the_zone():
    """The bridge used to send every game under the zone to the slow engine. The two engines are checked equal under
    the zone by tools/js_equivalence.py --zone."""
    assert jsbridge.ported(RC.with_rules(digital=True, zone='on'))
    assert jsbridge.ported(RC.with_rules(digital=True))
    assert not jsbridge.ported(RC.with_rules(digital=True, late_closeout=True))     # a rule the fast engine doesn't play still goes to the slow one


def test_the_setup_as_it_was_keeps_its_time():
    """It read the clock only between one defender and the next and ran 4 to 6 seconds over. Now it reads it before
    every reading, so it is over by at most the readings it has begun."""
    assert not AG.setup_search()
    rules = RC.with_rules(digital=True)
    make = lambda o, x, a, b: game_state('Five Out', 'High-Low', list(o), list(x), list(a), ball=b, rules=rules)
    one = time.time()
    AG.Read(make(['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'], ['N', 'NW', 'NE', 'N', 'N'], 0)).leaf()
    one = time.time() - one                                                        # what one reading costs on this machine
    for budget in (0.05, 0.4):
        t0 = time.time()
        r = AG.propose_offence(make, 5, budget=budget, level='starter')
        t1 = time.time()
        d = AG.propose_defence(make, r['squares'], r['ball'], 6, budget=budget, level='starter')
        t2 = time.time()
        assert t1 - t0 < budget + 6 * one + 0.2, (budget, t1 - t0, one)
        assert t2 - t1 < budget + 4 * one + 0.2, (budget, t2 - t1, one)
        assert len({tuple(q) for q in r['squares']} | {tuple(q) for q in d['squares']}) == 10


def test_the_setup_search_stays_off():
    assert CONFIG['setup']['search'] is False and CONFIG['eval'].get('learned') is not True


def test_d196_is_recorded_and_heads_the_principles():
    p = open(os.path.join(ROOT, 'docs', 'reference', 'SHAUN_PRINCIPLES.md')).read()
    assert p.index("Shaun's rule for Fable (D-196") < p.index('The standing principles')
    assert 'Trust the design pillars more than the computer simulation data' in p
    assert '**D-196.' in open(os.path.join(ROOT, 'DECISIONS.md')).read()
    assert os.path.exists(os.path.join(ROOT, 'docs', 'plans', 'COMPUTER_FIX_PLAN.md'))
