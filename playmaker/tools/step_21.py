"""Step 21 (Shaun, 17 Nov 2026): how both sides use the map. The engines' equality, the named positions B1 to B3, the
forced lines and the Watch game.

python3 tools/step_21.py lgequal [n] [seed]       the lasting gap in the two engines (real read, fresh read, passes in the air)
python3 tools/step_21.py boards                    B1 and B3 read by the map
python3 tools/step_21.py lines [copies]            B1, B2, B3 and S3 by forced lines
python3 tools/step_21.py watch [tag]               eight possessions, All-Star against All-Star"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
RUN = os.path.join(ROOT, 'docs', 'runs', 'step21')
os.makedirs(RUN, exist_ok=True)


def _js(s, **opts):
    from playmaker_engine import agent as AG, jsbridge
    return json.loads(AG.JS['coverage'](json.dumps(dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), options=dict(only='lasting', **opts)))))


def cmd_lgequal(n='60', seed='21'):
    """The lasting gap, the overload groups and the answer in the two engines on random positions under the app's
    rules: the real read, the fresh read and, where a pass is in the air, its read. -> docs/runs/step21/lasting_equal.json"""
    import random
    import js_equivalence as E
    from playmaker_engine import decide as D, jsbridge
    E._ZONE['v'] = 'on'
    E._CONTROL['size'] = 'app'
    E._FIBA.update(three_seconds='on', closely_guarded='on', fiba_fouled_shot='on', soft_contest='on', fiba_steal_foul='on', off_balance='on', position_contest='on')
    eng = jsbridge.NodeEngine().install()
    rng = random.Random(int(seed))
    seen = same = pend = 0
    bad, tj, tp = [], 0.0, 0.0
    t0 = time.time()
    try:
        while seen < int(n):
            s, meta = E.random_state(rng)
            if s.stage != 'play' or not meta['digital'] or s.clock <= 2:
                continue
            seen += 1
            pend += bool(s.pending)
            ok = True
            for fresh in (False, True):
                a = time.time(); js = _js(s, fresh=fresh); tj += time.time() - a
                a = time.time(); g = D.lasting_of(s, fresh=fresh); tp += time.time() - a
                py = None if g is None else dict(L=round(g['L'], 2), before=round(g['before'], 2), overloads=g['ov'], moves=g['moves'])
                good = (js is None and py is None) or (js is not None and py is not None and abs(js['L'] - py['L']) < 0.006
                                                       and abs(js['before'] - py['before']) < 0.006 and js['overloads'] == py['overloads'] and js['moves'] == py['moves'])
                if not good and len(bad) < 8:
                    bad.append(dict(fresh=fresh, js=js, py=py, state=jsbridge.state_json(s)))
                ok = ok and good
            same += ok
    finally:
        eng.close()
    out = dict(positions=seen, with_a_pass_in_the_air=pend, equal=same, different=bad, seconds=round(time.time() - t0, 1),
               js_ms=round(1000 * tj / max(1, 2 * seen), 1), py_ms=round(1000 * tp / max(1, 2 * seen), 1))
    json.dump(out, open(os.path.join(RUN, 'lasting_equal.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'different'}))
    for b in bad[:3]:
        print(b['fresh'], b['js'], b['py'], json.dumps(b['state'])[:300])


# ---- the named positions ---------------------------------------------------------------------------------------------

def _state(o, x, ar, ball=0, off='Five Out', dfn='High-Low', **kw):
    from playmaker_engine import rules_config as RC
    from playmaker_engine.scenarios import game_state
    import step_18o as O
    s = game_state(off, dfn, list(o), list(x), list(ar), ball=ball, rules=RC.with_rules(digital=True, zone='on'), check=False, **O.T.FOULS)
    s.ctx.levels_key = ('senior', 'pro')
    return s.with_(**kw) if kw else s


def b1():
    """B1 (Shaun's example): O1 has driven into the key off O5's screen and X1 is beaten, up top behind the play. X4 and
    X5 have helped on O1, so O1, O5 rolling and O3 are 3 on 2 near the key. X2 is tight on O2 on the left wing. The
    defence to answer, phase 2, its tokens fresh (the offence has spent two actions)."""
    return _state(['I4', 'B9', 'L5', 'P10', 'J5'], ['I8', 'C8', 'P9', 'H3', 'J3'], ['S', 'E', 'N', 'S', 'S'],
                  side='X', clock=10, phase=2, tok_o=4, moved_o=1 | 16)


def b3():
    """B3 (Shaun's rotation): O1 has the ball up top; O5 has slipped to I4, the hole near the rim. X1 is beaten, behind
    the play at H11, two phases from the hole; X5 has switched onto O1. X2 (on O2 on the left wing) can get to the hole
    now (a Sprint to H4); X1 can get to the passing lane to O2 (G9). The defence to answer, phase 2."""
    return _state(['I9', 'D8', 'N8', 'P3', 'I4'], ['H11', 'E7', 'M7', 'O3', 'I8'], ['S', 'SE', 'W', 'E', 'N'],
                  side='X', clock=10, phase=2, tok_o=4, moved_o=1 | 16)


def b2():
    """B2: step 20's game 799D78, possession 4, phase 3, turn 3 (docs/runs/step20/watch2/possession4.json), replayed
    action by action from its setup (no dice were rolled in that possession): the offence to act, two tokens left."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    d = json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step20', 'watch2', 'possession4.json')))
    su = d['setup']['start']
    s = _state([p['sq'] for p in su['o']], [p['sq'] for p in su['x']], [['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][p['arrow']] for p in su['x']],
               ball=next(i for i, p in enumerate(su['o']) if p['ball']), off='High-Low', dfn='Five Out')
    for t in d['turns']:
        if (t['phase'], t['turn']) == (3, 3):
            return s
        for a in t['offence_actions'] + t['defence_actions']:
            s = apply(s, next(b for b in legal_actions(s) if str(b) == a))
    raise ValueError('B2 not reached')


def _act(s, text):
    from playmaker_engine.actions import legal_actions
    a = next((b for b in legal_actions(s) if str(b) == text), None)
    if a is None:
        raise ValueError(f'not legal: {text}')
    return a


def _turn(s, *texts):
    """A forced turn (the actions as JSON) from the actions' own words, each applied to the position it leaves."""
    from playmaker_engine.resolve import apply
    from step_18s import action_json
    out = []
    for t in texts:
        a = _act(s, t)
        out.append(action_json(a))
        s = apply(s, a)
    return out


def _lane_to(s, d, target):
    """Defender d's Move that leaves the pass to `target` least likely to arrive (the rules' own chance), the nearest to
    him on a tie: the passing lane."""
    from playmaker_engine import decide as D, board as B
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    best = None
    for a in legal_actions(s):
        if a.kind != 'move' or a.piece != d:
            continue
        n = apply(s, a)
        p = D._pass_prob(n.with_(side='O', turn_n=0), target)
        key = (p, B.cheb(a.dest, n.o[target]), str(a))
        if best is None or key < best[0]:
            best = (key, str(a))
    return best[1]


def named_lines():
    """[(id, position, [(name, turn)])] for B1, B2 and B3: the computer's own choice first, then each named line."""
    import step_18s as S
    from playmaker_engine import agent as AG
    from playmaker_engine.resolve import apply
    on = dict(pass_rules=True, map=True)
    s1, s2, s3 = b1(), b2(), b3()
    picks = S.weighed([s1, s2, s3], on, what='step 21: the computer\'s own picks (B1, B2, B3)')
    lane1 = _lane_to(s1, 0, 1)
    items = [('B1', s1, [("the computer's choice", picks[0][0][1]),
                         ('X1 chases the driver', _turn(s1, 'X1 Move to I5 facing S')),
                         ('X1 recovers to the open look the help left (O5 and O3)', _turn(s1, 'X1 Move to K6 facing S')),
                         ('X1 takes the passing lane to O2 (what Shaun saw)', _turn(s1, lane1))])]
    # B2: the line that attacks the overload at once: O2 sprints to H7 and the ball goes to whichever of O2 and O5 the
    # map then reads the bigger look for (X3 the only cover for both)
    after = apply(s2, _act(s2, 'O2 Sprint to H7'))
    c = AG.coverage(after)
    best = lambda a: max((v['worth'] for v in c['squares'][a].values()), default=-99)
    to = 1 if best(1) >= best(4) else 4
    items.append(('B2', s2, [("the computer's choice", picks[1][0][1]),
                             (f'attack the overload at once: O2 sprints to H7, O4 passes to O{to + 1}', _turn(s2, 'O2 Sprint to H7', f'O4 Pass to O{to + 1}'))]))
    items.append(('B3', s3, [("the computer's choice", picks[2][0][1]),
                             ('the rotation: X2 sprints to the hole (H4), X1 to the lane to O2 (G9)', _turn(s3, 'X2 Sprint to H4', 'X1 Move to G9 facing SW')),
                             ('X1 chases to the hole himself', _turn(s3, 'X1 Sprint to H6')),
                             ('nobody switches: X1 back onto O1, X2 stays on O2', _turn(s3, 'X1 Move to I10 facing S'))]))
    return items, picks


def cmd_lines(copies='16'):
    """B1, B2 and B3 by forced lines, 16 play-outs a line, All-Star against All-Star with the map on (same dice for
    every line of a position). -> docs/runs/step21/lines.json"""
    import step_18s as S
    from playmaker_engine import jsbridge
    S.RUN = RUN
    on = dict(pass_rules=True, map=True)
    eng = jsbridge.NodeEngine().install()             # the map's reads in this process (B2's attacking line)
    try:
        items, picks = named_lines()
    finally:
        eng.close()
    t0 = time.time()
    out = S.forced(items, int(copies), dict(O=on, X=on), what='step 21: B1, B2, B3 by forced lines')
    rep = {}
    for pid, st, cands in items:
        side = st.side
        rows = {nm: (v and {k: v[k] for k in ('mean', 'low', 'high', 'ends')}) for nm, v in out[pid].items()}
        best = (min if side == 'X' else max)(((v['mean'], nm) for nm, v in out[pid].items() if v), key=lambda z: z[0])[1]
        own = "the computer's choice"
        rep[pid] = dict(side=side, lines=rows, best_by_play=best, the_choice_in_words=S.turn_names(cands[0][1]),
                        the_choice_against_the_best=S.paired(out[pid][own], out[pid][best]),
                        turns={nm: S.turn_names(t) for nm, t in cands})
        print(pid, '| best by play:', best, '| the choice:', rep[pid]['the_choice_in_words'], rep[pid]['the_choice_against_the_best'])
        for nm, v in rows.items():
            print('     ', nm, v and (v['mean'], v['low'], v['high'], v['ends']))
    rep['seconds'] = round(time.time() - t0, 1)
    json.dump(rep, open(os.path.join(RUN, 'lines.json'), 'w'), indent=1)


def cmd_s3(copies='16'):
    """S3 again (D-209), with the map reading the defence as it really is. -> docs/runs/step21/s3.json"""
    import step_18s as S
    S.RUN = RUN
    S.cmd_s3('s3', copies, 'map')


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
