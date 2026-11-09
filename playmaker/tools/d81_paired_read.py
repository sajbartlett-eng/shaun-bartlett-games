"""Step 7 (D-81): the paired read. At every pass a defender could intercept in the 60 tabletop possessions on record
(docs/runs/3n/3n_f5_tabletop.json), the engine's read after a successful Intercept (played by the engine: -5, the phase
lost, the ball back to the passer, the interceptor back on his start square and arrow) against its read if the pass is
caught. Current rules; the rolls left out; no new games.

  python3 tools/d81_paired_read.py [out.json]
"""
import json
import os
import re
import statistics as st
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playmaker_engine import board as B, rules_config as RC                       # noqa: E402
from playmaker_engine.scenarios import game_state                                 # noqa: E402
from playmaker_engine.actions import Action, legal_actions, completed_view, lane_marks, MOVEMENT  # noqa: E402
from playmaker_engine.resolve import apply, ChanceNode, force                      # noqa: E402
from playmaker_engine.scoring import score, p_success                              # noqa: E402
from playmaker_engine.decide import Read                                           # noqa: E402


def decode(enc, off, dfn, rules):
    p = enc.split('|')
    stage, side = p[0].split(':')
    kw = {}
    o = x = arrows = None
    for f in p[1:]:
        k, v = f[0], f[1:]
        if k == 'c': kw['clock'] = int(v)
        elif k == 't': a, b = v.split('/'); kw['tok_o'], kw['tok_x'] = int(a), int(b)
        elif k == 'O': o = [B.parse_sq(q) for q in v.split(',')]
        elif k == 'X':
            x, arrows = [], []
            for q in v.split(','):
                m = re.match(r'([A-Q]\d+)([NESW]+)$', q); x.append(B.parse_sq(m.group(1))); arrows.append(B.DIR_NAMES.index(m.group(2)))
        elif k == 'b': ball = int(v) - 1
        elif k == 'm': kw['moved_o'], kw['moved_x'] = int(v[:2], 16), int(v[2:], 16)
        elif k == 'n': kw['cnt'] = tuple(int(c) for c in v)
        elif k == 'u': kw['turn_n'] = int(v[0]); kw['final'] = v.endswith('F')
        elif k == 'L': kw['lock_o'], kw['lock_x'] = int(v[:2], 16), int(v[2:], 16)
        elif k == 'S':
            scr = []
            for t in v.split(','):
                m = re.match(r'(\d)([NESW]+)(\*?)([0-9a-f]+)$', t)
                scr.append((int(m.group(1)) - 1, B.DIR_NAMES.index(m.group(2)), bool(m.group(3)), int(m.group(4), 16)))
            kw['screens'] = tuple(scr)
        elif k == 'P':
            m = re.match(r'(\d)>(\d)(?:a(\d))?', v); kw['pending'] = (int(m.group(1)) - 1, int(m.group(2)) - 1)
            if m.group(3): kw['approach'] = int(m.group(3)) - 1
        elif k == 'f':
            m = re.match(r'(\d+)\+(\d+)-(\d+)', v); kw['fouls'], kw['bonus5'], kw['tos'] = map(int, m.groups())
        elif k == 'q': kw['qs_o'], kw['qs_x'] = int(v[:2], 16), int(v[2:], 16)
    s = game_state(off, dfn, [B.sq(q) for q in o], [B.sq(q) for q in x], [B.DIR_NAMES[a] for a in arrows], ball=ball,
                   rules=rules, check=False)
    return s.with_(stage=stage, side=side, **kw)

rules = RC.DEFAULT_RULES                       # the current rules: D-18 and D-82 included


def value(n):
    if isinstance(n, ChanceNode):
        return sum(float(p) * value(x) for p, _, x in n.outcomes)
    return float(score(n).total) if n.stage == 'over' else Read(n).leaf()

def intercepted(pend, j):
    """The state after defender j's successful Intercept, by the engine (the pass roll fails), or None."""
    for a in legal_actions(pend):
        if a.kind == 'intercept' and a.piece == j:
            return force(apply(pend, a), 'failure')
    for a in legal_actions(pend):
        if a.kind in MOVEMENT and a.piece == j:
            n = apply(pend, a)
            if isinstance(n, ChanceNode) or n.stage != 'play':
                continue
            for b in legal_actions(n):
                if b.kind == 'intercept' and b.piece == j:
                    return force(apply(n, b), 'failure')
    return None


def value(n):
    if isinstance(n, ChanceNode):
        return sum(float(p) * value(x) for p, _, x in n.outcomes)
    return float(score(n).total) if n.stage == 'over' else Read(n).leaf()

def intercepted(pend, j):
    """The state after defender j's successful Intercept, by the engine (the pass roll fails), or None."""
    for a in legal_actions(pend):
        if a.kind == 'intercept' and a.piece == j:
            return force(apply(pend, a), 'failure')
    for a in legal_actions(pend):
        if a.kind in MOVEMENT and a.piece == j:
            n = apply(pend, a)
            if isinstance(n, ChanceNode) or n.stage != 'play':
                continue
            for b in legal_actions(n):
                if b.kind == 'intercept' and b.piece == j:
                    return force(apply(n, b), 'failure')
    return None

rows = json.load(open('docs/runs/3n/3n_f5_tabletop.json'))['rows']
pairs, passes, skipped = [], 0, 0
for r in rows:
    for e in r['events']:
        if e['kind'] != 'pass':
            continue
        passes += 1
        s = decode(e['state'], r['off'], r['dfn'], rules)
        m = re.match(r'O(\d) Pass to O(\d)', e['action'])
        a = Action('pass', 'O', int(m.group(1)) - 1, target=int(m.group(2)) - 1)
        if a not in legal_actions(s):
            skipped += 1
            continue
        pend = apply(s, a)
        if isinstance(pend, ChanceNode) or not pend.pending:
            continue
        marks, _ = lane_marks(pend)
        js = sorted({mk['defender'] for mk in marks},
                    key=lambda j: p_success(s.ctx.off[a.piece].r['pass'] - s.ctx.dfn[j].r['intercept'], rules))
        for j in js:                                   # the most likely interceptor first
            after = intercepted(pend, j)
            if after is None:
                continue
            caught = completed_view(pend)
            banked = 5 * s.bonus5 - 5 * s.tos
            pairs.append(dict(game=f"{r['off']} v {r['dfn']} {r['seed']}", clock=s.clock, banked=banked,
                              after=round(value(after), 2), caught=round(value(caught), 2), last=s.clock <= RC.PHASE_SECONDS,
                              over=after.stage == 'over', recv_zone=B.zone(s.o[a.target]), passer_zone=B.zone(s.o[a.piece])))
            break
gaps = [p['after'] - p['caught'] for p in pairs]
print(f'{passes} passes, {len(pairs)} pairs ({skipped} passes not legal under the current rules)')
if gaps:
    print(f'mean gap (after intercept - caught) {st.mean(gaps):+.2f}, sd {st.pstdev(gaps):.2f}, '
          f'median {st.median(gaps):+.2f}, min {min(gaps):+.2f}, max {max(gaps):+.2f}')
    better = [p for p, g in zip(pairs, gaps) if g > 0]
    print(f'offence better off after the Intercept: {len(better)} of {len(pairs)}')
    for p in sorted(better, key=lambda p: p['after'] - p['caught'], reverse=True):
        print('  better', p)
    if len(sys.argv) > 1:
        json.dump(dict(pairs=pairs), open(sys.argv[1], 'w'), indent=1)
