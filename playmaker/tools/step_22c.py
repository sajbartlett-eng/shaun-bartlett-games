"""Step 22c (Shaun, 18 Nov 2026): stagnation in the list, the takeover, the zone check.

python3 tools/step_22c.py equal [n] [seed]   the reading in the two engines on random positions -> docs/runs/step22c/equal.json
python3 tools/step_22c.py checks             the takeover board, Shaun's board, the zone check -> docs/runs/step22c/checks.json
python3 tools/step_22c.py again              step 22b's sense checks run again on this build -> docs/runs/step22c/checks_22b.json"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
RUN = os.path.join(ROOT, 'docs', 'runs', 'step22c')
os.makedirs(RUN, exist_ok=True)

ZONE_OFFENCE = 'Iron Wall'       # three attackers whose three-point rating is in the below-average band (7, 7 and 6), none above average


def cmd_equal(n='40', seed='23'):
    import step_22b as S
    S.RUN = RUN
    S.cmd_equal(n, seed)


def cmd_again():
    import step_22b as S
    S.RUN = RUN
    mine, keep = os.path.join(RUN, 'checks.json'), os.path.join(RUN, 'checks_22c.keep')
    if os.path.exists(mine):                             # (step 22b's tool writes the same file name: this step's own is put aside)
        os.replace(mine, keep)
    S.cmd_checks()
    os.replace(mine, os.path.join(RUN, 'checks_22b.json'))
    if os.path.exists(keep):
        os.replace(keep, mine)


def _state(o, x, arrows, off='Five Out', **kw):
    import step_21 as T
    return T._state(list(o), list(x), list(arrows), ball=0, off=off, **kw)


GAME_O, GAME_BALL = ['P8', 'L11', 'B3', 'H7', 'K3'], 1      # game 5DE415 (teams taken as Five Out against High-Low, as on the morning's board)


def _ball_board(S, T, B, o, ball):
    """Where all five settle on a board, and what the ball handler's card has to do with it."""
    s0 = T._state(list(o), S.SHAUN_X, S.SHAUN_A, ball=ball)
    t0 = time.time()
    z = S._js(s0, only='setup', evals=240)
    secs = round(time.time() - t0, 1)
    st = T._state(list(o), z['x'], z['arrows'], ball=ball)
    ro = S._js(st, only='roles')
    cov = S._js(st)
    bh = B.parse_sq(o[ball])
    d_on = z['perm'].index(ball)
    beside = [d for d in range(5) if B.cheb(B.parse_sq(z['x'][d]), bh) <= 1]
    looks, seen = [], set()
    for row in cov['top']:
        if row['o'] == ball and (row['shot'], row['value'], row['worth']) not in seen:
            seen.add((row['shot'], row['value'], row['worth']))
            looks.append(dict(sq=row['sq'], shot=row['shot'], open=row['value'], left=row['worth'], rushed=row['rushed'],
                              covered_by=None if row['cover'] < 0 else f"X{row['cover'] + 1}"))
    card = s0.ctx.off[ball]
    steal = []
    for j in range(5):
        dr, stl, fl = card.r['dribble'], s0.ctx.dfn[j].r['steal'], s0.ctx.dfn[j].r['foul_steal']
        kept, pf = max(0, min(20, dr - stl)) / 20, max(0, min(20, fl)) / 20
        steal.append(dict(x=f'X{j + 1}', steal=stl, steal_foul=fl, ball_kept=kept, worth_to_the_offence=round(5 * pf - 5 * (1 - pf) * (1 - kept), 2)))
    near = sorted({B.sq((bh[0] + dx, bh[1] + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0) and B.on_board((bh[0] + dx, bh[1] + dy))})
    rows = []
    for d in range(5):
        pr = S._js(st, only='probe', piece=d, squares=near)
        rows += [dict(q, x=d) for q in pr['rows']]
    return dict(
        board=dict(o=list(o), ball=f'O{ball + 1}'),
        settlement=dict(x=z['x'], arrows=z['arrows'], top=z['drivers']['list'][:8], lasting_gap=z['L'], seconds=secs,
                        matchups=[f'X{d + 1} on O{a + 1}' for d, a in enumerate(z['perm'])], lines=z['lines'],
                        steps=[dict(x=f"X{q['d'] + 1}", to=q['to'], arrow=q['arrow'], decided_by=q['by'], on_ball_pass=bool(q.get('pressure'))) for q in z['steps']]),
        the_ball_handler=dict(card=card.role, three=card.shot('three'), layup=card.shot('layup'), dribble=card.r['dribble'], quick_step=card.qs,
                              his_defender=f'X{d_on + 1}', his_defender_on=z['x'][d_on], squares_from_him=B.cheb(B.parse_sq(z['x'][d_on]), bh),
                              defenders_beside_him=[dict(x=f'X{d + 1}', on=z['x'][d], line=ro['roles'][d]['line']) for d in beside],
                              guarded=bool(B.cheb(B.parse_sq(z['x'][d_on]), bh) <= 1), his_looks=looks[:4]),
        the_steal_on_him_by_the_cards=steal,
        contests_of_a_three_by_the_cards={f'X{j + 1}': s0.ctx.dfn[j].con('three') for j in range(5)},
        placements_beside_him_read_in_full=len(rows), of_them_leaving_less=sum(1 for q in rows if q['better']),
        with_each_defender_off_the_court=[dict(x=f"X{q['x'] + 1}", worse=q['worse'], top=q['top']) for q in S._js(st, only='without')])


def cmd_checks():
    import step_22b as S
    import step_21 as T
    from playmaker_engine import board as B, jsbridge
    from playmaker_engine.agent import Agent
    from playmaker_engine.resolve import apply
    from playmaker_engine.goals import _likeliest
    out = {}
    eng = jsbridge.NodeEngine().install()
    try:
        # ---- the takeover: step 22b's check 8 board (X1 behind O1, who has driven into the key; X4 and X5 beside him) ----
        b1 = T.b1()
        prev = [0, 1, 3, 2, 4]                                          # X1 on O1; the others on the men they stand by
        before = S._js(b1, only='roles', prev=prev, fixed=True)
        ro = S._js(b1, only='roles', prev=prev)
        ag = Agent('X', 'allstar', seed=8)
        ag.assign = list(ro['perm'])
        cur, mv = b1, []
        while cur.stage == 'play' and cur.side == 'X':
            a = ag.choose(cur)
            mv.append(str(a))
            cur = _likeliest(apply(cur, a))
        after = S._js(cur, only='roles', prev=ro['perm']) if cur.stage == 'play' else None
        t = ro.get('takeover')
        picked = t and t['picks']
        d0 = picked is not None and B.cheb(b1.x[0], b1.o[picked])
        d1 = picked is not None and B.cheb(cur.x[0], cur.o[picked])
        out['the takeover (step 22b\'s check 8 board)'] = dict(
            passed=bool(t) and t['x'] == 0 and sorted(t['helpers']) == [3, 4],
            board=dict(o=[B.sq(q) for q in b1.o], x=[B.sq(q) for q in b1.x]), before=[q['line'] for q in before['roles']][:1],
            the_reading_says=ro['switched'], matchups=[f'X{d + 1} on O{a + 1}' for d, a in enumerate(ro['perm'])],
            read_again_with_nothing_changed=S._js(b1, only='roles', prev=ro['perm'])['switched'],
            the_defences_turn=mv, x1_squares_from_the_man_he_picked_up=dict(before=d0, after=d1), x1_moved_towards_him=bool(picked is not None and d1 < d0),
            lines_after=after and [q['line'] for q in after['roles']][:1] + (after['lines'] or []))
        # ---- Shaun's board of today: where all five go, and does anyone now press O1? ----
        s0 = S._board()
        base = S._js(s0, only='lasting')
        t0 = time.time()
        z = S._js(s0, only='setup', evals=240)
        st = S._board(z['x'], z['arrows'])
        ro2 = S._js(st, only='roles')
        d_on = z['perm'].index(0)
        near = sorted({B.sq((8 + dx, 11 + dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)})
        rows = []
        for d in range(5):
            pr = S._js(st, only='probe', piece=d, squares=near)
            rows += [dict(q, x=d) for q in pr['rows']]
        settled = pr['base']['list']
        best = min(rows, key=lambda q: (q['top'], q['L'], q['sq'], q['arrow'], q['x']))
        k = next((i for i, (u, v) in enumerate(zip(best['top'], settled)) if abs(u - v) > 1e-9), None)
        cards = s0.ctx
        steal = []
        for j in range(5):
            dr, stl, fl = cards.off[0].r['dribble'], cards.dfn[j].r['steal'], cards.dfn[j].r['foul_steal']
            kept, pf = max(0, min(20, dr - stl)) / 20, max(0, min(20, fl)) / 20
            for rolls in (1, 2):
                foul = pf if rolls == 1 else 1 - (1 - pf) ** 2
                steal.append(dict(x=f'X{j + 1}', foul_rolls=rolls, ball_kept=kept, foul=round(foul, 3), worth_to_the_offence=round(5 * foul - 5 * (1 - foul) * (1 - kept), 2)))
        pressed = S._board(['I10'] + z['x'][1:], [0] + z['arrows'][1:]) if 'I10' not in z['x'][1:] else None
        out['Shaun\'s board'] = dict(
            as_it_stood=dict(x=S.SHAUN_X, largest_item=base['top'], top=base['drivers']['list'][:6]),
            settlement=dict(x=z['x'], arrows=z['arrows'], largest_item=z['drivers']['list'][0], top=z['drivers']['list'][:8], lasting_gap=z['L'],
                            matchups=[f'X{d + 1} on O{a + 1}' for d, a in enumerate(z['perm'])], lines=z['lines'], seconds=round(time.time() - t0, 1),
                            steps=[dict(x=f"X{q['d'] + 1}", to=q['to'], arrow=q['arrow'], decided_by=q['by'], pressure_pass=bool(q.get('pressure'))) for q in z['steps']]),
            does_anyone_press_o1=any(B.cheb(B.parse_sq(q), B.parse_sq(S.SHAUN_O[0])) <= 1 for q in z['x']),
            defenders_beside_o1=[dict(x=f'X{d + 1}', on=z['x'][d], arrow=z['arrows'][d], line=ro2['roles'][d]['line'])
                                 for d in range(5) if B.cheb(B.parse_sq(z['x'][d]), B.parse_sq(S.SHAUN_O[0])) <= 1],
            o1s_defender=dict(x=f'X{d_on + 1}', on=z['x'][d_on], squares_from_him=B.cheb(B.parse_sq(z['x'][d_on]), B.parse_sq(S.SHAUN_O[0])), line=ro2['roles'][d_on]['line']),
            placements_on_o1_read_in_full=len(rows), of_them_leaving_less=sum(1 for q in rows if q['better']),
            the_nearest_miss=dict(x=f"X{best['x'] + 1}", on=best['sq'], arrow=best['arrow'], top=best['top'], settled_top=settled[:6],
                                  first_item_that_differs=None if k is None else dict(place=k + 1, pressing=best['top'][k], settled=settled[k])),
            the_steal_on_o1_by_the_cards=steal)
        # ---- Shaun's board of 18 Nov 15:08 (game 5DE415): O2 on L11 with the ball. Guarded, or sagged off? ----
        out['game 5DE415'] = _ball_board(S, T, B, GAME_O, GAME_BALL)
        # ---- the zone check: the same defence against a non-shooting line-up ----
        zs0 = _state(S.SHAUN_O, S.SHAUN_X, S.SHAUN_A, off=ZONE_OFFENCE)
        threes = [(c.role, c.shot('three'), (c.bands or {}).get('shot_three')) for c in zs0.ctx.off]
        zz = S._js(zs0, only='setup', evals=240)
        zst = _state(S.SHAUN_O, zz['x'], zz['arrows'], off=ZONE_OFFENCE)
        zro = S._js(zst, only='roles')
        dist = [min(B.cheb(B.parse_sq(q), B.parse_sq(o)) for o in S.SHAUN_O) for q in zz['x']]
        to_man = [B.cheb(B.parse_sq(zz['x'][d]), B.parse_sq(S.SHAUN_O[a])) for d, a in enumerate(zz['perm'])]
        # attackers cross areas with the defence standing still: O2 and O3 change wings, then O4 and O5 change corners
        hand = []
        for name, o in (('O2 and O3 change wings', [S.SHAUN_O[0], S.SHAUN_O[2], S.SHAUN_O[1], S.SHAUN_O[3], S.SHAUN_O[4]]),
                        ('O4 and O5 change corners', [S.SHAUN_O[0], S.SHAUN_O[1], S.SHAUN_O[2], S.SHAUN_O[4], S.SHAUN_O[3]]),
                        ('O2 cuts from the wing to the far corner side (C9 to N3)', [S.SHAUN_O[0], 'N3', S.SHAUN_O[2], S.SHAUN_O[3], S.SHAUN_O[4]])):
            crossed = _state(o, zz['x'], zz['arrows'], off=ZONE_OFFENCE)
            r = S._js(crossed, only='roles', prev=zz['perm'])
            hand.append(dict(what=name, handed_on=r['perm'] != zz['perm'], says=r['switched'], matchups=[f'X{d + 1} on O{a + 1}' for d, a in enumerate(r['perm'])]))
        # the same crossings against the Five Out shooters, for comparison
        hand5 = []
        for name, o in (('O2 and O3 change wings', [S.SHAUN_O[0], S.SHAUN_O[2], S.SHAUN_O[1], S.SHAUN_O[3], S.SHAUN_O[4]]),
                        ('O4 and O5 change corners', [S.SHAUN_O[0], S.SHAUN_O[1], S.SHAUN_O[2], S.SHAUN_O[4], S.SHAUN_O[3]])):
            crossed = S._board(z['x'], z['arrows'], o)
            r = S._js(crossed, only='roles', prev=z['perm'])
            hand5.append(dict(what=name, handed_on=r['perm'] != z['perm'], says=r['switched']))
        out['the zone check'] = dict(
            offence=ZONE_OFFENCE, threes=[dict(o=f'O{i + 1}', card=t3[0], three=t3[1], band={'L': 'below average', 'A': 'average', 'H': 'above average'}.get(t3[2], t3[2])) for i, t3 in enumerate(threes)],
            settlement=dict(x=zz['x'], arrows=zz['arrows'], largest_item=zz['drivers']['list'][0], top=zz['drivers']['list'][:8],
                            matchups=[f'X{d + 1} on O{a + 1}' for d, a in enumerate(zz['perm'])], lines=zz['lines']),
            squares_from_the_nearest_attacker=dict(zip([f'X{d + 1}' for d in range(5)], dist)),
            squares_from_his_own_man=dict(zip([f'X{d + 1}' for d in range(5)], to_man)),
            defenders_in_the_key=[f'X{d + 1}' for d in range(5) if B.in_key(B.parse_sq(zz['x'][d]))],
            jobs=[q['kind'] for q in zro['roles']],
            attackers_cross_with_the_defence_standing_still=hand, the_same_against_five_out=hand5)
    finally:
        eng.close()
    json.dump(out, open(os.path.join(RUN, 'checks.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1)[:9000])


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
