"""Step 28 (Shaun, 19 Nov 2026): the contest costs an action, one reading everywhere, and the defender's stance."""
import os
import shutil
import sys

import pytest

from playmaker_engine import board as B
from playmaker_engine import decide as D
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import legal_actions
from playmaker_engine.resolve import apply

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')

# Shaun's case (D-261): O1 shoots a three from C9; X1 on H11 needs two movements to get next to him (a Quick Step,
# then a Move that changes direction); everyone else far off
SHOOT_O = ['C9', 'O9', 'Q3', 'K12', 'I6']
SHOOT_X = ['H11', 'N8', 'P4', 'L11', 'J5']


def state(o, x, ar, ball=0, off='High-Low', dfn='Run and Gun', rules=None, **kw):
    from playmaker_engine.scenarios import game_state
    import step_18o as O
    s = game_state(off, dfn, list(o), list(x), list(ar), ball=ball, rules=RC.with_rules(digital=True, zone='on', **(rules or {})),
                   check=False, **O.T.FOULS)
    s.ctx.levels_key = ('senior', 'pro')
    return s.with_(**kw) if kw else s


def shoot(s, i=0, t=None):
    a = next(a for a in legal_actions(s) if a.kind == 'shot' and a.piece == i and (t is None or a.shot == t))
    return apply(s.with_(side='O', turn_n=0), a)


def _two_movements(r, d):
    """Every way defender d gets next to the shooter with two movements, as (first, second)."""
    out = []
    for a in legal_actions(r):
        if a.piece == d and a.kind in ('move', 'qs', 'sprint'):
            r2 = apply(r, a)
            if getattr(r2, 'stage', None) != 'reaction':
                continue
            for b in legal_actions(r2):
                if b.piece == d and b.kind in ('move', 'qs', 'sprint') and B.adjacent(b.dest, r.o[r.ball]):
                    out.append((a, b))
    return out


# ---- item 1: the contest is a defence action ---------------------------------------------------------------------------

def test_two_movements_leave_no_contest():
    s = state(SHOOT_O, SHOOT_X, [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    assert RC.contest_costs(s.ctx.rules)
    r = shoot(s)
    assert r.stage == 'reaction' and r.shot == 'three'
    one = [a for a in legal_actions(r) if a.piece == 0 and a.kind in ('move', 'qs', 'sprint') and B.adjacent(a.dest, r.o[0])]
    assert not one                                               # no single movement gets X1 next to him
    ways = _two_movements(r, 0)
    assert ways                                                  # two do
    a, b = ways[0]
    end = apply(apply(r, a), b)                                  # his two actions are spent: the reply is over
    assert end.stage == 'over' and end.result.contest == 0 and end.result.contester == -1
    # before D-261 the same two movements ended in a free hand up
    old = state(SHOOT_O, SHOOT_X, [5, 0, 0, 0, 0], rules=dict(contest_costs='off')).with_(side='O', turn_n=0)
    ro = shoot(old)
    eo = apply(apply(ro, a), b)
    assert eo.stage == 'over' and eo.result.contest > 0


def test_a_teammate_with_one_movement_can_still_contest():
    s = state(SHOOT_O, ['H11', 'E7', 'P4', 'L11', 'J5'], [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    r = shoot(s)
    near = [a for a in legal_actions(r) if a.piece == 1 and a.kind == 'move' and B.adjacent(a.dest, r.o[0])]
    assert near
    r2 = apply(r, near[0])
    cons = [a for a in legal_actions(r2) if a.kind == 'contest' and a.piece == 1]
    assert cons                                                  # one movement and the Contest: the reply's two actions
    end = apply(r2, cons[0])
    assert end.stage == 'over' and end.result.contester == 1 and end.result.contest >= RC.CONTEST_FLOOR


@pytest.mark.parametrize('jump', [True, False])
def test_the_contest_costs_an_action_jump_and_inside_normal_and_hard(jump):
    if jump:      # O1 shoots a three from C9, X1 next to him on D10 (in front, square), X2 beside him on C8
        s = state(['C9', 'O9', 'Q3', 'K12', 'I6'], ['D10', 'B9', 'P4', 'L11', 'J5'], [B.dir_between(B.parse_sq('D10'), B.parse_sq('C9')), 0, 0, 0, 0])
    else:         # O5 lays it up from H3, X5 beside him on G3 with his arrow off, X1 behind on H4
        s = state(['N12', 'O9', 'Q3', 'K12', 'H3'], ['H4', 'D8', 'P4', 'L11', 'G3'], [0, 0, 0, 0, 0], ball=4)
    s = s.with_(side='O', turn_n=0)
    r = shoot(s, s.ball, 'three' if jump else 'layup')
    cons = [a for a in legal_actions(r) if a.kind == 'contest']
    assert cons and all(a.piece >= 0 for a in cons)
    hard = [a for a in cons if a.shot == 'hard']
    assert (not hard) if jump else hard                          # the block only inside
    normal = [a for a in cons if a.shot != 'hard']
    for a in normal + hard:
        after = apply(r, a)
        node = after if getattr(after, 'stage', None) else after.outcomes[-1][2]
        if hasattr(after, 'outcomes'):                           # a hard Contest's foul roll: the no-foul branch
            node = [o for o in after.outcomes if o[1] == 'no foul'][-1][2]
            while hasattr(node, 'outcomes'):
                node = [o for o in node.outcomes if o[1] == 'no foul'][-1][2]
        assert node.stage == 'over' and node.result.contester == a.piece
        assert node.tok_x == r.tok_x - 1                          # it took a token: one of the reply's actions
    # nobody presses Contest: the shot goes up open
    open_ = apply(r, next(a for a in legal_actions(r) if a.kind == 'end_turn'))
    assert open_.stage == 'over' and open_.result.contest == 0


def test_after_one_movement_and_a_contest_the_reply_is_spent():
    s = state(SHOOT_O, ['H11', 'E7', 'P4', 'L11', 'J5'], [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    r = shoot(s)
    near = next(a for a in legal_actions(r) if a.piece == 1 and a.kind == 'move' and B.adjacent(a.dest, r.o[0]))
    r2 = apply(r, near)
    assert r2.stage == 'reaction' and r2.turn_n == 1
    assert not [a for a in legal_actions(r2) if a.kind in ('move', 'qs', 'sprint') and a.piece == 1 and False]
    # a second movement ends the reply: no Contest after it
    mv = next(a for a in legal_actions(r2) if a.kind in ('move', 'qs', 'sprint'))
    end = apply(r2, mv)
    assert end.stage == 'over' and end.result.contest == 0


@needs_node
def test_the_map_reads_shauns_shot_as_open(js28):
    from playmaker_engine import agent as AG
    s = state(SHOOT_O, SHOOT_X, [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    sq = AG.coverage(s)['squares'][0]
    lk = sq.get('C9')
    assert lk and lk['cover'] == -1 and lk['worth'] == pytest.approx(lk['value'])      # nobody can contest it in time
    t = state(SHOOT_O, ['H11', 'E7', 'P4', 'L11', 'J5'], [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    lk2 = AG.coverage(t)['squares'][0].get('C9')
    assert lk2 and lk2['cover'] == 1 and lk2['worth'] < lk2['value']                   # a teammate one movement away contests


@pytest.fixture
def js28():
    from playmaker_engine import jsbridge
    eng = jsbridge.NodeEngine().install()
    yield eng
    eng.close()
