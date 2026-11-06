"""Step 3g: an offence that creates advantages. advantages() labels the board; the offence's candidates are
advantage plays (shoot, dribble attack, screen, speed burst, post seal, cut, pass to move or finish an
advantage) scored by create, reply, exploit. Positions come from computer playouts and the playtest logs
(tests/data/adv_positions.json: the start plus every state field)."""
import json
import os

from playmaker_engine import board as B
from playmaker_engine import computer as C
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.advantage import advantages, KINDS
from playmaker_engine.headtohead import start_state
from playmaker_engine.resolve import apply
from playmaker_engine.solver import Play, apply_play

HERE = os.path.dirname(__file__)
DATA = json.load(open(os.path.join(HERE, 'data', 'adv_positions.json')))


def _tup(v):
    return tuple(_tup(x) for x in v) if isinstance(v, list) else v


def position(name, key='fields'):
    d = DATA[name]
    return start_state(d['spec']).with_(**{k: _tup(v) for k, v in d[key].items()}), d


def before(name, s):
    """The board before the defence's move, in the same game (same context) as the position s."""
    return s.with_(**{k: _tup(v) for k, v in DATA[name]['prev'].items()})


def computer(s, level='allstar', prev=None):
    c = C.Computer('O', level, seed=1, budget_s=None, habits=[])
    c._context(s)
    c._handover = prev
    view = C.seen_state(s, 'O', c.seen)
    return c, view


def kinds(s, prev=None):
    return {a['kind'] for a in advantages(s, prev=prev)}


# ---- the six states, and none on a neutral set position -------------------------------------------

def test_a_neutral_set_position_has_no_advantage():
    s, _ = position('neutral')
    assert advantages(s) == []


def test_each_state_is_found():
    for name in ('mismatch', 'bad_closeout', 'spent', 'numbers'):
        s, d = position(name)
        assert any(a['kind'] == name and a['attacker'] == d['attacker'] for a in advantages(s)), name
    # beaten: lock the defender a dribble beat (the neutral position, with the dribble won)
    s, _ = position('neutral')
    found = False
    for j in range(5):
        t = s.with_(lock_x=1 << j, beaten=((s.ball, j),))
        if any(a['kind'] == 'beaten' and a['attacker'] == s.ball and a['defender'] == j for a in advantages(t)):
            found = True
            break
    assert found
    # spent with an empty pool: every attacker with a shot is open to it
    s, _ = position('neutral')
    t = s.with_(tok_x=0)
    assert any(a['kind'] == 'spent' and a.get('no_tokens') for a in advantages(t))
    # help pulled: a defender stepped toward the ball and off the ▲ shooter he was nearest to
    s, d = position('move')
    prev = before('move', s)
    assert 'help_pulled' not in kinds(s)                       # needs the board before the move
    hp = [a for a in advantages(s, prev=prev) if a['kind'] == 'help_pulled']
    assert hp and hp[0]['attacker'] == d['shooter'] and hp[0]['helper'] == d['helper']
    assert set(KINDS) == {'beaten', 'mismatch', 'help_pulled', 'bad_closeout', 'spent', 'numbers', 'overloaded'}


def test_an_advantage_is_valued_at_the_shot_after_the_reaction():
    s, d = position('mismatch')
    a = next(a for a in advantages(s) if a['kind'] == 'mismatch')
    from playmaker_engine.computer import reachable_contest
    rc = reachable_contest(s, a['attacker'], a['shot'])
    assert rc and abs(rc[0]['value'] - a['value']) < 1e-9             # the same contest model as the game's


# ---- the plays ---------------------------------------------------------------------------------------

def test_all_star_screens_for_a_mismatch_over_a_contested_pass():
    """Step 3g: O5, the ball carrier, screened X4 off O1 for a mismatch. Step 3i ruled that the carrier
    can't Screen (OQ-63), so that play is gone; what stays is that All-Star doesn't throw the contested pass."""
    s, d = position('screen')
    assert any(not i['clean'] for i in (C.pass_risk(s, s.ball, r) for r in range(5) if r != s.ball) if i)
    assert not any(a.kind == 'screen' and a.piece == s.ball for a in legal_actions(s))
    for goals in (False, True):
        c = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
        c.cfg = dict(c.cfg, goals=goals)
        a = c.choose(s)
        assert not (a.kind == 'pass' and not C.pass_risk(s, s.ball, a.target)['clean']), (goals, a)


def test_d7d923_the_speed_burst_to_k4_is_an_advantage_play():
    """Possession 1, clock 10: O3 on N7 with the ball after the defence's turn."""
    from playmaker_engine.review import replay_states
    recs = [json.loads(l) for l in open(os.path.join(HERE, 'data', 'log_D7D923.jsonl'))]
    s = replay_states(recs)[19][0]
    assert s.clock == 10 and s.o[2] == B.parse_sq('N7') and s.ball == 2
    for level in ('starter', 'allstar'):
        c, view = computer(s, level)
        cats = c._adv_plays(view, legal_actions(view))
        k4 = [p for p in cats['speed'] if p.actions[0].dest == B.parse_sq('K4')]
        assert k4, (level, cats['speed'])
        assert c._adv_value(view, apply_play(view, k4[0]), 2) > 0
        assert any(a['attacker'] == 2 for a in advantages(apply_play(view, k4[0])))
    c, view = computer(s, 'rookie')                                 # Rookie doesn't know the speed burst
    assert 'speed' not in c._adv_plays(view, legal_actions(view))


def test_a_long_shot_dribble_with_a_payoff_beats_a_likely_one_that_leads_nowhere():
    """The value decides, not a 'decent chance' threshold: a 40% dribble that leaves a ▲ shooter with a
    mismatch the defence can't fix outscores a 60% dribble that opens nothing."""
    from playmaker_engine.scoring import p_success
    scores = {}
    for name in ('dribble_40', 'dribble_60'):
        s, d = position(name)
        a = next(x for x in legal_actions(s) if str(x) == d['dribble'])
        p = float(p_success(s.ctx.off[s.ball].r['dribble'] - s.ctx.dfn[a.target].r['agility'], s.ctx.rules))
        c, view = computer(s)
        scores[name] = (p, c._adv_value(view, apply(view, a), 2))
    (p40, v40), (p60, v60) = scores['dribble_40'], scores['dribble_60']
    assert p40 < 0.5 < p60 and v40 > 0 >= v60 and v40 > v60, scores


def test_all_star_moves_the_advantage_to_the_shooter_help_left():
    s, d = position('move')
    prev = before('move', s)
    c = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    c._context(s)
    c._handover = prev
    a = c.choose(s)
    assert a.kind == 'pass' and a.target == d['shooter'], a
    st, view = computer(s, 'starter', prev)                         # Starter doesn't look for it
    passes = st._adv_plays(view, legal_actions(view))['pass']
    assert not any(p.concept == 'pass to help_pulled' for p in passes), passes


def test_no_pass_without_an_advantage_to_move():
    s, _ = position('neutral')
    for level in C.LEVEL_NAMES:
        c, view = computer(s, level)
        assert c._adv_plays(view, legal_actions(view))['pass'] == [], level


def test_82866b_the_loop_plays_score_nothing():
    """Possession 1, clock 4: the cycle (O4/O2 pass exchange, Hesitate, O4 Move A5 + Quick Step A6) left
    no advantage. Each of its plays scores nothing, so none is chosen on its merits."""
    from playmaker_engine.review import replay_states
    recs = [json.loads(l) for l in open(os.path.join(HERE, 'data', 'log_82866B.jsonl'))]
    sts = replay_states(recs)
    for idx in (54, 59, 62):
        s, logged, _ = sts[idx]
        c, view = computer(s, 'rookie')
        play = Play('loop', (logged,))
        node = apply_play(view, play)
        assert node is not None and c._adv_value(view, node, 1) <= 0, (idx, logged)
        assert not any(p.actions == (logged,) for p in c._adv_plays(view, legal_actions(view))['pass']), (idx, logged)


def test_levels_map_the_play_types():
    L = C.LEVELS['offence']['levels']
    assert L['rookie']['plays'] == ['shoot', 'dribble', 'pass'] and L['rookie']['advantage_depth'] == 1
    assert set(L['starter']['plays']) == {'shoot', 'dribble', 'pass', 'screen', 'speed', 'seal', 'vcut', 'shift'}
    assert set(L['allstar']['plays']) - set(L['starter']['plays']) == {'cut', 'move_advantage', 'baseline', 'backcut',
                                                                       'offscreen', 'dilemma'}
    assert L['starter']['advantage_depth'] == L['allstar']['advantage_depth'] == 2


def test_the_review_names_the_advantage_plays():
    from playmaker_engine.review import computer_facts
    recs = [dict(type='setup', computer=dict(O=dict(level='allstar', name='All-Star', habits=[], concepts_off=[]))),
            dict(type='computer', side='O', possession=1, event='play', play='screen', attacker=0,
                 text='Screen for a mismatch: O2 screens X1 off O1', advantage='O1 has a mismatch on X4 (three)'),
            dict(type='computer', side='O', possession=1, event='advantage_moved', attacker=4, helper=4, shot='three',
                 text='Help came from X5; the advantage moved to O5'),
            dict(type='computer', side='O', possession=1, event='finish', attacker=4, shot='three', text='Finished: O5 three')]
    text = ' '.join(computer_facts(recs))
    assert 'Help came from X5; the advantage moved to O5.' in text and 'Finished: O5 three.' in text
    assert 'Screen for a mismatch: O2 screens X1 off O1. O1 has a mismatch on X4 (three).' in text
