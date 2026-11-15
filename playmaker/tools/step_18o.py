"""Step 18o: the square defender (D-194), a setup that fits the players (D-195), and the test with and without the zone.

  python3 tools/step_18o.py board <name> [copies] [zone]              sense check: play out the named placements on Shaun's board
  python3 tools/step_18o.py pool <level> [zone] [starts]              the possession starts by the new setup, for a level
  python3 tools/step_18o.py trace <tag> <n> <level> [seed] [zone]     self-play from that level's pool
  python3 tools/step_18o.py maps / fouls / measures / matchups         as step 18n's
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('SENSE_RUN', 'step18o')
os.environ.setdefault('SENSE_18N', '1')
import step_18n as N                                    # noqa: E402
T, S, L, G, J, K, RUN, WORK, tally = N.T, N.S, N.L, N.G, N.J, N.K, N.RUN, N.WORK, N.tally
ROOT = os.path.dirname(HERE)
SHAUN_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
SHAUN_DEAL = 3351                                        # a coherent Senior Pro deal whose home 4 and 5 are the A-tier post scorers


def shaun_teams():
    """Shaun's board (15 Nov 2026): O4 and O5 are the Post Scorer Power Forward and the Post Scorer Centre, A tier; the
    other eight cards come from the coherent deal that holds them (seed 3351: SPC-0002L3)."""
    from playmaker_engine import rosters as R, levels as LV
    from relative_average import register_cards
    d = R.deal('senior', 'pro', True, seed=SHAUN_DEAL)
    return (register_cards('shaun 18o O', LV.team(d['rosters'][0], 'senior', None)),
            register_cards('shaun 18o X', LV.team(d['rosters'][1], 'senior', None)))


def shaun_state(x, arrows, zone=False, o=SHAUN_O, ball=0, **kw):
    from playmaker_engine import rules_config as RC
    from playmaker_engine.scenarios import game_state
    off, dfn = shaun_teams()
    s = game_state(off, dfn, list(o), list(x), list(arrows), ball=ball, rules=RC.with_rules(digital=True, **({'zone': 'on'} if zone else {})),
                   check=False, **T.FOULS)
    s.ctx.levels_key = ('senior', 'pro')
    return s.with_(**kw) if kw else s


def play(named, level='allstar', copies=16, zone=False, seed=1, what='play-outs'):
    """Play each named position out `copies` times at a level (both sides that level, the app's rules). named:
    [(name, state)], all of one matchup. Every candidate gets the same dice, copy by copy. -> {name: [rows]}"""
    from playmaker_engine import jsbridge
    ctx = jsbridge.ctx_json(named[0][1].ctx)
    pol = L.policy(level, 2, L.profiles()[level]['noise'])
    positions = []
    for name, s in named:
        for k in range(copies):
            positions.append(dict(id=name, state=jsbridge.state_json(s), ctx=0, seed=104729 * (k + 1) + 7919 * seed))
    rules = dict(T.RULES)
    if zone:
        rules['zone'] = 'on'
    rows, secs = L.run_jobs('trace', positions, [ctx], n=1, seed=seed, stances=True, policies=dict(O=pol, X=pol), rules=rules, fouls=T.FOULS)
    tally(f'{what} ({len(named)} placements, {copies} each, {level}{", zone on" if zone else ""})', secs)
    out = {}
    for p, r in zip(positions, rows):
        out.setdefault(p['id'], []).append(r)
    return out


def summary(rows):
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    return round(m, 1), round(m - ci, 1), round(m + ci, 1)


def stored_starts(age='senior', std='pro'):
    """The stored possession starts (the pool every step since 18 has played from), as states: (off, dfn, state)."""
    import relative_average as RA
    from playmaker_engine import rules_config as RC
    out = []
    for a, sd, r in RA.rows():
        if (a, sd) != (age, std):
            continue
        off, dfn = RA.team_of(r['off'], age, std), RA.team_of(r['dfn'], age, std)
        enc = next((e for e in r['snapshots'] if e.startswith('play:')), None)
        if enc is None or not enc.startswith('play:O'):
            continue
        s = RA.decode(enc, off, dfn, RC.with_rules(digital=True))
        if s.clock != RC.START_CLOCK:
            continue
        s.ctx.levels_key = (age, std)
        out.append((off, dfn, s))
    return out


def maker(off, dfn, zone=False):
    """make_names for agent.propose_offence and propose_defence: a possession start of this matchup."""
    from playmaker_engine import rules_config as RC
    from playmaker_engine.scenarios import game_state
    rules = RC.with_rules(digital=True, **({'zone': 'on'} if zone else {}))

    def make(o, x, arrows, ball):
        s = game_state(off, dfn, list(o), list(x), list(arrows), ball=ball, rules=rules, **T.FOULS)
        s.ctx.levels_key = ('senior', 'pro')
        return s
    return make


def write_pool(name, states):
    """A pool of starts in the form the self-play tool reads (contexts and starts), kept in this step's work folder."""
    from playmaker_engine import jsbridge
    contexts, seen, starts = [], {}, []
    for s in states:
        ctx = json.dumps(jsbridge.ctx_json(s.ctx), sort_keys=True)
        if ctx not in seen:
            seen[ctx] = len(contexts)
            contexts.append(json.loads(ctx))
        starts.append(dict(id=f'start{len(starts)}', state=jsbridge.state_json(s), ctx=seen[ctx]))
    os.makedirs(WORK, exist_ok=True)
    json.dump(dict(contexts=contexts, starts=starts), open(os.path.join(WORK, f'pool_{name}.json'), 'w'))
    return len(starts)


def cmd_setups(n='48', level='allstar', turns='3'):
    """The same deals set up three ways, to be played out against each other: as stored (the setup before this step,
    as it ran on a fast machine), each defender next to his man against the stored offence, and the search of this
    step for both sides (its searches carried over `turns` setups, at the app's setup time for the level)."""
    from playmaker_engine import agent as AG, board as B
    from playmaker_engine.jsbridge import NodeEngine
    from playmaker_web.game import man_to_man
    src = stored_starts()
    step = max(1, len(src) // int(n))
    src = src[::step][:int(n)]
    NodeEngine().install()
    budget = AG.profile(level)['time_budget_s'] * 0.4          # game._setup_budget in the app's format
    stored, man, search, notes = [], [], [], []
    t0 = time.time()
    for k, (off, dfn, s) in enumerate(src):
        make = maker(off, dfn)
        stored.append(s)
        xs, ar = man_to_man(list(s.o), s.ball)
        man.append(make([B.sq(q) for q in s.o], [B.sq(q) for q in xs], ar, s.ball))
        mem_o, mem_x = {}, {}
        for t in range(int(turns)):
            ro = AG.propose_offence(make, 1000 * k + t, budget=budget, level=level, memory=mem_o, search=True)
            rx = AG.propose_defence(make, ro['squares'], ro['ball'], 1000 * k + t + 7, budget=budget, level=level, memory=mem_x, search=True)
        search.append(make([B.sq(q) for q in ro['squares']], [B.sq(q) for q in rx['squares']], rx['arrows'], ro['ball']))
        notes.append(dict(off=off, dfn=dfn, o=[B.sq(q) for q in ro['squares']], x=[B.sq(q) for q in rx['squares']], arrows=rx['arrows'],
                          o_reads=ro['reads'], x_reads=rx['reads'], o_judged=ro['judged'], x_judged=rx['judged'], o_seconds=ro['seconds'], x_seconds=rx['seconds']))
    secs = time.time() - t0
    tally(f'one core: the search setup for {len(src)} deals ({turns} setups each, {level})', secs)
    for name, states in (('stored', stored), ('man', man), ('search', search)):
        print(name, write_pool(f'setup_{name}_{level}', states), 'starts')
    json.dump(notes, open(os.path.join(RUN, f'setup_search_{level}.json'), 'w'), indent=1)


def cmd_setuptest(level='allstar', seed='1'):
    """Play the three setups of the same deals out (both sides the level), the same dice start by start."""
    pol = L.policy(level, 2, L.profiles()[level]['noise'])
    out = {}
    for name in ('stored', 'man', 'search'):
        pl = json.load(open(os.path.join(WORK, f'pool_setup_{name}_{level}.json')))
        T.pool_is_current(pl)
        starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(pl['starts'])]
        rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), stances=True, policies=dict(O=pol, X=pol), rules=dict(T.RULES), fouls=T.FOULS)
        json.dump(dict(size=name, rows=rows), open(os.path.join(WORK, f'trace_setup_{name}_{level}.json'), 'w'))
        tally(f'self-play (setup {name}, {level}, {len(rows)} possessions)', secs)
        m, sd, ci = L.mean_ci([r['points'] for r in rows])
        out[name] = dict(n=len(rows), mean=round(m, 2), low=round(m - ci, 2), high=round(m + ci, 2), points=[r['points'] for r in rows])
        print(name, level, len(rows), 'possessions', round(m, 2), [round(m - ci, 2), round(m + ci, 2)])
    base = out['stored']['points']
    for name in ('man', 'search'):
        d = [a - b for a, b in zip(out[name]['points'], base)]
        m, sd, ci = L.mean_ci(d)
        out[name]['against_stored'] = [round(m, 2), round(m - ci, 2), round(m + ci, 2)]
        print(name, 'less stored, start by start:', out[name]['against_stored'])
    d = [a - b for a, b in zip(out['search']['points'], out['man']['points'])]
    m, sd, ci = L.mean_ci(d)
    out['search']['against_man'] = [round(m, 2), round(m - ci, 2), round(m + ci, 2)]
    print('search less man, start by start:', out['search']['against_man'])
    json.dump(out, open(os.path.join(RUN, f'setup_test_{level}.json'), 'w'))


# ---- the sense checks on Shaun's board (part 2) ------------------------------------------------------------------------

HIS = (['J10', 'D8', 'O8', 'B4', 'P2'], ['NW', 'NW', 'N', 'SW', 'NE'])        # the defence in his game, from the screenshot
SENSE = os.path.join(RUN, 'sense_18o.json')


def _sense():
    return json.load(open(SENSE)) if os.path.exists(SENSE) else {}


def _reading(make, o, ball, xs, arrows, depth=2):
    """The All-Star's own reading of a start, one pair ahead (its turn and the reply), no time limit. Asked of the
    JavaScript search directly: the bridge (jsbridge.ported) sends a game under rules.zone to the Python search, which
    is the same search and far slower."""
    from playmaker_engine import agent as AG, jsbridge
    s = make(o, xs, arrows, ball)
    p = dict(AG.profile('allstar'), noise=0.0, depth=[depth, depth])
    out = json.loads(AG.JS['search'](json.dumps(dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), profile=p, budget=600, max_depth=depth, stale=None))))
    return max(v for v, _ in out['results'])


def cmd_prepare():
    """What the search itself rates best on Shaun's board, read one pair ahead with no time limit: each off-ball
    defender's arrow on his game's squares (one defender at a time), and X1's square and arrow next to O1; with the
    zone off and on. Kept in sense_18o.json under 'prepared'."""
    from playmaker_engine import board as B, agent as AG
    from playmaker_engine.jsbridge import NodeEngine
    NodeEngine().install()
    out, t0 = dict(_sense().get('prepared') or {}), time.time()
    for zone in (False, True):
        if ('zone on' if zone else 'zone off') in out:
            continue
        make = lambda o, x, a, b, z=zone: shaun_state(x, a, zone=z, o=o, ball=b)
        base = _reading(make, SHAUN_O, 0, *HIS)
        arrows, table = list(HIS[1]), {}
        for j in (1, 2, 3, 4):
            vals = {}
            for d in B.DIR_NAMES:
                ar = HIS[1][:j] + [d] + HIS[1][j + 1:]
                vals[d] = _reading(make, SHAUN_O, 0, HIS[0], ar)
            best = min(vals.values())
            # the arrow the search rates best for the defence; his game's arrow is kept when it reads level with the best
            arrows[j] = HIS[1][j] if vals[HIS[1][j]] <= best + 1e-9 else min(vals, key=lambda d: (vals[d], B.DIR_NAMES.index(d)))
            table[f'X{j + 1}'] = {d: round(v, 2) for d, v in vals.items()}
        x1 = {}
        o1 = B.parse_sq('I11')
        for step in B.DIRS:
            q = B.add(o1, step)
            if not B.on_board(q) or B.sq(q) in SHAUN_O or B.sq(q) in HIS[0][1:]:
                continue
            for d in B.DIR_NAMES:
                x1[f'{B.sq(q)} {d}'] = _reading(make, SHAUN_O, 0, [B.sq(q)] + HIS[0][1:], [d] + HIS[1][1:])
        bestx1 = min(x1, key=lambda k: (x1[k], k))
        out['zone on' if zone else 'zone off'] = dict(his_game=round(base, 2), arrows=arrows, arrow_readings=table, with_arrows=round(_reading(make, SHAUN_O, 0, HIS[0], arrows), 2),
                                                     x1=bestx1, x1_reading=round(x1[bestx1], 2), x1_readings={k: round(v, 2) for k, v in sorted(x1.items(), key=lambda kv: kv[1])})
        d = _sense()
        d['prepared'] = out
        json.dump(d, open(SENSE, 'w'), indent=1)
        print('zone on' if zone else 'zone off', 'his game reads', round(base, 2), '; arrows', arrows, 'read', out['zone on' if zone else 'zone off']['with_arrows'], '; X1', bestx1, round(x1[bestx1], 2))
    tally('one core: the search\'s own reading of arrows and of X1\'s squares on Shaun\'s board', time.time() - t0)
    d = _sense()
    d['prepared'] = out
    json.dump(d, open(SENSE, 'w'), indent=1)


def _beaten(s):
    """The same board after the point guard wins his Dribble against X1 (the defence to answer)."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    n = apply(s, next(a for a in legal_actions(s) if a.kind == 'dribble'))
    return next(sub for p, lab, sub in n.outcomes if sub.beaten)


def _drive(s):
    """The same board after O1's straight drive: his Sprint that ends nearest the rim (down the I file when level)."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    from playmaker_engine import board as B
    spr = [a for a in legal_actions(s) if a.kind == 'sprint' and a.side == 'O' and a.piece == 0]
    a = min(spr, key=lambda a: (B.dist_rim(a.dest), abs(a.dest[0] - 8), a.dest))
    return apply(s, a), B.sq(a.dest)


def _facts(rows):
    """What happened over the play-outs of one candidate: the score, how each ended, drives that reached the key,
    and on those whether a second defender was square in front at the finish."""
    from playmaker_engine import board as B
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    ends, key, helped, rim = {}, 0, 0, 0
    for r in rows:
        x = r.get('result') or {}
        t = x.get('shot_type') or x.get('kind') or 'unfinished'
        ends[t] = ends.get(t, 0) + 1
        inside = x.get('shot_type') in ('layup', 'dunk', 'floater', 'post')
        rim += inside
        drove = any(e[2] == 'O' and e[3] in ('move', 'qs', 'sprint') and e[4] == e[8] and e[6] and B.zone(B.parse_sq(e[6])) in ('K', 'k', 'R', 'r', 'P', 'p')
                    for e in r['events'])
        if inside and r.get('endX') and x.get('shooter') is not None:
            sp = B.parse_sq(r['endO'][x['shooter']])
            sq_front = [j for j in range(5) if B.adjacent(B.parse_sq(r['endX'][j]), sp) and B.dist_rim(B.parse_sq(r['endX'][j])) < B.dist_rim(sp)
                        and r['endArrows'][j] == B.dir_between(B.parse_sq(r['endX'][j]), sp)]
            helped += bool(sq_front)
        key += drove
    return dict(n=len(rows), mean=round(m, 1), low=round(m - ci, 1), high=round(m + ci, 1), ends=ends, inside=rim, inside_square_defender=helped,
                points=[r['points'] for r in rows])


def cmd_sense(group, copies='16'):
    """Play one group of candidates out. Groups: setup, beaten, zone_setup, zone_beaten, drive, zone_drive."""
    prep = _sense()['prepared']
    zone = group.startswith('zone_')
    pz = prep['zone on' if zone else 'zone off']
    kind = group.replace('zone_', '')
    x45 = lambda x4, a4, x5, a5: (HIS[0][:3] + [x4, x5], HIS[1][:3] + [a4, a5])
    named, notes = [], {}
    if kind == 'setup':
        cands = {'his game': HIS,
                 'his game, X1 square on I10': (['I10'] + HIS[0][1:], ['N'] + HIS[1][1:]),
                 'X1 square, X4 and X5 in the lane (H5, J5)': (['I10', 'D8', 'O8', 'H5', 'J5'], ['N', 'NW', 'N', 'N', 'N']),
                 'the search, first pick (J10 E4 K7 M6 D4)': (['J10', 'E4', 'K7', 'M6', 'D4'], ['N', 'N', 'N', 'NW', 'SW']),
                 'the search, second pick (L7 D3 N3 I10 I5)': (['L7', 'D3', 'N3', 'I10', 'I5'], ['W', 'E', 'NE', 'NE', 'N']),
                 'the search at Starter (H12 N5 I7 F2 N3)': (['H12', 'N5', 'I7', 'F2', 'N3'], ['NE', 'E', 'SE', 'SW', 'SE']),
                 'his game, off-ball arrows as the search rates them': (HIS[0], pz['arrows'])}
        if not zone:
            done = ('his game', 'his game, X1 square on I10', 'X1 square, X4 and X5 in the lane (H5, J5)', 'the search, first pick (J10 E4 K7 M6 D4)',
                    'the search, second pick (L7 D3 N3 I10 I5)', 'the search at Starter (H12 N5 I7 F2 N3)')
            cands = {k: v for k, v in cands.items() if k not in done}        # played in the first look, the same dice
        else:
            cands = {k: v for k, v in cands.items() if 'second pick' not in k and 'Starter' not in k}
        if pz['arrows'] == HIS[1]:
            cands.pop('his game, off-ball arrows as the search rates them', None)
            notes['arrows'] = 'the search rates his game\'s arrows level with the best for every off-ball defender: no other candidate'
        named = [(k, shaun_state(x, a, zone=zone)) for k, (x, a) in cands.items()]
    elif kind == 'arrows':
        # the search reads every arrow of every off-ball defender level (cmd_prepare), so it names no arrow to try.
        # Shaun's question is arrows on men against arrows on passing lanes, so that pair is played: each off-ball
        # defender on his game's square, his arrow turned onto the straight line from the ball to his man
        cands = {'his game, off-ball arrows along the passing lanes (X2 N, X3 NW, X4 NE, X5 N)': (HIS[0], ['NW', 'N', 'NW', 'NE', 'N'])}
        named = [(k, shaun_state(x, a, zone=zone)) for k, (x, a) in cands.items()]
    elif kind == 'beaten':
        cands = {'X4 and X5 as in his game (B4, P2, arrows on their men)': x45('B4', 'SW', 'P2', 'NE'),
                 'X4 and X5 in the lane (H5, J5, facing the ball)': x45('H5', 'N', 'J5', 'N'),
                 'X4 and X5 as the search placed them (M6, D4)': x45('M6', 'NW', 'D4', 'SW'),
                 'X4 and X5 on his game\'s squares, arrows as the search rates them': x45('B4', pz['arrows'][3], 'P2', pz['arrows'][4])}
        if pz['arrows'][3:] == HIS[1][3:]:
            cands.pop('X4 and X5 on his game\'s squares, arrows as the search rates them')
        named = [(k, _beaten(shaun_state(x, a, zone=zone))) for k, (x, a) in cands.items()]
    elif kind == 'drive':
        sq, ar = pz['x1'].split()
        cands = {'X1 on J10, arrow on O1 (his game)': ('J10', 'NW'), 'X1 on I10, arrow on O1 (square)': ('I10', 'N'),
                 f'X1 where the search rates him best ({sq} facing {ar})': (sq, ar), 'X1 on J10 facing W (his arrow across the lane)': ('J10', 'W')}
        seen = set()
        for k, (q, d) in cands.items():
            if (q, d) in seen:
                notes[k] = 'the same placement as one above'
                continue
            seen.add((q, d))
            st, to = _drive(shaun_state([q] + HIS[0][1:], [d] + HIS[1][1:], zone=zone))
            notes[k] = f'O1 Sprints to {to}'
            named.append((k, st))
    out = play(named, copies=int(copies), zone=zone, what=f'sense check: {group}') if named else {}
    d = _sense()
    d[group] = dict(candidates={k: _facts(rows) for k, rows in out.items()}, notes=notes)
    json.dump(d, open(SENSE, 'w'), indent=1)
    json.dump({k: rows for k, rows in out.items()}, open(os.path.join(WORK, f'sense_{group}.json'), 'w'))
    for k, f in d[group]['candidates'].items():
        print(group, '|', k, '|', f['mean'], [f['low'], f['high']], f['ends'], 'inside', f['inside'], 'with a square defender in front', f['inside_square_defender'], notes.get(k, ''))


# ---- the test in two arms (part 4) ---------------------------------------------------------------------------------------

def cmd_trace(tag, n='200', level='allstar', seed='1', zone='off'):
    """Self-play at a level from the stored starts, under the app's rules; zone: 'zone' plays rules.zone on (arm B)."""
    rules = dict(T.RULES)
    if zone == 'zone':
        rules['zone'] = 'on'
    pl = G.pool()
    T.pool_is_current(pl)
    pol = L.policy(level, 2, L.profiles()[level]['noise'])
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, features=True, stances=True, boards=True,
                            policies=dict(O=pol, X=pol), rules=rules, fouls=T.FOULS)
    json.dump(dict(size=tag, rows=rows, zone=zone == 'zone'), open(os.path.join(WORK, f'trace_{tag}.json'), 'w'))
    tally(f'self-play ({tag}, {level}, {n} possessions{", zone on" if zone == "zone" else ""})', secs)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    print(tag, level, len(rows), 'possessions', round(m, 2), [round(m - ci, 2), round(m + ci, 2)], 'positions', sum(len(r['reads']) for r in rows))


INSIDE = ('layup', 'dunk', 'post', 'floater')


def _arrow_on(arrow, frm, to, zone):
    """Does a defender on frm, with this arrow, have an arrow on the player on to (the two arrows under the zone)?"""
    from playmaker_engine import geometry as GM, rules_config as RC
    rules = _arrow_on.rules.setdefault(zone, RC.with_rules(digital=True, **({'zone': 'on'} if zone else {})))
    return bool(GM.faces(rules, (8 + arrow) if zone else arrow, frm, to))


_arrow_on.rules = {}


def cmd_arm(tag):
    """One arm, player against player: every table part 4 asks for, to docs/runs/step18o/arm_<tag>.json."""
    from playmaker_engine import board as B, rules_config as RC
    CARDS, by = N._cards()
    pl = G.pool()
    tr = json.load(open(os.path.join(WORK, f'trace_{tag}.json')))
    rows, zone = tr['rows'], bool(tr.get('zone'))
    P = B.parse_sq
    card = lambda r, side, i: CARDS[by[json.dumps(pl['contexts'][r['ctx']]['off' if side == 'O' else 'dfn'][i], sort_keys=True)]]
    made = lambda s: max(0, s['rating'] - s['contest']) / 20.0
    rushed_x = lambda rx, lx, j: bool((rx >> (2 * j)) & 3) or bool((lx >> j) & 1)

    def square_on(o, x, arrows, rx, lx, i):
        """The defenders square to attacker i: next to him, in front (nearer the rim), an arrow on him. [(j, rushed)]"""
        sp = P(o[i])
        return [(j, rushed_x(rx, lx, j)) for j in range(5) if B.adjacent(P(x[j]), sp) and B.dist_rim(P(x[j])) < B.dist_rim(sp)
                and _arrow_on(arrows[j], P(x[j]), sp, zone)]

    # -- every shot
    shots = []
    for n, r in enumerate(rows):
        x = r.get('result') or {}
        if x.get('kind') not in ('shot', 'free_throws') or not x.get('shot_type'):
            continue
        i, j, t = x['shooter'], x.get('contester', -1), x['shot_type']
        c = card(r, 'O', i)
        rec = dict(row=n, shooter=c.key, role=c.role, tier=c.tier, slot=i + 1, shot=t, open=c.shot(t), rating=x['rating'], contest=x.get('contest', 0),
                   fouled=x['kind'] == 'free_throws', blocked=any(e[3] == 'contest' for e in r['events']), where='open', rushed=False, foul_rating=None,
                   own_defender=None)
        if j >= 0:
            d = card(r, 'X', j)
            dq, sp = P(r['endX'][j]), P(r['endO'][i])
            front, level = B.dist_rim(dq) < B.dist_rim(sp), B.dist_rim(dq) == B.dist_rim(sp)
            rush = rushed_x(r['endRushX'], r['endLockX'], j)
            full, less3 = max(1, d.con(t) - (2 if rush else 0)), max(1, d.con(t) - 3 - (2 if rush else 0))
            square = front and (x.get('contest') == full if full != less3 else _arrow_on(r['endArrows'][j], dq, sp, zone))
            rec.update(defender=d.key, card_contest=d.con(t), rushed=rush, foul_rating=d.r['foul_contest'], own_defender=j == i,
                       where=('square in front, ' + ('rushed' if rush else 'set')) if square else 'behind' if not front and not level else 'not square')
        shots.append(rec)
    rep = dict(run=tag, zone=zone, possessions=len(rows), shots=len(shots))
    # -- the matchup tables
    tables = {}
    for name, kinds in (('three', ('three',)), ('mid', ('mid',)), ('long', ('long',)), ('inside', INSIDE)):
        cell = {}
        for s in shots:
            if s['shot'] in kinds and not s['fouled']:
                c = cell.setdefault(str(s['open']), {}).setdefault('open' if s['where'] == 'open' else str(s['contest']), [0, 0.0])
                c[0] += 1
                c[1] += made(s)
        tables[name] = {r: {c: dict(taken=v[0], made=round(v[1], 1)) for c, v in sorted(cols.items(), key=lambda kv: (kv[0] != 'open', kv[0].zfill(2)))}
                        for r, cols in sorted(cell.items(), key=lambda kv: -int(kv[0]))}
    rep['tables'] = tables
    threes = [s for s in shots if s['shot'] == 'three']
    pos = {}
    for s in threes:
        p = pos.setdefault(s['where'], dict(taken=0, made=0.0, points=0.0))
        p['taken'] += 1
        p['made'] += made(s)
    for p in pos.values():
        p['points'] = round(3 * p['made'] / p['taken'], 2)
        p['made'] = round(p['made'], 1)
    by_open = {}
    for s in threes:
        t = by_open.setdefault(str(s['open']), dict(taken=0, contested=0, square=0))
        t['taken'] += 1
        t['contested'] += s['where'] != 'open'
        t['square'] += s['where'].startswith('square')
    rep['threes'] = dict(taken=len(threes), contested=sum(1 for s in threes if s['where'] != 'open'), by_defender_position=pos,
                         by_open_rating=dict(sorted(by_open.items(), key=lambda kv: -int(kv[0]))))
    # -- inside shots: the defender's position, the block, the fouls, by his Contest foul rating
    ins = [s for s in shots if s['shot'] in INSIDE]
    ipos, ifoul = {}, {}
    for s in ins:
        p = ipos.setdefault(s['where'], dict(shots=0, made=0.0, block_tried=0, fouled=0))
        p['shots'] += 1
        p['made'] += 0 if s['fouled'] else made(s)
        p['block_tried'] += s['blocked']
        p['fouled'] += s['fouled']
        if s['where'] not in ('open',) and not s['where'].startswith('square'):
            f = ifoul.setdefault(str(s['foul_rating']), dict(could_block=0, block_tried=0, fouled=0))
            f['could_block'] += 1
            f['block_tried'] += s['blocked']
            f['fouled'] += s['fouled']
    for p in ipos.values():
        p['made'] = round(p['made'], 1)
    rep['inside'] = dict(shots=len(ins), made=round(sum(0 if s['fouled'] else made(s) for s in ins), 1), block_tried=sum(s['blocked'] for s in ins), fouled=sum(s['fouled'] for s in ins),
                         by_position=ipos, by_contest_foul_rating=dict(sorted(ifoul.items(), key=lambda kv: int(kv[0]))),
                         by_shot={t: sum(1 for s in ins if s['shot'] == t) for t in INSIDE})
    # -- faced with a square defender on a jump-shot square: what the ball handler did, and whether it worked
    faced = dict(turns=0, first={}, after_a_move=dict(free=0, defender_rushed=0, still_square=0, ball_lost=0, passed_on=0), dribble=dict(tried=0, won=0))
    for r in rows:
        bs = [b for b in (r.get('boards') or []) if b[2] == 'O']
        for k, b in enumerate(bs):
            at, ph, side, o, x, ar, ball, rx, lx = b[:9]
            if B.zone(P(o[ball])) not in ('3', 'L', 'M'):
                continue
            sq = [j for j, rush in square_on(o, x, ar, rx, lx, ball) if not rush]
            if not sq:
                continue
            faced['turns'] += 1
            end = bs[k + 1][0] if k + 1 < len(bs) else len(r['events'])
            mine = [e for e in r['events'][at:end] if e[2] == 'O' and e[1] == 'play']
            first = next((e for e in mine if e[3] in ('shot', 'dribble', 'pass') or (e[3] in ('move', 'qs', 'sprint') and e[4] == ball)), None)
            kind = ('waited, or only others moved' if first is None else 'shot over him' if first[3] == 'shot' else 'Dribble at him' if first[3] == 'dribble'
                    else 'passed' if first[3] == 'pass' else {'move': 'Move', 'qs': 'Quick Step', 'sprint': 'Sprint'}[first[3]] + ' away')
            faced['first'][kind] = faced['first'].get(kind, 0) + 1
            if first is None or first[3] in ('shot', 'pass'):
                continue
            if first[3] == 'dribble':
                faced['dribble']['tried'] += 1
                won = next((d[1] for d in r.get('dribbles') or [] if d[2] == at + r['events'][at:end].index(first)), 0)
                faced['dribble']['won'] += won
            # what he had made of it by his own next turn (or by the end of the possession)
            nxt = bs[k + 1] if k + 1 < len(bs) else None
            x_ = r.get('result') or {}
            if nxt is None:
                if x_.get('kind') in ('steal', 'turnover_end', 'violation'):
                    faced['after_a_move']['ball_lost'] += 1
                elif x_.get('shooter') == ball:
                    s_ = next((s for s in shots if s['row'] == rows.index(r)), None) if False else None
                    w = [j for j in range(5) if r.get('endX') and B.adjacent(P(r['endX'][j]), P(r['endO'][ball])) and B.dist_rim(P(r['endX'][j])) < B.dist_rim(P(r['endO'][ball]))
                         and _arrow_on(r['endArrows'][j], P(r['endX'][j]), P(r['endO'][ball]), zone)]
                    if not w:
                        faced['after_a_move']['free'] += 1
                    elif all(rushed_x(r['endRushX'], r['endLockX'], j) for j in w):
                        faced['after_a_move']['defender_rushed'] += 1
                    else:
                        faced['after_a_move']['still_square'] += 1
                else:
                    faced['after_a_move']['passed_on'] += 1
                continue
            if nxt[6] != ball:
                faced['after_a_move']['passed_on'] += 1
                continue
            w = square_on(nxt[3], nxt[4], nxt[5], nxt[7], nxt[8], ball)
            faced['after_a_move']['free' if not w else 'defender_rushed' if all(rush for _, rush in w) else 'still_square'] += 1
    rep['faced_with_a_square_defender'] = faced
    # -- help: drives that reached the key and finished inside
    help_ = dict(drives_finished_inside=0, no_square_defender=0, his_own_defender_square=0, another_defender_square=0)
    for s in ins:
        r = rows[s['row']]
        i = (r['result'] or {})['shooter']
        drove = any(e[2] == 'O' and e[3] in ('move', 'qs', 'sprint') and e[4] == i and e[8] == i and e[6] and B.zone(P(e[6])) == 'K' for e in r['events'])
        if not drove:
            continue
        help_['drives_finished_inside'] += 1
        sp = P(r['endO'][i])
        w = [j for j in range(5) if B.adjacent(P(r['endX'][j]), sp) and B.dist_rim(P(r['endX'][j])) < B.dist_rim(sp) and _arrow_on(r['endArrows'][j], P(r['endX'][j]), sp, zone)]
        help_['another_defender_square' if any(j != i for j in w) else 'his_own_defender_square' if w else 'no_square_defender'] += 1
    # -- where the defenders of non-shooters started (a non-shooter: his three is below average on his card)
    starts = dict(non_shooters=0, next_to_his_man=0, in_the_key=0, elsewhere=0)
    setup_o, setup_x = {}, {}
    area = lambda q: {'K': 'the key', 'M': 'mid-range', 'L': 'long two', '3': 'the three-point line', '.': 'beyond the line'}[B.zone(P(q))]
    for r in rows:
        o, x = r['start']['o'], r['start']['x']
        for i in range(5):
            c = card(r, 'O', i)
            kind = c.role.split()[-2] + ' ' + c.role.split()[-1] if c.role.split()[-1] in ('Guard', 'Forward') else c.role.split()[-1]
            setup_o.setdefault(kind, {}).setdefault(area(o[i]), 0)
            setup_o[kind][area(o[i])] += 1
            d = card(r, 'X', i)
            dk = d.role.split()[-2] + ' ' + d.role.split()[-1] if d.role.split()[-1] in ('Guard', 'Forward') else d.role.split()[-1]
            where = 'next to his man' if B.adjacent(P(x[i]), P(o[i])) else 'in the key' if B.zone(P(x[i])) == 'K' else 'elsewhere'
            setup_x.setdefault(dk, {}).setdefault(where, 0)
            setup_x[dk][where] += 1
            if c.bands['shot_three'] == 'L':
                starts['non_shooters'] += 1
                starts[where.replace(' ', '_')] += 1
    rep['help'] = dict(finishes=help_, defenders_of_non_shooters_at_the_start=starts)
    rep['setup'] = dict(offence=setup_o, defence=setup_x)
    # -- arrows off the ball, at every defence turn
    arrows = dict(at_his_man=0, at_the_ball_handler=0, along_a_passing_lane=0, toward_the_rim=0, other=0)
    rimsq = P('I2')
    for r in rows:
        for b in (r.get('boards') or []):
            if b[2] != 'X':
                continue
            o, x, ar, ball = b[3], b[4], b[5], b[6]
            for j in range(5):
                if j == ball:
                    continue
                q, a = P(x[j]), ar[j]
                ray = [B.add(q, (B.DIRS[a][0] * k, B.DIRS[a][1] * k)) for k in range(1, 7)]
                lane = set()
                for i in range(5):
                    if i != ball:
                        p0, p1 = P(o[ball]), P(o[i])
                        nn = max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))
                        lane |= {(round(p0[0] + (p1[0] - p0[0]) * t / nn), round(p0[1] + (p1[1] - p0[1]) * t / nn)) for t in range(1, nn)}
                if P(o[j]) in ray[:3] or a == B.nearest_dir(q, P(o[j])):
                    arrows['at_his_man'] += 1
                elif P(o[ball]) in ray or a == B.nearest_dir(q, P(o[ball])):
                    arrows['at_the_ball_handler'] += 1
                elif any(z in lane for z in ray[:3]):
                    arrows['along_a_passing_lane'] += 1
                elif a == B.nearest_dir(q, rimsq):
                    arrows['toward_the_rim'] += 1
                else:
                    arrows['other'] += 1
    inter = sum(1 for r in rows for e in r['events'] if e[3] == 'intercept')
    won = sum(1 for r in rows if r['events'] and r['events'][-1][3] == 'intercept' and (r.get('result') or {}).get('kind') in ('turnover_end', 'intercept', 'steal'))
    passes = sum(1 for r in rows for e in r['events'] if e[3] == 'pass')
    rep['arrows_off_the_ball'] = dict(defender_turns=arrows, passes=passes, intercepts_tried=inter, intercepts_won=won,
                                      pass_turnovers=sum(1 for r in rows if (r.get('result') or {}).get('kind') == 'turnover_end' and r['events'] and r['events'][-1][3] in ('pass', 'intercept')))
    kinds = {}
    for s in shots:
        g = 'threes' if s['shot'] == 'three' else 'rim shots (layup, dunk)' if s['shot'] in ('layup', 'dunk') else 'other twos'
        kinds[g] = kinds.get(g, 0) + 1
    rep['shot_mix'] = kinds
    json.dump(dict(rep, every_shot=shots), open(os.path.join(RUN, f'arm_{tag}.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'tables'}, indent=1))
    for name, tb in rep['tables'].items():
        print('==', name)
        for rr, cols in tb.items():
            print('  open', rr, '|', ' '.join(f"{c}: {v['taken']} ({v['made']})" for c, v in cols.items()))


if __name__ == '__main__':
    cmd = sys.argv[1]
    fn = globals().get('cmd_' + cmd) or getattr(N, 'cmd_' + cmd)
    fn(*sys.argv[2:])
