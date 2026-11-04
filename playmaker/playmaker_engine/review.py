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


def _start(setup, possession, o_sq=TABLE_O, x_sq=TABLE_X, arrows=TABLE_ARROWS, ball=0):
    if setup.get('scenario'):
        return scenario_state(setup['scenario'])
    off, dfn = setup['teams'] if possession == 1 else setup['teams'][::-1]
    return game_state(off, dfn, list(o_sq), list(x_sq), list(arrows), ball=ball)


def replay(records, on_decision=None):
    """Rebuild every state from the log. Rolls are replayed from the logged outcomes.
    Returns a list of (possession, final state)."""
    setup = next(r for r in records if r['type'] == 'setup')
    possession = 1
    state = _start(setup, 1)
    finals = []
    undo = []                         # states before each action since the last roll (as the server keeps)
    placed_o = None
    i = 0
    while i < len(records):
        r = records[i]
        if r['type'] == 'placement':
            if r['side'] == 'O':
                placed_o = (r['squares'], r['ball'])
            else:
                state = _start(setup, possession, placed_o[0], r['squares'], r['arrows'], placed_o[1])
                if r.get('start') and state.encode() != r['start']:
                    raise ValueError('placement replay diverged')
        elif r['type'] == 'possession':
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


# ---- post-game review helpers (step 3c) -------------------------------------------------------------

def replay_states(records):
    """Every decision state in the log, in order, with the action taken there."""
    out = []

    def grab(state, a, rec):
        out.append((state, a, rec))
    _replay_all(records, grab)
    return out


def _replay_all(records, fn):
    """Like replay(), but calls fn at every action (human and computer)."""
    orig = [dict(r) for r in records]
    for r in orig:
        if r['type'] == 'action':
            r['actor'] = 'human'
    replay(orig, on_decision=fn)


def board_advantages(records, k=3):
    """The biggest matchup advantages the board offered: a ▲ shooter's shot value against the contester
    eligible at that moment (an adjacent defender, the one giving the lowest value; none = contest 0),
    over every decision point. Returns the top k (distinct player, square and shot type), and whether
    the possession's shot used any of them."""
    from . import board as B
    from . import rules_config as RC
    from .scoring import contest_rating
    best = {}
    finals = []
    for state, a, rec in replay_states(records):
        if state.stage not in ('play', 'reaction'):
            continue
        for i, p in enumerate(state.o):
            if not B.on_board(p):
                continue
            z = B.zone(p)
            for t in RC.ZONE_SHOTS[z]:
                card = state.ctx.off[i]
                if card.bands['shot_' + t] != 'H':
                    continue
                pts = RC.ZONE_POINTS[z]
                opts = [(0, None)]
                for j, xp in enumerate(state.x):
                    if B.adjacent(xp, p):
                        opts.append((contest_rating(state.ctx.dfn[j], t, xp, p, state.ctx.rules), j))
                c, j = max(opts, key=lambda o: o[0])
                v = pts * (card.shot(t) - c)
                key = (rec.get('possession', 1), i, B.sq(p), t)
                if key not in best or v > best[key]['value']:
                    best[key] = dict(possession=key[0], o=i + 1, square=key[2], shot=t, rating=card.shot(t),
                                     contest=c, contester=(j + 1) if j is not None else None, value=v,
                                     clock=state.clock, phase=state.phase,
                                     text=f'O{i + 1} {t} {card.shot(t)}▲ on {key[2]} v '
                                          + (f'X{j + 1} contest {c}' if j is not None else 'no eligible contester')
                                          + f': {pts} × ({card.shot(t)} − {c}) = {v}')
    top = sorted(best.values(), key=lambda b: (-b['value'], b['o']))[:k]
    shots = [r for r in records if r['type'] == 'end']
    taken = []
    for r in records:
        if r['type'] == 'action' and r['action']['kind'] in ('shot', 'forced_shot'):
            taken.append((r.get('possession', 1), r['action']['piece'] + 1, r['action']['shot']))
    for b in top:
        b['used'] = (b['possession'], b['o'], b['shot']) in taken
    return top


def solver_disagreements(path_or_records, budget_s=1.0, k=3, max_decisions=12):
    """Key moments where the solver's preferred action differed most in value (estimates)."""
    import tempfile, os, json as _json
    recs = path_or_records if isinstance(path_or_records, list) else read(path_or_records)
    humans = [r for r in recs if r['type'] == 'action' and r.get('actor') == 'human']
    if len(humans) > max_decisions:              # keep the review quick: the first decisions of each side
        keep = set(id(r) for r in humans[:max_decisions])
        recs = [r if r['type'] != 'action' or r.get('actor') != 'human' or id(r) in keep else dict(r, actor='skip')
                for r in recs]
    with tempfile.NamedTemporaryFile('w', suffix='.jsonl', delete=False) as f:
        for r in recs:
            f.write(_json.dumps(r) + '\n')
        path = f.name
    try:
        rows = review(path, budget_s, out=lambda *a: None)
    finally:
        os.remove(path)
    rows = [r for r in rows if r['gap'] > 0.5]
    rows.sort(key=lambda r: -r['gap'])
    return [dict(r, label='estimate') for r in rows[:k]]
