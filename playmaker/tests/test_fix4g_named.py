"""Step 31, fix 4g (Shaun, 28 Nov 2026): each race names its own answers.

1. In play, each race the number turns on names the movements that would stop it (a square in front of its line, a
   drop to where it finishes, a helper arriving there, a step into its passing lane); those are read in full with the
   map's own. Both engines take the same answer, at the same number: R4 (two movements, both named), P2 (a named
   drop under the rim, then a movement tried and taken back) and P3.
2. A movement tried and taken back leaves the board exactly as it was: the fake's follow-up on a board kept from
   earlier reads the races as they stood on it, never the races of the movement tried since. On P2 the number after
   the take-back equals the number before it.
(The exact answer, _pvAnswers, is the test that measures what the new answer misses: tools/step_31_fix4g_proof.py.)
"""
import os
import shutil
import sys

import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import exam_boards as X                       # noqa: E402
import step_31 as T                           # noqa: E402
from playmaker_engine import board as B       # noqa: E402
from playmaker_engine import value as V       # noqa: E402

needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


@needs_node
def test_both_engines_take_the_same_race_named_answer():
    names = ['R4', 'P2', 'P3']
    js = T.js([T.req(n, dict(only='value')) for n in names])
    for n, r in zip(names, js):
        pp = V.poss_parts(X.get(n))
        assert r['res']['play_on'] == round(pp['V'], 4), (n, r['res']['play_on'], pp['V'])   # (engine.js reports 4 decimals)
        assert r['res']['answer'] == [[d, B.sq(q), a] for d, q, a in pp['moves']], (n, r['res']['answer'], pp['moves'])
    assert js[0]['res']['answer'] and js[1]['res']['answer'], 'R4 and P2 take a race-named answer'


@needs_node
def test_a_movement_taken_back_leaves_the_number_as_it_was():
    r = T.js([T.req('P2', dict(only='value'))], debug=True)[0]['res']
    backs = [d for d in r['debug'] if d['path'] == 'back']
    assert backs, 'P2 tries a movement and takes it back'
    for d in backs:
        assert abs(d['U'] - d['snapU']) <= 1e-9, d
