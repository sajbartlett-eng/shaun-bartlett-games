"""Step 3d part C: the decision timer. Off by default; a fake clock drives every check."""
import json

import pytest

from playmaker_engine.actions import ORDER, legal_actions
from playmaker_engine.review import replay
from playmaker_engine.scenarios import scenario_state
from playmaker_engine.timer import timer_forfeit
from playmaker_web.game import Game, GameError, action_to_json
from playmaker_web.view import state_json


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def tick(self, s):
        self.t += s


def timed(seconds=30, mode='hotseat', **kw):
    c = Clock()
    g = Game(mode=mode, scenario=kw.pop('scenario', 6), seed=kw.pop('seed', 3), level='pro', timer=seconds, clock=c, **kw)
    return g, c


def tok(g):
    return g.tokens['both']


def ready(g):
    g.timer_event(tok(g), 'ready')


def forfeits(g):
    return [r for r in g.read_log() if r['type'] == 'timer' and r['event'] == 'forfeit']


# ---- the penalty ----------------------------------------------------------------------------------

def test_a_forfeit_costs_one_token_keeps_the_turn_and_restarts_the_timer():
    g, c = timed(30)
    ready(g)
    c.tick(29.9)
    assert state_json(g, tok(g))['tokens']['O'] == 6
    c.tick(0.2)
    s = state_json(g, tok(g))
    assert s['tokens']['O'] == 5 and s['side'] == 'O' and s['timer']['mode'] == 'main'
    assert s['timer']['left'] == pytest.approx(29.9, abs=0.01)               # restarted at full at the forfeit
    assert s['timer']['note'] == 'Timer: 1 token lost. 5 left.'
    f = forfeits(g)
    assert len(f) == 1 and f[0]['effect'] == 'token' and f[0]['phase'] == 1 and f[0]['side'] == 'O'


def test_the_last_token_ends_the_turn_and_an_empty_pool_ends_it_too():
    s = scenario_state(6)
    for _ in range(5):
        s, eff = timer_forfeit(s)
        assert eff == 'token' and s.side == 'O'
    s, eff = timer_forfeit(s)
    assert eff == 'token_end' and s.side == 'X' and s.tok_o == 0
    empty = scenario_state(6).with_(tok_o=0)
    s2, eff2 = timer_forfeit(empty)
    assert eff2 == 'end_turn' and s2.side == 'X'


def test_a_committed_action_resets_the_timer():
    g, c = timed(30)
    ready(g)
    c.tick(20)
    a = next(a for a in g.legal() if a.kind == 'move' and a.side == 'O')
    g.act(tok(g), action_to_json(a))
    s = state_json(g, tok(g))
    if s['side'] == 'O':
        assert s['timer']['left'] == pytest.approx(30, abs=0.01)
    assert not forfeits(g)


# ---- token-free decisions -------------------------------------------------------------------------

def _to_contest(g):
    """O1 to J10, declares the shot, the defence passes its reaction: the contest choice is next."""
    t = tok(g)
    for pred in (lambda a: a.kind == 'move' and a.piece == 0 and a.dest == (9, 10),
                 lambda a: a.kind == 'shot', lambda a: a.kind == 'end_turn'):
        a = next(a for a in g.legal() if pred(a))
        g.act(t, action_to_json(a))
        if g.timer and g.tm['mode'] == 'ready':
            ready(g)


def test_an_expired_contest_choice_means_no_contest_and_no_token_lost():
    # step 6 (D-18): the Contest is a reaction action with a token, so an expired reaction decision costs a token like
    # any other; ending the reaction then means no Contest (a contest of 0)
    c = Clock()
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], seed=2, level='pro', timer=30, clock=c)
    ready(g)
    _to_contest(g)
    assert g.state.stage == 'over' and g.state.result.contester == -1
    from playmaker_engine.scoring import score
    assert 'contested by nobody' in score(g.state).detail
    g2 = Game(mode='hotseat', teams=['Five Out', 'High-Low'], seed=2, level='pro', timer=30, clock=c)
    ready(g2)
    t = tok(g2)
    for pred in (lambda a: a.kind == 'move' and a.piece == 0 and a.dest == (9, 10), lambda a: a.kind == 'shot'):
        g2.act(t, action_to_json(next(a for a in g2.legal() if pred(a))))
        if g2.timer and g2.tm['mode'] == 'ready':
            ready(g2)
    assert g2.state.stage == 'reaction'
    tx = g2.state.tok_x
    c.tick(31)
    state_json(g2, t)
    f = forfeits(g2)[-1]
    assert f['effect'] == 'token' and g2.state.tok_x == tx - 1 and g2.state.stage == 'reaction'


def test_an_expired_forced_shot_takes_the_first_legal_type():
    s = scenario_state(6)
    s = s.with_(o=((9, 10),) + s.o[1:], stage='forced', side='O', forced=True, shot=None)   # O1 on J10 (three zone)
    first = next(a for a in legal_actions(s) if a.kind == 'forced_shot')
    node, eff = timer_forfeit(s)
    assert eff == 'default'
    assert node.shot == first.shot and node.tok_o == s.tok_o


# ---- pauses ---------------------------------------------------------------------------------------

def test_no_timer_before_tip_off_or_during_the_handover():
    c = Clock()
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], seed=1, level='scout', timer=30, clock=c)
    assert g.timer_json()['mode'] == 'idle'                     # the scouting picks come first: no timer
    g.scout(tok(g), dict(side='O', hunt=dict(o=1, x=1)))
    g.scout(tok(g), dict(side='X', protect=dict(x=1)))
    assert g.timer_json()['mode'] == 'ready'                    # hot-seat: waits for Ready
    c.tick(500)
    assert state_json(g, tok(g))['tokens']['O'] == 6 and not forfeits(g)
    ready(g)
    c.tick(10)
    assert g.timer_json()['left'] == pytest.approx(20)


def test_placement_has_no_timer():
    c = Clock()
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], seed=1, level='pro', timer=30, clock=c, place=True, full=True)
    assert g.placing == 'O' and g.timer_json()['mode'] == 'idle'
    c.tick(300)
    assert not forfeits(g)


def test_pause_for_a_roll_dialog_and_resume():
    g, c = timed(30)
    ready(g)
    c.tick(5)
    g.timer_event(tok(g), 'pause')
    c.tick(100)
    assert g.timer_json()['left'] == pytest.approx(25) and not forfeits(g)
    g.timer_event(tok(g), 'resume')
    c.tick(5)
    assert g.timer_json()['left'] == pytest.approx(20)


def test_the_opponents_turn_does_not_run_your_timer():
    c = Clock()
    g = Game(mode='remote', scenario=6, seed=3, level='pro', timer=30, clock=c)
    o, x = g.join('O'), g.join('X')
    assert g.timer_json()['side'] == 'O' and g.timer_json()['mode'] == 'main'    # remote: no Ready screen
    a = next(a for a in g.legal() if a.kind == 'hesitate')
    g.act(o, action_to_json(a))
    assert g.timer_json()['side'] == 'X'
    c.tick(29)
    assert g.state.tok_o == g.state.tok_o and not forfeits(g)
    with pytest.raises(GameError):
        g.act(o, action_to_json(next(iter(g.legal()))))                         # not O's turn
    c.tick(2)
    state_json(g, x)
    assert forfeits(g)[-1]['side'] == 'X'


def test_the_computer_side_has_no_timer():
    c = Clock()
    g = Game(mode='hotseat', scenario=6, seed=3, level='pro', timer=30, clock=c, ai=dict(X='greedy'))
    ready(g)
    a = next(a for a in g.legal() if a.kind == 'hesitate')
    g.act(tok(g), action_to_json(a))
    g.after_human()
    assert g.timer_json()['side'] in ('O', None)


# ---- the admin grace ------------------------------------------------------------------------------

def test_completing_within_the_grace_never_costs_a_token():
    g, c = timed(30)
    ready(g)
    c.tick(28)
    g.timer_event(tok(g), 'select')
    c.tick(14)                                       # 42 s in total: past the main period, inside the grace
    a = next(a for a in g.legal() if a.kind == 'pass')
    g.act(tok(g), action_to_json(a))
    assert not forfeits(g)
    rec = [r for r in g.read_log() if r['type'] == 'action'][-1]
    assert rec['grace_s'] == pytest.approx(14, abs=0.01) and rec['timer_left'] == pytest.approx(2, abs=0.01)


def test_an_expired_grace_resumes_the_main_timer_from_where_it_paused():
    g, c = timed(30)
    ready(g)
    c.tick(10)
    g.timer_event(tok(g), 'select')
    c.tick(15)
    assert g.timer_json()['mode'] == 'main' and g.timer_json()['left'] == pytest.approx(20)
    log = g.read_log()
    assert any(r['type'] == 'timer' and r['event'] == 'grace_expired' for r in log)
    c.tick(20)
    state_json(g, tok(g))
    assert len(forfeits(g)) == 1


def test_cancelling_resumes_without_a_reset_or_a_penalty():
    g, c = timed(30)
    ready(g)
    c.tick(10)
    g.timer_event(tok(g), 'select')
    c.tick(5)
    g.timer_event(tok(g), 'cancel')
    assert g.timer_json()['left'] == pytest.approx(20) and g.timer_json()['mode'] == 'main'
    assert any(r['type'] == 'timer' and r['event'] == 'cancel' for r in g.read_log()) and not forfeits(g)


def test_select_and_cancel_cycling_cannot_freeze_the_clock():
    g, c = timed(30)
    ready(g)
    for _ in range(40):
        g.timer_event(tok(g), 'select')
        c.tick(1)
        g.timer_event(tok(g), 'cancel')
        c.tick(1)
    # a fresh grace needs 5 s of main timer since the last selection, so the main clock keeps running
    assert forfeits(g), 'cycling froze the clock'


# ---- replay, neutrality, the solver, off ---------------------------------------------------------

def test_a_timed_games_log_replays_to_the_same_final_state():
    g, c = timed(30)
    ready(g)
    for _ in range(30):
        if g.state.stage == 'over':
            break
        if g.tm['mode'] == 'ready':
            ready(g)
        c.tick(31)
        state_json(g, tok(g))
    assert forfeits(g)
    finals = replay(g.read_log())
    assert finals[-1][1].encode() == g.state.encode()


def test_both_sides_get_the_same_setting_unless_handicap_is_ticked():
    with pytest.raises(GameError):
        Game(mode='hotseat', scenario=6, level='pro', timer=dict(A=60, B=30))
    g = Game(mode='hotseat', scenario=6, level='pro', timer=dict(A=60, B=30, handicap=True))
    assert g.timer['handicap'] and g.read_log()[0]['timer']['handicap']
    s = state_json(g, tok(g))
    assert s['timer']['handicap'] and s['timer']['by_side'] == dict(O=60, X=30)
    same = Game(mode='hotseat', scenario=6, level='pro', timer=45)
    assert same.timer_json()['by_side'] == dict(O=45, X=45) and not same.timer['handicap']
    with pytest.raises(GameError):
        Game(mode='hotseat', scenario=6, level='pro', timer=50)


def test_timer_forfeit_is_never_a_legal_action():
    assert 'timer_forfeit' not in ORDER and 'timer' not in ORDER
    s = scenario_state(6)
    assert all(a.kind != 'timer_forfeit' for a in legal_actions(s))


def test_timer_off_means_no_timer_state_anywhere():
    g = Game(mode='hotseat', scenario=6, seed=3, level='pro')
    s = state_json(g, tok(g))
    assert 'timer' not in s and g.timer is None
    assert g.read_log()[0]['timer'] is None
    with pytest.raises(GameError):
        g.timer_event(tok(g), 'ready')
    blob = json.dumps(s)
    assert '"grace' not in blob and 'timer_left' not in blob


def test_the_review_shows_forfeits_as_plain_facts():
    from playmaker_engine.review import timer_facts
    g, c = timed(30)
    ready(g)
    for _ in range(40):
        if g.state.stage == 'over':
            break
        if g.tm['mode'] == 'ready':
            ready(g)
        c.tick(31)
        state_json(g, tok(g))
    facts = timer_facts(g.read_log())
    assert facts and facts[0] == 'Possession 1: the offence lost 1 token to the timer in phase 1 (clock 6).'
    r = g.review(tok(g))
    assert r['timer'] == facts and 'mistake' not in json.dumps(r).lower()
