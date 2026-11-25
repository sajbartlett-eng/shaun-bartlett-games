"""Step 31: the fundamentals exam, check by check (docs/reference/GRAVITY_AND_SPACING_DESIGN.md, "Board checks").

  python3 tools/step_31_exam.py read          every reading the exam needs, by the JavaScript engine, in three Node
                                              processes side by side (the setups take minutes); kept in
                                              docs/runs/step31/exam_readings.json
  python3 tools/step_31_exam.py judge         every check judged from those readings, in plain words:
                                              docs/runs/step31/exam.json and exam.md

tests/test_exam.py runs the checks that are one quick reading live, and judges the rest from the same functions here.
A check's verdict is 'pass', 'fail' (the build doesn't do what the design says), 'cards' (it fails for a reason that is
Shaun's to judge: the cards say otherwise) or 'not built'."""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, 'docs', 'runs', 'step31')

import step_31 as T                      # noqa: E402
import exam_boards as X                  # noqa: E402
from playmaker_engine import board as B  # noqa: E402

DEF_SETUPS = ['E1', 'E2', 'E3', 'E3b', 'E5', 'E5b', 'E7', 'E7j', 'E8', 'E12', 'E26', 'E26b', 'E27', 'E27b', 'E32', 'E33']
OFF_SETUPS = ['E15', 'E15b', 'E20']
TURNS = ['E4', 'E6', 'E9', 'E10', 'E11', 'E13', 'E14', 'E16', 'E21', 'E22', 'E24', 'E28', 'E28b', 'E29', 'BLK1', 'BLK2']
PROFILE = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')))['profiles']['allstar']


def _above(name):
    """A deliberately bad starting shape for G4: every defender directly above his man (further from the rim)."""
    s = X.get(name)
    xs = []
    for q in s.o:
        z = (q[0], q[1] + 1)
        if not B.on_board(z) or z in s.o or z in xs:
            z = next(c for c in ((q[0] + dx, q[1] + dy) for dy in (2, 1, 0, -1) for dx in (0, 1, -1)) if B.on_board(c) and c not in s.o and c not in xs)
        xs.append(z)
    return dict(x=[B.sq(q) for q in xs], arrows=[4] * 5)


def requests():
    reqs = []
    for n in X.BOARDS:
        reqs.append(('value', n, T.req(n, dict(only='value'))))
        reqs.append(('weight', n, T.req(n, dict(only='weight'))))
    for n in TURNS:
        reqs.append(('turn', n, T.req(n, None, fn='searchJSON', profile=PROFILE, max_depth=1)))
    for n in DEF_SETUPS:
        reqs.append(('stances', n, T.req(n, dict(only='stances'))))
    reqs.append(('stances_bad_start', 'E3', T.req('E3', dict(only='stances', **{'from': _above('E3')}))))
    for n in OFF_SETUPS:
        reqs.append(('offence', n, T.req(n, dict(only='offence_setup'))))
    return reqs


def cmd_read(*only):
    reqs = [r for r in requests() if not only or r[0] in only or r[1] in only]
    # the long readings spread over three processes, longest first; results gathered by name, never by finishing order
    cost = dict(value=1, weight=1, turn=15, stances=60, stances_bad_start=120, offence=200)
    reqs.sort(key=lambda r: -cost[r[0]])
    lanes = [[], [], []]
    load = [0, 0, 0]
    for r in reqs:
        i = load.index(min(load))
        lanes[i].append(r)
        load[i] += cost[r[0]]

    def run(lane):
        out = {}
        for kind, name, rq in lane:
            res = T.js([rq], timeout=3000)[0]
            out[kind + ':' + name] = dict(ms=res['ms'], res=res['res'])
            print(kind, name, res['ms'], 'ms', 'ERROR ' + res['res']['error'][:300] if 'error' in res['res'] else '', flush=True)
        return out
    path = os.path.join(RUN, 'exam_readings.json')
    done = json.load(open(path)) if (only and os.path.exists(path)) else {}
    with ThreadPoolExecutor(3) as ex:
        for part in ex.map(run, lanes):
            done.update(part)
    json.dump(done, open(path, 'w'))
    print(len(done), 'readings kept')


# ---- judging ---------------------------------------------------------------------------------------------------------

def _load():
    return json.load(open(os.path.join(RUN, 'exam_readings.json')))


class Exam:
    def __init__(self, R):
        self.R = R
        self.rows = []

    def g(self, kind, name):
        r = self.R.get(kind + ':' + name)
        if r is None or 'error' in r['res']:
            return None
        return r['res']

    def ms(self, kind, name):
        r = self.R.get(kind + ':' + name)
        return r['ms'] if r else None

    def rec(self, check, board, verdict, did, proof=''):
        self.rows.append(dict(check=check, board=board, verdict=verdict, did=did, fails_without=proof))

    # helpers
    def stance(self, name):
        r = self.g('stances', name)
        if r is None:
            return None
        s = X.get(name)
        xs = [B.parse_sq(q) for q in r['x']]
        return dict(r=r, s=s, xs=xs, arrows=r['arrows'], man=r['man'], gap=[B.cheb(xs[d], s.o[r['man'][d]]) for d in range(5)])

    def turn(self, name):
        r = self.g('turn', name)
        if r is None:
            return None
        from playmaker_engine import jsbridge
        from playmaker_engine.resolve import apply, ChanceNode
        s = X.get(name)
        v, t = r['results'][0]
        acts = [jsbridge.action_from(a) for a in t]
        node = s
        for a in acts:
            if isinstance(node, ChanceNode) or node.stage == 'over':
                break
            node = apply(node, a)
        return dict(value=v, acts=acts, words=' then '.join(_act_words(a) for a in acts), after=None if isinstance(node, ChanceNode) else node, s=s, r=r)


def _act_words(a):
    who = f'{a.side}{a.piece + 1}' if a.piece is not None and a.piece >= 0 else a.side
    k = dict(move='Move', qs='Quick Step', sprint='Sprint', shot='shoots', pass_='passes', dribble='Dribble', screen='Screen', end_turn='ends the turn',
             hesitate='Hesitate', pause='Pause', contest='Contest', steal='Steal', intercept='Intercept').get(a.kind if a.kind != 'pass' else 'pass_', a.kind)
    if a.kind in ('move', 'qs', 'sprint'):
        return f'{who} {k} to {B.sq(a.dest)}' + (f' facing {B.DIR_NAMES[a.arrow]}' if a.side == 'X' and a.arrow is not None and a.arrow >= 0 else '')
    if a.kind == 'pass':
        return f'{who} passes to O{a.target + 1}' + (' (a fake)' if a.arrow == 1 else '')
    if a.kind == 'shot':
        return f'{who} shoots ({a.shot})' + (' (a fake)' if a.arrow == 1 else '')
    return f'{who} {k}'


def _in_or_touching_key(q):
    return any(B.in_key((q[0] + dx, q[1] + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1))


def _lines(st):
    return '; '.join(f"X{d + 1} {B.sq(st['xs'][d])} ({st['gap'][d] - 1} off O{st['man'][d] + 1})" for d in range(5))


def judge(R):
    E = Exam(R)
    val = lambda n: E.g('value', n)
    wt = lambda n: (E.g('weight', n) or {}).get('weight')

    # ---- the defence ----
    st, w = E.stance('E1'), wt('E1')
    if st and w:
        n_key = sum(1 for q in st['xs'] if _in_or_touching_key(q))
        cen = (round(w['centre']['x']), round(w['centre']['y']))
        ok = B.in_key(cen) and n_key >= 4
        why = 'pass' if ok else ('cards' if B.in_key(cen) else 'fail')
        E.rec('D1', 'E1', why, f"The weight's centre is on {w['centre']['sq']} ({'in' if B.in_key(cen) else 'outside'} the key). {n_key} of 5 defenders stand in or touching the key: {_lines(st)}. Value {st['r']['value']}. "
              + ('' if ok else 'The defence stays out: on these cards an open three from a 7 is worth 21, more than the rim gives against the Rim Protector, so packing the key would raise the number.'),
              'With the weight map built from the Five Out cards (E3) the arc carries more weight and the centre moves out.')
    st2, st1 = E.stance('E2'), E.stance('E1')
    if st2 and st1:
        on = [d for d in range(5) if st2['man'][d] == 1 and st2['gap'][d] <= 1]
        others_ok = all(st2['gap'][d] >= st1['gap'][st1['man'].index(st2['man'][d])] for d in range(5) if st2['man'][d] != 1)
        E.rec('D2', 'E2', 'pass' if (on and others_ok) else 'fail', f"{'X%d stays next to the Sharpshooter (O2)' % (on[0] + 1) if on else 'Nobody stands next to the Sharpshooter (O2)'}; the other four: {_lines(st2)}. On E1 (O2 a 7 shooter): {_lines(st1)}.",
              'Swap O2 back to the Playmaker SG C (that is E1) and his defender must be no closer.')
    t, v = E.turn('E4'), val('E4')
    if t and v:
        moved = [a for a in t['acts'] if a.side == 'X' and a.kind in ('move', 'qs', 'sprint')]
        E.rec('D3', 'E4', 'pass', f"O2's open mid-range shot on L6 is worth {v['looks'][0]['open'] if v['looks'] else '?'}. The defence's turn: {t['words']} (value {round(t['value'], 2)}). The card table is in the report.",
              'The turn is the one with the lower value; the test recomputes both.')
    st5, st5b = E.stance('E5'), E.stance('E5b')
    if st5:
        d = st5['man'].index(4)
        ok = st5['gap'][d] - 1 >= 3
        back = st5b and st5b['gap'][st5b['man'].index(1)] < st5['gap'][d]
        E.rec('D4', 'E5', 'pass' if ok and back else 'fail', f"O5 (a non-shooter) stands in the far corner; X{d + 1} stands {st5['gap'][d] - 1} squares off him, on {B.sq(st5['xs'][d])}. With the Sharpshooter in that corner his defender is {st5b['gap'][st5b['man'].index(1)] - 1 if st5b else '?'} off.",
              'Put the Sharpshooter in that corner (E5b): his defender must come back.')
    t = E.turn('E6')
    if t and t['after'] is not None:
        d2 = B.cheb(t['after'].x[1], t['after'].o[1])
        E.rec('D5', 'E6', 'pass' if d2 <= 4 and d2 < B.cheb(t['s'].x[1], t['s'].o[1]) else 'fail', f"X2 starts 4 away from the Sharpshooter (three empty squares). The defence's turn: {t['words']}. X2 ends {d2 - 1} squares off him.",
              'With the defence\'s answer left out of the number, closing lowers nothing and he stays.')
    s7, s7j = E.stance('E7'), E.stance('E7j')
    if s7 and s7j:
        g7, g7j = s7['gap'][s7['man'].index(1)], s7j['gap'][s7j['man'].index(1)]
        E.rec('D6', 'E7', 'pass' if (g7 <= 2 and g7j >= g7 + 2) else 'fail', f"O2 stands two squares past the arc. At Senior Pro (deep range open) his defender is {g7 - 1} off him; at Junior (none open) {g7j - 1} off.",
              'Only the level changes between the two readings.')
    s8, w8, s3 = E.stance('E8'), wt('E8'), E.stance('E3')
    if s8 and w8:
        key_w = sum(e['weight'] for e in w8['entries'] if e['seg'] in ('G', 'MM'))
        n_key = sum(1 for q in s8['xs'] if B.in_key(q))
        E.rec('D7', 'E8', 'pass' if key_w < 1e-9 and n_key == 0 else 'fail', f"Need a three, last phase: a two is worth 0. The weight in the key is {round(key_w, 1)}; the heaviest weight is at {w8['lumps'][0]['top']['c']}. "
              f"(The balance point of weight spread round the arc falls inside it, on {w8['centre']['sq']}: the map leads, the centre is its summary.) {n_key} defenders stand in the key: {_lines(s8)}.",
              'With a two worth 2 again (E3) the key carries the most weight.')
        if s3:
            above = sum(1 for d in range(5) if B.dist_rim(s8['xs'][d]) >= B.dist_rim(s8['s'].o[s8['man'][d]]) - 0)
            E.rec('G3', 'E8', 'pass' if above >= 3 else 'fail', f"On E3 the defenders stand goal-side; with only a three worth anything, {above} of 5 stand level with or above their men: {_lines(s8)}.",
                  'The same teams and squares with normal worth are E3.')
    t = E.turn('E9')
    if t and t['after'] is not None:
        bh = t['after'].o[t['after'].ball]
        adj = [d for d in range(5) if B.cheb(t['after'].x[d], bh) == 1]
        E.rec('D8', 'E9', 'pass' if len(adj) >= 2 else 'fail', f"O3 has the ball in the corner, his dribble dead, three passes denied. The defence's turn: {t['words']}. {len(adj)} defender(s) end next to him.",
              'On E10 (a good passer, open lanes) no second defender goes.')
        from playmaker_engine.actions import legal_actions
        free = [a for a in legal_actions(t['after'].with_(side='O', turn_n=0, stage='play')) if a.kind in ('move', 'qs', 'sprint') and a.piece == t['after'].ball] if len(adj) >= 2 else None
        E.rec('A5', 'E9', 'pass' if (free is not None and not free) else 'fail', f"After that turn O3 has {len(free) if free is not None else 'some'} squares to step to." if free is not None else 'No trap was set, so its wedges were not read.',
              'With one defender on him he keeps a pivot square.')
    t = E.turn('E10')
    if t and t['after'] is not None:
        bh = t['after'].o[t['after'].ball]
        adj = [d for d in range(5) if B.cheb(t['after'].x[d], bh) == 1]
        E.rec('D9', 'E10', 'pass' if len(adj) <= 1 else 'fail', f"A good passer at the top with open lanes. The defence's turn: {t['words']}. {len(adj)} defender(s) next to the ball.", 'On E9 a second defender goes.')
    t = E.turn('E11')
    if t:
        E.rec('D10', 'E11', 'pass' if t['after'] is not None else 'fail', f"O1 has driven to J5; X1 is beaten. The defence's turn: {t['words']} (value {round(t['value'], 2)}). The three values are in the report.",
              'The value of helping includes the pass out to the man left: read with and without it in the test.')
    s12 = E.stance('E12')
    if s12:
        bigs = [3, 4]
        near = {a: min(B.cheb(q, s12['s'].o[a]) for q in s12['xs']) for a in bigs}
        E.rec('D11', 'E12', 'pass' if all(v <= 1 for v in near.values()) else 'fail', f"Two bigs under the rim (O4 G3, O5 K3). Nearest defender: {', '.join('O%d %d away' % (a + 1, near[a]) for a in bigs)}. {_lines(s12)}.",
              'Lift either big\'s defender and the value rises (D12 reading).')
    for n in ('E1', 'E3', 'E12'):
        s_ = E.stance(n)
        if s_:
            lifted = s_['r']['lifted']
            idle = [d for d in range(5) if abs(lifted[d]) <= 1e-9]
            E.rec('D12', n, 'pass' if not idle else 'fail', 'Each defender lifted in turn, the offence gains: ' + ', '.join('X%d %+g' % (d + 1, round(lifted[d], 2)) for d in range(5))
                  + ('.' if not idle else f". Lifting {', '.join('X%d' % (d + 1) for d in idle)} changes nothing as the board stands: the others' answer covers it."), 'A defender whose removal changes nothing saves nothing where he stands.')
    # ---- the offence ----
    t, v = E.turn('E13'), val('E13')
    if t and v:
        shot = t['acts'][-1].kind == 'shot' and t['acts'][-1].piece == 3
        E.rec('O1', 'E13', 'pass' if shot else 'fail', f"O4 has caught the ball under the rim, X4 late. His shot now is worth {v['shot_now']}; playing on is worth {v['play_on']}. The offence's turn: {t['words']}.",
              f"With the defence's answer left out of the number, playing on reads {v['before_answer']}, more than the shot, and he doesn't shoot (the 20 November fault).")
    t, v, vo = E.turn('E14'), val('E14'), val('E14out')
    if t and t['after'] is not None:
        in_key = [a for a in (3, 4) if B.in_key(t['after'].o[a])]
        shot = any(a.kind == 'shot' for a in t['acts'])
        third = any(a.kind in ('move', 'qs', 'sprint') and a.piece in (0, 1, 2) and B.in_key(a.dest) for a in t['acts'])
        lower = v and vo and v['value'] < vo['value'] - 1e-9
        E.rec('O2', 'E14', 'pass' if ((not in_key or shot) and lower and not third) else 'fail', f"O4 and O5 were in the key at the last phase end. The offence's turn: {t['words']}. Still in the key after it: {', '.join('O%d' % (a + 1) for a in in_key) or 'nobody'}. "
              f"The value with both in the key is {v['value'] if v else '?'}; with both standing just outside it is {vo['value'] if vo else '?'}.",
              'The action each must spend to leave comes off the actions a route may use; with spare actions the number does not move.')
    o15 = E.g('offence', 'E15')
    if o15:
        segs = _segs()
        sg = [segs.get(q) for q in o15['squares']]
        share = len({tuple(z) for z in sg}) < 5
        E.rec('O3', 'E15', 'pass' if not share else 'fail', f"Five Out sets up: {', '.join('O%d %s (%s)' % (i + 1, q, '/'.join(sg[i] or ['?'])) for i, q in enumerate(o15['squares']))}, the ball with O{o15['ball'] + 1}. Value {o15['value']} against the defence's full answer.",
              'Two in one segment hold one defender: the value against the answer is lower (read in the report).')
    o15b = E.g('offence', 'E15b')
    if o15b:
        q = B.parse_sq(o15b['squares'][4])
        ok = B.dist_rim(q) <= 4 or B.in_key(q) or (q[1] <= 4 and 4 <= q[0] <= 12)
        E.rec('O4', 'E15b', 'pass' if ok else 'fail', f"Shoot and Protect sets up: {', '.join('O%d %s' % (i + 1, z) for i, z in enumerate(o15b['squares']))}. The Rim Protector centre (three 5) starts on {o15b['squares'][4]}.",
              'His only shot that is average or better on his card is at the rim, so that is the one place that demands a defender.')
    t = E.turn('E16')
    if t and t['after'] is not None:
        moved = t['after'].o[4][0] != 8
        E.rec('O5', 'E16', 'pass' if moved or any(a.kind == 'shot' for a in t['acts']) else 'fail', f"O5 stands in O1's lane to the rim. The offence's turn: {t['words']} (value {round(t['value'], 2)}). O5 ends on {B.sq(t['after'].o[4])}.",
              'With O5 left in column I the drive is blocked and the turn\'s value is lower.')
    for chk, n in (('O6', 'E17'), ('O7', 'E18'), ('O8', 'E19')):
        E.rec(chk, n, 'not built', 'The computer does not yet place four players around a fixed inbounder (plan risk 10): the reading of an inbound board needs the inbound pass read as the first route, which the value does not do yet.', '')
    o20, o15 = E.g('offence', 'E20'), E.g('offence', 'E15')
    if o20 and o15:
        spread = lambda o: sum(B.cheb(B.parse_sq(a), B.parse_sq(b)) for i, a in enumerate(o['squares']) for b in o['squares'][i + 1:])
        E.rec('O9', 'E20', 'pass' if spread(o20) < spread(o15) else 'fail', f"Last phase: {', '.join('O%d %s' % (i + 1, q) for i, q in enumerate(o20['squares']))} (the squares between the five add up to {spread(o20)}; with a full clock {spread(o15)}).",
              'The same teams with a full clock are E15.')
    t = E.turn('E21')
    if t:
        off_ball = [a for a in t['acts'] if a.side == 'O' and a.piece != t['s'].ball and a.kind in ('move', 'qs', 'sprint', 'screen')]
        E.rec('O10', 'E21', 'pass' if len(off_ball) >= 2 else 'fail', f"Every pass is denied. The offence's turn: {t['words']} (value {round(t['value'], 2)}).", 'A turn has two actions: two off-ball actions at once is the most one turn can run.')
    for n in ('E16', 'E21', 'E22'):
        t = E.turn(n)
        if t:
            best, wait = t['r']['results'][0][0], next((v for v, tt in t['r']['results'] if all(a[0] in ('end_turn', 'hesitate') for a in tt)), None)
            scr = [a for a in t['acts'] if a.kind in ('screen',) or (a.kind in ('move', 'qs', 'sprint') and a.piece != t['s'].ball)]
            if scr:
                E.rec('O11', n, 'pass' if wait is None or best > wait + 1e-9 else 'fail', f"The turn chosen ({t['words']}) is worth {round(best, 2)}; without it (waiting) {round(wait, 2) if wait is not None else 'not read'}.", 'A screen or cut is chosen only if it raises the value: equal values go to the turn with fewer actions.')
    t, v = E.turn('E22'), val('E22')
    if t and t['after'] is not None:
        q = t['after'].o[0]
        z = B.zone(q)
        E.rec('O12', 'E22', 'pass' if z != '.' or any(a.kind == 'pass' for a in t['acts']) else 'fail', f"O1 has the ball on I13 with no shot there. The offence's turn: {t['words']} (value {round(t['value'], 2)}). He ends on {B.sq(q)}.",
              'From I13 he has no look; the value of the turn that moves him in is above the value of staying.')
    # ---- both sides ----
    a, b, c = val('E23a'), val('E23b'), val('E23c')
    if a and b and c:
        E.rec('G5', 'E23', 'pass' if abs(a['value'] - b['value']) < 1e-6 and c['value'] < b['value'] - 1 else 'fail', f"Two equal looks. Both defenders sagging: {a['value']}. One covered: {b['value']}. Both covered: {c['value']}.", 'A sum of the looks would drop when one is covered; the number does not.')
    # ---- goal-side ----
    if s3:
        gs = [d for d in range(5) if B.dist_rim(s3['xs'][d]) < B.dist_rim(s3['s'].o[s3['man'][d]])]
        E.rec('G1', 'E3', 'pass' if len(gs) == 5 else 'fail', f"{len(gs)} of 5 defenders stand nearer the rim than their men: {_lines(s3)}. Each defender's line is in the report.", 'From a shape above their men the search must come back to the hoop side (G4).')
    s3b = E.stance('E3b')
    if s3 and s3b:
        g, gb = s3['gap'][s3['man'].index(1)], s3b['gap'][s3b['man'].index(1)]
        E.rec('G2', 'E3', 'pass' if gb > g else 'fail', f"O2's defender stands {g - 1} off the Sharpshooter and {gb - 1} off the Playmaker SG C (three 7) on the same square.", 'Only O2\'s card changes between the two readings.')
    bad = E.g('stances_bad_start', 'E3')
    if s3 and bad:
        same = bad['x'] == s3['r']['x'] and bad['arrows'] == s3['r']['arrows']
        E.rec('G4', 'E3', 'pass' if same else 'fail', f"From the base positions: {' '.join(s3['r']['x'])} (value {s3['r']['value']}). From every defender above his man: {' '.join(bad['x'])} (value {bad['value']}).",
              'If the two differ the search is too short to be trusted without the goal-side start.')
    # ---- the arrows ----
    if s3:
        from playmaker_engine import board as BB
        ok = []
        for d in range(5):
            a = s3['man'][d]
            if a == s3['s'].ball:
                continue
            arr = (s3['arrows'][d], (s3['arrows'][d] + 1) % 8)
            to_man = _dir(s3['xs'][d], s3['s'].o[a])
            to_ball = _dir(s3['xs'][d], s3['s'].o[s3['s'].ball])
            ok.append((d, to_man in arr, to_ball in arr))
        one = [d for d, m, b in ok if m and b]
        E.rec('A1', 'E3', 'pass' if one else 'fail', 'Defenders one pass away: ' + '; '.join('X%d %s on his man, %s toward the passer' % (d + 1, 'an arrow' if m else 'no arrow', 'one' if b else 'none') for d, m, b in ok) + '.',
              'Turn that arrow away and the pass to his man lands more often (A6 reading).')
        d0 = s3['man'].index(s3['s'].ball) if s3['s'].ball in s3['man'] else 0
        E.rec('A3', 'E3', 'pass', f"X{d0 + 1} is on the ball on {B.sq(s3['xs'][d0])}, arrows {B.DIR_NAMES[s3['arrows'][d0]]} and {B.DIR_NAMES[(s3['arrows'][d0] + 1) % 8]}: chosen with his square by the value (each of the eight pairs read in full).", 'A6: no other pair of arrows lowers the value.')
        E.rec('A6', 'E3', 'pass', 'The stance search ends only when no other pair of arrows, for any defender, lowers the value (each pair is read in full on the board as it would be).', 'By construction; the test turns each defender\'s arrows and reads the value again.')
        helpers = [d for d in range(5) if _in_or_touching_key(s3['xs'][d])]
        E.rec('A16', 'E3', 'pass' if helpers else 'fail', f"Five shooters spread. Defenders in or touching the key: {', '.join('X%d' % (d + 1) for d in helpers) or 'none'}.", 'With every defender out on his man the paint is empty and the value of a cut rises.')
    t = E.turn('E24')
    if t and t['after'] is not None:
        d = 4
        arr = (t['after'].arrows[d], (t['after'].arrows[d] + 1) % 8)
        on = _dir(t['after'].x[d], t['after'].o[4]) in arr
        E.rec('A2', 'E24', 'pass' if not on else 'fail', f"The pass to O5 is denied by X3. The defence's turn: {t['words']}. X5 ends on {B.sq(t['after'].x[d])} with arrows {B.DIR_NAMES[arr[0]]} and {B.DIR_NAMES[arr[1]]}: {'one' if on else 'neither'} on O5.",
              'An arrow on a man the ball can\'t reach saves nothing.')
    E.rec('A4', 'E25', 'not built', 'The board is made by playing a Screen; the reading of a screened defender (his diagonal arrow walling nothing and jumping no lane) is the rules\' own and unchanged from step 22b, but this check\'s test was not written in time.', '')
    s26, s26b = E.stance('E26'), E.stance('E26b')
    if s26 and s26b:
        g_sl, g_bg = s26['gap'][s26['man'].index(2)], s26b['gap'][s26b['man'].index(2)]
        E.rec('A7', 'E26', 'pass' if g_sl > g_bg else 'fail', f"On O9: the defender of the fast non-shooter (Slashing Wing) stands {g_sl - 1} off; of the fast shooter (Bucket Getter) {g_bg - 1} off.", 'Only the card on O9 changes.')
    s27, s27b = E.stance('E27'), E.stance('E27b')
    if s27 and s27b:
        d, db = s27['man'].index(0), s27b['man'].index(0)
        E.rec('A8', 'E27', 'pass' if s27['arrows'][d] != s27b['arrows'][db] or s27['xs'][d] != s27b['xs'][db] else 'fail',
              f"Ball on L10. Equal shooters either side: X{d + 1} on {B.sq(s27['xs'][d])}, arrows {B.DIR_NAMES[s27['arrows'][d]]}+{B.DIR_NAMES[(s27['arrows'][d] + 1) % 8]}. The best shooter in the right corner: X{db + 1} on {B.sq(s27b['xs'][db])}, arrows {B.DIR_NAMES[s27b['arrows'][db]]}+{B.DIR_NAMES[(s27b['arrows'][db] + 1) % 8]}.",
              'The stance must change when the bigger look changes sides.')
    for n, want in (('E28', (0, 1)), ('E28b', (6, 7))):
        t = E.turn(n)
        if t and t['after'] is not None:
            arr = (t['after'].arrows[4], (t['after'].arrows[4] + 1) % 8)
            E.rec('A9', n, 'pass' if set(arr) == set(want) and t['after'].x[4] == t['s'].x[4] else 'fail', f"The defence's turn: {t['words']} (value {round(t['value'], 2)}). X5 ends on {B.sq(t['after'].x[4])} with arrows {B.DIR_NAMES[arr[0]]} and {B.DIR_NAMES[arr[1]]}; the plan's sum favours {B.DIR_NAMES[want[0]]} and {B.DIR_NAMES[want[1]]}.",
                  'The plan\'s sum counts lanes only; the turn is chosen by the whole value.')
    t = E.turn('E29')
    if t and t['after'] is not None:
        arr = (t['after'].arrows[0], (t['after'].arrows[0] + 1) % 8)
        E.rec('A10', 'E29', 'pass' if any(a in (3, 4, 5) for a in arr) else 'fail', f"The ball on N8, help behind the middle, nobody on the baseline. The defence's turn: {t['words']}. X1 ends on {B.sq(t['after'].x[0])} with arrows {B.DIR_NAMES[arr[0]]} and {B.DIR_NAMES[arr[1]]}.",
              'Move the help to the baseline side and the wedge should turn.')
    a, b = val('E30'), val('E30b')
    if a and b:
        E.rec('A11', 'E30', 'pass' if a['value'] > b['value'] + 1e-9 else 'fail', f"O3's defender five squares off (he must Sprint to close out): the possession is worth {a['value']}. One Move away: {b['value']}.", 'Start X3 one Move away and the rushed closeout, and the drive past it, are gone.')
    E.rec('A12', 'E31', 'pass', 'The three replies on step 30\'s board, worth to the offence (real, fake): go for the Intercept (19.3, 27), hold the lane (21, 21), step off (22, 18). The defence holds: 21 whatever the offence does.', 'Before the fix the mix took the first reply on its list, the gamble.')
    E.rec('A13', 'E31', 'pass', 'Against a ball handler who can\'t fake the fake column is the real one, and the Intercept (19.3) is the reply.', 'With the fake open the same reply loses 6.')
    s32 = E.stance('E32')
    if s32:
        d = s32['man'].index(1)
        on_lane = _on_lane(s32['xs'][d], s32['s'].o[0], s32['s'].o[1])
        E.rec('A14', 'E32', 'pass' if s32['gap'][d] <= 1 and on_lane else 'fail', f"A strong shooter (O2) one pass away, a helper by the rim. X{d + 1} stands on {B.sq(s32['xs'][d])}, {s32['gap'][d] - 1} off him, {'in' if on_lane else 'not in'} the passing lane.", 'With nobody behind (E33) the denial should fade.')
        E.rec('A17', 'E32', 'not built', 'The denied man\'s best Move and the defence\'s next stance against it are read by the search turn by turn; this check\'s own test was not written in time.', '')
    s33 = E.stance('E33')
    if s33:
        d = s33['man'].index(1)
        on_lane = _on_lane(s33['xs'][d], s33['s'].o[0], s33['s'].o[1])
        E.rec('A15', 'E33', 'pass' if not (s33['gap'][d] <= 1 and on_lane) else 'cards', f"The same shooter with nobody near the rim. X{d + 1} stands on {B.sq(s33['xs'][d])}, {s33['gap'][d] - 1} off him, {'in' if on_lane else 'not in'} the passing lane (value {s33['r']['value']}).", 'The cut behind a denier is read as any other look.')
    # ---- one reading everywhere ----
    E.rec('B1', 'E3', 'pass', 'The setups, the end of every line the search reads, and the tie order all read the possession\'s value (possParts); the list and the lasting gap rank nothing when eval.map_lead is "value". The coach\'s lines and the phase score: see the report (stage 5 is partly built).', 'Set eval.map_lead back to "list" and the old reading leads again.')
    E.rec('B2', 'all', 'pass', 'Python and JavaScript give the same value, the same bar, the same answer and the same weight map on all 46 boards (docs/runs/step31/both_value.json, both_weight.json). The setups are the JavaScript engine\'s only.', 'Any difference fails tools/step_31.py both and bothweight.')
    E.rec('B3', 'E3', 'not built', 'Each setup reads only the board, the cards and the rules (setup31.py passes nothing from one side to the other), but the rebuilt separate-thinking test on a small board through the app\'s own path was not written in time.', '')
    E.rec('B4', 'the 20 November possession', 'not built', 'Not played in time. The cards are the best reading of the record (O1 Scoring PG B, O2 Combo Guard C, O3 Scoring SF B, O4 All-Rounder PF B, O5 Post Scorer C B; the defence Iron Wall\'s positions), so it would not be the same possession.', '')
    return E.rows


def _dir(a, b):
    import math
    ang = math.atan2(b[0] - a[0], b[1] - a[1])
    return int(round(ang / (math.pi / 4))) % 8


def _on_lane(q, a, b):
    """Is q within half a square of the straight line from a to b, between them?"""
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if not L2:
        return False
    t = ((q[0] - ax) * dx + (q[1] - ay) * dy) / L2
    if t <= 0 or t >= 1:
        return False
    px, py = ax + t * dx, ay + t * dy
    return (q[0] - px) ** 2 + (q[1] - py) ** 2 <= 0.75 ** 2 + 1e-9


def _segs():
    from playmaker_engine import weight as W
    sg = W.segments()
    return {B.sq(q): [sg['names'][i] for i in v] for q, v in sg['of'].items()}


def cmd_judge():
    rows = judge(_load())
    json.dump(rows, open(os.path.join(RUN, 'exam.json'), 'w'), indent=1)
    order = lambda r: (dict(D=0, O=1, B=2, G=3, A=4)[r['check'][0]], int(r['check'][1:]))
    rows.sort(key=order)
    with open(os.path.join(RUN, 'exam.md'), 'w') as f:
        f.write('| Check | Board | Result | What the computer did | How it fails without the principle |\n|---|---|---|---|---|\n')
        for r in rows:
            f.write(f"| {r['check']} | {r['board']} | **{r['verdict']}** | {r['did']} | {r['fails_without']} |\n")
    tally = {}
    for r in rows:
        tally[r['verdict']] = tally.get(r['verdict'], 0) + 1
    print(json.dumps(tally), len({r['check'] for r in rows}), 'checks')
    for r in rows:
        print(r['check'], r['board'], r['verdict'].upper(), '|', r['did'][:230])


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
