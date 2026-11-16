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


# ---- stop two, part 2: the search reads the map ------------------------------------------------------------------------

def cmd_mapdata(tag, n='128', seed='1', rate='0.125', map_on='no'):
    """Play for the fit, the way the fix plan sets it (D-196): All-Star against All-Star from the stored starts under
    the app's rules, at most one turn a possession drawn at random from all the turns the search weighed, every
    open-play position kept with the map's three numbers (the shot that can go up now, the best way, the second way)."""
    pl = O.G.pool()
    T.pool_is_current(pl)
    sw = dict(map=True) if map_on == 'map' else {}
    pol = dict(L.policy('allstar', 2, L.profiles()['allstar']['noise'], **sw), explore=float(rate))
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), mapparts=True, policies=dict(O=pol, X=pol), rules=RULES, fouls=T.FOULS)
    json.dump(dict(size=tag, rows=rows, explore=float(rate), map=bool(sw)), open(os.path.join(WORK, f'mapdata_{tag}.json'), 'w'))
    tally(f'part 2: play for the fit ({tag}, {n} possessions, a drawn turn at rate {rate}{", the map read" if sw else ""})', secs)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    print(tag, len(rows), 'possessions', round(m, 2), [round(m - ci, 2), round(m + ci, 2)], '| positions', sum(len(r['reads']) for r in rows),
          'usable', sum(len(r['reads']) - r['clean_from'] for r in rows))


MAP_MIN = 60                                            # a line is fitted from this many positions or more (else the reading as it was)


def map_rows(tags, form='answered'):
    """(possession, phase, what was left to earn, today's reading of it, offence to act, [1, shot, best way, second way])
    for every usable position: one with no drawn turn after it. form: 'answered' (the two ways the defence's answers
    leave) or 'standing' (the two ways as the board stands)."""
    import numpy as np
    g, ph, y, hand, side, X = [], [], [], [], [], []
    k = 0
    for tag in tags:
        for r in json.load(open(os.path.join(WORK, f'mapdata_{tag}.json')))['rows']:
            k += 1
            for st in r['reads'][r.get('clean_from', 0):]:
                g.append(k); ph.append(min(6, max(1, (12 - st[0]) // 2 + 1))); y.append(r['value'] - st[1]); hand.append(st[2] - st[1]); side.append(int(st[3]))
                X.append([1.0, st[-7], st[-4], st[-3]] if form == 'answered' else [1.0, st[-7], st[-6], st[-5]])
    return np.array(g), np.array(ph), np.array(y, float), np.array(hand, float), np.array(side), np.array(X, float), k


def cmd_fitmap(write='no', *tags):
    """How the map's numbers combine into the reading's one number, fitted to what positions went on to earn: per phase
    and side to act, what is left to earn = w0 + w1 x the shot now + w2 x the best way + w3 x the second way (w1 to w3
    never below 0). With the spread of each over possessions drawn again, and the error on possessions held out, beside
    today's reading's on the same positions."""
    import hashlib
    import numpy as np
    from step_18h import nnls
    form = 'answered'
    if tags and tags[0] in ('answered', 'standing'):
        form, tags = tags[0], tags[1:]
    g, ph, y, hand, side, X, n = map_rows(tags, form)
    fold = np.random.default_rng(18).permutation(n + 1) % 5
    maps, pred = {}, np.full(len(y), np.nan)
    for p in range(1, 7):
        for sd in (0, 1):
            m = (ph == p) & (side == sd)
            if m.sum() < MAP_MIN:
                continue
            w = nnls(X[m], y[m])
            rs, ws, ids = np.random.default_rng(7), [], np.unique(g[m])
            for _ in range(60):
                cnt = np.bincount(rs.choice(ids, len(ids)), minlength=n + 1)[g] * m
                sel = np.repeat(np.arange(len(y)), cnt)
                ws.append(nnls(X[sel], y[sel]))
            ws = np.array(ws)
            maps[f"{p}{'O' if sd else 'X'}"] = dict(w=[round(float(v), 5) for v in w], positions=int(m.sum()),
                                                 spread=[[round(float(np.percentile(ws[:, k], 5)), 3), round(float(np.percentile(ws[:, k], 95)), 3)] for k in range(4)])
            for k in range(5):
                tr, te = m & (fold[g] != k), m & (fold[g] == k)
                if tr.sum() >= 20 and te.any():
                    pred[te] = X[te] @ nnls(X[tr], y[tr])
    ok = ~np.isnan(pred)
    rmse = lambda v: round(float(np.sqrt(np.mean((v[ok] - y[ok]) ** 2))), 2)
    corr = lambda v: round(float(np.corrcoef(v[ok], y[ok])[0, 1]), 3)
    rep = dict(form=form, possessions=n, positions=int(len(y)), fitted_positions=int(ok.sum()), lines=sorted(maps),
               held_out_error=dict(the_map=rmse(pred), todays_reading=rmse(hand)), held_out_agreement=dict(the_map=corr(pred), todays_reading=corr(hand)), maps=maps)
    json.dump(rep, open(os.path.join(RUN, f'fit_map_{form}_{"_".join(tags)}.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'maps'}))
    for k in sorted(maps):
        print('   ', k, maps[k]['positions'], maps[k]['w'], maps[k]['spread'])
    if write != 'no':
        body = json.load(open(L.WEIGHTS))
        body.pop('hash', None)
        body['calibration_map'] = dict(version=1, form=form, inputs=['the best shot that can go up now', "the best way the coverage map leaves next phase, after the defence's answers", 'the second, separate way'],
                                       meaning="what is left to earn = w[0] + w[1] x input 1 + w[2] x input 2 + w[3] x input 3, per phase and side to act (O: the "
                                               "offence to act); w[1] to w[3] never below 0; a phase and side without a line reads as before (eval.map, step 18s)",
                                       fitted_on=dict(tags=list(tags), possessions=n, positions=int(len(y))), maps=maps)
        body['hash'] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        json.dump(body, open(L.WEIGHTS, 'w'), indent=1)
        print('wrote', body['hash'])


# ---- stop two, part 3: forced lines for any named position -------------------------------------------------------------

def _sj(s):
    from playmaker_engine import jsbridge
    return (jsbridge.state_json(s), jsbridge.ctx_json(s.ctx)) if not isinstance(s, tuple) else s


def weighed(states, sets=None, what='searches'):
    """One whole All-Star search on each position (a state, or its (state, ctx) JSON): the turns it weighed, best
    first, as [(value, turn)]."""
    contexts, pos = [], []
    for k, s in enumerate(states):
        sj, cj = _sj(s)
        contexts.append(cj)
        pos.append(dict(id=str(k), state=sj, ctx=k))
    rows, secs = L.run_jobs('search', pos, contexts, policies={'p': L.policy('allstar', 2, 0.0, **(sets or {}))}, rules=RULES, fouls=T.FOULS)
    tally(f'{what} ({len(states)} positions, {sets or {}})', secs)
    rows = {int(r['id']): r for r in rows}
    return [rows[k]['by']['p']['results'] for k in range(len(states))]


def forced(items, n=16, sets=None, what='forced lines', seed=1):
    """items: [(id, position, [(name, turn)])], a turn being a list of actions as JSON, or None for the position as it
    stands. Each turn is made, then played out n times, All-Star against All-Star (sets: each side's settings), the
    same dice for every turn of a position. -> {id: {name: dict(mean, low, high, ends, values)}}"""
    import zlib
    contexts, jobs, names = [], [], {}
    for pid, s, cands in items:
        sj, cj = _sj(s)
        contexts.append(cj)
        names[pid] = [nm for nm, _ in cands]
        jobs.append(dict(id=pid, state=sj, ctx=len(contexts) - 1, seed=15485863 * seed + 1 + 2 * (zlib.crc32(pid.encode()) % 500000), turns=[t for _, t in cands]))
    sets = sets or dict(O={}, X={})
    pol = {k: L.policy('allstar', 2, L.profiles()['allstar']['noise'], **v) for k, v in sets.items()}
    rows, secs = L.run_jobs('rollout', jobs, contexts, n=n, seed=7, keep=True, ends=True, policies=pol, rules=RULES, fouls=T.FOULS)
    tally(f'{what} ({sum(len(c) for _, _, c in items)} lines on {len(items)} positions, {n} each, {sets})', secs)
    out = {}
    for r in rows:
        res = {}
        for nm, t in zip(names[r['id']], r['turns']):
            if not t['values']:
                res[nm] = None
                continue
            m, sd, ci = L.mean_ci(t['values'])
            import collections
            res[nm] = dict(mean=round(m, 1), low=round(m - ci, 1), high=round(m + ci, 1), ends=dict(collections.Counter(t.get('ends') or [])), values=[round(v, 2) for v in t['values']])
        out[r['id']] = res
    return out


def paired(a, b):
    """The mean difference a - b over the same dice, with its 95% range."""
    d = [x - y for x, y in zip(a['values'], b['values'])]
    m, sd, ci = L.mean_ci(d)
    return dict(diff=round(m, 1), low=round(m - ci, 1), high=round(m + ci, 1))


def cmd_mapequal(n='200', seed='5'):
    """The map's numbers for the search in the two engines: the shot now, the best way, the second way, on random
    positions under the app's rules. -> docs/runs/step18s/map_equal.json"""
    import random
    import js_equivalence as E
    from playmaker_engine import agent as AG, decide as D
    E._ZONE['v'] = 'on'
    E._CONTROL['size'] = 'app'
    E._FIBA.update(three_seconds='on', closely_guarded='on', fiba_fouled_shot='on', soft_contest='on', fiba_steal_foul='on', off_balance='on', position_contest='on')
    cov(board(), 0)                                    # the fast engine, installed
    rng = random.Random(int(seed))
    t0 = time.time()
    seen = same = 0
    bad = []
    while seen < int(n):
        s, meta = E.random_state(rng)
        if s.stage != 'play' or s.pending or not B_on(s) or not meta['digital']:
            continue
        from playmaker_engine import jsbridge
        js = json.loads(AG.JS['coverage'](json.dumps(dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), options=dict(only='parts')))))['parts']
        r = D.Read(s)
        py = [r.map_shot()] + list(r.map_two()) + [s.tok_o, s.tok_x]
        seen += 1
        ok = all(abs(a - b) < 1e-9 for a, b in zip(js, py))
        same += ok
        if not ok and len(bad) < 8:
            from playmaker_engine.jsbridge import state_json
            bad.append(dict(js=js, py=py, state=state_json(s)))
    out = dict(positions=seen, equal=same, different=bad, seconds=round(time.time() - t0, 1))
    json.dump(out, open(os.path.join(RUN, 'map_equal.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'different'}))
    for b in bad[:3]:
        print(b['js'], b['py'], json.dumps(b['state'])[:400])


def turn_names(turn):
    from playmaker_engine import jsbridge
    return [str(jsbridge.action_from(t)) for t in (turn or [])]


def after_turn(s, turn):
    """The position after a turn's actions, or None if one of them rolls."""
    from playmaker_engine import jsbridge
    from playmaker_engine.resolve import apply, ChanceNode
    n = s
    for t in turn:
        if isinstance(n, ChanceNode):
            return None
        n = apply(n, jsbridge.action_from(t))
    return None if isinstance(n, ChanceNode) else n


def _same(a, b):
    return json.dumps(a) == json.dumps(b)


def cmd_closeout(tag='closeout', copies='16', map_on='no'):
    """18o's closeout positions and game EB3F5B's pass in the air, replayed under today's rules (D-198): every named
    answer forced and played out; and what the computer itself picks there."""
    sets = dict(pass_rules=True, **(dict(map=True) if map_on == 'map' else {}))
    pos = {p['id']: p for p in json.load(open(os.path.join(HERE, 'sense_set', 'positions_18o.json')))}
    ids = ['closeout, shooter cannot move', 'closeout, step 2', 'game EB3F5B, the pass in the air']
    items = [(pid, (pos[pid]['state'], pos[pid]['ctx']), [(c['name'], c['turn']) for c in pos[pid]['candidates'] if not c.get('added_by')][:5]) for pid in ids]
    picks = weighed([it[1] for it in items], sets, what=f'part 3: the closeout positions, the computer\'s own pick ({tag})')
    for it, res in zip(items, picks):
        if not any(_same(res[0][1], t) for _, t in it[2]):
            it[2].append(("the computer's own pick", res[0][1]))
    out = forced(items, int(copies), dict(O=sets, X=sets), what=f'part 3: the closeout positions replayed under D-198 ({tag})')
    rep = {}
    for it, res in zip(items, picks):
        pid = it[0]
        own = next(nm for nm, t in it[2] if _same(res[0][1], t))
        rep[pid] = dict(what=pos[pid]['what'], side=pos[pid]['side'], lines={nm: (v and {k: v[k] for k in ('mean', 'low', 'high', 'ends')}) for nm, v in out[pid].items()},
                        the_computer_picks=own, its_pick_in_words=turn_names(res[0][1]), it_reads=round(res[0][0], 1))
        best = min((v['mean'], nm) for nm, v in out[pid].items() if v) if pos[pid]['side'] == 'X' else max((v['mean'], nm) for nm, v in out[pid].items() if v)
        rep[pid]['best_by_play'] = best[1]
        rep[pid]['the_pick_against_the_best'] = paired(out[pid][own], out[pid][best[1]])
        print(pid, '| picks:', own, '| best by play:', best[1], rep[pid]['the_pick_against_the_best'])
        for nm, v in out[pid].items():
            print('     ', nm, v and (v['mean'], v['low'], v['high'], v['ends']))
    json.dump(rep, open(os.path.join(RUN, f'{tag}.json'), 'w'), indent=1)


def cmd_check7(tag='check7', copies='16'):
    """Check 7 by forced lines, the map read by both sides: 18r's position after the beat (the lane open, help in it; the
    offence as it chooses, and made to sprint in) and Shaun's board. Same dice as cmd_passlines."""
    named = []
    for label, kw in (('lane open', {}), ('help in the lane', dict(x4='H5', a4='N', x5='J5', a5='N'))):
        a = P._after_beat(**kw)
        named.append((f'{label}: the offence as it chooses', a))
        named.append((f'{label}: made to sprint into the lane', P._act(a, 'sprint', 0, 'I6')))
    named.append(("Shaun's board from the start: his game", board()))
    named.append(("Shaun's board from the start: X4 and X5 in the lane", board(['J10', 'D8', 'O8', 'H5', 'J5'], ['NW', 'NW', 'N', 'N', 'N'])))
    on = dict(pass_rules=True, map=True)
    out = play2(named, int(copies), dict(O=on, X=on), what=f'part 3: check 7 by forced lines, the map read ({tag})')
    json.dump(out, open(os.path.join(WORK, f'{tag}_rows.json'), 'w'))
    rep = {k: dict(P._summary(v), **passes_of(v)) for k, v in out.items()}
    base = json.load(open(os.path.join(RUN, 'passlines_pass.json')))
    for k, v in rep.items():
        v['without_the_map'] = {x: base[k]["the rules' own"][x] for x in ('mean', 'low', 'high', 'ends')} if k in base else None
        print(f"{k:52} {v['mean']} ({v['low']} to {v['high']}) {v['ends']} | without the map {v['without_the_map'] and v['without_the_map']['mean']} | first: {v['first_action'][:2]}")
    json.dump(rep, open(os.path.join(RUN, f'{tag}.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
