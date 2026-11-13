"""Step 18h: the sense-check set (D-162). A fixed set of positions whose answers are measured by playing each
candidate turn out by the rules with common dice. Stored in tools/sense_set/ so that any later step scores a
setting against it in minutes.

  python3 tools/sense_18h.py harvest [n]          positions from All-Star self-play (sense_set/sources/harvest.json)
  python3 tools/sense_18h.py build                the set's positions and named candidates -> sense_set/positions.json
  python3 tools/sense_18h.py play                 every candidate without an answer played out -> sense_set/answers.json
  python3 tools/sense_18h.py score <tag> [k=v..]  the computer's choice on each position under a setting, against the answers
  python3 tools/sense_18h.py floor                the reading's parts after each candidate (the floor shown)
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import step_18e as E18                                 # noqa: E402
L = E18.L

SET = os.path.join(HERE, 'sense_set')
RUN = os.path.join(ROOT, 'docs', 'runs', os.environ.get('SENSE_RUN', 'step18h'))
WORK = os.path.join(RUN, 'work')
E18.RUN, E18.WORK, L.WORK = RUN, WORK, WORK
# SENSE_ZONE=1 (step 18g): the set's positions replayed under rules.zone, with answers of their own (the answers
# under today's rules stay as they are). SENSE_ONLY: score only the positions whose name starts with one of these.
ZONE = os.environ.get('SENSE_ZONE') == '1'
ONLY = [x for x in os.environ.get('SENSE_ONLY', '').split('|') if x]
RULE = dict(zone=True) if ZONE else {}
# SENSE_FIBA=1 (step 18i): the positions replayed with three seconds, closely guarded and the FIBA fouled shot on, with
# answers of their own. Without it those three rules are held off, so the set's first answers keep their meaning.
# SENSE_FOULS='4,10' (D-175): the defence's team fouls and its possessions left in the quarter, laid over every position.
FIBA = os.environ.get('SENSE_FIBA') == '1'
FOULS = os.environ.get('SENSE_FOULS', '')
RULE['rules'] = {k: ('on' if FIBA else 'off') for k in ('three_seconds', 'closely_guarded', 'fiba_fouled_shot')}
if FOULS:
    RULE['fouls'] = dict(team_fouls=int(FOULS.split(',')[0]), quarter_left=int(FOULS.split(',')[1]))
_NAME = 'answers_zone.json' if ZONE else 'answers.json'
if FIBA:
    _NAME = 'answers_fiba' + ('_' + FOULS.replace(',', '_') if FOULS else '') + '.json'
POS, ANS = os.path.join(SET, 'positions.json'), os.path.join(SET, _NAME)
SRC = os.path.join(SET, 'sources')                    # what the set is built from: play harvested for it, and earlier steps' positions
# The reference engine: the one the answers are measured with (the default at the start of step 18h, its map kept in
# sense_set/reference_weights.json). Every play-out, in this step and later ones, is continued by it.
REF = dict(whole_turns=True, split_ties=True, rank_in_hand=True, kept_actions=False, no_floor=False, map='reference')
N = int(os.environ.get('SENSE_N', '64'))               # play-outs a candidate


def tally(what, secs):
    """Every run's cost, kept at the foot of the step's PREDICTIONS.md (the hard limit is in core-hours)."""
    path = os.path.join(WORK, 'tally.json')
    os.makedirs(WORK, exist_ok=True)
    t = json.load(open(path)) if os.path.exists(path) else []
    t.append([what, round(secs / 3600, 3)])
    json.dump(t, open(path, 'w'))
    total = round(sum(x[1] for x in t), 2)
    with open(os.path.join(RUN, 'PREDICTIONS.md'), 'a') as f:
        f.write(f'- {what}: {round(secs / 3600, 2)} (running total {total})\n')
    print(f'[tally] {what}: {round(secs / 3600, 3)} core-hours; total {total}', flush=True)
    return total


def key(turn):
    return json.dumps(turn, sort_keys=True)


def words(turn):
    def one(a):
        kind, side, piece, dest, arrow, target, shot = a
        who = f'{side}{piece + 1}' if piece is not None and piece >= 0 else side
        if kind == 'move': return f"{who} moves to {dest}" + (f", facing {['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][arrow]}" if side == 'X' and arrow is not None and arrow >= 0 else '')
        if kind == 'qs': return f"{who} Quick Steps to {dest}"
        if kind == 'sprint': return f"{who} Sprints to {dest}"
        if kind == 'pass': return f"{who} passes to {side}{target + 1}"
        if kind in ('shot', 'forced_shot'): return f"{who} shoots ({shot})"
        if kind == 'steal': return f"{who} tries a Steal"
        if kind == 'pause': return 'the defence Pauses'
        if kind == 'hesitate': return 'the offence Hesitates'
        if kind == 'end_turn': return f"{'the defence' if side == 'X' else 'the offence'} ends its turn"
        if kind == 'dribble': return f"{who} dribbles at X{target + 1}"
        if kind == 'contest': return f"{who} Contests"
        if kind == 'screen': return f"{who} sets a screen"
        return f"{who} {kind}"
    return ', then '.join(one(a) for a in turn)


def load():
    return json.load(open(POS)), (json.load(open(ANS)) if os.path.exists(ANS) else dict(play_outs=N, engine=REF, results={}))


def searches(items, tag='ref', noise=0.0, **switches):
    """One whole search (the All-Star, 1 pair, no pick noise) on each item {state, ctx (JSON)}: the turns best first."""
    contexts, pos = [], []
    for k, it in enumerate(items):
        contexts.append(it['ctx'])
        pos.append(dict(id=str(k), state=it['state'], ctx=k))
    rows, secs = L.run_jobs('search', pos, contexts, policies={'p': L.policy('allstar', 2, noise, **switches)}, **RULE)
    tally(f'searches ({tag}, {len(items)} positions)', secs)
    rows = {int(r['id']): r for r in rows}               # the rows come back core by core, not in the order sent
    return [rows[k]['by']['p']['results'] for k in range(len(items))]


def cmd_harvest(n='40', seed='18'):
    """All-Star self-play on the reference engine, every decision's position kept, and every position where the defence
    answers a shot -> work/harvest.json"""
    pl = json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step18', 'pools.json')))['senior/pro/digital']
    pol = L.policy('allstar', 2, L.profiles()['allstar']['noise'], **REF)
    starts = [pl['starts'][(7 * i + 3) % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('selfplay', starts, pl['contexts'], n=1, seed=int(seed), keepReactions=True, policies=dict(O=pol, X=pol))
    os.makedirs(SRC, exist_ok=True)
    json.dump(dict(contexts=pl['contexts'], rows=rows), open(os.path.join(SRC, 'harvest.json'), 'w'))
    tally(f'harvest ({n} possessions)', secs)
    print(len(rows), 'possessions;', sum(len(r['states']) for r in rows), 'decisions;', sum(len(r['reactions']) for r in rows), 'shot reactions')


# ---- the set ---------------------------------------------------------------------------------------------------------

def _distinct(results, n, skip=()):
    """The first n turns of a search that read differently from each other (and from the turns in skip)."""
    out, seen = [], set(round(v, 3) for v in skip)
    for v, t in results:
        if round(v, 3) in seen:
            continue
        seen.add(round(v, 3))
        out.append((v, t))
        if len(out) >= n:
            break
    return out


def cmd_build():
    """The set's positions and their named candidates (the moves expected, the board's moves, each earlier step's
    choice). Fixed before any setting is scored; a setting's own choice is added when it is scored."""
    from playmaker_engine import exam as EX, jsbridge as J
    from playmaker_engine import rules_config as RC
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    out = []

    def add(pid, group, what, s=None, cands=(), state=None, ctx=None, note=''):
        sj, cj = (J.state_json(s), J.ctx_json(s.ctx)) if s is not None else (state, ctx)
        cs = []
        for name, turn in cands:
            if turn is None or any(key(turn) == key(c['turn']) for c in cs):
                continue
            cs.append(dict(name=name, turn=turn))
        out.append(dict(id=pid, group=group, what=what, note=note, side=sj['side'], stage=sj['stage'], clock=sj['clock'], state=sj, ctx=cj, candidates=cs))

    nm = lambda s, *names: E18._named(s, tuple(names), soft=True)
    # -- the closeout board, both versions; its step 2; game EB3F5B; step 18e's two Steal positions
    s0 = E18.closeout_board()
    add('closeout, shooter cannot move', 'closeout', "O4 (three 11) has the ball at A3 and can't move again. X3 is at F4, a Quick Step and a Move away.", s0,
        [("your order: X3 Quick Steps to E4 and keeps the Move; X2 moves to B6", nm(s0, 'X3 Quick Step to E4', 'X2 Move to B6 facing SW')),
         ("X3 Moves to C4 and keeps the Quick Step; X2 moves to B6", nm(s0, 'X3 Move to C4 facing SW', 'X2 Move to B6 facing SW')),
         ("X3 Quick Steps to E4, and the computer chooses the rest", nm(s0, 'X3 Quick Step to E4')),
         ("the defence Pauses", nm(s0, 'X Pause'))], note='18f: your order 5.6 better by play (2.4 to 8.7)')
    free = s0.with_(moved_o=0, qs_o=0, cnt=(0,) * len(s0.cnt))
    add('closeout, shooter can move', 'closeout', "The same board, O4 able to move.", free,
        [("X3 Moves to C4, facing him", nm(free, 'X3 Move to C4 facing SW')),
         ("X3 Quick Steps to E4", nm(free, 'X3 Quick Step to E4')),
         ("X3 Moves to C4; X2 moves to B6", nm(free, 'X3 Move to C4 facing SW', 'X2 Move to B6 facing SW')),
         ("X3 Quick Steps to E4; X2 moves to B6", nm(free, 'X3 Quick Step to E4', 'X2 Move to B6 facing SW'))], note='18e: the Move closer better')
    s2 = E18._apply_names(s0, ('X3 Quick Step to E4', 'X End turn', 'O2 Move to B8', 'O End turn'))
    add('closeout, step 2', 'closeout', "After X3's Quick Step to E4, the offence has moved O2 to B8.", s2,
        [("X3 Moves next to him, then tries a Steal", nm(s2, 'X3 Move to B4 facing SW', 'X3 Steal')),
         ("X3 Moves next to him and stops", nm(s2, 'X3 Move to B4 facing SW', 'X End turn')),
         ("the defence Pauses", nm(s2, 'X Pause'))], note='18e: too close to call')
    before, _ = E18._replay(RC.with_rules(digital=True), ['N'] * 5)
    lines = [ln.split('] ', 1)[1] for ln in E18.LOG.splitlines()]
    sb = before[lines.index('O1 Pass to O4')]
    sp = apply(sb, next(a for a in legal_actions(sb) if str(a) == 'O1 Pass to O4'))
    add('game EB3F5B, the pass in the air', 'closeout', "Your playtest: the pass to O4 in the corner is in the air. X4 is at F4.", sp,
        [("X4 Moves to C4, facing him", nm(sp, 'X4 Move to C4 facing SW')),
         ("X4 Quick Steps to E4", nm(sp, 'X4 Quick Step to E4')),
         ("the defence Pauses (the log)", nm(sp, 'X Pause'))], note='18e and 18f: the Move closer 2.6 to 3.0 better')
    src = SRC                                          # step 18e's two positions, kept with the set
    for name, label in (('defence242', "18e's Steal position, clock 2"), ('defence377', "18e's Steal position, clock 10")):
        job = json.load(open(os.path.join(src, f'regret_open_defence_{name}.job.json')))
        o = json.load(open(os.path.join(src, f'regret_open_defence_{name}.out.json')))
        on = [r for r in o['rows'] if r['stage'] == 4]
        choice = min(on, key=lambda r: r['pair'])
        steal = min((r for r in o['rows'] if 'Steal' in r['words']), key=lambda r: r['pair'])
        pause = next((r for r in o['rows'] if r['words'] == 'X Pause'), None)
        add(label, 'steal', "A position from play where step 18d's reading wanted a Steal and step 18e's computer declined.", None,
            [("step 18e's choice: " + words(choice['turn']), choice['turn']), ("step in, then Steal: " + words(steal['turn']), steal['turn'])] +
            ([('the defence Pauses', pause['turn'])] if pause else []), state=job['state'], ctx=job['ctx'], note="18e: the computer's move better")
    # -- from play (work/harvest.json): Contest or not; the defence's last turn before an open shot; shoot now or play on
    h = json.load(open(os.path.join(SRC, 'harvest.json')))
    cx = lambda i: h['contexts'][h['rows'][i]['ctx']]
    re = [(i, st) for i, r in enumerate(h['rows']) for st in r['reactions']]
    rres = searches([dict(state=st, ctx=cx(i)) for i, st in re], 'reactions', **REF)
    n_con, open_shots = 0, []
    for (i, st), res in zip(re, rres):
        if len(set(round(v, 3) for v, _ in res)) < 2:
            open_shots.append(i)                        # nothing the defence can do changes the shot: it is open
            continue
        if n_con >= 4:
            continue
        n_con += 1
        cands = [(f"the reference's {k + 1}{['st', 'nd', 'rd'][k]} reading: " + words(t), t) for k, (v, t) in enumerate(_distinct(res, 3))]
        end = next((t for v, t in res if t[0][0] == 'end_turn'), None)
        add(f'Contest or not {n_con}', 'contest', f"O{st['ball'] + 1} has declared a {st['shot']} from {st['o'][st['ball']]}; the defence answers.", None,
            cands + ([('no Contest: the defence ends its turn', end)] if end else []), state=st, ctx=cx(i))
    # the defence's last turn of its own before a shot nobody could reach
    lasts = []
    for i in open_shots:
        r = h['rows'][i]
        xs = [st for st in r['states'] if st['side'] == 'X' and st['turn_n'] == 0 and st['stage'] == 'play']
        if xs and len(lasts) < 3 and i not in [j for j, _ in lasts]:
            lasts.append((i, xs[-1]))
    lres = searches([dict(state=st, ctx=cx(i)) for i, st in lasts], 'last turns', **REF)
    for k, ((i, st), res) in enumerate(zip(lasts, lres)):
        shot = next(s for s in h['rows'][i]['reactions'])
        sq = shot['o'][shot['ball']]
        xy = lambda q: (ord(q[0]) - 65, int(q[1:]))
        cheb = lambda a, b: max(abs(xy(a)[0] - xy(b)[0]), abs(xy(a)[1] - xy(b)[1]))
        # of the turns the search listed, the one that ends with a defender nearest the square the shot then came from
        def near(t):
            ends = list(st['x'])
            for a in t:
                if a[0] in ('move', 'qs', 'sprint') and a[1] == 'X':
                    ends[a[2]] = a[3]
            return min(cheb(q, sq) for q in ends)
        closest = min(res, key=lambda r: (near(r[1]), r[0]))
        cands = [(f"the reference's {j + 1}{['st', 'nd', 'rd'][j]} reading: " + words(t), t) for j, (v, t) in enumerate(_distinct(res, 2))]
        pause = next((t for v, t in res if t[0][0] == 'pause'), [['pause', 'X', -1, None, -1, -1, '']])
        add(f'before an open shot {k + 1}', 'position', f"The defence's last turn before O{shot['ball'] + 1} shot a {shot['shot']} from {sq} with nobody in reach.", None,
            cands + [("the listed turn that ends nearest the shooter: " + words(closest[1]), closest[1]), ('the defence Pauses', pause)], state=st, ctx=cx(i))
    # shoot now or play on: the offence's turn in phases 1 and 2 with a shot it can release at once
    offs = [(i, st) for i, r in enumerate(h['rows']) for st in r['states'] if st['side'] == 'O' and st['turn_n'] == 0 and st['stage'] == 'play' and not st['pending'] and st['clock'] >= 9]
    ores = searches([dict(state=st, ctx=cx(i)) for i, st in offs], 'offence turns', **REF)
    took, held, used = 0, 0, set()
    for (i, st), res in zip(offs, ores):
        if i in used:
            continue
        shots = [(v, t) for v, t in res if t[0][0] == 'shot']
        plays = [(v, t) for v, t in res if not any(a[0] == 'shot' for a in t)]
        if not shots or not plays:
            continue
        shoots = res[0][1][0][0] == 'shot'
        if (shoots and took >= 2) or (not shoots and (held >= 2 or shots[0][0] < res[0][0] - 4)):
            continue
        took, held = took + shoots, held + (not shoots)
        used.add(i)
        add(f'shoot now or play on {took + held}', 'shoot', f"The offence's turn in phase {(12 - st['clock']) // 2 + 1}: O{st['ball'] + 1} can shoot at once from {st['o'][st['ball']]}.", None,
            [('shoot now: ' + words(shots[0][1]), shots[0][1])] + [(f"play on, the reference's {j + 1}{['st', 'nd'][j]} such turn: " + words(t), t) for j, (v, t) in enumerate(_distinct(plays, 2))],
            state=st, ctx=cx(i))
    # -- "move, then shoot": the two worst misses of step 18f's reply list (tools/reply_miss_18f.js)
    rm = json.load(open(os.path.join(SRC, 'reply_miss.json')))
    for k, x in enumerate(sorted(rm, key=lambda x: x['A'] - x['C'])[:2]):
        add(f'move, then shoot {k + 1}', 'move then shoot', "The offence's turn: step 18f's picture of this reply held the first turn and missed the second.", None,
            [("what 18f's reply list held: " + words(x['Aj']), x['Aj']), ("the turn it missed: " + words(x['Cj']), x['Cj'])], state=x['state'], ctx=x['ctx'])
    # -- the boards still unclear
    for n in ('1', '3', '8', '9'):
        _, s, _ = EX.POSITIONS[int(n) - 1]()
        add(f'board {n}', 'board', EX.POSITIONS[int(n) - 1]()[0] if isinstance(EX.POSITIONS[int(n) - 1]()[0], str) else f'exam board {n}', s,
            [(name, nm(s, *acts)) for name, acts in E18.BOARD_TURNS[n]])
    b2 = EX.POSITIONS[1]()[1][12]
    sag = [(f, nm(b2, f'X2 Move to D7 facing {f}')) for f in ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')]
    sag = [(f, t) for f, t in sag if t]
    sres = searches([dict(state=J.state_json(b2), ctx=J.ctx_json(b2.ctx))], 'board 2', **REF)[0]
    add('board 2 (three 12)', 'board', "Sag by shooting: O2's three is rated 12; the board wants X2 to sag to D7, where he can still Contest.", b2,
        [("the board's sag: " + words(t), t) for f, t in sag[:1]] + [("the board's sag, facing " + f + ': ' + words(t), t) for f, t in sag[1:3]] +
        [('the defence Pauses', nm(b2, 'X Pause'))])
    os.makedirs(SET, exist_ok=True)
    if os.path.exists(POS):                             # a choice some setting made when it was scored stays in the set, with its answer
        old = {p['id']: p for p in json.load(open(POS))}
        for p in out:
            for c in old.get(p['id'], {}).get('candidates', []):
                if c.get('added_by') and not any(key(c['turn']) == key(x['turn']) for x in p['candidates']):
                    p['candidates'].append(c)
    json.dump(out, open(POS, 'w'), indent=1)
    if os.path.exists(ANS):                             # answers are kept only for candidates still in the set
        ans = json.load(open(ANS))
        keep = {p['id']: set(key(c['turn']) for c in p['candidates']) for p in out}
        ans['results'] = {pid: {k: v for k, v in d.items() if k in keep[pid]} for pid, d in ans['results'].items() if pid in keep}
        json.dump(ans, open(ANS, 'w'))
    print(len(out), 'positions;', sum(len(p['candidates']) for p in out), 'candidates')
    for p in out:
        print(' ', p['id'], '|', p['side'], 'clock', p['clock'], '|', len(p['candidates']), 'candidates')
        for c in p['candidates']:
            print('      -', c['name'][:110])


def cmd_grow(n='10'):
    """Step 18g: positions two of the defence's turns before a shot nobody could reach (from the harvested play),
    added to the set without touching what is there. Candidates: the reference's own choice; the listed turn that
    ends with a defender nearest the player who went on to shoot; the one nearest the square he shot from; a Pause."""
    positions, answers = load()
    h = json.load(open(os.path.join(SRC, 'harvest.json')))
    cx = lambda i: h['contexts'][h['rows'][i]['ctx']]
    re = [(i, st) for i, r in enumerate(h['rows']) for st in r['reactions']]
    rres = searches([dict(state=st, ctx=cx(i)) for i, st in re], 'reactions', **REF)
    picked = []
    for (i, shot), res in zip(re, rres):
        if len(set(round(v, 3) for v, _ in res)) >= 2:
            continue                                     # the defence could do something about this shot
        xs = [st for st in h['rows'][i]['states'] if st['side'] == 'X' and st['turn_n'] == 0 and st['stage'] == 'play']
        if len(xs) >= 2 and i not in [j for j, _, _ in picked] and len(picked) < int(n):
            picked.append((i, xs[-2], shot))
    lres = searches([dict(state=st, ctx=cx(i)) for i, st, _ in picked], 'two turns before', **REF)
    xy = lambda q: (ord(q[0]) - 65, int(q[1:]))
    cheb = lambda a, b: max(abs(xy(a)[0] - xy(b)[0]), abs(xy(a)[1] - xy(b)[1]))
    have = set(p['id'] for p in positions)
    for k, ((i, st, shot), res) in enumerate(zip(picked, lres)):
        pid = f'two turns before an open shot {k + 1}'
        if pid in have:
            continue
        who, sq = shot['ball'], shot['o'][shot['ball']]

        def ends(t):
            e = list(st['x'])
            for a in t:
                if a[0] in ('move', 'qs', 'sprint') and a[1] == 'X':
                    e[a[2]] = a[3]
            return e
        near_him = min(res, key=lambda r: (min(cheb(q, st['o'][who]) for q in ends(r[1])), r[0]))
        near_sq = min(res, key=lambda r: (min(cheb(q, sq) for q in ends(r[1])), r[0]))
        pause = next((t for v, t in res if t[0][0] == 'pause'), [['pause', 'X', -1, None, -1, -1, '']])
        cands, seen = [], set()
        for name, t in ((f"the reference's choice: " + words(res[0][1]), res[0][1]),
                        (f"the listed turn that ends nearest O{who + 1}, who went on to shoot: " + words(near_him[1]), near_him[1]),
                        (f"the listed turn that ends nearest {sq}, where the shot came from: " + words(near_sq[1]), near_sq[1]),
                        ('the defence Pauses', pause)):
            if key(t) not in seen:
                seen.add(key(t))
                cands.append(dict(name=name, turn=t))
        positions.append(dict(id=pid, group='two turns before', note=f"O{who + 1} is at {st['o'][who]} now",
                              what=f"Two of the defence's turns before O{who + 1} shot a {shot['shot']} from {sq} with nobody in reach.",
                              side=st['side'], stage=st['stage'], clock=st['clock'], state=st, ctx=cx(i), candidates=cands))
        print(pid, '|', st['clock'], '|', [c['name'][:70] for c in cands])
    json.dump(positions, open(POS, 'w'), indent=1)
    print(len(positions), 'positions')


def _seed(pid, k):
    import zlib
    return 15485863 * (k + 1) + 1 + 2 * (zlib.crc32(pid.encode()) % 500000)


def play(positions, answers, only=None, copies=(0, 1)):
    """Play out every candidate that lacks an answer on one of the named copies (a copy: 16 play-outs with dice of its
    own; play-out i of copy k has the same dice for every candidate of a position, whenever it is played). The
    reference engine on both sides, its pick noise."""
    jobs, contexts, names = [], [], {}
    for p in positions:
        if only and p['id'] not in only:
            continue
        have = answers['results'].setdefault(p['id'], {})
        for k in copies:
            # under the zone only the named candidates and the zone's own choices are played (the limit on compute)
            miss = [c['turn'] for c in p['candidates'] if not (have.get(key(c['turn'])) or [[], [], [], []])[k]
                    and not (ZONE and c.get('added_by') and not c['added_by'].startswith('zone') and not c.get('zone_too'))
                    and not (FIBA and c.get('added_by') and not c['added_by'].startswith('fiba') and not c.get('fiba_too'))]
            if not miss:
                continue
            if p['id'] not in names:
                names[p['id']] = len(contexts)
                contexts.append(p['ctx'])
            jobs.append(dict(id=f"{p['id']}##{k}", state=p['state'], ctx=names[p['id']], seed=_seed(p['id'], k), turns=miss))
    if not jobs:
        return 0.0
    pol = L.policy('allstar', 2, L.profiles()['allstar']['noise'], **REF)
    rows, secs = L.run_jobs('rollout', jobs, contexts, n=16, seed=7, keep=True, policies=dict(O=pol, X=pol), **RULE)
    n = 0
    for r in rows:                                     # each row names its own position and copy (the rows come back core by core)
        pid, k = r['id'].rsplit('##', 1)
        for t in r['turns']:
            if not t['values']:
                print('  not legal from this position, left out:', pid, words(t['turn']))
                continue
            answers['results'][pid].setdefault(key(t['turn']), [[], [], [], []])[int(k)] = [round(v, 3) for v in t['values']]
            n += 1
    json.dump(answers, open(ANS, 'w'))
    tally(f'play-outs ({n} candidate copies of 16 on {len(names)} positions)', secs)
    return secs


def cmd_reply(pid, name, top='8'):
    """A sense check's detail (step 18g): the other side's reply to one candidate, as the reference engine reads it:
    its turns best first with their values. Under SENSE_ZONE the zone rule."""
    positions, answers = load()
    p = next(q for q in positions if q['id'] == pid)
    c = next(c for c in p['candidates'] if name in c['name'])
    rows, secs = L.run_jobs('search', [dict(id='0', state=p['state'], ctx=0, pre=c['turn'])], [p['ctx']], chunks=1,
                            policies={'p': L.policy('allstar', 2, 0.0, **REF)}, **RULE)
    print(pid, '| after', c['name'][:80], '| to act:', rows[0]['side'])
    for v, t in rows[0]['by']['p']['results'][:int(top)]:
        print('   ', round(v, 2), words(t))


def cmd_split(pid, name):
    """Step 18i: a Steal's value in its parts, as the All-Star reads each way it can come out: the foul, the ball
    won, the miss. The candidate's turn is played up to and including its Steal. Under the rules and foul situation
    the environment sets."""
    positions, answers = load()
    p = next(q for q in positions if q['id'] == pid)
    c = next(c for c in p['candidates'] if name in c['name'])
    k = max(i for i, a in enumerate(c['turn']) if a[0] == 'steal')
    rows, secs = L.run_jobs('split', [dict(id='0', state=p['state'], ctx=0, pre=c['turn'][:k + 1])], [p['ctx']], chunks=1,
                            policies={'p': L.policy('allstar', 2, 0.0)}, **RULE)
    parts = rows[0]['parts']
    print(pid, '|', c['name'][:70], '| fiba' if FIBA else '| before', '| fouls', FOULS or 'none')
    tot = 0.0
    out = []
    for q in parts:
        tot += q['p'] * q['value']
        out.append(dict(what=q['label'], chance=round(q['p'], 3), worth=round(q['value'], 2), share=round(q['p'] * q['value'], 2), ended=q['ended']))
        print('   ', q['label'].ljust(22), 'chance', round(q['p'], 3), '| worth to the offence', round(q['value'], 2), '| share', round(q['p'] * q['value'], 2), '|', q['ended'] or 'play goes on')
    print('    the Steal as a whole:', round(tot, 2))
    return dict(position=pid, candidate=c['name'], fiba=FIBA, fouls=FOULS, parts=out, whole=round(tot, 2))


def cmd_lines(pid, lines='2', *names):
    """A sense check's detail (step 18g): each candidate of one position played out on copy 0's dice again, keeping how
    each play-out ended and the actions of the first few. Under SENSE_ZONE the zone rule. -> runs/<step>/lines_*.json"""
    from collections import Counter
    positions, answers = load()
    p = next(q for q in positions if q['id'] == pid)
    cands = [c for c in p['candidates'] if (not names or any(n in c['name'] for n in names))
             and (key(c['turn']) in answers['results'].get(pid, {}))]
    jobs = [dict(id=str(i), state=p['state'], ctx=0, seed=_seed(pid, 0), turns=[c['turn']]) for i, c in enumerate(cands)]
    pol = L.policy('allstar', 2, L.profiles()['allstar']['noise'], **REF)
    rows, secs = L.run_jobs('rollout', jobs, [p['ctx']], n=16, seed=7, keep=True, ends=True, lines=int(lines), policies=dict(O=pol, X=pol), **RULE)
    out = []
    for r in sorted(rows, key=lambda r: int(r['id'])):
        t = r['turns'][0]
        c = cands[int(r['id'])]
        out.append(dict(name=c['name'], turn=words(c['turn']), scored=round(sum(t['values']) / max(1, len(t['values'])), 2),
                        ended=dict(Counter(t['ends'])), values=t['values'], lines=t['lines']))
        print(c['name'][:90], '|', out[-1]['scored'], '|', out[-1]['ended'])
        for ln, v in zip(t['lines'], t['values']):
            print('     ', round(v, 1), '<-', '; '.join(ln)[:400])
    json.dump(dict(position=pid, zone=ZONE, candidates=out), open(os.path.join(RUN, f"lines_{'zone' if ZONE else 'today'}_{pid.replace(' ', '_').replace(',', '')}.json"), 'w'), indent=1)
    tally(f"sense check detail ({pid}, {'zone' if ZONE else 'today'})", secs)


def cmd_play(copies='0,1', *only):
    positions, answers = load()
    play(positions, answers, set(only) or None, tuple(int(k) for k in copies.split(',')))


def table(positions, answers, choices=None):
    """Each position: every candidate's played-out value (what the offence went on to score; the side to act wants it
    low on defence, high on offence), the best, and each against the best with a paired interval."""
    rep = []
    for p in positions:
        res = answers['results'].get(p['id'], {})
        sign = 1 if p['side'] == 'O' else -1                 # the side to act's own point of view
        rows = []
        flat = lambda v: [x for c in v for x in c]
        for c in p['candidates']:
            v = res.get(key(c['turn']))
            if not v or not flat(v):
                continue
            m, sd, ci = L.mean_ci(flat(v))
            rows.append(dict(name=c['name'], turn=c['turn'], play_outs=len(flat(v)), scored=round(m, 2), interval=[round(m - ci, 2), round(m + ci, 2)], values=v))
        if not rows:
            continue
        # candidates are set against each other on the copies they share (the same dice, play-out for play-out)
        both = lambda a, b: [(x, y) for ca, cb in zip(a['values'], b['values']) if ca and cb for x, y in zip(ca, cb)]
        common = [k for k in range(4) if all(r['values'][k] for r in rows)]
        on_common = lambda r: sum(x for k in common for x in r['values'][k]) / max(1, sum(len(r['values'][k]) for k in common)) if common else r['scored']
        best = max(rows, key=lambda r: sign * on_common(r))
        for r in rows:
            d = [sign * (b - a) for a, b in both(r, best)]      # points lost against the best
            dm, dsd, dci = L.mean_ci(d)
            r['behind_the_best'] = round(dm, 2)
            r['behind_interval'] = [round(dm - dci, 2), round(dm + dci, 2)]
            r['is_best_or_level'] = r is best or dm - dci <= 0
            r['compared_on'] = len(d)
        one = dict(id=p['id'], group=p['group'], side=p['side'], best=best['name'], rows=[{k: v for k, v in r.items() if k != 'values'} for r in rows])
        if choices is not None:
            ch = next((r for r in rows if key(r['turn']) == key(choices[p['id']])), None)
            one['choice'] = None if ch is None else dict(name=ch['name'], behind_the_best=ch['behind_the_best'], behind_interval=ch['behind_interval'], matches=ch['is_best_or_level'],
                                                         lost=[sign * (b - a) for a, b in both(ch, best)])
        rep.append(one)
    return rep


def cmd_answers():
    positions, answers = load()
    positions = [p for p in positions if not ONLY or any(p['id'].startswith(x) for x in ONLY)]
    for one in table(positions, answers):
        print(one['id'], '|', one['side'])
        for r in one['rows']:
            print('    ', ('* ' if r['name'] == one['best'] else '  ') + r['name'][:95], '|', r['scored'], r['interval'], '| behind', r['behind_the_best'], r['behind_interval'])


def _switches(args):
    sw = {}
    for a in args:
        k, v = a.split('=') if '=' in a else (a, 'true')
        sw[k] = True if v == 'true' else False if v == 'false' else v
    return sw


def cmd_choices(tag, *args):
    """The computer's choice on each position under a setting, and whether the set already has an answer for it
    (no play-outs)."""
    positions, answers = load()
    positions = [p for p in positions if not ONLY or any(p['id'].startswith(x) for x in ONLY)]
    res = searches(positions, tag + ' choices', **_switches(args))
    new = 0
    for p, r in zip(positions, res):
        t = r[0][1]
        known = any(key(c['turn']) == key(t) for c in p['candidates'])
        new += not known
        tied = sum(1 for v, _ in r if abs(v - r[0][0]) < 1e-9)
        print(('     ' if known else ' new '), p['id'], '|', words(t), round(r[0][0], 2), f'({tied} level)' if tied > 1 else '')
    print(tag, ':', new, 'choices without an answer yet')


def cmd_score(tag, *args):
    """A setting scored against the set: on each position the computer's own choice (the All-Star, 1 pair, no pick
    noise; the config as it stands, with the switches given as k=v). A choice that has no answer yet is added to the
    set and played out. -> runs/<step>/sense_<tag>.json"""
    import math
    positions, answers = load()
    scored = [p for p in positions if not ONLY or any(p['id'].startswith(x) for x in ONLY)]
    res = searches(scored, tag, **_switches(args))
    choices, added = {}, 0
    for p, r in zip(scored, res):
        t = r[0][1]
        choices[p['id']] = t
        if not any(key(c['turn']) == key(t) for c in p['candidates']):
            p['candidates'].append(dict(name=f"the computer's choice ({tag}): " + words(t), turn=t, added_by=tag))
            added += 1
        elif ZONE or FIBA:
            # the choice is a turn an earlier setting added: it is played under this rule set too
            w = 'zone' if ZONE else 'fiba'
            for c in p['candidates']:
                if key(c['turn']) == key(t) and c.get('added_by') and not c['added_by'].startswith(w) and not c.get(w + '_too'):
                    c[w + '_too'] = True
                    added += 1
    if added:
        json.dump(positions, open(POS, 'w'), indent=1)
    play(positions, answers, set(p['id'] for p in scored), tuple(int(k) for k in os.environ.get('SENSE_COPIES', '0,1').split(',')))
    rep = table(scored, answers, choices)
    rows, lost, var = [], [], 0.0
    for one in rep:
        ch = one.get('choice')
        if ch is None:
            rows.append(dict(id=one['id'], group=one['group'], best=one['best'], choice=words(choices[one['id']]), matches=None))
            continue
        d = ch.pop('lost')
        m, sd, ci = L.mean_ci(d)
        lost.append(m)
        var += sd * sd / len(d)
        rows.append(dict(id=one['id'], group=one['group'], best=one['best'], choice=ch['name'], matches=ch['matches'], points_lost=ch['behind_the_best'], interval=ch['behind_interval']))
    n = len(lost)
    mean = sum(lost) / n
    half = 1.96 * math.sqrt(var) / n
    k = sum(1 for r in rows if r['matches'])
    out = dict(tag=tag, switches=_switches(args), positions=len(rows), scored=n, matched=k, points_lost_a_position=round(mean, 2),
               interval=[round(mean - half, 2), round(mean + half, 2)], candidates_added=added, rows=rows,
               by_group={g: dict(positions=sum(1 for r in rows if r['group'] == g), matched=sum(1 for r in rows if r['group'] == g and r['matches']),
                                 points_lost=round(sum(r.get('points_lost', 0) for r in rows if r['group'] == g) / max(1, sum(1 for r in rows if r['group'] == g)), 2))
                         for g in sorted(set(r['group'] for r in rows))})
    json.dump(out, open(os.path.join(RUN, f'sense_{tag}.json'), 'w'), indent=1)
    for r in rows:
        print(('  ok ' if r['matches'] else '  -- '), r['id'], '|', (r['choice'] or '')[:70], '| lost', r.get('points_lost'), r.get('interval'), '| best:', r['best'][:50])
    print(f"{tag}: matched {k} of {n}; points lost a position {out['points_lost_a_position']} {out['interval']}; {added} choices added")
    print(json.dumps(out['by_group']))


def cmd_floor():
    """Part 1, no code change: the reading's parts after each candidate, which one today's reading returns, and how
    often candidates that leave different shots read the same -> runs/<step>/floor.json"""
    import subprocess
    outp = os.path.join(RUN, 'floor.json')
    subprocess.run(['node', os.path.join(HERE, 'floor_18h.js'), POS, outp], check=True)
    rows = json.load(open(outp))
    cs = [c for r in rows for c in r['candidates'] if c.get('to_act')]
    off = [c for c in cs if c['to_act'] == 'O']
    pairs = same = 0
    for r in rows:
        v = [c for c in r['candidates'] if c.get('to_act') == 'O']
        for i in range(len(v)):
            for j in range(i + 1, len(v)):
                if abs(v[i]['shot_now'] - v[j]['shot_now']) >= 5:
                    pairs += 1
                    same += abs(v[i]['today'] - v[j]['today']) < 0.5
    rep = dict(candidates_read=len(cs), the_offence_to_act=len(off), play_on_returned=sum(1 for c in off if c['returns'] == 'play on'),
               pairs_whose_shot_now_differs_by_5_or_more=pairs, of_them_reading_within_half_a_point_today=same,
               of_them_within_half_a_point_with_no_floor=sum(1 for r in rows for i, a in enumerate([c for c in r['candidates'] if c.get('to_act') == 'O'])
                                                              for b in [c for c in r['candidates'] if c.get('to_act') == 'O'][i + 1:]
                                                              if abs(a['shot_now'] - b['shot_now']) >= 5 and abs(a['no_floor'] - b['no_floor']) < 0.5), rows=rows)
    json.dump(rep, open(outp, 'w'), indent=1)
    print({k: v for k, v in rep.items() if k != 'rows'})
    for r in rows[:4]:
        print(r['id'])
        for c in r['candidates']:
            if c.get('to_act'):
                print('    ', c['name'][:60], '| shot now', round(c['shot_now'], 1), '| looks left', round(c['best_look_left'], 1), round(c['second_look_left'], 1), '|', c['returns'], '| today', round(c['today'], 2), '| no floor', round(c['no_floor'], 2))


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
