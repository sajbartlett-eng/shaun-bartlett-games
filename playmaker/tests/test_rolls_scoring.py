"""Chance nodes, intercept geometry, Dribble, Challenge, Steal, contests and scoring."""
import pytest
from fractions import Fraction as F

from conftest import mk, P

from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import settle, apply, force, ChanceNode
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


@pytest.mark.usefixtures('legacy_rules')   # recorded under the rules before the step 3i follow-up rulings
def test_challenge_screen():
    s = base(side='X', screens=((2, 5, False, 0),))         # O3 at O9, T to the SW on X3 at N8
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
    o = s.ctx.off[0]
    assert foul.stage == 'over' and score(foul).free_throws == max(2 * o.r['free_throw'], 2 * o.shot('long'))
    stolen = force(st, 'no foul', 'stolen')
    assert stolen.result.kind == 'steal' and score(stolen).total == -5
    kept = settle(force(st, 'no foul', 'kept'))
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


def test_declared_negative_shot_floors_at_zero():
    # Ruling OQ-5. Twin Towers O4 (three 6) on Q3 v Shoot and Protect X2 tndA (con_three 7), arrow on,
    # nearer the rim: 3 x (6 - 7) = -3 scores 0. With the old setting it scores -3.
    sq = (['I14', 'A14', 'C14', 'Q3', 'E14'], ['A13', 'P3', 'M14', 'K14', 'O14'], ['N', 'E', 'N', 'N', 'N'])
    s = mk(*sq, ball=3, off='Twin Towers', dfn='Shoot and Protect')
    end = settle(apply(apply(s, Action('shot', 'O', 3, shot='three')), Action('end_turn', 'X')))
    assert end.result.shot_value == 0 and score(end).total == 0
    s2 = mk(*sq, ball=3, off='Twin Towers', dfn='Shoot and Protect', rules=with_rules(floor_declared_shot=False))
    end2 = settle(apply(apply(s2, Action('shot', 'O', 3, shot='three')), Action('end_turn', 'X')))
    assert end2.result.shot_value == -3 and score(end2).total == -3


def test_contest_never_below_zero():
    # Ruling OQ-20: a far defender with contest 2 contests at 0, not -1.
    s = shooter_state('I10', 'S', osq='I9')            # X1 cgA further from the rim than the shooter
    c = s.ctx.dfn[0].con('long')
    got = [o for o in contest_options(s, 0, 'long') if o.defender == 0][0].contest
    assert got == max(0, c - 3)
    from playmaker_engine.scoring import contest_rating
    from playmaker_engine.cards import CARDS
    low = min(CARDS.values(), key=lambda k: k.con('three'))
    assert contest_rating(low, 'three', P('I12'), P('I10'), s.ctx.rules) == 0
    assert contest_rating(low, 'three', P('I12'), P('I10'), with_rules(floor_contest_zero=False)) == low.con('three') - 3


def test_and_one_foul_scores_the_better_of_ft_and_open_shot():
    # Three by Five Out O1: the foul scores the higher of 3 x FT and 3 x the three rating.
    s = mk(['J10', 'C9', 'O9', 'A3', 'Q3'], ['J9', 'D8', 'N8', 'G4', 'N4'], ['E', 'NE', 'NW', 'N', 'N'],
           off='Five Out')
    o = s.ctx.off[0]
    opt = [x for x in contest_options(s, 0, 'three') if x.defender == 0][0]
    assert opt.ft == max(3 * o.r['free_throw'], 3 * o.shot('three'))
    # Post shot where the open look beats the free throws: High-Low O5 pscA post 18 -> 36 v 2 x FT 14 = 28.
    s2 = mk(['I4', 'C9', 'O9', 'A3', 'A14'], ['I3', 'D8', 'N8', 'G4', 'N4'], ['E', 'NE', 'NW', 'N', 'N'],
            off='High-Low', dfn='Five Out')
    o2 = s2.ctx.off[0]
    opt2 = [x for x in contest_options(s2, 0, 'post') if x.defender == 0][0]
    assert opt2.ft == max(2 * o2.r['free_throw'], 2 * o2.shot('post'))
    r = apply(s2, Action('shot', 'O', 0, shot='post'))
    from playmaker_engine.resolve import resolve_shot
    node = resolve_shot(r)
    if isinstance(node, ChanceNode):
        f = force(node, 'foul')
        assert f.result.free_throws == opt2.ft
        assert f.result.and_one == (2 * o2.shot('post') > 2 * o2.r['free_throw'])
    s3 = mk(['I4', 'C9', 'O9', 'A3', 'A14'], ['I3', 'D8', 'N8', 'G4', 'N4'], ['E', 'NE', 'NW', 'N', 'N'],
            off='High-Low', dfn='Five Out', rules=with_rules(and_one=False))
    old = [x for x in contest_options(s3, 0, 'post') if x.defender == 0][0]
    assert old.ft == 2 * o2.r['free_throw']


def test_and_one_covers_steal_foul_after_declared_shot():
    s = base(o=['I9', 'C9', 'O9', 'A3', 'Q3'], x=['I8', 'D8', 'N8', 'G4', 'N4'])
    r = apply(apply(s, Action('shot', 'O', 0, shot='long')), Action('move', 'X', 0, P('I8'), 0))
    foul = force(apply(r, Action('steal', 'X', 0)), 'foul')
    o = s.ctx.off[0]
    assert foul.result.free_throws == max(2 * o.r['free_throw'], 2 * o.shot('long'))


def test_matchup_check_every_pairing():
    from playmaker_engine.matchups import closeout_report
    rep = closeout_report()
    print(rep['summary'])
    assert rep['total'] == 75 * 75 * 7
    assert rep['foul_breaks'] == 0, rep['examples']          # a foul never beats leaving the shot open
    assert rep['clean_breaks'] == 0                          # a clean closeout always pays (or ties)
    assert 0 < rep['share'] < 1
    old = closeout_report(with_rules(and_one=False))
    assert old['foul_breaks'] > 0                            # without the and-one, fouling can pay


# ---- bands, Coach's Call, match ------------------------------------------------------------

def test_bands():
    assert [band(v) for v in (30, 29, 25, 24, 20, 19, 15, 14, -5)] == \
        ['Excellent', 'Great', 'Great', 'Good', 'Good', 'Okay', 'Okay', 'Poor', 'Poor']


def test_coach_call_bonus():
    from playmaker_engine.scenarios import scenario_state
    s = scenario_state(8, target=0)
    # put O1 on a three square, nobody near, and shoot
    s = s.with_(o=(P('J10'),) + s.o[1:], x=(P('A14'),) + s.x[1:])
    end = settle(apply(apply(s, Action('shot', 'O', 0, shot='three')), Action('end_turn', 'X')))
    sc = score(end)
    assert sc.coach_bonus == RC.COACH_BONUS[band(sc.look)] and sc.total == sc.shot_value + sc.coach_bonus
    s2 = scenario_state(8, target=1).with_(o=(P('J10'),) + s.o[1:], x=(P('A14'),) + s.x[1:])
    end2 = settle(apply(apply(s2, Action('shot', 'O', 0, shot='three')), Action('end_turn', 'X')))
    assert score(end2).coach_bonus == 0


def test_match_tiebreak():
    assert match_result(30, 20)['A'] == 1
    r = match_result(25, 25, (15, 5), (12, 4))
    pa, pb = F(10, 20), F(8, 20)
    assert r == {'A': pa * (1 - pb), 'B': pb * (1 - pa), 'tie': pa * pb + (1 - pa) * (1 - pb)}
    assert sum(r.values()) == 1


# ---- rulings 16 and 17 ---------------------------------------------------------------------

def test_locked_carrier_cannot_dribble():
    s = base(lock_o=0b1)                                     # O1 has the ball, X1 adjacent at I10
    k = {a.kind for a in legal_actions(s)}
    assert 'dribble' not in k and 'pass' in k
    assert 'dribble' in {a.kind for a in legal_actions(base())}
    assert 'dribble' in {a.kind for a in legal_actions(base(lock_o=0b1, rules=with_rules(locked_can_dribble=True)))}


def test_only_the_defender_on_the_t_square_may_challenge():
    s = base(side='X', screens=((2, 5, False, 0),))         # O3 at O9, T on N8 where X3 stands
    who = [a.piece for a in legal_actions(s) if a.kind == 'challenge']
    assert who == [2]
    s_off = base(side='X', screens=((2, 4, False, 0),))     # T on O8: nobody there
    assert not [a for a in legal_actions(s_off) if a.kind == 'challenge']
    s_any = base(side='X', screens=((2, 4, False, 0),), rules=with_rules(challenge_who='any'))
    assert len([a for a in legal_actions(s_any) if a.kind == 'challenge']) == 5


# ---- step 3b: the contest and the forced-shot type are player decisions -------------------------

def _declared(xsq, arrow, osq='I9', shot='long', extra_x=None):
    x = [xsq, 'D8', 'N8', 'G4', 'N4']
    arr = [arrow, 'NE', 'NW', 'N', 'N']
    if extra_x:
        x[1], arr[1] = extra_x
    s = base(o=[osq, 'C9', 'O9', 'A3', 'Q3'], x=x, arr=arr)
    return apply(apply(s, Action('shot', 'O', 0, shot=shot)), Action('end_turn', 'X'))


def test_contest_decision_offers_every_adjacent_defender_and_no_contest():
    # X1 on I8 (arrow N, on the shooter at I9: clean); X2 on H9 (arrow N, off the shooter: foul roll)
    node = _declared('I8', 'N', extra_x=('H9', 'N'))
    assert node.stage == 'contest' and node.side == 'X'
    acts = legal_actions(node)
    assert sorted(a.piece for a in acts) == [-1, 0, 1]
    opts = {o.defender: o for o in contest_options(node, 0, 'long')}
    assert opts[0].clean and not opts[1].clean and opts[1].p_foul == F(node.ctx.dfn[1].r['foul_contest'], 20)
    # each choice reproduces the old outcome for that contester
    clean = apply(node, Action('contest', 'X', 0))
    assert clean.stage == 'over' and clean.result.contester == 0 and clean.result.shot_value == opts[0].value
    side = apply(node, Action('contest', 'X', 1))
    assert isinstance(side, ChanceNode) and {l for _, l, _ in side.outcomes} == {'foul', 'no foul'}
    none = apply(node, Action('contest', 'X', -1))
    assert none.result.contester == -1 and none.result.shot_value == opts[-1].value
    # the old automatic minimum is one of the player's choices
    auto = choose_contest(node, 0, 'long')
    assert auto.defender in opts


def test_contest_setting_alternatives_still_work():
    s = base(o=['I9', 'C9', 'O9', 'A3', 'Q3'], x=['I8', 'D8', 'N8', 'G4', 'N4'], rules=with_rules(contest_choice='min_value'))
    end = apply(apply(s, Action('shot', 'O', 0, shot='long')), Action('end_turn', 'X'))
    assert not isinstance(end, ChanceNode) and end.stage == 'over'


def test_forced_shot_type_is_the_offence_choice():
    # O1 on I4 (rim zone: layup, dunk, post) when the clock runs out
    s = base(o=['I4', 'C9', 'O9', 'A3', 'Q3'], x=['A14', 'D8', 'N8', 'G7', 'N4'], clock=2, side='X', tok_x=1)
    node = apply(s, Action('move', 'X', 3, P('G8'), 0))
    assert node.stage == 'forced' and node.side == 'O'
    acts = legal_actions(node)
    assert [a.shot for a in acts] == list(RC.ZONE_SHOTS['K'])
    nxt = apply(node, next(a for a in acts if a.shot == 'post'))
    assert nxt.stage == 'contest' and nxt.forced and nxt.shot == 'post'
    end = apply(nxt, Action('contest', 'X', -1))
    assert end.result.kind == 'forced' and end.result.shot_type == 'post' and score(end).turnovers == 1
    alt = base(o=['I4', 'C9', 'O9', 'A3', 'Q3'], x=['A14', 'D8', 'N8', 'G7', 'N4'], clock=2, side='X', tok_x=1,
               rules=with_rules(forced_shot_choice='best', contest_choice='min_value'))
    assert apply(alt, Action('move', 'X', 3, P('G8'), 0)).stage == 'over'
