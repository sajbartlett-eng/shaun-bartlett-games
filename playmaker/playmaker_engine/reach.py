"""Step 12: the reach map (switch: eval.reach, off by default). For every player and every square: the fewest Move and
Quick Step uses to get there this phase, with what he has left; the fewest next phase, fresh; and the earliest turn he
can arrive (0: he is there; 1: his side's next turn, this phase; 2: next phase). It follows the movement rules exactly
(straight and diagonal steps, blocking pieces, screens, locks): the defenders' reach is solver.defender_reach, the
attackers' decide.attacker_reach(exact=True). The reading uses it (decide.Read with eval.reach on) for who can Contest
a shooter in time, who can step into a pass, and who can reach the squares on an attacker's path before he does."""
from functools import lru_cache

from . import board as B
from .decide import defender_map, attacker_reach, _geo_paths
from .resolve import new_phase


def _min_counts(free, fixed):
    out = dict(free)
    for q, arrs in fixed.items():
        n = min(arrs.values())
        if out.get(q, 99) > n:
            out[q] = n
    return out


def player_reach(s, side, i):
    """{square: fewest movement actions} for one player now (up to two of his side's actions)."""
    if side == 'X':
        return _min_counts(*defender_map(s, i, exact=True))
    return attacker_reach(s, i, exact=True)


def reach_map(s):
    """{(side, i): {square: (this phase, next phase fresh, earliest turn)}}."""
    fresh = new_phase(s, s.clock)
    out = {}
    for side in 'OX':
        for i in range(5):
            start = (s.o if side == 'O' else s.x)[i]
            cur, nxt = player_reach(s, side, i), player_reach(fresh, side, i)
            row = {}
            for q in set(cur) | set(nxt):
                a, b = cur.get(q), nxt.get(q)
                row[q] = (a, b, 0 if q == start else 1 if a is not None else 2 if b is not None else None)
            out[(side, i)] = row
    return out


@lru_cache(maxsize=200000)
def paths_to(start, c, qs, rules):
    """The movement paths (Move, Quick Step, Sprint geometry, every square on the board) from start that end on c."""
    out = []
    for p in B.move_paths(start, rules):
        if p[-1] == c and all(B.on_board(q) for q in p):
            out.append(tuple(p))
    for p in B.qs_paths(start, qs, rules):
        if p[-1] == c and all(B.on_board(q) for q in p):
            out.append(tuple(p))
    for _, p in B.sprint_paths(start, qs, rules):
        if p[-1] == c and all(B.on_board(q) for q in p):
            out.append(tuple(p))
    return tuple(out)


def blocks_path(q, start, c, qs, rules):
    """A defender standing on q blocks the attacker's way from start to c: q is c, or every path there crosses q."""
    if q == c:
        return True
    ps = paths_to(start, c, qs, rules)
    return bool(ps) and all(q in p[:-1] for p in ps)


def path_squares(start, c, qs, rules):
    return {q for p in paths_to(start, c, qs, rules) for q in p}
