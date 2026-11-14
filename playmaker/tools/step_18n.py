"""Step 18n: jump shots contested by position only (D-191, D-193), the contest ratings (D-189, D-192), the refit, and
the test: player against player.

  python3 tools/step_18n.py trace <tag> <n> <level> [seed] [k=v ...]   self-play at a level under the app's rules
  python3 tools/step_18n.py maps <write|no> level=tag[,tag] ...         the calibrated map per level, as in step 18h
  python3 tools/step_18n.py fouls <tag> [write]                         the two numbers that price a foul
  python3 tools/step_18n.py measures <tag> [<tag> ...]                  the measures of each run, the FIBA figures included
  python3 tools/step_18n.py matchups <tag>                              every shot, shooter against contest: the tables
  python3 tools/step_18n.py speed [rounds]                              the time to finish 1 pair: 18l's code and this step's
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('SENSE_RUN', 'step18n')
os.environ.setdefault('SENSE_18N', '1')
import step_18l as T                                    # noqa: E402
T.RULES = dict(T.RULES, position_contest='on')
S, L, G, J, K, RUN, WORK, tally = T.S, T.L, T.G, T.J, T.K, T.RUN, T.WORK, T.tally
JUMP = ('mid', 'long', 'three')

cmd_trace, cmd_maps, cmd_fouls, cmd_measures = T.cmd_trace, T.cmd_maps, T.cmd_fouls, T.cmd_measures


def _cards():
    from playmaker_engine.cards import CARDS
    from playmaker_engine.jsbridge import card_json
    return CARDS, {json.dumps(card_json(c), sort_keys=True): k for k, c in CARDS.items()}


def shots_of(tag):
    """Every shot of a run, one record each: who shot (card, type, tier, his open rating for it), the rating he shot
    with, the contest that counted and who gave it, where that defender stood (in front, beside, behind), whether he
    was rushed, whether the defence went for the block, and whether it was fouled."""
    CARDS, by = _cards()
    pl = G.pool()
    rows = json.load(open(os.path.join(WORK, f'trace_{tag}.json')))['rows']
    sq = lambda name: ('ABCDEFGHIJKLMNOPQ'.index(name[0]), int(name[1:]))
    rim = lambda name: max(abs(sq(name)[0] - 8), abs(sq(name)[1] - 2)) if False else None
    from playmaker_engine import board as B
    out = []
    for r in rows:
        x = r.get('result') or {}
        if x.get('kind') not in ('shot', 'free_throws') or not x.get('shot_type'):
            continue
        ctx = pl['contexts'][r['ctx']]
        i, j, t = x['shooter'], x.get('contester', -1), x['shot_type']
        key = by[json.dumps(ctx['off'][i], sort_keys=True)]
        card = CARDS[key]
        rec = dict(shooter=key, role=card.role, tier=card.tier, shot=t, open=card.shot(t), rating=x['rating'], contest=x.get('contest', 0),
                   fouled=x['kind'] == 'free_throws', value=x.get('shot_value', 0), ft=x.get('free_throws', 0), points=x['points'],
                   blocked=any(e[3] == 'contest' for e in r['events']), phase=r['events'][-1][0] if r['events'] else 0,
                   rushed_shot=x['rating'] < card.shot(t), defender=None, where='open', rushed=False, auto=bool(x.get('soft')))
        if j >= 0:
            dkey = by[json.dumps(ctx['dfn'][j], sort_keys=True)]
            dq, sp = B.parse_sq(r['endX'][j]), B.parse_sq(r['endO'][i])
            rec.update(defender=dkey, card_contest=CARDS[dkey].con(t),
                       where='in front' if B.dist_rim(dq) < B.dist_rim(sp) else 'beside' if B.dist_rim(dq) == B.dist_rim(sp) else 'behind',
                       rushed=bool((r['endRushX'] >> (2 * j)) & 3) or bool((r['endLockX'] >> j) & 1))
        out.append(rec)
    return out, len(rows)


def cmd_matchups(tag):
    """The matchup tables: rows the shooter's open rating, columns the contest that counted after its modifiers (open
    its own column); each cell the shots taken and the makes the cards give them (the game scores a shot by its
    chance, rating less contest in 20; it rolls no make or miss, so 'made' is that chance summed)."""
    shots, n = shots_of(tag)
    rep = dict(run=tag, possessions=n, shots=len(shots), tables={}, contested_threes={}, inside={})
    made = lambda s: max(0, s['rating'] - s['contest']) / 20.0
    for name, kinds in (('three', ('three',)), ('mid', ('mid',)), ('long', ('long',)), ('inside', ('layup', 'dunk', 'post', 'floater'))):
        cell = {}
        for s in shots:
            if s['shot'] not in kinds or s['fouled']:
                continue
            c = cell.setdefault(str(s['open']), {}).setdefault('open' if s['defender'] is None else str(s['contest']), [0, 0.0])
            c[0] += 1; c[1] += made(s)
        rep['tables'][name] = {r: {c: dict(taken=v[0], made=round(v[1], 1)) for c, v in sorted(cols.items())} for r, cols in sorted(cell.items(), key=lambda kv: -int(kv[0]))}
    con3 = [s for s in shots if s['shot'] == 'three' and s['defender'] is not None]
    by_type, by_where = {}, {}
    for s in con3:
        k = f"{s['role']} {s['tier']} (three {s['open']})"
        by_type[k] = by_type.get(k, 0) + 1
        w = s['where'] + (', rushed' if s['rushed'] else '')
        by_where[w] = by_where.get(w, 0) + 1
    all3 = [s for s in shots if s['shot'] == 'three']
    taken = {}
    for s in all3:
        t = taken.setdefault(str(s['open']), [0, 0]); t[0] += 1; t[1] += s['defender'] is not None
    rep['contested_threes'] = dict(threes=len(all3), contested=len(con3), by_shooter=dict(sorted(by_type.items(), key=lambda kv: -kv[1])), by_defender_position=by_where,
                                   by_open_rating={k: dict(taken=v[0], contested=v[1]) for k, v in sorted(taken.items(), key=lambda kv: -int(kv[0]))})
    ins = [s for s in shots if s['shot'] not in JUMP]
    pos = {}
    for s in ins:
        w = 'open' if s['defender'] is None else s['where']
        p = pos.setdefault(w, dict(shots=0, went_for_the_block=0, fouled=0, automatic=0))
        p['shots'] += 1; p['went_for_the_block'] += s['blocked']; p['fouled'] += s['fouled']; p['automatic'] += (s['defender'] is not None and not s['blocked'])
    rep['inside'] = dict(shots=len(ins), went_for_the_block=sum(s['blocked'] for s in ins), fouled=sum(s['fouled'] for s in ins), by_position=pos,
                         by_shot={t: sum(1 for s in ins if s['shot'] == t) for t in ('layup', 'dunk', 'post', 'floater')})
    json.dump(dict(rep, every_shot=shots), open(os.path.join(RUN, f'matchups_{tag}.json'), 'w'), indent=1)
    for name, tb in rep['tables'].items():
        print('==', name)
        for r, cols in tb.items():
            print('  open', r, '|', ' '.join(f"{c}: {v['taken']} ({v['made']})" for c, v in cols.items()))
    print('contested threes', json.dumps(rep['contested_threes']))
    print('inside', json.dumps(rep['inside']))


def _timed(sw, rules=None):
    return T._timed(sw, rules)


def cmd_speed(rounds='2'):
    """D-161: step 18l's code (on the cards it had) and this step's, timed in turn."""
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18l as T; "
            "print('RESULT ' + json.dumps(T._timed({}, T.RULES)))")
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18l/playmaker', capture_output=True, text=True, check=True,
                             env=dict(os.environ, SENSE_RUN='step18l', SENSE_18L='1', SENSE_18N='0')).stdout
        one = {'18l': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18n'] = T._timed({}, T.RULES)
        tally(f'speed, round {r + 1} (one core)', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair; each round times step 18l's code and this step's", rounds=rep),
                  open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
