"""Step 31, fix 4e (Shaun, 27 Nov 2026: "each side answers what it can see"; D-283, never narrow the reading).

The defence's answer that answers every look and race (engine.js, a switch: _pvAnswers) is held to the full reading (fix 4d's
_pvFull), which reads every legal movement in full with the races read again: on R2 the two give the same number,
the same movements and the same races. And each race it reads again by difference from the board as it stands
equals the same race read afresh, for every movement it reads.
"""
import os
import shutil
import sys

import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import step_31 as T                           # noqa: E402

needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


def _races(v):
    return [(x['advantage'], x['beaten'], x['from'], x['worth']) for x in v.get('drive_race') or []]


@needs_node
def test_the_new_answer_is_the_full_reading_on_R2():
    full = T.js([T.req('R2', dict(only='value'))], timeout=900, answer='full')[0]['res']
    got = T.js([T.req('R2', dict(only='value'))], timeout=900, answer='answers')[0]['res']
    assert got['value'] == full['value'] and got['answer'] == full['answer'], (got['value'], got['answer'], full['value'], full['answer'])
    assert _races(got) == _races(full)


@needs_node
def test_each_race_read_by_difference_is_the_race_read_afresh():
    r = T.js([T.req('R2', dict(only='value'))], timeout=900, answer='check')[0]
    rc = r['race_check']
    assert rc['n'] > 0 and rc['bad'] == 0, rc
