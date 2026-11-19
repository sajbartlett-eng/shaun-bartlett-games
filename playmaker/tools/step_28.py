"""Step 28: the contest costs an action, one reading everywhere, the defender's stance. One reading of each board.

  python3 tools/step_28.py checks        boards 1 to 3: both setup buttons, then what the prompt asks to report
  python3 tools/step_28.py morning       the morning board of the Sharpshooter check, as it now settles
  python3 tools/step_28.py answer        D-262: which boards' map answer changes with the list leading (against the gap)
  python3 tools/step_28.py turn          one computer offence turn in play, timed (under about 20 seconds)
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'runs', 'step28')
os.makedirs(RUN, exist_ok=True)

BOARDS = (('High-Low', 'Shoot and Protect', 'board 1'), ('Twin Towers', 'Lockdown', 'board 2'),
          ('High-Low', 'Run and Gun', 'board 3'))
HIGH_SCREEN = (['I11', 'C9', 'Q3', 'A3', 'K12'], ['I10', 'D8', 'P4', 'B4', 'K11'], [0, 7, 1, 7, 0])


def _make(off, dfn):
    import step_21 as T
    from playmaker_engine import board as B
    return lambda o, b, x, a: T._state([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), ball=b, off=off, dfn=dfn)


def _save(name, out):
    json.dump(out, open(os.path.join(RUN, name), 'w'), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


def _between(B, st, perm):
    """Who stands between each big and the rim: a defender nearer the rim than him and within two squares of him."""
    from playmaker_engine import scouting as SCT
    rows = []
    for i, c in enumerate(st.ctx.off):
        if SCT.position(c) not in ('C', 'PF'):
            continue
        q = st.o[i]
        who = [f"X{j + 1} on {B.sq(x)}" for j, x in enumerate(st.x) if B.dist_rim(x) < B.dist_rim(q) and B.cheb(x, q) <= 2]
        rows.append(dict(big=f"O{i + 1} ({SCT.short_role(c)}) on {B.sq(q)}", between_him_and_the_rim=who or 'nobody'))
    return rows


def cmd_checks(only=None):
    from playmaker_engine import agent as AG, board as B, jsbridge, plan as PL, scouting as SCT
    out = {}
    eng = jsbridge.NodeEngine().install()
    try:
        for off, dfn, label in BOARDS:
            if only and only not in label:
                continue
            make = _make(off, dfn)
            t0 = time.time()
            r = PL.place_offence(make, seed=1)
            t1 = time.time()
            d = PL.place_defence(make, r['squares'], r['ball'], seed=1)
            t2 = time.time()
            st = make(r['squares'], r['ball'], d['squares'], d['arrows'])
            p = r['plan'] or {}
            jobs = []
            for z in r['roles']:
                a = z['o']
                own = ', '.join(c['name'] for c in p.get('ahead') or [] if c['o'] == a)
                jobs.append(f"O{a + 1} ({SCT.short_role(st.ctx.off[a])}) on {B.sq(r['squares'][a])}: " + (z['role'] or own or 'spacing: his look holds a defender'))
            ball_q = r['squares'][r['ball']]
            # who guards the best shooter (the best three on the cards), and how closely
            best = max(range(5), key=lambda a: (st.ctx.off[a].shot('three'), -a))
            dq = [(B.cheb(q, st.o[best]), j) for j, q in enumerate(st.x)]
            near_d = min(dq)
            from playmaker_engine import conditions as CD
            guard = dict(shooter=f"O{best + 1} ({SCT.short_role(st.ctx.off[best])}, three {st.ctx.off[best].shot('three')}) on {B.sq(st.o[best])}",
                         his_defender=f"X{d['perm'].index(best) + 1} on {B.sq(st.x[d['perm'].index(best)])}" if best in d['perm'] else None,
                         nearest=f"X{near_d[1] + 1}, {near_d[0]} squares off", stance=CD.stance(st, d['perm'].index(best), best) if best in d['perm'] else None)
            corner = [f"O{a + 1} ({SCT.short_role(c)}) on {B.sq(st.o[a])}" for a, c in enumerate(st.ctx.off)
                      if SCT.position(c) == 'C' and B.zone(st.o[a]) == '3' and st.o[a][1] <= 4]
            press = [f"X{j + 1} on {B.sq(q)} ({B.cheb(q, ball_q)} from the ball)" for j, q in enumerate(d['squares']) if B.cheb(q, ball_q) <= 3]
            out[f'{off} v {dfn}, {label}'] = dict(
                offence=dict(squares=[B.sq(q) for q in r['squares']], ball=f"O{r['ball'] + 1}", jobs=jobs,
                             in_the_key=sum(1 for q in r['squares'] if B.in_key(q)),
                             line=p.get('line'), alternative=(r.get('alternative') or {}).get('text'), words=r['words'],
                             read_ahead=r['horizon'], built_on_the_way=p.get('ahead'),
                             worth_against_the_full_defence=r['list'], table_squares=r['table'],
                             ranked_in_full=r['ranked'], read_in_full=r['full'], read_quick=r['candidates'],
                             checks=[c['text'] for c in r['checks']], seconds=round(t1 - t0, 1)),
                defence=dict(squares=[B.sq(q) for q in d['squares']], arrows=d['arrows'], read=[z['text'] for z in d['read']],
                             avoided=[z['text'] for z in d['avoided']], watching=[z['text'] for z in d.get('watching') or []],
                             read_ahead=d.get('horizon'), ways_read_ahead=d.get('ahead'), bigs=_between(B, st, d['perm']),
                             near_the_ball=press, stances=[z['text'] for z in d.get('stances') or []],
                             best_shooter=guard, seconds=round(t2 - t1, 1)),
                post_scorer_in_the_corner=corner or 'no',
                jobs_read=r.get('jobs'),
                placement_checks_after_the_defence_sets_up=[c['text'] for c in PL.placement_checks(st, PL.Scout(st.ctx, 'O'), PL.read_plan(st, PL.Scout(st.ctx, 'O')))])
    finally:
        eng.close()
    _save('checks.json' if not only else f'checks_{only.split()[0]}.json', out)


def cmd_morning():
    """The morning board of the Sharpshooter check: where the defence settles now, and what that leaves by the list."""
    from playmaker_engine import agent as AG, board as B, jsbridge, plan as PL, conditions as CD
    import step_22b as S
    eng = jsbridge.NodeEngine().install()
    try:
        s0 = S._board()
        t = time.time()
        z = S._js(s0, only='setup', evals=240)
        secs = round(time.time() - t, 1)
        st = S._board(z['x'], z['arrows']).with_(side='O', turn_n=0)
        ro = AG.coverage(st, only='roles') or {}
        perm = ro.get('perm') or list(range(5))
        cov = AG.coverage(st)
        sharp = next(i for i, c in enumerate(st.ctx.off) if 'Sharpshooter' in (c.role or ''))
        best = max(((v['worth'], k, v) for k, v in (cov['squares'][sharp] or {}).items()), default=(0, None, None))
        out = dict(defence=dict(x=z['x'], arrows=z['arrows'], seconds=secs, lines=z.get('lines')),
                   list=z['drivers']['list'][:6], sharpshooter=f"O{sharp + 1} on {B.sq(st.o[sharp])}",
                   his_best_look=dict(sq=best[1], worth=best[0], value_open=best[2] and best[2]['value'], cover=best[2] and best[2]['cover']),
                   pass_to_him=(cov.get('passes') or [None] * 5)[sharp], stances=[q['text'] for q in CD.stances(st, perm)],
                   bigs=_between(B, st, perm), route=PL.horizon_words(PL.horizon_read(st, budget=60, depth=PL.HORIZON_TURNS)))
    finally:
        eng.close()
    _save('morning.json', out)


def cmd_answer():
    """D-262: each board's settled position, the map's own answer led by the list (now) and by the lasting gap (before)."""
    from playmaker_engine import jsbridge, board as B
    import step_22b as S
    d = json.load(open(os.path.join(RUN, 'checks.json')))
    eng = jsbridge.NodeEngine().install()
    out = {}
    try:
        boards = [(k, _make(off, dfn), v) for (off, dfn, label), (k, v) in zip(BOARDS, d.items())]
        for k, make, v in boards:
            o = [B.parse_sq(q) for q in v['offence']['squares']]
            x = [B.parse_sq(q) for q in v['defence']['squares']]
            st = make(o, int(v['offence']['ball'][1:]) - 1, x, v['defence']['arrows']).with_(side='O', turn_n=0)
            a = S._js(st, only='lasting', answer=True)
            g = S._js(st, only='lasting', answer=True, answer_lead='gap')
            out[k] = dict(list_led=dict(answer=a.get('answer'), list=a['drivers']['list'][:5], L=a['L']),
                          gap_led=dict(answer=g.get('answer'), list=g['drivers']['list'][:5], L=g['L']),
                          changed=a.get('answer') != g.get('answer'))
        s0 = S._board()
        z = S._js(s0, only='setup', evals=240)
        st = S._board(z['x'], z['arrows']).with_(side='O', turn_n=0)
        a = S._js(st, only='lasting', answer=True)
        g = S._js(st, only='lasting', answer=True, answer_lead='gap')
        out['morning board'] = dict(list_led=dict(answer=a.get('answer'), list=a['drivers']['list'][:5], L=a['L']),
                                    gap_led=dict(answer=g.get('answer'), list=g['drivers']['list'][:5], L=g['L']),
                                    changed=a.get('answer') != g.get('answer'))
    finally:
        eng.close()
    _save('answer.json', out)


def cmd_turn():
    """One computer offence turn in play on the high-screen board, with its plan (the phase's re-read included)."""
    from playmaker_engine import agent as AG, jsbridge, plan as PL
    import step_21 as T
    eng = jsbridge.NodeEngine().install()
    try:
        st = T._state(*HIGH_SCREEN, off='High-Low', dfn='Run and Gun').with_(side='O', turn_n=0)
        ag = AG.Agent('O', 'allstar', seed=1)
        ag.scout = PL.Scout(st.ctx, 'O')
        ag.setup_plan = PL.read_plan(st, ag.scout, deep=True)
        t = time.time()
        a = ag.choose(st)
        out = dict(action=str(a), seconds=round(time.time() - t, 1), line=(ag.last or {}).get('plan_line') if isinstance(ag.last, dict) else None,
                   route=(ag.setup_plan or {}).get('route'), ahead=(ag.setup_plan or {}).get('horizon'))
    finally:
        eng.close()
    _save('turn.json', out)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
