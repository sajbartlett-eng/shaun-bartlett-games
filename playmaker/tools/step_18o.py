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
    elif kind == 'beaten_drive':
        # after the beat the computer's offence did not drive (it stepped to the side), so the drive itself is played:
        # the beaten X1 reaches and misses (what the defence did 16 times in 16), then O1 takes his straight drive, or
        # the offence plays on as it chooses. With X4 and X5 next to their men, and in the lane.
        from playmaker_engine.actions import legal_actions
        from playmaker_engine.resolve import apply, ChanceNode
        for label, (x, a) in {'X4 and X5 as in his game': x45('B4', 'SW', 'P2', 'NE'), 'X4 and X5 in the lane (H5, J5)': x45('H5', 'N', 'J5', 'N')}.items():
            st = _beaten(shaun_state(x, a, zone=zone))
            n = apply(st, next(z for z in legal_actions(st) if z.kind == 'steal' and z.piece == 0))
            fouls = st.fouls
            while isinstance(n, ChanceNode):          # the reach misses, no foul: the outcome that plays on with no foul added
                n = next(sub for p_, lab, sub in n.outcomes if isinstance(sub, ChanceNode) or (sub.stage != 'over' and sub.fouls == fouls))
            st = n
            while st.side == 'X' and st.stage == 'play':
                st = apply(st, next(z for z in legal_actions(st) if z.kind in ('pause', 'end_turn')))
                if isinstance(st, ChanceNode):
                    raise SystemExit('a roll where none was expected')
            drv, to = _drive(st)
            named.append((f'{label}: the offence plays on as it chooses', st))
            named.append((f'{label}: O1 drives', drv))
            notes[f'{label}: O1 drives'] = f'O1 Sprints to {to}'
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
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, features=True, stances=True, boards=tag.startswith('arm'),
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


def cmd_armtable(*tags):
    """The arms' tables for the report, as markdown (docs/runs/step18o/arm_tables.md)."""
    arms = [json.load(open(os.path.join(RUN, f'arm_{t}.json'))) for t in tags]
    names = ['Arm A (zone off)', 'Arm B (zone on)'][:len(arms)]
    out = []
    pct = lambda a, b: f'{round(100 * a / b)} in 100' if b else 'none'
    for nm, a in zip(names, arms):
        out.append(f'**{nm}: every three, shooter against the contest that counted.** Each cell: taken (made).\n')
        cols = ['open'] + [str(c) for c in range(1, 9)]
        used = [c for c in cols if any(c in row for row in a['tables']['three'].values())]
        out.append('| The shooter\'s open three | ' + ' | '.join('Open' if c == 'open' else f'Contest {c}' for c in used) + ' | All |')
        out.append('|---' * (len(used) + 2) + '|')
        tot = {c: [0, 0.0] for c in used}
        for r, row in a['tables']['three'].items():
            cells = []
            for c in used:
                v = row.get(c)
                cells.append(f"{v['taken']} ({v['made']})" if v else '')
                if v:
                    tot[c][0] += v['taken']
                    tot[c][1] += v['made']
            out.append(f"| {r} | " + ' | '.join(cells) + f" | {sum(v['taken'] for v in row.values())} ({round(sum(v['made'] for v in row.values()), 1)}) |")
        out.append('| **All** | ' + ' | '.join(f'{tot[c][0]} ({round(tot[c][1], 1)})' for c in used) + f" | {sum(v[0] for v in tot.values())} ({round(sum(v[1] for v in tot.values()), 1)}) |")
        out.append('')
        for kind, label in (('mid', 'mid-range shots'), ('long', 'long twos')):
            n = sum(v['taken'] for row in a['tables'][kind].values() for v in row.values())
            out.append(f'- **{nm}, {label}:** {n} taken' + ('.' if not n else ': ' + '; '.join(f"open rating {r}: " + ', '.join(f"{'open' if c == 'open' else 'contest ' + c} {v['taken']} ({v['made']})" for c, v in row.items()) for r, row in a['tables'][kind].items()) + '.'))
        out.append('')
    out.append('**Contested threes, by where the defender stood.** Taken, and points a shot.\n')
    out.append('| The defender | ' + ' | '.join(names) + ' |')
    out.append('|---' * (len(arms) + 1) + '|')
    for k, lab in (('square in front, set', 'Square in front, set'), ('square in front, rushed', 'Square in front, rushed'), ('not square', 'Not square (in front with his arrow off, or beside)'), ('behind', 'Behind'), ('open', 'Nobody: open')):
        out.append(f'| {lab} | ' + ' | '.join((lambda p: f"{p['taken']}, {p['points']} a shot" if p else '0')(a['threes']['by_defender_position'].get(k)) for a in arms) + ' |')
    out.append('')
    out.append('**Threes by the shooter\'s open rating.** Taken, contested, and over a square defender.\n')
    out.append('| Open three | ' + ' | '.join(names) + ' |')
    out.append('|---' * (len(arms) + 1) + '|')
    for r in sorted({r for a in arms for r in a['threes']['by_open_rating']}, key=lambda x: -int(x)):
        out.append(f'| {r} | ' + ' | '.join((lambda t: f"{t['taken']} taken, {t['contested']} contested, {t['square']} over a square defender" if t else '0')(a['threes']['by_open_rating'].get(r)) for a in arms) + ' |')
    out.append('')
    out.append('**Faced with a square, set defender on a jump-shot square, at the start of his turn.**\n')
    out.append('| | ' + ' | '.join(names) + ' |')
    out.append('|---' * (len(arms) + 1) + '|')
    out.append('| Turns it happened, in 200 possessions | ' + ' | '.join(str(a['faced_with_a_square_defender']['turns']) for a in arms) + ' |')
    firsts = sorted({k for a in arms for k in a['faced_with_a_square_defender']['first']})
    for k in firsts:
        out.append(f'| First: {k} | ' + ' | '.join(str(a['faced_with_a_square_defender']['first'].get(k, 0)) for a in arms) + ' |')
    out.append('| His Dribble at him: tried, won | ' + ' | '.join(f"{a['faced_with_a_square_defender']['dribble']['tried']}, {a['faced_with_a_square_defender']['dribble']['won']}" for a in arms) + ' |')
    for k, lab in (('free', 'After his move: no square defender on him'), ('defender_rushed', 'After his move: a square defender, but rushed'), ('still_square', 'After his move: still square and set'),
                   ('passed_on', 'After his move: he gave the ball up'), ('ball_lost', 'After his move: the ball was lost')):
        out.append(f'| {lab} | ' + ' | '.join(str(a['faced_with_a_square_defender']['after_a_move'][k]) for a in arms) + ' |')
    out.append('')
    out.append('**Inside shots, by where the defender stood.** Shots, the makes the cards give, the block tried, fouls.\n')
    out.append('| The defender | ' + ' | '.join(names) + ' |')
    out.append('|---' * (len(arms) + 1) + '|')
    for k, lab in (('square in front, set', 'Square in front, set'), ('square in front, rushed', 'Square in front, rushed'), ('not square', 'Not square'), ('behind', 'Behind'), ('open', 'Nobody: open')):
        out.append(f'| {lab} | ' + ' | '.join((lambda p: f"{p['shots']} shots, {p['made']} made ({pct(p['made'], p['shots'])}), block {p['block_tried']}, fouls {p['fouled']}" if p else '0')(a['inside']['by_position'].get(k)) for a in arms) + ' |')
    out.append('| **All** | ' + ' | '.join(f"{a['inside']['shots']} shots, {a['inside']['made']} made ({pct(a['inside']['made'], a['inside']['shots'])}), block {a['inside']['block_tried']}, fouls {a['inside']['fouled']}" for a in arms) + ' |')
    out.append('')
    out.append('**The block, by the defender\'s Contest foul rating** (inside shots where he wasn\'t square, so he could go for it): could, tried, fouled.\n')
    out.append('| Contest foul rating | ' + ' | '.join(names) + ' |')
    out.append('|---' * (len(arms) + 1) + '|')
    for r in sorted({r for a in arms for r in a['inside']['by_contest_foul_rating']}, key=int):
        out.append(f'| {r} | ' + ' | '.join((lambda f: f"{f['could_block']}, {f['block_tried']}, {f['fouled']}" if f else '0')(a['inside']['by_contest_foul_rating'].get(r)) for a in arms) + ' |')
    out.append('')
    out.append('**Help: drives that reached the key and finished inside.**\n')
    out.append('| At the finish | ' + ' | '.join(names) + ' |')
    out.append('|---' * (len(arms) + 1) + '|')
    for k, lab in (('drives_finished_inside', 'Drives finished inside'), ('no_square_defender', 'No defender square in front'), ('his_own_defender_square', 'Only his own defender square in front'), ('another_defender_square', 'Another defender square in front (help)')):
        out.append(f'| {lab} | ' + ' | '.join(str(a['help']['finishes'][k]) for a in arms) + ' |')
    st = arms[0]['help']['defenders_of_non_shooters_at_the_start']
    out.append('')
    out.append(f"**Where the defenders of non-shooters started** (a non-shooter: his three is below average on his card; the starts are the same in both arms): of {st['non_shooters']}, "
               f"{st['next_to_his_man']} next to their man, {st['in_the_key']} in the key, {st['elsewhere']} elsewhere.\n")
    so, sx = arms[0]['setup']['offence'], arms[0]['setup']['defence']
    merge = lambda d: {('Point Guard' if k == 'Combo Guard' else 'Small Forward' if k == 'Wing' else k): v for k, v in d.items()}
    def fold(d):
        o = {}
        for k, v in d.items():
            k2 = 'Point Guard' if k == 'Combo Guard' else 'Small Forward' if k == 'Wing' else k
            for a_, n in v.items():
                o.setdefault(k2, {})[a_] = o.setdefault(k2, {}).get(a_, 0) + n
        return o
    so, sx = fold(so), fold(sx)
    areas = ['beyond the line', 'the three-point line', 'long two', 'mid-range', 'the key']
    out.append('**Setup: where each type started, on offence.**\n')
    out.append('| Type | ' + ' | '.join(x[0].upper() + x[1:] for x in areas) + ' |')
    out.append('|---' * (len(areas) + 1) + '|')
    for t in ('Point Guard', 'Shooting Guard', 'Small Forward', 'Power Forward', 'Centre'):
        out.append(f'| {t} | ' + ' | '.join(str(so.get(t, {}).get(x, 0)) for x in areas) + ' |')
    out.append('')
    out.append('**Setup: where each type started, on defence.**\n')
    out.append('| Type | Next to his man | In the key | Elsewhere |')
    out.append('|---|---|---|---|')
    for t in ('Point Guard', 'Shooting Guard', 'Small Forward', 'Power Forward', 'Centre'):
        out.append(f"| {t} | {sx.get(t, {}).get('next to his man', 0)} | {sx.get(t, {}).get('in the key', 0)} | {sx.get(t, {}).get('elsewhere', 0)} |")
    out.append('')
    out.append('**Arrows off the ball, at every defence turn.**\n')
    out.append('| The off-ball defender\'s arrow pointed | ' + ' | '.join(names) + ' |')
    out.append('|---' * (len(arms) + 1) + '|')
    for k, lab in (('at_his_man', 'At his man'), ('at_the_ball_handler', 'At the ball handler'), ('along_a_passing_lane', 'Along a passing lane'), ('toward_the_rim', 'Toward the rim'), ('other', 'Somewhere else')):
        out.append(f'| {lab} | ' + ' | '.join((lambda d: f"{d[k]} ({pct(d[k], sum(d.values()))})")(a['arrows_off_the_ball']['defender_turns']) for a in arms) + ' |')
    out.append('| Passes thrown | ' + ' | '.join(str(a['arrows_off_the_ball']['passes']) for a in arms) + ' |')
    out.append('| Intercepts tried | ' + ' | '.join(str(a['arrows_off_the_ball']['intercepts_tried']) for a in arms) + ' |')
    out.append('| Intercepts won | ' + ' | '.join(str(a['arrows_off_the_ball']['intercepts_won']) for a in arms) + ' |')
    open(os.path.join(RUN, 'arm_tables.md'), 'w').write('\n'.join(out) + '\n')
    print('\n'.join(out))


def cmd_sensetable():
    """The sense checks as tables for the report (docs/runs/step18o/sense_tables.md), recounted from the kept rows:
    how each candidate's 16 possessions ended, and at inside finishes whether a defender was square in front."""
    from playmaker_engine import board as B
    P = B.parse_sq
    d = _sense()
    out = []
    order = ['setup', 'arrows', 'beaten', 'beaten_drive', 'drive', 'zone_setup', 'zone_arrows', 'zone_beaten', 'zone_drive']
    for g in order:
        if g not in d:
            continue
        zone = g.startswith('zone_')
        rows_of = json.load(open(os.path.join(WORK, f'sense_{g}.json'))) if os.path.exists(os.path.join(WORK, f'sense_{g}.json')) else {}
        out.append(f'### {g}\n')
        out.append('| Candidate | Points a possession | Threes | Inside shots | Other twos | Ball lost | Fouled | Inside finishes with a square defender in front |')
        out.append('|---|---|---|---|---|---|---|---|')
        for name, f in d[g]['candidates'].items():
            e = f['ends']
            ins = sum(e.get(t, 0) for t in INSIDE)
            sq = ''
            if name in rows_of:
                k = 0
                for r in rows_of[name]:
                    x = r.get('result') or {}
                    if x.get('shot_type') in INSIDE and r.get('endX'):
                        sp = P(r['endO'][x['shooter']])
                        k += any(B.adjacent(P(r['endX'][j]), sp) and B.dist_rim(P(r['endX'][j])) < B.dist_rim(sp) and _arrow_on(r['endArrows'][j], P(r['endX'][j]), sp, zone) for j in range(5))
                sq = f'{k} of {ins}'
                f['inside_square_defender'] = k
            note = d[g].get('notes', {}).get(name, '')
            out.append(f"| {name}{' (' + note + ')' if note else ''} | {f['mean']} ({f['low']} to {f['high']}) | {e.get('three', 0)} | {ins} | {e.get('mid', 0) + e.get('long', 0)} | "
                       f"{e.get('turnover_end', 0) + e.get('steal', 0) + e.get('violation', 0)} | {e.get('free_throws', 0)} | {sq or 'not kept'} |")
        out.append('')
    json.dump(d, open(SENSE, 'w'), indent=1)
    open(os.path.join(RUN, 'sense_tables.md'), 'w').write('\n'.join(out))
    print('\n'.join(out))


def cmd_firstlook():
    """The six placements played before the sense tool was written (the same dice, 16 each): their scores and how
    each possession ended, added to the 'setup' group. The rows themselves were not kept."""
    pts = json.load(open(os.path.join(RUN, 'first_look_points.json')))
    ends = {'his game': {'turnover_end': 3, 'layup': 4, 'three': 7, 'free_throws': 1, 'post': 1},
            'X1 square, rest his': {'three': 9, 'layup': 2, 'turnover_end': 4, 'post': 1},
            'X1 square, X4 X5 in the lane': {'three': 10, 'turnover_end': 2, 'post': 1, 'layup': 2, 'floater': 1},
            'search A (J10N E4N K7N M6NW D4SW)': {'layup': 7, 'post': 1, 'floater': 1, 'three': 7},
            'search B (L7W D3E N3NE I10NE I5N)': {'three': 8, 'layup': 4, 'post': 2, 'turnover_end': 2},
            'starter junk (H12NE N5E I7SE F2SW N3SE)': {'three': 13, 'layup': 2, 'floater': 1}}
    names = {'his game': 'his game', 'X1 square, rest his': 'his game, X1 square on I10', 'X1 square, X4 X5 in the lane': 'X1 square, X4 and X5 in the lane (H5, J5)',
             'search A (J10N E4N K7N M6NW D4SW)': 'the search, first pick (J10 E4 K7 M6 D4)', 'search B (L7W D3E N3NE I10NE I5N)': 'the search, second pick (L7 D3 N3 I10 I5)',
             'starter junk (H12NE N5E I7SE F2SW N3SE)': 'the search at Starter (H12 N5 I7 F2 N3)'}
    d = _sense()
    g = d.setdefault('setup', dict(candidates={}, notes={}))
    for k, p in pts.items():
        m, sd, ci = L.mean_ci(p)
        g['candidates'][names[k]] = dict(n=len(p), mean=round(m, 1), low=round(m - ci, 1), high=round(m + ci, 1), ends=ends[k], points=p, first_look=True)
    json.dump(d, open(SENSE, 'w'), indent=1)
    for k, f in g['candidates'].items():
        print(k, f['mean'], [f['low'], f['high']], f['ends'])


def cmd_speed(rounds='2'):
    """D-161: step 18n's code (on the cards it had) and this step's, timed in turn."""
    import subprocess
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18n as N; "
            "print('RESULT ' + json.dumps(N.T._timed({}, N.T.RULES)))")
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18n/playmaker', capture_output=True, text=True, check=True,
                             env=dict(os.environ, SENSE_RUN='step18n', SENSE_18N='1')).stdout
        one = {'18n': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18o'] = T._timed({}, T.RULES)
        if r == 0:
            one['18o, zone on'] = T._timed({}, dict(T.RULES, zone='on'))        # arm B's rules, once
        tally(f'speed, round {r + 1} (one core)', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair; each round times step 18n's code and this step's", rounds=rep),
                  open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


def cmd_setuptime(n='12'):
    """Setup time against its budget (game._setup_budget in the app's format: 0.4 of a decision's time), each level,
    both sides: the setup as it was (the default) and the search (off), with the JavaScript engine as in the app."""
    from playmaker_engine import agent as AG, board as B
    from playmaker_engine.jsbridge import NodeEngine
    NodeEngine().install()
    src = stored_starts()[:: max(1, len(stored_starts()) // int(n))][:int(n)]
    out, t0 = {}, time.time()
    for level in ('rookie', 'starter', 'allstar'):
        budget = AG.profile(level)['time_budget_s'] * 0.4
        for search in (False, True):
            to, tx = [], []
            for k, (off, dfn, s) in enumerate(src):
                make = maker(off, dfn)
                mem_o, mem_x = {}, {}
                a = time.time()
                ro = AG.propose_offence(make, 77 + k, budget=budget, level=level, memory=mem_o, search=search)
                b = time.time()
                AG.propose_defence(make, ro['squares'], ro['ball'], 78 + k, budget=budget, level=level, memory=mem_x, search=search)
                to.append(b - a)
                tx.append(time.time() - b)
            out[f'{level}, {"the search" if search else "as it was"}'] = dict(budget=budget, offence_median=round(sorted(to)[len(to) // 2], 3), offence_slowest=round(max(to), 3),
                                                                             defence_median=round(sorted(tx)[len(tx) // 2], 3), defence_slowest=round(max(tx), 3))
            print(level, 'search' if search else 'as it was', out[f'{level}, {"the search" if search else "as it was"}'], flush=True)
    tally('one core: setup time against its budget', time.time() - t0)
    json.dump(out, open(os.path.join(RUN, 'setup_time.json'), 'w'), indent=1)


if __name__ == '__main__':
    cmd = sys.argv[1]
    fn = globals().get('cmd_' + cmd) or getattr(N, 'cmd_' + cmd)
    fn(*sys.argv[2:])
