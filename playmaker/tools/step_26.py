"""Step 26 (Shaun, 19 Nov 2026): the defence feels the danger of the pass; then is the offence still bunching? Each check
is a single reading of one board.

python3 tools/step_26.py checks     -> docs/runs/step26/checks.json"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
RUN = os.path.join(ROOT, 'docs', 'runs', 'step26')
os.makedirs(RUN, exist_ok=True)

BOARDS = (('High-Low', 'Shoot and Protect', 'board 1 (hot-seat 8427AA)'), ('Twin Towers', 'Lockdown', 'board 2 (computer v computer AC7286)'))


def _make(off, dfn):
    import step_21 as T
    from playmaker_engine import board as B
    return lambda o, b, x, a: T._state([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), ball=b, off=off, dfn=dfn)


def _post_side(B, xq, oq, passer):
    """Where a defender stands against a big: behind (nearer the rim), in front (between him and the passer), or beside."""
    if not B.adjacent(xq, oq):
        return f'{B.cheb(xq, oq)} squares off'
    if B.dist_rim(xq) < B.dist_rim(oq):
        return 'behind him (between him and the rim)'
    if B.cheb(xq, passer) < B.cheb(oq, passer):
        return 'in front of him (fronting, between him and the passer)'
    return 'beside him'


def cmd_checks():
    from playmaker_engine import agent as AG, board as B, jsbridge, plan as PL, scouting as SCT, decide as D
    from playmaker_web.game import TABLE_O
    out = {}
    eng = jsbridge.NodeEngine().install()
    try:
        for off, dfn, label in BOARDS:
            make = _make(off, dfn)
            t0 = time.time()
            r = PL.place_offence(make, seed=1, budget=12)
            t1 = time.time()
            d = PL.place_defence(make, r['squares'], r['ball'], seed=1)
            t2 = time.time()
            st = make(r['squares'], r['ball'], d['squares'], d['arrows'])
            in_key = [i for i, q in enumerate(r['squares']) if B.in_key(q)]
            bunch_far = min((B.dist_rim(r['squares'][i]) for i in in_key), default=None)
            between = [f"X{j + 1} on {B.sq(q)}" for j, q in enumerate(d['squares']) if bunch_far is not None and B.dist_rim(q) <= bunch_far]
            base = [B.parse_sq(q) for q in TABLE_O]
            tab = AG._map_setup(make, base, 0, evals=0)
            p = r['plan'] or {}
            bigs = [i for i, c in enumerate(st.ctx.off) if SCT.position(c) in ('C', 'PF') and B.in_key(r['squares'][i])]
            post = []
            for i in bigs:
                j = d['perm'].index(i) if i in d['perm'] else None
                if j is not None:
                    post.append(dict(big=f"O{i + 1} {st.ctx.off[i].role} on {B.sq(r['squares'][i])}", his_defender=f"X{j + 1} on {B.sq(d['squares'][j])}",
                                     where=_post_side(B, d['squares'][j], r['squares'][i], r['squares'][r['ball']]),
                                     the_pass_to_him_lands=round(D.cov_pass(st, i, st.o[i]), 2) if i != st.ball else 'he has the ball'))
            out[f'{off} v {dfn}, {label}'] = dict(
                offence=dict(squares=[B.sq(q) for q in r['squares']], ball=f"O{r['ball'] + 1}", in_the_key=[f"O{i + 1} on {B.sq(r['squares'][i])}" for i in in_key],
                             plan=p.get('target'), needs=p.get('needs'), plan_worth=r['value'], table_squares_worth=tab and round(float(tab[2]), 2),
                             bars=[b['bar'] for b in PL.bars(st)], checks=[c['text'] for c in r['checks']], seconds=round(t1 - t0, 1)),
                defence=dict(squares=[B.sq(q) for q in d['squares']], arrows=d['arrows'], read=[z['text'] for z in d['read']], avoided=[z['text'] for z in d['avoided']],
                             watching=[z['text'] for z in d.get('watching') or []], between_the_bunch_and_the_rim=between, seconds=round(t2 - t1, 1)),
                post_defence=post,
                placement_checks_after_the_defence_sets_up=[c['text'] for c in PL.placement_checks(st, PL.Scout(st.ctx, 'O'), PL.read_plan(st, PL.Scout(st.ctx, 'O')))])
    finally:
        eng.close()
    json.dump(out, open(os.path.join(RUN, 'checks.json'), 'w'), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
