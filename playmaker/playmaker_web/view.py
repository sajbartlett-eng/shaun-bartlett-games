"""State -> JSON for the browser. Everything shown comes from the engine; nothing here decides a rule."""
from playmaker_engine import board as B
from playmaker_engine import geometry as G
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import intercept_status
from playmaker_engine.cards import OFF, DEF, TEAMS
from playmaker_engine.scenarios import SCENARIOS
from playmaker_engine.scoring import score, choose_contest, shot_points, foul_on_shot_points, band, contest_options

from .game import action_to_json, chance_preview, FEEDBACK_QUESTIONS, _score_json

MARK = {'H': '▲', 'A': '', 'L': '▼'}
LABELS = {
    'dribble': 'Dribble', 'pass': 'Pass', 'screen': 'Screen', 'shot_layup': 'Layup', 'shot_dunk': 'Dunk',
    'shot_post': 'Post', 'shot_floater': 'Floater', 'shot_mid': 'Mid', 'shot_long': 'Long 2', 'shot_three': 'Three',
    'free_throw': 'FT', 'agility': 'Agility', 'intercept': 'Intercept', 'challenge': 'Challenge', 'steal': 'Steal',
    'foul_steal': 'Foul (steal)', 'con_layup': 'v Layup', 'con_dunk': 'v Dunk', 'con_post': 'v Post',
    'con_floater': 'v Floater', 'con_mid': 'v Mid', 'con_long': 'v Long 2', 'con_three': 'v Three',
    'foul_contest': 'Foul (contest)',
}
CHANCE_KINDS = {'dribble', 'intercept', 'challenge', 'steal', 'contest', 'forced_shot'}
# Printed-card order: actions first, then shot zones (ratings keep their ▲ / ▼ marks)
GROUPS = {
    'O': [('Actions', ['dribble', 'pass', 'screen']),
          ('Shots', ['shot_layup', 'shot_dunk', 'shot_post', 'shot_mid', 'shot_floater', 'shot_long', 'shot_three', 'free_throw'])],
    'X': [('Actions', ['agility', 'intercept', 'challenge', 'steal', 'foul_steal']),
          ('Contests', ['con_layup', 'con_dunk', 'con_post', 'con_mid', 'con_floater', 'con_long', 'con_three', 'foul_contest'])],
}


def card_json(card, side):
    names = OFF if side == 'O' else DEF
    r = lambda n: dict(name=LABELS[n], value=card.r[n], band=card.bands[n], mark=MARK[card.bands[n]])
    groups = [dict(name='Actions', ratings=[dict(name='Quick Step', value=card.qs, band='A', mark='')]
                   + [r(n) for n in GROUPS[side][0][1]]),
              dict(name=GROUPS[side][1][0], ratings=[r(n) for n in GROUPS[side][1][1]])]
    from playmaker_engine import levels as LV
    grow = getattr(card, 'growth', None)
    return dict(key=card.key, role=card.role, tier=card.tier, tagline=card.tagline, qs=card.qs,
                ratings=[r(n) for n in names], groups=groups,
                label=LV.card_label(card), age=getattr(card, 'age', 'senior'), slot=getattr(card, 'slot', card.num),
                printed=card.num, flex=LV.flex_words(card),
                coach_growth=LV.growth_line(grow))         # D-88: Coach Vision's line; no tag names on the card


def zones():
    return [[B.zone((x, y)) for x in range(B.W)] for y in range(1, B.H + 1)]


def arrow_lines(s):
    """Arrow lines the ball carrier can't cross (adjacent defenders, not beaten by a Dribble)."""
    c = s.o[s.ball]
    out = []
    for j, xp in enumerate(s.x):
        if B.adjacent(xp, c) and (s.ball, j) not in s.beaten:
            for d in G.lines(s.ctx.rules, s.arrows[j]):        # a wedge (step 3h) has two lines
                e = B.ray_end(xp, d)
                out.append(dict(defender=j, start=list(xp), end=[float(e[0]), float(e[1])]))
    return out


def influence(s):
    """Everything the board shows always, to both players at every detail level (step 3i follow-up):
    each defender's zone of influence (the movement that reaches each square: a Move or Quick Step solid,
    a Sprint as the lighter extension), each active screen's T and the diagonal steps it blocks, capacity
    badges (Move used, Quick Step used, locked) for every piece, and each attacker's movement reach this
    phase (shown when he is selected)."""
    from playmaker_engine.actions import zone, stance, movement_dests, can_move_kind
    rules = s.ctx.rules
    zones = []
    for j in range(5):
        z = zone(s, j)
        st = stance(s, j)                               # step 18g: two lines under the zone, none when it is broken
        zones.append(dict(defender=j, lines=list(G.lines(rules, st)), broken=st >= 16,
                          squares=[dict(sq=B.sq(q), x=q[0], y=q[1], kind=k) for q, k in sorted(z.items())]))
    screens = []
    for sc in s.screens:
        t = B.add(s.o[sc[0]], B.DIRS[sc[1]])
        blocked = []
        for a in [t] + [B.add(t, d) for d in B.DIRS]:
            for d in B.DIRS:
                b = B.add(a, d)
                if B.on_board(a) and B.on_board(b) and B.diag_step_banned(a, b, t, rules):
                    if [b[0], b[1], a[0], a[1]] not in blocked:
                        blocked.append([a[0], a[1], b[0], b[1]])
        screens.append(dict(screener=sc[0], t=dict(sq=B.sq(t), x=t[0], y=t[1]), blocked=blocked))
    st = s if (s.side == 'O' and s.stage == 'play') else s.with_(side='O', stage='play')
    reach = []
    for i in range(5):
        sq = set()
        for kind in ('move', 'qs', 'sprint'):
            if can_move_kind(st, 'O', i, kind):
                sq |= set(movement_dests(st, 'O', i, kind, rules))
        reach.append([dict(sq=B.sq(q), x=q[0], y=q[1]) for q in sorted(sq)])
    # rushed (D-151, rules.control): 0 set, 1 his last movement this phase was a Quick Step, 2 a Sprint
    badges = dict(O=[dict(move=s.moved('O', i), qs=s.quick_stepped('O', i), locked=s.locked('O', i), rushed=s.rush('O', i))
                     for i in range(5)],
                  X=[dict(move=s.moved('X', j), qs=s.quick_stepped('X', j), locked=s.locked('X', j), rushed=s.rush('X', j))
                     for j in range(5)])
    return dict(zones=zones, screens=screens, reach=reach, badges=badges, arrow_mode=rules.arrow_mode,
                drive_rule=rules.drive_rule, control=RC.control_size(rules), zone=rules.zone != 'off')


def rv(card, name):
    """A rating as the card prints it: value plus its ▲ / ▼ mark."""
    return f'{card.r[name]}{MARK[card.bands[name]]}'


SHOT_NAME = {'layup': 'Layup', 'dunk': 'Dunk', 'post': 'Post', 'floater': 'Floater', 'mid': 'Mid', 'long': 'Long 2',
             'three': 'Three'}


def shot_chips(s, shooter, t):
    """The comparison the tracker tells players to make, for a shot: rating v each eligible contester."""
    card = s.ctx.off[shooter]
    sp = s.o[shooter]
    out = []
    for j, xp in enumerate(s.x):
        if B.adjacent(xp, sp):
            eligible, foul_roll, penalty, cat = G.terms(s.ctx.rules, xp, s.arrows[j], sp)
            if not eligible:
                continue                      # step 3h geometries: lines off the shooter, no contest
            if s.ctx.rules.contest_geometry == 'current':
                far = ' (further from the rim: −3)' if penalty else ''
                why = 'arrow off'
            else:
                far = ' (behind: −3)' if penalty else ''
                why = cat
            out.append(f'{SHOT_NAME[t]} {rv(card, "shot_" + t)} v contest {rv(s.ctx.dfn[j], "con_" + t)} (X{j + 1}){far}'
                       + ('' if not foul_roll else f', {why}: foul roll on Foul {rv(s.ctx.dfn[j], "foul_contest")}'))
    if not out:
        out.append(f'{SHOT_NAME[t]} {rv(card, "shot_" + t)} v no contester next to the shooter now')
    return out


def matchups(s):
    """Who guards whom, as the board shows it: an adjacent defender whose arrow points at the player,
    otherwise the nearest (all tied nearest). The same for both players."""
    def pick(me, others, arrows_of_others=None, arrow_me=None):
        out = []
        if arrows_of_others is not None:
            out = [j for j, q in enumerate(others) if B.adjacent(q, me) and arrows_of_others[j] == B.dir_between(q, me)]
        if arrow_me is not None:
            out = [j for j, q in enumerate(others) if B.adjacent(q, me) and arrow_me == B.dir_between(me, q)]
        if out:
            return out
        d = [B.cheb(q, me) for q in others]
        m = min(d)
        return [j for j, v in enumerate(d) if v == m]
    return dict(O=[pick(p, s.x, arrows_of_others=s.arrows) for p in s.o],
                X=[pick(p, s.o, arrow_me=s.arrows[i]) for i, p in enumerate(s.x)])


def denied_json(s):
    """The carrier's denied lanes (receiver denial): a pass that would go through a defender next to the receiver."""
    from playmaker_engine.actions import denied_lanes
    if s.stage not in ('play',) or s.ball is None or s.ball < 0 or not B.on_board(s.o[s.ball]):
        return []
    return [dict(receiver=d['receiver'], defender=d['defender'], rsq=B.sq(s.o[d['receiver']]), dsq=B.sq(s.x[d['defender']]))
            for d in denied_lanes(s)]


def legal_json(s, acts):
    out = []
    for a in acts:
        d = action_to_json(a)
        if a.kind in CHANCE_KINDS or (a.kind == 'end_turn' and s.stage == 'reaction'):
            d['roll'] = chance_preview(s, a)
        if a.kind == 'pass' and s.ctx.rules.intercept_rule in ('ring_jump', 'move_then_intercept'):
            from playmaker_engine.actions import lane_marks
            from playmaker_engine.resolve import apply as _apply
            pend = _apply(s, a)
            marks, ring = lane_marks(pend) if getattr(pend, 'pending', None) else ([], [])
            d['threats'] = [dict(defender=m['defender'], how=m['how'], sq=B.sq(m['sq']), x=m['sq'][0], y=m['sq'][1],
                                 by=m['by'], via=B.sq(m['via']) if m['via'] else None) for m in marks]
            d['ring'] = [dict(sq=B.sq(q), x=q[0], y=q[1]) for q in ring if B.on_board(q)]
            uniq = sorted({t['defender'] for t in d['threats']})
            d['chips'] = [f'Pass {rv(s.ctx.off[a.piece], "pass")} v Intercept {rv(s.ctx.dfn[j], "intercept")} (X{j + 1})' for j in uniq]
        elif a.kind == 'pass':
            pend = s.with_(pending=(a.piece, a.target))
            d['threats'] = [dict(defender=j, how=intercept_status(pend, j)) for j in range(5)
                            if intercept_status(pend, j)]
            d['chips'] = [f'Pass {rv(s.ctx.off[a.piece], "pass")} v Intercept {rv(s.ctx.dfn[t["defender"]], "intercept")} '
                          f'(X{t["defender"] + 1})' for t in d['threats']]
        if a.kind == 'dribble':
            d['chips'] = [f'Dribble {rv(s.ctx.off[a.piece], "dribble")} v Agility {rv(s.ctx.dfn[a.target], "agility")} (X{a.target + 1})']
        if a.kind == 'screen':
            tq = B.add(s.o[a.piece], B.DIRS[a.target])
            d['chips'] = [f'Screen {rv(s.ctx.off[a.piece], "screen")} v Challenge {rv(s.ctx.dfn[j], "challenge")} (X{j + 1} on the T square)'
                          for j, xp in enumerate(s.x) if xp == tq]
        if a.kind == 'steal':
            d['chips'] = [f'Steal {rv(s.ctx.dfn[a.piece], "steal")} v Dribble {rv(s.ctx.off[s.ball], "dribble")} (O{s.ball + 1})',
                          f'Foul (steal) {rv(s.ctx.dfn[a.piece], "foul_steal")}: a straight foul roll first']
        if a.kind == 'intercept':
            d['chips'] = [f'Intercept {rv(s.ctx.dfn[a.piece], "intercept")} v Pass {rv(s.ctx.off[s.pending[0]], "pass")} (O{s.pending[0] + 1})']
        if a.kind == 'challenge':
            d['chips'] = [f'Challenge {rv(s.ctx.dfn[a.piece], "challenge")} v Screen {rv(s.ctx.off[a.target], "screen")} (O{a.target + 1})']
        if a.kind == 'contest':
            opts = {o.defender: o for o in contest_options(s, s.ball, s.shot, s.forced)}
            o = opts[a.piece]
            sh = s.ctx.off[s.ball]
            t = s.shot
            if a.piece < 0:
                d['option'] = f"Don't contest: {SHOT_NAME[t]} {rv(sh, 'shot_' + t)} v no contest"
            else:
                dc = s.ctx.dfn[a.piece]
                far = ', further from the rim: −3' if o.contest < dc.con(t) else ''
                d['option'] = (f'Contest with X{a.piece + 1}: {SHOT_NAME[t]} {rv(sh, "shot_" + t)} v contest '
                               f'{rv(dc, "con_" + t)}{far}, ' + ('arrow on the shooter (clean)' if o.clean else
                               f'arrow off the shooter: foul roll on Foul {rv(dc, "foul_contest")}'))
            d['clean'] = bool(o.clean)
        if a.kind == 'forced_shot':
            d['chips'] = shot_chips(s, a.piece, a.shot)
        if a.kind == 'shot':
            d['chips'] = shot_chips(s, a.piece, a.shot)
        out.append(d)
    return out


def screen_blocked_json(s):
    """D-104: for the defence to act, each defender's steps blocked by a screen (shown greyed, with the reason)."""
    from playmaker_engine.actions import screen_blocked
    if s.stage not in ('play', 'reaction') or s.side != 'X' or not s.screens:
        return {}
    out = {}
    for j in range(5):
        b = screen_blocked(s, j)
        if b:
            out[str(j)] = {k: [dict(x=q[0], y=q[1], sq=B.sq(q)) for q in qs] for k, qs in b.items()}
    return out


def turn_summary(s):
    if s.stage == 'contest':
        return 'Contest: the defence chooses who contests the shot (or nobody)'
    if s.stage == 'forced':
        return 'Shot clock out: the offence chooses the forced shot (turnover, −5 as well)'
    if s.stage == 'over':
        return 'Possession over'
    if s.stage == 'target':
        return "Coach's Call: the offence writes its secret target (defence, look away)"
    if s.stage == 'pick':
        return 'Failed inbound: the offence chooses who gets the ball'
    if s.stage == 'reaction':
        left = min(2 - s.turn_n, s.tok_x)
        return (f'Shot declared ({s.shot}). Defence reacts: {left} action{"s" if left != 1 else ""} left (Move, Quick Step, '
                f'Sprint, Steal or Contest; a Contest is the last). No Contest: a contest of 0')
    who = 'Offence' if s.side == 'O' else 'Defence'
    left = min(2 - s.turn_n, s.tokens(s.side))
    extra = ' · final turn of the phase' if s.side == 'X' and s.final else ''
    wk = 'pause' if s.side == 'X' else 'hesitate'
    wait = RC.LIMITS[s.side][wk]
    extra += f" · {wk.capitalize()}: {wait} a phase{' (used)' if s.count(s.side, wk) >= wait else ''}"
    if s.pending:
        extra += ' · a pass is in the air'
    return f'{who} turn: {left} action{"s" if left != 1 else ""} left · a turn-ender ends it now{extra}'


def board_json(s, slots=None):
    """The board after one action, small enough to keep with every feed entry: the page steps through the
    other side's turn one action at a time (where each piece stood, arrows, ball, clock, tokens)."""
    o = []
    for i, p in enumerate(s.o):
        sc = s.screen_of(i)
        o.append(dict(sq=B.sq(p), x=p[0], y=p[1], ball=i == s.ball, locked=s.locked('O', i), moved=s.moved('O', i),
                      slots=list(slots['O'][i]) if slots else [],
                      screen=dict(dir=sc[1], t=B.sq(B.add(p, B.DIRS[sc[1]]))) if sc else None))
    x = [dict(sq=B.sq(p), x=p[0], y=p[1], arrow=s.arrows[i], arrow_name=B.DIR_NAMES[s.arrows[i]],
              locked=s.locked('X', i), moved=s.moved('X', i), slots=list(slots['X'][i]) if slots else [])
         for i, p in enumerate(s.x)]
    return dict(o=o, x=x, clock=s.clock, phase=s.phase, stage=s.stage, tokens=dict(O=s.tok_o, X=s.tok_x),
                pending=list(s.pending) if s.pending else None, inbound=s.inbound, shot=s.shot,
                arrow_lines=arrow_lines(s) if B.on_board(s.o[s.ball]) and s.ctx.rules.drive_rule == 'arrow_line' else [],
                summary=turn_summary(s), bonus=RC.STEAL_FOUL_BONUS * s.bonus5, turnovers=s.tos,
                influence=influence(s) if s.stage != 'over' else None)


def state_json(game, token):
    game.timer_tick()                    # apply any forfeit that fell due before reading the state
    s = game.state
    ctx = s.ctx
    seat = game.seat_of(token)
    can = game.can_act(token)
    seen_o, seen_x = game.seen_cards(ctx.off_team, seat) if ctx.off_team in TEAMS else ctx.off, \
        game.seen_cards(ctx.def_team, seat) if ctx.def_team in TEAMS else ctx.dfn
    show_target = s.stage == 'over' or seat == 'O' or (game.mode == 'hotseat' and False)
    pieces_o = []
    for i, p in enumerate(s.o):
        sc = s.screen_of(i)
        pieces_o.append(dict(i=i, sq=B.sq(p), x=p[0], y=p[1], ball=i == s.ball, locked=s.locked('O', i),
                             moved=s.moved('O', i), slots=game.slots['O'][i],
                             screen=dict(dir=sc[1], t=B.sq(B.add(p, B.DIRS[sc[1]]))) if sc else None,
                             card=card_json(seen_o[i], 'O')))
    pieces_x = []
    for i, p in enumerate(s.x):
        pieces_x.append(dict(i=i, sq=B.sq(p), x=p[0], y=p[1], arrow=s.arrows[i], arrow_name=B.DIR_NAMES[s.arrows[i]],
                             locked=s.locked('X', i), moved=s.moved('X', i), slots=game.slots['X'][i],
                             card=card_json(seen_x[i], 'X')))
    limits = {side: [dict(kind=k, used=s.count(side, k), limit=v) for k, v in RC.LIMITS[side].items()]
              for side in ('O', 'X')}
    sc_info = None
    if game.scenario:
        c = SCENARIOS[game.scenario]
        sc_info = dict(n=game.scenario, title=c['title'], kind=c['kind'], clock=c['clock'], text=c['text'],
                       goal='An Excellent look: shot value 30 or more.',
                       rules=_scenario_rules(c), off=c['off'], dfn=c['dfn'])
    result = None
    if s.stage == 'over':
        sc = score(s)
        result = _score_json(sc)
    legal = legal_json(s, game.legal()) if can else []
    placing = None
    if game.placing:
        o_sq = game.placed.get('O', (None,))[0]
        occupied = {B.sq(q) for q in o_sq} if o_sq else set()
        squares = [B.sq((x, y)) for y in range(1, B.H + 1) for x in range(B.W)]
        placing = dict(side=game.placing, by_ai=game.placing in game.ai,
                       mine=(seat == 'both' or seat == game.placing) and game.placing not in game.ai,
                       squares=[q for q in squares if q not in occupied],
                       ball_squares=[q for q in squares if B.zone(B.parse_sq(q)) == '.' and B.parse_sq(q)[1] > 1],
                       offence=[B.sq(q) for q in o_sq] if o_sq else None,
                       ball=game.placed.get('O', (None, None))[1])
        if game.placing == 'X' and o_sq:
            # the defence's draft: man-to-man against the offence actually on the floor (not the table squares)
            from playmaker_web.game import man_to_man
            mx, ma = man_to_man(o_sq, game.placed['O'][1])
            placing['draft'] = dict(squares=[B.sq(q) for q in mx], arrows=list(ma))
    inbound_note = ('Inbounder: can only pass. The defence answers the pass with its normal turn.'
                    if s.inbound else None)
    out = dict(code=game.code, mode=game.mode, version=game.version, seat=seat, can_act=can,
                side_to_act=game.side_to_act(), ai=game.ai, title=ctx.title, scenario=sc_info, full=game.full,
                possession=game.possession, attacker=game.offence_player(), match_format=game.match_format,
                n_poss=game.n_poss, per_side=game.per_side, strip=score_strip(game), quarter=game.quarter_words(),
                quarter_state=game.quarter if game.match_format == 'digital' else None, teams=[ctx.off_team, ctx.def_team],
                clock=s.clock, phase=s.phase, stage=s.stage, side=s.side, turn_n=s.turn_n, final=s.final, turn=game.turn_no,
                tokens=dict(O=s.tok_o, X=s.tok_x), limits=limits, inbound=s.inbound, inbounder=ctx.inbounder,
                pending=list(s.pending) if s.pending else None, shot=s.shot,
                o=pieces_o, x=pieces_x, zones=zones(),
                arrow_lines=arrow_lines(s) if B.on_board(s.o[s.ball]) and ctx.rules.drive_rule == 'arrow_line' else [],
                bonus=RC.STEAL_FOUL_BONUS * s.bonus5, turnovers=s.tos, fouls=s.fouls,
                target=(s.target if show_target else ('secret' if s.target >= 0 else None)),
                summary=turn_summary(s), rolls=game.rolls, result=result, scores=game.scores, match=game.match,
                legal=legal, can_undo=bool(game.undo), undo_votes=sorted(game.undo_votes),
                feedback_questions=FEEDBACK_QUESTIONS, feedback_done=game.feedback is not None,
                feedback_due=game.feedback_due(), placing=placing, inbound_note=inbound_note,
                log_name=game.log_name, static=getattr(game, 'static', False),
                feed=game.feed[-40:], feed_n=len(game.feed),
                level=game.level, scout=scout_json(game, seat), matchups=matchups(s), denied=denied_json(s),
                screen_blocked=screen_blocked_json(s),
                custom=game.custom or None, experimental=game.experimental, levels=levels_json(game, seat),
                bands=[dict(name=n, low=lo) for n, lo in RC.BANDS], screen_rule=ctx.rules.screen_rule,
                influence=influence(s))
    if game.timer:
        out['timer'] = game.timer_json()
    return out


def score_strip(game):
    """Step 3m Part A: each possession's result for the score strip (points, 'TO' or 'FT') and the running totals."""
    out, tot = [], dict(A=0, B=0)
    for x in game.scores:
        kind = ('TO' if x.get('ended') in ('turnover_end', 'steal') else 'FT' if x.get('ended') == 'free_throws'
                else str(x['total']))
        tot[x['attacker']] += x['total']
        out.append(dict(possession=x['possession'], attacker=x['attacker'], total=x['total'], mark=kind))
    return dict(entries=out, totals=tot)


def levels_json(game, seat):
    """Step 3l: the dials and roster mode this game is played at, the strength totals and the growth tags (each team's
    tags only once they are face up, or to their own player)."""
    lv = game.levels
    if not lv:
        return None
    from playmaker_engine import levels as LV
    tags = {}
    for side in ('O', 'X'):
        t = game.team_of(side)
        if (lv.get('tags') or {}).get(t) and (game.tags_revealed() or side in game._viewer_sides(seat)):
            tags[t] = lv['tags'][t]
    std = lv.get('standard')
    return dict(age=lv['age'], age_words=LV.AGE_WORDS[lv['age']], roster=lv['roster'], standard=std,
                standard_words=LV.STANDARD_WORDS[std] if isinstance(std, str) else None,
                deal=lv.get('deal'), coherent=lv.get('coherent'), random=lv.get('random'),
                strength=lv.get('strength'), uneven=lv.get('uneven'), tags=tags or None,
                revealed=game.tags_revealed(), draft=lv.get('draft'))


def _scenario_rules(c):
    out = []
    if c['kind'] == 'INBOUNDS' or c.get('inb'):
        out.append('Inbounds: two phases to complete a pass from the inbounder; the clock does not run yet. '
                   'The defence answers the pass with its normal turn; then the clock starts at the card\'s number.')
    if c.get('target'):
        out.append("Coach's Call: the offence secretly names a target. If the target takes the shot: "
                   'Poor +0, Okay +2, Good +5, Great +8, Excellent +10.')
    if c['title'] == 'Need a Three':
        out.append('Only a three-point shot scores.')
    if c['title'] == 'Two or Three':
        out.append('An Excellent three wins; an Excellent two ties.')
    if c['title'] == 'Hold for One':
        out.append('No shot before the final phase (clock on 2). A turnover ends the possession at 0.')
    if c['title'] == 'In the Bonus':
        out.append('The offence starts on +5; the next steal foul gives +5 and free throws, and ends the possession.')
    if c['title'] == 'Star Locked':
        out.append('O1 starts locked until the phase resets. He can still pass or shoot.')
    if c['title'] == 'Late Clock Reset':
        out.append("Both Screens are spent; O5's screen is still standing. Offence 4 tokens, defence 4.")
    return out


def scout_json(game, seat=None):
    """The pre-game report (identical for both players) and the pick status (picks stay private).
    At Scout level the report is only sent once this client's picks are locked."""
    from playmaker_engine.scouting import report
    rep = (report(game.seen_team('O', seat), game.seen_team('X', seat), game.level, full=game.full)
           if game.report_visible(seat) else None)
    return dict(report=rep, locked=game.level == 'scout' and rep is not None,
                mine=game.picks.get(seat) if seat in ('O', 'X') else None, needs={side: game.picks_needed(side) for side in ('O', 'X')},
                done=sorted(game.picks), pending=game.picks_pending(),
                ai=[side for side in ('O', 'X') if side in game.ai],
                teams=dict(O=game.team_of('O'), X=game.team_of('X')))
