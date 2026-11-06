"""Board and movement: shapes, blocking, Quick Step, Sprint, locks, arrow lines, screens."""
import pytest
from conftest import mk, P, dests

from playmaker_engine import board as B
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply, force
from playmaker_engine.rules_config import with_rules

FAR_O = ['A14', 'C14', 'E14', 'G14']
FAR_X = ['Q14', 'O14', 'M14', 'K14']


def offence(o1, extra_x=(), arrows=(), off='Five Out', **kw):
    xs = (list(extra_x) + (FAR_X + ['Q12'])[len(extra_x):])[:5]
    arr = list(arrows) + ['N'] * (5 - len(arrows))
    return mk([o1] + FAR_O, xs, arr, off=off, **kw)


def rel(state, piece, kind, side='O'):
    start = (state.o if side == 'O' else state.x)[piece]
    return {(a.dest[0] - start[0], a.dest[1] - start[1]) for a in legal_actions(state)
            if a.kind == kind and a.piece == piece and a.side == side and a.dest != start}


MOVE_SHAPE = ({(0, k) for k in (1, 2, 3)} | {(0, -k) for k in (1, 2, 3)} | {(k, 0) for k in (1, 2, 3)}
              | {(-k, 0) for k in (1, 2, 3)} | {(a * k, b * k) for a in (1, -1) for b in (1, -1) for k in (1, 2)}
              | {(a, 2 * b) for a in (1, -1) for b in (1, -1)} | {(2 * a, b) for a in (1, -1) for b in (1, -1)})


def test_move_shapes_exact():
    s = offence('I7')
    assert rel(s, 0, 'move') == MOVE_SHAPE
    for bad in [(0, 4), (3, 3), (3, 1), (1, 3), (4, 0)]:
        assert bad not in rel(s, 0, 'move')


def test_move_never_through_or_onto_a_piece():
    s = offence('I7', ['I8', 'Q13'])
    r = rel(s, 0, 'move')
    assert (0, 1) not in r and (0, 2) not in r and (0, 3) not in r      # straight north blocked at I8
    assert (0, -3) in r


def test_one_plus_one_either_order():
    # Target J9 = (1, 2): N then NE via I8, or NE then N via J8.
    s = offence('I7', ['I8', 'Q13'])
    assert (1, 2) in rel(s, 0, 'move')                                  # J8 route still open
    s2 = offence('I7', ['I8', 'J8'])
    assert (1, 2) not in rel(s2, 0, 'move')                             # both routes blocked
    s3 = offence('I7', ['I8', 'Q13'], rules=with_rules(move_either_order=False))
    assert (1, 2) not in rel(s3, 0, 'move')                             # straight-first only


def test_quick_step():
    s = offence('I7', off='Run and Gun')                                # O1 apgB: Quick Step 2
    r = rel(s, 0, 'qs')
    assert (0, 2) in r and (2, 2) in r and (0, 1) in r
    assert (0, 3) not in r and (1, 2) not in r                          # not 3, not bent
    s0 = mk(['A14', 'C14', 'E14', 'G14', 'I7'], FAR_X + ['Q12'], ['N'] * 5)
    assert rel(s0, 4, 'qs') == set()                                    # O5 stcC: Quick Step 0


def test_locked_player_quick_steps_but_does_not_move():
    s = offence('I7', lock_o=1)
    assert rel(s, 0, 'move') == set() and rel(s, 0, 'sprint') == set()
    assert rel(s, 0, 'qs')


def test_sprint_length_and_move_use():
    s = offence('I7', off='Run and Gun')                                # Quick Step 2
    r = rel(s, 0, 'sprint')
    assert (0, 5) in r and (0, 6) not in r and (4, 4) in r and (5, 5) not in r
    assert (1, 2) not in r                                              # one straight line
    s2 = apply(s, Action('sprint', 'O', 0, P('I12')))
    assert rel(s2, 0, 'move') == set() and rel(s2, 0, 'sprint') == set()
    assert s2.count('O', 'qs') == 1


def test_quick_step_limit_counts_sprints():
    s = offence('I7', off='Run and Gun')
    s = apply(s, Action('sprint', 'O', 0, P('I12')))
    s = apply(s, Action('qs', 'O', 1, P('C13')))                       # second Quick Step: turn over
    assert s.side == 'X'
    s = apply(s, Action('end_turn', 'X')) if s.turn_n else apply(s, Action('pause', 'X'))
    assert s.side == 'O' and rel(s, 2, 'qs') == set() and rel(s, 2, 'sprint') == set()


def test_move_once_per_player():
    s = offence('I7')
    s = apply(s, Action('move', 'O', 0, P('I8')))
    assert rel(s, 0, 'move') == set()
    assert rel(s, 1, 'move')


def test_defender_arrow_move_quickstep_sprint():
    s = mk(FAR_O + ['A12'], ['I7', 'Q13', 'O14', 'M14', 'K14'], ['N'] * 5, side='X')
    acts = legal_actions(s)
    turns = [a for a in acts if a.kind == 'move' and a.piece == 0 and a.dest == P('I7')]
    assert {a.arrow for a in turns} == set(range(8)) - {0}               # turn on the spot, uses the Move
    s2 = apply(s, Action('move', 'X', 0, P('I7'), 2))
    assert s2.arrows[0] == 2 and s2.moved('X', 0)
    assert not [a for a in legal_actions(s2) if a.piece == 0 and a.kind in ('move', 'sprint')]
    s3 = apply(s, Action('qs', 'X', 0, P('J8')))                         # Quick Step keeps the arrow
    assert s3.arrows[0] == 0
    s4 = apply(s, Action('sprint', 'X', 0, P('L4')))                     # Sprint SE: arrow faces SE
    assert s4.arrows[0] == 3


def test_locked_defender_cannot_turn_arrow():
    s = mk(FAR_O + ['A12'], ['I7', 'Q13', 'O14', 'M14', 'K14'], ['N'] * 5, side='X', lock_x=1)
    assert not [a for a in legal_actions(s) if a.piece == 0 and a.kind in ('move', 'sprint')]
    assert [a for a in legal_actions(s) if a.piece == 0 and a.kind == 'qs']


# ---- arrow line -----------------------------------------------------------------

def arrow_state(ball=0, beaten=()):
    # Carrier O1 at H8; X1 at I8 (adjacent) arrow N: the ray runs I9, I10, ... to the edge.
    return mk(['H8'] + FAR_O, ['I8'] + FAR_X, ['N'] * 5, ball=ball, beaten=beaten)


def test_carrier_cannot_cross_adjacent_arrow_line():
    d = dests(legal_actions(arrow_state()), 'move', 0)
    assert 'J10' not in d and 'J9' not in d                             # would cross the ray
    assert 'I10' in d and 'I9' in d                                     # stepping onto it is fine
    assert 'J6' in d                                                    # behind the defender: no ray


def test_arrow_line_only_binds_the_carrier_and_dribble_frees_it():
    d = dests(legal_actions(arrow_state(ball=1)), 'move', 0)            # O1 without the ball
    assert 'J10' in d
    d2 = dests(legal_actions(arrow_state(beaten=((0, 0),))), 'move', 0)  # won a Dribble vs X1
    assert 'J10' in d2


def test_arrow_line_strict_crossing_unit():
    D, n = (8, 8), 0
    assert B.path_crosses_ray([(7, 8), (8, 9), (9, 10)], D, n)
    assert not B.path_crosses_ray([(7, 8), (7, 9), (8, 10)], D, n)     # onto the line only
    assert not B.path_crosses_ray([(7, 8), (8, 7), (9, 6)], D, n)      # passes behind the defender
    assert B.path_crosses_ray([(7, 9), (9, 9)], D, n)                  # straight across
    assert not B.path_crosses_ray([(7, 9), (8, 10), (7, 11)], D, n)    # touch and come back


# ---- screen geometry ------------------------------------------------------------

def screen_state(xpos, beaten=0, rule=None):
    # Screener O2 at I6 with its T to the south: the T square is I5.
    rules = with_rules(screen_rule=rule) if rule else None
    return mk(['A14', 'I6', 'E14', 'G14', 'C14'], ['Q14', xpos, 'O14', 'M14', 'K14'], ['N'] * 5,
              side='X', screens=((1, 4, False, beaten),), rules=rules)


def test_screen_t_square_exact_squares():
    # X2 (Quick Step 1) standing on the T square I5.
    assert dests(legal_actions(screen_state('I5')), 'qs', 1, 'X') == {'J5', 'I4', 'H5'}
    # From H5 the diagonal to I4 cuts the T square's corner: banned. Everything else is open.
    assert dests(legal_actions(screen_state('H5')), 'qs', 1, 'X') == {'H6', 'I5', 'H4', 'G4', 'G5', 'G6'}


def test_screen_rule_alternative_from_t_only():
    d = dests(legal_actions(screen_state('H5', rule='from_t_only')), 'qs', 1, 'X')
    assert 'I4' in d
    assert dests(legal_actions(screen_state('I5', rule='from_t_only')), 'qs', 1, 'X') == {'J5', 'I4', 'H5'}


def test_beaten_screen_cross_t_but_not_stop():
    held = dests(legal_actions(screen_state('H4')), 'move', 1, 'X')
    assert 'J6' not in held                 # H4 -> I5 -> J6 goes diagonally from the T square
    assert 'I5' in held                     # may still step onto T
    beat = dests(legal_actions(screen_state('H4', beaten=0b10)), 'move', 1, 'X')
    assert 'J6' in beat                     # crossed the T square
    assert 'I5' not in beat                 # but can't stop on it


def test_screener_cannot_move_and_flips_back_after_next_offence_turn():
    s = mk(['I11', 'I6', 'E14', 'G14', 'C14'], ['Q14', 'I5', 'O14', 'M14', 'K14'], ['N'] * 5)
    s = apply(s, Action('screen', 'O', 1, target=4))
    assert s.side == 'X' and s.screen_of(1)
    s = apply(s, Action('pause', 'X'))
    assert not [a for a in legal_actions(s) if a.piece == 1 and a.kind in ('move', 'qs', 'sprint')]
    s = apply(s, Action('move', 'O', 0, P('I12')))
    s = apply(s, Action('end_turn', 'O'))
    assert s.screen_of(1) is None           # flipped back after the offence's next turn


def test_post_seal_move_then_screen_same_turn():
    s = mk(['I11', 'H6', 'E14', 'G14', 'C14'], ['Q14', 'I6', 'O14', 'M14', 'K14'], ['N'] * 5)
    s = apply(s, Action('move', 'O', 1, P('I7')))        # round the defender
    assert s.side == 'O'
    s = apply(s, Action('screen', 'O', 1, target=4))     # T on the defender at I6
    assert s.side == 'X' and B.add(s.o[1], B.DIRS[4]) == s.x[1]


# ---- OQ-52 (ruled): one Quick Step per player per phase; a Sprint uses it -------------------------

def _first(s, **kw):
    from playmaker_engine.actions import legal_actions
    return next(a for a in legal_actions(s) if all(getattr(a, k) == v for k, v in kw.items()))


def _has(s, **kw):
    from playmaker_engine.actions import legal_actions
    return any(all(getattr(a, k) == v for k, v in kw.items()) for a in legal_actions(s))


def test_no_sprint_after_a_quick_step_and_no_quick_step_after_a_sprint():
    from playmaker_engine.scenarios import scenario_state
    from playmaker_engine.resolve import apply
    s = scenario_state(6)
    t = apply(s, _first(s, kind='qs', piece=1))
    assert not _has(t, kind='sprint', piece=1) and not _has(t, kind='qs', piece=1)
    assert _has(t, kind='move', piece=1)                     # Quick Step then Move: still fine
    assert _has(t, kind='qs', piece=2)                        # another player's Quick Step: fine
    u = apply(s, _first(s, kind='sprint', piece=1))
    assert not _has(u, kind='qs', piece=1) and not _has(u, kind='move', piece=1)
    m = apply(s, _first(s, kind='move', piece=1))
    assert _has(m, kind='qs', piece=1) and not _has(m, kind='sprint', piece=1)   # Move then Quick Step: fine


def test_the_side_limit_of_two_still_applies_and_the_phase_reset_clears_it():
    from playmaker_engine.scenarios import scenario_state
    from playmaker_engine.resolve import apply, new_phase
    s = scenario_state(6)
    s = apply(s, _first(s, kind='qs', piece=1))
    s = apply(s, _first(s, kind='qs', piece=2))
    if s.side == 'O':
        assert not _has(s, kind='qs') and not _has(s, kind='sprint')
    r = new_phase(s, 4)
    assert r.qs_o == 0 and r.qs_x == 0


def test_the_defence_follows_the_same_rule_in_play_and_in_the_reaction():
    from playmaker_engine.scenarios import scenario_state
    from playmaker_engine.resolve import apply
    s = scenario_state(6)
    s = apply(s, _first(s, kind='hesitate'))
    assert s.side == 'X'
    t = apply(s, _first(s, kind='qs', side='X', piece=0))
    if t.side == 'X':
        assert not _has(t, kind='sprint', piece=0) and not _has(t, kind='qs', piece=0)
    # reaction to a declared shot
    s = scenario_state(6)
    s = apply(s, _first(s, kind='move', piece=0, dest=(9, 10)))
    s = apply(s, _first(s, kind='shot'))
    assert s.stage == 'reaction'
    qs = [a for a in __import__('playmaker_engine.actions', fromlist=['legal_actions']).legal_actions(s) if a.kind == 'qs']
    if qs:
        t = apply(s, qs[0])
        if t.stage == 'reaction':
            assert not _has(t, kind='sprint', piece=qs[0].piece) and not _has(t, kind='qs', piece=qs[0].piece)


def _phase_moves_ok(log):
    """In every phase each player Quick Steps or Sprints at most once, and at most 2 per side."""
    used = {}
    for before, a, after in log:
        if before.phase != getattr(after, 'phase', before.phase):
            pass
        if a.kind in ('qs', 'sprint'):
            key = (before.phase, a.side)
            used.setdefault(key, []).append(a.piece)
    return all(len(v) == len(set(v)) and len(v) <= 2 for v in used.values()), used


@pytest.mark.parametrize('who', ['random', 'greedy', 'rookie', 'starter', 'allstar'])
def test_every_player_type_follows_the_movement_rules(who):
    from playmaker_engine.scenarios import scenario_state, SCENARIOS
    from playmaker_engine.policies import play, RandomPolicy, GreedyPolicy
    from playmaker_engine.computer import Computer
    cards = sorted(SCENARIOS) if who in ('random', 'greedy') else [1, 6, 7, 13]
    for n in cards:
        for seed in (1, 2) if who in ('random', 'greedy') else (1,):
            if who == 'random':
                o, x = RandomPolicy(seed), RandomPolicy(seed + 1)
            elif who == 'greedy':
                o, x = GreedyPolicy(), GreedyPolicy()
            else:
                o, x = Computer('O', who, seed=seed, budget_s=0.3), Computer('X', who, seed=seed, budget_s=0.3)
            log = []
            play(scenario_state(n), o, x, seed=seed, check=lambda b, a, s: log.append((b, a, s)))
            ok, used = _phase_moves_ok(log)
            assert ok, (who, n, used)


def test_the_solver_reach_never_uses_two_quick_steps_for_one_defender():
    from playmaker_engine.scenarios import scenario_state
    from playmaker_engine.solver import defender_reach
    for n in (6, 7, 13, 15):
        s = scenario_state(n)
        for d in range(5):
            free, fixed = defender_reach(s, d, 2)
            seqs = list(free.values()) + [q for v in fixed.values() for q in v.values()]
            assert all(sum(k in ('qs', 'sprint') for k, _ in seq) <= 1 for seq in seqs), (n, d)
        used = s.with_(qs_x=0b11111)
        for d in range(5):
            free, fixed = defender_reach(used, d, 2)
            seqs = list(free.values()) + [q for v in fixed.values() for q in v.values()]
            assert all(not any(k in ('qs', 'sprint') for k, _ in seq) for seq in seqs)


def test_the_ball_carrier_has_no_legal_screen():
    """Ruled in step 3i (OQ-63): the ball carrier can't Screen; teammates still can."""
    from playmaker_engine import rules_config as RC
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.soak import golden_setup
    s = golden_setup()
    acts = legal_actions(s)
    assert not any(a.kind == 'screen' and a.piece == s.ball for a in acts)
    assert any(a.kind == 'screen' and a.piece != s.ball for a in acts)
    old = s.with_(ctx=s.ctx.__class__(s.ctx.off, s.ctx.dfn, RC.with_rules(carrier_can_screen=True), s.ctx.title, s.ctx.kind,
                                      s.ctx.scenario, s.ctx.card_clock, s.ctx.inbounder, s.ctx.coach_call, s.ctx.three_only,
                                      s.ctx.two_or_three, s.ctx.hold_for_one, s.ctx.off_team, s.ctx.def_team))
    assert any(a.kind == 'screen' and a.piece == old.ball for a in legal_actions(old))
