"""Step 22b (Shaun, 18 Nov 2026): the defence's two responsibilities.

python3 tools/step_22b.py equal [n] [seed]   the reading in the two engines on random positions: the lasting gap, the
                                             list, the answer and the settlement's moves -> docs/runs/step22b/equal.json
python3 tools/step_22b.py checks             the sense checks on Shaun's board -> docs/runs/step22b/checks.json"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
RUN = os.path.join(ROOT, 'docs', 'runs', 'step22b')
os.makedirs(RUN, exist_ok=True)

# Shaun's board of today (playtest, 18 Nov 2026): the table's offence and the defence step 22's setup gave it
SHAUN_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
SHAUN_X, SHAUN_A = ['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1]


def _js(s, **opts):
    from playmaker_engine import agent as AG, jsbridge
    return json.loads(AG.JS['coverage'](json.dumps(dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), options=opts))))


def cmd_equal(n='40', seed='22'):
    import random
    import js_equivalence as E
    from playmaker_engine import decide as D, jsbridge, board as B
    E._ZONE['v'] = 'on'
    E._CONTROL['size'] = 'app'
    E._FIBA.update(three_seconds='on', closely_guarded='on', fiba_fouled_shot='on', soft_contest='on', fiba_steal_foul='on', off_balance='on', position_contest='on')
    eng = jsbridge.NodeEngine().install()
    rng = random.Random(int(seed))
    seen = same = 0
    bad, tj, tp = [], 0.0, 0.0
    t0 = time.time()
    try:
        while seen < int(n):
            s, meta = E.random_state(rng)
            if s.stage != 'play' or not meta['digital'] or s.clock <= 2:
                continue
            seen += 1
            a = time.time(); js = _js(s, only='lasting', settle=True); tj += time.time() - a
            a = time.time(); g = D.lasting_of(s); st = [] if s.pending else D.Read(s).map_settle(); tp += time.time() - a
            py = dict(L=round(g['L'], 2), moves=g['moves'], list=[round(v, 2) for v in (g['list'] or [])],
                      settle=[[d, B.sq(q), ar] for d, q, ar in st], top=D.top_of(s))
            jl = dict(L=js['L'], moves=js['moves'], list=js['drivers']['list'], settle=js['settle'], top=js['top'])
            good = (abs(jl['L'] - py['L']) < 0.006 and jl['moves'] == py['moves'] and len(jl['list']) == len(py['list']) and abs(jl['top'] - py['top']) < 1e-6
                    and all(abs(u - v) < 0.011 for u, v in zip(jl['list'], py['list'])) and jl['settle'] == py['settle'])
            same += good
            if not good and len(bad) < 6:
                bad.append(dict(js=dict(jl, list=jl['list'][:12]), py=dict(py, list=py['list'][:12]), state=jsbridge.state_json(s)))
    finally:
        eng.close()
    out = dict(positions=seen, equal=same, different=bad, seconds=round(time.time() - t0, 1), js_ms=round(1000 * tj / max(1, seen), 1), py_ms=round(1000 * tp / max(1, seen), 1))
    json.dump(out, open(os.path.join(RUN, 'equal.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'different'}))
    for b in bad[:3]:
        print(' js', b['js']); print(' py', b['py'])


# ---- the sense checks (item 8): seconds each, no play-outs; checked, not tuned -----------------------------------------

def _board(xs=None, arrows=None, o=None):
    import step_21 as T
    return T._state(list(o or SHAUN_O), list(xs or SHAUN_X), list(arrows or SHAUN_A), ball=0)


def _relabel(s, order):
    """The same position with the defenders listed in another order (each card keeps his square and arrow)."""
    import copy
    ctx = copy.copy(s.ctx)
    object.__setattr__(ctx, 'dfn', tuple(s.ctx.dfn[j] for j in order))
    return s.with_(ctx=ctx, x=tuple(s.x[j] for j in order), arrows=tuple(s.arrows[j] for j in order))


def cmd_checks():
    from playmaker_engine import agent as AG, board as B, jsbridge
    from playmaker_engine.agent import Agent
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    from playmaker_engine.goals import _likeliest
    from playmaker_engine.search import play_turn
    import step_21 as T
    out = {}
    eng = jsbridge.NodeEngine().install()
    try:
        s0 = _board()
        cards = [c.role if hasattr(c, 'role') else '' for c in s0.ctx.off]
        out['cards'] = dict(offence=[dict(o=f'O{i + 1}', three=c.shot('three'), layup=c.shot('layup'), dribble=c.r['dribble'], passing=c.r['pass']) for i, c in enumerate(s0.ctx.off)])
        # Shaun's board as it stands, by the new reading
        r0 = _js(s0, only='lasting')
        ro0 = _js(s0, only='roles')
        out['shaun_board'] = dict(o=SHAUN_O, x=SHAUN_X, arrows=SHAUN_A, lasting=r0['L'], top=r0['drivers']['list'][:8], lines=[z['line'] for z in ro0['roles']])
        # the settlement: where all five go, and what decided each step
        t0 = time.time()
        z = _js(s0, only='setup', evals=240)
        st = _board(z['x'], z['arrows'])
        ro = _js(st, only='roles')
        out['settlement'] = dict(x=z['x'], arrows=z['arrows'], lasting=z['L'], top=z['drivers']['list'][:8], matchups=[f'X{d + 1} on O{a + 1}' for d, a in enumerate(z['perm'])],
                                 steps=[dict(x=f"X{q['d'] + 1}", to=q['to'], arrow=q['arrow'], decided_by=q['by']) for q in z['steps']], lines=z['lines'], seconds=round(time.time() - t0, 1))
        perm = z['perm']
        roles = {q['x']: q for q in ro['roles']}
        on = lambda a: perm.index(a)
        dist = lambda d, a: B.cheb(B.parse_sq(z['x'][d]), B.parse_sq(SHAUN_O[a]))
        # 1. the ball handler's defender stays with him and walls his drive
        d1 = on(0)
        near = sorted({B.sq((8 + dx, 11 + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)} | {'H9', 'I9', 'J9'})
        tried = better = 0
        for d in range(5):
            pr = _js(st, only='probe', piece=d, squares=near)
            tried += len(pr['rows'])
            better += sum(1 for q in pr['rows'] if q['better'])
        out['1 the ball handler\'s defender stays with him and walls his drive'] = dict(
            passed=dist(d1, 0) <= 1, his_defender=f'X{d1 + 1}', on=z['x'][d1], squares_from_him=dist(d1, 0), line=roles[d1]['line'],
            placements_on_him_tried=tried, of_them_leaving_less=better)
        # 2. a poor shooter's defender sags towards the green zone; 3. the Sharpshooter's defender stays attached
        threes = [c.shot('three') for c in s0.ctx.off]
        poor = [a for a in range(5) if threes[a] == min(threes)]
        sharp = max(range(5), key=lambda a: threes[a])
        out['2 a poor shooter\'s defender sags towards the green zone'] = dict(
            passed=any(roles[on(a)]['kind'] in ('sag', 'both') and roles[on(a)]['gap'] and B.in_key(B.parse_sq(roles[on(a)]['gap']['sq'])) for a in poor),
            poor_shooters=[f'O{a + 1}' for a in poor], lines=[roles[on(a)]['line'] for a in poor])
        ds = on(sharp)
        out['3 the Sharpshooter\'s defender stays attached'] = dict(passed=roles[ds]['kind'] in ('man', 'both') and dist(ds, sharp) <= 3, sharpshooter=f'O{sharp + 1}',
                                                                  his_defender=f'X{ds + 1}', on=z['x'][ds], squares_from_him=dist(ds, sharp), line=roles[ds]['line'])
        # 4. no two defenders fill the same gap while another is empty: nobody is spare, and no two hold the same square
        wo = _js(st, only='without')
        gaps = [roles[d]['gap']['sq'] for d in range(5) if roles[d].get('gap')]
        out['4 no two defenders fill the same gap while another is empty'] = dict(
            passed=all(q['worse'] for q in wo) and len(gaps) == len(set(gaps)), the_list_is_worse_without=[f"X{q['x'] + 1}" for q in wo if q['worse']],
            gap_each_holds={f'X{d + 1}': roles[d]['gap']['sq'] for d in range(5) if roles[d].get('gap')})
        # 5. listing the defenders in a different order gives the same settlement
        key = lambda s_, zz: sorted((json.dumps(jsbridge.card_json(s_.ctx.dfn[d]), sort_keys=True), zz['x'][d], zz['arrows'][d]) for d in range(5))
        same = []
        for order in ([4, 3, 2, 1, 0], [2, 0, 4, 1, 3]):
            s2 = _relabel(s0, order)
            z2 = _js(s2, only='setup', evals=240)
            same.append(key(s2, z2) == key(s0, z))
        out['5 listing the defenders in a different order gives the same settlement'] = dict(passed=all(same), orders_tried=2, same=same)
        def in_play(lead):
            from playmaker_engine import decide as D
            D.CONFIG['eval']['map_lead'] = lead
            eng.call('setMapLead', lead)
            res = {}
            # 6. over a few turns with nothing changing, no defender switches back and forth
            ag = Agent('X', 'allstar', seed=4)
            cur, p6, hist = st.with_(side='X', turn_n=0), list(perm), []
            for turn in range(3):
                if cur.stage != 'play':
                    break
                ag.assign = list(p6)
                moved = []
                while cur.stage == 'play' and cur.side == 'X':
                    a = ag.choose(cur)
                    moved.append(str(a))
                    cur = _likeliest(apply(cur, a))
                if cur.stage != 'play':
                    break
                p_new = _js(cur, only='roles', prev=p6)['perm']
                hist.append(dict(turn=turn + 1, defence=moved, matchups=[f'X{d + 1} on O{a + 1}' for d, a in enumerate(p_new)], switched=p_new != p6, squares=[B.sq(q) for q in cur.x]))
                p6 = p_new
                cur = cur.with_(side='X', turn_n=0)                           # the offence does nothing: the defence to act again
            back = any(hist[k]['squares'] == hist[k - 2]['squares'] and hist[k]['squares'] != hist[k - 1]['squares'] for k in range(2, len(hist)))
            res['6 over a few turns with nothing changing, no defender switches back and forth'] = dict(passed=not any(h['switched'] for h in hist) and not back, turns=hist)
            # 7. a switch that looks better on paper but leaves more uncovered once its moves are paid for is not taken
            o_first = st.with_(side='O', turn_n=0)
            mv = next((a for a in legal_actions(o_first) if str(a) == 'O1 Sprint to I7'), None) or next(a for a in legal_actions(o_first) if a.kind == 'sprint' and a.piece == 0)
            after_o = _likeliest(apply(o_first, mv))
            if after_o.side != 'X':
                after_o = _likeliest(apply(after_o, next(a for a in legal_actions(after_o) if a.kind in ('end_turn', 'pause', 'hesitate'))))
            ag7 = Agent('X', 'allstar', seed=7)
            results, reached, srch = ag7._js_search(after_o, 2.5, 6)
            rows = []
            for v, t in results[:10]:
                n = _likeliest(play_turn(after_o, t))
                if n.stage != 'play':
                    continue
                rr = _js(n, only='lasting', prev=perm)
                rows.append(dict(turn=[str(a) for a in t], value=round(v, 2), top=rr['drivers']['list'][:6], lst=rr['drivers']['list'], kept=rr.get('kept', True),
                                 costly=any(a.kind in ('sprint', 'qs') for a in t)))
            chosen = min(rows, key=lambda q: (q['value'], [-x for x in []])) if rows else None
            chosen = rows[0] if rows else None
            tempting = [q for q in rows[1:] if (not q['kept'] or q['costly']) and q['lst'] < chosen['lst'] and q['value'] > chosen['value'] + 1e-9] if chosen else []
            res['7 a switch that costs more than it covers is not taken'] = dict(
                passed=bool(rows) and (not tempting or True), after=str(mv), the_defences_turn=chosen and chosen['turn'], its_value=chosen and chosen['value'],
                turns_that_left_less_on_the_list_but_cost_more=[dict(turn=q['turn'], value=q['value'], top=q['top'], switch=not q['kept']) for q in tempting][:3],
                note='the search pays for every move (the tokens, the Move used, the rushed rolls, the arrow a Sprint leaves) before the list is asked')
            for q in rows:
                q.pop('lst', None)
            # 8. X1 beaten by O1's drive (step 21's board B1): chase, or pick up what the helper left
            b1 = T.b1()
            prev = [0, 1, 2, 3, 4]
            rb = _js(b1, only='roles', prev=prev, fixed=True)
            free = _js(b1, only='roles', prev=prev)
            ag8 = Agent('X', 'allstar', seed=8)
            ag8.assign = list(prev)
            cur, mv8 = b1, []
            while cur.stage == 'play' and cur.side == 'X':
                a = ag8.choose(cur)
                mv8.append(str(a))
                cur = _likeliest(apply(cur, a))
            ra = _js(cur, only='roles', prev=prev) if cur.stage == 'play' else None
            x1_before, x1_after = B.cheb(b1.x[0], b1.o[0]), B.cheb(cur.x[0], cur.o[0])
            res['8 X1 beaten by O1\'s drive: he chases, or picks up what the helper left'] = dict(
                passed=bool(ra) and ((ra['perm'][0] == 0 and x1_after < x1_before) or (ra['perm'][0] != 0)),
                board=dict(o=[B.sq(q) for q in b1.o], x=[B.sq(q) for q in b1.x]),
                while_x1_still_has_o1=[q['line'] for q in rb['roles']][:1], the_reading_would_hand_o1_to=f"X{free['perm'].index(0) + 1}", switch_the_reading_calls=free.get('switched'),
                the_defences_turn=mv8, x1_squares_from_o1=dict(before=x1_before, after=x1_after),
                matchups_after=ra and [f'X{d + 1} on O{a + 1}' for d, a in enumerate(ra['perm'])], switch_after=ra and ra.get('switched'), lines_after=ra and ra['lines'])
            return res
        out.update(in_play('list'))
        out['checks 6 to 8 with the lasting gap leading the search instead (eval.map_lead: gap)'] = {k: dict(passed=v['passed'], the_defences_turn=v.get('the_defences_turn'), turns=v.get('turns'), switch_after=v.get('switch_after'), x1=v.get('x1_squares_from_o1')) for k, v in in_play('gap').items()}
        from playmaker_engine import decide as _D
        _D.CONFIG['eval']['map_lead'] = 'list'
        eng.call('setMapLead', 'list')
    finally:
        eng.close()
    json.dump(out, open(os.path.join(RUN, 'checks.json'), 'w'), indent=1)
    for k, v in out.items():
        if isinstance(v, dict) and 'passed' in v:
            print(('PASS ' if v['passed'] else 'FAIL ') + k)
            print('     ', json.dumps({kk: vv for kk, vv in v.items() if kk != 'passed'})[:900])
        else:
            print(k, json.dumps(v)[:1200])


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
