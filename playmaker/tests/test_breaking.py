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


# These positions were built for single arrows and the intercept rule of step 3i. Under the wedge (the default since the follow-up
# rulings) every defender covers a second line and the positions mean something else, so they keep the single
# arrow; the screen, drive and intercept rulings apply as everywhere. The wedge is tested in test_rulings_3i.py.
RULES = RC.with_rules(arrow_mode='single', intercept_rule='approach')   # and the lanes as they were (OQ-72 ruling)


def board(off, dfn, o, x, arrows, ball=0, **kw):
    return game_state(off, dfn, o, x, arrows, ball=ball, rules=RULES, check=False).with_(**kw)


def lineup(off_cards, dfn_cards, o, x, arrows, ball=0, **kw):
    ctx = Context(off_cards, dfn_cards, RULES, title='step 3i test', kind='GAME', off_team='test', def_team='test')
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
        s = s.with_(ctx=Context(cards, s.ctx.dfn, RULES, title='t', kind='GAME', off_team='t', def_team='High-Low'))
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
    """The planned chain is played in order: both receivers open their lanes, then the two swing passes.
    (With the ball on the weak side, O5's cut to the rim square is worth more than the post-up, so the
    finish may change there: that is a logged trigger, not noise.) The possession ends with O5's catch."""
    o = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    passive_defence(o, post_position(), steps=40)
    first = next(n for n in o.notes if n['event'] == 'goal')
    assert first['text'] == 'Goal: O5 in the post on X5 (Post entry, 6 steps)'
    steps = [n['text'] for n in o.notes if n['event'] == 'goal_step'][:4]
    assert steps == ['O2 moved to open the lane', 'O3 moved to open the lane', 'Swung the ball to O2', 'Swung the ball to O3']
    fin = next(n for n in o.notes if n['event'] == 'goal_finish')
    assert 'O5' in fin['text'].split('.')[0]


def test_the_entry_is_clean_when_it_is_thrown():
    o = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    s = post_position()
    for _ in range(40):
        if s.side == 'O' and s.stage == 'play':
            a = o.choose(s)
            if a.kind == 'pass' and a.target == 4:
                assert C.pass_risk(s, s.ball, 4)['clean'] and s.ball != 0           # from the weak side, clean
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
    """Against a defence that stands still, over ten actions: the first goal is kept through its set-up
    (the opens and the swing), and a goal only ever changes with a logged trigger or after it finishes."""
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
    ev = [x['event'] for x in o.notes if x['event'] in ('goal', 'goal_step', 'goal_reassess', 'goal_finish')]
    assert n >= 8 and ev[:6] == ['goal', 'goal_step', 'goal_step', 'goal_step', 'goal_step', ev[5]], ev
    for k, e in enumerate(ev):
        if e == 'goal' and k > 0:
            assert ev[k - 1] in ('goal_reassess', 'goal_finish'), ev       # every change has its reason
    assert all(x.get('why') for x in o.notes if x['event'] == 'goal_reassess')


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
    assert (a.kind in MOVEMENT and a.piece == 1) or (a.kind == 'pass' and C.pass_risk(s, 0, a.target)['clean']), a


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


# ---- E1: a ball screen to force a switch (step 3i follow-up) ---------------------------------------------
# O1 (Ball Movement's point guard: Dribble 19) is guarded by X1 (Lockdown's guard: ▼ post contest); O5 (High-Low's
# centre: ▲ post) is guarded by X5 (Twin Towers' centre: Agility 4). If O5's screen makes them switch, O5 posts
# up the small X1 and O1 attacks the slow X5.

E1_OFF = [TEAMS['Ball Movement'][0], TEAMS['Iron Wall'][0], TEAMS['Lockdown'][0], TEAMS['Twin Towers'][3], TEAMS['High-Low'][4]]
E1_DFN = [TEAMS['Lockdown'][0], TEAMS['Lockdown'][1], TEAMS['Lockdown'][2], TEAMS['Lockdown'][3], TEAMS['Twin Towers'][4]]
E1_O = ['J7', 'C8', 'P8', 'B3', 'L5']
E1_X = ['J8', 'D8', 'O8', 'C3', 'L4']
E1_ARROWS = ['S', 'NE', 'NW', 'NE', 'N']


def e1_position(dfn=None):
    return lineup(E1_OFF, dfn or E1_DFN, E1_O, E1_X, E1_ARROWS)


def _e1(s, m=None, mems=None):
    from playmaker_engine import guarding
    m = m or guarding.initial(s)
    return next((g for g in goals(s, 'allstar', mems, matchups=m) if g['entry']['id'] == 'E1' and g['bind']['sc'] == 4), None)


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


def test_e1_holds_both_branches_and_ranks_above_the_contested_shot():
    from playmaker_engine.planner import board_looks
    from playmaker_engine.scoring import p_success
    s = e1_position()
    g = _e1(s)
    assert g and g['role'] == 'setup' and g['words'] == 'O5 screens X1 to switch X5 onto O1'
    br = g['branches']
    off, dfn = s.ctx.off, s.ctx.dfn
    assert br['post'] == 2 * (off[4].shot('post') - dfn[0].con('post'))           # (a) O5 on the small X1
    pw = float(p_success(off[0].r['dribble'] - dfn[4].r['agility']))
    assert 0 < br['drive'] <= pw * 40                                            # (b) O1 at the slow X5
    assert br['switch'] == min(br['post'], br['drive'])                           # the defence denies the bigger
    assert g['V'] == min(br['switch'], br['stay'])                                # ...and picks its reply
    assert g['P'] == float(p_success(off[4].r['screen'] - dfn[0].r['challenge']))
    contested = board_looks(s)[0][0]                                              # the best look now: O1's own
    assert g['score'] > contested


def test_a_switch_between_equal_defenders_is_worth_about_nothing():
    dfn = list(E1_DFN)
    dfn[4] = dfn[0]                                       # X5 the same card as X1
    g = _e1(e1_position(dfn))
    assert g and abs(g['branches']['switch_gain']) < 1.0


def test_e1_reads_the_reply_and_a_switch_back_breaks_it():
    """After the screen the defence switched (the record: X5 on O1, X1 on O5): the plan's next step is already
    there, the branch the defence left open. When the defence switches back, the goal is reassessed."""
    from playmaker_engine import guarding
    s = e1_position()
    o = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    o._context(s)
    switched = (4, 1, 2, 3, 0)                            # X1 now on O5, X5 on O1
    g = _e1(s, switched, {'E1': {'orig4': [0, 4]}})
    assert g and g['e1']['switched'] and g['remember'] == {'switched4': True}
    assert set(g['branches']) == {'post', 'drive'} and g['todo'][0]['id'] == 'read'
    assert g['todo'][0]['plays']()                        # the next steps are already in the plan
    o.matchups = switched
    o.goal = dict(key=g['key'], id='E1', words=g['words'], chain=[], score=g['score'])
    o.goal_mem = {'E1': {'orig4': [0, 4], 'switched4': True}}
    o._goal_snap = (s.phase, s.tos, s.lock_o, s.screens)
    back = guarding.initial(s)                            # switched back
    assert _e1(s, back, o.goal_mem) is None
    from playmaker_engine.planner import goals as plan
    o.matchups = back
    o._goal_choose(s, plan(s, 'allstar', o.goal_mem, matchups=back, keep=g['key']))
    re = [n for n in o.notes if n['event'] == 'goal_reassess']
    assert re and re[0]['why'] == "the defence broke a condition that can't be restored in time"


def test_no_goal_has_a_fixed_score():
    """Every goal's score is P x ((1 - risk) x V + risk x the pick-off) + (1 - P) x the best look now - the
    steps' cost: V a look on the expected board (a finish) or what the offence keeps there (a set-up)."""
    from playmaker_engine.planner import TEMPO
    for s in (post_position(), e1_position(), board('Five Out', 'High-Low', TABLE_O, TABLE_X, ['N', 'NE', 'NW', 'N', 'N'])):
        for g in goals(s, 'allstar'):
            want = g['P'] * ((1 - g['risk']) * g['V'] + g['risk'] * RC.TURNOVER_POINTS) + (1 - g['P']) * g['base'] - TEMPO * len(g['todo'])
            assert g['score'] == pytest.approx(want, abs=0.02), g['words']
            assert g['V'] <= 3 * 20                                              # a look: never more than an open three
    from playmaker_engine.planner import keeps, simulate
    for s in (post_position(), e1_position()):            # the overload: no score of its own any more
        g = next((g for g in goals(s, 'allstar') if g['entry']['id'] == 'C5'), None)
        if g is not None:
            after, p, _ = simulate(s, g['todo'])
            if any(not st['finish'] for st in g['todo']):      # still setting up: what it unlocks
                want = keeps(after, s)[0]
            else:                                              # set up: the finish it made
                from playmaker_engine.planner import look_value
                want = look_value(after, g['att'])
            assert g['V'] == pytest.approx(want, abs=0.01) and g['V'] != 18.0


# ---- matchups (OQ-67a) -------------------------------------------------------------------------------

def test_matchups_are_set_at_the_start_and_persist_through_a_screen_that_forces_no_switch():
    from playmaker_engine import guarding
    s = board('Five Out', 'High-Low', ['I11', 'F10', 'O9', 'A3', 'Q3'], ['I10', 'E9', 'N8', 'G4', 'N4'], ['N', 'NE', 'NW', 'N', 'N'])
    m = guarding.initial(s)
    assert m == (0, 1, 2, 3, 4)
    # O2 comes over and screens X1: X1 is now next to O2, but X2 can still reach his man and nothing the
    # defence did changed, so neither switches
    t = s.with_(o=(s.o[0], P('H10')) + s.o[2:], screens=((1, B.DIR_NAMES.index('E'), True, 0),))
    assert guarding.update(m, s, t) == m
    stay = t.with_(arrows=(t.arrows[0], B.DIR_NAMES.index('E')) + t.arrows[2:])      # the defence's turn: X2 turns
    assert guarding.update(m, t, stay) == m
    # the computer's own record, decision to decision, keeps it too
    c = C.Computer('X', 'allstar', seed=1, budget_s=None, habits=[])
    c._context(s)
    c._track_matchups(s)
    c._track_matchups(t)
    assert c.matchups == m


def test_a_switch_is_the_defences_own_choice_and_a_locked_defender_is_replaced():
    from playmaker_engine import guarding
    s = board('Five Out', 'High-Low', TABLE_O, TABLE_X, ['N', 'NE', 'NW', 'N', 'N'])
    m = guarding.initial(s)
    # the defence moves X1 onto O2 and X2 onto O1: a switch
    sw = s.with_(x=(P('D9'), P('H10')) + s.x[2:])
    assert guarding.update(m, s, sw) == (1, 0, 2, 3, 4)
    # X1 locked and X3 now next to O1 (his own man far): X3 takes O1, X1 takes O3
    lk = s.with_(lock_x=1, x=(P('I10'), P('D8'), P('J10'), P('G4'), P('N4')))
    assert guarding.update(m, s, lk)[2] == 0


def test_the_defence_covers_both_comparable_goals():
    """The post position with a ▲ three-point shooter on the weak-side wing (O3): a post entry and a weak-side
    three are comparable goals. The All-Star defence's turn leaves both answered: the entry still contested,
    the lane to O3 still covered and his closeout still reachable."""
    off = list(POST_OFF)
    off[2] = TEAMS['Twin Towers'][1]
    s = lineup(off, POST_DFN, POST_O, POST_X, POST_ARROWS)
    top = goals(s, 'allstar')[:8]
    assert any(g['entry']['pattern'] == 'post_entry' for g in top)
    assert any(g['att'] == 2 and g['entry']['pattern'] in ('spot_up', 'get_open', 'shift_away') for g in goals(s, 'allstar'))
    t = s.with_(side='X')
    c = C.Computer('X', 'allstar', seed=1, budget_s=None, habits=[])
    while t.side == 'X' and t.stage == 'play':
        t = apply(t, c.choose(t))
        assert not isinstance(t, ChanceNode)
    o = t.with_(side='O', turn_n=0)
    assert not C.pass_risk(o, 0, 4)['clean'] and not C.pass_risk(o, 0, 2)['clean'] and closeout_reach(o, 2, 2)
