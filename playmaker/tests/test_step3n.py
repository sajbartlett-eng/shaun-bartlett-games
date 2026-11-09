"""Step 3n: the JavaScript search core, the designer rulings F1-F4, and the fixes to the step 3m engine and trainer."""
import json
import random
import shutil

import pytest

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply, ChanceNode, force
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import contest_options

needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node')
DIGITAL = RC.with_rules(digital=True)
TABLE = RC.DEFAULT_RULES


def _state(o, x, arrows, ball=0, rules=DIGITAL, **kw):
    s = game_state('Five Out', 'Iron Wall', o, x, arrows, ball=ball, rules=rules, check=False,
                   team_fouls=kw.pop('team_fouls', 0), quarter_left=kw.pop('quarter_left', 0))
    return s.with_(**kw) if kw else s


def _steal_board(rules=DIGITAL, x1='I8', **kw):
    # O1 on I9 with the ball; X1 next to him facing him (I8 is closer to the rim than I9; H9 is level)
    s = _state(['I9', 'C9', 'O9', 'E4', 'M4'], [x1, 'D8', 'N8', 'F4', 'L4'],
               [B.dir_between(B.parse_sq(x1), B.parse_sq('I9')), 0, 0, 0, 0], rules=rules, **kw)
    s = s.with_(side='X')
    assert Action('steal', 'X', 0) in legal_actions(s)
    return s


# ---- A: the JavaScript port ---------------------------------------------------------------------------------------

@needs_node
def test_javascript_and_python_agree_on_random_legal_states():
    """A3 (the full 2,000-state run is tools/js_equivalence.py, docs/3n_equivalence.json): legal actions, reach maps,
    every threat value and square, the best cover and its value, and the leaf value agree exactly."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
    from js_equivalence import random_state, py_probe, run_js, close
    from playmaker_engine.jsbridge import state_json, ctx_json
    rng = random.Random(3)
    states = [random_state(rng)[0] for _ in range(60)]
    js = run_js([json.dumps(dict(state=state_json(s), ctx=ctx_json(s.ctx))) for s in states])
    for s, b in zip(states, js):
        a = py_probe(s)
        assert 'error' not in b, b
        for k, v in a.items():
            assert close(v, b.get(k)), (k, s.encode())


@needs_node
def test_javascript_search_matches_python_search_at_fixed_depth():
    """The search itself (whole turns, Star2, the transposition table, killers and history): same values, same leaves."""
    from playmaker_engine import agent as AG
    from playmaker_engine.jsbridge import NodeEngine, state_json, ctx_json
    from playmaker_engine.search import Searcher, actor
    eng = NodeEngine()
    try:
        s = _steal_board()
        ag = AG.Agent('X', 'starter')
        sr = Searcher('X', ag.p, ag._evaluate(s), float('inf'))
        res, reached = sr.root(s, 2)
        out = json.loads(eng.call('searchJSON', json.dumps(dict(state=state_json(s), ctx=ctx_json(s.ctx), profile=ag.p,
                                                                   budget=None, max_depth=2))))
        assert reached == out['reached'] == 2 and sr.leaves == out['leaves']
        assert [round(v, 9) for v, _ in res] == [round(v, 9) for v, _ in out['results']]
    finally:
        eng.close()


# ---- F1: a failed Steal locks the defender --------------------------------------------------------------------------

@pytest.mark.parametrize('rules', [DIGITAL, TABLE], ids=['digital', 'tabletop'])
def test_a_failed_steal_locks_the_defender_who_keeps_only_his_quick_step(rules):
    s = _steal_board(rules)
    node = apply(s, Action('steal', 'X', 0))
    kept = force(node, 'no foul', 'kept')
    assert not isinstance(kept, ChanceNode) and kept.locked('X', 0)
    if kept.side == 'X':
        mine = [a for a in legal_actions(kept) if a.piece == 0 and a.side == 'X']
        assert mine and all(a.kind == 'qs' for a in mine if a.kind in ('move', 'qs', 'sprint'))
        assert not any(a.kind in ('move', 'sprint') for a in mine)
    from playmaker_engine.actions import can_move_kind
    assert not can_move_kind(kept.with_(side='X', tok_x=4), 'X', 0, 'move')
    assert not can_move_kind(kept.with_(side='X', tok_x=4), 'X', 0, 'sprint')
    assert can_move_kind(kept.with_(side='X', tok_x=4), 'X', 0, 'qs')


# ---- F2: the angle of a reach -----------------------------------------------------------------------------------------

def _foul_depth(node):
    """How many foul rolls the node asks for before the security roll."""
    n = 0
    while isinstance(node, ChanceNode) and any(l == 'foul' for _, l, _ in node.outcomes):
        n += 1
        node = next(sub for _, l, sub in node.outcomes if l == 'no foul')
    return n


def test_a_reach_from_closer_to_the_rim_makes_one_foul_roll_level_or_behind_two():
    front = apply(_steal_board(x1='I8'), Action('steal', 'X', 0))       # closer to the rim than the carrier
    side = apply(_steal_board(x1='H9'), Action('steal', 'X', 0))        # level with him
    behind = apply(_steal_board(x1='I10'), Action('steal', 'X', 0))     # further from the rim
    assert _foul_depth(front) == 1 and _foul_depth(side) == 2 and _foul_depth(behind) == 2
    assert 'two foul rolls' in side.what and 'Reaching from the side or behind' in side.what.replace('reaching', 'Reaching')


def test_contest_foul_rolls_follow_the_same_angle_and_the_minus_three_is_unchanged():
    # shooter O1 on I6 (mid); X1 on I5 (closer, arrow off him), on H6 (level, arrow off), on I7 (behind, arrow off)
    def opt(xsq, arrow):
        s = _state(['I6', 'C9', 'O9', 'E4', 'M4'], [xsq, 'D8', 'N8', 'F4', 'L4'], [arrow, 0, 0, 0, 0])
        o = [o for o in contest_options(s, 0, 'mid') if o.defender == 0][0]
        return o, s
    closer, s = opt('I5', B.DIR_NAMES.index('S'))
    level, _ = opt('H6', B.DIR_NAMES.index('W'))
    further, _ = opt('I7', B.DIR_NAMES.index('N'))
    assert not closer.clean and closer.rolls == 1
    assert not level.clean and level.rolls == 2
    assert not further.clean and further.rolls == 2
    con = s.ctx.dfn[0].con('mid')
    assert closer.contest == max(0, con) and level.contest == max(0, con) and further.contest == max(0, con - 3)
    assert abs(float(further.p_foul) - (1 - (1 - min(20, max(0, s.ctx.dfn[0].r['foul_contest'])) / 20) ** 2)) < 1e-12


# ---- F3: team fouls across a quarter (digital), the tabletop rule kept -------------------------------------------------

def test_the_bonus_starts_at_the_fifth_team_foul():
    four = force(apply(_steal_board(team_fouls=4, quarter_left=8), Action('steal', 'X', 0)), 'foul')
    three = force(apply(_steal_board(team_fouls=3, quarter_left=8), Action('steal', 'X', 0)), 'foul')
    assert four.stage == 'over' and four.result.kind == 'free_throws'          # the 5th: free throws, possession over
    assert three.stage != 'over' and three.bonus5 == 1                          # the 4th: +5 and play on


def test_the_tabletop_format_keeps_its_within_possession_rule():
    s = _steal_board(TABLE, team_fouls=9)                  # team fouls mean nothing at the table
    first = force(apply(s, Action('steal', 'X', 0)), 'foul')
    assert first.stage != 'over' and first.bonus5 == 1
    second = force(apply(_steal_board(TABLE).with_(fouls=1), Action('steal', 'X', 0)), 'foul')
    assert second.stage == 'over' and second.result.kind == 'free_throws'


def test_a_shooting_foul_counts_toward_the_team_total():
    s = _state(['I6', 'C9', 'O9', 'E4', 'M4'], ['H6', 'D8', 'N8', 'F4', 'L4'], [B.DIR_NAMES.index('W'), 0, 0, 0, 0])
    s = s.with_(stage='contest', side='X', shot='mid')
    fouled = force(apply(s, Action('contest', 'X', 0)), 'foul')
    assert fouled.result.kind == 'free_throws' and fouled.fouls == 1


def test_team_fouls_carry_across_matches_for_the_pairing_and_reset_after_eighteen_possessions_each():
    from playmaker_web.game import Game
    q = dict(fouls=dict(A=2, B=3), poss=dict(A=17, B=17), number=2)
    g = Game(ai={'A': 'rookie', 'B': 'rookie'}, level='learn', seed=5, match_format='digital', per_side=4, place=True,
             quarter=q)
    first_def = 'B' if g.scores[0]['attacker'] == 'A' else 'A'
    assert g.scores                                                   # the computers played possession 1
    assert g.quarter['poss'][g.scores[0]['attacker']] == 18           # carried in, counted on
    assert g.quarter['fouls'][first_def] >= q['fouls'][first_def]
    g.next_possession(g.tokens['both'])
    assert g.quarter == dict(fouls=dict(A=0, B=0), poss=dict(A=0, B=0), number=3)     # both had 18: reset
    words = g.quarter_words()['text']
    assert words.startswith('Team fouls 0 · bonus from the 5th · 18 possessions left this quarter')


def test_the_possession_sees_the_defences_team_fouls_before_it():
    from playmaker_web.game import Game
    g = Game(ai={'A': 'rookie', 'B': 'rookie'}, level='learn', seed=6, match_format='digital', per_side=4, place=True,
             quarter=dict(fouls=dict(A=1, B=4), poss=dict(A=3, B=3), number=1))
    att = g.scores[0]['attacker']
    dfn = 'B' if att == 'A' else 'A'
    assert g.state.ctx.team_fouls == dict(A=1, B=4)[dfn] and g.state.ctx.quarter_left == 18 - 3


# ---- F4: the engine prices a foul by the quarter --------------------------------------------------------------------

@needs_node
def test_all_star_reaches_with_no_team_fouls_and_declines_with_four():
    """A marginal steal board (found by search over random boards, docs/3n report): the same position with 0 and with 4
    team fouls (10 possessions left). The reason is in plain words."""
    from playmaker_engine import agent as AG
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    try:
        out = {}
        for tf in (0, 4):
            s = _state(['L8', 'H7', 'K4', 'D6', 'N7'], ['K8', 'B9', 'B11', 'O1', 'K5'], [2, 4, 6, 4, 6], team_fouls=tf,
                       quarter_left=10)
            s = apply(s, Action('hesitate', 'O'))
            ag = AG.Agent('X', 'allstar', seed=1)
            ag.p = dict(ag.p, time_budget_s=1000.0, depth=[1, 2], noise=0.0, variety_margin=0)
            a = ag.choose(s)
            out[tf] = (a.kind, ag.last.get('reason') or '')
    finally:
        eng.close()
    assert out[0][0] == 'steal' and out[0][1].startswith('Reached for the steal')
    assert out[4][0] != 'steal' and "a foul now would be their 5th team foul" in out[4][1]
    for _, why in out.values():
        assert not any(t in why.lower() for t in ('value', 'leaf', 'residual'))


def test_the_foul_price_rises_toward_the_bonus_and_vanishes_inside_it():
    from playmaker_engine.decide import foul_marginal
    ctx = _state(['L8', 'H7', 'K4', 'D6', 'N7'], ['K8', 'B9', 'B11', 'O1', 'K5'], [2, 4, 6, 4, 6]).ctx
    m = [foul_marginal(ctx, f, 10) for f in range(6)]
    assert m[0] < m[1] < m[2] < m[3] and m[4] == m[5] == 0.0
    assert foul_marginal(game_state('Five Out', 'Iron Wall', ['L8', 'H7', 'K4', 'D6', 'N7'], ['K8', 'B9', 'B11', 'O1', 'K5'],
                                    [2, 4, 6, 4, 6], check=False).ctx, 0, 10) == 0.0        # tabletop: no quarter


# ---- C: the phase table ---------------------------------------------------------------------------------------------

def test_the_phase_table_counts_every_possession_alive_at_the_start_of_the_phase():
    """A possession that turns over late still counts in the early phases: V_k is the mean final score of the
    possessions alive at the start of phase k, so a late selection of good possessions can't lift it."""
    from playmaker_engine.decide import solve_phase_table
    recs = [([(1, 'a|0|1|3|32'), (2, 'a|0|2|3|32')], 30), ([(1, 'a|0|1|3|32')], 0), ([(1, 'b|0|1|3|32')], 20)]
    V = solve_phase_table(recs, prior=0)
    assert V['_phase1'] == round((30 + 0 + 20) / 3, 2) and V['_phase2'] == 30.0
    assert V['_alive1'] == 3 and V['_alive2'] == 1
    assert V['a|0|1|3|32'] == 15.0                           # (V(phase-2 key) = 30, and 0) / 2


@pytest.mark.xfail(strict=False, reason='Step 3n C finding: at Senior Pro V rises from phase 1 (24.6) to phase 2 (27.2), '
                   'beyond one standard error (1.3): half the turnovers (9 of 18, at 0) come in phase 1, so surviving it '
                   'lifts a possession. From phase 2 on V is flat within sampling error. Reported for the designer.')
def test_v_by_phase_never_rises_at_senior_pro():
    """Step 3n C: the shipped table at Senior Pro, within sampling error (one standard error of the later phase)."""
    import json as _j
    import os
    from playmaker_engine.decide import HERE
    tab = _j.load(open(os.path.join(HERE, 'data', 'vcoarse.json')))['senior/pro']
    se = tab.get('_se', {})
    for k in range(1, 6):
        a, b = tab[f'_phase{k}'], tab[f'_phase{k + 1}']
        assert b <= a + se.get(str(k + 1), 0.0) + 1e-9, (k, a, b, se)


# ---- D: the answering defender ---------------------------------------------------------------------------------------

def test_credit_names_the_helper_who_answered_the_decoy():
    from playmaker_engine import trainer as TR
    from playmaker_engine.exam import board
    s = board(['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'D4', 'N4'], ['N', 'W', 'E', 'E', 'W'])
    a = Action('move', 'O', 1, dest=B.parse_sq('D9'))             # O2 lifts; X3 leaves the far side to answer
    c = TR.credit(s, [a])[0]
    assert c['indirect'] >= TR.TC['inaccuracy'] and c['moved'] == 2
    _, with_ = TR._cf(s, [a], 0, 0.4, 'phase')
    _, without = TR._cf(s, [], 0, 0.4, 'phase')
    assert with_.x[2] != without.x[2]                             # his reply differs between the counterfactuals


# ---- E: accuracy ----------------------------------------------------------------------------------------------------

def test_accuracy_averages_the_harmonic_and_the_volatility_weighted_means():
    from playmaker_engine import trainer as TR
    k = TR.TC['accuracy_k']
    accs = [100.0, 100 * __import__('math').exp(-8 / k)]
    harmonic = 2 / sum(1 / a for a in accs)
    weighted = (accs[0] * 1 + accs[1] * 3) / 4
    assert TR.accuracy([0.0, 8.0], weights=[1, 3]) == round(0.5 * (harmonic + weighted), 1)
    assert TR.accuracy([0.0, 0.0, 0.0, 20.0]) > 30            # one blunder shows without zeroing the rest


# ---- G: the recogniser ------------------------------------------------------------------------------------------------

def test_shots_never_appear_as_unnamed_actions_and_hesitates_are_flagged():
    from playmaker_engine import labels as LB
    s = _state(['I6', 'C9', 'O9', 'E4', 'M4'], ['H9', 'D8', 'N8', 'F4', 'L4'], [0, 0, 0, 0, 0])
    shot = Action('shot', 'O', 0, shot='mid')
    after = apply(s, shot)
    assert LB.unnamed([(s, shot, after)], []) == []
    assert 'G4' in LB.EXTRA and all(v for v in LB.EXTRA.values())


# ---- J: legibility ----------------------------------------------------------------------------------------------------

def _literals():
    import os
    import re
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'playmaker_web', 'static')
    lit = re.compile(r"'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"|`(?:[^`\\]|\\.)*`", re.S)
    for f in ('app.js', 'trainer.js', 'coach.js', 'records.js', 'notation.js', 'index.html'):
        src = open(os.path.join(root, f)).read()
        if f.endswith('.html'):
            items = re.findall(r'>([^<]+)<', src) + re.findall(r'(?:title|aria-label|placeholder)="([^"]+)"', src)
        else:
            items = [m.group(0)[1:-1] for m in lit.finditer(re.sub(r'^\s*//.*$', '', src, flags=re.M))]
        for t in items:
            if re.fullmatch(r'[a-z0-9_\-#.:/ ]*', t) and ' ' not in t.strip():
                continue                                          # identifiers, classes, keys: not shown
            yield f, t


def test_no_banned_term_in_any_interface_string_or_template():
    from playmaker_engine.plain import check
    bad = [(f, t[:120], check(t)) for f, t in _literals() if check(t)]
    assert not bad, bad


@needs_node
def test_trainer_summaries_and_why_read_in_plain_words():
    """A real possession (computers on the JavaScript core), read by the trainer: every line a player sees passes the
    banned-term check, numbers are whole, and a change is never '+0'."""
    import re
    from playmaker_engine import selfplay, trainer as TR, plain as PL
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    try:
        r = selfplay.possession('Five Out', 'Iron Wall', ('rookie', 'starter'), 11, 0.1, keep=True)
    finally:
        eng.close()
    out = TR.read_possession(r['triples'], 'O', budget=0.1)
    texts = [p['text'] for p in out['summary']]
    for g in out['groups']:
        texts += [g.get('actions_text') or '', g.get('better_text') or '']
        texts += [f['text'] for f in g.get('flags', [])]
        texts += [c.get('action_text', '') for c in g.get('credits', [])]
        if g.get('goal'):
            texts += [str(v) for v in g['goal'].values() if isinstance(v, str)]
    assert texts and out['summary']
    for t in texts:
        assert not PL.check(t), t
        assert not re.search(r'\d\.\d', t), t                    # whole numbers
        assert '+0' not in t, t


def test_rating_shows_a_confidence_word_never_plus_minus():
    from playmaker_engine.plain import confidence
    assert confidence(300) == 'still settling' and confidence(60) == 'settled'


# ---- K: the rules register ---------------------------------------------------------------------------------------

def test_every_shared_rule_has_identical_values_in_both_formats():
    from playmaker_engine import register as RG
    dig, tab = RC.with_rules(digital=True), RC.DEFAULT_RULES
    shared = [e for e in RG.ENTRIES if e[1] == RG.SHARED]
    assert len(shared) > 40
    for name, _, src, _, _ in shared:
        assert RG.value(dig, src) == RG.value(tab, src), name
    named = {e[2].get('rules') for e in RG.ENTRIES}
    from dataclasses import fields
    assert all(f.name in named for f in fields(RC.Rules))          # every setting is in the register
    import os
    doc = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'rules_register.md')).read()
    assert doc == RG.markdown()                                     # the document is the register


def test_shared_mechanisms_roll_the_same_dice_in_both_formats():
    """The code never applies different numbers to a shared rule by format: the same position in each format offers the
    same actions and every roll has the same odds (only the declared splits change what an outcome is worth)."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
    from js_equivalence import random_state
    from playmaker_engine.state import Context
    rng = random.Random(9)
    n = 0
    while n < 40:
        s, _ = random_state(rng)
        if s.stage != 'play':
            continue
        c = s.ctx
        other = Context(c.off, c.dfn, RC.with_rules(digital=not c.rules.digital))
        t = s.with_(ctx=other)
        la, lb = legal_actions(s), legal_actions(t)
        assert la == lb
        for a in la:
            if a.kind in ('move', 'qs', 'sprint'):
                continue
            x, y = apply(s, a), apply(t, a)
            px = [p for p, _, _ in x.flatten()] if isinstance(x, ChanceNode) else [1]
            py = [p for p, _, _ in y.flatten()] if isinstance(y, ChanceNode) else [1]
            assert sorted(px) == sorted(py), (a, s.encode())
        n += 1


def test_a_tabletop_game_is_graded_with_tabletop_costs():
    """The same risky pass graded in each format: the table plays on after an interception at -5, the digital game ends
    the possession at 0, and the grade follows the format the game was played in."""
    from playmaker_engine import trainer as TR
    o, x = ['I11', 'B7', 'P7', 'A3', 'Q3'], ['I10', 'C7', 'O7', 'B3', 'M7']     # X5 stands on the lane to O5
    ar = [0, 6, 2, 6, 7]
    vals = {}
    for name, rules in (('digital', DIGITAL), ('tabletop', TABLE)):
        s = _state(o, x, ar, rules=rules)
        p = Action('pass', 'O', 0, target=4)
        assert p in legal_actions(s)
        vals[name] = TR.group_value(s, [p])
    assert vals['digital'] != vals['tabletop']
    from playmaker_engine.decide import turnover_value, vcoarse
    st = _state(o, x, ar, rules=TABLE)
    # the table: -5, the clock loses a phase, play goes on; digital: the possession is over at 0
    assert turnover_value(st) == -5 + vcoarse(st.with_(clock=st.clock - 2))
    assert turnover_value(_state(o, x, ar, rules=DIGITAL)) == 0.0
