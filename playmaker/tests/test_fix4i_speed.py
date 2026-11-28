"""Step 31, fix 4i (Shaun, 29 Nov 2026): exact speed only, every answer the same as fix 4h's.

1. The fake's follow-up read by difference. A movement changes it only through the mover's own contests (his column)
   and, once they are read again, the races. So the board's readings are kept, read again only where those changed, and
   put back when the movement is taken back. On P4 (a two-step route) and P2 two off (a switch, then a two-step
   route) the answer reads the same as with the follow-up read afresh after every movement, and the same as fix 4h.
2. Batches handed out from a shared counter, in runs of neighbours, put back in the batch's order: tests/test_fix4f_cores.py
   holds E13's turn on four cores to one core's.
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

FIX4H = {'P4': (30, [[1, 'D6', 7]]), 'P2off': (30, [[0, 'K2', 3], [1, 'D9', 7]])}


@needs_node
def test_the_follow_up_by_difference_reads_as_afresh_and_as_fix_4h():
    names = list(FIX4H)
    diff = T.js([T.req(n, dict(only='value')) for n in names])
    fresh = T.js([T.req(n, dict(only='value')) for n in names], env_extra=dict(PM_FU_FRESH='1'))
    for n, a, b in zip(names, diff, fresh):
        assert (a['res']['play_on'], a['res']['answer']) == (b['res']['play_on'], b['res']['answer']) == (FIX4H[n][0], FIX4H[n][1]), (n, a['res'], b['res'])
