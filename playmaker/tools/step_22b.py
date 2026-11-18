"""Step 22b (Shaun, 18 Nov 2026): position and arrow logic, ranked drivers, the screen that blocks the path around it.

python3 tools/step_22b.py board      Shaun's board of today read by the map, and where the computer puts each player and
                                     why (which ranked driver decided it). -> docs/runs/step22b/board.json"""
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
DRIVER = {'a': 'the lasting gap', 'b': "the offence's least likely actions (the rules' chances)", 'c': 'efficiency (fewest actions)',
          'd': 'doubled cover', 'looks behind': 'the looks behind the gap'}


def cmd_board():
    from playmaker_engine import agent as AG, board as B, jsbridge
    from playmaker_engine.agent import Agent
    import step_21 as T
    make = lambda oo, b, x, a: T._state([B.sq(q) for q in oo], [B.sq(q) for q in x], list(a), ball=b)
    make_names = lambda o, x, a, b: T._state(list(o), list(x), list(a), ball=b)
    o = [B.parse_sq(q) for q in SHAUN_O]
    eng = jsbridge.NodeEngine().install()
    out = {}
    try:
        s_shaun = make(o, 0, [B.parse_sq(q) for q in SHAUN_X], SHAUN_A)
        out['shaun_board'] = dict(o=SHAUN_O, x=SHAUN_X, arrows=SHAUN_A, drivers=AG.coverage(s_shaun, only='lasting')['drivers'],
                                  roles=[r['line'] for r in AG.coverage(s_shaun, only='roles')])
        t0 = time.time()
        r = AG.coverage(s_shaun, only='setup', evals=240)
        out['defence_setup'] = dict(x=r['x'], arrows=r['arrows'], L=r['L'], start=r['start'], drivers=r['drivers'],
                                    steps=[dict(s, x=f"X{s['d'] + 1}", why=DRIVER[s['by']]) for s in r['steps']], seconds=round(time.time() - t0, 1))
        s_new = make(o, 0, [B.parse_sq(q) for q in r['x']], r['arrows'])
        out['defence_setup']['roles'] = [z['line'] for z in AG.coverage(s_new, only='roles')]
        t0 = time.time()
        off = AG._fixed_offence(make_names, 22, budget=20, level='allstar')
        out['offence_setup'] = dict(o=[B.sq(q) for q in off['squares']], ball=off['ball'], value=off['value'], text=off['text'],
                                    steps=[dict(z, why=DRIVER[z['by']]) for z in off.get('steps', [])], seconds=round(time.time() - t0, 1))
        # the first turn from tip-off on the defence the computer set, each side's own choice
        ag_o, ag_x = Agent('O', 'allstar', seed=3), Agent('X', 'allstar', seed=4)
        st = s_new
        turns = []
        from playmaker_engine.resolve import apply
        from playmaker_engine.search import actor
        from playmaker_engine.goals import _likeliest
        for _ in range(4):
            if st.stage != 'play':
                break
            side = actor(st)
            a = (ag_o if side == 'O' else ag_x).choose(st)
            turns.append(dict(side=side, action=str(a)))
            st = _likeliest(apply(st, a))
        out['first_turns'] = [dict(side=t['side'], action=t['action']) for t in turns]
    finally:
        eng.close()
    json.dump(out, open(os.path.join(RUN, 'board.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
