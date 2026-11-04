"""State -> JSON for the browser. Everything shown comes from the engine; nothing here decides a rule."""
from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import intercept_status
from playmaker_engine.cards import OFF, DEF
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
    return dict(key=card.key, role=card.role, tier=card.tier, tagline=card.tagline, qs=card.qs,
                ratings=[r(n) for n in names], groups=groups)


def zones():
    return [[B.zone((x, y)) for x in range(B.W)] for y in range(1, B.H + 1)]


def arrow_lines(s):
    """Arrow lines the ball carrier can't cross (adjacent defenders, not beaten by a Dribble)."""
    c = s.o[s.ball]
    out = []
    for j, xp in enumerate(s.x):
        if B.adjacent(xp, c) and (s.ball, j) not in s.beaten:
            e = B.ray_end(xp, s.arrows[j])
            out.append(dict(defender=j, start=list(xp), end=[float(e[0]), float(e[1])]))
    return out


def legal_json(s, acts):
    out = []
    for a in acts:
        d = action_to_json(a)
        if a.kind in CHANCE_KINDS or (a.kind == 'end_turn' and s.stage == 'reaction'):
            d['roll'] = chance_preview(s, a)
        if a.kind == 'pass':
            pend = s.with_(pending=(a.piece, a.target))
            d['threats'] = [dict(defender=j, how=intercept_status(pend, j)) for j in range(5)
                            if intercept_status(pend, j)]
        if a.kind == 'contest':
            opts = {o.defender: o for o in contest_options(s, s.ball, s.shot, s.forced)}
            o = opts[a.piece]
            pts = shot_points(s.o[s.ball])
            rating = s.ctx.off[s.ball].shot(s.shot)
            if a.piece < 0:
                d['option'] = f"Don't contest: {pts} × {rating} = {o.value}"
            elif o.clean:
                d['option'] = (f'Contest with X{a.piece + 1}: contest {o.contest}, clean (arrow on the shooter): '
                               f'{pts} × ({rating} − {o.contest}) = {o.value}')
            else:
                d['option'] = (f'Contest with X{a.piece + 1}: contest {o.contest}, foul roll (arrow off: foul on '
                               f'{int(o.p_foul * 20)} or less scores {o.ft}; otherwise {o.value})')
            d['clean'] = bool(o.clean)
        if a.kind == 'forced_shot':
            opt = choose_contest(s, a.piece, a.shot, True)
            d['value_now'] = f'{a.shot}: worth {float(opt.ev):.1f} against the defence\'s best contest'
        if a.kind == 'shot':
            opt = choose_contest(s, a.piece, a.shot)
            pts = shot_points(s.o[a.piece])
            rating = s.ctx.off[a.piece].shot(a.shot)
            who = f'X{opt.defender + 1}' if opt.defender >= 0 else 'nobody'
            txt = f'{a.shot}: {pts} × ({rating} − {opt.contest}) = {opt.value} if contested by {who} now'
            if not opt.clean and opt.defender >= 0:
                txt += f' (arrow off: foul on {int(opt.p_foul * 20)} or less scores {opt.ft})'
            d['value_now'] = txt + '; the defence reacts first'
        out.append(d)
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
        return f'Shot declared ({s.shot}). Defence reacts: {left} action{"s" if left != 1 else ""} left, then the contest'
    who = 'Offence' if s.side == 'O' else 'Defence'
    left = min(2 - s.turn_n, s.tokens(s.side))
    extra = ' · final turn of the phase' if s.side == 'X' and s.final else ''
    if s.pending:
        extra += ' · a pass is in the air'
    return f'{who} turn: {left} action{"s" if left != 1 else ""} left · a turn-ender ends it now{extra}'


def state_json(game, token):
    s = game.state
    ctx = s.ctx
    seat = game.seat_of(token)
    can = game.can_act(token)
    show_target = s.stage == 'over' or seat == 'O' or (game.mode == 'hotseat' and False)
    pieces_o = []
    for i, p in enumerate(s.o):
        sc = s.screen_of(i)
        pieces_o.append(dict(i=i, sq=B.sq(p), x=p[0], y=p[1], ball=i == s.ball, locked=s.locked('O', i),
                             moved=s.moved('O', i), slots=game.slots['O'][i],
                             screen=dict(dir=sc[1], t=B.sq(B.add(p, B.DIRS[sc[1]]))) if sc else None,
                             card=card_json(ctx.off[i], 'O')))
    pieces_x = []
    for i, p in enumerate(s.x):
        pieces_x.append(dict(i=i, sq=B.sq(p), x=p[0], y=p[1], arrow=s.arrows[i], arrow_name=B.DIR_NAMES[s.arrows[i]],
                             locked=s.locked('X', i), moved=s.moved('X', i), slots=game.slots['X'][i],
                             card=card_json(ctx.dfn[i], 'X')))
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
    inbound_note = ('Inbounder: can only pass. The defence answers the pass with its normal turn.'
                    if s.inbound else None)
    return dict(code=game.code, mode=game.mode, version=game.version, seat=seat, can_act=can,
                side_to_act=game.side_to_act(), ai=game.ai, title=ctx.title, scenario=sc_info, full=game.full,
                possession=game.possession, attacker=game.offence_player(), teams=[ctx.off_team, ctx.def_team],
                clock=s.clock, phase=s.phase, stage=s.stage, side=s.side, turn_n=s.turn_n, final=s.final,
                tokens=dict(O=s.tok_o, X=s.tok_x), limits=limits, inbound=s.inbound, inbounder=ctx.inbounder,
                pending=list(s.pending) if s.pending else None, shot=s.shot,
                o=pieces_o, x=pieces_x, zones=zones(), arrow_lines=arrow_lines(s) if B.on_board(s.o[s.ball]) else [],
                bonus=RC.STEAL_FOUL_BONUS * s.bonus5, turnovers=s.tos, fouls=s.fouls,
                target=(s.target if show_target else ('secret' if s.target >= 0 else None)),
                summary=turn_summary(s), rolls=game.rolls, result=result, scores=game.scores, match=game.match,
                legal=legal, can_undo=bool(game.undo), undo_votes=sorted(game.undo_votes),
                feedback_questions=FEEDBACK_QUESTIONS, feedback_done=game.feedback is not None,
                feedback_due=game.feedback_due(), placing=placing, inbound_note=inbound_note,
                log_name=game.log_name, static=getattr(game, 'static', False),
                feed=game.feed[-40:], feed_n=len(game.feed),
                bands=[dict(name=n, low=lo) for n, lo in RC.BANDS])


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
        out.append('The offence starts on +5; the next steal foul gives free throws.')
    if c['title'] == 'Star Locked':
        out.append('O1 starts locked until the phase resets. He can still pass or shoot.')
    if c['title'] == 'Late Clock Reset':
        out.append("Both Screens are spent; O5's screen is still standing. Offence 4 tokens, defence 4.")
    return out
