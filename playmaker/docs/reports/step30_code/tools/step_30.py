"""Step 30: after the block (D-276), the two app-only cards (D-277), the fake read ahead. One reading of each check.

  python3 tools/step_30.py block      step 29's block board: off a Sprint (rushed), then in control (a fake open);
                                      the computer's reply, timed, and what follows a block by the list
  python3 tools/step_30.py sag        step 29's sag board: where the defence's setup stands against the shooter now
  python3 tools/step_30.py checks     boards 1 to 3: both setups, timed; where the defence stands against the best
                                      shooter; fakes and blocks in the setup's one reading of the phase
  python3 tools/step_30.py elite      the elite shooter board, both setups, the same
  python3 tools/step_30.py morning    the morning board of the Sharpshooter check
  python3 tools/step_30.py turn       one computer offence turn in play, timed
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'runs', 'step30')
OLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'runs', 'step29')
os.makedirs(RUN, exist_ok=True)

import step_28 as S28            # noqa: E402  (the same boards and the same reading of them)
import step_29 as S29            # noqa: E402

SAG_O = ('I11', 'C9', 'O9', 'E4', 'M4')


def _save(name, out):
    json.dump(out, open(os.path.join(RUN, name), 'w'), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


def _old(name):
    try:
        return json.load(open(os.path.join(OLD, name)))
    except Exception:
        return None


def _reading(plan):
    """Fakes and blocks in the setup's one reading of the phase (its route read ahead, plan.horizon_read)."""
    h = (plan or {}).get('horizon') or {}
    path = h.get('path') or []
    return dict(turns=h.get('turns'), route=h.get('words'),
                fakes=sum(1 for p in path if p.get('fake')),
                blocks=sum(1 for p in path for w in (p.get('defence') or []) if 'block' in w))


def cmd_block():
    """Step 29's board: a Rim Protector set square in front of a driver. Off a Sprint (rushed, no fake), then in control
    (a fake is open). The computer's reply, and the block by the list: what the defence is left with if it blocks."""
    from playmaker_engine import agent as AG, board as B, jsbridge, rules_config as RC
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    from playmaker_engine.scoring import contest_options
    from playmaker_engine.search import reset_choice, reset_candidates
    from playmaker_engine.plan import _key_of
    import step_21 as T
    eng = jsbridge.NodeEngine().install()
    out = {}
    try:
        for label, rush in (('off a Sprint (rushed: no fake)', RC.RUSH_SPRINT), ('in control (a fake is open)', 0)):
            st = T._state(['H4', 'C9', 'O9', 'A3', 'Q9'], ['D8', 'B8', 'N8', 'B3', 'H3'], [0, 0, 0, 0, 0], ball=0,
                          off='Five Out', dfn='Iron Wall').with_(side='O', turn_n=0, rush_o=rush)
            shot = next(a for a in legal_actions(st) if a.kind == 'shot' and a.arrow != 1 and a.shot == 'layup')
            decl = apply(st, shot)
            opts = {(o.defender, o.hard): o for o in contest_options(decl, 0, 'layup') if o.defender >= 0}
            blk, con = opts.get((4, True)), opts.get((4, False))
            # what follows a block, by the list: the shooter forced back, the blocker's reset, the new phase
            node = apply(decl, next(a for a in legal_actions(decl) if a.kind == 'contest' and a.piece == 4 and a.shot == 'hard'))
            after = None

            def find(n):
                nonlocal after
                for _, lab, sub in getattr(n, 'outcomes', []):
                    if lab == 'blocked':
                        after = sub
                    find(sub)
            find(node)
            follow = None
            if after is not None and after.stage == 'reset':
                cands = reset_candidates(after)
                keys = [(str(a), _key_of(apply(after, a), st)) for a in cands]
                t0 = time.time()
                ra = AG.Agent('X', 'allstar', seed=1).choose(after)          # the computer's reset, by its search
                follow = dict(shooter_forced_back_to=B.sq(after.o[0]),
                              resets_read={k: dict(list=list(v[0][:4]), L=round(v[1], 2)) for k, v in keys},
                              computer_reset=str(ra), seconds=round(time.time() - t0, 1),
                              line=f"Blocked by X5. O1 is forced back to {B.sq(after.o[0])}; X5 resets to {B.sq(ra.dest)}.")
            ag = AG.Agent('X', 'allstar', seed=1)
            t = time.time()
            a = ag.choose(decl)
            mix = next((n for n in reversed(ag.notes) if n.get('event') == 'mix'), None)
            out[label] = dict(fake_open_at_the_shot=bool(decl.decl), defender=f"X5 ({st.ctx.dfn[4].role}) square on H3",
                              block_chance=blk and round(float((1 - blk.p_foul) * blk.p_block) * 100),
                              block_roll=blk and blk.block, foul_risk=blk and round(float(blk.p_foul) * 100),
                              contest_if_he_misses=blk and blk.contest, honest_contest=con and con.contest,
                              what_follows_a_block=follow, computer_reply=str(a), seconds=round(time.time() - t, 1),
                              mix=mix, step29=(_old('block.json') or {}).get(label, {}).get('computer_reply'))
    finally:
        eng.close()
    _save('block.json', out)


def cmd_sag():
    """Step 29's sag board (the elite shooter on I11 in control): where the defence's setup now stands against him,
    reading the full fake, and the offence's fake mix there."""
    from playmaker_engine import board as B, jsbridge, plan as PL, scouting as SCT, conditions as CD
    eng = jsbridge.NodeEngine().install()
    try:
        make = S29._elite_make()
        o = [B.parse_sq(q) for q in SAG_O]
        t = time.time()
        d = PL.place_defence(make, o, 0, seed=1)
        secs = round(time.time() - t, 1)
        st = make(o, 0, d['squares'], d['arrows'])
        j = d['perm'].index(0) if 0 in d['perm'] else min(range(5), key=lambda k: B.cheb(st.x[k], st.o[0]))
        out = dict(offence=list(SAG_O), defence=[B.sq(q) for q in d['squares']], arrows=d['arrows'], seconds=secs,
                   his_defender=f"X{j + 1} on {B.sq(st.x[j])}, {B.cheb(st.x[j], st.o[0])} squares off",
                   squares_off=B.cheb(st.x[j], st.o[0]), stance=CD.stance(st, j, 0),
                   read=[z['text'] for z in d['read']][:5], step29_sag_board_defender='X1 on I8, 3 squares off (set by hand)')
    finally:
        eng.close()
    _save('sag.json', out)


def cmd_checks(only=None):
    from playmaker_engine import board as B, jsbridge, scouting as SCT, conditions as CD
    old = _old('checks.json') or {}
    out = {}
    eng = jsbridge.NodeEngine().install()
    try:
        for off, dfn, label in S28.BOARDS:
            if only and only not in label:
                continue
            make = S28._make(off, dfn)
            r, d, so, sd = S29._setup(make)
            st = make(r['squares'], r['ball'], d['squares'], d['arrows'])
            key = f'{off} v {dfn}, {label}'
            out[key] = dict(offence=dict(squares=[B.sq(q) for q in r['squares']], ball=f"O{r['ball'] + 1}", line=(r['plan'] or {}).get('line'),
                                         seconds=so, one_reading=_reading(r.get('plan'))),
                            defence=dict(squares=[B.sq(q) for q in d['squares']], arrows=d['arrows'], seconds=sd,
                                         read=[z['text'] for z in d['read']][:4]),
                            best_shooter_now=S29._guard(B, st, d['perm'], SCT, CD),
                            best_shooter_step29=(old.get(key) or {}).get('best_shooter_now'))
    finally:
        eng.close()
    _save('checks.json' if not only else f'checks_{only.split()[0]}.json', out)


def cmd_elite():
    from playmaker_engine import board as B, jsbridge, scouting as SCT, conditions as CD
    eng = jsbridge.NodeEngine().install()
    try:
        make = S29._elite_make()
        r, d, so, sd = S29._setup(make)
        st = make(r['squares'], r['ball'], d['squares'], d['arrows'])
        out = dict(offence=dict(squares=[B.sq(q) for q in r['squares']], ball=f"O{r['ball'] + 1}", seconds=so,
                                line=(r['plan'] or {}).get('line'), one_reading=_reading(r.get('plan'))),
                   defence=dict(squares=[B.sq(q) for q in d['squares']], arrows=d['arrows'], seconds=sd,
                                read=[z['text'] for z in d['read']][:5]),
                   best_shooter=S29._guard(B, st, d['perm'], SCT, CD),
                   step29=(_old('elite.json') or {}).get('best_shooter'))
    finally:
        eng.close()
    _save('elite.json', out)


def cmd_morning():
    S29.RUN, S29.OLD = RUN, OLD
    S29.cmd_morning()


def cmd_turn():
    S29.RUN = RUN
    S29.cmd_turn()


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
