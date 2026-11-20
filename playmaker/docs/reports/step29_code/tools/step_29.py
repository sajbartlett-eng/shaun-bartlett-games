"""Step 29: the block, fakes, the pivot and deep range. One reading of each check.

  python3 tools/step_29.py checks     boards 1 to 3: both setup buttons; where the defence stands against the best shooter
  python3 tools/step_29.py morning    the morning board of the Sharpshooter check, as it now settles
  python3 tools/step_29.py elite      an elite shooter with weak inside threats, at pro level: both setups
  python3 tools/step_29.py sag        the same board, his defender sagging, the shooter in control: the offence's fake mix
  python3 tools/step_29.py block      a rim protector set in front of a driver off a Sprint, then in control
  python3 tools/step_29.py deep       deep range: at pro, does his defender follow him out; at junior, the squares closed
  python3 tools/step_29.py turn       one computer offence turn in play, timed
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'runs', 'step29')
OLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'runs', 'step28')
os.makedirs(RUN, exist_ok=True)

import step_28 as S28            # noqa: E402  (the same boards and the same reading of them)

ELITE = ('shsA', 'tndA', 'stsfA', 'stpfA', 'stcA')          # an elite shooter, weak inside threats (every big a stretch big)


def _save(name, out):
    json.dump(out, open(os.path.join(RUN, name), 'w'), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


def _guard(B, st, perm, SCT, CD):
    best = max(range(5), key=lambda a: (st.ctx.off[a].shot('three'), -a))
    j = perm.index(best) if best in perm else min(range(5), key=lambda k: B.cheb(st.x[k], st.o[best]))
    near = min((B.cheb(q, st.o[best]), k) for k, q in enumerate(st.x))
    return dict(shooter=f"O{best + 1} ({SCT.short_role(st.ctx.off[best])}, three {st.ctx.off[best].shot('three')}) on {B.sq(st.o[best])}",
                his_defender=f"X{j + 1} on {B.sq(st.x[j])}, {B.cheb(st.x[j], st.o[best])} squares off",
                nearest=f"X{near[1] + 1}, {near[0]} squares off", squares_off=B.cheb(st.x[j], st.o[best]),
                stance=CD.stance(st, j, best))


def _setup(make):
    from playmaker_engine import plan as PL
    t0 = time.time()
    r = PL.place_offence(make, seed=1)
    t1 = time.time()
    d = PL.place_defence(make, r['squares'], r['ball'], seed=1)
    t2 = time.time()
    return r, d, round(t1 - t0, 1), round(t2 - t1, 1)


def cmd_checks(only=None):
    from playmaker_engine import board as B, jsbridge, scouting as SCT, conditions as CD
    old = {}
    try:
        old = json.load(open(os.path.join(OLD, 'checks.json')))
    except Exception:
        pass
    out = {}
    eng = jsbridge.NodeEngine().install()
    try:
        for off, dfn, label in S28.BOARDS:
            if only and only not in label:
                continue
            make = S28._make(off, dfn)
            r, d, so, sd = _setup(make)
            st = make(r['squares'], r['ball'], d['squares'], d['arrows'])
            key = f'{off} v {dfn}, {label}'
            before = (old.get(key) or {}).get('defence', {}).get('best_shooter')
            out[key] = dict(offence=dict(squares=[B.sq(q) for q in r['squares']], ball=f"O{r['ball'] + 1}", line=(r['plan'] or {}).get('line'),
                                         seconds=so),
                            defence=dict(squares=[B.sq(q) for q in d['squares']], arrows=d['arrows'], seconds=sd,
                                         read=[z['text'] for z in d['read']][:4], stances=[z['text'] for z in d.get('stances') or []]),
                            best_shooter_now=_guard(B, st, d['perm'], SCT, CD), best_shooter_step28=before,
                            bigs=S28._between(B, st, d['perm']))
    finally:
        eng.close()
    _save('checks.json' if not only else f'checks_{only.split()[0]}.json', out)


def cmd_morning():
    from playmaker_engine import agent as AG, board as B, jsbridge, conditions as CD
    import step_22b as S
    eng = jsbridge.NodeEngine().install()
    try:
        s0 = S._board()
        t = time.time()
        z = S._js(s0, only='setup', evals=240)
        secs = round(time.time() - t, 1)
        st = S._board(z['x'], z['arrows']).with_(side='O', turn_n=0)
        perm = (AG.coverage(st, only='roles') or {}).get('perm') or list(range(5))
        sharp = next(i for i, c in enumerate(st.ctx.off) if 'Sharpshooter' in (c.role or ''))
        j = perm.index(sharp)
        before = None
        try:
            before = json.load(open(os.path.join(OLD, 'morning.json')))['defence']
        except Exception:
            pass
        out = dict(defence=dict(x=z['x'], arrows=z['arrows'], seconds=secs), list=z['drivers']['list'][:6],
                   sharpshooter=f"O{sharp + 1} on {B.sq(st.o[sharp])}",
                   his_defender=f"X{j + 1} on {B.sq(st.x[j])}, {B.cheb(st.x[j], st.o[sharp])} squares off",
                   stances=[q['text'] for q in CD.stances(st, perm)], step28_defence=before)
    finally:
        eng.close()
    _save('morning.json', out)


def _elite_make(deep=None):
    import step_21 as T
    from playmaker_engine import board as B, cards as CD
    name = CD.register_team('Elite shooter 29', list(ELITE))

    def make(o, b, x, a):
        s = T._state([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), ball=b, off=name, dfn='Lockdown')
        if deep is not None:
            s.ctx.deep_rows = deep
        return s
    return make


def cmd_elite():
    from playmaker_engine import board as B, jsbridge, scouting as SCT, conditions as CD
    eng = jsbridge.NodeEngine().install()
    try:
        make = _elite_make()
        r, d, so, sd = _setup(make)
        st = make(r['squares'], r['ball'], d['squares'], d['arrows'])
        out = dict(offence=dict(squares=[B.sq(q) for q in r['squares']], ball=f"O{r['ball'] + 1}", seconds=so,
                                line=(r['plan'] or {}).get('line')),
                   defence=dict(squares=[B.sq(q) for q in d['squares']], arrows=d['arrows'], seconds=sd,
                                read=[z['text'] for z in d['read']][:5]),
                   best_shooter=_guard(B, st, d['perm'], SCT, CD))
    finally:
        eng.close()
    _save('elite.json', out)


def cmd_sag():
    """His defender three squares off, the shooter in control with the ball: the offence's fake mix, read by its own search."""
    from playmaker_engine import agent as AG, board as B, jsbridge
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    from playmaker_engine.search import mix_game
    eng = jsbridge.NodeEngine().install()
    try:
        make = _elite_make()
        o = [B.parse_sq(q) for q in ('I11', 'C9', 'O9', 'E4', 'M4')]
        x = [B.parse_sq(q) for q in ('I8', 'D8', 'N8', 'F4', 'L4')]
        st = make(o, 0, x, [0, 1, 7, 0, 0]).with_(side='O', turn_n=0)
        shot = next(a for a in legal_actions(st) if a.kind == 'shot' and a.arrow != 1)
        decl = apply(st, shot)
        ag = AG.Agent('O', 'allstar', seed=1)
        t = time.time()
        cols, turns = ag._mix_cols(decl, 20.0)
        v, p, q = mix_game(cols)
        out = dict(board=dict(o=[B.sq(z) for z in o], x=[B.sq(z) for z in x]), shot=str(shot), seconds=round(time.time() - t, 1),
                   fake_chance=round(p, 3), value=round(v, 2),
                   replies=[dict(turn=[str(a) for a in turns[k]], real=round(cols[k][0], 2), fake=round(cols[k][1], 2),
                                 defence_mix=round(q.get(k, 0.0), 3)) for k in range(len(cols))])
    finally:
        eng.close()
    _save('sag.json', out)


def cmd_block():
    """A Rim Protector set square in front of a driver: off a Sprint (rushed: no fake), then in control (a fake is open)."""
    from playmaker_engine import agent as AG, board as B, jsbridge, rules_config as RC
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    from playmaker_engine.scoring import contest_options
    from playmaker_engine.search import mix_game
    import step_21 as T
    eng = jsbridge.NodeEngine().install()
    out = {}
    try:
        for label, rush in (('off a Sprint (rushed: no fake)', RC.RUSH_SPRINT), ('in control (a fake is open)', 0)):
            st = T._state(['H4', 'C9', 'O9', 'A3', 'Q9'], ['D8', 'B8', 'N8', 'B3', 'H3'], [0, 0, 0, 0, 0], ball=0,
                          off='Five Out', dfn='Iron Wall').with_(side='O', turn_n=0, rush_o=rush)
            rp = next(j for j in range(5) if 'Rim Protector' in (st.ctx.dfn[j].role or '')) if any('Rim Protector' in (c.role or '') for c in st.ctx.dfn) else 4
            shot = next(a for a in legal_actions(st) if a.kind == 'shot' and a.arrow != 1 and a.shot == 'layup')
            decl = apply(st, shot)
            opts = {(o.defender, o.hard): o for o in contest_options(decl, 0, 'layup') if o.defender >= 0}
            blk = opts.get((4, True))
            ag = AG.Agent('X', 'allstar', seed=1)
            t = time.time()
            a = ag.choose(decl)
            mix = next((n for n in reversed(ag.notes) if n.get('event') == 'mix'), None)
            out[label] = dict(fake_open_at_the_shot=bool(decl.decl), defender=f"X5 ({st.ctx.dfn[4].role}) square on H3",
                              block_chance=blk and round(float((1 - blk.p_foul) * blk.p_block) * 100),
                              block_roll=blk and blk.block, foul_risk=blk and round(float(blk.p_foul) * 100),
                              contest_if_he_misses=blk and blk.contest, computer_reply=str(a), seconds=round(time.time() - t, 1),
                              mix=mix)
    finally:
        eng.close()
    _save('block.json', out)


def cmd_deep():
    from playmaker_engine import board as B, jsbridge, plan as PL, scouting as SCT, conditions as CD
    from playmaker_engine.actions import legal_actions
    eng = jsbridge.NodeEngine().install()
    out = {}
    try:
        o = [B.parse_sq(q) for q in ('B10', 'I10', 'P8', 'F3', 'L3')]
        for label, rows in (('Senior Pro', 5), ('Junior', 0)):
            make = _elite_make(rows)
            t = time.time()
            d = PL.place_defence(make, o, 1, seed=1)
            st = make(o, 1, d['squares'], d['arrows'])
            shooter = 0
            j = min(range(5), key=lambda k: B.cheb(st.x[k], st.o[shooter]))
            on_ball = make(o, 0, d['squares'], d['arrows']).with_(side='O', turn_n=0)
            out[label] = dict(shooter=f"O1 ({SCT.short_role(st.ctx.off[0])}, three {st.ctx.off[0].shot('three')}) on B10, {B.deep(o[0])} square past the arc",
                              defence=[B.sq(q) for q in d['squares']], nearest=f"X{j + 1} on {B.sq(st.x[j])}, {B.cheb(st.x[j], st.o[0])} squares off",
                              can_shoot_there=any(a.kind == 'shot' for a in legal_actions(on_ball)), seconds=round(time.time() - t, 1))
    finally:
        eng.close()
    _save('deep.json', out)


def cmd_turn():
    from playmaker_engine import agent as AG, jsbridge, plan as PL
    import step_21 as T
    eng = jsbridge.NodeEngine().install()
    try:
        st = T._state(*S28.HIGH_SCREEN, off='High-Low', dfn='Run and Gun').with_(side='O', turn_n=0)
        ag = AG.Agent('O', 'allstar', seed=1)
        ag.scout = PL.Scout(st.ctx, 'O')
        ag.setup_plan = PL.read_plan(st, ag.scout, deep=True)
        t = time.time()
        a = ag.choose(st)
        out = dict(action=str(a) if a.arrow != 1 else str(a._replace(arrow=-1)) + ' (fake)', seconds=round(time.time() - t, 1),
                   notes=[n for n in ag.notes if n.get('event') in ('mix', 'decision')][-2:])
    finally:
        eng.close()
    _save('turn.json', out)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
