"""Helpers the live tests borrow from modules retired in step 5, copied word for word (step 5, part 3).

- golden_setup: from playmaker_engine/soak.py (the module stays; the tests take the position from here).
- The agreement set (micro, state_of, load_agreement, agreement): from archive/engine/agreement.py. Two names
  changed because this file also holds the defence set: PATH became AGREEMENT_PATH and load became load_agreement.
- The defence sets (load, position, grade, summary_play and what they use): from archive/engine/defence_check.py.
"""
import json
import os

from playmaker_engine.actions import Action
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_engine.scenarios import game_state
from playmaker_engine.state import CI, ZERO_COUNTS


# ---- from soak.py ------------------------------------------------------------------------------------------------

def golden_setup():
    return game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'],
                      ['I10', 'D8', 'N8', 'G4', 'N4'], ['N', 'NE', 'NW', 'N', 'N'], ball=0)


# ---- from agreement.py -------------------------------------------------------------------------------------------

FILL_O = ['A14', 'C14', 'E14', 'G14']
FILL_X = ['Q14', 'O14', 'M14', 'K14']
AGREEMENT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'data', 'agreement_set.json')


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


def state_of(spec):
    return micro({int(k): v for k, v in spec['o'].items()}, {int(k): tuple(v) for k, v in spec['x'].items()})


def load_agreement():
    with open(AGREEMENT_PATH) as f:
        return json.load(f)


def agreement(cfg, rows=None):
    """Mean absolute error and share within 2 points of the exact value, for an evaluation config."""
    from playmaker_engine.solver import Evaluator
    rows = rows or load_agreement()
    errs = []
    for r in rows:
        v = Evaluator(cfg)(state_of(r['spec']))[0].ev
        errs.append(abs(v - r['ev']))
    return dict(mae=sum(errs) / len(errs), within2=sum(e <= 2 for e in errs) / len(errs), n=len(errs))


# ---- from defence_check.py ---------------------------------------------------------------------------------------

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'data', 'defence_set.json')


def _aj(a):
    return dict(kind=a.kind, side=a.side, piece=a.piece, dest=list(a.dest) if a.dest is not None else None,
                arrow=a.arrow, target=a.target, shot=a.shot)


def _ja(d):
    return Action(d['kind'], d['side'], d['piece'], tuple(d['dest']) if d['dest'] is not None else None,
                  d['arrow'], d['target'], d['shot'])


def _settle(node):
    """Follow a chance node to its most likely outcome (a pass, a dribble...)."""
    while isinstance(node, ChanceNode):
        node = max(node.outcomes, key=lambda o: o[0])[2]
    return node


def load():
    with open(PATH) as f:
        return json.load(f)


def position(row):
    st = state_of(row['spec'])
    for d in row['offence']:
        st = _settle(apply(st, _ja(d)))
    return st


def grade(policy, rows=None, tol=0.5):
    """Share of defence positions where the policy's first action is within tol of the exact best, and
    the mean gap in points (defence: higher value = worse)."""
    rows = rows or load()
    agree, gaps, missing = 0, [], 0
    for r in rows:
        st = position(r)
        a = policy.choose(st)
        v = r['values'].get(json.dumps(_aj(a)))
        if v is None:
            missing += 1
            continue
        gap = v - r['best']
        gaps.append(gap)
        agree += gap <= tol
    n = len(gaps)
    return dict(n=n, agree=agree / n if n else 0.0, mean_gap=sum(gaps) / n if n else 0.0, missing=missing)


PLAY_PATH = os.path.join(os.path.dirname(PATH), 'defence_play_set.json')


def summary_play(rows, tol=0.5):
    out = {}
    for name in ('greedy', 'reader'):
        gaps = [r['values'][name] - r['ref'] for r in rows]
        out[name] = dict(n=len(gaps), agree=sum(g <= tol for g in gaps) / len(gaps), mean_gap=sum(gaps) / len(gaps))
    return out
