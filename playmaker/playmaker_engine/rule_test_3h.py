"""Step 3h: a short comparison of four rule variants (not adopted).

  A  single arrow, current contests (the rules as they stand)
  B  wedge, wedge_mirror      C  wedge, rim_distance      D  single arrow, rim_distance

For each variant: the solver on the 16 scenario cards and the golden position at a short budget, 2
seeds (value, look, verdict, the best first play); the context test (each card with the two other
matchups round 2 used); and All-Star v All-Star play-outs from the same starts, 2 seeds, counting
contests by category, foul rolls, and-ones, interceptions, Dribbles and how shot reactions were spent.
Resumable: results go to solver_results/rule3h.json as they finish.
"""
import json
import os
import random
import time
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'solver_results')
STORE = os.path.join(RESULTS, 'rule3h.json')
VARIANTS = {'A': ('single', 'current'), 'B': ('wedge', 'wedge_mirror'), 'C': ('wedge', 'rim_distance'),
            'D': ('single', 'rim_distance')}
NAMES = {'A': 'A: single arrow, current', 'B': 'B: wedge, wedge_mirror', 'C': 'C: wedge, rim_distance',
         'D': 'D: single arrow, rim_distance'}
CARDS = list(range(1, 17))
STARTS = CARDS + ['golden']


def rules_of(v):
    from . import rules_config as RC
    am, cg = VARIANTS[v]
    return RC.with_rules(arrow_mode=am, contest_geometry=cg)


def start(n, rules):
    from .scenarios import scenario_state, game_state
    if n == 'golden':
        return game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'],
                          ['N', 'NE', 'NW', 'N', 'N'], ball=0, rules=rules)
    return scenario_state(n, rules=rules)


def _solve(args):
    v, kind, n, seed, budget, extra = args
    from .solver_report import solve_card, solve_state, _best_target
    from .solver_fixes import teams
    R = rules_of(v)
    t0 = time.time()
    if n == 'golden':
        r = solve_state(start('golden', R), budget_s=budget, seed=seed)
    elif kind == 'context':
        r = solve_card(n, budget, seed, rules=R, setup=teams(*extra), target=_best_target(n))
    else:
        r = solve_card(n, budget, seed, rules=R)
    keep = {k: r.get(k) for k in ('value', 'look', 'p30', 'verdict', 'best_label', 'n_plans', 'depth', 'teams')}
    keep['first'] = r['line'][0]['text'] if r.get('line') else ''
    keep['wall'] = round(time.time() - t0, 1)
    return ['solve', v, kind, n, seed, extra], keep


def _play(args):
    """One All-Star v All-Star possession, with the counts the comparison needs."""
    v, n, seed, budget = args
    from . import board as B
    from .computer import Computer, BUDGET
    from .resolve import apply, ChanceNode, sample
    from .scoring import score, contest_options
    BUDGET['active'] = budget
    R = rules_of(v)
    s = start(n, R)
    pols = {'O': Computer('O', 'allstar', seed=seed), 'X': Computer('X', 'allstar', seed=seed)}
    rng = random.Random(seed * 1009 + 7)
    st = Counter()
    contest = None
    for _ in range(300):
        if s.stage == 'over':
            break
        side = 'O' if (s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play')) else 'X'
        a = pols[side].choose(s)
        if s.stage == 'contest' and contest is None:
            opts = [o for o in contest_options(s, s.ball, s.shot, s.forced) if o.defender >= 0]
            if a.piece >= 0:
                o = next((x for x in opts if x.defender == a.piece), None)
                contest = o.category if o else 'none'
            else:
                contest = 'declined' if opts else 'none'
        if s.stage == 'reaction' and a.side == 'X':
            if a.kind == 'move' and a.dest == s.x[a.piece]:
                st['react_turn'] += 1
            elif a.kind in ('move', 'qs', 'sprint'):
                st['react_move'] += 1
            elif a.kind == 'steal':
                st['react_steal'] += 1
        if a.kind == 'dribble':
            st['dribbles'] += 1
        if a.kind == 'intercept':
            st['icpt_tried'] += 1
        node = apply(s, a)
        while isinstance(node, ChanceNode):
            nxt, lab = sample(node, rng)
            what = node.what or ''
            if what.startswith('Pass ') and lab == 'failure':
                st['icpt_won'] += 1
            if what.startswith('Contest foul'):
                st['foul_rolls'] += 1
                st['fouls'] += lab == 'foul'
            node = nxt
        s = node
    sc = score(s) if s.stage == 'over' else None
    if sc is not None and s.result is not None and getattr(s.result, 'and_one', False):
        st['and_ones'] += 1
    return ['play', v, n, seed], dict(counts=dict(st), contest=contest, total=float(sc.total) if sc else None,
                                      band=sc.band if sc else None)


def jobs(budget=15.0, play_budget=0.5, seeds=(0, 1)):
    from .solver_report import alt_matchups
    out = []
    for v in VARIANTS:
        for n in STARTS:
            for sd in seeds:
                out.append(('solve', (v, 'solve', n, sd, budget, None)))
        for n in CARDS:
            for m in alt_matchups(n):
                out.append(('solve', (v, 'context', n, 0, budget, list(m))))
        for n in STARTS:
            for sd in seeds:
                out.append(('play', (v, n, sd + 1, play_budget)))
    return out


def _key(k):
    return json.dumps(k)


def load():
    return json.load(open(STORE)) if os.path.exists(STORE) else {}


def run(workers=3, **kw):
    done = load()
    todo = []
    for kind, args in jobs(**kw):
        k = ['solve', args[0], args[1], args[2], args[3], args[5]] if kind == 'solve' else ['play', args[0], args[1], args[2]]
        if _key(k) not in done:
            todo.append((kind, args))
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex:
        futs = [ex.submit(_solve if kind == 'solve' else _play, args) for kind, args in todo]
        for i, f in enumerate(futs):
            k, r = f.result()
            done[_key(k)] = r
            tmp = STORE + '.tmp'
            json.dump(done, open(tmp, 'w'))
            os.replace(tmp, STORE)
            print(f'{i + 1}/{len(futs)} {k} {round(time.time() - t0)} s', flush=True)
    return done


# ---- the comparison ---------------------------------------------------------------------------------

def summary(R=None):
    R = R or load()
    out = {}
    rows = [(json.loads(k), v) for k, v in R.items()]
    for v in VARIANTS:
        solves = {(k[3], k[4]): r for k, r in rows if k[0] == 'solve' and k[1] == v and k[2] == 'solve'}
        ctx = [(k[3], r) for k, r in rows if k[0] == 'solve' and k[1] == v and k[2] == 'context']
        plays = [r for k, r in rows if k[0] == 'play' and k[1] == v]
        n_play = len(plays)
        cats = Counter(p['contest'] or 'no shot' for p in plays)
        counts = Counter()
        for p in plays:
            counts.update(p['counts'])
        card_vals = [solves[(n, 0)]['value'] for n in CARDS if (n, 0) in solves]
        bands = Counter()
        from .scoring import band
        for n in CARDS:
            if (n, 0) in solves:
                bands[band(solves[(n, 0)]['look'] or 0)] += 1
        changes = pairs = 0
        for n, r in ctx:
            own = solves.get((n, 0))
            if own:
                pairs += 1
                changes += r['best_label'] != own['best_label']
        reacts = counts['react_turn'] + counts['react_move'] + counts['react_steal']
        shots = sum(cats[c] for c in ('front', 'side', 'behind', 'none', 'declined'))
        out[v] = dict(
            n_play=n_play, contests=dict(cats), shots=shots,
            share={c: (cats[c] / shots if shots else 0.0) for c in ('front', 'side', 'behind', 'none', 'declined')},
            per_poss={k: counts[k] / n_play if n_play else 0.0 for k in
                      ('foul_rolls', 'fouls', 'and_ones', 'icpt_tried', 'icpt_won', 'dribbles')},
            play_value=(sum(p['total'] for p in plays if p['total'] is not None) / max(1, sum(p['total'] is not None for p in plays))),
            play_bands=dict(Counter(p['band'] for p in plays)),
            card_value=sum(card_vals) / len(card_vals) if card_vals else None, card_bands=dict(bands),
            golden=[solves.get(('golden', sd), {}).get('value') for sd in (0, 1)],
            context_rate=changes / pairs if pairs else None, context_pairs=pairs,
            react_turn=counts['react_turn'] / reacts if reacts else 0.0,
            react_move=counts['react_move'] / reacts if reacts else 0.0, reacts=reacts,
            verdicts={n: solves[(n, 0)]['verdict'] for n in CARDS if (n, 0) in solves},
            values={n: solves[(n, 0)]['value'] for n in CARDS if (n, 0) in solves},
            seeds_agree=sum(1 for n in CARDS if (n, 0) in solves and (n, 1) in solves and
                            solves[(n, 0)]['verdict'] == solves[(n, 1)]['verdict']))
    for v in VARIANTS:
        if v != 'A' and 'A' in out:
            out[v]['changed'] = [n for n in CARDS if out[v]['verdicts'].get(n) != out['A']['verdicts'].get(n)]
    return out


# ---- the PDF ------------------------------------------------------------------------------------------

def _table(head, rows):
    h = ''.join(f'<th>{x}</th>' for x in head)
    b = ''.join('<tr>' + ''.join(f'<td>{x}</td>' for x in r) + '</tr>' for r in rows)
    return f'<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>'


def html(S, findings, recommendation, notes=''):
    V = list(VARIANTS)
    pct = lambda x: f'{100 * x:.0f}%'
    f2 = lambda x: '' if x is None else f'{x:.2f}'
    f1 = lambda x: '' if x is None else f'{x:.1f}'
    parts = []
    parts.append('<h2>1. Who contests, and from where</h2><p>Shots in the play-outs (All-Star v All-Star, 2 seeds '
                 'from each of the 16 cards and the golden position). Under A the category is descriptive (by rim '
                 'distance, the measure the current −3 uses); there a contest is "clean" or a foul roll by facing.</p>')
    parts.append(_table(['Variant', 'Shots', 'Front', 'Side', 'Behind', 'No eligible contester', 'Contest declined'],
                        [[NAMES[v], S[v]['shots']] + [pct(S[v]['share'][c]) for c in ('front', 'side', 'behind', 'none', 'declined')] for v in V]))
    parts.append('<h2>2. Foul rolls and and-ones</h2>')
    parts.append(_table(['Variant', 'Contest foul rolls / possession', 'Fouls given / possession', 'And-ones / possession'],
                        [[NAMES[v], f2(S[v]['per_poss']['foul_rolls']), f2(S[v]['per_poss']['fouls']), f2(S[v]['per_poss']['and_ones'])] for v in V]))
    parts.append('<h2>3. Passing lanes and drives</h2><p>A Dribble is how a ball carrier crosses an adjacent '
                 'defender\'s arrow line, so Dribbles per possession is the measure of drives the lines force.</p>')
    parts.append(_table(['Variant', 'Interceptions tried / possession', 'Interceptions won / possession', 'Dribbles / possession'],
                        [[NAMES[v], f2(S[v]['per_poss']['icpt_tried']), f2(S[v]['per_poss']['icpt_won']), f2(S[v]['per_poss']['dribbles'])] for v in V]))
    parts.append('<h2>4. Possession value and bands</h2><p>Solver values: the 16 cards at a short budget (one '
                 'complete search level, seed 0) and the golden position (seeds 0 and 1). Play-out values are '
                 'the points scored.</p>')
    bands = ['Excellent', 'Great', 'Good', 'Okay', 'Poor']
    parts.append(_table(['Variant', 'Cards: mean value', 'Golden (2 seeds)', 'Play-outs: mean points'] + [f'Cards {b}' for b in bands],
                        [[NAMES[v], f1(S[v]['card_value']), ' / '.join(f1(x) for x in S[v]['golden']), f1(S[v]['play_value'])]
                         + [S[v]['card_bands'].get(b, 0) for b in bands] for v in V]))
    parts.append('<h2>5. Plan change rate (the context test)</h2><p>Each card re-solved with the two other matchups '
                 'round 2 used; the rate is how often the best first play changes. Lower means the card\'s plan '
                 'depends less on who is playing.</p>')
    parts.append(_table(['Variant', 'Plan change rate', 'Pairs'], [[NAMES[v], pct(S[v]['context_rate'] or 0), S[v]['context_pairs']] for v in V]))
    parts.append('<h2>6. How shot reactions were spent</h2>')
    parts.append(_table(['Variant', 'Reaction actions', 'Turning on the spot', 'Moving', 'Other (steal)'],
                        [[NAMES[v], S[v]['reacts'], pct(S[v]['react_turn']), pct(S[v]['react_move']),
                          pct(max(0.0, 1 - S[v]['react_turn'] - S[v]['react_move'])) if S[v]['reacts'] else '0%'] for v in V]))
    parts.append('<h2>7. Card verdicts that change from A</h2>')
    rows = []
    for n in CARDS:
        a = S['A']['verdicts'].get(n, '')
        rows.append([n, a] + [S[v]['verdicts'].get(n, '') + (' *' if S[v]['verdicts'].get(n) != a else '') for v in V[1:]])
    parts.append(_table(['Card', 'A'] + [NAMES[v] for v in V[1:]], rows))
    parts.append('<p>* differs from A. At this budget the two seeds agree on '
                 + ', '.join(f'{S[v]["seeds_agree"]}/16 ({v})' for v in V) + ' verdicts.</p>')
    css = ('body{font-family:Helvetica,Arial,sans-serif;font-size:11px;margin:28px;color:#1d1b18}'
           'h1{font-size:20px;margin:0 0 4px}h2{font-size:14px;margin:18px 0 6px}'
           'table{border-collapse:collapse;width:100%;margin:4px 0 8px}th,td{border:1px solid #bbb;padding:3px 6px;text-align:left}'
           'th{background:#eee}.box{border:2px solid #1d1b18;padding:8px 10px;margin:10px 0}')
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>Rule test 3h</title><style>{css}</style></head><body>'
            f'<h1>Step 3h: wedge and positional contests, a short comparison</h1>'
            f'<p>Four variants, built as engine settings and not adopted. Short budget: one complete solver level '
            f'per position (10 s budget), 2 seeds; play-outs at the computer\'s 0.5 s budget.</p>'
            f'<div class="box"><b>Findings.</b> {findings}</div><div class="box"><b>Recommendation.</b> {recommendation}</div>'
            + ''.join(parts) + (f'<h2>Notes</h2><p>{notes}</p>' if notes else '') + '</body></html>')


def write_pdf(findings, recommendation, notes='', path=None):
    S = summary()
    docs = os.path.join(os.path.dirname(RESULTS), 'docs')
    path = path or os.path.join(docs, 'Rule_Test_3h.pdf')
    h = html(S, findings, recommendation, notes)
    hp = path.replace('.pdf', '.html')
    open(hp, 'w').write(h)
    import subprocess
    js = os.path.join(RESULTS, '_pdf.js')
    open(js, 'w').write("const { chromium } = require('playwright'); (async () => { const [s, o] = process.argv.slice(2); "
                        "const b = await chromium.launch(); const p = await b.newPage(); await p.goto('file://' + s); "
                        "await p.pdf({ path: o, format: 'A4', printBackground: true, margin: { top: '12mm', bottom: '12mm', "
                        "left: '10mm', right: '10mm' } }); await b.close(); })();")
    subprocess.run(['node', js, hp, path], check=True)
    os.remove(js)
    return path, S
