"""Step 20 (Shaun, 17 Nov 2026): the lasting gap. The engines' equality, the hand checks, and the report runs.

python3 tools/step_20.py lgequal [n] [seed] [broken]    the lasting gap in the two engines, on random positions
python3 tools/step_20.py hand                           the map on three boards, for the hand checks"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
RUN = os.path.join(ROOT, 'docs', 'runs', 'step20')
os.makedirs(RUN, exist_ok=True)


def _js_lasting(s):
    from playmaker_engine import agent as AG, jsbridge
    return json.loads(AG.JS['coverage'](json.dumps(dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), options=dict(only='lasting')))))


def cmd_lgequal(n='200', seed='5', broken=''):
    """The lasting gap (the number, the threat before the answer, the overloads and the answer's moves) in the two
    engines, on random positions under the app's rules. -> docs/runs/step20/lasting_equal.json"""
    import random
    import js_equivalence as E
    from playmaker_engine import decide as D, jsbridge
    E._ZONE['v'] = 'on'
    E._CONTROL['size'] = 'app'
    E._FIBA.update(three_seconds='on', closely_guarded='on', fiba_fouled_shot='on', soft_contest='on', fiba_steal_foul='on', off_balance='on', position_contest='on')
    if broken:
        E._ZONE['broken'] = True
    eng = jsbridge.NodeEngine().install()
    rng = random.Random(int(seed))
    t0 = time.time()
    seen = same = 0
    bad, tj, tp = [], 0.0, 0.0
    try:
        while seen < int(n):
            s, meta = E.random_state(rng)
            if s.stage != 'play' or not meta['digital'] or s.clock <= 2:
                continue
            a = time.time(); js = _js_lasting(s); tj += time.time() - a
            a = time.time(); g = D.lasting_of(s); tp += time.time() - a
            py = None if g is None else dict(L=round(g['L'], 2), before=round(g['before'], 2), overloads=g['ov'], moves=g['moves'])
            seen += 1
            ok = (js is None and py is None) or (js is not None and py is not None and abs(js['L'] - py['L']) < 0.006
                                                 and abs(js['before'] - py['before']) < 0.006 and js['overloads'] == py['overloads'] and js['moves'] == py['moves'])
            same += ok
            if not ok and len(bad) < 8:
                bad.append(dict(js=js, py=py, state=jsbridge.state_json(s)))
    finally:
        eng.close()
    out = dict(positions=seen, equal=same, different=bad, seconds=round(time.time() - t0, 1), js_ms=round(1000 * tj / max(1, seen), 1), py_ms=round(1000 * tp / max(1, seen), 1))
    json.dump(out, open(os.path.join(RUN, 'lasting_equal' + ('_broken' if broken else '') + '.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'different'}))
    for b in bad[:3]:
        print(b['js'], b['py'], json.dumps(b['state'])[:300])


def report_text(rep):
    """One possession's report as plain lines, in the order the downloaded report shows them."""
    out = [f"Possession {rep['possession']}: {rep['teams'][0]} v {rep['teams'][1]}"]
    su = rep.get('setup') or {}
    if su.get('offence'):
        out += ['The setup', '  ' + su['offence'], '  ' + su['defence']]
    for ph in sorted({t['phase'] for t in rep['turns']}):
        out.append(f'Phase {ph}')
        for t in [t for t in rep['turns'] if t['phase'] == ph]:
            out += [f"  Turn {t['turn']}", '    ' + t['offence'], '    ' + t['defence']]
        pa = next((p for p in rep['phases'] if p['phase'] == ph), None)
        if pa:
            out.append(f'  The coach on phase {ph}')
            out += ['    Offence: ' + x for x in pa['offence']] + ['    Defence: ' + x for x in pa['defence']]
            if pa['next']:
                out.append('    ' + pa['next'])
    sm = rep.get('summary')
    if sm:
        out.append('The coach on the possession')
        out += ['  ' + x for x in (sm['verdict'], sm['shot'], sm['score'], sm['best'], sm['trend']) if x]
        for side in ('offence', 'defence'):
            for k in ('keep', 'change'):
                if sm[side][k]:
                    out.append(f'  {side.capitalize()}: {sm[side][k]}')
    ev = rep['switches']['eval']
    out.append(f"Played with: the heat map {'on for both sides' if ev.get('map') is True else ev.get('map')}; computer {rep['switches']['computer']}")
    if rep.get('checks'):
        out.append('CHECKS FAILED: ' + '; '.join(rep['checks']))
    return out


def cmd_watch(tag='watch', level='allstar', seed='', poss='8'):
    """Watch the computer: one game of Five Out v High-Low (game 4E81CC's teams), the computer on both sides, every
    possession's report built and written out. -> docs/runs/step20/<tag>/possession<N>.txt and .json"""
    from playmaker_engine import agent as AG
    from playmaker_web.api import Manager, handle
    from playmaker_web import report as R
    from playmaker_web.server import coverage_engine, stop_coverage_engine
    out_dir = os.path.join(RUN, tag)
    os.makedirs(out_dir, exist_ok=True)
    assert coverage_engine()
    t0 = time.time()
    try:
        m = Manager()
        body = dict(mode='hotseat', match_format='digital', teams=['Five Out', 'High-Low'], level='pro', full=True,
                    per_side=int(poss) // 2, ai=dict(O=level, X=level))
        if seed:
            body['seed'] = int(seed)
        st, r = handle(m, 'POST', '/api/new', body=body)
        g = m.get(r['code'])
        tok = r['token']
        times, summary = [], []
        for p in range(1, int(poss) + 1):
            if p > 1:
                a = time.time()
                handle(m, 'POST', '/api/next', body=dict(code=g.code, token=tok))
                times.append(round(time.time() - a, 1))
            assert g.state.stage == 'over', (p, g.state.stage)
            a = time.time()
            rep = R.build(g, p)
            lines = report_text(rep)
            open(os.path.join(out_dir, f'possession{p}.txt'), 'w').write('\n'.join(lines) + '\n')
            json.dump(rep, open(os.path.join(out_dir, f'possession{p}.json'), 'w'), indent=1, default=str)
            rolls = [r2 for (pp, i), e in g._trail_entries.items() if pp == p for r2 in e.get('rolls', [])]
            summary.append(dict(possession=p, score=rep['summary']['numbers']['total'], verdict=rep['summary']['verdict'],
                                checks=rep['checks'], turns=len(rep['turns']), rolls=[(x['what'], x['face'], x['picked']) for x in rolls],
                                report_s=round(time.time() - a, 1)))
            print(p, summary[-1]['score'], summary[-1]['verdict'], summary[-1]['checks'], 'rolls', len(rolls), flush=True)
        res = dict(code=g.code, seed=g.seed, seeded=g.seeded, level=level, map=AG.CONFIG['eval']['map'], possessions=summary,
                   play_s=times, seconds=round(time.time() - t0, 1))
        json.dump(res, open(os.path.join(out_dir, 'summary.json'), 'w'), indent=1)
        print(json.dumps(dict(code=g.code, seconds=res['seconds'], play_s=times)))
    finally:
        stop_coverage_engine()


def cmd_hand():
    """The map on three boards, for the hand checks of part 1: Shaun's board of 15 November, the screen board (step
    18s, S3) and the closeout board (step 18d). -> docs/runs/step20/hand.json"""
    import step_18s as T
    import step_18d as T18
    from playmaker_engine import agent as AG, board as B, jsbridge
    eng = jsbridge.NodeEngine().install()
    out = []
    try:
        for name, s in [('Shaun, 15 Nov', T.board()), ('the screen board', T.screen_board()), ('the closeout board', T18.closeout_board())]:
            a = time.time()
            c = AG.coverage(s)
            row = dict(board=name, o=[B.sq(p) for p in s.o], ball=f'O{s.ball + 1}', x=[B.sq(p) for p in s.x],
                       arrows=[['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][d] for d in s.arrows], side=s.side, tok_x=s.tok_x,
                       before=c['before'], lasting=c['lasting'], answers=c['answers'], left=c['left'],
                       overloads=[dict(x=v['x'], value=v['value'], line=v['line'], threats=v['threats']) for v in c['overloads']],
                       words=c['words'], seconds=round(time.time() - a, 2))
            # the shading after the answer against the words: the darkest square after the answer is what the words leave
            top = max(((sq, v['worth'], a2) for a2, d in enumerate(c['squares_after']) for sq, v in d.items()), key=lambda z: z[1], default=None)
            row['darkest_after'] = dict(sq=top[0], worth=top[1], o=top[2]) if top else None
            out.append(row)
            print(json.dumps(row, indent=1))
    finally:
        eng.close()
    json.dump(out, open(os.path.join(RUN, 'hand.json'), 'w'), indent=1)


def cmd_blueprint(copies='8'):
    """The blueprint's play checks with the map on for both sides (today's default), run and reported, not gating:
    the closeout positions, check 7, check 8 with S2, S3 and S4 (tools/step_18s.py), written to docs/runs/step20/
    instead of step 18s's folder. Checks 1 to 6 are `python3 tools/step_18s.py checks` (its checks.json, copied here)."""
    import shutil as _sh
    import step_18s as S
    S.RUN = RUN
    base = os.path.join(ROOT, 'docs', 'runs', 'step18s', 'passlines_pass.json')
    if not os.path.exists(os.path.join(RUN, 'passlines_pass.json')):
        _sh.copy(base, os.path.join(RUN, 'passlines_pass.json'))     # check 7's "without the map", step 18s's own run
    t = {}
    for name, fn, args in (('closeout', S.cmd_closeout, ('closeout', copies, 'map')), ('check7', S.cmd_check7, ('check7', copies)),
                           ('check8', S.cmd_check8, ('check8', copies, 'map')), ('s3', S.cmd_s3, ('s3', copies, 'map')),
                           ('s4', S.cmd_s4, ('s4', '4', '4', '2'))):
        a = time.time()
        print('==', name, flush=True)
        try:
            fn(*args)
        except Exception as e:                     # report it, run the rest
            print('FAILED', name, repr(e), flush=True)
        t[name] = round(time.time() - a, 1)
        print('== seconds', name, t[name], flush=True)
    json.dump(t, open(os.path.join(RUN, 'blueprint_seconds.json'), 'w'), indent=1)


def _grid(o, x, ball, marks):
    """A board in text: row 14 at the top, the rim end at the bottom. O1 to O5 (the ball handler with *), X1 to X5,
    and marks {square: two letters}."""
    from playmaker_engine import board as B
    cells = {}
    for k, q in marks.items():
        cells[q] = k
    for i, q in enumerate(x):
        cells[q] = f'X{i + 1}'
    for i, q in enumerate(o):
        cells[q] = f'O{i + 1}' + ('*' if i == ball else '')
    lines = ['     ' + ''.join(f'{c:^4}' for c in B.COLS)]
    for row in range(14, 0, -1):
        lines.append(f'{row:>3}  ' + ''.join(f'{cells.get(f"{c}{row}", "."):^4}' for c in B.COLS))
    return '\n'.join(lines)


def cmd_handboards():
    """docs/runs/step20/hand.json as boards in text: the position, then the defence after its best answer with the
    square it leaves (LG) and each overload's two threats (V1, V2...). -> docs/runs/step20/hand_boards.md"""
    rows = json.load(open(os.path.join(RUN, 'hand.json')))
    out = ['# Step 20 hand checks: the boards', '']
    for r in rows:
        ball = int(r['ball'][1:]) - 1
        out += [f"## {r['board']}", '', f"Before the answer the best look is worth {r['before']:.0f}; the lasting gap is {r['lasting']:.0f}.", '', '```',
                _grid(r['o'], r['x'], ball, {}), '```', '']
        placed = list(r['x'])
        for a in r['answers']:
            placed[a['x']] = a['to']
        marks = {}
        if r['left']:
            marks['LG'] = r['left']['sq']
        for k, v in enumerate(r['overloads']):
            for t in v['threats'][:2]:
                marks.setdefault(f'V{k + 1}', t['sq']) if False else None
                marks[f'V{k + 1}' + ('a' if t is v['threats'][0] else 'b')] = t['sq']
        out += ["After the defence's best answer (LG: the square it leaves; Va/Vb: an overloaded defender's two looks):", '', '```',
                _grid(r['o'], placed, ball, marks), '```', '', r['words'], '']
    open(os.path.join(RUN, 'hand_boards.md'), 'w').write('\n'.join(out) + '\n')
    print('\n'.join(out))


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
