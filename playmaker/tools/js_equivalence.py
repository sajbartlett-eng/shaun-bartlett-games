"""Step 3n Part A: prove the JavaScript search core gives the Python engine's answers.

Random legal states across ages, standards, formats and phases (random deals, random placements, then random legal
play with the rolls sampled), and for each: the legal actions, every attacker's and defender's reach map (geometric and
the rules' exact reach), each attacker's threat (value, square, route), the best cover (value, the responses chosen and
the residual threats) and the leaf value, with the geometric and the exact read, and the ordering read.

  python3 tools/js_equivalence.py --n 2000 [--seed 1] [--out docs/runs/3n/3n_equivalence.json]
  python3 tools/js_equivalence.py --n 300 --reaction     # step 7: shot reactions only, with what each Contest, Steal and
                                                          # ending the reaction resolves to (the roll tree, scored)
"""
import argparse
import json
import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from playmaker_engine import board as B                       # noqa: E402
from playmaker_engine import rules_config as RC               # noqa: E402
from playmaker_engine import levels as L, rosters as R        # noqa: E402
from playmaker_engine.actions import legal_actions            # noqa: E402
from playmaker_engine.resolve import apply, ChanceNode, sample  # noqa: E402
from playmaker_engine.state import Context, GameState         # noqa: E402
from playmaker_engine.decide import Read, attacker_reach, defender_map  # noqa: E402
from playmaker_engine.jsbridge import state_json, ctx_json    # noqa: E402

AGES = ('senior', 'youth', 'junior')
STANDARDS = ('pro', 'semi_pro', 'amateur')


def random_state(rng):
    age, std = rng.choice(AGES), rng.choice(STANDARDS)
    digital = rng.random() < 0.5
    d = R.deal(age, std, seed=rng.randrange(36 ** 6))
    tags = d['tags'] or [None, None]
    off, dfn = L.team(d['rosters'][0], age, tags[0]), L.team(d['rosters'][1], age, tags[1])
    rules = RC.with_rules(digital=digital, control=_CONTROL['size'])     # D-151: the control rule's size ('off' by default)
    ctx = Context(off, dfn, rules, team_fouls=rng.randrange(0, 7) if digital else 0,
                  quarter_left=rng.randrange(0, 19) if digital else 0)
    ctx.levels_key = (age, std)                    # step 18a: each age and standard reads its own phase table and scale
    squares = [(x, y) for x in range(B.W) for y in range(1, B.H + 1)]
    # the offence beyond the arc mostly, the defence between them and the rim mostly: positions a game can reach
    pick = rng.sample(squares, 10)
    o, x = tuple(pick[:5]), tuple(pick[5:])
    arrows = tuple(rng.randrange(8) for _ in range(5))
    s = GameState(ctx=ctx, o=o, x=x, arrows=arrows, ball=rng.randrange(5))
    steps = rng.choice((0, 1, 2, 3, 5, 8, 12, 20, 30, 45))
    for _ in range(steps):
        if s.stage == 'over':
            break
        acts = legal_actions(s)
        if not acts:
            break
        a = rng.choice(acts)
        node = apply(s, a)
        if isinstance(node, ChanceNode):
            node, _ = sample(node, rng)
        s = node
    return s, dict(age=age, standard=std, digital=digital, steps=steps)


def reaction_state(rng):
    """A random state inside a shot reaction: a random position played on, then a declared shot, then 0 or 1 reaction
    actions at random."""
    while True:
        s, m = random_state(rng)
        if s.stage != 'play' or s.side != 'O':
            continue
        shots = [a for a in legal_actions(s) if a.kind == 'shot']
        if not shots:
            continue
        r = apply(s, rng.choice(shots))
        if isinstance(r, ChanceNode) or r.stage != 'reaction':
            continue
        if rng.random() < 0.35:
            mv = [a for a in legal_actions(r) if a.kind in ('move', 'qs', 'sprint')]
            if mv:
                r2 = apply(r, rng.choice(mv))
                if not isinstance(r2, ChanceNode) and r2.stage == 'reaction':
                    r = r2
        return r, m


def py_outcomes(s):
    """In a shot reaction: every leaf of the roll tree for each Contest, Steal and ending the reaction (see js_probe.js)."""
    from playmaker_engine.scoring import score
    out = {}

    def leaves(n, p, acc):
        if isinstance(n, ChanceNode):
            for q, _, sub in n.outcomes:
                leaves(sub, p * float(q), acc)
            return acc
        acc.append([round(p * 1e12) / 1e12, 'over', score(n).total] if n.stage == 'over' else
                   [round(p * 1e12) / 1e12, n.stage, n.clock, n.tos])
        return acc
    for a in legal_actions(s):
        if a.kind in ('contest', 'steal', 'end_turn'):
            out[str(a)] = sorted(leaves(apply(s, a), 1.0, []), key=lambda x: json.dumps(x))
    return out


_ADV = {'on': False}
_SETTLE = {'on': False}
_CONTROL = {'size': 'off'}
_HELP = {'on': False}
_OPEN = {'v': None}            # step 18e: search.open_list ('defence', 'both')


def py_probe(s, reach_map=False):
    mp = lambda m: {B.sq(q): n for q, n in m.items()}
    fx = lambda m: {B.sq(q): {str(a): n for a, n in arrs.items()} for q, arrs in m.items()}
    out = dict(legal=[str(a) for a in legal_actions(s)])
    if s.stage == 'over':
        return out
    out['attacker_reach'] = [mp(attacker_reach(s, i)) for i in range(5)]
    from playmaker_engine.decide import ceiling as _ceiling
    out['ceiling'] = _ceiling(s)                    # step 18b (D-145)
    if _HELP['on'] and s.stage == 'play' and not s.pending and s.side == 'O':      # step 18c: the reading with the floor
        from playmaker_engine.search import Searcher as _S
        from playmaker_engine.agent import profile as _p
        out['floored'] = _S('O', _p('allstar'), lambda n: Read(n).leaf(), float('inf')).leaf(s)
    if _SETTLE['on'] and s.stage != 'play':         # step 18b: a declared shot settled by the rules
        from playmaker_engine.search import Searcher, actor as _actor
        from playmaker_engine.agent import profile as _profile
        out['settled'] = Searcher(_actor(s), _profile('allstar'), lambda n: Read(n).leaf(), float('inf')).settled(s)
    if _OPEN['v'] and s.stage == 'play' and s.side == 'X':      # step 18e: the open list itself, turn by turn
        from playmaker_engine.search import Searcher as _S2, turns as _turns
        from playmaker_engine.agent import profile as _p2
        _sr = _S2('X', _p2('allstar'), lambda n: Read(n).leaf(), float('inf'))
        out['open_list'] = [[v, ' ; '.join(str(a) for a in t)] for v, t in _turns(s, 24, None, _sr.quick, None, None, 2, _OPEN['v'], _sr.whole)]
    out['defender_reach'] = [[mp(f), fx(x)] for f, x in (defender_map(s, d) for d in range(5))]
    out['defender_exact'] = [[mp(f), fx(x)] for f, x in (defender_map(s, d, exact=True) for d in range(5))]
    if s.stage in ('play', 'reaction'):
        for exact in (False, True):
            r = Read(s, exact=exact)
            cv = r.cover()
            tag = 'exact' if exact else 'geo'
            out['threat_' + tag] = [[r.threat[i]['value'], B.sq(r.threat[i]['sq']) if r.threat[i]['sq'] else None,
                                     r.threat[i]['route']] for i in range(5)]
            out['cover_' + tag] = [cv['value'], sorted([[j, B.sq(resp[0]), resp[1], resp[2]] for j, resp in cv['choice'].items()]),
                                   [cv['residual'][i] for i in range(5)]]
            out['leaf_' + tag] = r.leaf()
            if not s.pending and s.stage == 'play':
                out['features_' + tag] = r.features()          # step 17: the named readings
            if _ADV['on']:                          # step 16: the advantage list, each worth, and the potential
                out['adv_' + tag] = [[[a['kind'], a['i'], a['j'], B.sq(a['sq']) if a['sq'] else None, a['stage'], a['value'],
                                       a['chance'], a['worth'], a['gap']] for a in r.advantages()], r.phi()]
            if r._budget_on() and not s.pending:    # step 13 B: the allocation itself, and every look's two parts
                bd = r.budget()
                out['budget_' + tag] = [bd['value'], [bd['left'].get(i) for i in range(5)],
                                        [[j, i, k, x] for j, i, k, x in bd['shares']]]
                out['split_' + tag] = [[list(r.look_split(lk)) for lk in r.looks[i]] for i in range(5)]
        out['quick'] = Read(s, k=0, looks_per=3).leaf()
    if reach_map:                                  # step 12: the reach map, square by square (the tool asks for it)
        from playmaker_engine.reach import reach_map as _rm
        out['reach_map'] = {f'{side}{i}': {B.sq(q): list(v) for q, v in row.items()} for (side, i), row in _rm(s).items()}
    return out


def close(a, b, tol=1e-9):
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= tol * max(1.0, abs(a))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k], tol) for k in a)
    return a == b


def run_js(lines):
    p = subprocess.run(['node', os.path.join(HERE, 'js_probe.js')], input='\n'.join(lines) + '\n', capture_output=True,
                       text=True, check=True)
    return [json.loads(ln) for ln in p.stdout.splitlines() if ln.strip()]


def compare_searches(args, rng):
    """Steps 12 and 13: whole searches (the All-Star, 2 moves ahead, no time limit) in both engines: every root value
    and its turn (the choices), the choice at each depth, the depth used, the extensions, cap hits and kept choices."""
    from playmaker_engine.agent import Agent, profile
    from playmaker_engine.search import Searcher, actor
    from playmaker_engine import jsbridge
    sts = []
    while len(sts) < args.search:
        s, _ = random_state(rng)
        if s.stage == 'play':
            sts.append(s)
    lines = [json.dumps(dict(stable=args.stable, switches=args.switch_map, speed=args.speed, reach=args.reach,
                             coverage_budget=args.coverage_budget, advantages=args.advantages, goals=args.goals,
                             learned=args.learned, calibrated=args.calibrated, settle=args.settle, help=args.help_readings, open=args.open_list, whole=args.whole_turns, kept=args.kept_actions, split=args.split_ties, in_hand=args.rank_in_hand, no_floor=args.no_floor, leaf_mode=args.leaf_mode,
                             search=dict(state=state_json(s), ctx=ctx_json(s.ctx), profile=profile('allstar'),
                                         budget=None, max_depth=2, stale=None))) for s in sts]
    js = [json.loads(x) if isinstance(x, str) else x for x in run_js(lines)]
    bad, same = [], 0
    for k, (s, j) in enumerate(zip(sts, js)):
        ag = Agent(actor(s), 'allstar', seed=1)
        sr = Searcher(actor(s), ag.p, ag._evaluate(s), float('inf'))
        res, reached = sr.root(s, 2, 2)
        py = dict(values=[v for v, _ in res], turns=[[str(a) for a in t] for _, t in res], reached=reached,
                  extensions=getattr(sr, 'extensions', 0), cap_hits=getattr(sr, 'cap_hits', 0), kept=getattr(sr, 'kept', 0),
                  choices=[[d, [str(a) for a in t]] for d, t, _ in sr.trace], choice_values=[v for _, _, v in sr.trace])
        if 'error' in j:
            bad.append(dict(n=k, field='search', js=j['error'][:400]))
            continue
        jj = dict(values=[v for v, _ in j['results']], reached=j['reached'], extensions=j.get('extensions', 0),
                  cap_hits=j.get('cap_hits', 0), kept=j.get('kept', 0),
                  choices=[[d, [str(jsbridge.action_from(a)) for a in t]] for d, t, _ in j.get('trace', [])],
                  choice_values=[v for _, _, v in j.get('trace', [])])
        # the choices: the turn chosen at each depth; and the same turns, each with the same value
        jt = {' ; '.join(str(jsbridge.action_from(a)) for a in t): v for v, t in j['results']}
        pt = {' ; '.join(t): v for v, t in zip(py['values'], py['turns'])}
        ok = close(py['values'], jj['values']) and close(py['choice_values'], jj['choice_values']) \
            and all(py[f] == jj[f] for f in ('reached', 'extensions', 'cap_hits', 'kept', 'choices')) and close(pt, jt)
        if args.split_ties:                         # step 18f: the turns in the same order too (ties are put in order)
            jj['turns'] = [[str(jsbridge.action_from(a)) for a in tn] for _, tn in j['results']]
            ok = ok and py['turns'] == jj['turns']
        same += ok
        if not ok:
            bad.append(dict(n=k, field='search', state=s.encode(), py={f: py[f] for f in jj}, js=jj))
    return dict(bad=bad, summary=dict(compared=len(sts), equal=same))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=2000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default=None)
    ap.add_argument('--show', type=int, default=5)
    ap.add_argument('--reaction', action='store_true', help='shot reactions only, with their outcomes compared')
    ap.add_argument('--stable', action='store_true', help='step 12: search.stable on, in both engines')
    ap.add_argument('--switches', default='', help='step 13: the stable search\'s switches to turn on, comma-separated '
                    '(quiet_points, like_with_like, tempo, play_on, clear_reason; "cheap" = the first three)')
    ap.add_argument('--without', default='', help='step 13: the JavaScript speed-ups to turn off, comma-separated '
                    '(reach_cache, forcing, quiet_read, tt_order; "all"), to prove each changes nothing')
    ap.add_argument('--reach', action='store_true', help='eval.reach on, in both engines (the default since D-121)')
    ap.add_argument('--no-reach', action='store_true', help='eval.reach off, in both engines')
    ap.add_argument('--calibrated', action='store_true', help='step 17D: eval.calibrated on, in both engines (the default since D-138)')
    ap.add_argument('--no-calibrated', action='store_true', help='eval.calibrated off, in both engines')
    ap.add_argument('--learned', action='store_true', help='step 17: eval.learned on, in both engines')
    ap.add_argument('--control', default='app', help="rules.control in every position: app (the default: size 2 in the app's format), 0, 1, 2 or 3")
    ap.add_argument('--settle', action='store_true', help='step 18b: eval.settle_shots on, in both engines (the default since D-148)')
    ap.add_argument('--no-settle', action='store_true', help='eval.settle_shots off, in both engines')
    ap.add_argument('--help-readings', action='store_true', help='step 18c: eval.help_readings on, in both engines')
    ap.add_argument('--open-list', default=None, choices=('defence', 'both', 'off'), help="step 18e: search.open_list, in both engines (unset: each level's own; off: no level)")
    ap.add_argument('--whole-turns', action='store_true', help='step 18f: search.whole_turns on, in both engines')
    ap.add_argument('--kept-actions', action='store_true', help='step 18f: eval.kept_actions on, in both engines')
    ap.add_argument('--split-ties', action='store_true', help='step 18f: search.split_ties on, in both engines')
    ap.add_argument('--rank-in-hand', action='store_true', help='step 18f: search.rank_in_hand on, in both engines')
    ap.add_argument('--no-floor', action='store_true', help='step 18h: eval.no_floor on, in both engines')
    ap.add_argument('--advantages', action='store_true', help='step 16: eval.advantages on, in both engines')
    ap.add_argument('--goals', action='store_true', help='step 16: search.goals on (with eval.advantages), in both engines')
    ap.add_argument('--coverage-budget', action='store_true', help='step 13 B: eval.coverage_budget on, in both engines')
    ap.add_argument('--search', type=int, default=0, help='step 12: also compare this many searches (2 moves ahead)')
    ap.add_argument('--leaf-mode', default=None, choices=('floor', 'relative', 'looks'),
                    help="the leaf's mode, in both engines (default: eval.leaf_mode in ai_profiles.json)")
    args = ap.parse_args()
    from playmaker_engine.decide import CONFIG as _CFG
    args.leaf_mode = args.leaf_mode or _CFG['eval'].get('leaf_mode', 'floor')
    _CFG['eval']['leaf_mode'] = args.leaf_mode
    _CFG.setdefault('search', {})['stable'] = args.stable
    args.reach = not args.no_reach and (args.reach or bool(_CFG['eval'].get('reach')))
    _CFG['eval']['coverage_budget'] = args.coverage_budget
    args.advantages = args.advantages or args.goals
    _CFG['eval']['advantages'] = args.advantages
    _CFG['search']['goals'] = args.goals
    _ADV['on'] = args.advantages
    _CFG['eval']['learned'] = args.learned
    _CONTROL['size'] = args.control
    args.settle = not args.no_settle and (args.settle or bool(_CFG['eval'].get('settle_shots')))
    _CFG['eval']['settle_shots'] = args.settle
    _SETTLE['on'] = args.settle
    _CFG['eval']['help_readings'] = args.help_readings
    args.open_list = False if args.open_list == 'off' else args.open_list
    _OPEN['v'] = args.open_list
    _CFG.setdefault('search', {})['whole_turns'] = args.whole_turns or bool(_CFG.get('search', {}).get('whole_turns'))
    args.whole_turns = _CFG['search']['whole_turns']
    _CFG['eval']['kept_actions'] = args.kept_actions or bool(_CFG['eval'].get('kept_actions'))
    args.kept_actions = _CFG['eval']['kept_actions']
    _CFG['search']['split_ties'] = args.split_ties or bool(_CFG['search'].get('split_ties'))
    args.split_ties = _CFG['search']['split_ties']
    _CFG['search']['rank_in_hand'] = args.rank_in_hand or bool(_CFG['search'].get('rank_in_hand'))
    args.rank_in_hand = _CFG['search']['rank_in_hand']
    _CFG['eval']['no_floor'] = args.no_floor or bool(_CFG['eval'].get('no_floor'))
    args.no_floor = _CFG['eval']['no_floor']
    _CFG.setdefault('search', {})['open_list'] = args.open_list
    _HELP['on'] = args.help_readings
    args.calibrated = not args.no_calibrated and (args.calibrated or bool(_CFG['eval'].get('calibrated'))) and not args.learned
    _CFG['eval']['calibrated'] = args.calibrated
    from playmaker_engine.search import PARTS
    names = [x for x in args.switches.replace('cheap', 'quiet_points,like_with_like,tempo').split(',') if x]
    if not args.switches:                          # none named: the config's own (like_with_like, D-121)
        names = [k for k in PARTS if _CFG['search'].get(k) is True]
    names = [x for x in names if x != 'none']
    assert all(x in PARTS for x in names), names
    args.switch_map = {k: k in names for k in PARTS}
    _CFG['search'].update(args.switch_map)
    speedups = ('reach_cache', 'forcing', 'quiet_read', 'tt_order', 'two_direct', 'two_bound', 'path_block')
    off = speedups if args.without == 'all' else [x for x in args.without.split(',') if x]
    assert all(x in speedups for x in off), off
    args.speed = {k: k not in off for k in speedups}
    from playmaker_engine import search as _S
    _S.SPEED['tt_order'] = 'tt_order' not in off      # the one speed-up the Python search shares
    _CFG['eval']['reach'] = args.reach
    rng = random.Random(args.seed)
    states, meta, lines = [], [], []
    t0 = time.time()
    while len(states) < args.n:
        s, m = reaction_state(rng) if args.reaction else random_state(rng)
        states.append(s)
        meta.append(m)
        lines.append(json.dumps(dict(state=state_json(s), ctx=ctx_json(s.ctx), outcomes=args.reaction,
                                     leaf_mode=args.leaf_mode, stable=args.stable, switches=args.switch_map, speed=args.speed,
                                     reach=args.reach, coverage_budget=args.coverage_budget, advantages=args.advantages,
                                     goals=args.goals, learned=args.learned, calibrated=args.calibrated, settle=args.settle, help=args.help_readings,
                                     open=args.open_list, whole=args.whole_turns, kept=args.kept_actions, split=args.split_ties, in_hand=args.rank_in_hand, no_floor=args.no_floor, reach_map=True)))
    py = [py_probe(s, reach_map=True) for s in states]
    if args.reaction:
        for s, a in zip(states, py):
            a['react_outcomes'] = py_outcomes(s)
    t_py = time.time() - t0
    t1 = time.time()
    js = run_js(lines)
    t_js = time.time() - t1
    if args.open_list:                              # the JS list's actions in the Python engine's words
        from playmaker_engine import jsbridge as _jb
        for b in js:
            if 'open_list' in b:
                b['open_list'] = [[v, ' ; '.join(str(_jb.action_from(a)) for a in t)] for v, t in b['open_list']]
    fields = ('legal', 'attacker_reach', 'defender_reach', 'defender_exact', 'threat_geo', 'cover_geo', 'leaf_geo',
              'threat_exact', 'cover_exact', 'leaf_exact', 'quick', 'reach_map', 'budget_geo', 'budget_exact', 'split_geo',
              'split_exact', 'adv_geo', 'adv_exact', 'features_geo', 'features_exact', 'ceiling', 'settled', 'floored', 'open_list') + (('react_outcomes',) if args.reaction else ())
    tally = {f: [0, 0] for f in fields}
    bad = []
    stages, phases = {}, {}
    for k, (s, a, b) in enumerate(zip(states, py, js)):
        stages[s.stage] = stages.get(s.stage, 0) + 1
        phases[s.phase] = phases.get(s.phase, 0) + 1
        if 'error' in b:
            bad.append(dict(n=k, field='error', js=b['error'][:400], state=s.encode()))
            continue
        for f in fields:
            if f not in a:
                continue
            tally[f][0] += 1
            if close(a[f], b.get(f)):
                tally[f][1] += 1
            else:
                bad.append(dict(n=k, field=f, state=s.encode(), py=a[f], js=b.get(f)))
    srch = compare_searches(args, rng) if args.search else None
    if srch:
        bad += srch['bad']
    rep = dict(leaf_mode=args.leaf_mode, stable=args.stable, switches=names, reach=args.reach, speedups_off=list(off),
               coverage_budget=args.coverage_budget, advantages=args.advantages, goals=args.goals, learned=args.learned, calibrated=args.calibrated, control=args.control, settle=args.settle, help=args.help_readings,
               searches=srch and srch['summary'],
               states=len(states), seconds_python=round(t_py, 1), seconds_js=round(t_js, 1),
               by_stage=stages, by_phase=phases,
               by_age={a: sum(1 for m in meta if m['age'] == a) for a in AGES},
               by_standard={a: sum(1 for m in meta if m['standard'] == a) for a in STANDARDS},
               digital=sum(1 for m in meta if m['digital']),
               reaction_kinds={k: sum(1 for s in states if any(a.kind == k for a in legal_actions(s)))
                               for k in ('contest', 'steal', 'end_turn')} if args.reaction else None,
               reaction_after_one_action=sum(1 for s in states if s.stage == 'reaction' and s.turn_n == 1)
               if args.reaction else None,
               checks={f: dict(compared=t[0], equal=t[1]) for f, t in tally.items()},
               mismatches=len(bad))
    print(json.dumps(rep, indent=1))
    for b in bad[:args.show]:
        print(json.dumps(b)[:3000])
    if args.out:
        rep['first_mismatches'] = bad[:20]
        json.dump(rep, open(args.out, 'w'), indent=1)
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
