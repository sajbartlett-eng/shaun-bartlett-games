"""Replay a playtest log, and show where the solver disagreed with each human decision.

The solver's values are estimates from a short search, so a gap is "where the solver disagreed",
not a mistake.
"""
import json

from .actions import Action
from .resolve import apply, ChanceNode, force
from .scenarios import scenario_state, game_state

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
TABLE_ARROWS = ['N', 'NE', 'NW', 'N', 'N']


def read(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def _action(d):
    dest = d.get('dest')
    return Action(d['kind'], d['side'], int(d.get('piece', -1)), tuple(dest) if dest is not None else None,
                  int(d.get('arrow', -1)), int(d.get('target', -1)), d.get('shot', '') or '')


def _start(setup, possession):
    if setup.get('scenario'):
        return scenario_state(setup['scenario'])
    off, dfn = setup['teams'] if possession == 1 else setup['teams'][::-1]
    return game_state(off, dfn, TABLE_O, TABLE_X, TABLE_ARROWS, ball=0)


def replay(records, on_decision=None):
    """Rebuild every state from the log. Rolls are replayed from the logged outcomes.
    Returns a list of (possession, final state)."""
    setup = next(r for r in records if r['type'] == 'setup')
    possession = 1
    state = _start(setup, 1)
    finals = []
    undo = []                         # states before each action since the last roll (as the server keeps)
    i = 0
    while i < len(records):
        r = records[i]
        if r['type'] == 'possession':
            finals.append((possession, state))
            possession = r['possession']
            state = _start(setup, possession)
            undo = []
        elif r['type'] == 'undo':
            state = undo.pop()
            if state.encode() != r['state']:
                raise ValueError('undo replay diverged')
        elif r['type'] == 'action':
            a = _action(r['action'])
            if on_decision and r.get('actor') == 'human':
                on_decision(state, a, r)
            before = state
            node = apply(state, a)
            j = i + 1
            rolled = isinstance(node, ChanceNode)
            while isinstance(node, ChanceNode) and j < len(records) and records[j]['type'] == 'roll':
                node = force(node, records[j]['picked'])
                j += 1
            if isinstance(node, ChanceNode):
                raise ValueError(f'log is missing a roll after {a}')
            undo = [] if rolled else undo + [before]
            state = node
            i = j - 1
            if state.encode() != r['after']:
                raise ValueError(f'replay diverged after {a}: {state.encode()} != {r["after"]}')
        i += 1
    finals.append((possession, state))
    return finals


def review(path, budget_s=5.0, out=print):
    """Print each human decision with the solver's preferred action and the gap in value."""
    from .solver import Searcher, apply_play, expected
    from .solver_config import with_config
    cfg = with_config(eval_turns=1)
    rows = []

    def decide(state, a, rec):
        if a.kind in ('target', 'pick', 'end_turn') and state.stage != 'reaction':
            return
        se = Searcher(cfg)
        res = se.search(state, budget_s=budget_s)
        e = res['entry']
        if e is None or not e.children:
            return
        maximise = state.side == 'O' and state.stage != 'reaction'
        best_p, best_v = (max if maximise else min)(e.children, key=lambda pv: pv[1][0].ev)
        chosen = [v for p, v in e.children if p.actions[0] == a]
        if chosen:
            cv = chosen[0][0].ev
        else:
            node = apply(state, a)
            cv = expected(node, se.ev)[0].ev
        gap = (best_v[0].ev - cv) if maximise else (cv - best_v[0].ev)
        rows.append(dict(possession=rec.get('possession'), clock=rec.get('clock'), side=state.side,
                         played=str(a), solver=best_p.text(), gap=round(gap, 2)))

    replay(read(path), decide)
    out(f'Review of {path} ({len(rows)} human decisions; solver at {budget_s:g} s per position).')
    out('Where the solver disagreed (its values are estimates, not verdicts):')
    for r in rows:
        mark = '' if r['gap'] <= 0.5 else f'   <- solver preferred: {r["solver"]} (+{r["gap"]:.1f} for the {"offence" if r["side"] == "O" else "defence"})'
        out(f'  poss {r["possession"]} clock {r["clock"]:>2} {r["side"]}: {r["played"]}{mark}')
    return rows
