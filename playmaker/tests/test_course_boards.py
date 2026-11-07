"""Every move the course draws on its whiteboards is a legal action of the engine from that board. The lesson boards
are hand-authored in coach.js; tools/dump_lessons.js reads them out, and this test rebuilds each board as a game state
and asks the engine. (Marks are checked one at a time from the lesson's starting board, each from the side that plays
it; a lesson that tells a story in turns is checked in order, applying each mark when the engine lets it.)"""
import json
import os
import shutil
import subprocess

import pytest

from playmaker_engine import board as B
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply, ChanceNode, force
from playmaker_engine.scenarios import game_state

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOVEMENT = {'move', 'qs', 'sprint'}


def lessons():
    if not shutil.which('node'):
        pytest.skip('node is needed to read the course boards')
    out = subprocess.run(['node', os.path.join(ROOT, 'tools', 'dump_lessons.js')], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def start(board, side):
    o = [p['sq'] for p in board['o']]
    x = [p['sq'] for p in board['x']]
    arrows = [p['arrow'] for p in board['x']]
    ball = next((i for i, p in enumerate(board['o']) if p.get('ball')), 0)
    s = game_state('Five Out', 'High-Low', o, x, arrows, ball=ball, check=False)
    screens = tuple((i, p['screen']['dir'], False, 0) for i, p in enumerate(board['o']) if p.get('screen'))   # (screener, T direction, fresh, beaten-by)
    if screens:
        s = s.with_(screens=screens)
    return s.with_(side=side, turn_n=0, stage='play')


def settle(node):
    while isinstance(node, ChanceNode):
        labels = [lab for _, lab, _ in node.outcomes]
        node = force(node, next((l for l in ('success', 'won', 'kept', 'no foul', 'holds') if l in labels), labels[0]))
    return node


def matches(a, m):
    """Does legal action a draw mark m?"""
    if a.kind != m['kind'] or a.side != m['side'] or a.piece != m['piece']:
        return False
    if m['kind'] in MOVEMENT:
        if a.dest != B.parse_sq(m['to']):
            return False
        if m['side'] == 'X' and m.get('arrow_to') is not None and m['kind'] == 'move' and a.arrow != m['arrow_to']:
            return False
        return True
    if m['kind'] == 'pass':
        return m.get('target') is not None and a.target == next(i for i in range(5)) if False else a.kind == 'pass'
    if m['kind'] == 'screen':
        return a.target == m.get('dir') if m.get('dir') is not None else True
    if m['kind'] == 'shot':
        return (a.shot or '').lower() == (m.get('shot') or '').lower() or not m.get('shot')
    return True


def target_index(s, sq):
    p = B.parse_sq(sq)
    return next((i for i, q in enumerate(s.o) if q == p), None)


def find(s, m):
    acts = legal_actions(s)
    k = m['kind']
    if k == 'pass':
        r = target_index(s, m['target'])
        return [a for a in acts if a.kind == 'pass' and a.side == 'O' and a.target == r]
    if k in MOVEMENT:
        return [a for a in acts if matches(a, m)]
    if k == 'screen':
        return [a for a in acts if a.kind == 'screen' and a.piece == m['piece'] and (m.get('dir') is None or a.target == m['dir'])]
    if k in ('shot', 'dribble', 'steal', 'intercept'):
        return [a for a in acts if a.kind == k and a.piece == m['piece']]
    return None                                      # a contest or a result mark: drawn, not played


def check_lesson(lesson):
    """Play the marks in the order drawn: each from the state the previous ones left (the pass, then the defender's
    move, then his Intercept), or, when that chain cannot continue, from the lesson's starting board."""
    board = dict(lesson['board'])
    drawn = {m['piece'] for m in board['marks'] if m['kind'] == 'screen' and m['side'] == 'O'}
    board['o'] = [dict(p, screen=None) if i in drawn else p for i, p in enumerate(board['o'])]   # the mark sets it
    problems = []
    s = None
    for m in board['marks']:
        side = m['side']
        want = None
        if s is not None and s.side != side and s.stage == 'play':      # the story moves to the other side: end the turn
            end = [a for a in legal_actions(s) if a.kind == 'end_turn']
            if end:
                s = settle(apply(s, end[0]))
        if s is not None and s.side == side and s.stage in ('play', 'reaction'):
            want = find(s, m)
        if not want:
            s = start(board, side)
            want = find(s, m)
        if want is None:
            continue
        if not want:
            where = B.sq(s.x[m['piece']] if side == 'X' else s.o[m['piece']])
            problems.append(f"{lesson['id']}: {side}{m['piece'] + 1} {m['kind']} {m['frm']}->{m.get('to') or m.get('target')} is not legal from {where}")
            s = None
            continue
        s = settle(apply(s, want[0]))
    return problems


def test_the_drawn_reach_is_the_engines_zone():
    """A lesson that hatches a defender's reach draws exactly what the engine's zone() gives for that board."""
    from playmaker_engine.actions import zone
    for lesson in lessons():
        b = lesson['board']
        if not b or not b.get('reach'):
            continue
        s = start(b, 'X')
        want = {(B.sq(q), j + 1) for j in range(5) for q in zone(s, j)}
        drawn = {(sq, n) for sq, n in b['reach']}
        assert drawn == want, f"{lesson['id']}: drawn {sorted(drawn - want)} not in the zone; zone has {sorted(want - drawn)} undrawn"


def test_every_drawn_move_is_legal():
    problems = []
    for lesson in lessons():
        if lesson['board'] and lesson['board']['marks']:
            problems += check_lesson(lesson)
    assert not problems, '\n'.join(problems)
