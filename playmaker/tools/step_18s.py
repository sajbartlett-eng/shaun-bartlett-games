"""Step 18s, stop one (D-199): the coverage map. Read on named positions, the design checks, check 1 by play.

  python3 tools/step_18s.py show [name]        the map on Shaun's board (or one named position), in words and numbers
  python3 tools/step_18s.py checks             design checks 1 to 6 by the map -> docs/runs/step18s/checks.json
  python3 tools/step_18s.py played TAG         check 1 by play: Shaun's defence against the placement the map reads smallest
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('SENSE_RUN', 'step18s')
os.environ.setdefault('SENSE_18N', '1')
import step_18r as R                                    # noqa: E402
Q, P, O, T, L, RUN, WORK, tally, RULES = R.Q, R.P, R.O, R.T, R.L, R.RUN, R.WORK, R.tally, R.RULES
_ENG = []


def cov(s, answers=None):
    from playmaker_engine import agent as AG
    from playmaker_engine.jsbridge import NodeEngine
    if not _ENG:
        _ENG.append(NodeEngine().install())
    return AG.coverage(s, answers)


def board(x=None, arrows=None, o=None, **kw):
    """Shaun's board of 15 November under the app's rules (the zone on)."""
    s = O.shaun_state(list(x or O.HIS[0]), list(arrows or O.HIS[1]), zone=True, **({'o': o} if o else {}))
    return s.with_(**kw) if kw else s


def brief(c):
    return dict(best=c['best'], answers=[f"X{a['x'] + 1} to {a['to']}" for a in c['answers']], left=c['left'], left_worth=c['left_worth'],
                dribble=c['dribble'] and dict(target=c['dribble']['target'], chance=c['dribble']['chance'], worth=c['dribble']['worth']),
                now=c['now'], worth=c['worth'], words=c['words'])


def cmd_show(name=''):
    s = board()
    t0 = time.time()
    c = cov(s)
    print(round(time.time() - t0, 2), 's')
    print(c['words'])
    print(json.dumps(brief(c), indent=1))
    print('who covers what:', c['covers'])
    for a in range(5):
        sq = c['squares'][a]
        top = sorted(sq.items(), key=lambda kv: -kv[1]['worth'])[:5]
        print(f'O{a + 1}', len(sq), 'squares; best:', [(k, v['worth'], v['shot'], v['reach'], v['cover']) for k, v in top])


def shot_now(st, i, kind='three'):
    """What a shot going up now is worth by the rules' own resolution, the defence with no token to react: the expected
    score over the dice."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    from playmaker_engine.scoring import score
    a = next(a for a in legal_actions(st.with_(side='O', turn_n=0)) if a.kind == 'shot' and a.shot == kind)

    def ev(n):
        if isinstance(n, ChanceNode):
            return sum(float(p) * ev(sub) for p, _, sub in n.outcomes)
        assert n.stage == 'over', n.stage
        return float(score(n).total)
    return round(ev(apply(st.with_(side='O', turn_n=0), a)), 1)


def pass_arrives(st, target):
    """The chance a pass from the ball handler to `target` arrives, by trying every answer the rules give the defence
    once it is in the air (an Intercept through a square, or one movement and then the Intercept). None: no pass."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    st = st.with_(side='O', turn_n=0)
    p = next((a for a in legal_actions(st) if a.kind == 'pass' and a.target == target), None)
    if p is None:
        return None
    n = apply(st, p)
    worst = 1.0
    for a in legal_actions(n) if not isinstance(n, ChanceNode) and n.pending else []:
        if a.kind == 'intercept':
            n2 = apply(n, a)
        elif a.kind in ('move', 'qs', 'sprint'):
            m = apply(n, a)
            if isinstance(m, ChanceNode) or not m.pending:
                continue
            ic = [b for b in legal_actions(m) if b.kind == 'intercept' and b.piece == a.piece]
            if not ic:
                continue
            n2 = apply(m, ic[0])
        else:
            continue
        if isinstance(n2, ChanceNode):
            worst = min(worst, float(next(q for q, lab, sub in n2.outcomes if lab == 'success')))
    return round(worst, 2)


def _sq(c, a, sq):
    return c['squares'][a].get(sq)


def cmd_checks():
    """Design checks 1 to 6 by the map (blueprint, section 5), on Shaun's board of 15 November."""
    from playmaker_engine import board as B
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    out = {}
    his = board()
    cards = his.ctx.off
    three = {i: 3 * cards[i].shot('three') for i in range(5)}
    layup = {i: 2 * max(cards[i].shot('layup'), cards[i].shot('dunk'), cards[i].shot('post')) for i in range(5)}
    out['the cards'] = {f'O{i + 1} ({cards[i].role})': dict(open_three=three[i], best_open_shot_at_the_rim=layup[i]) for i in range(5)}

    # 1. the clear lane reads as a large weakness; the defence's own best placement reads it smaller
    c = cov(his)
    placed = board(c['after']['x'], c['after']['arrows'])
    c2 = cov(placed, answers=0)
    out['check 1'] = dict(his_game=dict(best=c['best'], words=c['words']), the_maps_own_answers=c['answers'], after_them=dict(x=c['after']['x'], best_left=c['left'], worth=c['left_worth']),
                          the_same_placement_read_from_the_start=dict(best=c2['best'], worth=c2['left_worth']),
                          falls_out=bool(c['best'] and c['best']['worth'] >= 30 and c['left_worth'] < c['best']['worth'] - 4))

    # 2 and 3. value comes from the cards: a non-shooter's three is worth little, a sharpshooter's a lot
    best3 = max(three, key=lambda i: (three[i], -layup[i]))
    worst3 = min(three, key=three.get)
    stay = cov(his, answers=0)

    def own_best(cc, i):
        mine = cc['squares'][i]
        return max(mine.values(), key=lambda v: v['worth']) if mine else None

    def three_of(cc, i):
        return _sq(cc, i, B.sq(his.o[i]))

    def leave(i, sq, arrow):
        """The defence with attacker i's defender moved to sq (off his man), no further answers: what the offence gets."""
        x, ar = list(O.HIS[0]), list(O.HIS[1])
        x[i], ar[i] = sq, arrow
        cc = cov(board(x, ar), answers=0)
        return dict(the_offences_best=cc['left_worth'], best=cc['best'], his_man_where_he_stands=three_of(cc, i), his_mans_best=own_best(cc, i))
    for key, i, label in (('check 2', worst3, 'non_shooter'), ('check 3', best3, 'sharpshooter')):
        out[key] = {label: f'O{i + 1} ({cards[i].role})', 'his_open_three': three[i], 'his_best_open_shot_at_the_rim': layup[i],
                    'his_defender_on_him': dict(the_offences_best=stay['left_worth'], his_man_where_he_stands=three_of(stay, i), his_mans_best=own_best(stay, i)),
                    'his_defender_in_the_lane': leave(i, 'I4', 'N')}
    c2_, c3_ = out['check 2'], out['check 3']
    give = lambda c_: (c_['his_defender_in_the_lane']['his_man_where_he_stands'] or {}).get('worth', 0) - (c_['his_defender_on_him']['his_man_where_he_stands'] or {}).get('worth', 0)
    c2_['what_leaving_him_gives_his_shot_where_he_stands'] = give(c2_)
    c3_['what_leaving_him_gives_his_shot_where_he_stands'] = give(c3_)
    c2_['falls_out'] = bool(three[worst3] < three[best3] - 6 and c2_['his_defender_in_the_lane']['the_offences_best'] < stay['left_worth'] - 2)
    c3_['falls_out'] = bool(three[best3] > three[worst3] + 6 and c3_['his_defender_in_the_lane']['the_offences_best'] > c2_['his_defender_in_the_lane']['the_offences_best'] + 2)

    # 4. arrows matter. At a phase's start a fresh defender can turn within the reaction, so an arrow matters where
    # the rules make it: the bar on the ball handler's way, the lane a defender can jump, and a contest with no token left
    from playmaker_engine.decide import Read
    ar4 = {}
    for nm, d in (('on him (NW, his game)', 'NW'), ('across his way to the rim (W)', 'W'), ('away from everything (E)', 'E')):
        x, ar = list(O.HIS[0]), list(O.HIS[1])
        ar[0] = d
        cc = cov(board(x, ar), answers=0)
        mine = cc['squares'][0]
        ar4[nm] = dict(squares_the_ball_handler_reaches=len(mine), his_best=own_best(cc, 0), squares_worth_30_or_more=sum(1 for v in mine.values() if v['worth'] >= 30))
    lanes = {}
    for nm, d in (('NW (his game)', 'NW'), ('N', 'N'), ('E', 'E'), ('S', 'S')):
        x, ar = list(O.HIS[0]), list(O.HIS[1])
        ar[1] = d
        lanes[nm] = pass_arrives(board(x, ar), 1)
    # a three going up now with the defence out of tokens: the arrow decides whether he is square
    now4 = {}
    on = B.dir_between(B.parse_sq('C8'), his.o[1])
    for nm, d in (('arrow on him', on), ('arrow off him', (on + 4) % 8)):
        x, ar = list(O.HIS[0]), list(O.HIS[1])
        x[1], ar[1] = 'C8', d
        now4[nm] = shot_now(board(x, ar, ball=1, tok_x=0), 1)
    out['check 4'] = dict(x1s_arrow_and_the_ball_handlers_way=ar4, x2s_arrow_and_the_chance_a_pass_reaches_his_man_where_he_stands=lanes,
                          x2_in_front_of_a_three_going_up_now_with_no_token_left=now4)
    out['check 4']['falls_out'] = bool(len({v['squares_worth_30_or_more'] for v in ar4.values()}) > 1 and len(set(lanes.values())) > 1 and now4['arrow on him'] < now4['arrow off him'])

    # 5. square in front reads stronger than beside, and beside stronger than behind, square by square: a shot going up
    # now. With the reaction's two actions a fresh defender gets in front from anywhere next to him; with no token left
    # he contests from where he stands
    b3 = his.o[1]
    pos = {}
    for nm, (dx, dy) in (('in front', (0, -1)), ('beside', (1, 0)), ('behind', (0, 1))):
        q = (b3[0] + dx, b3[1] + dy)
        x, ar = list(O.HIS[0]), list(O.HIS[1])
        x[1], ar[1] = B.sq(q), B.dir_between(q, b3)
        fresh = _sq(cov(board(x, ar, ball=1), answers=0), 1, B.sq(b3))
        pos[nm] = dict(defender_on=B.sq(q), with_the_reaction=fresh and fresh['weakness'], no_token_left=shot_now(board(x, ar, ball=1, tok_x=0), 1))
    out['check 5'] = dict(shooter=f'O2 ({cards[1].role}) with the ball on {B.sq(b3)}, his open three {three[1]}', the_three_going_up_now=pos)
    w = [pos[k]['no_token_left'] for k in ('in front', 'beside', 'behind')]
    out['check 5']['falls_out'] = w[0] < w[1] < w[2]

    # 6. a screen that stops a covering defender shows the squares he covered going weak. The defence with one token
    # left has one answer; a screen that stops that defender leaves more
    one = his.with_(tok_x=1)
    base = cov(one)
    scr = None
    for a in legal_actions(one):
        if a.kind != 'screen':
            continue
        cc = cov(apply(one, a).with_(side='O', turn_n=0, tok_x=1))
        row = dict(screen=str(a), left=cc['left_worth'], answers=[f"X{q['x'] + 1} to {q['to']}" for q in cc['answers']])
        if scr is None or row['left'] > scr['left']:
            scr = row
    # an attacker's body on the helper's way (O4 on C4, between X4 and the lane) against one off it (C5)
    body = {}
    for nm, sq in (('O4 off his way (C5)', 'C5'), ('O4 on his way (C4)', 'C4')):
        cc = cov(board(o=[*O.SHAUN_O[:3], sq, O.SHAUN_O[4]]).with_(tok_x=1))
        body[nm] = dict(left=cc['left_worth'], answers=[f"X{q['x'] + 1} to {q['to']}" for q in cc['answers']])
    out['check 6'] = dict(the_defence_with_one_token=dict(left=base['left_worth'], answers=[f"X{q['x'] + 1} to {q['to']}" for q in base['answers']]),
                          the_screen_action_that_leaves_most=scr, a_body_on_the_helpers_way=body,
                          falls_out=bool(scr and scr['left'] > base['left_worth'] + 1),
                          falls_out_for_a_body_on_his_way=bool(body['O4 on his way (C4)']['left'] > body['O4 off his way (C5)']['left'] + 1),
                          note="The Screen action bars only a diagonal step past its T square; on this board the helpers travel straight, and no Screen in the 16 placements tried next to X4 and X5 stops one. A body on the helper's way does.")
    out['which fall out'] = {k: v['falls_out'] for k, v in out.items() if isinstance(v, dict) and 'falls_out' in v}
    json.dump(out, open(os.path.join(RUN, 'checks.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


def cmd_played(tag='check1', copies='16'):
    """Check 1 by play: Shaun's defence against the placement the map's own answers give, from the possession's start,
    the same dice copy by copy. The computer plays as it does today (it doesn't read the map yet)."""
    his = board()
    c = cov(his)
    named = [('his game: X4 and X5 next to their men', his), ("the map's placement: " + ', '.join(c['after']['x']), board(c['after']['x'], c['after']['arrows']))]
    out = Q.play(named, int(copies), False, what=f'check 1 played ({tag})')
    rep = {k: P._summary(v) for k, v in out.items()}
    rep['the_map_reads'] = dict(his_game=c['best']['worth'], its_own_placement=c['left_worth'])
    json.dump(rep, open(os.path.join(RUN, f'played_{tag}.json'), 'w'), indent=1)
    for k, v in rep.items():
        print(k, v if k == 'the_map_reads' else (v['mean'], v['low'], v['high'], v['ends']))


# ---- stop two, part 1: the pass chance by the rules -------------------------------------------------------------------

def rules_pass(s, i):
    """The chance a pass from the ball handler to attacker i arrives, from the rules' own actions: every Intercept the
    defence may make once it is in the air, through a square or after one movement. None: the pass isn't legal."""
    from playmaker_engine.actions import Action, legal_actions, mti_approach
    from playmaker_engine.resolve import apply, ChanceNode
    from playmaker_engine.scoring import p_success, rolled
    st = s.with_(side='O', stage='play', turn_n=0, tok_o=max(1, s.tok_o), pending=None)
    a = Action('pass', 'O', s.ball, target=i)
    if a not in legal_actions(st):
        return None
    nxt = apply(st, a)
    if isinstance(nxt, ChanceNode) or nxt.stage != 'play' or nxt.side != 'X' or not nxt.pending:
        return 1.0
    worst = 0.0
    for b in legal_actions(nxt):
        if b.kind == 'intercept':
            worst = max(worst, 1 - float(p_success(rolled(nxt, 'O', s.ball, 'pass') - rolled(nxt, 'X', b.piece, 'intercept'), s.ctx.rules)))
        elif b.kind in ('move', 'qs', 'sprint') and mti_approach(nxt, b):
            af = apply(nxt, b)
            if not isinstance(af, ChanceNode) and af.pending:
                worst = max(worst, 1 - float(p_success(rolled(af, 'O', s.ball, 'pass') - rolled(af, 'X', b.piece, 'intercept'), s.ctx.rules)))
    return 1.0 - worst


def cmd_passproof(n='400', seed='7', broken=''):
    """The reading's pass chance against the rules' own actions, on random positions under the app's rules (the zone
    on): every legal pass of every position. -> docs/runs/step18s/pass_proof.json"""
    import random
    import js_equivalence as E
    from playmaker_engine import decide as D
    E._ZONE['v'] = 'on'
    if broken:
        E._ZONE['broken'] = True
    E._CONTROL['size'] = 'app'
    E._FIBA.update(three_seconds='on', closely_guarded='on', fiba_fouled_shot='on', soft_contest='on', fiba_steal_foul='on', off_balance='on', position_contest='on')
    rng = random.Random(int(seed))
    t0 = time.time()
    seen = same = old_same = 0
    bad, kinds = [], dict(cant_be_intercepted=0, through_or_jump=0)
    while seen < int(n):
        s, meta = E.random_state(rng)
        if s.stage != 'play' or s.pending or not B_on(s):
            continue
        for i in range(5):
            if i == s.ball:
                continue
            want = rules_pass(s, i)
            if want is None:
                continue
            got = D._lane_p_calc(s, i, s.o[i])
            D.CONFIG['eval']['pass_rules'] = False
            old = D._lane_p_calc(s, i, s.o[i])
            D.CONFIG['eval'].pop('pass_rules')
            seen += 1
            kinds['cant_be_intercepted' if want >= 1 else 'through_or_jump'] += 1
            same += abs(got - want) < 1e-9
            old_same += abs(old - want) < 1e-9
            if abs(got - want) >= 1e-9 and len(bad) < 12:
                from playmaker_engine.jsbridge import state_json
                bad.append(dict(to=i, rules=want, reading=got, state=state_json(s), digital=meta['digital']))
    out = dict(passes=seen, the_new_reading_equal_to_the_rules=same, the_old_reading_equal_to_the_rules=old_same, kinds=kinds, different=bad,
               seconds=round(time.time() - t0, 1))
    json.dump(out, open(os.path.join(RUN, 'pass_proof' + ('_broken' if broken else '') + '.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'different'}, indent=1))
    for b in bad[:4]:
        print(b)
    tally(f'part 1: the pass chance against the rules on {seen} random passes', time.time() - t0)


def B_on(s):
    from playmaker_engine import board as B
    return all(B.on_board(q) for q in s.o) and all(B.on_board(q) for q in s.x)


def play2(named, copies=16, sets=None, seed=1, what='play-outs'):
    """Each named position played out `copies` times, All-Star against All-Star, the app's rules, the same dice copy by
    copy. sets: dict(O=..., X=...), each side's own settings (pass_rules, ...). Rows filed by the name they carry."""
    from playmaker_engine import jsbridge
    ctx = jsbridge.ctx_json(named[0][1].ctx)
    sets = sets or dict(O={}, X={})
    pol = {k: L.policy('allstar', 2, L.profiles()['allstar']['noise'], **v) for k, v in sets.items()}
    positions = [dict(id=name, state=jsbridge.state_json(s), ctx=0, seed=104729 * (k + 1) + 7919 * seed) for name, s in named for k in range(copies)]
    rows, secs = L.run_jobs('trace', positions, [ctx], n=1, seed=seed, stances=True, policies=pol, rules=RULES, fouls=T.FOULS)
    tally(f'{what} ({len(named)} positions, {copies} each, {sets})', secs)
    out = {name: [] for name, _ in named}
    for r in rows:
        out[r['id']].append(r)
    assert all(len(v) == copies for v in out.values())
    return out


def passes_of(rows):
    """Passes thrown and passes intercepted a possession, and how often the possession's first two actions hold a pass."""
    n = len(rows)
    thrown = sum(1 for r in rows for e in r['events'] if e[2] == 'O' and e[3] == 'pass')
    return dict(passes_a_possession=round(thrown / n, 2), turnovers_a_possession=round(sum(r.get('tos', 0) or 0 for r in rows) / n, 2))


def cmd_passlines(tag='pass', copies='16', which='help'):
    """Part 1 by forced lines: 18r's position after the beat (the lane open, help in it; the offence as it chooses, and
    made to sprint in), and Shaun's board from the start. Each line with the old pass chance and with the rules' own."""
    named = []
    if which in ('help', 'all'):
        for label, kw in (('lane open', {}), ('help in the lane', dict(x4='H5', a4='N', x5='J5', a5='N'))):
            a = P._after_beat(**kw)
            named.append((f'{label}: the offence as it chooses', a))
            named.append((f'{label}: made to sprint into the lane', P._act(a, 'sprint', 0, 'I6')))
    if which in ('board', 'all'):
        named.append(("Shaun's board from the start: his game", board()))
        named.append(("Shaun's board from the start: X4 and X5 in the lane", board(['J10', 'D8', 'O8', 'H5', 'J5'], ['NW', 'NW', 'N', 'N', 'N'])))
    rep = {}
    for arm, on in (('the old pass chance', False), ("the rules' own", True)):
        out = play2(named, int(copies), dict(O=dict(pass_rules=on), X=dict(pass_rules=on)), what=f'part 1 forced lines ({tag}, {arm})')
        json.dump(out, open(os.path.join(WORK, f'passlines_{tag}_{"new" if on else "old"}_rows.json'), 'w'))
        for k, v in out.items():
            rep.setdefault(k, {})[arm] = dict(P._summary(v), **passes_of(v))
    json.dump(rep, open(os.path.join(RUN, f'passlines_{tag}.json'), 'w'), indent=1)
    for k, arms in rep.items():
        for arm, v in arms.items():
            print(f"{k:52} {arm:20} {v['mean']} ({v['low']} to {v['high']}) {v['ends']} passes {v['passes_a_possession']} first: {v['first_action'][:2]}")


def cmd_passcross(tag='cross', copies='16'):
    """Part 1, the offence alone: the offence with the rules' own pass chance against the defence with the old one, on
    the lines where the offence chooses for itself. Same dice as cmd_passlines."""
    a0, a1 = P._after_beat(), P._after_beat(x4='H5', a4='N', x5='J5', a5='N')
    named = [('lane open: the offence as it chooses', a0), ('help in the lane: the offence as it chooses', a1), ("Shaun's board from the start: his game", board())]
    out = play2(named, int(copies), dict(O=dict(pass_rules=True), X=dict(pass_rules=False)), what=f'part 1 forced lines ({tag}, the offence alone on the rules\' own)')
    json.dump(out, open(os.path.join(WORK, f'passlines_{tag}_rows.json'), 'w'))
    rep = {k: dict(P._summary(v), **passes_of(v)) for k, v in out.items()}
    json.dump(rep, open(os.path.join(RUN, f'passlines_{tag}.json'), 'w'), indent=1)
    for k, v in rep.items():
        print(f"{k:52} {v['mean']} ({v['low']} to {v['high']}) {v['ends']} passes {v['passes_a_possession']} first: {v['first_action'][:2]}")


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
