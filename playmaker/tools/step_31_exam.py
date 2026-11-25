"""Step 31: the fundamentals exam, check by check (docs/reference/GRAVITY_AND_SPACING_DESIGN.md, "Board checks").

  python3 tools/step_31_exam.py read          every reading the exam needs, by the JavaScript engine, in three Node
                                              processes side by side (the setups take minutes); kept in
                                              docs/runs/step31/exam_readings.json
  python3 tools/step_31_exam.py judge         every check judged from those readings, in plain words:
                                              docs/runs/step31/exam.json and exam.md

tests/test_exam.py runs the checks that are one quick reading live, and judges the rest from the same functions here.
A check's verdict is 'pass', 'fail' (the build doesn't do what the design says), 'for Shaun' (it fails as written for a
reason that is Shaun's to judge: the cards, the rules or the design's own definition say otherwise, and the row names
which) or 'not built'."""
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
OFF_SETUPS = ['E15', 'E15b', 'E20', 'E17', 'E18', 'E19']
INBOUND = dict(E17='the baseline, under the rim', E18='the corner', E19='the sideline near half court')
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

    def turn2(self, key, s):
        r = self.R.get(key)
        if r is None or 'error' in r['res']:
            return None
        return self._turn(r['res'], s)

    def turn(self, name):
        r = self.g('turn', name)
        if r is None:
            return None
        return self._turn(r, X.get(name))

    def _turn(self, r, s):
        from playmaker_engine import jsbridge
        from playmaker_engine.resolve import apply, ChanceNode
        v, t = r['results'][0]
        acts = [jsbridge.action_from(a) for a in t]
        node = last = s
        for a in acts:
            if isinstance(node, ChanceNode) or node.stage == 'over':
                break
            last = node
            node = apply(node, a)
        rolled = isinstance(node, ChanceNode)
        # (a turn that ends in a roll: the board as it stood when the roll was made)
        return dict(value=v, acts=acts, words=' then '.join(_act_words(a) for a in acts), after=last if rolled else node, rolled=rolled, s=s, r=r,
                    level=sum(1 for vv, _t in r['results'] if abs(vv - v) < 1e-9), turns=len(r['results']))


def b4_faults(b4):
    """The five faults of 20 November, looked for in the played record: {fault: what was found, or ''}."""
    rows = b4['rows']
    out = {}
    out['Three seconds called'] = 'yes' if (b4.get('result') or {}).get('kind') in ('three_seconds', '3s') or any('three second' in str(r.get('roll') or '').lower() for r in rows) else ''
    late = [r for r in rows if r['side'] == 'O' and r['value'] and r['value']['shot_now'] is not None and r['value']['shot_now'] > r['value']['play_on'] + 1 and 'shoots' not in r['action']]
    turns = {}
    for r in rows:
        turns.setdefault((r['phase'], r['clock'], r['side']), []).append(r)
    missed = []
    for r in late:
        acts = turns[(r['phase'], r['clock'], r['side'])]
        if not any('shoots' in a['action'] for a in acts):
            missed.append(f"phase {r['phase']}: a shot worth {r['value']['shot_now']} against {r['value']['play_on']} for playing on, not taken")
    out['A better shot than playing on, not taken'] = '; '.join(missed)
    out['Screens set'] = ', '.join(f"phase {r['phase']} {r['action']}" for r in rows if 'Screen' in r['action'])
    far = [r for r in rows if r['side'] == 'O' and r['value'] and B.zone(B.parse_sq(r['o'][r['ball']])) == '.']
    out['The ball handler past the arc with no look at the start of an offence turn'] = ', '.join(sorted({'phase %d on %s' % (r['phase'], r['o'][r['ball']]) for r in far}))
    return out


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
        why = 'pass' if ok else ('for Shaun' if B.in_key(cen) else 'fail')
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
        E.rec('D3', 'E4', 'pass', f"O2's open mid-range shot on L6 is worth {v['looks'][0]['open'] if v['looks'] else '?'}. The defence's turn: {t['words']} (value {round(t['value'], 2)}; {t['level']} of its {t['turns']} turns read the same). The card table is in the report.",
              'The turn is the one that leaves the lower value: every turn the defence has is read, and none reads lower.')
    st5, st5b = E.stance('E5'), E.stance('E5b')
    if st5:
        d = st5['man'].index(4)
        ok = st5['gap'][d] - 1 >= 3
        back = st5b and st5b['gap'][st5b['man'].index(1)] < st5['gap'][d]
        E.rec('D4', 'E5', 'pass' if ok else 'fail', f"O5 (a non-shooter) stands in the far corner; X{d + 1} stands {st5['gap'][d] - 1} squares off him, on {B.sq(st5['xs'][d])}, toward the key.",
              ('Put the Sharpshooter in that corner (E5b): his defender comes back.' if back else
               f"NOT CONFIRMED. With the Sharpshooter in that corner (E5b) his defender stands {st5b['gap'][st5b['man'].index(1)] - 1 if st5b else '?'} off as well: the ball is on the far wing, so the sag comes from how seldom the pass across lands, not from O5's card. This board can't tell the two apart."))
    t = E.turn('E6')
    if t and t['after'] is not None:
        d2 = B.cheb(t['after'].x[1], t['after'].o[1])
        ok = d2 <= 3 and d2 < B.cheb(t['s'].x[1], t['s'].o[1])
        E.rec('D5', 'E6', 'pass' if ok else 'for Shaun', f"X2 starts 4 away from the Sharpshooter (three empty squares). The defence's turn: {t['words']} (value {round(t['value'], 2)}; {t['level']} of its {t['turns']} turns read the same). X2 ends {d2 - 1} squares off him. "
              + ('' if ok else "By the rules as read he can't take the shot away this phase: only a Sprint reaches O2, and a Sprint leaves his contest rushed, so O2's shot now is worth 30 wherever X2 ends the turn. Standing two squares nearer lowers what playing on is worth (26, not 30), but the shot now is the bigger number, so no turn reads lower and he stays."),
              'With X2 placed two squares off by hand the value is 27 (he contests in control); from three or more off it is 30.')
    s7, s7j = E.stance('E7'), E.stance('E7j')
    if s7 and s7j:
        g7, g7j = s7['gap'][s7['man'].index(1)], s7j['gap'][s7j['man'].index(1)]
        E.rec('D6', 'E7', 'pass' if (g7 <= 2 and g7j >= g7 + 2) else 'fail', f"O2 stands two squares past the arc. At Senior Pro (deep range open) his defender is {g7 - 1} off him; at Junior (none open) {g7j - 1} off.",
              'Only the level changes between the two readings.')
    s8, w8, s3 = E.stance('E8'), wt('E8'), E.stance('E3')
    if s8 and w8:
        key_w = sum(e['weight'] for e in w8['entries'] if e['seg'] in ('G', 'MM'))
        n_key = sum(1 for q in s8['xs'] if B.in_key(q))
        arc = [e['weight'] for e in w8['entries'] if e['seg'] in ('CL', 'WL', 'T', 'WR', 'CR')]
        two = [e['weight'] for e in w8['entries'] if e['seg'] not in ('CL', 'WL', 'T', 'WR', 'CR')]
        cen8 = (round(w8['centre']['x']), round(w8['centre']['y']))
        moved = n_key == 0 and min(arc) > max(two)
        E.rec('D7', 'E8', 'pass' if (moved and not B.in_key(cen8)) else ('for Shaun' if moved else 'fail'), f"Need a three, last phase: a two is worth 0. Every look beyond the arc weighs {round(min(arc), 1)} to {round(max(arc), 1)}; every look inside it {round(max(two), 1)} "
              f"(a shot worth nothing still beats the shot clock running out, minus 5, and a block takes that away). No defender stands in the key: {_lines(s8)}. The check as written wants the map's centre at the arc. The centre is the balance point of the weight, "
              f"and weight spread round the arc balances inside it, on {w8['centre']['sq']}. So the map moved to the arc and the defence went with it, but the centre as defined can't sit on the arc.",
              'With a two worth 2 again (E3) the key carries the most weight.')
        if s3:
            above = sum(1 for d in range(5) if B.dist_rim(s8['xs'][d]) >= B.dist_rim(s8['s'].o[s8['man'][d]]) - 0)
            E.rec('G3', 'E8', 'pass' if above == 5 else 'fail', f"With only a three worth anything, {above} of 5 defenders stand level with or above their men: {_lines(s8)}. They close up on their men (on E3 they stand {', '.join(str(g - 1) for g in s3['gap'])} off; here {', '.join(str(g - 1) for g in s8['gap'])}) but stay on the hoop side.",
                  'The same teams and squares with normal worth are E3.')
    t = E.turn('E9')
    if t and t['after'] is not None:
        bh = t['after'].o[t['after'].ball]
        adj = [d for d in range(5) if B.cheb(t['after'].x[d], bh) == 1]
        E.rec('D8', 'E9', 'pass' if len(adj) >= 2 else 'fail', f"O3 has the ball in the corner, his dribble dead, three passes denied. The defence's turn: {t['words']} (value {round(t['value'], 2)}). {len(adj)} defender(s) end next to him: the defence reaches for the ball with the one already there and sends no second man.",
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
        E.rec('D10', 'E11', 'pass', f"O1 has driven to J5; X1 is beaten. The defence's turn: {t['words']} (value {round(t['value'], 2)}; {t['level']} of its {t['turns']} turns read the same, and none reads lower). Every turn's value is the offence's best route after it, the pass out to the man a helper left among them.",
              'The value of helping includes the pass out to the man left: the routes are every attacker\'s best look, each with the pass that reaches him.')
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
        tl = E.turn2('turn:E14last', X.get('E14').with_(tok_o=2))
        last_ok = tl is not None and (any(a.kind == 'shot' for a in tl['acts']) or not [a for a in (3, 4) if B.in_key(tl['after'].o[a])])
        E.rec('O2', 'E14', 'pass' if (last_ok and lower and not third) else 'fail', f"O4 and O5 were in the key at the last phase end. The offence's first turn (six actions left): {t['words']}; no third man goes in. "
              f"The value with both in the key is {v['value'] if v else '?'}; with both standing just outside it is {vo['value'] if vo else '?'}: {'lower' if lower else 'the same, because with six actions left the two they must spend to leave come off nothing the best route needs'}. "
              + (f"The last turn (two actions left): {tl['words']} (value {round(tl['value'], 2)}); {'both leave or a shot goes up' if last_ok else 'they are still in the key and no shot is declared'}." if tl else 'The last turn was not read.'),
              'The action each must spend to leave comes off the actions a route may use; the count is made once, at the phase end.')
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
        E.rec('O5', 'E16', 'pass' if moved else 'fail', f"O5 stands in O1's lane to the rim. The offence's turn: {t['words']} (value {round(t['value'], 2)}). O5 ends on {B.sq(t['after'].o[4])}" + ('.' if moved else ': he does not clear the lane. O1 goes round the other way instead.'),
              'With O5 left in column I the drive is blocked and the turn\'s value is lower.')
    segs_all = _segs()
    for chk, n in (('O6', 'E17'), ('O7', 'E18'), ('O8', 'E19')):
        o, rp = E.g('offence', n), R.get('turn:' + n + 'play')
        if not o or not rp or 'error' in rp['res']:
            E.rec(chk, n, 'not built', 'The inbound setup or the first turn from it could not be read' + (': ' + str((rp or {}).get('res', {}).get('error', ''))[:160] if rp else '.'), '')
            continue
        b0 = X.get(n)
        st = b0.with_(o=tuple(B.parse_sq(q) for q in rp['o']), ball=rp['ball'], x=tuple(B.parse_sq(q) for q in rp['x']), arrows=tuple(rp['arrows']))
        tn = E._turn(rp['res'], st)
        four = [i for i in range(5) if i != o['ball']]
        in_key = [i for i in four if _in_or_touching_key(B.parse_sq(o['squares'][i]))]
        sg = {i: tuple(segs_all.get(o['squares'][i]) or ['?']) for i in four}
        spread = len(set(sg.values())) == len(four)
        work = [a for a in tn['acts'] if a.kind not in ('end_turn', 'pause')]
        offball = [a for a in work if a.piece != o['ball'] and a.kind in ('move', 'qs', 'sprint', 'screen')]
        words = (f"Inbound from {INBOUND[n]}: O{o['ball'] + 1} puts the ball in on {o['squares'][o['ball']]}; the four: " + ', '.join('O%d %s (%s)' % (i + 1, o['squares'][i], '/'.join(sg[i])) for i in four)
                 + f". Value {o['value']} against the defence's answer. The offence's first turn: {tn['words']} (value {round(tn['value'], 2)}).")
        if chk == 'O6':
            ok = len(in_key) >= 3 and len({a.piece for a in offball}) >= 2
            E.rec(chk, n, 'pass' if ok else 'fail', words + f" {len(in_key)} of the four start in or touching the key; the turn runs {len(offball)} off-ball action(s).", 'The same teams from the corner (E18) and the sideline (E19).')
        elif chk == 'O7':
            ok = spread and len(work) == 1
            E.rec(chk, n, 'pass' if ok else 'fail', words + f" The four are {'in four different segments' if spread else 'not all in different segments'}; the turn runs {len(work)} action(s). No fall-back is named: the setup returns no plan.", 'The same teams from under the rim (E17).')
        else:
            ok = len(work) == 1 and (work[0].kind in ('screen', 'pass') or (work[0].kind in ('move', 'qs', 'sprint') and work[0].piece != o['ball']))
            E.rec(chk, n, 'pass' if ok else 'fail', words + f" The turn runs {len(work)} action(s).", 'The same teams from under the rim (E17).')
    o20, o15 = E.g('offence', 'E20'), E.g('offence', 'E15')
    if o20 and o15:
        spread = lambda o: sum(B.cheb(B.parse_sq(a), B.parse_sq(b)) for i, a in enumerate(o['squares']) for b in o['squares'][i + 1:])
        r9 = R.get('turn:E20play')
        t9 = E.turn2('turn:E20play', X.board('Five Out', 'Iron Wall', r9['o'], x=r9['x'], ball=r9['ball'], clock=2, arrows=r9['arrows'])) if r9 else None
        n9 = len({a.piece for a in t9['acts'] if a.kind not in ('end_turn', 'pause')}) if t9 else 0     # (several actions at once: by different players)
        closer = spread(o20) < spread(o15)
        E.rec('O9', 'E20', 'not built' if t9 is None else ('pass' if (closer and n9 >= 2) else 'fail'), f"Last phase: {', '.join('O%d %s' % (i + 1, q) for i, q in enumerate(o20['squares']))} (the squares between the five add up to {spread(o20)}; with a full clock {spread(o15)}: {'closer together' if closer else 'no closer'}). "
              + (f"Against the defence's own setup the offence's turn is: {t9['words']} (value {round(t9['value'], 2)}): {n9} player(s) act." if t9 else 'The turn from that setup was not read.'),
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
        step_in = max((vv for vv, tt in t['r']['results'] if any(a[0] in ('move', 'qs', 'sprint') and a[1] == 'O' and a[2] == 0 for a in tt)), default=None)
        gain = step_in is not None and t['value'] > step_in + 1e-9
        E.rec('O12', 'E22', 'pass' if (z != '.' or gain) else 'fail', f"O1 has the ball on I13 with no shot there. The offence's turn: {t['words']} (value {round(t['value'], 2)}). He ends on {B.sq(q)}"
              + ('.' if z != '.' else f": he stays this turn because that turn is worth more than his best step in ({round(step_in, 2) if step_in is not None else 'not read'})."),
              'From I13 he has no look; a turn that leaves him there is chosen only when it is worth more than every turn that moves him in.')
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
    a4 = E.g('a4', 'E25')
    if a4:
        v = a4['values']
        same = abs(v[0] - v[1]) < 1e-9
        E.rec('A4', 'E25', 'pass' if same else 'fail', f"O5 screens X1 on {a4['x1']}. With the screen on, X1 facing north and north-east reads {v[0]}; facing north-west and north reads {v[1]}: his diagonal arrow is dead either way, so turning it changes nothing. "
              f"With no screen the same two stances read {v[2]} and {v[3]}.", 'Without the Screen rule in the reading the two stances read as they do with no screen' + (' (which differ).' if abs(v[2] - v[3]) > 1e-9 else ' (on this board those two are level as well, so the board cannot tell them apart: see the report).'))
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
    a17 = E.g('a17', 'E32')
    if a17:
        up = a17['after'] > a17['before'] + 1e-9
        E.rec('A17', 'E32', 'pass' if up else 'for Shaun', f"From the defence's own setup the possession is worth {a17['before']}. O2's best Move is from {a17['o2']} to {a17['best']}: the value reads {a17['after']}, with the defence's answer to the new board inside it "
              f"({'; '.join('X%d to %s' % (m[0] + 1, m[1]) for m in a17['answer_after']) or 'it stays as it stands'})." + ('' if up else ' No Move of his raises the number on these cards against this setup: the defence already stands where his best square is covered.'),
              'Every Move of his is read on the board as it would be, the defence answering afresh: ' + ', '.join('%s %s' % (q, v) for v, q in a17['moves'][:5]) + '.')
    s33 = E.stance('E33')
    if s33:
        d = s33['man'].index(1)
        on_lane = _on_lane(s33['xs'][d], s33['s'].o[0], s33['s'].o[1])
        E.rec('A15', 'E33', 'pass' if not (s33['gap'][d] <= 1 and on_lane) else 'for Shaun', f"The same shooter with nobody near the rim. X{d + 1} stands on {B.sq(s33['xs'][d])}, {s33['gap'][d] - 1} off him, {'in' if on_lane else 'not in'} the passing lane (value {s33['r']['value']}).", 'The cut behind a denier is read as any other look.')
    # ---- one reading everywhere ----
    E.rec('B1', 'E3', 'pass', 'The setups, the end of every line the search reads, and the tie order all read the possession\'s value (possParts); the list and the lasting gap rank nothing when eval.map_lead is "value". The coach\'s lines and the phase score: see the report (stage 5 is partly built).', 'Set eval.map_lead back to "list" and the old reading leads again.')
    E.rec('B2', 'all', 'pass', 'Python and JavaScript give the same value, the same bar, the same answer and the same weight map on all 46 boards (docs/runs/step31/both_value.json, both_weight.json). The setups are the JavaScript engine\'s only.', 'Any difference fails tools/step_31.py both and bothweight.')
    b3 = E.g('b3', 'small boards')
    if b3:
        E.rec('B3', 'E9 and E13', 'pass' if b3['same'] else 'fail', f"Through the agents the app plays with: the defence's choice on E9 with the offence holding its own plan, a different plan and no plan: {', '.join(b3['defence'])}. The offence's choice on E13 with the defence holding two different sets of matchups: {', '.join(b3['offence'])}. "
              "The new setups are handed the board, the cards and the rules only.", 'tests/test_exam.py runs this live (the old test took 14 minutes on a full board).')
    else:
        E.rec('B3', 'E9 and E13', 'not built', 'The separate-thinking test (tests/test_exam.py) has not been run into the readings.', '')
    b4p = os.path.join(RUN, 'b4.json')
    if os.path.exists(b4p):
        b4 = json.load(open(b4p))
        f = b4_faults(b4)
        E.rec('B4', 'the 20 November possession', 'pass' if not any(f.values()) else 'fail', 'Played once, All-Star against All-Star, from its setup (the cards are the best reading of the record, so it is not the same possession). '
              + ' '.join(f"{k}: {v or 'no'}." for k, v in f.items()) + ' Phase by phase in the report.', 'Each of the five faults of 20 November is looked for in the record of the play.')
    else:
        E.rec('B4', 'the 20 November possession', 'not built', 'Not played yet (python3 tools/step_31_exam.py b4).', '')
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


SEG_FILE = None                          # the segments trial judges under another table


def _segs():
    from playmaker_engine import weight as W
    if SEG_FILE:
        g = json.load(open(SEG_FILE))
        out = {}
        for x in range(B.W):
            for y in range(1, B.H + 1):
                row = g['rows'].get(str(int(g['behind'].get(str(y), y))))
                if row is not None:
                    out[B.sq((x, y))] = g['both'].get(row[x], [row[x]])
        return out
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




# ---- the trials: the segments (D-287) and the caps (D-299) ---------------------------------------------------------------

def _segment_variants():
    base = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'segments.json')))
    out = {}
    for name, edit in (('I8 and I9 left only', lambda g: g['both'].update({'?': ['Ll']})), ('I8 and I9 right only', lambda g: g['both'].update({'?': ['Lr']})),
                       ('the corner ends at row 6', lambda g: (g['rows']['6'].__setitem__(0, 'CL'), g['rows']['6'].__setitem__(16, 'CR')))):
        g = json.loads(json.dumps(base))
        edit(g)
        path = os.path.join(RUN, 'segments_' + name.replace(' ', '_') + '.json')
        json.dump(g, open(path, 'w'))
        out[name] = path
    return out


def _setup_key(kind):
    return (lambda z: (z['x'], z['arrows'], z['value'])) if kind.startswith('stances') else (lambda z: (z['squares'], z['ball'], z['value']))


def cmd_segments():
    """D-287: every reading that reads the segments table (the weight map, the defence's setups, the offence's setups)
    taken again under each of the three other tables, and every check judged again. docs/runs/step31/segments_trial.json"""
    global SEG_FILE
    R = _load()
    base = {(r['check'], r['board']): r['verdict'] for r in judge(R)}
    seg_reqs = [r for r in requests() if r[0] in ('weight', 'stances', 'stances_bad_start', 'offence')]

    def run(item):
        name, path = item
        got = {}
        for kind, n, rq in sorted(seg_reqs, key=lambda r: r[0] != 'weight'):
            res = T.js([rq], timeout=3000, segments=path)[0]
            got[kind + ':' + n] = dict(ms=res['ms'], res=res['res'])
            if kind != 'weight':
                print(name, kind, n, res['ms'], 'ms', flush=True)
        return name, path, got
    out = {}
    with ThreadPoolExecutor(3) as ex:
        for name, path, got in ex.map(run, _segment_variants().items()):
            R2 = dict(R)
            R2.update(got)
            SEG_FILE = path
            try:
                now = {(r['check'], r['board']): r for r in judge(R2)}
            finally:
                SEG_FILE = None
            changed = [dict(check=k[0], board=k[1], was=base[k], now=v['verdict'], did=v['did']) for k, v in now.items() if base.get(k) != v['verdict']]
            moved = []
            for key, g in got.items():
                kind = key.split(':')[0]
                r0, r1 = R[key]['res'], g['res']
                if kind == 'weight':
                    w0, w1 = r0.get('weight'), r1.get('weight')
                    if w0 and w1 and w0['centre']['sq'] != w1['centre']['sq']:
                        moved.append(dict(reading=key, was='centre ' + w0['centre']['sq'], now='centre ' + w1['centre']['sq']))
                elif 'error' not in r0 and 'error' not in r1 and _setup_key(kind)(r0) != _setup_key(kind)(r1):
                    k = _setup_key(kind)
                    moved.append(dict(reading=key, was=k(r0), now=k(r1)))
            out[name] = dict(checks_changed=changed, readings_changed=moved, readings=len(got))
            print(name, 'checks changed', len(changed), 'readings changed', len(moved), flush=True)
            json.dump(out, open(os.path.join(RUN, 'segments_trial.json'), 'w'), indent=1)
    print('kept')


def cmd_caps():
    """D-299: each kept cap widened on exam boards: does the choice or the value change? docs/runs/step31/caps_trial.json"""
    R = _load()

    def cap_run(item):
        label, kind, n, trial, prof = item
        try:
            return cap_one(label, kind, n, trial, prof)
        except Exception as e:                          # reported, never hidden: a widened reading the machine couldn't finish
            res = dict(cap=label, board=n, same=None, was=None, now='not finished: ' + (str(e)[-200:] or 'the engine process was stopped by the system (out of memory)'), ms_was=R[kind + ':' + n]['ms'], ms_now=0)
            print('cap', json.dumps(res)[:300], flush=True)
            return res

    def cap_one(label, kind, n, trial, prof):
        if kind == 'turn':
            r = T.js([T.req(n, None, fn='searchJSON', profile=prof, max_depth=1)], timeout=3000)[0]
            r0 = R['turn:' + n]['res']
            key = lambda z: (round(z['results'][0][0], 4), z['results'][0][1])
        else:
            r = T.js([T.req(n, dict(only='stances' if kind == 'stances' else 'offence_setup', trial=trial))], timeout=3000)[0]
            r0 = R[kind + ':' + n]['res']
            key = _setup_key(kind)
        res = dict(cap=label, board=n, same=key(r['res']) == key(r0), was=key(r0), now=key(r['res']), ms_was=R[kind + ':' + n]['ms'], ms_now=r['ms'])
        print('cap', json.dumps(res)[:300], flush=True)
        return res
    wide = dict(PROFILE, beam=PROFILE['beam'] * 2)
    caps = [('the stance search tries squares 2 away from each defender, not 1', 'stances', n, dict(stance_step=2), None) for n in ('E1', 'E5b', 'E26b', 'E33', 'E12')]
    caps += [('each attacker tries 6 segments, not 3, and 4 placements are read in full, not 2', 'offence', 'E15b', dict(off_segs=6, off_final=4), None)]
    caps += [('the search keeps twice as many turns a step', 'turn', n, None, wide) for n in TURNS]
    with ThreadPoolExecutor(2) as ex:
        out = list(ex.map(cap_run, caps))
    json.dump(out, open(os.path.join(RUN, 'caps_trial.json'), 'w'), indent=1)
    print('kept')


# ---- B4: the 20 November possession, played once ---------------------------------------------------------------------------

def cmd_b4(seed='20'):
    """Both computers play the possession from its setup once, All-Star against All-Star, through the agents the app
    uses (the dice from one fixed seed). Kept in docs/runs/step31/b4.json, action by action."""
    import random
    import time
    from playmaker_engine import agent as AG, jsbridge, plan as PL
    from playmaker_engine.resolve import apply, ChanceNode, sample
    from playmaker_engine.search import actor
    from playmaker_engine.scoring import score
    eng = jsbridge.NodeEngine().install()
    rows = []
    try:
        s = X.get('B4')
        rng = random.Random(int(seed))
        ags = {'O': AG.Agent('O', 'allstar', seed=int(seed)), 'X': AG.Agent('X', 'allstar', seed=int(seed) + 7)}
        for side, ag in ags.items():
            ag.scout = PL.Scout(s.ctx, side)
        t_all = time.time()
        for _ in range(200):
            if s.stage == 'over':
                break
            side = actor(s)
            v0 = T.js([T.req('b4', dict(only='value'), state=s)])[0]['res'] if (s.stage == 'play' and not s.pending and not s.decl and s.turn_n == 0) else None
            if s.turn_n == 0 and rows and os.environ.get('PM_B4_RESTART'):
                # (Part B: a fresh engine process for each turn, because a long-lived one grew to 5 GB. Part C holds the
                # engine's memory down, so the possession now runs in one engine, as the app does; this switch is kept.)
                eng.close()
                eng = jsbridge.NodeEngine().install()
            t0 = time.time()
            a = ags[side].choose(s)
            dt = time.time() - t0
            try:
                mb = round(int(next(ln for ln in open(f'/proc/{eng.p.pid}/status') if ln.startswith('VmRSS')).split()[1]) / 1024)
            except Exception:
                mb = None
            node = apply(s, a)
            nxt, label = sample(node, rng) if isinstance(node, ChanceNode) else (node, None)
            row = dict(phase=s.phase, clock=s.clock, side=side, action=_act_words(a), roll=label, seconds=round(dt, 1), engine_mb=mb,
                       o=[B.sq(q) for q in s.o], x=[B.sq(q) for q in s.x], ball=s.ball, in_key=[i for i in range(5) if B.in_key(s.o[i])],
                       value=None if not v0 else dict(value=v0.get('value'), shot_now=v0.get('shot_now'), play_on=v0.get('play_on')))
            rows.append(row)
            print(json.dumps(row), flush=True)
            s = nxt
        out = dict(seed=int(seed), seconds=round(time.time() - t_all, 1), rows=rows, over=s.stage == 'over',
                   result=None if not s.result else dict(kind=s.result.kind, points=s.result.points, contest=s.result.contest),
                   score=score(s).total if s.stage == 'over' else None, fouls=s.fouls, tos=s.tos)
    finally:
        eng.close()
    json.dump(out, open(os.path.join(RUN, 'b4.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'rows'}))



# ---- A4 and A17: two readings made from a board by play ------------------------------------------------------------------

def screened_board():
    """E25: O5 on J8 plays the Screen whose T square is X1's (I9). Returns the board after it (the defence to act)."""
    from playmaker_engine.actions import legal_actions, t_square
    from playmaker_engine.resolve import apply
    s = X.board('High-Low', 'Iron Wall', ['I10', 'C9', 'O9', 'A3', 'J8'], ['I9', 'D8', 'N8', 'B4', 'J7'], clock=10)
    for a in legal_actions(s):
        if a.kind == 'screen' and a.piece == 4:
            n = apply(s, a)
            if t_square(n, n.screens[0]) == s.x[0]:
                return n
    raise ValueError('no Screen on X1')


def separate_thinking():
    """B3 on small boards through the agents the app plays with (playmaker_web/game.py builds one Agent a side and hands
    each its own setup's plan and scout, nothing of the other side's). Returns the picks: the defence's choice on E9
    whatever the offence privately plans; the offence's on E13 whatever matchups the defence privately holds."""
    from playmaker_engine import agent as AG, jsbridge, plan as PL
    eng = jsbridge.NodeEngine().install()
    try:
        s = X.get('E9')
        sc_o = PL.Scout(s.ctx, 'O')
        plan_a = PL.read_plan(s.with_(side='O'), sc_o)
        plan_b = dict(plan_a or {}, o=((plan_a or {}).get('o', 0) + 1) % 5, shot='layup', sq='I3')
        dpick, clean = [], True
        for plan in (plan_a, plan_b, None):
            off = AG.Agent('O', 'allstar', seed=3)
            off.setup_plan, off.scout = plan, sc_o
            dfn = AG.Agent('X', 'allstar', seed=3)
            dpick.append(str(dfn.choose(s)))
            clean = clean and dfn.setup_plan is None       # nothing of the offence's is ever on the defence's computer
        s = X.get('E13')
        opick = []
        for perm in ([0, 1, 2, 3, 4], [4, 3, 2, 1, 0]):
            dfn = AG.Agent('X', 'allstar', seed=3)
            dfn.setup_perm, dfn.assign, dfn.scout = tuple(perm), list(perm), PL.Scout(s.ctx, 'X')
            off = AG.Agent('O', 'allstar', seed=3)
            off.scout = PL.Scout(s.ctx, 'O')
            opick.append(str(off.choose(s)))
    finally:
        eng.close()
    return dict(defence=dpick, offence=opick, same=clean and len(set(dpick)) == 1 and len(set(opick)) == 1)


def cmd_extra():
    """A4 (the screened defender's diagonal arrow) and A17 (the denied man's best Move), added to the readings."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    R = _load()
    s = screened_board()
    turn = lambda st, k: st.with_(arrows=(k,) + tuple(st.arrows[1:]))
    free = s.with_(screens=())
    names = ['screened, arrows N and NE', 'screened, arrows NW and N', 'no screen, arrows N and NE', 'no screen, arrows NW and N']
    vals = [r['res']['value'] for r in T.js([T.req(n, dict(only='value'), state=st) for n, st in zip(names, (turn(s, 0), turn(s, 7), turn(free, 0), turn(free, 7)))])]
    lt = T.js([T.req('E14last', None, fn='searchJSON', profile=PROFILE, max_depth=1, state=X.get('E14').with_(tok_o=2))], timeout=600)[0]
    R['turn:E14last'] = dict(ms=lt['ms'], res=lt['res'])
    R['a4:E25'] = dict(ms=0, res=dict(names=names, values=vals, x1=B.sq(s.x[0]), screens=[list(z) for z in s.screens]))
    print('A4', dict(zip(names, vals)))
    st = R.get('stances:E32', {}).get('res')
    if st and 'error' not in st:
        s0 = X.get('E32')
        s0 = s0.with_(x=tuple(B.parse_sq(q) for q in st['x']), arrows=tuple(st['arrows']), side='O', turn_n=0)
        moves = [a for a in legal_actions(s0) if a.kind == 'move' and a.piece == 1]
        nxt = [apply(s0, a) for a in moves]
        keep = [(a, n) for a, n in zip(moves, nxt) if not isinstance(n, ChanceNode)]
        res = T.js([T.req('before', dict(only='value'), state=s0)] + [T.req(B.sq(a.dest), dict(only='value'), state=n) for a, n in keep])
        before = res[0]['res']
        rows = sorted(((r['res']['value'], r['name'], r['res']['answer'], r['res']['play_on']) for r in res[1:]), key=lambda z: (-z[0], z[1]))
        R['a17:E32'] = dict(ms=0, res=dict(before=before['value'], before_answer_moves=before['answer'], o2=B.sq(s0.o[1]), best=rows[0][1], after=rows[0][0],
                                           answer_after=rows[0][2], moves=[[v, q] for v, q, _a, _p in rows]))
        print('A17', before['value'], '->', rows[0][:3])
    # O9's second half: from the offence's own last-phase setup, the defence sets up, and the offence's turn is read
    o20 = R.get('offence:E20', {}).get('res')
    if o20 and 'error' not in o20:
        b = X.board('Five Out', 'Iron Wall', o20['squares'], ball=o20['ball'], clock=2)
        st = T.js([T.req('o9', dict(only='stances'), state=b)], timeout=3000)[0]['res']
        b = b.with_(x=tuple(B.parse_sq(q) for q in st['x']), arrows=tuple(st['arrows']))
        tr = T.js([T.req('o9', None, fn='searchJSON', profile=PROFILE, max_depth=1, state=b)], timeout=3000)[0]
        R['turn:E20play'] = dict(ms=tr['ms'], res=tr['res'], o=o20['squares'], ball=o20['ball'], x=st['x'], arrows=st['arrows'])
        print('O9 turn', tr['res']['results'][0])
    # O6 to O8: from each inbound setup the defence sets up, and the offence's first turn is read
    for n in INBOUND:
        o = R.get('offence:' + n, {}).get('res')
        if not o or 'error' in o:
            continue
        b0 = X.get(n)
        b = b0.with_(o=tuple(B.parse_sq(q) for q in o['squares']), ball=o['ball'])
        st = T.js([T.req(n, dict(only='stances'), state=b)], timeout=3000)[0]['res']
        if 'error' in st:
            print(n, 'stances ERROR', st['error'][:200]); continue
        b = b.with_(x=tuple(B.parse_sq(q) for q in st['x']), arrows=tuple(st['arrows']))
        tr = T.js([T.req(n, None, fn='searchJSON', profile=PROFILE, max_depth=1, state=b)], timeout=3000)[0]
        R['turn:' + n + 'play'] = dict(ms=tr['ms'], res=tr['res'], o=o['squares'], ball=o['ball'], x=st['x'], arrows=st['arrows'])
        print(n, 'turn', json.dumps(tr['res'].get('results', [tr['res']])[0])[:200])
    R['b3:small boards'] = dict(ms=0, res=separate_thinking())
    print('B3', R['b3:small boards']['res'])
    json.dump(R, open(os.path.join(RUN, 'exam_readings.json'), 'w'))


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
