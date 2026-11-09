"""Agreement test set: 50 small endgames solved exactly, used to judge evaluation variants.

Each position: the final phase (clock 2), offence to act with 2 tokens (so it can set up and
then shoot, or pass and let the clock run out), defence 1 token, two active players a side.
The other pieces are parked, locked and already moved; Quick Steps and Screens are spent.
"""
import json
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor

from . import board as B
from .scenarios import game_state
from .state import CI, ZERO_COUNTS

FILL_O = ['A14', 'C14', 'E14', 'G14']
FILL_X = ['Q14', 'O14', 'M14', 'K14']
PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'data', 'agreement_set.json')


def micro(o_act, x_act, ball=0, tok_o=2, tok_x=1, clock=2):
    o, x, arr = [None] * 5, [None] * 5, ['N'] * 5
    fo, fx = iter(FILL_O), iter(FILL_X)
    for i in range(5):
        o[i] = o_act.get(str(i)) or o_act.get(i) or next(fo)
        if i in x_act or str(i) in x_act:
            x[i], arr[i] = x_act.get(i) or x_act.get(str(i))
        else:
            x[i] = next(fx)
    frozen_o = sum(1 << i for i in range(5) if i not in o_act and str(i) not in o_act)
    frozen_x = sum(1 << i for i in range(5) if i not in x_act and str(i) not in x_act)
    cnt = list(ZERO_COUNTS)
    cnt[CI['o_qs']] = cnt[CI['x_qs']] = 2
    cnt[CI['screen']] = 2
    s = game_state('Five Out', 'High-Low', o, x, arr, ball=ball, check=False)
    return s.with_(clock=clock, tok_o=tok_o, tok_x=tok_x, moved_o=frozen_o, moved_x=frozen_x, lock_o=frozen_o,
                   lock_x=frozen_x, cnt=tuple(cnt))


def specs(n=50, seed=11):
    rng = random.Random(seed)
    out = []
    squares = [(x, y) for x in range(B.W) for y in range(2, 12)]
    while len(out) < n:
        p = rng.sample(squares, 4)
        if B.zone(p[0]) == '.' and rng.random() < 0.5:
            continue
        out.append(dict(o={0: B.sq(p[0]), 1: B.sq(p[1])},
                        x={0: [B.sq(p[2]), rng.choice(B.DIR_NAMES)], 1: [B.sq(p[3]), rng.choice(B.DIR_NAMES)]}))
    return out


def state_of(spec):
    return micro({int(k): v for k, v in spec['o'].items()}, {int(k): tuple(v) for k, v in spec['x'].items()})


def _exact(spec):
    from .solver import exact_solve
    t = time.time()
    v, _ = exact_solve(state_of(spec))
    return dict(spec=spec, ev=v.ev, look=v.look, seconds=round(time.time() - t, 1))


def build(workers=4):
    with ProcessPoolExecutor(workers) as ex:
        rows = list(ex.map(_exact, specs()))
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, 'w') as f:
        json.dump(rows, f, indent=1)
    return rows


def load():
    with open(PATH) as f:
        return json.load(f)


def agreement(cfg, rows=None):
    """Mean absolute error and share within 2 points of the exact value, for an evaluation config."""
    from .solver import Evaluator
    rows = rows or load()
    errs = []
    for r in rows:
        v = Evaluator(cfg)(state_of(r['spec']))[0].ev
        errs.append(abs(v - r['ev']))
    return dict(mae=sum(errs) / len(errs), within2=sum(e <= 2 for e in errs) / len(errs), n=len(errs))
