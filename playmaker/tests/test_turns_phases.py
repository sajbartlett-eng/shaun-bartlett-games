"""Turns, per-phase limits, phase end, reset, clock expiry, waits."""
import pytest
from conftest import mk, P

from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import settle, apply, force, ChanceNode
from playmaker_engine.scoring import score
from playmaker_engine.state import CI, ZERO_COUNTS

O5 = ['I11', 'C9', 'O9', 'A3', 'Q3']
X5 = ['I10', 'D8', 'N8', 'G4', 'N4']
ARR = ['N', 'NE', 'NW', 'N', 'N']


def base(**kw):
    return mk(O5, X5, ARR, **kw)


def with_count(s, key, n):
    c = list(s.cnt)
    c[CI[key]] = n
    return s.with_(cnt=tuple(c))


def kinds(s):
    return {a.kind for a in legal_actions(s)}


@pytest.mark.parametrize('key,kind,side,limit', [
    ('pass', 'pass', 'O', 2), ('screen', 'screen', 'O', 2), ('dribble', 'dribble', 'O', 2),
    ('hesitate', 'hesitate', 'O', 1), ('o_qs', 'qs', 'O', 2),
    ('steal', 'steal', 'X', 2), ('challenge', 'challenge', 'X', 2), ('pause', 'pause', 'X', 1), ('x_qs', 'qs', 'X', 2),
])
def test_per_phase_limits(key, kind, side, limit):
    s = base(side=side)
    if kind == 'challenge':
        s = s.with_(screens=((2, 5, False, 0),))      # O3's T on X3 (N8): X3 may Challenge
    if kind == 'dribble':
        pass                                    # X1 at I10 is adjacent to the carrier
    s_ok = with_count(s, key, limit - 1)
    s_full = with_count(s, key, limit)
    assert kind in kinds(s_ok)
    assert kind not in kinds(s_full)


def test_intercept_limit():
    s = apply(base(), Action('pass', 'O', 0, target=2))
    s_on = s.with_(x=(P('I10'), P('D8'), P('L10'), P('G4'), P('N4')))
    assert 'intercept' in kinds(s_on)
    assert 'intercept' not in kinds(with_count(s_on, 'intercept', 2))


def test_shot_limit_and_plain_wood():
    s = base()
    assert 'shot' not in kinds(s)               # O1 on plain wood (I11)
    s2 = base(o=(P('I9'),) + base().o[1:])
    assert 'shot' in kinds(s2)
    assert 'shot' not in kinds(with_count(s2, 'shot', 1))


def test_turn_enders_end_the_turn():
    s = base()
    assert apply(s, Action('hesitate', 'O')).side == 'X'
    s1 = apply(s, Action('move', 'O', 1, P('C10')))
    assert s1.side == 'O' and s1.turn_n == 1 and 'end_turn' in kinds(s1)
    s2 = apply(s1, Action('move', 'O', 2, P('O10')))
    assert s2.side == 'X'                       # two actions: turn over
    s3 = apply(s1, Action('pass', 'O', 0, target=1))
    assert s3.side == 'X'                       # a turn-ender as the second action
    assert 'end_turn' not in kinds(s)           # at least one action


def test_offence_last_token_gives_defence_one_final_turn():
    s = base(tok_o=1, tok_x=4)
    s = apply(s, Action('move', 'O', 1, P('C10')))
    assert s.side == 'X' and s.final
    s = apply(s, Action('move', 'X', 3, P('G5'), 0))
    s = settle(apply(s, Action('end_turn', 'X')))
    assert s.phase == 2 and s.clock == 10 and s.tok_o == 6 and s.tok_x == 6 and s.side == 'O'


def test_defence_last_token_ends_phase_at_once():
    s = base(side='X', tok_o=5, tok_x=1)
    s = apply(s, Action('move', 'X', 3, P('G5'), 0))
    assert s.phase == 2 and s.clock == 10 and s.side == 'O'


@pytest.mark.usefixtures('legacy_rules')   # recorded under the rules before the step 3i follow-up rulings
def test_reset_clears_tokens_locks_keeps_pieces_and_screens():
    s = base(side='X', tok_x=1, lock_o=0b1, lock_x=0b10, screens=((2, 4, False, 0),), cnt=tuple([1] * len(ZERO_COUNTS)))
    s2 = apply(s, Action('qs', 'X', 0, P('I9')) if False else Action('move', 'X', 3, P('G5'), 0))
    assert (s2.tok_o, s2.tok_x, s2.lock_o, s2.lock_x, s2.cnt, s2.moved_o, s2.moved_x) == (6, 6, 0, 0, ZERO_COUNTS, 0, 0)
    assert s2.o == s.o and s2.x[3] == P('G5') and s2.screens == s.screens and s2.clock == s.clock - 2


def test_clock_expiry_forced_shot():
    # O1 on a three square, X1 adjacent but arrow off: forced shot, -5 turnover.
    s = base(o=(P('I10'), P('C9'), P('O9'), P('A3'), P('Q3')), x=(P('I14'),) + base().x[1:], clock=2,
             side='X', tok_x=1)
    end = apply(s, Action('move', 'X', 3, P('G5'), 0))
    assert end.stage == 'contest' and [a.piece for a in legal_actions(end)] == [-1]   # nobody adjacent
    end = settle(end)
    assert not isinstance(end, ChanceNode)          # nobody adjacent: no foul roll, contest 0
    assert end.stage == 'over' and end.result.kind == 'forced'
    sc = score(end)
    o1 = end.ctx.off[0]
    assert sc.turnovers == 1 and sc.shot_value == 3 * o1.shot('three') and sc.total == sc.shot_value - 5


def test_clock_expiry_plain_wood_scores_zero():
    s = base(clock=2, side='X', tok_x=1)       # O1 on I11, plain wood
    end = apply(s, Action('move', 'X', 3, P('G5'), 0))
    sc = score(end)
    assert sc.shot_value == 0 and sc.total == -5


def test_clock_expiry_negative_value_floors_at_zero():
    # Weak three-point shooter heavily contested: value would be negative, forced shot scores 0.
    # O4 pspfB three 6 v X2 tndA con_three 7, arrow on the shooter, nearer the rim: 3 x (6 - 7) = -3 -> 0.
    s = mk(['I14', 'A14', 'C14', 'Q3', 'E14'], ['A13', 'P3', 'M14', 'K14', 'O14'], ['N', 'E', 'N', 'N', 'N'],
           ball=3, off='Twin Towers', dfn='Shoot and Protect', clock=2, side='X', tok_x=1)
    end = settle(apply(s, Action('move', 'X', 4, P('O13'), 0)))
    assert end.result.kind == 'forced' and end.result.shot_value == 0 and score(end).total == -5


def test_hesitate_pause_chain():
    s = base()
    s = apply(s, Action('hesitate', 'O'))
    assert 'pause' not in kinds(s)             # not straight after Hesitate
    s = apply(s, Action('move', 'X', 3, P('G5'), 0))
    s = settle(apply(s, Action('end_turn', 'X')))
    s = apply(s, Action('move', 'O', 1, P('C10')))
    s = apply(s, Action('end_turn', 'O'))
    assert 'pause' in kinds(s)
    s = apply(s, Action('pause', 'X'))
    assert 'hesitate' not in kinds(s.with_(cnt=ZERO_COUNTS))   # not straight after Pause


def test_shot_declaration_then_reaction_then_contest():
    s = base(o=(P('I9'),) + base().o[1:])     # O1 on long two at I9, X1 at I10 arrow N (off the shooter)
    r = apply(s, Action('shot', 'O', 0, shot='long'))
    assert r.stage == 'reaction' and r.side == 'X'
    kinds_r = kinds(r)
    assert kinds_r <= {'move', 'qs', 'sprint', 'steal', 'contest', 'end_turn'}      # step 6 (D-18): Contest is an action
    end = settle(apply(r, Action('end_turn', 'X')))
    flat = end.flatten() if isinstance(end, ChanceNode) else [(1, '', end)]
    assert all(st.stage == 'over' for _, _, st in flat)


def test_forfeit_when_stuck():
    s = base(side='X', moved_x=0b11111, cnt=tuple(2 if k in ('x_qs', 'steal') else (1 if k == 'pause' else 0) for k in CI))
    acts = legal_actions(s)
    assert [a.kind for a in acts] == ['forfeit']
    s2 = apply(s, acts[0])
    assert s2.phase == 2


def test_legal_actions_deterministic_and_unique():
    s = base()
    a1, a2 = legal_actions(s), legal_actions(s)
    assert a1 == a2 and len(a1) == len(set(a1))
    sx = base(side='X')
    ax = legal_actions(sx)
    assert len(ax) == len(set(ax))
