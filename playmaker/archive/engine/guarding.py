"""Matchups (step 3i follow-up, OQ-67a): who guards whom, as a persistent record the computer keeps.

The rules have no assignment, so the computer keeps one. It is set when the possession starts (from the
placement: the cheapest one-to-one pairing of defenders to attackers by distance, man-to-man by number
on a tie) and changed only by an explicit decision:

  switch       two defenders each take the other's man by their own movement this turn: each is now
               nearer the other's man than his own, and at least one of them moved or turned
  replacement  a defender who is locked, or out of reach of his man (more than one movement away), is
               replaced by the teammate now next to that man, who hands over his own

A screen, a cut or a drive by the offence changes nothing by itself: a defender left behind by a screen
that doesn't force a switch is still guarding his man. The defence keeps its record from its own
decisions; the offence infers the same record from what it can see (squares and arrows), with the same
rules, so both see a switch when it happens.

  initial(state)                  -> m, where m[j] is the attacker defender j guards
  update(m, before, after)        -> m after the defence's turn from `before` to `after`
  guard_of(m, i)                  -> the defender guarding attacker i
"""
from itertools import permutations

from . import board as B

REACH = 3          # one Move: up to 3 straight


def initial(state):
    best = None
    for perm in permutations(range(5)):
        cost = sum(B.cheb(state.x[j], state.o[perm[j]]) for j in range(5) if B.on_board(state.o[perm[j]]))
        facing = -sum(1 for j in range(5) if state.arrows[j] == B.nearest_dir(state.x[j], state.o[perm[j]]))
        moved = sum(perm[j] != j for j in range(5))
        k = (cost, facing, moved, perm)
        if best is None or k < best:
            best = k
    return tuple(best[3])


def guard_of(m, i):
    return m.index(i) if m is not None and i in m else None


def _switch(m, j, k):
    m = list(m)
    m[j], m[k] = m[k], m[j]
    return tuple(m)


def update(m, before, after):
    """The record after the defence's turn (before: the board as the defence got it; after: as it left it)."""
    if m is None:
        return initial(after)
    moved = {j for j in range(5) if before.x[j] != after.x[j] or before.arrows[j] != after.arrows[j]}
    d = lambda j, i: B.cheb(after.x[j], after.o[i])
    for j in range(5):
        for k in range(j + 1, 5):
            a, b = m[j], m[k]
            if (j in moved or k in moved) and d(j, b) < d(j, a) and d(k, a) < d(k, b):
                m = _switch(m, j, k)
    for j in range(5):
        a = m[j]
        if not moved or not (after.locked('X', j) or d(j, a) > REACH):
            continue                                   # a replacement is the defence's call too: after it acts
        cover = [k for k in range(5) if k != j and B.adjacent(after.x[k], after.o[a]) and d(k, m[k]) >= d(k, a)]
        if cover:
            m = _switch(m, j, min(cover, key=lambda k: (d(k, a), k)))
    return m


def describe(m):
    return ', '.join(f'X{j + 1} on O{m[j] + 1}' for j in range(5))
