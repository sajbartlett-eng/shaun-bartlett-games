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
    v = sub.add_parser('solve', help='solve one scenario card')
    v.add_argument('n', type=int)
    v.add_argument('--budget', type=float, default=None, help='minutes (default: the first budget in solver_config)')
    v.add_argument('--depth', type=int, default=None, help='fixed search depth in turns instead of a time budget')
    v.add_argument('--exact', action='store_true', help='exact solve from the start (only small positions finish)')
    va = sub.add_parser('solve-all', help='solve every card at both budgets, then write SOLVER_REPORT.md')
    va.add_argument('--short', type=float, default=None, help='short budget, minutes')
    va.add_argument('--long', type=float, default=None, help='long budget, minutes')
    va.add_argument('--seeds', type=int, default=None)
    va.add_argument('--workers', type=int, default=3)
    sub.add_parser('rule-health', help='print the rule-health checks from the saved solver runs')
    rv = sub.add_parser('review', help='replay a playtest log and show where the solver disagreed')
    rv.add_argument('log')
    rv.add_argument('--budget', type=float, default=5.0, help='solver seconds per decision')
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
    if a.cmd == 'solve':
        from .scenarios import scenario_state as _ss
        from .solver import exact_solve, NodeCap
        from .solver_config import DEFAULT
        from .solver_report import solve_card, format_card
        if a.exact:
            st = _ss(a.n, target=0 if SCENARIOS[a.n].get('target') else None)
            try:
                v, per = exact_solve(st, cap=DEFAULT.exact_node_cap * 250)
                print(f'exact value {v.ev:.3f} (look {v.look:.2f}, P(30+) {v.p30:.2f})')
            except NodeCap:
                print('exact solve gave up: the position is too large (raise exact_node_cap, or use the guided search)')
            return 0
        budget = (a.budget if a.budget is not None else DEFAULT.budgets_min[0]) * 60
        r = solve_card(a.n, budget_s=None if a.depth else budget, max_depth=a.depth)
        print(format_card(a.n, r))
        return 0
    if a.cmd == 'solve-all':
        from .solver_config import DEFAULT
        from .solver_report import main_jobs, run_jobs, write_report
        short = (a.short if a.short is not None else DEFAULT.budgets_min[0]) * 60
        long = (a.long if a.long is not None else DEFAULT.budgets_min[1]) * 60
        run_jobs(main_jobs(int(short), int(long), a.seeds or DEFAULT.seeds), workers=a.workers)
        print(write_report(int(short), int(long)))
        return 0
    if a.cmd == 'review':
        from .review import review
        review(a.log, a.budget)
        return 0
    if a.cmd == 'rule-health':
        from .solver_report import load_runs, rule_health_text
        print(rule_health_text(load_runs()))
        return 0
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
