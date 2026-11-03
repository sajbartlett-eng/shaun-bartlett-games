"""Chance nodes, intercept geometry, Dribble, Challenge, Steal, contests and scoring."""
from fractions import Fraction as F

from conftest import mk, P

from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply, force, ChanceNode
from playmaker_engine.scoring import (score, band, p_success, contest_options, choose_contest, free_throws,
                                      match_result)
from playmaker_engine.rules_config import with_rules

O5 = ['I11', 'C9', 'O9', 'A3', 'Q3']
X5 = ['I10', 'D8', 'N8', 'G4', 'N4']
ARR = ['N', 'NE', 'NW', 'N', 'N']


def base(o=O5, x=X5, arr=ARR, **kw):
    return mk(list(o), list(x), list(arr), **kw)


def icpts(s):
    return [a for a in legal_actions(s) if a.kind == 'intercept']


def outcomes(node):
    return {lab: p for p, lab, _ in node.flatten()}


# ---- probability ----------------------------------------------------------------

def test_roll_bounds_and_example():
    assert p_success(13) == F(13, 20)
    assert p_success(20) == 1 and p_success(25) == 1
    assert p_success(0) == 0 and p_success(-3) == 0
    alt = with_rules(natural_rolls=True)
    assert p_success(25, alt) == F(19, 20) and p_success(-3, alt) == F(1, 20)


def test_pass_18_v_intercept_5_is_13_in_20():
    s = apply(base(), Action('pass', 'O', 0, target=2))      # O1 ppgC Pass 18 -> O3
    assert s.side == 'X' and s.pending == (0, 2)
    s = apply(s, Action('move', 'X', 2, P('L10'), 7))        # X3 stsfC (Intercept 5) arrow across: onto the line
    assert s.pending and s.approach == 2 and s.tok_x == 5
    node = apply(s, Action('intercept', 'X', 2))
    assert isinstance(node, ChanceNode)
    assert outcomes(node) == {'success': F(13, 20), 'failure': F(7, 20)}
    assert node.total() == 1
    ok = force(node, 'success')
    assert ok.ball == 2 and ok.tok_x == 4 and ok.side == 'O'
    lost = force(node, 'failure')
    assert lost.ball == 0 and lost.tos == 1 and lost.pending is None and score(lost.with_(stage='over')).total == -5


# ---- intercept geometry ------------------------------------------------------------

def test_on_line_defender_intercepts_facing_any_way():
    s = apply(base(x=['I10', 'D8', 'L10', 'G4', 'N4'], arr=['N', 'NE', 'S', 'N', 'N']), Action('pass', 'O', 0, target=2))
    assert [a.piece for a in icpts(s)] == [2]


def test_arrow_across_must_reach_line_first():
    s = apply(base(), Action('pass', 'O', 0, target=2))
    assert icpts(s) == []                                    # X3's arrow crosses, but it isn't on the line
    s2 = apply(s, Action('move', 'X', 2, P('M9'), 7))        # moves, but not onto the line
    assert icpts(s2) == [] and s2.ball == 2 and s2.pending is None   # the pass landed


def test_defender_without_arrow_across_cannot_approach():
    # X5 at N4 arrow N: its ray (N5..N14) misses the I11->O9 segment. Moving onto the line is just a move.
    s = apply(base(), Action('pass', 'O', 0, target=2))
    s2 = apply(s, Action('qs', 'X', 0, P('I9')))
    assert s2.pending is None and s2.ball == 2


def test_adjacent_passer_arrow_on_passer_only_stops_pass_through_its_square():
    # X1 at I10, arrow N at the passer I11.
    s = apply(base(), Action('pass', 'O', 0, target=2))              # pass I11 -> O9: not through I10
    assert 1 - 1 not in [a.piece for a in icpts(s)]
    s2 = apply(base(o=['I11', 'C9', 'I5', 'A3', 'Q3'], x=['I10', 'D8', 'N8', 'G4', 'N4']),
               Action('pass', 'O', 0, target=2))                     # pass straight down through I10
    assert [a.piece for a in icpts(s2)] == [0]


def test_adjacent_passer_counts_only_through_its_arrow():
    # Pass I11 -> A7. X1 at H11 is adjacent to the passer and its centre is on the line, but its
    # arrow (N) neither points at the passer nor crosses the pass: it cannot intercept.
    s = base(o=['I11', 'C9', 'O9', 'A7', 'Q3'], x=['H11', 'D12', 'N8', 'G4', 'N4'], arr=['N', 'NE', 'NW', 'N', 'N'])
    from playmaker_engine import board as B
    assert B.on_segment(P('H11'), P('I11'), P('A7'), 0.5)
    s = apply(s, Action('pass', 'O', 0, target=3))
    assert icpts(s) == []
    # Same spot with the arrow SW across the pass: it counts, but must first move onto the line.
    s2 = base(o=['I11', 'C9', 'O9', 'A7', 'Q3'], x=['H11', 'D12', 'N8', 'G4', 'N4'], arr=['SW', 'NE', 'NW', 'N', 'N'])
    s2 = apply(s2, Action('pass', 'O', 0, target=3))
    assert icpts(s2) == []
    s3 = apply(s2, Action('move', 'X', 0, P('G10'), 0))
    assert s3.approach == 0 and [a.piece for a in icpts(s3)] == [0]


# ---- Dribble / Challenge -------------------------------------------------------------

def test_dribble_probabilities_and_results():
    s = base()
    node = apply(s, Action('dribble', 'O', 0, target=0))     # O1 ppgC Dribble 17 v X1 cgA Agility 8
    o, x = s.ctx.off[0], s.ctx.dfn[0]
    assert outcomes(node) == {'success': F(o.r['dribble'] - x.r['agility'], 20), 'failure': 1 - F(o.r['dribble'] - x.r['agility'], 20)}
    win, lose = force(node, 'success'), force(node, 'failure')
    assert win.locked('X', 0) and (0, 0) in win.beaten and win.side == 'X'
    assert lose.locked('O', 0) and not lose.locked('X', 0)
    assert {a.kind for a in legal_actions(lose.with_(side='O', turn_n=0))} >= {'pass'}


def test_challenge_screen():
    s = base(side='X', screens=((2, 4, False, 0),))
    node = apply(s, Action('challenge', 'X', 2, target=2))
    o, x = s.ctx.off[2], s.ctx.dfn[2]
    p = F(o.r['screen'] - x.r['challenge'], 20)
    assert outcomes(node) == {'success': p, 'failure': 1 - p}
    assert force(node, 'success').locked('X', 2)
    assert force(node, 'failure').screens[0][3] == 0b100


# ---- Steal ---------------------------------------------------------------------------

def steal_state(**kw):
    return base(side='X', **kw)                              # X1 at I10, arrow N on O1 at I11


def test_steal_needs_adjacent_arrow_on_carrier():
    assert [a.piece for a in legal_actions(steal_state()) if a.kind == 'steal'] == [0]
    s = base(side='X', arr=['E', 'NE', 'NW', 'N', 'N'])
    assert not [a for a in legal_actions(s) if a.kind == 'steal']


def test_steal_foul_then_dribble_nesting():
    s = steal_state()
    node = apply(s, Action('steal', 'X', 0))
    o, x = s.ctx.off[0], s.ctx.dfn[0]
    pf = F(x.r['foul_steal'], 20)
    pk = F(o.r['dribble'] - x.r['steal'], 20)
    assert outcomes(node) == {'foul': pf, 'no foul/kept': (1 - pf) * pk, 'no foul/stolen': (1 - pf) * (1 - pk)}
    assert node.total() == 1
    first = force(node, 'foul')
    assert first.stage == 'play' and first.bonus5 == 1 and first.fouls == 1
    stolen = force(node, 'no foul', 'stolen')
    assert stolen.stage == 'play' and stolen.tos == 1 and stolen.ball == 0      # play on (OQ-1)


def test_second_steal_foul_free_throws():
    s = steal_state(fouls=1, bonus5=1)
    end = force(apply(s, Action('steal', 'X', 0)), 'foul')
    sc = score(end)
    assert end.stage == 'over' and sc.free_throws == 2 * s.ctx.off[0].r['free_throw'] and sc.bonus == 5


def test_steal_after_declared_shot():
    s = base(o=['I9', 'C9', 'O9', 'A3', 'Q3'], x=['I8', 'D8', 'N8', 'G4', 'N4'])
    r = apply(s, Action('shot', 'O', 0, shot='long'))
    node = apply(r, Action('move', 'X', 0, P('I8'), 0))       # X1 turns its arrow onto the shooter
    st = apply(node, Action('steal', 'X', 0))
    foul = force(st, 'foul')
    assert foul.stage == 'over' and score(foul).free_throws == 2 * s.ctx.off[0].r['free_throw']
    stolen = force(st, 'no foul', 'stolen')
    assert stolen.result.kind == 'steal' and score(stolen).total == -5
    kept = force(st, 'no foul', 'kept')
    assert kept.stage == 'over' and kept.result.kind == 'shot'       # then the contest


# ---- contest and free throws -----------------------------------------------------------

def shooter_state(xsq, arrow, osq='I9'):
    return base(o=[osq, 'C9', 'O9', 'A3', 'Q3'], x=[xsq, 'D8', 'N8', 'G4', 'N4'], arr=[arrow, 'NE', 'NW', 'N', 'N'])


def test_contest_minus_three_when_further_from_rim():
    near = {o.defender: o.contest for o in contest_options(shooter_state('I8', 'N'), 0, 'long')}
    far = {o.defender: o.contest for o in contest_options(shooter_state('I10', 'S'), 0, 'long')}
    c = shooter_state('I8', 'N').ctx.dfn[0].con('long')
    assert near[0] == c and far[0] == c - 3


def test_contest_arrow_on_is_clean_off_rolls_foul():
    on = contest_options(shooter_state('I8', 'N'), 0, 'long')
    off = contest_options(shooter_state('I8', 'E'), 0, 'long')
    x = shooter_state('I8', 'N').ctx.dfn[0]
    assert [o for o in on if o.defender == 0][0].clean
    o_off = [o for o in off if o.defender == 0][0]
    assert not o_off.clean and o_off.p_foul == F(x.r['foul_contest'], 20)


def test_contest_foul_gives_free_throws():
    s = shooter_state('I8', 'E', osq='I9')
    r = apply(s, Action('shot', 'O', 0, shot='long'))
    r = r.with_(tok_x=0)
    from playmaker_engine.resolve import resolve_shot
    node = resolve_shot(r)
    opt = choose_contest(r, 0, 'long')
    if opt.defender == 0:                      # defence chose to contest with the arrow off
        assert isinstance(node, ChanceNode) and force(node, 'foul').result.kind == 'free_throws'
    else:                                      # or chose not to (allowed with the arrow off)
        assert opt.defender == -1


def test_no_adjacent_defender_contest_zero():
    s = shooter_state('A14', 'N')
    opt = choose_contest(s, 0, 'long')
    assert opt.defender == -1 and opt.contest == 0 and opt.value == 2 * s.ctx.off[0].shot('long')


def test_free_throw_multipliers():
    c = shooter_state('A14', 'N').ctx.off[0]
    assert free_throws(c, 2) == 2 * c.r['free_throw'] and free_throws(c, 3) == 3 * c.r['free_throw']


def test_declared_negative_shot_scores_negative():
    # Twin Towers O4 (three 6) on Q3 v Shoot and Protect X2 tndA (con_three 7), arrow on, nearer the rim.
    s = mk(['I14', 'A14', 'C14', 'Q3', 'E14'], ['A13', 'P3', 'M14', 'K14', 'O14'], ['N', 'E', 'N', 'N', 'N'],
           ball=3, off='Twin Towers', dfn='Shoot and Protect')
    r = apply(s, Action('shot', 'O', 3, shot='three'))
    end = apply(r, Action('end_turn', 'X'))
    assert end.result.shot_value == -3 and score(end).total == -3
    s2 = mk(['I14', 'A14', 'C14', 'Q3', 'E14'], ['A13', 'P3', 'M14', 'K14', 'O14'], ['N', 'E', 'N', 'N', 'N'],
            ball=3, off='Twin Towers', dfn='Shoot and Protect', rules=with_rules(floor_declared_shot=True))
    end2 = apply(apply(s2, Action('shot', 'O', 3, shot='three')), Action('end_turn', 'X'))
    assert score(end2).total in (0, 18)          # floored: the defence may now prefer no contest


# ---- bands, Coach's Call, match ------------------------------------------------------------

def test_bands():
    assert [band(v) for v in (30, 29, 25, 24, 20, 19, 15, 14, -5)] == \
        ['Excellent', 'Great', 'Great', 'Good', 'Good', 'Okay', 'Okay', 'Poor', 'Poor']


def test_coach_call_bonus():
    from playmaker_engine.scenarios import scenario_state
    s = scenario_state(8, target=0)
    # put O1 on a three square, nobody near, and shoot
    s = s.with_(o=(P('J10'),) + s.o[1:], x=(P('A14'),) + s.x[1:])
    end = apply(apply(s, Action('shot', 'O', 0, shot='three')), Action('end_turn', 'X'))
    sc = score(end)
    assert sc.coach_bonus == RC.COACH_BONUS[band(sc.look)] and sc.total == sc.shot_value + sc.coach_bonus
    s2 = scenario_state(8, target=1).with_(o=(P('J10'),) + s.o[1:], x=(P('A14'),) + s.x[1:])
    end2 = apply(apply(s2, Action('shot', 'O', 0, shot='three')), Action('end_turn', 'X'))
    assert score(end2).coach_bonus == 0


def test_match_tiebreak():
    assert match_result(30, 20)['A'] == 1
    r = match_result(25, 25, (15, 5), (12, 4))
    pa, pb = F(10, 20), F(8, 20)
    assert r == {'A': pa * (1 - pb), 'B': pb * (1 - pa), 'tie': pa * pb + (1 - pa) * (1 - pb)}
    assert sum(r.values()) == 1
