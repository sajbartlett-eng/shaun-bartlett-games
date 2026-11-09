"""Step 3h: two rule settings under test (not adopted). arrow_mode 'wedge' gives each defender two arrow
lines 45 degrees apart; contest_geometry 'wedge_mirror' / 'rim_distance' make facing gate the contest and
position set its quality (Front full, Side a foul roll, Behind a foul roll and the -3). With the defaults
nothing changes (the golden solver search is identical)."""
import pytest
import json
import os

from conftest import P
from playmaker_engine import board as B
from playmaker_engine import geometry as G
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, intercept_status
from playmaker_engine.resolve import apply
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import contest_options

WEDGE = RC.with_rules(arrow_mode='wedge')
MIRROR = RC.with_rules(arrow_mode='wedge', contest_geometry='wedge_mirror')
RIMD = RC.with_rules(arrow_mode='wedge', contest_geometry='rim_distance')
RIMD1 = RC.with_rules(contest_geometry='rim_distance')
D = {n: i for i, n in enumerate(B.DIR_NAMES)}


def board(o, x, arrows, rules=None, ball=0, **kw):
    s = game_state('Five Out', 'High-Low', o, x, arrows, ball=ball, rules=rules, check=False)
    return s.with_(**kw) if kw else s


# ---- the wedge ------------------------------------------------------------------------------------

def test_a_pass_can_be_intercepted_across_either_line_and_only_one_needs_to_cross():
    """O1 I11 passes to O2 C9; X1 on F7, off the line. Its N line crosses the pass, its NE line doesn't."""
    o, x = ['I11', 'C9', 'O9', 'A3', 'Q3'], ['F7', 'P2', 'N4', 'K4', 'Q6']
    pend = lambda rules, a: board(o, x, [a, 'N', 'N', 'N', 'N'], rules).with_(pending=(0, 1), side='X')
    assert intercept_status(pend(None, 'N'), 0) == 'approach'          # single arrow N: crosses
    assert intercept_status(pend(None, 'NE'), 0) is None               # single arrow NE: misses
    assert intercept_status(pend(WEDGE, 'N'), 0) == 'approach'         # wedge N+NE: the first line crosses
    assert intercept_status(pend(WEDGE, 'NW'), 0) == 'approach'        # wedge NW+N: the second line crosses
    assert intercept_status(pend(WEDGE, 'NE'), 0) is None              # wedge NE+E: neither crosses


def test_a_drive_across_either_line_of_an_adjacent_defender_needs_a_dribble():
    """O1 on I11 with X1 next to it on I10. The drive I11-J10-K9 crosses X1's E line, not its SE line."""
    o, x = ['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4']
    drive = Action('move', 'O', 0, P('K9'))
    can = lambda rules, a: drive in legal_actions(board(o, x, [a, 'NE', 'NW', 'N', 'N'], rules))
    assert not can(None, 'E') and can(None, 'SE')                     # single arrow: E blocks, SE doesn't
    assert not can(WEDGE, 'E')                                         # wedge E+SE: the first line blocks
    assert not can(WEDGE, 'NE')                                        # wedge NE+E: the second line blocks
    assert can(WEDGE, 'SE')                                            # wedge SE+S: neither does


def test_a_sprint_sets_one_edge_to_the_run_and_the_defender_picks_the_other():
    o, x = ['I11', 'C9', 'O9', 'A3', 'Q3'], ['K4', 'D8', 'N8', 'G4', 'I10']      # X1 (Quick Step 2) on K4
    s = board(o, x, ['S', 'NE', 'NW', 'N', 'N'], WEDGE).with_(side='X')
    sprints = [a for a in legal_actions(s) if a.kind == 'sprint' and a.piece == 0]
    assert sprints
    dest = sprints[0].dest
    both = [a for a in sprints if a.dest == dest]
    assert len(both) == 2                                              # the other edge clockwise or anticlockwise
    from playmaker_engine.actions import sprint_dir
    run = sprint_dir(s.x[0], dest)
    ends = {G.lines(WEDGE, apply(s, a).arrows[0]) for a in both}
    assert all(run in e for e in ends) and len(ends) == 2, ends       # the run is an edge either way
    single = board(o, x, ['S', 'NE', 'NW', 'N', 'N'], RC.with_rules(arrow_mode='single')).with_(side='X')
    assert len([a for a in legal_actions(single) if a.kind == 'sprint' and a.piece == 0 and a.dest == dest]) == 1


def test_a_quick_step_and_a_locked_defender_cannot_rotate_the_wedge():
    o, x = ['I11', 'C9', 'O9', 'A3', 'Q3'], ['K4', 'D8', 'N8', 'G4', 'I10']
    s = board(o, x, ['S', 'NE', 'NW', 'N', 'N'], WEDGE).with_(side='X')
    qs = next(a for a in legal_actions(s) if a.kind == 'qs' and a.piece == 0)
    assert apply(s, qs).arrows[0] == s.arrows[0]
    locked = s.with_(lock_x=1 << 0)
    assert not any(a.piece == 0 and a.kind in ('move', 'sprint') for a in legal_actions(locked))


# ---- the gate ---------------------------------------------------------------------------------------

def test_with_a_new_geometry_a_defender_whose_lines_miss_the_shooter_cannot_contest_until_he_turns():
    """O1 shoots from I8; X1 stands on I9 facing N (away). Under the current rules that's a foul-roll
    contest; under the new geometries no contest at all, until the reaction turns X1 to face I8."""
    o, x = ['I8', 'C9', 'O9', 'A3', 'Q3'], ['I9', 'D8', 'N8', 'G4', 'N4']
    for rules in (None, MIRROR, RIMD, RIMD1):
        s = board(o, x, ['N', 'NE', 'NW', 'N', 'N'], rules).with_(stage='contest', side='X', shot='mid')
        mine = [opt for opt in contest_options(s, 0, 'mid') if opt.defender == 0]
        if rules is None:
            assert mine and not mine[0].clean                          # the old foul-roll contest
            continue
        assert not mine, rules
        turned = s.with_(arrows=(D['S'],) + s.arrows[1:])               # after a reaction Move in place
        assert any(opt.defender == 0 for opt in contest_options(turned, 0, 'mid')), rules


# ---- the categories ---------------------------------------------------------------------------------

def test_categories_front_side_behind_under_both_geometries():
    rim, cases = None, [
        # (defender, arrow (wedge index), shooter, expected)
        ('I7', 'N', 'I8', G.FRONT),     # a help defender who sprinted out of the paint (run N), facing out
        ('I9', 'S', 'I8', G.BEHIND),    # beaten, chasing from behind
        ('H8', 'E', 'I8', G.SIDE),      # beside the shooter, level with him
    ]
    for rules in (MIRROR, RIMD):
        for d, a, sh, want in cases:
            assert G.category(rules, P(d), D[a], P(sh)) == want, (rules.contest_geometry, d, a, sh)
            assert G.terms(rules, P(d), D[a], P(sh))[0]                 # facing: eligible


def test_a_help_defender_sprinting_out_of_the_paint_lands_front():
    o, x = ['I8', 'C9', 'O9', 'A3', 'Q3'], ['I4', 'D8', 'N8', 'G4', 'N4']
    for rules in (MIRROR, RIMD):
        s = board(o, x, ['N', 'NE', 'NW', 'N', 'N'], rules).with_(side='X', stage='reaction', shot='mid')
        sp = [a for a in legal_actions(s) if a.kind == 'sprint' and a.piece == 0 and a.dest == P('I7')]
        assert sp, [str(a) for a in legal_actions(s) if a.piece == 0][:10]
        cats = set()
        for a in sp:
            t = apply(s, a)
            for opt in contest_options(t.with_(stage='contest'), 0, 'mid'):
                if opt.defender == 0:
                    cats.add(opt.category)
        assert G.FRONT in cats, (rules.contest_geometry, cats)


def test_a_shooter_on_the_rim_square_never_meets_a_front_contest():
    """I2: nobody is nearer the rim than the shooter, so every contest is Side or Behind (on this grid,
    with distance in king moves, all eight neighbours are Behind)."""
    for rules in (MIRROR, RIMD):
        for sq in ('H1', 'I1', 'J1', 'H2', 'J2', 'H3', 'I3', 'J3'):
            dp = P(sq)
            for a in range(8):
                ok, foul, pen, cat = G.terms(rules, dp, a, P('I2'))
                if ok:
                    assert cat in (G.SIDE, G.BEHIND), (rules.contest_geometry, sq, a, cat)


def test_the_minus_three_is_for_behind_only_and_never_twice():
    o = ['I8', 'C9', 'O9', 'A3', 'Q3']
    for rules in (MIRROR, RIMD):
        for d, a, want in (('I9', 'S', G.BEHIND), ('I7', 'N', G.FRONT), ('H8', 'E', G.SIDE)):
            s = board(o, [d, 'D8', 'N8', 'G4', 'N4'], [a, 'NE', 'NW', 'N', 'N'], rules).with_(stage='contest', side='X', shot='mid')
            opt = next(x for x in contest_options(s, 0, 'mid') if x.defender == 0)
            raw = s.ctx.dfn[0].con('mid')
            assert opt.category == want
            assert opt.contest == (max(0, raw - 3) if want == G.BEHIND else raw), (rules.contest_geometry, d, opt)
            assert opt.clean == (want == G.FRONT)                      # Side and Behind roll for the foul
    # under the current rules the -3 is the old 'further from the rim' rule, once
    s = board(o, ['I9', 'D8', 'N8', 'G4', 'N4'], ['S', 'NE', 'NW', 'N', 'N']).with_(stage='contest', side='X', shot='mid')
    opt = next(x for x in contest_options(s, 0, 'mid') if x.defender == 0)
    assert opt.contest == max(0, s.ctx.dfn[0].con('mid') - 3) and opt.clean


def test_wedge_mirror_needs_the_wedge():
    import pytest
    with pytest.raises(ValueError):
        G.check(RC.with_rules(contest_geometry='wedge_mirror', arrow_mode='single'))
    G.check(MIRROR)


# ---- the computer and the solver read the same helper -------------------------------------------------

