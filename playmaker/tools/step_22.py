"""Step 22 (Shaun, 18 Nov 2026): fix it, merge it, hand it to Shaun to test. The forced lines.

python3 tools/step_22.py setup [copies]     the table's offence against three setups, played from tip-off
python3 tools/step_22.py b1 [copies]        B1 (step 21's beaten defender) by forced lines
python3 tools/step_22.py s3 [copies]        S3 (Shaun's screen sequence) by forced lines"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
RUN = os.path.join(ROOT, 'docs', 'runs', 'step22')
os.makedirs(RUN, exist_ok=True)
ON = dict(pass_rules=True, map=True)

PAINT = ['I10', 'D8', 'O8', 'H4', 'J4']        # packed paint: X4 and X5 in the key, the rest on their men


def setups():
    """The table's offence (the app's own preset) against the hug, the packed paint and the computer's own setup."""
    from playmaker_engine import agent as AG, board as B, jsbridge
    from playmaker_web.game import TABLE_O, man_to_man
    import step_21 as T
    o = [B.parse_sq(q) for q in TABLE_O]
    hug, ar = man_to_man(o, 0)
    make = lambda oo, b, x, a: T._state([B.sq(q) for q in oo], [B.sq(q) for q in x], list(a), ball=b)
    eng = jsbridge.NodeEngine().install()
    try:
        mine = AG._map_setup(make, o, 0)
        rows = []
        for nm, xs, a in (('the hug (each defender next to his man)', hug, ar),
                          ('the packed paint (X4 and X5 in the key)', [B.parse_sq(q) for q in PAINT], ar),
                          ("the computer's own setup (the map's answer)", mine[0], mine[1])):
            s = make(o, 0, xs, a)
            c = AG.coverage(s)
            rows.append((nm, s, dict(squares=[B.sq(q) for q in xs], arrows=list(a), lasting=c['lasting'], before=c['before'])))
    finally:
        eng.close()
    return rows


def cmd_setup(copies='16'):
    import step_18s as S
    S.RUN = RUN
    rows = setups()
    items = [(nm, s, [('played from tip-off', None)]) for nm, s, _ in rows]
    t0 = time.time()
    out = S.forced(items, int(copies), dict(O=ON, X=ON), what='step 22: the setup board by forced lines')
    rep = {}
    for nm, s, info in rows:
        v = out[nm]['played from tip-off']
        rep[nm] = dict(info, play=v and {k: v[k] for k in ('mean', 'low', 'high', 'ends')})
        print(nm, info, rep[nm]['play'] and (rep[nm]['play']['mean'], rep[nm]['play']['low'], rep[nm]['play']['high']))
    rep['seconds'] = round(time.time() - t0, 1)
    json.dump(rep, open(os.path.join(RUN, 'setup.json'), 'w'), indent=1)


def cmd_b1(copies='16'):
    import step_18s as S
    import step_21 as T
    from playmaker_engine import jsbridge
    S.RUN = RUN
    eng = jsbridge.NodeEngine().install()
    try:
        s1 = T.b1()
        pick = S.weighed([s1], ON, what="step 22: the computer's own pick (B1)")[0]
        lane = T._lane_to(s1, 0, 1)
        cands = [("the computer's choice", pick[0][1]),
                 ('X1 chases the driver', T._turn(s1, 'X1 Move to I5 facing S')),
                 ('X1 recovers to the open look the help left (O5 and O3)', T._turn(s1, 'X1 Move to K6 facing S')),
                 ('X1 takes the passing lane to O2 (what Shaun saw)', T._turn(s1, lane))]
    finally:
        eng.close()
    t0 = time.time()
    out = S.forced([('B1', s1, cands)], int(copies), dict(O=ON, X=ON), what='step 22: B1 by forced lines')['B1']
    best = min(((v['mean'], nm) for nm, v in out.items() if v), key=lambda z: z[0])[1]
    rep = dict(best_by_play=best, the_choice_in_words=S.turn_names(cands[0][1]),
               lines={nm: v and {k: v[k] for k in ('mean', 'low', 'high', 'ends')} for nm, v in out.items()},
               turns={nm: S.turn_names(t) for nm, t in cands}, seconds=round(time.time() - t0, 1))
    print('B1 | best by play:', best, '| the choice:', rep['the_choice_in_words'])
    for nm, v in rep['lines'].items():
        print('     ', nm, v and (v['mean'], v['low'], v['high'], v['ends']))
    json.dump(rep, open(os.path.join(RUN, 'b1.json'), 'w'), indent=1)


def cmd_s3(copies='16'):
    import step_18s as S
    S.RUN = RUN
    S.cmd_s3('s3', copies, 'map')


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
