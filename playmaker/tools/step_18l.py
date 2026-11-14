"""Step 18l: off balance (D-185), the refit on the new cards (D-184, D-186), and the check against real FIBA basketball.

  python3 tools/step_18l.py trace <tag> <n> <level> [seed] [k=v ...]   self-play at a level under the app's rules and the
                                                                        default foul situation, every action kept;
                                                                        off_balance=off plays without the rule
  python3 tools/step_18l.py maps <write|no> level=tag[,tag] ...         the calibrated map per level, as in step 18h
  python3 tools/step_18l.py fouls <tag> [write]                         the two numbers that price a foul, from a run
  python3 tools/step_18l.py measures <tag> [<tag> ...]                  the measures of each run, the FIBA figures included
  python3 tools/step_18l.py h2h <tag> <pairs> <a k=v,..> <b k=v,..>     a head to head
  python3 tools/step_18l.py speed [rounds] [k=v ...]                    the time to finish 1 pair: 18k's code and this step's
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('SENSE_RUN', 'step18l')
os.environ.setdefault('SENSE_18L', '1')
import step_18k as K                                   # noqa: E402
S, L, G, J, RUN, WORK, tally = K.S, K.L, K.G, K.J, K.RUN, K.WORK, K.tally
RULES = dict(K.RULES, off_balance='on')
FOULS = K.FOULS
ROOT = os.path.dirname(HERE)


def pool_is_current(pl):
    """The pool (docs/runs/step18/pools.json, not kept in the repository) holds its own copy of each card as it was
    when the pool was made. This step's first runs played on a pool copied from the last step's folder, made before
    D-184, so they played the old cards. A pool is only played if every card in it is a card as it is now; rebuild
    one with: python3 tools/step_18.py pools"""
    from playmaker_engine.cards import CARDS
    from playmaker_engine.jsbridge import card_json
    now = {json.dumps(card_json(c), sort_keys=True) for c in CARDS.values()}
    stale = sum(1 for c in pl['contexts'] for side in ('off', 'dfn') for card in c[side] if json.dumps(card, sort_keys=True) not in now)
    if stale:
        raise SystemExit(f'the pool holds {stale} cards that are not the cards as they are now: rebuild it with "python3 tools/step_18.py pools"')


def cmd_trace(tag, n='200', level='allstar', seed='1', *switches):
    sw = S._switches(switches) if switches else {}
    rules = dict(RULES)
    if 'off_balance' in sw:
        rules['off_balance'] = sw.pop('off_balance')
    pl = G.pool()
    pool_is_current(pl)
    pol = L.policy(level, 2, L.profiles()[level]['noise'], **sw)
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, features=True, stances=True,
                            policies=dict(O=pol, X=pol), rules=rules, fouls=FOULS)
    json.dump(dict(size=tag, rows=rows), open(os.path.join(WORK, f'trace_{tag}.json'), 'w'))
    tally(f'self-play ({tag}, {level}, {n} possessions)', secs)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    print(tag, level, len(rows), 'possessions', round(m, 2), [round(m - ci, 2), round(m + ci, 2)], 'positions', sum(len(r['reads']) for r in rows))


def cmd_maps(write='no', *sources):
    """Step 18h's fit, on this step's runs: level=tag[,tag] names the trace files. First the one shared map (the
    'calibration' block: the line a level borrows where it has too few positions of its own) from all the runs
    together, so no borrowed line is left from the cards before D-184 where this step's play can fit one."""
    import hashlib
    import numpy as np
    import step_18h as H
    H.RUN, H.WORK = RUN, WORK
    named = [a.split('=')[0] + '=' + ','.join(f'trace_{t}.json' for t in a.split('=')[1].split(',')) for a in sources]
    files = [f for a in named for f in a.split('=')[1].split(',')]
    g, ph, y, hand, side, n = H.map_rows(files)
    maps, _ = L.fit_maps('linear', ph, side, hand, y, np.ones(len(y), bool))
    body = json.load(open(L.WEIGHTS))
    fresh = sorted(k for k, m in maps.items() if m.get('positions', 0) >= H.MIN_POSITIONS)
    old = sorted(k for k in body['calibration']['maps'] if k not in fresh)
    print('the shared map:', len(y), 'positions from', n, 'possessions; refitted', fresh, '| kept from before D-184 (too few positions)', old)
    if write != 'no':
        for k in fresh:
            body['calibration']['maps'][k] = maps[k]
        for k in old:
            body['calibration']['maps'][k] = dict(body['calibration']['maps'][k], from_before_d184=True)
        body['calibration']['fitted_on'] = dict(runs=[os.path.basename(f) for f in files], possessions=n, positions=int(len(y)))
        body.pop('hash', None)
        body['hash'] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        json.dump(body, open(L.WEIGHTS, 'w'), indent=1)
    H.cmd_maps(write, *named)


def cmd_fouls(tag, write='no'):
    """The two numbers that price a foul over the quarter: the defence's fouls a possession, and what a possession is
    worth, from a self-play run."""
    rows = [r for t in tag.split(',') for r in json.load(open(os.path.join(WORK, f'trace_{t}.json')))['rows']]
    f = L.mean_ci([r.get('fouls', 0) for r in rows]); p = L.mean_ci([r['points'] for r in rows])
    rep = dict(run=tag, possessions=len(rows), fouls_per_possession=round(f[0], 2), fouls_interval=[round(f[0] - f[2], 2), round(f[0] + f[2], 2)],
               play_on_value=round(p[0], 1), value_interval=[round(p[0] - p[2], 1), round(p[0] + p[2], 1)])
    print(json.dumps(rep))
    json.dump(rep, open(os.path.join(RUN, 'foul_numbers.json'), 'w'), indent=1)
    if write == 'write':
        path = os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')
        cfg = json.load(open(path))
        cfg['eval']['fouls_per_possession'], cfg['eval']['play_on_value'] = rep['fouls_per_possession'], rep['play_on_value']
        json.dump(cfg, open(path, 'w'), indent=2)
        print('wrote', path)


def _sq(sq):
    return 'ABCDEFGHIJKLMNOPQ'.index(sq[0]), int(sq[1:])


def _rim(sq):
    x, y = _sq(sq)
    return max(abs(x - 8), abs(y - 2))


def cmd_measures(*tags):
    """Step 18k's measures, and the figures set beside real FIBA basketball: turnovers, steals, steal tries and fouls,
    shooting fouls, hard contests ("blocks" has no like in the game: reported as shots a hard contest took to nothing),
    points a possession; and the off-balance tests read from the actions."""
    K.cmd_measures(*tags)
    rep = json.load(open(os.path.join(RUN, 'measures.json')))
    P = K._per100
    for tag in tags:
        rows = json.load(open(os.path.join(WORK, f'trace_{tag}.json')))['rows']
        n = len(rows)
        res = [r.get('result') or {} for r in rows]
        steal_end = lambda r, x: x.get('kind') in ('turnover_end', 'steal') and not x.get('violation') and r['events'] and r['events'][-1][3] == 'steal'
        turnovers = sum(1 for x in res if x.get('kind') in ('turnover_end', 'steal'))
        steals = sum(1 for r, x in zip(rows, res) if steal_end(r, x))
        icpt = sum(1 for r, x in zip(rows, res) if x.get('kind') == 'turnover_end' and not x.get('violation') and r['events'] and r['events'][-1][3] == 'intercept')
        tries = sum(1 for r in rows for e in r['events'] if e[3] == 'steal')
        sfouls = sum(r.get('fouls', 0) - (1 if (x.get('kind') == 'free_throws' and x.get('shot_type')) else 0) for r, x in zip(rows, res))
        shots = [x for x in res if x.get('kind') in ('shot', 'free_throws') and x.get('shot_type')]
        rim = [x for x in shots if x.get('shot_type') in ('layup', 'dunk')]
        threes = [x for x in shots if x.get('points') == 3]
        twos = [x for x in shots if x.get('points') == 2]
        fouled = lambda xs: sum(1 for x in xs if x.get('kind') == 'free_throws')
        ft_trips = sum(1 for x in res if x.get('kind') == 'free_throws')
        pts = L.mean_ci([r['points'] / 20.0 for r in rows])
        share = lambda k, m: J._share(k, m)
        fiba = dict(
            turnovers_per_possession=P(turnovers, n), live_ball=P(steals + icpt, n),
            steals_per_possession=P(steals + icpt, n), steals_from_a_reach=P(steals, n), steals_from_an_intercept=P(icpt, n),
            steal_attempts_per_possession=P(tries, n), fouls_on_a_steal_per_possession=P(sfouls, n),
            shooting_fouls_on_threes=share(fouled(threes), len(threes)), shooting_fouls_at_the_rim=share(fouled(rim), len(rim)),
            free_throw_trips=P(ft_trips, n),
            twos_taken_to_nothing_by_a_hard_contest=share(sum(1 for x in twos if x.get('kind') == 'shot' and not x.get('soft') and x.get('contester', -1) >= 0 and x.get('shot_value', 1) == 0), len(twos)),
            points_per_possession=dict(mean=round(pts[0], 3), interval=[round(pts[0] - pts[2], 3), round(pts[0] + pts[2], 3)]),
            shots=dict(threes=len(threes), rim=len(rim), other_twos=len(twos) - len(rim)))
        rep[tag]['fiba'] = fiba
        rep[tag]['off_balance'] = _off_balance(rows)
        print('==', tag, 'beside FIBA')
        for k, v in fiba.items():
            print('  ', k, json.dumps(v))
        print('   off balance:', json.dumps(rep[tag]['off_balance']))
    json.dump(rep, open(os.path.join(RUN, 'measures.json'), 'w'), indent=1)


def _off_balance(rows):
    """From each possession's record of its Dribbles ([phase, won, place, how the ball handler stood (0 set, 1 after a
    Quick Step, 2 after a Sprint), whether he was locked, the same two for the defender, the roll's chance by the
    rules]) and its Steals ([phase, place, defender, how the ball handler stood, whether he was locked, how the
    defender stood, the outcome, the chance of winning the ball])."""
    names = ('all', 'both_set', 'at_a_set_defender', 'at_a_rushed_defender', 'at_a_defender_who_sprinted', 'at_a_defender_who_quick_stepped',
             'at_a_locked_defender', 'by_a_set_ball_handler', 'by_a_rushed_ball_handler', 'by_a_ball_handler_who_sprinted',
             'set_ball_handler_at_a_rushed_defender', 'rushed_ball_handler_at_a_set_defender')
    d = {k: [0, 0, 0.0] for k in names}
    snames = ('all', 'on_a_set_ball_handler', 'on_a_rushed_ball_handler', 'on_a_ball_handler_who_sprinted', 'by_a_set_defender', 'by_a_rushed_defender')
    st = {k: [0, 0, 0, 0.0] for k in snames}
    after = dict(steals_missed_or_fouled_with_play_going_on=0, offence_acts_again_that_phase=0, next_offence_action={}, shoots_next=0, shoots_later_that_phase=0,
                 ball_handler_moves_nearer_the_rim_next=0, drives_at_that_defender_next=0, drives_at_that_defender_later_that_phase=0, drives_at_him_won=[0, 0])
    for r in rows:
        ev = r['events']
        for x in r.get('dribbles') or []:
            if len(x) < 8 or x[7] >= 1:                    # a defender this ball handler had already beaten: no roll
                continue
            won, ro, lo, rx, lx, pr = x[1], x[3], x[4], x[5], x[6], x[7]
            ro_, rx_ = bool(ro or lo), bool(rx or lx)
            for name, cond in (('all', True), ('both_set', not ro_ and not rx_), ('at_a_set_defender', not rx_), ('at_a_rushed_defender', rx_),
                               ('at_a_defender_who_sprinted', rx == 2), ('at_a_defender_who_quick_stepped', rx == 1), ('at_a_locked_defender', bool(lx)),
                               ('by_a_set_ball_handler', not ro_), ('by_a_rushed_ball_handler', ro_), ('by_a_ball_handler_who_sprinted', ro == 2),
                               ('set_ball_handler_at_a_rushed_defender', rx_ and not ro_), ('rushed_ball_handler_at_a_set_defender', ro_ and not rx_)):
                if cond:
                    d[name][0] += 1; d[name][1] += won; d[name][2] += pr
        for x in r.get('steals') or []:
            ph, at, j, ro, lo, rx, out = x[:7]
            pr = x[7] if len(x) > 7 else 0.0
            for name, cond in (('all', True), ('on_a_set_ball_handler', not ro and not lo), ('on_a_rushed_ball_handler', bool(ro or lo)), ('on_a_ball_handler_who_sprinted', ro == 2),
                               ('by_a_set_defender', not rx), ('by_a_rushed_defender', bool(rx))):
                if cond:
                    st[name][0] += 1; st[name][1] += out == 'won'; st[name][2] += out == 'foul'; st[name][3] += pr
            if out == 'won' or at + 1 >= len(ev):
                continue
            after['steals_missed_or_fouled_with_play_going_on'] += 1
            rest = [(k, e) for k, e in enumerate(ev) if k > at and e[0] == ph and e[2] == 'O' and e[3] not in ('end_turn', 'pause')]
            if not rest:
                continue
            after['offence_acts_again_that_phase'] += 1
            k0, e0 = rest[0]
            kind = e0[3]
            after['next_offence_action'][kind] = after['next_offence_action'].get(kind, 0) + 1
            after['shoots_next'] += kind in ('shot', 'forced_shot')
            after['shoots_later_that_phase'] += any(e[3] in ('shot', 'forced_shot') for _k, e in rest)
            if kind in ('move', 'qs', 'sprint') and e0[4] == e0[8] and e0[5] and e0[6] and _rim(e0[6]) < _rim(e0[5]):
                after['ball_handler_moves_nearer_the_rim_next'] += 1
            at_him = [(k, e) for k, e in rest if e[3] == 'dribble' and e[7] == j]
            if at_him:
                after['drives_at_that_defender_later_that_phase'] += 1
                if at_him[0][0] == k0:
                    after['drives_at_that_defender_next'] += 1
                dr = next((y for y in r.get('dribbles') or [] if len(y) >= 7 and y[2] == at_him[0][0]), None)
                if dr is not None:
                    after['drives_at_him_won'][0] += 1; after['drives_at_him_won'][1] += dr[1]
    sh = lambda w, m: J._share(w, m) if m else None
    return dict(drives={k: dict(drives=m, won=w, share=sh(w, m), chance_by_the_rules=round(100 * pr / m, 1) if m else None) for k, (m, w, pr) in d.items()},
                steals={k: dict(tried=m, won=w, fouled=f, won_share=sh(w, m), foul_share=sh(f, m), chance_by_the_rules=round(100 * pr / m, 1) if m else None)
                        for k, (m, w, f, pr) in st.items()},
                after_a_steal_that_missed=dict(after, drives_at_him_won=dict(drives=after['drives_at_him_won'][0], won=after['drives_at_him_won'][1])))


def cmd_h2h(tag, pairs='80', a_on='', b_on='', first='1'):
    K.RULES, K.FOULS = RULES, FOULS
    K.cmd_h2h(tag, pairs, a_on, b_on, first)


def _timed(sw, rules=None):
    positions, contexts = L.hand_boards()
    pols = {lv: L.policy(lv, 2, 0.0, **sw) for lv in ('rookie', 'starter', 'allstar')}
    kw = dict(rules=rules) if rules else {}
    L.run_jobs('search', positions[:6], contexts, chunks=1, policies=pols, fouls=FOULS, **kw)
    rows, _ = L.run_jobs('search', positions + positions, contexts, chunks=1, policies=pols, fouls=FOULS, **kw)
    rows = rows[len(positions):]
    out = {}
    for lv in pols:
        v = sorted(r['by'][lv]['seconds'] for r in rows)
        out[lv] = dict(median=round(v[len(v) // 2], 3), nine_in_ten=round(v[int(0.9 * (len(v) - 1) + 0.5)], 3), slowest=round(v[-1], 3))
    return out


def cmd_speed(rounds='2', *switches):
    """D-161: step 18k's code (on the cards it had) and this step's, timed in turn."""
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18k as K; "
            "L = K.L; rj = L.run_jobs; L.run_jobs = lambda *a, **k: rj(*a, **dict(k, rules=K.RULES)); "
            "print('RESULT ' + json.dumps(K._timed({})))")
    sw = S._switches(switches) if switches else {}
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18k/playmaker', capture_output=True, text=True, check=True,
                             env=dict(os.environ, SENSE_RUN='step18k', SENSE_18K='1', SENSE_18L='0')).stdout
        one = {'18k': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18l'] = _timed(sw, RULES)
        one['18l, the rule off'] = _timed(sw, dict(RULES, off_balance='off'))
        tally(f'speed, round {r + 1} (one core)', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair; each round times step 18k's code and this step's", switches=sw, rounds=rep),
                  open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
