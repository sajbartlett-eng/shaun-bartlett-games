"""Step 3i behaviours under the live rules (single arrow, hold-until-move screens, zone drives, move-then-intercept and
the minus5_lose_phase turnover cost). test_breaking.py keeps the step 3i positions as the record, and 31 of its 39 tests
pass unchanged under the live rules too (PM_LIVE_RULES=1). These are the other 8, rebuilt where the live rules changed
what a position shows: the post-entry chain (X1 now intercepts through his square on the swing lanes, so he stands
off them, facing the baseline), the rotation (X2 faces up the wing), and the goal score's clock-aware pick-off."""
import pytest
from conftest import P

from playmaker_engine import board as B
from playmaker_engine import computer as C
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.advantage import advantages, describe
from playmaker_engine.capacity import capacity
from playmaker_engine.cards import TEAMS
from playmaker_engine.planner import goals
from playmaker_engine.resolve import apply, ChanceNode, force
from playmaker_engine.scenarios import game_state
from playmaker_engine.state import Context, GameState

LIVE = RC.Rules()
TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']


def board(off, dfn, o, x, arrows, ball=0, **kw):
    return game_state(off, dfn, o, x, arrows, ball=ball, rules=LIVE, check=False).with_(**kw)


def lineup(off_cards, dfn_cards, o, x, arrows, ball=0, **kw):
    ctx = Context(off_cards, dfn_cards, LIVE, title='live test', kind='GAME', off_team='test', def_team='test')
    return GameState(ctx=ctx, o=tuple(P(q) for q in o), x=tuple(P(q) for q in x),
                     arrows=tuple(B.DIR_NAMES.index(a) for a in arrows), ball=ball, **kw)


def settle(node, prefer=('success', 'kept', 'no foul', 'holds')):
    while isinstance(node, ChanceNode):
        labels = [lab for _, lab, _ in node.outcomes]
        node = force(node, next((l for l in prefer if l in labels), labels[0]))
    return node


def passive_defence(o, s, steps=80):
    """The offence computer against a defence that never moves, every roll the offence's way."""
    for _ in range(steps):
        if s.stage == 'over':
            break
        if s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play'):
            a = o.choose(s)
        else:
            acts = legal_actions(s)
            a = next((x for x in acts if x.kind in ('pause', 'end_turn')), None) or \
                next((x for x in acts if x.kind == 'contest' and x.piece < 0), acts[0])
        s = settle(apply(s, a))
    return s


def test_these_are_the_live_rules():
    assert LIVE.intercept_rule == 'move_then_intercept' and LIVE.turnover_cost == 'minus5_lose_phase'
    assert LIVE.arrow_mode == 'single' and LIVE == RC.DEFAULT_RULES


# ---- the goal chain on the post position ----------------------------------------------------------------
# The step 3i post position (O5, ▲ post, on the right block against a ▼ post X5 fronting him), with O2 a square
# higher and X1 facing the baseline: X1 can't jump either swing lane from where he stands, so the chain is the
# full one: both receivers open their lanes, two swings, the seal, the entry.

BB = TEAMS['Bucket Brigade']
POST_OFF = [TEAMS['Iron Wall'][0], TEAMS['Lockdown'][0], TEAMS['Iron Wall'][3], TEAMS['Twin Towers'][3], TEAMS['High-Low'][4]]
POST_DFN = [BB[0], BB[1], BB[4], BB[3], BB[2]]
POST_O = ['O8', 'H8', 'C5', 'B3', 'K3']
POST_O = ['O8', 'H9', 'C5', 'B3', 'K3']
POST_X = ['M8', 'G6', 'E7', 'A2', 'L4']
POST_ARROWS = ['S', 'E', 'E', 'NE', 'NE']
CHAIN = ['O2 moved to open the lane', 'O3 moved to open the lane', 'swung the ball to O2', 'swung the ball to O3', 'O5 sealed X5', 'entry to O5']


def post_position(**kw):
    return lineup(POST_OFF, POST_DFN, POST_O, POST_X, POST_ARROWS, **kw)


def test_all_star_sets_the_post_goal_and_chains_it_backwards():
    s = post_position()
    assert not C.pass_risk(s, 0, 4)['clean'] and all(not C.pass_risk(s, 0, r)['clean'] for r in (1, 2))
    g = next(g for g in goals(s, 'allstar') if g['entry']['id'] == 'A1')
    assert g is goals(s, 'allstar')[0] and g['words'] == 'O5 in the post on X5'
    assert [t['words'] for t in g['todo']] == CHAIN


def test_rookie_tries_the_goal_directly_and_starter_one_condition_deep():
    s = post_position()
    rk = next(g for g in goals(s, 'rookie') if g['entry']['id'] == 'A1')
    st = next(g for g in goals(s, 'starter') if g['entry']['id'] == 'A1')
    al = next(g for g in goals(s, 'allstar') if g['entry']['id'] == 'A1')
    assert [t['words'] for t in rk['todo']] == ['entry to O5']
    assert [t['words'] for t in st['todo']] == ['O5 sealed X5', 'entry to O5']
    assert [t['words'] for t in al['todo']] == CHAIN


def _events(o):
    return [n for n in o.notes if n['event'] in ('goal', 'goal_step', 'goal_reassess', 'goal_finish')]


def test_the_chain_runs_and_the_log_matches():
    """The post goal is set and its first step played. Against a defence that stands still each move of the
    offence's opens more (here O5's move to open his lane makes a cut cheaper), so goals change, each with
    its reason; and every goal that finishes says exactly the steps the log shows for it."""
    o = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    passive_defence(o, post_position(), steps=40)
    ev = _events(o)
    assert ev[0]['text'] == 'Goal: O5 in the post on X5 (Post entry, 6 steps)'
    assert ev[1]['event'] == 'goal_step' and ev[1]['text'] == CHAIN[0]
    fins = 0
    for k, e in enumerate(ev):
        if e['event'] != 'goal_finish' or 'a shot went up first' in e['text']:
            continue
        start = max(i for i in range(k) if ev[i]['event'] == 'goal')
        steps = [x['text'].lower() for x in ev[start:k] if x['event'] == 'goal_step']
        said = e['text'].split('. ', 1)[1].rstrip('.').lower().split(', ')
        assert said == steps, (said, steps)
        fins += 1
    assert fins >= 1


def test_no_reassessment_on_noise_the_goal_persists():
    """A goal only changes after the offence's own progress (a step played) or a broken condition, never twice
    on the same board, and always with a logged reason."""
    o = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    s = post_position()
    n = 0
    for _ in range(60):
        if s.stage == 'over' or n >= 10:
            break
        if s.side == 'O' and s.stage == 'play':
            a = o.choose(s)
            n += 1
        else:
            acts = legal_actions(s)
            a = next((x for x in acts if x.kind in ('pause', 'end_turn')), acts[0])
        s = settle(apply(s, a), ('success', 'kept', 'no foul'))
    ev = [x['event'] for x in _events(o)]
    assert n >= 8 and ev[:2] == ['goal', 'goal_step'], ev
    for k, e in enumerate(ev):
        if e == 'goal' and k > 0:
            assert ev[k - 1] in ('goal_reassess', 'goal_finish'), ev
        if e == 'goal_reassess':
            prev = max((i for i in range(k) if ev[i] == 'goal'), default=None)
            assert prev is not None and 'goal_step' in ev[prev:k], ev        # progress before every change
    assert all(x.get('why') for x in o.notes if x['event'] == 'goal_reassess')


def test_no_goal_has_a_fixed_score():
    """Every goal's score is P x ((1 - risk) x V + risk x the pick-off) + (1 - P) x the best look now - the
    steps' cost; the pick-off is now -5 and two seconds with the ball kept (0 in the final phase)."""
    from playmaker_engine.planner import TEMPO
    for s in (post_position(), board('Five Out', 'High-Low', TABLE_O, TABLE_X, ['N', 'NE', 'NW', 'N', 'N'])):
        for g in goals(s, 'allstar'):
            want = g['P'] * ((1 - g['risk']) * g['V'] + g['risk'] * g['pick']) + (1 - g['P']) * g['base'] - TEMPO * len(g['todo'])
            assert g['score'] == pytest.approx(want, abs=0.02), g['words']
            assert g['V'] <= 3 * 20
    from playmaker_engine.resolve import pickoff_value
    s = board('Five Out', 'High-Low', TABLE_O, TABLE_X, ['N', 'NE', 'NW', 'N', 'N'])
    assert pickoff_value(s, 12.0, relative=True) == 7.0                      # -5, the ball kept: his look
    assert pickoff_value(s.with_(clock=2), 12.0, relative=True) == 0.0       # the final phase: 0


# ---- rotations -------------------------------------------------------------------------------------------
# The step 3i playout position (Bucket Brigade v Lockdown); X1, X4 and X5 have used their Moves. Under the live
# rules X3 is the one with two jobs: help on O1's drive and the lane to O3. X2 (Move left) faces up the wing;
# turning him takes the lane off X3.

def _rotation():
    s = board('Bucket Brigade', 'Lockdown', ['I6', 'D7', 'O9', 'D2', 'Q2'], ['H7', 'D8', 'N8', 'I5', 'J6'],
              ['W', 'N', 'NW', 'NW', 'W'], clock=10)
    return s.with_(tok_o=1, tok_x=2, moved_o=24, moved_x=25, cnt=(0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1), lock_o=1, phase=2, qs_x=1)


def test_the_defence_hands_a_job_to_a_defender_with_capacity_left():
    s = _rotation()
    od = [a for a in advantages(s, dilemma=True) if a['kind'] == 'overloaded']
    assert od and od[0]['defender'] == 2
    assert describe(od[0]) == "X3 had two jobs (help on O1's drive and the lane to O3); O3 was left for a three"
    x = s.with_(side='X')
    for lv in ('starter', 'allstar'):
        a = C.Computer('X', lv, seed=1, budget_s=None, habits=[]).choose(x)
        assert a.piece not in (None, 2) and capacity(x, a.piece)['movements'], (lv, a)      # a fresh defender
        n = apply(x, a)
        assert not isinstance(n, ChanceNode)
        assert not [b for b in advantages(n.with_(side='O'), dilemma=True) if b['kind'] == 'overloaded'], (lv, a)
