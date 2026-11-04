"""Step 3e: the computer opponent at three levels. It chooses among legal actions only, sees only what a
human sees, values contests after the defence's legal reaction, and its levels make named mistakes."""
import json

import pytest
from conftest import P

from playmaker_engine import board as B
from playmaker_engine import computer as C
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_engine.scenarios import scenario_state, game_state
from playmaker_engine.state import CI

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
TABLE_ARROWS = ['N', 'NE', 'NW', 'N', 'N']


def table(off='Five Out', dfn='High-Low'):
    return game_state(off, dfn, TABLE_O, TABLE_X, TABLE_ARROWS)


def shot_declared():
    """Scenario 6: O1 steps to J10 and declares a three. X1 on I10 faces N, not the shooter (E)."""
    s = scenario_state(6)
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == (9, 10)))
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'shot'))
    assert s.stage == 'reaction' and s.arrows[0] != B.dir_between(s.x[0], s.o[0])
    return s


def entry(rc, d):
    return next((e for e in rc if e['defender'] == d), None)


# ---- section 1: the reaction ----------------------------------------------------------------------

def test_an_unused_move_and_a_token_make_the_contest_clean():
    s = shot_declared()
    e = entry(C.reachable_contest(s), 0)
    assert e and e['clean'] and e['actions'] == 1


def test_after_the_move_is_used_it_is_a_foul_roll():
    s = shot_declared()
    no_qs = list(s.cnt)
    no_qs[CI['x_qs']] = 2                         # Quick Steps spent too (a Quick Step keeps the facing anyway)
    s = s.with_(moved_x=s.moved_x | 1, cnt=tuple(no_qs))
    e = entry(C.reachable_contest(s), 0)
    assert e and not e['clean'] and 0 < e['foul_p'] < 1


def test_a_locked_defender_cannot_turn():
    """Locked: no Move, no turn. A Quick Step is still legal and keeps the facing, so with the Quick
    Steps spent the contest is a foul roll."""
    s = shot_declared()
    no_qs = list(s.cnt)
    no_qs[CI['x_qs']] = 2
    s = s.with_(lock_x=1, cnt=tuple(no_qs))
    e = entry(C.reachable_contest(s), 0)
    assert e is not None and not e['clean']
    locked_qs = entry(C.reachable_contest(shot_declared().with_(lock_x=1)), 0)
    assert locked_qs['square'] != 'I10'                     # clean only by stepping to a square it already faces from


def test_the_reaction_budget_is_shared_and_paid_from_tokens():
    s = shot_declared()
    assert C.reaction_budget(s) == 2 and C.reaction_budget(s.with_(tok_x=1)) == 1 and C.reaction_budget(s.with_(tok_x=0)) == 0
    one = C.reachable_contest(s.with_(tok_x=1))
    assert all(e['actions'] <= 1 for e in one)
    none = C.reachable_contest(s.with_(tok_x=0))
    assert all(e['actions'] == 0 for e in none)          # only the arrows as they stand


def test_every_clean_contest_is_a_real_legal_reaction():
    """Replay each claimed clean contest through the engine: the reaction's actions are legal and end with
    the defender adjacent and facing the shooter (Sprints face the way they ran, Quick Steps keep it)."""
    from playmaker_engine.solver import defender_reach, _seq_actions
    from playmaker_engine.scenarios import SCENARIOS
    checked = 0
    for n in sorted(SCENARIOS):
        s = scenario_state(n)
        if s.stage != 'play' or s.side != 'O':
            continue
        tries = [None] + [a for a in legal_actions(s) if a.kind in ('move', 'qs') and a.piece == s.ball][:8]
        for first in tries:
            st0 = s if first is None else apply(s, first)
            if isinstance(st0, ChanceNode) or st0.side != 'O' or st0.stage != 'play':
                continue
            shots = [a for a in legal_actions(st0) if a.kind == 'shot']
            if not shots:
                continue
            r = apply(st0, shots[0])
            if isinstance(r, ChanceNode) or r.stage != 'reaction':
                continue
            sp = r.o[r.ball]
            for e in C.reachable_contest(r):
                if not e['clean'] or e['actions'] == 0:
                    continue
                free, fixed = defender_reach(r, e['defender'], C.reaction_budget(r))
                q = B.parse_sq(e['square'])
                on = B.dir_between(q, sp)
                seq = free.get(q) or fixed[q][on]
                st = r
                for a in _seq_actions(e['defender'], seq, on):
                    assert a in legal_actions(st), (a, st.encode())
                    st = apply(st, a)
                assert st.x[e['defender']] == q and st.arrows[e['defender']] == on
                checked += 1
    assert checked >= 10, checked


# ---- sections 2-5: reserve, help, comfort line, paint, setup ------------------------------------

def test_reserve_all_star_holds_its_last_token_more_than_starter():
    from playmaker_engine.defence_check import play_positions
    spent = {}
    for lv in ('starter', 'allstar'):
        n = 0
        for _, s in play_positions()[:20]:
            s1 = s.with_(tok_x=1)
            if not legal_actions(s1):
                continue
            c = C.Computer('X', lv, seed=1, budget_s=None, overrides={'randomness': 0.0, 'habits': 0}, habits=[])
            a = c.choose(s1)
            n += a.kind not in ('end_turn', 'pause')
        spent[lv] = n
    assert spent['allstar'] <= spent['starter'], spent


def test_paint_a_helper_who_can_still_recover_is_worth_more():
    c = C.Computer('X', 'allstar', seed=1, budget_s=None)
    s = table()
    c._context(s)
    fresh = c.ev(s)[0].ev
    spent = c.ev(s.with_(moved_x=0b11110))[0].ev           # the help defenders' Moves already used
    assert fresh <= spent


def test_comfort_line_concedes_a_poor_shooter_and_guards_a_good_one():
    c = C.Computer('X', 'allstar', seed=1, budget_s=None)
    key = c._comfort_key(table())
    from playmaker_engine.solver import Play
    p = Play('x', (Action('end_turn', 'X'),))
    assert key((8.0, p)) == pytest.approx(key((12.0, p)), abs=1e-5)     # both below the line: conceded alike
    assert key((22.0, p)) > key((18.0, p))                              # above it: every point counts
    g = C.Computer('X', 'allstar', seed=1, budget_s=None, habits=['never_leaves_shooter'])
    gk = g._comfort_key(table())
    assert gk((12.0, p)) > gk((8.0, p))                                  # the habit keeps guarding below it


def test_setup_matchups_and_arrows_come_from_the_evaluation():
    from playmaker_web.game import Game
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], full=True, place=True, seed=1, level='pro', ai=dict(X='allstar'))
    g.place(g.tokens['both'], dict(squares=TABLE_O, ball=0))
    assert g.placing is None
    rec = [r for r in g.read_log() if r['type'] == 'computer' and r.get('event') == 'setup']
    assert rec and len(rec[0]['matchup']) == 5
    from playmaker_engine.defence import arrow_job
    assert any(arrow_job(g.state, j) != 'on_man' for j in range(5))


# ---- section 7: the offence -------------------------------------------------------------------------

def test_a_shot_an_adjacent_defender_can_turn_to_is_valued_as_contested():
    s = shot_declared()
    rc = C.reachable_contest(s)
    best = rc[0]
    open_value = 3 * s.ctx.off[0].shot('three')
    assert best['clean'] and best['value'] < open_value
    for lv in ('starter', 'allstar'):
        c = C.Computer('O', lv, seed=1, budget_s=None, habits=[], overrides={'randomness': 0.0})
        a = c.choose(scenario_state(6))
        assert not (a.kind == 'move' and a.piece == 0 and a.dest == (9, 10)), (lv, a)


def test_coachs_call_primary_target_is_the_secret_target():
    s = scenario_state(8)
    for t in range(5):
        st = apply(s, next(a for a in legal_actions(s) if a.kind == 'target' and a.target == t))
        c = C.Computer('O', 'starter', seed=1, habits=[])
        c._context(st)
        assert c.targets(C.seen_state(st, 'O', c.seen))[0]['o'] == t


def test_need_a_three_only_three_point_targets():
    s = scenario_state(6)
    c = C.Computer('O', 'allstar', seed=1, habits=[])
    c._context(s)
    assert all(t['shot'] == 'three' for t in c.targets(C.seen_state(s, 'O', c.seen)))


def test_patience_and_the_last_phase():
    c = C.Computer('O', 'starter', seed=1, habits=[])
    s = table()
    c._context(s)
    from playmaker_engine.solver import Play
    shot = Play('shoot', (Action('shot', 'O', 0, shot='three'),))
    assert not c._patient(s, shot, 9.0)                       # clock 12: below the curve, keep building
    late = s.with_(clock=2)
    assert c._patient(late, shot, 9.0)                        # the last phase: take the best shot there is


def test_risk_a_pass_through_a_reachable_lane_is_worth_less():
    from playmaker_engine.solver import Play
    c = C.Computer('O', 'starter', seed=1, budget_s=None, habits=[])
    s = table()
    c._context(s)
    p = Play('kick', (Action('pass', 'O', 0, target=2),))
    from playmaker_engine.solver import apply_play
    fn = c._value_fn()
    lane = c._node_value(apply_play(s, p), fn)                 # X3 on N8 can step onto the I11-O9 line
    clear_s = s.with_(x=s.x[:2] + ((16, 13),) + s.x[3:])       # X3 far away in the corner
    c2 = C.Computer('O', 'starter', seed=1, budget_s=None, habits=[])
    c2._context(clear_s)
    clear = c2._node_value(apply_play(clear_s, p), c2._value_fn())
    assert lane < clear


def test_golden_position_all_star_finds_a_line_worth_27():
    from playmaker_engine.soak import golden_setup
    from playmaker_engine.calibrate import solver_gap
    from playmaker_engine.solver import Searcher
    from playmaker_engine.solver_config import with_config
    s = golden_setup()
    for a in (Action('pass', 'O', 0, target=2), Action('move', 'X', 2, P('L10'), 7)):
        s = apply(s, a)
    from playmaker_engine.resolve import force
    s = force(apply(s, Action('intercept', 'X', 2)), 'success')
    for a in (Action('move', 'O', 2, P('N7')), Action('move', 'O', 0, P('G10')), Action('move', 'X', 4, P('N6'), 0),
              Action('move', 'X', 0, P('H9'), 7)):
        s = apply(s, a)
    c = C.Computer('O', 'allstar', seed=1, budget_s=3.0, habits=[])
    a = c.choose(s)
    se = Searcher(with_config(eval_turns=1, top_k_raw=0, endgame_tokens=-1))
    se.root_depth = 2
    se.value(s, 2)
    e = se.tt[(s, 2)]
    mine = [v[0].ev for p, v in e.children if p.actions[0] == a]
    assert mine and max(mine) >= 27 - 1e-6, (a, mine)                     # the step-back three: QS O8, then shoot
    assert c.queue and c.queue[1] and c.queue[1][0].kind == 'shot'


# ---- section 8: levels, habits, tunnel vision, card reading, no cheating -------------------------

def test_presets_load():
    for side in ('O', 'X'):
        for lv in C.LEVEL_NAMES:
            c = C.Computer(side, lv, seed=3)
            part = C.LEVELS['defence' if side == 'X' else 'offence']['levels'][lv]
            assert c.cfg == part and len(c.habits) == part['habits'] and c.level == lv
    assert C.Computer('X', 'rookie').comfort == 21 and C.Computer('X', 'allstar').comfort == 15


def test_habit_jumps_first_pass_fires_every_time():
    s = apply(table(), Action('pass', 'O', 0, target=2))
    c = C.Computer('X', 'allstar', seed=1, habits=['jumps_first_pass'], budget_s=None)
    for _ in range(3):
        if not any(a.kind == 'intercept' for a in legal_actions(s)):
            break
        assert c.choose(s).kind == 'intercept'


def test_habit_nearest_closes_out_fires_every_time():
    s = shot_declared()
    st = apply(s, Action('end_turn', 'X'))
    assert st.stage == 'contest'
    c = C.Computer('X', 'allstar', seed=1, habits=['nearest_closes_out'], budget_s=None)
    a = c.choose(st)
    sp = st.o[st.ball]
    near = min((x.piece for x in legal_actions(st) if x.piece >= 0), key=lambda j: (B.cheb(st.x[j], sp), j))
    assert a.piece == near


def test_habit_never_screens():
    from playmaker_engine.policies import play
    for n in (7, 13):
        acts = []
        play(scenario_state(n), C.Computer('O', 'starter', seed=n, habits=['never_screens']),
             C.Computer('X', 'rookie', seed=n), seed=n, check=lambda b, a, s: acts.append(a))
        assert not any(a.kind == 'screen' for a in acts if a.side == 'O')


def test_tunnel_vision_sees_exactly_the_n_nearest():
    c = C.Computer('X', 'rookie', seed=1)
    s = table()
    c._context(s)
    vis = c.ev.visible(s)
    cp = s.o[s.ball]
    order = sorted(range(5), key=lambda i: (i != s.ball, B.cheb(s.o[i], cp), i))
    assert vis == set(order[:2])
    assert c.ev.carrier_look(s, order[4], 2, True)[0] == 0.0


def test_marks_reading_never_uses_an_exact_number():
    s = table()
    seen = C.seen_context(s.ctx, 'marks')
    mid = C._mids()[0]
    for real, card in zip(s.ctx.off + s.ctx.dfn, seen.off + seen.dfn):
        for r, v in card.r.items():
            assert v == mid[(r, real.bands[r])]
    role = C.seen_context(s.ctx, 'role')
    assert all(c.r == role.off[0].r for c in role.off if C._POS[c.key] == C._POS[role.off[0].key])


def test_no_cheating_the_defence_never_reads_the_coachs_call_target():
    s = scenario_state(8)
    picks = set()
    for t in range(5):
        st = apply(s, next(a for a in legal_actions(s) if a.kind == 'target' and a.target == t))
        while st.side == 'O' and st.stage == 'play':
            st = apply(st, next(a for a in legal_actions(st) if a.kind in ('hesitate', 'end_turn', 'move')))
            if isinstance(st, ChanceNode):
                break
        if isinstance(st, ChanceNode) or st.side != 'X':
            continue
        c = C.Computer('X', 'starter', seed=1, habits=[], overrides={'randomness': 0.0}, budget_s=None)
        picks.add(str(c.choose(st)))
        assert C.seen_state(st, 'X', st.ctx).target == -1
    assert len(picks) == 1, picks


def test_about_the_computer_names_the_habits_and_missing_concepts():
    from playmaker_web.game import Game
    g = Game(mode='hotseat', scenario=6, seed=4, level='pro', ai=dict(O='rookie', X='starter'))
    assert g.state.stage == 'over'
    setup = g.read_log()[0]['computer']
    r = g.review(g.tokens['both'])
    text = ' '.join(r['computer'])
    for side in ('O', 'X'):
        for h in setup[side]['habits']:
            assert C.LEVELS['habit_words'][h] in text
        for k in setup[side]['concepts_off']:
            assert C.LEVELS['concept_words'][k] in text
    assert 'Rookie' in text and 'Starter' in text


def test_about_the_computer_waits_for_the_end():
    from playmaker_web.game import Game, GameError
    g = Game(mode='hotseat', scenario=6, seed=4, level='pro', ai=dict(X='starter'))
    with pytest.raises(GameError):
        g.review(g.tokens['both'])
    from playmaker_web.view import state_json
    assert 'About the computer' not in json.dumps(state_json(g, g.tokens['both']))


def test_help_the_golden_setup_still_contests_every_kick_out_cleanly():
    """All-Star's setup on the preview table: its arrows do more than face their men, and a kick-out to
    any attacker still meets a clean contest after the reaction."""
    from playmaker_web.game import Game
    from playmaker_engine.defence import arrow_job
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], full=True, place=True, seed=1, level='pro', ai=dict(X='allstar'))
    g.place(g.tokens['both'], dict(squares=TABLE_O, ball=0))
    s = g.state
    assert any(arrow_job(s, j) in ('wall', 'lane', 'help') for j in range(5))
    for i in range(1, 5):
        rc = C.reachable_contest(s.with_(ball=i), i)
        assert rc and rc[0]['clean'], (i, rc[:2])


def test_drain_only_the_reserve_aware_levels_see_the_closeout_tax():
    """The only closeout defender's Move spent: All-Star (drain on) values the shot higher; Starter (drain
    off: it assumes the defence can always react) sees no difference."""
    s = shot_declared()
    before = C.reachable_contest(s)[0]
    tired = list(s.cnt)
    tired[CI['x_qs']] = 2
    drained = s.with_(moved_x=0b11111, cnt=tuple(tired))
    after = C.reachable_contest(drained)[0]
    assert after['value'] > before['value']
    vals = {}
    for lv in ('starter', 'allstar'):
        c = C.Computer('O', lv, seed=1, budget_s=None, habits=[])
        c._context(s)
        vals[lv] = (c.ev(s)[0].ev, c.ev(drained)[0].ev)
    assert vals['allstar'][1] > vals['allstar'][0]
    assert vals['starter'][1] == pytest.approx(vals['starter'][0])
