"""Step 27: the computer sets up the way it plays. One reading of each board (no play-outs).

  python3 tools/step_27.py checks        the three boards: both setup buttons, then what the prompt asks to report
  python3 tools/step_27.py ahead         the high-screen board as step 24 built it, read ahead (does the corner dive appear?)
  python3 tools/step_27.py sharp         the Sharpshooter question on the morning board (change nothing)
  python3 tools/step_27.py turn          one computer offence turn in play, timed (under about 20 seconds)
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'runs', 'step27')
os.makedirs(RUN, exist_ok=True)

BOARDS = (('High-Low', 'Shoot and Protect', 'board 1'), ('Twin Towers', 'Lockdown', 'board 2'),
          ('High-Low', 'Run and Gun', "step 24's high-screen board (its teams)"))
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
                             near_the_ball=press, seconds=round(t2 - t1, 1)),
                placement_checks_after_the_defence_sets_up=[c['text'] for c in PL.placement_checks(st, PL.Scout(st.ctx, 'O'), PL.read_plan(st, PL.Scout(st.ctx, 'O')))])
    finally:
        eng.close()
    _save('checks.json' if not only else f'checks_{only.split()[0]}.json', out)


def cmd_ahead():
    """The high-screen board as step 24 built it: is the corner player's dive read once the board is read ahead?"""
    from playmaker_engine import agent as AG, jsbridge, plan as PL, conditions as CD
    import step_21 as T
    eng = jsbridge.NodeEngine().install()
    try:
        st = T._state(*HIGH_SCREEN, off='High-Low', dfn='Run and Gun').with_(side='O', turn_n=0)
        out = {}
        for depth in (1, 2, 3, 4):
            t = time.time()
            h = PL.horizon_read(st, budget=90, depth=depth)
            out[f'{depth} turns'] = dict(list=h['list'], turns=h['turns'], words=PL.horizon_words(h), conditions=CD.ahead(h, st), seconds=round(time.time() - t, 1))
        cov = AG.coverage(st)
        o3 = {k: v['worth'] for k, v in (cov['squares'][2] or {}).items() if v.get('worth', 0) >= 20}
        out['O3 (corner) looks worth 20 or more, one turn'] = o3
        # the screen, then the dive: the screen's own continuation, read a turn on
        rows = []
        for words, after, act in PL._continuations(st, None):
            if act.kind != 'screen':
                continue
            nxt, dn = PL._defence_turn(after)
            c2 = AG.coverage(nxt.with_(turn_n=0))
            rows.append(dict(turn=words, defence=dn, list=PL.list_key(AG.coverage(nxt.with_(turn_n=0), only='lasting'))[0][:5],
                             O3_paint=max((v['worth'] for k, v in (c2['squares'][2] or {}).items() if k[0] in 'GHIJK' and int(k[1:]) <= 6), default=0)))
        out['screens read a turn on'] = rows
    finally:
        eng.close()
    _save('ahead.json', out)


def cmd_sharp():
    """Shaun's question (step 22b's morning board, as it now settles): change nothing, read it."""
    from playmaker_engine import agent as AG, board as B, jsbridge, plan as PL
    import step_22b as S
    eng = jsbridge.NodeEngine().install()
    try:
        st = S._board(['D5', 'O5', 'L6', 'G7', 'I4'], [1, 0, 0, 4, 1]).with_(side='O', turn_n=0)
        cov = AG.coverage(st)
        r = AG.coverage(st, only='lasting')
        roles = AG.coverage(st, only='roles') or {}
        best = lambda a, c=cov: max((((v['worth'], k, v) for k, v in (c['squares'][a] or {}).items())), default=(0, None, None))
        sharp = next(i for i, c in enumerate(st.ctx.off) if 'Sharpshooter' in (c.role or ''))
        bs = best(sharp)
        lk = bs[2] or {}
        helpers = dict(his_best_look=dict(sq=bs[1], worth=bs[0], shot=lk.get('shot'), chance=lk.get('reach'), value_open=lk.get('value'),
                                          weakness=lk.get('weakness'), cover=lk.get('cover'), next=lk.get('next')),
                       defenders_near=[f"X{d + 1} on {B.sq(q)}" for d, q in enumerate(st.x) if B.cheb(q, st.o[sharp]) <= 3])
        open_ = sorted(((best(a)[0], a) for a in range(5) if a != sharp), reverse=True)
        a0 = open_[0][1]
        w, k, v = best(a0)
        out = dict(board=dict(o=[B.sq(q) for q in st.o], x=[B.sq(q) for q in st.x], arrows=list(st.arrows), ball=f"O{st.ball + 1}"),
                   sharpshooter=f"O{sharp + 1} on {B.sq(st.o[sharp])}", helping_on_him=helpers,
                   sharpshooter_best=dict(zip(('worth', 'sq'), best(sharp)[:2])),
                   most_open_other=dict(o=f"O{a0 + 1}", sq=k, worth=w, chance_it_goes_up=v and v.get('reach'), value_if_it_does=v and v.get('value'), shot=v and v.get('shot')),
                   list=r['drivers']['list'][:6], L=r['L'], passes={f"O{a + 1}": p for a, p in enumerate(cov.get('passes') or [])})
        # the pass to him cut instead: the defender nearest the lane stands in it (the map's own reading of that board)
        from playmaker_engine import decide as D
        pr = D.cov_pass(st, sharp, st.o[sharp])
        # place one defender on each square of the lane (between the ball and him) and read the board again
        bq, sq_ = st.o[st.ball], st.o[sharp]
        lane = [q for q in ((x, y) for x in range(B.W) for y in range(1, B.H + 1)) if B.on_board(q) and q not in st.o and q not in st.x
                and B.cheb(q, bq) + B.cheb(q, sq_) <= B.cheb(bq, sq_) + 1 and B.cheb(q, sq_) <= 3]
        best_cut = None
        for d in range(5):
            for q in lane:
                for ar in range(8):
                    xs = list(st.x); arr = list(st.arrows); xs[d] = q; arr[d] = ar
                    t = st.with_(x=tuple(xs), arrows=tuple(arr))
                    p2 = D.cov_pass(t, sharp, t.o[sharp])
                    if p2 > 0.25:
                        continue
                    rr = AG.coverage(t, only='lasting')
                    k2 = PL.list_key(rr)
                    if best_cut is None or k2 < best_cut[0]:
                        best_cut = (k2, d, q, ar, p2, t)
        if best_cut:
            k2, d, q, ar, p2, t = best_cut
            c2 = AG.coverage(t)
            sb = max(((v['worth'], kk) for kk, v in (c2['squares'][sharp] or {}).items()), default=(0, None))
            oth = sorted(((max((v['worth'] for v in (c2['squares'][a] or {}).values()), default=0), a) for a in range(5) if a != sharp), reverse=True)
            a1 = oth[0][1]
            w1, k1, v1 = best(a1, c2)
            out['pass_cut_instead'] = dict(defender=f"X{d + 1} to {B.sq(q)}", pass_lands=round(p2, 2), sharpshooter_best=dict(worth=sb[0], sq=sb[1]),
                                           left_open=dict(o=f"O{a1 + 1}", sq=k1, worth=w1, chance=v1 and v1.get('reach'), value=v1 and v1.get('value'), shot=v1 and v1.get('shot')),
                                           list=list(k2[0][:6]))
        out['pass_to_him_now'] = round(pr, 2)
    finally:
        eng.close()
    _save('sharp.json', out)


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
