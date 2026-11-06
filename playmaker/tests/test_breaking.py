"""Step 3i: an offence that breaks the arrows. Defender capacity (C1), the goal-directed planner (C2a), the
off-ball movement templates (C2), the overloaded defender (C3), the defence's follow-or-stay choice (C5),
the off-ball threat in the defence's evaluation (Part B fix 1), and the late_closeout rule test."""
import pytest
from conftest import P

from playmaker_engine import board as B
from playmaker_engine import computer as C
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, MOVEMENT
from playmaker_engine.advantage import advantages, describe
from playmaker_engine.capacity import capacity, lane_reach, lanes, help_reach, closeout_reach
from playmaker_engine.cards import TEAMS
from playmaker_engine.planner import goals, defence_objectives
from playmaker_engine.resolve import apply, ChanceNode, force
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import contest_options
from playmaker_engine.state import Context, GameState

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']


def board(off, dfn, o, x, arrows, ball=0, **kw):
    return game_state(off, dfn, o, x, arrows, ball=ball, check=False).with_(**kw)


def lineup(off_cards, dfn_cards, o, x, arrows, ball=0, **kw):
    ctx = Context(off_cards, dfn_cards, title='step 3i test', kind='GAME', off_team='test', def_team='test')
    return GameState(ctx=ctx, o=tuple(P(q) for q in o), x=tuple(P(q) for q in x),
                     arrows=tuple(B.DIR_NAMES.index(a) for a in arrows), ball=ball, **kw)


def passive_defence(o, s, steps=80):
    """Play the offence computer against a defence that never moves, every roll the offence's way."""
    for _ in range(steps):
        if s.stage == 'over':
            break
        if s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play'):
            a = o.choose(s)
        else:
            acts = legal_actions(s)
            a = next((x for x in acts if x.kind in ('pause', 'end_turn')), None) or \
                next((x for x in acts if x.kind == 'contest' and x.piece < 0), acts[0])
        node = apply(s, a)
        while isinstance(node, ChanceNode):
            labels = [lab for _, lab, _ in node.outcomes]
            node = force(node, next((l for l in ('success', 'kept', 'no foul', 'holds') if l in labels), labels[0]))
        s = node
    return s


# ---- C1: capacity ------------------------------------------------------------------------------------

def test_after_a_move_the_defender_cannot_turn_and_only_quick_steps():
    """High-Low's X1 has Quick Step 2. Before his Move: every movement, the arrow can turn. After it: only a
    Quick Step, which keeps the facing."""
    s = apply(board('Five Out', 'High-Low', TABLE_O, TABLE_X, ['N', 'NE', 'NW', 'N', 'N']), Action('end_turn', 'O'))
    c = capacity(s, 0)
    assert c['can_turn'] and c['movements'] == ['move', 'qs', 'sprint'] and c['reaction'] == 2
    mv = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == P('H10'))
    t = apply(s, mv)
    c = capacity(t, 0)
    assert not c['move_left'] and not c['can_turn'] and c['movements'] == ['qs'] and c['tokens'] == 5
    assert {a.kind for a in legal_actions(t) if a.piece == 0} == {'qs'}


def test_the_three_reaches():
    s = board('Five Out', 'High-Low', TABLE_O, TABLE_X, ['N', 'NE', 'NW', 'N', 'N'])
    assert lanes(s, 1) == {1: 'approach'}                      # X2 can answer the pass to O2 by an approach
    assert lane_reach(s, 1, 0, 1) == 'approach'
    assert closeout_reach(s, 1)                                 # and still close out on him
    assert any(help_reach(s, 3).values()) and not help_reach(s, 4)      # X4 can reach help by the rim, X5 can't


# ---- Part B fix 1: the off-ball threat in the defence's evaluation -------------------------------------

TT = list(TEAMS['Twin Towers'])
WEAK = [TT[0], TT[4], TT[2], TT[3], TT[4]]                       # a poor three-point shooter in O2's slot


def _threat(level, on, x2='D8', cards=None, **kw):
    s = board('Twin Towers', 'High-Low', TABLE_O, ['I10', x2, 'N8', 'G4', 'N4'], ['N', 'NW', 'NW', 'N', 'N'], **kw)
    if cards:
        s = s.with_(ctx=Context(cards, s.ctx.dfn, s.ctx.rules, title='t', kind='GAME', off_team='t', def_team='High-Low'))
    c = C.Computer('X', level, seed=1, budget_s=None, habits=[])
    c.cfg = dict(c.cfg, offball_threat=on)
    c._context(s)
    return c._threat(s), c


@pytest.mark.parametrize('lv', ['starter', 'allstar'])
def test_an_open_shooter_off_the_ball_raises_the_defence_value(lv):
    """O2 (a ▲ three-point shooter) two squares from X2, who still has his Move: the off-ball term counts the
    pass and catch, so the position is worth more to the offence than the carrier's own look."""
    with_term, _ = _threat(lv, True, 'E7')
    without, _ = _threat(lv, False, 'E7')
    assert with_term > without


@pytest.mark.parametrize('lv', ['starter', 'allstar'])
def test_with_no_defender_able_to_recover_it_raises_it_more(lv):
    can, _ = _threat(lv, True, 'E7')
    spent, _ = _threat(lv, True, 'E7', moved_x=0b10, qs_x=0b10)     # X2's Move and Quick Step gone
    assert spent > can


@pytest.mark.parametrize('lv', ['starter', 'allstar'])
def test_a_poor_shooter_in_the_same_spot_changes_it_less_than_the_comfort_line(lv):
    strong = _threat(lv, True, 'E7')[0] - _threat(lv, False, 'E7')[0]
    weak_on, c = _threat(lv, True, 'E7', cards=WEAK)
    weak_off, _ = _threat(lv, False, 'E7', cards=WEAK)
    assert weak_on - weak_off < strong
    line = c.comfort
    assert max(weak_on, line) - max(weak_off, line) < 1.0          # the comfort line concedes the difference


def test_rookie_defence_has_no_off_ball_term():
    assert not C.LEVELS['defence']['levels']['rookie'].get('offball_threat')
    assert C.LEVELS['defence']['levels']['starter']['offball_threat'] and C.LEVELS['defence']['levels']['allstar']['offball_threat']


# ---- C2a: the goal planner on a hand-built post position ----------------------------------------------
# O5 (High-Low's centre, ▲ post) on the right block against X5 (▼ post). X5 fronts on the line from O1, so
# the strong-side entry is contested. The ball has to swing to the left wing, and both receivers have to
# move first to open their lanes.

BB = TEAMS['Bucket Brigade']
POST_OFF = [TEAMS['Iron Wall'][0], TEAMS['Lockdown'][0], TEAMS['Iron Wall'][3], TEAMS['Twin Towers'][3], TEAMS['High-Low'][4]]
POST_DFN = [BB[0], BB[1], BB[4], BB[3], BB[2]]
POST_O = ['O8', 'H8', 'C5', 'B3', 'K3']
POST_X = ['M8', 'G6', 'E7', 'A2', 'L4']
POST_ARROWS = ['E', 'E', 'E', 'NE', 'NE']


def post_position(**kw):
    return lineup(POST_OFF, POST_DFN, POST_O, POST_X, POST_ARROWS, **kw)


def test_the_post_position():
    s = post_position()
    assert s.ctx.off[4].bands['shot_post'] == 'H' and s.ctx.dfn[4].bands['con_post'] == 'L'
    assert not C.pass_risk(s, 0, 4)['clean']                                  # X5's front: contested
    assert all(not C.pass_risk(s, 0, r)['clean'] for r in (1, 2))             # neither swing lane is open yet


def test_all_star_sets_the_post_goal_and_chains_it_backwards():
    s = post_position()
    g = goals(s, 'allstar')[0]
    assert g['entry']['id'] == 'A1' and g['words'] == 'O5 in the post on X5'
    assert [t['words'] for t in g['todo']] == ['O2 moved to open the lane', 'O3 moved to open the lane',
                                              'swung the ball to O2', 'swung the ball to O3', 'O5 sealed X5', 'entry to O5']


def test_the_chain_runs_and_the_log_matches():
    o = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    passive_defence(o, post_position(), steps=40)
    first = next(n for n in o.notes if n['event'] == 'goal')
    assert first['text'] == 'Goal: O5 in the post on X5 (Post entry, 6 steps)'
    fin = next(n for n in o.notes if n['event'] == 'goal_finish')
    assert fin['text'] == ('Goal: O5 in the post on X5. O2 moved to open the lane, O3 moved to open the lane, swung the '
                           'ball to O2, swung the ball to O3, O5 sealed X5, entry to O5.')
    assert not any(n['event'] == 'goal_reassess' for n in o.notes[:o.notes.index(fin)])     # no noise


def test_the_entry_is_clean_when_it_is_thrown():
    o = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    s = post_position()
    for _ in range(40):
        if s.side == 'O' and s.stage == 'play':
            a = o.choose(s)
            if a.kind == 'pass' and a.target == 4:
                assert C.pass_risk(s, s.ball, 4)['clean'] and s.ball == 2           # from the weak-side wing
                return
        else:
            acts = legal_actions(s)
            a = next((x for x in acts if x.kind in ('pause', 'end_turn')), acts[0])
        node = apply(s, a)
        while isinstance(node, ChanceNode):
            labels = [lab for _, lab, _ in node.outcomes]
            node = force(node, next((l for l in ('success', 'kept', 'no foul') if l in labels), labels[0]))
        s = node
    pytest.fail('no entry pass')


def test_a_broken_condition_that_cannot_be_restored_changes_the_goal():
    """After the goal is set, X4 (▲ post defence) switches onto O5 and X5 leaves: the post edge is gone."""
    o = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    s = post_position()
    o.choose(s)
    assert o.goal and o.goal['id'] == 'A1'
    t = s.with_(x=(P('M8'), P('G6'), P('E7'), P('L4'), P('A2')), arrows=s.arrows[:3] + (B.DIR_NAMES.index('NE'),) * 2)
    t = t.with_(tok_o=s.tok_o - 1)
    o.choose(t)
    re = [n for n in o.notes if n['event'] == 'goal_reassess']
    assert re and re[0]['why'] == "the defence broke a condition that can't be restored in time"
    assert o.goal is None or o.goal['key'] != ('A1', ('d', 4), ('p', 4))


def test_no_reassessment_on_noise_the_goal_persists():
    """Against a defence that stands still, the goal is set once and kept for at least ten actions."""
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
        node = apply(s, a)
        while isinstance(node, ChanceNode):
            labels = [lab for _, lab, _ in node.outcomes]
            node = force(node, next((l for l in ('success', 'kept', 'no foul') if l in labels), labels[0]))
        s = node
    ev = [x['event'] for x in o.notes]
    upto = ev.index('goal_finish') if 'goal_finish' in ev else len(ev)
    assert n >= 7 and ev[:upto].count('goal') == 1 and 'goal_reassess' not in ev[:upto], ev


def test_rookie_tries_the_goal_directly_and_starter_one_condition_deep():
    s = post_position()
    rk = next(g for g in goals(s, 'rookie') if g['entry']['id'] == 'A1')
    st = next(g for g in goals(s, 'starter') if g['entry']['id'] == 'A1')
    al = next(g for g in goals(s, 'allstar') if g['entry']['id'] == 'A1')
    assert [t['words'] for t in rk['todo']] == ['entry to O5']
    assert [t['words'] for t in st['todo']] == ['O5 sealed X5', 'entry to O5']
    assert len(al['todo']) == 6


def test_the_defence_objectives_follow_visible_progress():
    """The defence reads only the board: after the swing to the weak side and the seal, keeping the ball
    out of O5's post weighs more."""
    s = post_position()
    before = next(o for o in defence_objectives(s, 'allstar', k=8) if o['id'] == 'DO-front')
    swung = s.with_(o=(P('O8'), P('H10'), P('A5'), P('B3'), P('K3')), ball=2)
    after = next(o for o in defence_objectives(swung, 'allstar', k=8) if o['id'] == 'DO-front')
    assert after['words'] == "keep the ball out of O5's post" or 'O5' in after['words']
    assert after['weight'] > before['weight']


def test_the_review_shows_both_sides_thinking():
    from playmaker_engine.review import computer_facts
    recs = [dict(type='setup', computer=dict(O=dict(level='allstar', name='All-Star', habits=[], concepts_off=[]),
                                            X=dict(level='allstar', name='All-Star', habits=[], concepts_off=[]))),
            dict(type='computer', side='O', possession=1, event='goal_finish',
                 text='Goal: O5 in the post on X5. O2 moved to open the lane, swung the ball to O2, O5 sealed X5, entry to O5.'),
            dict(type='computer', side='X', possession=1, event='objectives', text="Objectives: keep the ball out of O5's post")]
    text = ' '.join(computer_facts(recs))
    assert 'Goal: O5 in the post on X5.' in text and "keep the ball out of O5's post" in text


# ---- C2: off-ball movement --------------------------------------------------------------------------

def _wing(o2, x2, a2, **kw):
    return board('Five Out', 'High-Low', ['I11', o2, 'O9', 'A3', 'Q3'], ['I10', x2, 'N8', 'G4', 'N4'], ['N', a2, 'NW', 'N', 'N'], **kw)


def test_v_cut_the_defender_who_followed_in_cannot_answer_the_pass_back_out():
    """O2 Moved in to E7 at the end of one phase; X2 followed him in with his Move, to D7 facing him. In the
    next phase O2 Moves back out to C9: X2's arrow faces in, so no movement reaches the lane. Clean."""
    start = _wing('C9', 'D8', 'NE')
    assert lane_reach(start, 1, 0, 1) == 'approach' and not C.pass_risk(start, 0, 1)['clean']
    out = _wing('C9', 'D7', 'E')
    assert lane_reach(out, 1, 0, 1) is None and C.pass_risk(out, 0, 1)['clean']


def test_v_cut_a_defender_who_does_not_follow_leaves_the_inside_open():
    stay = _wing('E7', 'D8', 'NE')
    assert lane_reach(stay, 1, 0, 1) is None and C.pass_risk(stay, 0, 1)['clean']


def test_all_star_moves_the_cutter_instead_of_throwing_the_contested_pass():
    s = _wing('C9', 'D8', 'NE')
    a = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[]).choose(s)
    assert not (a.kind == 'pass' and a.target == 1), a
    assert a.kind in MOVEMENT and a.piece == 1, a


def test_baseline_cut_the_chaser_ends_behind_and_cannot_answer_the_far_side_pass():
    """O4 cut along the baseline from the right corner, under the rim, to E2; X4 chased and trails at G2 facing
    him. O3 has the ball on the left wing: the pass is clean and X4 can't reach it even with his Move left.
    Had X4 stayed level above the cutter (G3), he could."""
    def at(x4, a4):
        return board('Five Out', 'High-Low', ['I11', 'C9', 'C6', 'E2', 'Q6'], ['I10', 'D8', 'D6', x4, 'P6'],
                     ['N', 'NE', 'NW', a4, 'N'], ball=2)
    trail = at('G2', 'W')
    assert capacity(trail, 3)['move_left'] and lane_reach(trail, 3, 2, 3) is None and C.pass_risk(trail, 2, 3)['clean']
    level = at('G3', 'W')
    assert lane_reach(level, 3, 2, 3) == 'approach'


def test_the_templates_by_level():
    """Rookie generates no C2 plays; Starter only the V-cut and the shift away; All-Star all of them."""
    s = _wing('C9', 'D8', 'NE')
    kinds = {}
    for lv in C.LEVEL_NAMES:
        c = C.Computer('O', lv, seed=1, budget_s=None, habits=[])
        c._context(s)
        view = C.seen_state(s, 'O', c.seen)
        known = set(c.cfg.get('plays', ()))
        kinds[lv] = {k for k, v in c._movement_plays(view, legal_actions(view), known, []).items()}
    assert kinds['rookie'] == set()
    assert kinds['starter'] == {'vcut', 'shift'}
    assert kinds['allstar'] == {'vcut', 'shift', 'baseline', 'backcut', 'offscreen'}


def test_all_star_baseline_template_crosses_under_the_rim():
    s = board('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'L2'], ['I10', 'D8', 'N8', 'G4', 'L3'], ['N', 'NE', 'NW', 'N', 'S'])
    c = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    c._context(s)
    view = C.seen_state(s, 'O', c.seen)
    bl = c._movement_plays(view, legal_actions(view), set(c.cfg['plays']), [])['baseline']
    p = next(p for p in bl if p.actions[0].piece == 4)
    assert p.actions[0].dest[1] <= 2 and abs(p.actions[0].dest[0] - RC.RIM[0]) < abs(P('L2')[0] - RC.RIM[0])


# ---- C3: the overloaded defender ----------------------------------------------------------------------
# From a computer playout (Ball Movement v High-Low): X5 is the only help on O4's drive and the only answer
# to the lane to O2, a ▲ three-point shooter after he shifted away.

def _dilemma():
    return board('Ball Movement', 'High-Low', ['R10', 'A6', 'L11', 'K4', 'F5'], ['Q10', 'C8', 'L10', 'L7', 'G4'],
                 ['E', 'W', 'NE', 'NW', 'NE'], ball=3, clock=8)


def test_advantages_reports_the_overloaded_defender():
    od = [a for a in advantages(_dilemma(), dilemma=True) if a['kind'] == 'overloaded']
    assert od and od[0]['defender'] == 4 and od[0]['attacker'] == 1
    assert describe(od[0]) == "X5 had two jobs (help on O4's drive and the lane to O2); O2 was left for a three"
    assert not [a for a in advantages(_dilemma()) if a['kind'] == 'overloaded']      # only levels that know it


def test_all_star_attacks_the_job_the_defence_left_open():
    c = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    a = c.choose(_dilemma())
    assert a.piece == 1 or (a.kind == 'pass' and a.target == 1), a                      # O2, the job left open
    assert any(n['event'] == 'goal_hold' and 'two jobs' in n['text'] for n in c.notes), c.notes


def _rotation():
    """From a playout (Bucket Brigade v Lockdown): X5 is the only closeout on O1 and the only answer to the
    lane to O5. X1, X4 and X5 have used their Moves; X2 and X3 have theirs."""
    s = board('Bucket Brigade', 'Lockdown', ['I6', 'D7', 'O9', 'D2', 'Q2'], ['H7', 'D8', 'N8', 'I5', 'J6'],
              ['W', 'SE', 'NW', 'NW', 'W'], clock=10)
    return s.with_(tok_o=1, tok_x=1, moved_o=24, moved_x=25, cnt=(0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1), lock_o=1, phase=2, qs_x=1)


def test_the_defence_hands_a_job_to_a_defender_with_capacity_left():
    s = _rotation()
    od = [a for a in advantages(s, dilemma=True) if a['kind'] == 'overloaded']
    assert od and od[0]['defender'] == 4
    x = s.with_(side='X')
    for lv in ('starter', 'allstar'):
        a = C.Computer('X', lv, seed=1, budget_s=None, habits=[]).choose(x)
        assert a.piece not in (None, 4) and capacity(x, a.piece)['movements'], (lv, a)       # a fresh defender
        n = apply(x, a)
        assert not isinstance(n, ChanceNode)
        assert not [b for b in advantages(n.with_(side='O'), dilemma=True) if b['kind'] == 'overloaded'], (lv, a)


# ---- C5: follow or stay ---------------------------------------------------------------------------------

def test_follow_or_stay_the_defence_weighs_what_following_costs():
    """O2 cuts in from the wing. Following spends X2's Move and turns him in; staying keeps the lane but gives
    up the inside. The All-Star defence's choice is the one its evaluation says is worth less to the offence,
    and the evaluation sees the difference."""
    s = _wing('E7', 'D8', 'NE')
    x = apply(s, Action('end_turn', 'O'))
    c = C.Computer('X', 'allstar', seed=1, budget_s=None, habits=[])
    c._context(x)
    from playmaker_engine.solver import Play
    follow = next(a for a in legal_actions(x) if a.kind == 'move' and a.piece == 1 and B.adjacent(a.dest, P('E7'))
                  and a.arrow == B.dir_between(a.dest, P('E7')))
    stay = next(a for a in legal_actions(x) if a.kind in ('pause', 'end_turn'))
    scored = dict((str(p.actions[0]), v) for v, p in c._rank(x, [Play('f', (follow,)), Play('s', (stay,))], c._value_fn(), False, None))
    assert scored[str(follow)] != scored[str(stay)]
    a = c.choose(x)
    assert a is not None


# ---- the late_closeout rule test -------------------------------------------------------------------

LATE = RC.with_rules(late_closeout=True)


def _contest(shot, o1, x1, a1, moved, rules=LATE):
    s = game_state('Five Out', 'High-Low', [o1, 'C9', 'O9', 'A3', 'Q3'], [x1, 'D8', 'N8', 'G4', 'N4'],
                   [a1, 'NE', 'NW', 'N', 'N'], rules=rules, check=False)
    s = s.with_(react_moved=1 if moved else 0)
    return next(o for o in contest_options(s, 0, shot) if o.defender == 0)


def test_late_closeout_off_by_default():
    assert RC.Rules().late_closeout is False
    set_ = _contest('three', 'J10', 'I10', 'E', False, rules=None)
    late = _contest('three', 'J10', 'I10', 'E', True, rules=None)
    assert set_ == late                                     # the default ignores the reaction movement


def test_a_late_contester_on_a_three_takes_the_minus_three_and_no_foul_roll():
    set_ = _contest('three', 'J10', 'I10', 'E', False)
    late = _contest('three', 'J10', 'I10', 'E', True)
    assert late.clean and late.contest == set_.contest - RC.FAR_CONTEST_PENALTY


def test_a_late_contester_at_the_rim_contests_with_a_foul_roll():
    late = _contest('layup', 'I3', 'H3', 'E', True)
    set_ = _contest('layup', 'I3', 'H3', 'E', False)
    assert set_.clean and not late.clean and late.p_foul > 0


def test_a_reaction_move_to_another_square_marks_the_contester_late():
    from conftest import P as _P
    from playmaker_engine.scenarios import scenario_state
    s = scenario_state(6, rules=LATE)
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == (9, 10)))
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'shot'))
    assert s.stage == 'reaction'
    step = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest != s.x[0])
    t = apply(s, step)
    assert t.react_moved & 1
    turn = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == s.x[0])
    assert not apply(s, turn).react_moved & 1                # turning in place: set, not late


# ---- E1: a created edge (screen so a ▼ post defender picks up O5) -----------------------------------------
# O5 (▲ post) on the right block is guarded by X4 (▲ post defence); X5 (▼) guards O4 on the left block.

E1_O = ['O8', 'H9', 'N5', 'G5', 'K3']
E1_X = ['N9', 'H8', 'O6', 'L3', 'H4']
E1_ARROWS = ['N', 'S', 'E', 'W', 'E']


def e1_position():
    return lineup(POST_OFF, POST_DFN, E1_O, E1_X, E1_ARROWS)


def _e1(s):
    return next((g for g in goals(s, 'allstar') if g['entry']['id'] == 'E1' and g['att'] == 4), None)



def _offence_turn(s):
    """Pass the defence's turns (it stands still) until the offence is to act."""
    for _ in range(12):
        if s.stage == 'over' or (s.side == 'O' and s.stage == 'play'):
            return s
        acts = legal_actions(s)
        a = next((x for x in acts if x.kind in ('pause', 'end_turn')), None) or \
            next((x for x in acts if x.kind == 'contest' and x.piece < 0), acts[0])
        node = apply(s, a)
        while isinstance(node, ChanceNode):
            labels = [lab for _, lab, _ in node.outcomes]
            node = force(node, next((l for l in ('success', 'kept', 'no foul') if l in labels), labels[0]))
        s = node
    return s


def test_e1_the_created_edge_is_ranked_above_the_contested_shot():
    s = e1_position()
    g = _e1(s)
    assert g and g['words'] == 'screen X4 so X5 picks up O5'
    contested = 2 * (s.ctx.off[4].shot('post') - s.ctx.dfn[3].con('post'))      # O5's post-up on X4 now
    assert g['edge'] == 2 * (s.ctx.off[4].shot('post') - s.ctx.dfn[4].con('post')) and g['score'] > contested


def _run_step(s, step):
    from playmaker_engine.solver import apply_play
    plays = [p for p in step['plays']() if apply_play(s, p) is not None]
    assert plays, step['words']
    node = s
    for a in plays[0].actions:
        node = apply(node, a)
        while isinstance(node, ChanceNode):
            labels = [lab for _, lab, _ in node.outcomes]
            node = force(node, next((l for l in ('success', 'kept', 'no foul', 'holds') if l in labels), labels[0]))
    return _offence_turn(node)


def test_e1_the_chain_runs_and_the_post_up_follows_once_the_screen_holds():
    """E1's steps in order: O3 screens X4, O5 goes at X5. With the switch made (X5 now the nearest, ▼ post),
    the screen's job is done and the same edge is a post-up on X5, which the plan carries to the entry."""
    s = e1_position()
    done = []
    for _ in range(4):
        g = _e1(s)
        if g is None:
            break
        step = g['todo'][0]
        done.append(step['words'])
        s = _run_step(s, step)
    assert done[:2] == ['O3 screened X4', 'O5 went at X5'], done
    assert min(range(5), key=lambda j: (B.cheb(s.x[j], s.o[4]), j)) == 4          # the switch: X5 has him
    for _ in range(6):
        g = next((x for x in goals(s, 'allstar') if x['entry']['id'] == 'A1' and x['att'] == 4), None)
        assert g and g['bind']['d'] == 4, g and g['bind']                          # the post-up on X5
        step = g['todo'][0]
        done.append(step['words'])
        s = _run_step(s, step)
        if step['finish']:
            break
    assert done[-1] == 'entry to O5' and s.ball == 4, done
    post = [a for a in legal_actions(s) if a.kind == 'shot' and a.shot == 'post']
    assert post and B.adjacent(s.x[4], s.o[4])                                     # the post-up, on X5


def test_e1_when_the_screen_is_beaten_the_goal_is_reassessed_and_gained_steps_kept():
    """The goal is E1; X4 beats the screen (a Challenge won). The roll went the wrong way, so the offence
    reassesses; O5's move next to X5 is still on the board and the new chain doesn't ask for it again."""
    o = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    s = e1_position()
    o._context(s)
    g = _e1(s)
    o.goal = dict(key=g['key'], id='E1', words=g['words'], chain=[], score=g['score'])
    o._goal_snap = (s.phase, s.tos, s.lock_o, ((2, 3, 0, 0),))
    t = s.with_(o=s.o[:4] + (P('I3'),), screens=((2, 3, 0, 1 << 3),))           # O3's screen on X4, beaten by X4
    o._goal_choose(t, goals(t, 'allstar'))
    re = [n for n in o.notes if n['event'] == 'goal_reassess']
    assert re and re[0]['why'] == 'a screen was beaten'
    new = next(x for x in goals(t, 'allstar') if x['key'] == o.goal['key'])
    assert not any(st['id'] == 'repos' for st in new['todo'])


def test_the_defence_covers_both_comparable_goals():
    """The post position with a ▲ three-point shooter on the weak-side wing (O3): a post entry and a weak-side
    three are comparable goals. The All-Star defence's turn leaves both answered: the entry still contested,
    the lane to O3 still covered and his closeout still reachable."""
    off = list(POST_OFF)
    off[2] = TEAMS['Twin Towers'][1]
    s = lineup(off, POST_DFN, POST_O, POST_X, POST_ARROWS)
    top = {g['entry']['pattern'] for g in goals(s, 'allstar')[:5]}
    assert {'post_entry', 'spot_up'} <= top
    t = s.with_(side='X')
    c = C.Computer('X', 'allstar', seed=1, budget_s=None, habits=[])
    while t.side == 'X' and t.stage == 'play':
        t = apply(t, c.choose(t))
        assert not isinstance(t, ChanceNode)
    o = t.with_(side='O', turn_n=0)
    assert not C.pass_risk(o, 0, 4)['clean'] and not C.pass_risk(o, 0, 2)['clean'] and closeout_reach(o, 2, 2)
