"""Step 31, stage 2 (Shaun, 25 Nov 2026): the team's weight map and its centre. The Python engine's copy of engine.js
weightMap, weightBase and weightJSON; the two must agree on every board (tests/test_exam.py, check B2).

"The team's weight is a map of where a defender's presence saves the most points right now." Three layers, on the one
scale (docs/reference/GRAVITY_AND_SPACING_DESIGN.md, "The defence, part 1"):
  1. the points a contest saves: a look's worth with nobody on it, less its worth against the best answer a defender
     can give standing there (set, in front, his arrow on the shooter; the block where it pays, as a line in what the
     phase after it is worth; against a shooter in control the fake is a two-by-two mix, D-296, whose value is the
     hold's, so a block counts only against a rushed shooter). Whose contest (D-288): the best of the five for the
     team's map; each defender's own for his own base position (`own`).
  2. occupation: each zone cut into segments (D-287, data/segments.json, provisional); a segment no attacker can reach
     this phase carries nothing.
  3. the ball's reach: each look at the chance its man has the ball there in time, by the rules. Counted once, here.
One entry an attacker a segment (his heaviest look in it). The centre of gravity is where the entries balance; `lumps`
gives the weight itself, group by group. `left` is the weight with the cover it already faces taken off."""
import json
import os

from . import board as B, rules_config as RC

_SEG = {}
K0 = (0, 99, 99, 99, 99, 99)                 # the contest row "in front, his arrow on the shooter", set (decide.KINDS[0])
NEG = float('-inf')


def segments():
    """data/segments.json (one table, both engines): {'names': [...], 'of': {square: [segment indices]}}."""
    if not _SEG:
        g = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'segments.json')))
        names = g['order']
        idx = {n: i for i, n in enumerate(names)}
        of = {}
        for x in range(B.W):
            for y in range(1, B.H + 1):
                yy = int(g['behind'].get(str(y), y))
                row = g['rows'].get(str(yy))
                if row is None:
                    continue
                v = row[x]
                of[(x, y)] = [idx[n] for n in g['both'].get(v, [v])]
        _SEG.update(names=names, of=of)
    return _SEG


def _split(r, lk, d, flags_rushed):
    lines = []
    cv = r._vals2(lk, d, K0, K0, split=lines)
    return (cv or {}, lines) if (cv or lines) else None


def weight_map(s, cfg=None):
    """engine.js weightMap -> dict(looks, entries, left, centre, centre_left, lumps, lumps_left, B)."""
    from . import memo
    from .value import poss_parts
    if s.stage != 'play':
        return None
    base = s.with_(ball=s.pending[1], pending=None, approach=-1) if s.pending else s
    pp = poss_parts(base, cfg)
    if 'L' not in pp:
        return None

    def calc():
        seg = segments()
        r, L = pp['r'], pp['L']
        Bv = pp['before'][-2] if len(pp['before']) >= 2 else 0.0
        looks = []
        for i, o in enumerate(L):
            types, opens = o['lk'].types, o['open']
            fake = not o['rushed']
            op = max(opens)
            best, by, cont = float('inf'), -1, [0.0] * 5
            for d in range(5):
                if not B.on_board(r.s.x[d]):
                    cont[d] = op
                    continue
                sv = _split(r, o['lk'], d, o['rushed'])
                v = op
                if sv:
                    cv, bl = sv
                    v = NEG
                    for t, ty in enumerate(types):
                        u = min(opens[t], cv[ty]) if ty in cv else opens[t]
                        if not fake:
                            for (bt, c0, c1) in bl:
                                if bt == t and c0 + c1 * Bv < u:
                                    u = c0 + c1 * Bv
                        if u > v:
                            v = u
                cont[d] = v
                if v < best - 1e-12:
                    best, by = v, d
            stands = pp['worth0'][i] - o['adj']
            own = [round(o['r'] * max(0.0, min(op, stands) - v), 6) for v in cont]
            looks.append(dict(i=i, a=o['a'], c=o['c'], q0=o['q0'], r=o['r'], open=op, contested=best, by=by, saving=op - best,
                              weight=o['r'] * max(0.0, op - best), left=o['r'] * max(0.0, min(op, stands) - best), stands=stands, own=own))

        def pick(field):
            ent = {}
            for k in looks:
                sg = seg['of'].get(k['c'])
                if not sg or not k[field] > 1e-9:
                    continue
                for g in sg:
                    key = k['a'] * 32 + g
                    cur = ent.get(key)
                    if cur is None or k[field] > cur[field] + 1e-9 or (abs(k[field] - cur[field]) <= 1e-9 and k['c'] < cur['c']):
                        ent[key] = k
            return ent

        def balance(ent, field):
            sw = sx = sy = 0.0
            seen = set()
            for k in ent.values():
                if (k['a'], k['c']) in seen:
                    continue
                seen.add((k['a'], k['c']))
                sw += k[field]
                sx += k[field] * k['c'][0]
                sy += k[field] * k['c'][1]
            return dict(total=sw, x=sx / sw, y=sy / sw) if sw > 0 else dict(total=0.0, x=RC.RIM[0], y=RC.RIM[1])

        def lumps_of(ent, field):
            uniq = {}
            for k in ent.values():
                uniq[(k['a'], k['c'])] = k
            items = sorted(uniq.values(), key=lambda k: (k['c'], k['a']))
            gid = list(range(len(items)))

            def find(i):
                while gid[i] != i:
                    i = gid[i]
                return i
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    if B.cheb(items[i]['c'], items[j]['c']) <= 2:
                        a, b = find(i), find(j)
                        if a != b:
                            gid[max(a, b)] = min(a, b)
            groups = {}
            for i, k in enumerate(items):
                g = find(i)
                o = groups.setdefault(g, dict(weight=0.0, x=0.0, y=0.0, top=k, n=0))
                o['weight'] += k[field]
                o['x'] += k[field] * k['c'][0]
                o['y'] += k[field] * k['c'][1]
                o['n'] += 1
                if k[field] > o['top'][field] + 1e-9:
                    o['top'] = k
            out = [dict(weight=o['weight'], x=o['x'] / o['weight'], y=o['y'] / o['weight'], top=o['top'], n=o['n']) for o in groups.values()]
            out.sort(key=lambda o: (-o['weight'], o['top']['c']))
            return out
        ent, ent_l = pick('weight'), pick('left')
        return dict(looks=looks, entries=ent, left=ent_l, centre=balance(ent, 'weight'), centre_left=balance(ent_l, 'left'),
                    lumps=lumps_of(ent, 'weight'), lumps_left=lumps_of(ent_l, 'left'), B=Bv, seg=seg)
    return memo.get('map', ('WM', id(base.ctx), base, id(cfg)), calc)


_BASE = {}


def weight_base(s):
    """engine.js weightBase: layer 1 alone, from the cards and the empty board (worked out once a game)."""
    from .decide import Read, Look, card_shot, shot_zone
    ctx = s.ctx
    hit = _BASE.get(id(ctx))
    if hit is not None and hit[0] is ctx:
        return hit[1]
    seg = segments()
    r = Read(s.with_(stage='play', pending=None))
    no_rim = RC.rim_shot_barred(ctx.rules)
    ent = {}
    for x in range(B.W):
        for y in range(1, B.H + 1):
            c = (x, y)
            z = shot_zone(ctx, c)
            if z not in RC.ZONE_POINTS or (no_rim and c == RC.RIM) or c not in seg['of']:
                continue
            types, pts = RC.ZONE_SHOTS[z], RC.worth_now(ctx, z)
            for a in range(5):
                lk = Look(a, c, 'later', 1.0, False)
                lk.types = types
                lk.rushed = False
                opens = [pts * card_shot(ctx, ctx.off[a], t, c) for t in types]
                op = max(opens)
                best = op
                for d in range(5):
                    cv = r._vals2(lk, d, K0, K0, split=[])
                    if not cv:
                        continue
                    v = max((min(opens[t], cv[ty]) if ty in cv else opens[t]) for t, ty in enumerate(types))
                    if v < best:
                        best = v
                k = dict(a=a, c=c, weight=op - best, open=op, contested=best)
                if not k['weight'] > 1e-9:
                    continue
                for g in seg['of'][c]:
                    key = a * 32 + g
                    cur = ent.get(key)
                    if cur is None or k['weight'] > cur['weight'] + 1e-9 or (abs(k['weight'] - cur['weight']) <= 1e-9 and c < cur['c']):
                        ent[key] = k
    sw = sx = sy = 0.0
    seen = set()
    for k in ent.values():
        if (k['a'], k['c']) in seen:
            continue
        seen.add((k['a'], k['c']))
        sw += k['weight']
        sx += k['weight'] * k['c'][0]
        sy += k['weight'] * k['c'][1]
    out = dict(entries=ent, centre=dict(total=sw, x=sx / sw, y=sy / sw) if sw > 0 else dict(total=0.0, x=RC.RIM[0], y=RC.RIM[1]))
    if len(_BASE) > 8:
        _BASE.clear()
    _BASE[id(ctx)] = (ctx, out)
    return out


def weight_json(s, cfg=None):
    """engine.js weightJSON: the map for the view, the tools and the tests (the same numbers, the same rounding)."""
    w = weight_map(s, cfg)
    if w is None:
        return None
    seg = w['seg']

    def r2(v):
        import math
        return math.floor(v * 100 + 0.5) / 100 + 0.0          # (halves go up, as JavaScript's toFixed prints them)

    def xy(c):
        return dict(x=r2(c['x']), y=r2(c['y']), sq=B.sq((int(_round(c['x'])), int(_round(c['y'])))), total=r2(c['total']))

    def ents(entm):
        return [dict(a=k['a'], seg=seg['names'][key % 32], c=B.sq(k['c']), ball_at=B.sq(k['q0']), reach=round(k['r'], 4), open=r2(k['open']),
                     contested=r2(k['contested']), by=k['by'], saving=r2(k['saving']), weight=r2(k['weight']), left=r2(k['left']),
                     own=[r2(v) for v in k['own']]) for key, k in sorted(entm.items())]

    def lump(l):
        return dict(weight=r2(l['weight']), x=r2(l['x']), y=r2(l['y']), sq=B.sq((int(_round(l['x'])), int(_round(l['y'])))),
                    top=dict(a=l['top']['a'], c=B.sq(l['top']['c'])), entries=l['n'])
    wb = weight_base(s)
    return dict(centre=xy(w['centre']), centre_left=xy(w['centre_left']), base_centre=xy(wb['centre']), entries=ents(w['entries']),
                left=[e for e in ents(w['left']) if e['left'] > 0], lumps=[lump(l) for l in w['lumps']],
                lumps_left=[lump(l) for l in w['lumps_left']], playing_on=r2(w['B']),
                base=[dict(a=k['a'], seg=seg['names'][key % 32], c=B.sq(k['c']), open=r2(k['open']), contested=r2(k['contested']), weight=r2(k['weight']))
                      for key, k in sorted(wb['entries'].items())])


def _round(v):
    """JavaScript's Math.round (halves go up), so both engines name the same square."""
    import math
    return math.floor(v + 0.5)
