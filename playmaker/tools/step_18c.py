"""Step 18c: the defence's missing readings. The measures, on tools/step_18b.py's harness (the possessions are played
by tools/playout.js). App only (Shaun, 11 Nov 2026): nothing here plays under the table's rules.

  python3 tools/step_18c.py level rookie [pairs]         eval.settle_shots at a level, against that level without it
  python3 tools/step_18c.py h2h a b [max_pairs]          head to head, sequential (engines: see ENGINES)
  python3 tools/step_18c.py selfplay name engine [n]     self-play, every position kept
  python3 tools/step_18c.py timing name...               shot timing from kept self-play runs
  python3 tools/step_18c.py exam engines                 the outcome exam against the default
  python3 tools/step_18c.py regret name [n_def] [help]   what the defence's list leaves out, on positions from play
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import step_18b as B                                   # noqa: E402
L = B.L

RUN = os.path.join(ROOT, 'docs', 'runs', 'step18c')
WORK = os.environ.get('STEP18C_WORK', os.path.join(RUN, 'work'))
B.RUN, B.WORK, L.WORK = RUN, WORK, WORK
NOISE = {lv: p['noise'] for lv, p in L.profiles().items()}


def level(lv, **switches):
    """A level as it plays: its own settings and pick noise, 1 pair ahead (D-118)."""
    return L.policy(lv, 2, NOISE[lv], **switches)


L.ENGINES.update({
    # part 0: eval.settle_shots at the lower levels, each against itself without it (explicit, whatever the default is)
    'rookie_settle': lambda: level('rookie', settle_shots=True), 'rookie_plain': lambda: level('rookie', settle_shots=False),
    'starter_settle': lambda: level('starter', settle_shots=True), 'starter_plain': lambda: level('starter', settle_shots=False),
    # the readings, at All-Star, on the default (eval.settle_shots as the config has it)
    'default': lambda: L.policy('allstar', 2, 0.5),
    'default_b': lambda: L.policy('allstar', 2, 0.5),
    'help': lambda: L.policy('allstar', 2, 0.5, help_readings=True),
    'help_budget': lambda: L.policy('allstar', 2, 0.5, help_readings=True, budget=True),
    'budget': lambda: L.policy('allstar', 2, 0.5, budget=True),
})


def cmd_level(lv, pairs='160'):
    B.cmd_h2h(f'{lv}_settle', f'{lv}_plain', pairs)


cmd_h2h, cmd_selfplay, cmd_timing, cmd_exam, cmd_speed = B.cmd_h2h, B.cmd_selfplay, B.cmd_timing, B.cmd_exam, B.cmd_speed


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
