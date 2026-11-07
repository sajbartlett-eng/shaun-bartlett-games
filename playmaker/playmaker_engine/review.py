"""Replay a playtest log, and show where the solver disagreed with each human decision.

The solver's values are estimates from a short search, so a gap is "where the solver disagreed",
not a mistake.
"""
import json
import re

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


def log_rules(setup):
    """The rules a log was played with: its recorded settings, or (a log from before the step 3i follow-up
    rulings) the old screens, single arrow, arrow-line drives and interceptor left on the line."""
    from . import rules_config as RC
    rec = setup.get('rules')
    if not rec:
        return RC.with_rules(**RC.LEGACY_3I)
    # logs from before the OQ-72 ruling (no intercept_rule), before the turnover-cost ruling, or before the
    # rulebook revision (no on_line_tolerance / lane_jump_keeps_facing)
    return RC.with_rules(**{'intercept_rule': 'approach', 'turnover_cost': 'legacy', **RC.PRE_RULEBOOK, **rec})


def _start(setup, possession, o_sq=TABLE_O, x_sq=TABLE_X, arrows=TABLE_ARROWS, ball=0):
    rules = log_rules(setup)
    if setup.get('scenario'):
        return scenario_state(setup['scenario'], rules=rules)
    off, dfn = setup['teams'] if possession == 1 else setup['teams'][::-1]
    return game_state(off, dfn, list(o_sq), list(x_sq), list(arrows), ball=ball, rules=rules)


def _same(state, logged):
    """A replayed state matches its log entry (logs written before OQ-52 have no per-player Quick Step part)."""
    enc = state.encode()
    if enc == logged:
        return True
    return '|q' not in logged and re.sub(r'\|q[0-9a-f]{4}', '', enc) == logged


def register_custom(setup):
    """Custom lineups named in a log's setup record (step 3d), so the log replays anywhere."""
    from .cards import register_team
    for name, keys in (setup.get('custom') or {}).items():
        if register_team(name, keys) != name:
            raise ValueError(f'custom team {name} clashes with another lineup of that name')


def replay(records, on_decision=None):
    """Rebuild every state from the log. Rolls are replayed from the logged outcomes.
    Returns a list of (possession, final state)."""
    setup = next(r for r in records if r['type'] == 'setup')
    register_custom(setup)
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
                if r.get('start') and not _same(state, r['start']):
                    raise ValueError('placement replay diverged')
        elif r['type'] == 'possession':
            finals.append((possession, state))
            possession = r['possession']
            state = _start(setup, possession)
            undo = []
        elif r['type'] == 'undo':
            state = undo.pop()
            if not _same(state, r['state']):
                raise ValueError('undo replay diverged')
        elif r['type'] == 'timer' and r.get('event') == 'forfeit':
            from .timer import timer_forfeit
            node, _ = timer_forfeit(state)
            j = i + 1
            while isinstance(node, ChanceNode) and j < len(records) and records[j]['type'] == 'roll':
                node = force(node, records[j]['picked'])
                j += 1
            state = node
            undo = []
            i = j - 1
            if not _same(state, r['after']):
                raise ValueError(f'timer forfeit replay diverged: {state.encode()} != {r["after"]}')
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
            if not _same(state, r['after']):
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

    recs = read(path)
    replay(recs, decide)
    out(f'Review of {path} ({len(rows)} human decisions; solver at {budget_s:g} s per position).')
    for t in timer_facts(recs):
        out('  ' + t)
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


def best_look(state):
    """The best ▲ look the board offers at this moment: a ▲ shooter's shot value against the contester eligible now
    (an adjacent defender, the one giving the lowest value; none = contest 0). None when there is no ▲ shooter in
    a shot zone. The same arithmetic board_advantages uses over a whole log."""
    from . import board as B
    from . import rules_config as RC
    from .scoring import contest_rating
    if state.stage not in ('play', 'reaction') or not B.on_board(state.o[state.ball]):
        return None
    best = None
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
            if best is None or v > best['value']:
                best = dict(o=i + 1, square=B.sq(p), shot=t, rating=card.shot(t), contest=c,
                            contester=(j + 1) if j is not None else None, value=v, clock=state.clock, phase=state.phase,
                            text=f'O{i + 1} {t} {card.shot(t)}▲ on {B.sq(p)} v '
                                 + (f'X{j + 1} contest {c}' if j is not None else 'no eligible contester')
                                 + f': {pts} × ({card.shot(t)} − {c}) = {v}')
    return best


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


# ---- "The report in play" (step 3d): facts from the log, no solver values -------------------------

RIM, MIDS = ('layup', 'dunk'), ('mid', 'long')


def play_events(records):
    """Every counted event in the log, per possession, with the teams on each end. Undone actions are
    dropped. Returns (events, possessions) where possessions maps n -> (offence team, defence team)."""
    setup = next(r for r in records if r['type'] == 'setup')
    register_custom(setup)
    if setup.get('scenario'):
        st = scenario_state(setup['scenario'])
        poss = {1: (st.ctx.off_team, st.ctx.def_team)}
    else:
        a, b = setup['teams']
        poss = {1: (a, b), 2: (b, a)}
    states = iter(replay_states(records))
    ev, stack = [], []
    p = 1
    i = 0
    while i < len(records):
        r = records[i]
        if r['type'] == 'possession':
            p = r['possession']
        elif r['type'] == 'undo':
            if stack:
                n = stack.pop()
                del ev[len(ev) - n:]
        elif r['type'] == 'end':
            if r['score'].get('free_throws'):
                shooters = [e for e in ev if e['poss'] == p and e['kind'] in ('shot', 'steal')]
                o = shooters[-1]['o'] if shooters else None
                ev.append(dict(poss=p, kind='free_throws', o=o, x=None))
                stack = []
        elif r['type'] == 'action':
            state, act, _ = next(states)
            rolls = []
            j = i + 1
            while j < len(records) and records[j]['type'] == 'roll':
                rolls.append(records[j]['picked'])
                j += 1
            k, d = act.kind, None
            if k in ('qs', 'sprint') and act.side == 'O':
                d = dict(kind='move_fast', o=act.piece, x=None)
            elif k == 'dribble':
                d = dict(kind='dribble', o=act.piece, x=act.target, beat='success' in rolls)
            elif k == 'pass':
                d = dict(kind='pass', o=act.piece, x=None, picked=False)
            elif k == 'intercept':
                d = dict(kind='intercept', o=state.pending[0] if state.pending else None, x=act.piece,
                         picked='failure' in rolls)
                for e in reversed(ev):
                    if e['kind'] == 'pass' and e['poss'] == p:
                        e['picked'] = e['picked'] or d['picked']
                        break
            elif k == 'screen':
                d = dict(kind='screen', o=act.piece, x=None)
            elif k == 'challenge':
                d = dict(kind='challenge', o=act.target, x=act.piece)
            elif k == 'steal':
                d = dict(kind='steal', o=state.ball, x=act.piece, stolen='stolen' in rolls, foul='foul' in rolls)
            elif k in ('shot', 'forced_shot'):
                d = dict(kind='shot', o=act.piece, x=None, shot=act.shot, foul=False)
            elif k == 'contest':
                for e in reversed(ev):
                    if e['kind'] == 'shot' and e['poss'] == p:
                        e['x'] = act.piece if act.piece >= 0 else None
                        e['foul'] = 'foul' in rolls
                        break
            n = 0
            if d:
                d['poss'] = p
                ev.append(d)
                n = 1
            stack = [] if rolls else stack + [n]
            i = j - 1
        i += 1
    return ev, poss


def _plural(n, word, many=None):
    return f'{n} {word if n == 1 else (many or word + "s")}'


def _player_count(pid, side, n, evs):
    """(tested?, text) for one player phrase. evs are the events of the possessions where this player
    was on that end; n is the player's index (0-4)."""
    if side == 'off':
        mine = [e for e in evs if e['o'] == n]
        shots = lambda kinds: [e for e in mine if e['kind'] == 'shot' and e['shot'] in kinds]
        def shot_text(es, word):
            if not es:
                return 0, ''
            by = sorted({f"X{e['x'] + 1}" for e in es if e['x'] is not None})
            open_n = sum(e['x'] is None for e in es)
            extra = [f'contest from {", ".join(by)}'] if by else []
            if open_n:
                extra.append(f'{open_n} uncontested')
            return len(es), f'{_plural(len(es), word)} taken' + (', ' + ', '.join(extra) if extra else '')
        if pid == 'quick_step':
            c = sum(e['kind'] == 'move_fast' for e in mine)
            return c, f'{_plural(c, "quick step or sprint", "quick steps or sprints")}'
        if pid == 'dribble':
            ds = [e for e in mine if e['kind'] == 'dribble']
            st = [e for e in evs if e['kind'] == 'steal' and e['o'] == n]
            c = len(ds) + len(st)
            return c, (f'{_plural(len(ds), "dribble")}, {sum(e["beat"] for e in ds)} beat the defender; '
                       f'{_plural(len(st), "steal try", "steal tries")}, {sum(e["stolen"] for e in st)} stolen')
        if pid == 'pass':
            ps = [e for e in mine if e['kind'] == 'pass']
            return len(ps), f'{_plural(len(ps), "pass", "passes")}, {sum(e["picked"] for e in ps)} intercepted'
        if pid == 'screen':
            c = sum(e['kind'] == 'screen' for e in mine)
            return c, _plural(c, 'screen')
        if pid == 'rim':
            return shot_text(shots(RIM), 'rim shot')
        if pid == 'post':
            return shot_text(shots(('post',)), 'post shot')
        if pid == 'floater':
            return shot_text(shots(('floater',)), 'floater')
        if pid == 'pullup':
            return shot_text(shots(MIDS), 'pull-up')
        if pid == 'three':
            return shot_text(shots(('three',)), 'three')
        if pid == 'free_throw':
            c = sum(e['kind'] == 'free_throws' for e in mine)
            return c, f'went to the line {_plural(c, "time")}'
    else:
        mine = [e for e in evs if e['x'] == n]
        if pid == 'agility':
            ds = [e for e in evs if e['kind'] == 'dribble' and e['x'] == n]
            return len(ds), f'dribbled at {_plural(len(ds), "time")}, beaten {sum(e["beat"] for e in ds)}'
        if pid == 'intercept':
            it = [e for e in mine if e['kind'] == 'intercept']
            return len(it), f'{_plural(len(it), "intercept try", "intercept tries")}, {sum(e["picked"] for e in it)} picked off'
        if pid == 'challenge':
            c = sum(e['kind'] == 'challenge' for e in mine)
            return c, _plural(c, 'screen challenge')
        if pid == 'steal':
            st = [e for e in mine if e['kind'] == 'steal']
            return len(st), f'{_plural(len(st), "steal try", "steal tries")}, {sum(e["stolen"] for e in st)} stolen'
        if pid == 'rim_d':
            c = sum(e['kind'] == 'shot' and e['shot'] in RIM for e in mine)
            return c, f'contested {_plural(c, "rim shot")}'
        if pid == 'post_d':
            c = sum(e['kind'] == 'shot' and e['shot'] == 'post' for e in mine)
            return c, f'contested {_plural(c, "post shot")}'
        if pid == 'closeout':
            c = sum(e['kind'] == 'shot' and e['shot'] in ('three', 'mid', 'long') for e in mine)
            return c, f'contested {_plural(c, "jump shot")}'
        if pid == 'foul':
            fs = sum(e.get('foul', False) for e in mine)
            tries = sum(e['kind'] in ('shot', 'steal') for e in mine)
            return tries, f'{_plural(fs, "foul")} on {_plural(tries, "contest or steal try", "contests and steal tries")}'
    return 0, ''


def _team_count(lid, off_evs, def_evs):
    """(tested?, text) for one team line. off_evs: this team on offence; def_evs: this team defending."""
    shots = lambda es, kinds: [e for e in es if e['kind'] == 'shot' and e['shot'] in kinds]
    if lid in ('fast', 'slow'):
        c = sum(e['kind'] == 'move_fast' for e in off_evs)
        return c, _plural(c, 'quick step or sprint', 'quick steps and sprints')
    if lid in ('built_to_shoot', 'spacing', 'no_spacing'):
        c = len(shots(off_evs, ('three',)))
        return c, f'{_plural(c, "three")} taken'
    if lid == 'moves_ball':
        ps = [e for e in off_evs if e['kind'] == 'pass']
        return len(ps), f'{_plural(len(ps), "pass", "passes")}, {sum(e["picked"] for e in ps)} intercepted'
    if lid in ('creators', 'no_creators', 'limited'):
        d = sum(e['kind'] == 'dribble' for e in off_evs)
        ps = sum(e['kind'] == 'pass' for e in off_evs)
        return d + ps, f'{_plural(d, "dribble")}, {_plural(ps, "pass", "passes")}'
    if lid == 'attacks_rim':
        c = len(shots(off_evs, RIM + ('post',)))
        return c, f'{_plural(c, "shot")} at the rim or in the post'
    if lid == 'inside_out':
        c = len(shots(off_evs, ('post',)))
        return c, f'{_plural(c, "post shot")}'
    if lid in ('paint', 'weak_interior'):
        c = len(shots(def_evs, RIM))
        return c, f'{_plural(c, "rim shot")} faced'
    if lid in ('perimeter', 'leaks'):
        ds = [e for e in def_evs if e['kind'] == 'dribble']
        return len(ds), f'dribbled at {_plural(len(ds), "time")}, beaten {sum(e["beat"] for e in ds)}'
    if lid == 'open_threes':
        c = len(shots(def_evs, ('three',)))
        return c, f'{_plural(c, "three")} taken against them'
    if lid == 'lanes':
        it = [e for e in def_evs if e['kind'] == 'intercept']
        return len(it), f'{_plural(len(it), "intercept try", "intercept tries")}, {sum(e["picked"] for e in it)} picked off'
    if lid == 'fouls':
        fs = sum(e.get('foul', False) for e in def_evs)
        tries = sum(e['kind'] in ('shot', 'steal') and e['x'] is not None for e in def_evs)
        return tries, f'{_plural(fs, "foul")} on {_plural(tries, "contest or steal try", "contests and steal tries")}'
    if lid == 'line':
        c = sum(e['kind'] == 'free_throws' for e in off_evs)
        return c, f'went to the line {_plural(c, "time")}'
    return 0, ''


def report_in_play(records, rep):
    """For each scout line about either team, the plain counts from the log, or 'not tested'."""
    from .scouting import PHRASES
    ev, poss = play_events(records)
    out = []
    for t in rep.get('teams', []):
        name = t['name']
        on_off = [p for p, (a, _) in poss.items() if a == name]
        on_def = [p for p, (_, d) in poss.items() if d == name]
        off_evs = [e for e in ev if e['poss'] in on_off]
        def_evs = [e for e in ev if e['poss'] in on_def]
        items = []
        for line in t['lines']:
            c, text = _team_count(line['id'], off_evs, def_evs)
            items.append(dict(who=name, line=line['text'], tested=bool(c), text=text if c else 'not tested'))
        for pl in t['players']:
            n = pl['num'] - 1
            for side, evs, tag in (('off', off_evs, 'O'), ('def', def_evs, 'X')):
                for ph in pl[side]['strengths'] + pl[side]['weaknesses']:
                    c, text = _player_count(ph['id'], side, n, evs)
                    items.append(dict(who=f'{tag}{pl["num"]}', line=ph['text'], tested=bool(c),
                                      text=text if c else 'not tested'))
        out.append(dict(team=name, items=items))
    return out


# ---- the decision timer in the log (step 3d part C) -----------------------------------------------

def timer_facts(records):
    """Every timer forfeit as a plain fact, no verdict."""
    side = {'O': 'offence', 'X': 'defence'}
    out = []
    for r in records:
        if r['type'] == 'timer' and r.get('event') == 'forfeit':
            what = {'token': 'lost 1 token to the timer', 'token_end': 'lost its last token to the timer (turn over)',
                    'end_turn': 'ran out of time with no tokens (turn over)',
                    'default': "ran out of time on a token-free choice (the default applied)"}[r['effect']]
            out.append(f"Possession {r.get('possession', 1)}: the {side[r['side']]} {what} in phase {r['phase']} "
                       f"(clock {r['clock']}).")
    return out


def _pct(xs, p):
    xs = sorted(xs)
    if not xs:
        return None
    k = (len(xs) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def timer_stats(paths=None, out=print, min_games=20):
    """Decision time (seconds, admin grace excluded) at the 50th, 75th and 90th percentiles, by action type
    and by side, over human decisions in real games. Scripted test games (every decision under a quarter
    of a second) are left out."""
    import glob
    import os
    paths = paths or sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'playtest_logs', '*.jsonl')))
    rows, games = [], 0
    for p in paths:
        try:
            recs = read(p)
        except (OSError, ValueError):
            continue
        acts = [r for r in recs if r['type'] == 'action' and r.get('actor') == 'human' and 'seconds' in r]
        secs = [max(0.0, r['seconds'] - r.get('grace_s', 0)) for r in acts]
        if not acts or _pct(secs, 50) < 0.25:
            continue
        games += 1
        rows += [(r['action']['kind'], r['action']['side'], s) for r, s in zip(acts, secs)]
    out(f'Decision times from {games} real game(s), {len(rows)} human decisions (seconds; admin grace excluded).')
    if games < min_games:
        out(f'Not enough data yet: about {min_games} logged games are needed for presets you can trust '
            f'({max(0, min_games - games)} more).')
    def line(label, xs):
        if xs:
            out(f'  {label:<18} n={len(xs):<5} p50 {_pct(xs, 50):6.1f}  p75 {_pct(xs, 75):6.1f}  p90 {_pct(xs, 90):6.1f}')
    line('all', [s for _, _, s in rows])
    for side in ('O', 'X'):
        line('offence' if side == 'O' else 'defence', [s for _, sd, s in rows if sd == side])
    for kind in sorted({k for k, _, _ in rows}):
        line(kind, [s for k, _, s in rows if k == kind])
    return dict(games=games, decisions=len(rows))


# ---- "About the computer" (step 3e): plain facts from the log, after the game ------------------

def computer_facts(records):
    """Name each computer side's level, the habits drawn and the concepts switched off, and the
    offence's plan and targets, from the log."""
    from .computer import LEVELS
    setup = next((r for r in records if r['type'] == 'setup'), {})
    comp = setup.get('computer') or {}
    out = []
    words, cwords = LEVELS['habit_words'], LEVELS['concept_words']
    for side in ('O', 'X'):
        d = comp.get(side)
        if not d:
            continue
        who = 'offence' if side == 'O' else 'defence'
        line = f"The computer {who} played at {d['name']} level."
        bits = [words.get(h, h) for h in d.get('habits', [])]
        if bits:
            line += f" This {who} " + '; it '.join(bits) + '.'
        off = [cwords.get(k, k) for k in d.get('concepts_off', [])]
        if off:
            line += f" It " + '; it '.join(off) + '.'
        out.append(line)
        if side == 'O':
            plans = [r for r in records if r['type'] == 'computer' and r.get('side') == 'O']
            for r in plans:
                if r.get('event') == 'plan' and r.get('targets'):
                    t = r['targets']
                    tx = ', then '.join(f"O{x['o'] + 1} ({x['shot']})" for x in t)
                    out.append(f"Possession {r.get('possession', 1)}: its targets were {tx}.")
                elif r.get('event') == 'plan_type':                  # logs from before step 3g
                    out.append(f"It worked a {r['plan']} plan.")
                elif r.get('event') == 'play':                       # step 3g: the advantage plays it ran
                    line = r['text'] + '.' + (f" {r['advantage']}." if r.get('advantage') else '')
                    out.append(line)
                elif r.get('event') in ('advantage_moved', 'advantage_gone', 'finish'):
                    out.append(r['text'] + '.')
                elif r.get('event') in ('goal_finish',):              # step 3i: the goal and its chain
                    out.append(r['text'])
                elif r.get('event') in ('goal_reassess', 'vcut'):
                    out.append(r['text'] + '.')
                elif r.get('event') == 'replan':
                    out.append(f"It changed plan: {r['why']}.")
        else:
            objs = [r for r in records if r['type'] == 'computer' and r.get('side') == 'X' and r.get('event') == 'objectives']
            for r in objs[:4]:
                out.append(r['text'] + '.')
            if len(objs) > 4:
                out.append(f'(The defence re-ranked its objectives {len(objs) - 4} more times.)')
    return out
