"""Command line: show, play, test, soak, ceilings."""
import argparse
import os
import subprocess
import sys

from .policies import POLICIES, play, format_log
from .scenarios import scenario_state, SCENARIOS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv=None):
    ap = argparse.ArgumentParser(prog='python -m playmaker_engine')
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('show', help='print a scenario board')
    s.add_argument('n', type=int)
    p = sub.add_parser('play', help='play a scenario')
    p.add_argument('n', type=int)
    p.add_argument('--offence', default='greedy', choices=sorted(POLICIES))
    p.add_argument('--defence', default='greedy', choices=sorted(POLICIES))
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--target', type=int, default=None, help="Coach's Call target (1-5)")
    t = sub.add_parser('test', help='run the test suite')
    t.add_argument('pytest_args', nargs='*')
    k = sub.add_parser('soak', help='random-vs-random soak with invariant checks')
    k.add_argument('--games', type=int, default=10000)
    k.add_argument('--workers', type=int, default=os.cpu_count() or 1)
    sub.add_parser('ceilings', help='first-turn ceilings: legacy script vs engine rules')
    sub.add_parser('matchups', help='closeout check for every offence card v defence card v shot type')
    a = ap.parse_args(argv)

    if a.cmd == 'show':
        if a.n not in SCENARIOS:
            print(f'no scenario {a.n}; choose 1-{len(SCENARIOS)}')
            return 2
        st = scenario_state(a.n, target=0 if SCENARIOS[a.n].get('target') else None)
        sc = SCENARIOS[a.n]
        print(f"{st.ctx.title} [{sc['kind']}]  O: {sc['off']}  X: {sc['dfn']}  clock {sc['clock']}")
        print(sc['text'])
        print(st.board())
        return 0
    if a.cmd == 'play':
        target = a.target - 1 if a.target else None
        st = scenario_state(a.n, target=target)
        res = play(st, POLICIES[a.offence](), POLICIES[a.defence](), seed=a.seed)
        print(st.board())
        print(format_log(res))
        print(res['final'].board())
        return 0
    if a.cmd == 'test':
        return subprocess.call([sys.executable, '-m', 'pytest', os.path.join(ROOT, 'tests'), '-q'] + a.pytest_args, cwd=ROOT)
    if a.cmd == 'soak':
        from .soak import run_soak
        rep = run_soak(a.games, a.workers)
        print(rep['summary'])
        return 0 if rep['ok'] else 1
    if a.cmd == 'matchups':
        from .matchups import closeout_report
        rep = closeout_report()
        print(rep['summary'])
        return 0 if rep['foul_breaks'] == 0 and rep['clean_breaks'] == 0 else 1
    if a.cmd == 'ceilings':
        from .analysis import ceilings_report
        print(ceilings_report())
        return 0
    return 1
