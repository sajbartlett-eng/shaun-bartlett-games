"""Step 3m B7: the goal library becomes labels. Nothing here decides anything: a recogniser names completed sequences
for the review and the trainer, using the GOAL_LIBRARY descriptions as pattern descriptions (goal_library.json:
id, name, conditions). A sequence that created a dilemma or an uncovered threat and matches no label is logged as an
"unnamed action" with its replay (the states before and after).

events: one possession's decisions in order, [(state before, action, state after)].
"""
import json
import os

from . import board as B
from . import rules_config as RC

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = {g['id']: g for g in json.load(open(os.path.join(HERE, 'goal_library.json')))['offence']}


def _name(gid):
    return LIB[gid]['name'] if gid in LIB else gid


def _guard(s, i):
    """The defender nearest attacker i (who is guarding him on this board)."""
    return min(range(5), key=lambda j: (B.cheb(s.x[j], s.o[i]), j))


def _passes(events):
    return [(k, s, a, n) for k, (s, a, n) in enumerate(events) if a.kind == 'pass' and a.side == 'O']


def _caught(events, k):
    """Did the pass at index k arrive (the receiver had the ball afterwards)?"""
    a = events[k][1]
    for s, b, n in events[k + 1:k + 6]:
        if n.stage == 'over' or n.ball == a.target:
            return n.ball == a.target or (n.result is not None and n.result.shooter == a.target)
    return False


def recognise(events):
    """Labels for one possession: [dict(id, label, start, end, who, text)]."""
    out = []

    def add(gid, start, end, who, text):
        out.append(dict(id=gid, label=_name(gid), start=start, end=end, who=who, text=text))
    for k, (s, a, n) in enumerate(events):
        if a.side != 'O':
            continue
        if a.kind == 'screen':
            S = a.piece
            t = B.add(s.o[S], B.DIRS[a.target])
            j = next((j for j, xp in enumerate(s.x) if xp == t or B.adjacent(xp, t)), None)
            ball_d = _guard(s, s.ball)
            for m in range(k + 1, min(len(events), k + 9)):
                s2, b, n2 = events[m]
                if b.side != 'O':
                    continue
                if j == ball_d and b.kind in ('move', 'qs', 'sprint') and b.piece == S and \
                        B.dist_rim(b.dest) < B.dist_rim(s2.o[S]):
                    add('D1', k, m, [S, s.ball], f'O{S + 1} screens X{j + 1} for O{s.ball + 1} and rolls')
                    break
                if j == ball_d and b.kind == 'pass' and b.target == S and B.zone(s2.o[S]) == '3':
                    add('D2', k, m, [S, s.ball], f'O{S + 1} screens for O{s.ball + 1} and pops')
                    break
                if j is not None and j != ball_d and b.kind in ('move', 'qs', 'sprint') and b.piece != S and \
                        _guard(s, b.piece) == j:
                    add('E2', k, m, [S, b.piece], f'O{S + 1} screens X{j + 1} for O{b.piece + 1}')
                    break
        if a.kind == 'pass':
            p, r = a.piece, a.target
            if not _caught(events, k):
                continue
            if B.cheb(s.o[p], s.o[r]) <= 1:
                nxt = next(((m, b) for m, (_, b, _) in enumerate(events[k + 1:k + 6], start=k + 1)
                            if b.side == 'O' and b.piece == r), None)
                if nxt and nxt[1].kind in ('move', 'qs', 'sprint', 'dribble', 'shot'):
                    add('D7', k, nxt[0], [p, r], f'O{p + 1} hands off to O{r + 1}')
            if B.zone(s.o[r]) == 'K' and any(B.adjacent(xp, s.o[r]) for xp in s.x):
                add('A1', k, k, [p, r], f'O{r + 1} in the post on X{_guard(s, r) + 1}')
                if B.zone(s.o[p]) in ('M', '.') and s.o[p][1] >= 5 and B.zone(s.o[p]) != '3':
                    add('A2', k, k, [p, r], f'high-low: O{p + 1} to O{r + 1}')
            if abs(s.o[p][0] - s.o[r][0]) >= 10:
                add('C4', k, k, [p, r], f'skip to O{r + 1}')
            # drive and kick: the passer moved toward the rim with the ball just before, the receiver on a three
            prev = [(m, b) for m, (_, b, _) in enumerate(events[max(0, k - 3):k], start=max(0, k - 3))
                    if b.side == 'O' and b.piece == p and b.kind in ('move', 'qs', 'sprint', 'dribble')]
            if prev and B.zone(s.o[r]) == '3':
                m0 = prev[0][0]
                if B.dist_rim(events[m0][0].o[p]) - B.dist_rim(s.o[p]) >= 2 or prev[0][1].kind == 'dribble':
                    add('C3', m0, k, [p, r], f'O{p + 1} drives and kicks')
            # backdoor: the receiver cut toward the rim behind his defender just before the catch
            cut = [(m, b) for m, (s0, b, _) in enumerate(events[max(0, k - 4):k], start=max(0, k - 4))
                   if b.side == 'O' and b.piece == r and b.kind in ('move', 'qs', 'sprint')]
            if cut:
                m0, b0 = cut[0]
                s0 = events[m0][0]
                g = _guard(s0, r)
                was_denied = B.cheb(s0.x[g], s0.o[s0.ball]) < B.cheb(s0.o[r], s0.o[s0.ball])
                if was_denied and B.dist_rim(s0.o[r]) - B.dist_rim(b0.dest) >= 2:
                    add('B3', m0, k, [r], f'O{r + 1} cuts backdoor on X{g + 1}')
            # give and go: p passed to r earlier in the possession, moved to the rim, gets it back
            for m in range(max(0, k - 6), k):
                s1, b1, _ = events[m]
                if b1.kind == 'pass' and b1.piece == r and b1.target == p:
                    moved = any(b.piece == p and b.side == 'O' and b.kind in ('move', 'qs', 'sprint')
                                and B.dist_rim(b.dest) < B.dist_rim(s_.o[p]) for s_, b, _ in events[m + 1:k])
                    if moved:
                        add('B6', m, k, [r, p], f'O{r + 1} gives and goes with O{p + 1}')
                    break
        if a.kind == 'dribble':
            c = s.ball
            if all(B.cheb(s.o[i], s.o[c]) > 3 for i in range(5) if i != c):
                add('A3', k, k, [c], f'O{c + 1} isolates X{a.target + 1}')
        if a.kind == 'shot':
            c = s.ball
            if B.zone(s.o[c]) == '3':
                caught_here = any(b.kind == 'pass' and b.target == c for _, b, _ in events[max(0, k - 3):k]) and \
                    not any(b.side == 'O' and b.piece == c and b.kind in ('move', 'qs', 'sprint') for _, b, _ in events[max(0, k - 3):k])
                if caught_here:
                    add('A4', k, k, [c], f'O{c + 1} spots up for a three')
            left = sum(1 for p_ in s.o if p_[0] < B.W // 2)
            right = sum(1 for p_ in s.o if p_[0] > B.W // 2)
            if max(left, right) >= 4:
                add('C5', k, k, list(range(5)), f"overload the {'left' if left >= 4 else 'right'} side")
    out.sort(key=lambda d: (d['start'], d['id']))
    return out


def unnamed(events, labels, reads=None):
    """Offence turn groups that created a dilemma (a new overload) or a new uncovered threat (the best uncovered
    threat up by 3 or more) and that no label covers: 'unnamed action', with its replay (the states' encodings)."""
    from .decide import Read
    covered = set()
    for l in labels:
        covered.update(range(l['start'], l['end'] + 1))
    out = []
    k = 0
    while k < len(events):
        s, a, n = events[k]
        if a.side != 'O' or s.stage != 'play':
            k += 1
            continue
        m = k
        while m + 1 < len(events) and events[m + 1][1].side == 'O' and events[m + 1][0].turn_n > 0:
            m += 1
        after = events[m][2]
        if after.stage == 'over':
            k = m + 1
            continue
        try:
            rb, ra = Read(s), Read(after)
            new_ov = ra.overloads() and not rb.overloads()
            up = ra.cover()['value'] - rb.cover()['value']
        except Exception:
            k = m + 1
            continue
        if (new_ov or up >= 3) and not covered & set(range(k, m + 1)):
            out.append(dict(label='unnamed action', start=k, end=m, actions=[str(e[1]) for e in events[k:m + 1]],
                            gain=round(up, 1), dilemma=bool(new_ov), before=s.encode(), after=after.encode(),
                            text=('created a dilemma for X%d' % (ra.overloads()[0]['defender'] + 1)) if new_ov
                            else f'opened an uncovered threat (+{up:.1f})'))
        k = m + 1
    return out


def possession_events(records):
    """[(possession, [(state before, action, state after)])] from a log, by replaying it."""
    from .review import replay_states
    rows = replay_states(records)
    out, cur, poss = [], [], None
    for i, (st, a, rec) in enumerate(rows):
        p = rec.get('possession', 1)
        if poss is not None and p != poss:
            out.append((poss, cur))
            cur = []
        poss = p
        nxt = rows[i + 1][0] if i + 1 < len(rows) and rows[i + 1][2].get('possession', 1) == p else None
        if nxt is None:
            from .review import _same
            from .state import GameState
            nxt = st  # the last action's result: rebuilt below
            from .resolve import apply, ChanceNode
            node = apply(st, a)
            nxt = node if not isinstance(node, ChanceNode) else max(node.outcomes, key=lambda o: o[0])[2]
        cur.append((st, a, nxt))
    if cur:
        out.append((poss, cur))
    return out
