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


def cmd_order(pairs='80'):
    """Do the levels still stand in order on the new default (eval.settle_shots on)? Each stronger level (a) against
    the next (b), each with its own settings and pick noise."""
    L.ENGINES.update({lv: (lambda lv=lv: level(lv)) for lv in ('rookie', 'starter', 'allstar')})
    for a, b in (('allstar', 'starter'), ('starter', 'rookie')):
        B.cmd_h2h(a, b, pairs)


def cmd_timing_h2h(*names):
    """Shot timing from head-to-head files (D-139), for the engine on offence in each: shots by phase, decisions, the
    clock-out rate, and the ball lost per 100 phases kept. Under the app's rules a possession passes through the
    phases in order, so its ending says which phases it entered."""
    rep = {}
    for name in names:
        d = json.load(open(os.path.join(RUN, f'h2h_{name}.json')))
        for side, key in ((d['a'], 'a_end'), (d['b'], 'b_end')):
            e = [r[key] for r in d['rows']]
            ph = lambda x: min(6, max(1, (12 - x[1]) // 2 + 1))
            shot = lambda x: x[0] in ('shot', 'free_throws', 'forced')
            ran = lambda x: x[0] == 'turnover_end' and x[1] <= 2 and x[2] <= 0
            kept = sum(sum(1 for x in e if ph(x) >= k) - sum(1 for x in e if ph(x) == k and shot(x)) for k in range(1, 7))
            lost = sum(1 for x in e if not shot(x) and not ran(x))
            p, lo, hi = L.wilson(lost, kept)
            s = B.ends(e)
            rep[f'{name}: {side} on offence'] = dict(
                possessions=len(e), shots_in_phases_1_and_2=round(s['shot_by_phase']['1'] + s['shot_by_phase']['2'], 3),
                shot_by_phase=s['shot_by_phase'], decisions=s['decisions'], clock_ran_out_in_100=s['clock_ran_out_in_100'],
                clock_interval_in_100=s['clock_ran_out_interval_in_100'], lost_in_100_phases_kept=round(100 * p, 1),
                lost_interval=[round(100 * max(0.0, lo), 1), round(100 * hi, 1)])
    json.dump(rep, open(os.path.join(RUN, 'shot_timing.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


cmd_h2h, cmd_selfplay, cmd_timing, cmd_exam, cmd_speed = B.cmd_h2h, B.cmd_selfplay, B.cmd_timing, B.cmd_exam, B.cmd_speed


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
