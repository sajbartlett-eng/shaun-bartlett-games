"""Step 24 (Shaun, 19 Nov 2026): the setup plan's checks. Each is a single reading of one board, seconds each.

python3 tools/step_24.py checks     -> docs/runs/step24/checks.json"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
RUN = os.path.join(ROOT, 'docs', 'runs', 'step24')
os.makedirs(RUN, exist_ok=True)

BOARDS = (('Shoot and Protect', 'Lockdown', "Shaun's board of 19 Nov"), ('High-Low', 'Run and Gun', "Shaun's board of 18 Nov"))


def _make(off, dfn):
    import step_21 as T
    from playmaker_engine import board as B
    return lambda o, b, x, a: T._state([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), ball=b, off=off, dfn=dfn)


def _plan_json(p):
    if not p:
        return None
    return dict(target=p['target'], needs=p['needs'], branch=p['branch'] and p['branch']['text'], backups=p['backup_words'], line=p['line'],
                spec=p['spec']['words'], backup_specs=[b['spec']['words'] for b in p['backups']], worth=p['worth'], open=p['open'], reach=p['reach'],
                bar_next_phase=p['bar'], bars=p['bars'], roles=p['roles'], conditions=[c['text'] for c in p['conditions']],
                screens=[dict(o=f"O{z['o'] + 1}", on=f"X{z['x'] + 1}", squares=z['squares'], worth=z['value'], gain=z['gain']) for z in p.get('screens') or []])


def cmd_checks():
    import step_21 as T
    from playmaker_engine import agent as AG, board as B, jsbridge, plan as PL, scouting as SCT
    from playmaker_engine.agent import Agent
    from playmaker_web.game import TABLE_O
    out = {}
    eng = jsbridge.NodeEngine().install()
    try:
        # ---- the dribble beat: a guard against a centre, at the top of the key and in the green zone ----
        s = T._state(TABLE_O, ['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1])
        sc = PL.Scout(s.ctx, 'O')
        rows = {}
        for name, q in (('the top of the key (I11)', 'I11'), ('the wing (C9)', 'C9'), ('the elbow (I7)', 'I7'), ('the green zone (I4)', 'I4')):
            rows[name] = sc.beat(s, 0, 4, B.parse_sq(q))
        top, green = rows['the top of the key (I11)'], rows['the green zone (I4)']
        out['the dribble beat'] = dict(attacker=f"O1 ({s.ctx.off[0].role}, Dribble {s.ctx.off[0].r['dribble']})", defender=f"X5 ({s.ctx.dfn[4].role}, Agility {s.ctx.dfn[4].r['agility']})",
                                       measured='the two of them alone; the coverage map before the Dribble and after a win: how many of his squares get better, and by how much in all',
                                       where=rows, large_at_the_top_small_in_the_paint=bool(top and green and top['grows'] > 3 * green['grows']))
        # ---- Shaun's two boards: each offence's plan, its placement, the defence's matchups ----
        for off, dfn, label in BOARDS:
            make = _make(off, dfn)
            t0 = time.time()
            r = PL.place_offence(make, seed=1, budget=12)
            t1 = time.time()
            d = PL.place_defence(make, r['squares'], r['ball'], seed=1)
            t2 = time.time()
            st = make(r['squares'], r['ball'], d['squares'], d['arrows'])
            pos_o = [SCT.position(c) for c in st.ctx.off]
            pos_x = [SCT.position(c) for c in st.ctx.dfn]
            arc = [f"X{x + 1} on O{o + 1} ({B.sq(r['squares'][o])})" for x, o in enumerate(d['perm'])
                   if pos_x[x] == 'C' and pos_o[o] == 'PG' and B.zone(r['squares'][o]) in ('.', '3')]
            base = [B.parse_sq(q) for q in TABLE_O]
            tab = AG._map_setup(make, base, 0, evals=0)
            out[f'{off} v {dfn} ({label})'] = dict(
                offence=dict(cards=[f"O{i + 1} {c.role}" for i, c in enumerate(st.ctx.off)], squares=[B.sq(q) for q in r['squares']], ball=f"O{r['ball'] + 1}",
                             value=r['value'], the_table_squares_for_comparison=dict(squares=TABLE_O, value=tab and round(float(tab[2]), 2)),
                             why=[dict(o=f"O{z['o'] + 1}", to=z['to'], why=z['why']) for z in r['steps']], placements_read=r['candidates'],
                             candidate_squares={f'O{a + 1}': len(sc2) for a, sc2 in enumerate(z['candidates'] for z in r['roles'])},
                             plan=_plan_json(r['plan']), checks=r['checks'], predicted_defence=r['predicted'], seconds=round(t1 - t0, 1)),
                defence=dict(cards=[f"X{i + 1} {c.role}" for i, c in enumerate(st.ctx.dfn)], squares=[B.sq(q) for q in d['squares']], arrows=d['arrows'],
                             matchups=[z['text'] for z in d['read']], avoided=[z['text'] for z in d['avoided']], lines=d['lines'],
                             the_matchup_rule=d['rule'], swaps=d['swaps'], seconds=round(t2 - t1, 1)),
                does_any_centre_guard_a_point_guard_at_the_arc=arc or False,
                does_any_poor_shooting_centre_stand_in_a_corner=[c['text'] for c in r['checks'] if c.get('check', '').startswith('a poor') and not c['passed']] or False)
        # ---- a high screen for the ball handler, the corner player free to dive ----
        pr = T._state(['I11', 'C9', 'Q3', 'A3', 'K12'], ['I10', 'D8', 'P4', 'B4', 'K11'], [0, 7, 1, 7, 0], off='High-Low', dfn='Run and Gun').with_(side='O', turn_n=0)
        scp = PL.Scout(pr.ctx, 'O')
        plan = PL.read_plan(pr, scp, deep=True)
        ag = Agent('O', 'allstar', seed=3)
        ag.setup_plan, ag.scout = plan, scp
        t0 = time.time()
        cur, turn = pr, []
        from playmaker_engine.resolve import apply
        from playmaker_engine.goals import _likeliest
        while cur.stage == 'play' and cur.side == 'O' and len(turn) < 3:
            a = ag.choose(cur)
            turn.append(str(a))
            cur = _likeliest(apply(cur, a))
        out['a high screen for the ball handler (the corner player free to dive)'] = dict(
            board=dict(o=[B.sq(q) for q in pr.o], x=[B.sq(q) for q in pr.x], offence='High-Low', defence='Run and Gun'),
            plan=_plan_json(plan), candidate_squares={f'O{a + 1}': len(scp.candidates(a)) for a in range(5)},
            the_offences_first_turn=turn, its_line=[n.get('text') for n in ag.notes if n.get('event') == 'plan'], seconds=round(time.time() - t0, 1),
            later_phases='not played out: they turn on the dice. Each phase the plan is measured again on the board as it then is.')
        # ---- a big guarded by a smaller defender: does a seal and feed appear? ----
        seal = T._state(['I11', 'C9', 'O9', 'A3', 'K4'], ['I9', 'D8', 'N8', 'B4', 'O4'], [0, 7, 0, 7, 0], off='High-Low', dfn='Run and Gun')
        seal = seal.with_(x=(B.parse_sq('K3'),) + seal.x[1:4] + (B.parse_sq('I9'),), arrows=(0, 7, 0, 7, 0))      # X1 (a guard) on O5 in the post; X5 up top
        scs = PL.Scout(seal.ctx, 'O')
        ps = PL.read_plan(seal, scs, deep=True)
        out['a big guarded by a smaller defender'] = dict(
            board=dict(o=[B.sq(q) for q in seal.o], x=[B.sq(q) for q in seal.x]), big=f"O5 {seal.ctx.off[4].role}", his_defender=f"X1 {seal.ctx.dfn[0].role}",
            o5_inside_against_x1=scs.matchup(4, 0)['zones']['K'], o5_inside_against_x5=scs.matchup(4, 4)['zones']['K'],
            plan=_plan_json(ps), a_seal_and_feed_appears=bool(ps and (ps['o'] == 4 or any(b['o'] == 4 for b in ps['backups']))))
        # ---- the defence leaves an open lane mid-plan: the sure layup, or the planned three? ----
        before = T._state(['I8', 'C9', 'O9', 'A3', 'Q3'], ['I7', 'D8', 'O8', 'H4', 'J4'], [0, 7, 0, 0, 0]).with_(side='O', turn_n=0)
        sco = PL.Scout(before.ctx, 'O')
        p0 = PL.read_plan(before, sco)
        # mid-plan: O1 has the ball on I5; the defence has gone out to the shooters and left the middle empty (X1 trails him)
        lane = before.with_(o=(B.parse_sq('I5'),) + before.o[1:], x=(B.parse_sq('I8'), before.x[1], before.x[2], B.parse_sq('B4'), B.parse_sq('P4')),
                            arrows=(4, 7, 0, 7, 1))
        stt = PL.plan_status(p0, lane, sco)
        ag2 = Agent('O', 'allstar', seed=3)
        ag2.setup_plan, ag2.scout = p0, sco
        cur, turn = lane, []
        while cur.stage == 'play' and cur.side == 'O' and len(turn) < 3:
            a = ag2.choose(cur)
            turn.append(str(a))
            cur = _likeliest(apply(cur, a))
        out['the defence leaves an open lane mid-plan'] = dict(
            the_plan_before=p0 and p0['target'], board=dict(o=[B.sq(q) for q in lane.o], x=[B.sq(q) for q in lane.x]),
            the_plan_measured_on_it=stt and dict(kind=stt['kind'], line=stt['line'], worth=stt.get('worth'), the_planned_look_is_worth=stt.get('planned')),
            the_offences_turn=turn, takes_the_lane=any(t.startswith('O1') and 'pass' not in t.lower() for t in turn))
        # ---- how much evidence changes a prediction ----
        out['evidence'] = dict(sightings_in_a_row=PL.EVIDENCE,
                               why='A setup has no dice in it. A defence does vary among setups it reads as level, so one unexpected matchup can be variety. The same unexpected matchup twice running is taken as its choice.')
    finally:
        eng.close()
    json.dump(out, open(os.path.join(RUN, 'checks.json'), 'w'), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str)[:200])


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
