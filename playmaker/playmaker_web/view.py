"""State -> JSON for the browser. Everything shown comes from the engine; nothing here decides a rule."""
from playmaker_engine import board as B
from playmaker_engine import geometry as G
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
            for d in G.lines(s.ctx.rules, s.arrows[j]):        # a wedge (step 3h) has two lines
                e = B.ray_end(xp, d)
                out.append(dict(defender=j, start=list(xp), end=[float(e[0]), float(e[1])]))
    return out


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
                arrow_lines=arrow_lines(s) if B.on_board(s.o[s.ball]) else [], summary=turn_summary(s),
                bonus=RC.STEAL_FOUL_BONUS * s.bonus5, turnovers=s.tos)


def state_json(game, token):
    game.timer_tick()                    # apply any forfeit that fell due before reading the state
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
    out = dict(code=game.code, mode=game.mode, version=game.version, seat=seat, can_act=can,
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
                level=game.level, scout=scout_json(game, seat), matchups=matchups(s),
                custom=game.custom or None, experimental=game.experimental,
                bands=[dict(name=n, low=lo) for n, lo in RC.BANDS])
    if game.timer:
        out['timer'] = game.timer_json()
    return out


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


def scout_json(game, seat=None):
    """The pre-game report (identical for both players) and the pick status (picks stay private).
    At Scout level the report is only sent once this client's picks are locked."""
    from playmaker_engine.scouting import report
    rep = (report(game.team_of('O'), game.team_of('X'), game.level, full=game.full)
           if game.report_visible(seat) else None)
    return dict(report=rep, locked=game.level == 'scout' and rep is not None,
                mine=game.picks.get(seat) if seat in ('O', 'X') else None, needs={side: game.picks_needed(side) for side in ('O', 'X')},
                done=sorted(game.picks), pending=game.picks_pending(),
                ai=[side for side in ('O', 'X') if side in game.ai],
                teams=dict(O=game.team_of('O'), X=game.team_of('X')))
