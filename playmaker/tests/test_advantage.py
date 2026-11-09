import pytest
"""Step 3g: an offence that creates advantages. advantages() labels the board; the offence's candidates are
advantage plays (shoot, dribble attack, screen, speed burst, post seal, cut, pass to move or finish an
advantage) scored by create, reply, exploit. Positions come from computer playouts and the playtest logs
(tests/data/adv_positions.json: the start plus every state field)."""
import json
import os

from playmaker_engine import board as B
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply
from playmaker_engine.solver import Play, apply_play

HERE = os.path.dirname(__file__)
DATA = json.load(open(os.path.join(HERE, 'data', 'adv_positions.json')))


def _tup(v):
    return tuple(_tup(x) for x in v) if isinstance(v, list) else v


def before(name, s):
    """The board before the defence's move, in the same game (same context) as the position s."""
    return s.with_(**{k: _tup(v) for k, v in DATA[name]['prev'].items()})


# ---- the six states, and none on a neutral set position -------------------------------------------

# ---- the plays ---------------------------------------------------------------------------------------

def test_the_review_names_the_advantage_plays():
    from playmaker_engine.review import computer_facts
    recs = [dict(type='setup', computer=dict(O=dict(level='allstar', name='All-Star', habits=[], concepts_off=[]))),
            dict(type='computer', side='O', possession=1, event='play', play='screen', attacker=0,
                 text='Screen for a mismatch: O2 screens X1 off O1', advantage='O1 has a mismatch on X4 (three)'),
            dict(type='computer', side='O', possession=1, event='advantage_moved', attacker=4, helper=4, shot='three',
                 text='Help came from X5; the advantage moved to O5'),
            dict(type='computer', side='O', possession=1, event='finish', attacker=4, shot='three', text='Finished: O5 three')]
    text = ' '.join(computer_facts(recs))
    assert 'Help came from X5; the advantage moved to O5.' in text and 'Finished: O5 three.' in text
    assert 'Screen for a mismatch: O2 screens X1 off O1. O1 has a mismatch on X4 (three).' in text
