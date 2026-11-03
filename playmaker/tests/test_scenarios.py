"""Scenario cards: loading, the checker's checks, printed boards, and each card's special rule."""
import json
import os
import subprocess
import sys

import pytest
from conftest import P

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply, force, ChanceNode
from playmaker_engine.scenarios import SCENARIOS, scenario_state, scenario_layout
from playmaker_engine.scoring import score

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'playmaker_engine', 'data')


def kinds(s):
    return {a.kind for a in legal_actions(s)}


@pytest.mark.parametrize('n', sorted(SCENARIOS))
def test_scenario_loads_and_passes_checks(n):
    O, X, arrows, errs = scenario_layout(n)
    assert errs == []
    st = scenario_state(n, target=0)
    assert len(set(st.o) | set(st.x)) == 10
    sc = SCENARIOS[n]
    for k, (sq, (mode, tgt)) in sc['X'].items():
        if mode == 'ball':
            assert B.cheb(P(sq), O[tgt]) == 1                         # on-ball defenders adjacent
        if mode == 'deny':
            p, ball = P(sq), O[sc['ball']]
            on = B.on_segment(p, ball, O[tgt], 0) or p in (ball, O[tgt])
            assert on or B.seg_cross(p, B.add(p, B.DIRS[arrows[k]], 30), ball, O[tgt])   # deny arrow crosses its lane
    if sc.get('inb'):
        p = O[sc['inb']]
        assert not B.on_board(p) and ((p[1] == 0 and 0 <= p[0] < B.W) or (p[0] in (-1, B.W) and 1 <= p[1] <= B.H))


def test_arrows_match_check_scenarios_output():
    ref = json.load(open(os.path.join(DATA, 'scenario_arrows.json')))
    for n in SCENARIOS:
        _, _, arrows, _ = scenario_layout(n)
        assert {str(k): v * 45 for k, v in arrows.items()} == {k: v for k, v in ref[str(n)].items()}, n


def test_check_scenarios_script_still_passes():
    out = subprocess.run([sys.executable, os.path.join(DATA, 'check_scenarios.py')], capture_output=True, text=True,
                         cwd=DATA).stdout
    assert 'failures 0' in out


def parse_board(text):
    """Read piece labels back off the printed board."""
    found = {}
    rows = text.splitlines()[1:B.H + 2]          # header, then rows 14 .. 1, then the off-board row 0
    for idx, line in enumerate(rows):
        y = B.H - idx
        for x in range(-1, B.W + 1):
            off = 3 + (x + 1) * 7
            cell = line[off:off + 7].strip()
            if cell[:1] in 'OX' and cell[1:2].isdigit():
                found[cell[:2]] = ((x, y), cell[2:])
    return found


@pytest.mark.parametrize('n', sorted(SCENARIOS))
def test_printed_board_matches_card(n):
    st = scenario_state(n, target=0)
    found = parse_board(st.board())
    sc = SCENARIOS[n]
    _, _, arrows, _ = scenario_layout(n)
    for k, sq in sc['O'].items():
        assert found[f'O{k}'][0] == P(sq)
    assert '*' in found[f'O{sc["ball"]}'][1]
    for k, (sq, _) in sc['X'].items():
        pos, tail = found[f'X{k}']
        assert pos == P(sq) and tail.rstrip('L') == B.DIR_NAMES[arrows[k]]


# ---- each card's rule --------------------------------------------------------------------

def test_inbounds_clock_frozen_two_phases_then_turnover():
    s = scenario_state(1)
    assert s.inbound == 1 and s.ball == 4 and not B.on_board(s.o[4])
    ib_acts = [a for a in legal_actions(s) if a.piece == 4]
    assert {a.kind for a in ib_acts} == {'pass'}                       # the inbounder can't move
    # burn phase 1 and 2 without passing
    for phase in (1, 2):
        s = s.with_(side='X', tok_x=1, turn_n=0)
        s = apply(s, Action('qs', 'X', 4, P('L1')) if phase == 1 else Action('pause', 'X'))
        if phase == 1:
            assert s.inbound == 2 and s.clock == 8 and s.ball == 4
    assert s.inbound == 0 and s.tos == 1 and s.clock == 8
    # O1 (G6) and O2 (K6) tie for furthest from the rim: the offence chooses (ruling OQ-27).
    assert s.stage == 'pick' and s.side == 'O'
    picks = legal_actions(s)
    assert [(a.kind, a.target) for a in picks] == [('pick', 0), ('pick', 1)]
    s2 = apply(s, picks[1])
    assert s2.stage == 'play' and s2.ball == 1 and s2.tok_o == 6


def test_failed_inbound_tie_lowest_number_alternative():
    from playmaker_engine.rules_config import with_rules
    s = scenario_state(1, rules=with_rules(inbound_tie='lowest'))
    for _ in (1, 2):
        s = apply(s.with_(side='X', tok_x=1, turn_n=0), Action('pause', 'X'))
    assert s.stage == 'play' and s.ball == 0


def test_inbound_pass_lands_new_phase_card_clock():
    s = scenario_state(3)                                              # inbounder O3 at R9
    s = apply(s, Action('pass', 'O', 2, target=0))
    assert s.side == 'X'
    acts = legal_actions(s)
    assert Action('end_turn', 'X') in acts                             # let it in
    s2 = apply(s, Action('end_turn', 'X'))
    assert s2.inbound == 0 and s2.ball == 0 and s2.clock == 8 and s2.phase == 2 and s2.tok_o == 6
    moves = [a for a in legal_actions(s2) if a.piece == 2 and a.kind == 'move']
    assert moves and all(B.on_board(a.dest) for a in moves)            # inbounder may step on


def test_need_a_three_only_threes_score():
    s = scenario_state(6)
    s = s.with_(o=(P('I8'),) + s.o[1:], x=(P('A14'),) + s.x[1:])
    end = apply(apply(s, Action('shot', 'O', 0, shot='long')), Action('end_turn', 'X'))
    assert score(end).total == 0
    s2 = s.with_(o=(P('J10'),) + s.o[1:])
    end2 = apply(apply(s2, Action('shot', 'O', 0, shot='three')), Action('end_turn', 'X'))
    assert score(end2).total == 3 * s.ctx.off[0].shot('three')


def test_two_or_three_results():
    s = scenario_state(7)
    sc = score(apply(apply(s.with_(o=(P('J10'),) + s.o[1:], x=(P('A14'),) + s.x[1:]),
                           Action('shot', 'O', 0, shot='three')), Action('end_turn', 'X')))
    assert sc.late_clock == ('win' if sc.look >= 30 else 'loss')
    s5 = s.with_(ball=4, o=s.o[:4] + (P('I3'),), x=s.x[:4] + (P('A14'),))
    sc5 = score(apply(apply(s5, Action('shot', 'O', 4, shot='dunk')), Action('end_turn', 'X')))
    assert sc5.look >= 30 and sc5.late_clock == 'tie'


def test_late_clock_reset_constraints():
    s = scenario_state(10)
    assert (s.tok_o, s.tok_x, s.clock) == (4, 4, 4)
    assert 'screen' not in kinds(s)                                    # both Screens spent
    scr = s.screen_of(4)
    assert scr and B.add(s.o[4], B.DIRS[scr[1]]) == P('J2') == s.x[4]  # O5's T on X5
    s = apply(s, Action('move', 'O', 0, P('I12')))
    s = apply(s, Action('end_turn', 'O'))
    assert s.screen_of(4) is None                                      # flips back after the offence's turn


def test_in_the_bonus():
    s = scenario_state(15)
    assert s.fouls == 1 and s.bonus5 == 1
    s = s.with_(side='X')
    end = force(apply(s, Action('steal', 'X', 0)), 'foul')
    sc = score(end)
    assert end.stage == 'over' and sc.free_throws > 0 and sc.bonus == 5


def test_hold_for_one():
    s = scenario_state(14).with_(o=(P('I9'),) + scenario_state(14).o[1:], x=(P('A14'),) + scenario_state(14).x[1:])
    assert 'shot' not in kinds(s)
    assert 'shot' in kinds(s.with_(clock=2))
    st = scenario_state(14).with_(side='X')
    end = force(apply(st, Action('steal', 'X', 0)), 'no foul', 'stolen')
    assert end.stage == 'over' and score(end).total == 0


def test_star_locked():
    s = scenario_state(16)
    assert s.locked('O', 0)
    k = {a.kind for a in legal_actions(s) if a.piece == 0}
    assert 'move' not in k and 'sprint' not in k and 'pass' in k and 'qs' in k


def test_coach_call_target_is_first_decision():
    s = scenario_state(8)
    assert s.stage == 'target' and [a.kind for a in legal_actions(s)] == ['target'] * 5
    s = apply(s, legal_actions(s)[2])
    assert s.stage == 'play' and s.target == 2
