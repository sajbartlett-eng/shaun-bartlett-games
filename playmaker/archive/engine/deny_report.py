"""Research tool: how a pairing's possessions end against the computer defence. For each seed the offence (All-Star
unless told otherwise) plays the table start of the pairing against the defence at the given level; the final shot
(shooter, type, points, contester) is recorded. Reports the share of possessions ending with a given shooter's shot
and the points by shooter. Used for the designer's report on Five Out v High-Low (O2's contested three).
  python3 -m playmaker_engine.deny_report --x allstar --n 20 [--o allstar] [--budget 2]"""
import argparse
import json
import random
import time
from collections import Counter, defaultdict


class Hunter:
    """The designer's offence: get the ball to one shooter (O2 by default) and take his three. Pass to him when the
    lane is clean; otherwise move him onto a three square or move the carrier; he shoots the three as soon as he has
    the ball on one. Legal actions only; the engine decides everything."""
    def __init__(self, who=1, seed=0):
        import random as _r
        self.who, self.rng = who, _r.Random(seed)

    def choose(self, s):
        from . import board as B
        from .actions import legal_actions
        from .computer import pass_risk
        acts = legal_actions(s)
        if len(acts) == 1:
            return acts[0]
        k = lambda kind: [a for a in acts if a.kind == kind]
        if s.stage in ('target', 'pick', 'forced'):
            t = [a for a in acts if getattr(a, 'target', -1) == self.who] or k('forced_shot') or acts
            return t[0]
        who = self.who
        if s.ball == who:
            three = [a for a in k('shot') if (a.shot or '') == 'three']
            if three:
                return three[0]
            mv = [a for a in k('move') + k('qs') if a.piece == who and B.zone(a.dest) == '3']
            if mv:
                return self.rng.choice(mv)
            other = k('shot')
            if other and s.clock <= 4:
                return other[0]
        else:
            ps = [a for a in k('pass') if a.target == who]
            if ps:
                info = pass_risk(s, s.ball, who)
                if info and info['clean']:
                    return ps[0]
            mv = [a for a in k('move') + k('qs') if a.piece == who and B.zone(a.dest) == '3' and a.dest != s.o[who]]
            if mv and not s.moved('O', who):
                return self.rng.choice(mv)
            if ps and s.clock <= 4:
                return ps[0]
            cm = [a for a in k('move') if a.piece == s.ball]
            if cm and not s.moved('O', s.ball):
                return self.rng.choice(cm)
        e = k('end_turn') or k('hesitate') or k('shot') or k('forced_shot')
        return e[0] if e else acts[0]


def play(o_level, x_level, off, dfn, seed, budget_s, place=False):
    from . import board as B
    from .computer import Computer, BUDGET
    from .resolve import apply, ChanceNode, sample
    from .scenarios import game_state
    from .headtohead import TABLE_O, TABLE_X, TABLE_ARROWS
    from .scoring import score
    BUDGET['active'] = budget_s
    pols = {'O': Hunter(int(o_level.split(':')[1]) - 1, seed) if o_level.startswith('hunt:') else Computer('O', o_level, seed=seed),
            'X': Computer('X', x_level, seed=seed)}
    rng = random.Random(seed * 1009 + 7)
    s = game_state(off, dfn, TABLE_O, TABLE_X, TABLE_ARROWS)
    if place:
        # the computer defence places its own pieces and arrows against the offence's table start (setup step 5)
        from .computer import place_defence
        o_sq = [B.parse_sq(q) for q in TABLE_O]
        build = lambda xq, ar: game_state(off, dfn, TABLE_O, [B.sq(q) for q in xq], list(ar), check=False)
        xs, arrows, perm = place_defence(pols['X'], o_sq, 0, build)
        s = build(xs, arrows)
    shot = None
    post = dict(attempted=0, completed=0)
    picks = 0
    entry = None                                         # a post entry in the air: the receiver
    for _ in range(300):
        if s.stage == 'over':
            break
        side = 'O' if (s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play')) else 'X'
        a = pols[side].choose(s)
        node = apply(s, a)
        nxt = sample(node, rng)[0] if isinstance(node, ChanceNode) else node
        if a.side == 'O' and a.kind == 'pass' and B.zone(s.o[a.target]) == 'K':
            post['attempted'] += 1                       # a pass to a receiver in the paint: a post entry
            entry = a.target
        if a.kind == 'intercept' and nxt.tos > s.tos:
            picks += 1                                   # an interception won
        if entry is not None and not getattr(nxt, 'pending', None) and a.kind != 'pass':
            if nxt.ball == entry and nxt.tos == s.tos:
                post['completed'] += 1
            entry = None
        if a.side == 'O' and a.kind in ('shot', 'forced_shot'):
            shot = dict(shooter=a.piece + 1, type=a.shot or (nxt.shot if hasattr(nxt, 'shot') else ''), square=B.sq(s.o[a.piece]),
                        clock=s.clock, forced=a.kind == 'forced_shot')
        s = nxt
    r = score(s) if s.stage == 'over' else None
    res = s.result if s.stage == 'over' else None
    return dict(seed=seed, points=float(r.total) if r else None, shot=shot, post=post, picks=picks,
                result=dict(kind=getattr(res, 'kind', None)) if res is not None else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--o', default='allstar'); ap.add_argument('--x', default='allstar')
    ap.add_argument('--off', default='Five Out'); ap.add_argument('--dfn', default='High-Low')
    ap.add_argument('--n', type=int, default=20); ap.add_argument('--budget', type=float, default=2.0)
    ap.add_argument('--store', default=None); ap.add_argument('--place', action='store_true', help='the computer defence places its pieces first')
    args = ap.parse_args()
    rows = []
    t0 = time.time()
    for seed in range(1, args.n + 1):
        rows.append(play(args.o, args.x, args.off, args.dfn, seed, args.budget, args.place))
    ends = Counter(); pts = defaultdict(float); o2_three = 0
    for r in rows:
        sh = r['shot']
        key = f"O{sh['shooter']} {sh['type']}" if sh else (r['result']['kind'] if r['result'] else 'none')
        ends[key] += 1
        pts[key] += r['points'] or 0
        if sh and sh['shooter'] == 2 and sh['type'] == 'three':
            o2_three += 1
    n = len(rows)
    print(f"{args.off} (offence {args.o}) v {args.dfn} (defence {args.x}{', computer placement' if args.place else ', table start'}): {n} possessions, {round(time.time() - t0)} s")
    print(f"possessions ending with an O2 three: {o2_three}/{n} = {100 * o2_three / n:.0f}%")
    tot = sum(r['points'] or 0 for r in rows)
    print(f"points: {tot:.0f} total, {tot / n:.1f} a possession")
    pa = sum(r['post']['attempted'] for r in rows); pc = sum(r['post']['completed'] for r in rows)
    print(f"post entries: {pa} attempted, {pc} completed")
    print(f"interceptions: {sum(r['picks'] for r in rows)} in {n} possessions = {100 * sum(r['picks'] for r in rows) / n:.0f} per 100")
    for k, c in ends.most_common():
        print(f"  {k}: {c} ({100 * c / n:.0f}%), {pts[k]:.0f} points ({100 * pts[k] / max(1, tot):.0f}% of the points)")
    if args.store:
        with open(args.store, 'w') as f:
            json.dump(dict(args=vars(args), rows=rows), f, indent=1, default=str)


if __name__ == '__main__':
    main()
