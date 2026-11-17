"""Step 19, stage 3 (Shaun, 17 Nov 2026): the play turn by turn, the coach's assessment of each phase and of the
whole possession, and the report to download.

A turn is the offence's turn and the defence's answer (the feed's own turn numbers). For each turn: the board before
it, its actions with their marks, and one line for each team, built from the coverage map at three moments: before
the offence's turn, after it, and after the defence's answer. The measure is the one D-201 rules on: the most the
offence can force by the start of the next phase, the defence's best answers counted ("their best look"); and who
covers whom. Where the map can't be read (a shot in the air, the possession over) a line says what happened, not why.
Read-only: nothing here decides a rule or changes the computer."""
from playmaker_engine import agent as AG
from playmaker_engine import board as B
from playmaker_engine import rules_config as RC

SHOT = dict(layup='layup', dunk='dunk', post='post shot', mid='mid-range two', floater='floater', long='long two', three='three')
DIRW = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west']


def _small(c):
    """What the report keeps of a coverage map: the measures and who covers whom (not every square)."""
    if not c:
        return None
    best = c.get('best')
    return dict(strength=c.get('strength'), worth=c.get('worth'), fragility=c.get('fragility'), broken=c.get('broken'),
                shot_now=c.get('shot_now'), carry_on=c.get('carry_on'), words=c.get('words'),
                best=dict(o=best['o'] if 'o' in best else best.get('a'), sq=best.get('sq'), shot=best.get('shot'), worth=best.get('worth'),
                          cover=best.get('cover'), next=best.get('next')) if best else None,
                covers=[list(d['attackers']) for d in c.get('covers', [])], answers=c.get('answers'))


def coverage_at(game, s):
    """The coverage map of a position, kept for the game (read once). None where it can't be read."""
    if s is None or s.stage != 'play' or AG.JS.get('coverage') is None:
        return None
    memo = game.__dict__.setdefault('_covmemo', {})
    k = s.encode()
    if k not in memo:
        try:
            memo[k] = _small(AG.coverage(s))
        except Exception:                  # the report must never stop a game
            memo[k] = None
    return memo[k]


def break_at(game, s):
    """Was the defence broken just before this action: the ball handler's shot now against playing on (the phase
    table), the map's own measure (coverage only='break', as phase_scores reads it)."""
    if s is None or s.stage != 'play' or AG.JS.get('coverage') is None:
        return None
    memo = game.__dict__.setdefault('_brkmemo', {})
    k = s.encode()
    if k not in memo:
        try:
            memo[k] = AG.coverage(s, only='break')
        except Exception:
            memo[k] = None
    return memo[k]


def act_words(a):
    who = f'{a.side}{a.piece + 1}' if a.piece is not None and a.piece >= 0 else ('the offence' if a.side == 'O' else 'the defence')
    k = a.kind
    if k in ('move', 'qs', 'sprint'):
        how = {'move': 'moved', 'qs': 'quick-stepped', 'sprint': 'sprinted'}[k]
        turn = '' if a.side == 'O' or a.arrow is None or a.arrow < 0 else f', facing {DIRW[a.arrow]}'
        return f'{who} {how} to {B.sq(a.dest)}{turn}'
    return {
        'pass': lambda: f'{who} passed to O{a.target + 1}',
        'screen': lambda: f'{who} set a screen',
        'dribble': lambda: f'{who} took on X{a.target + 1} off the dribble',
        'shot': lambda: f'{who} shot a {SHOT.get(a.shot, a.shot)}',
        'forced_shot': lambda: f'{who} forced up a {SHOT.get(a.shot, a.shot)}',
        'hesitate': lambda: 'the offence hesitated',
        'pause': lambda: 'the defence paused',
        'intercept': lambda: f'{who} went for the intercept',
        'steal': lambda: f'{who} went for the steal',
        'challenge': lambda: f'{who} challenged the screen',
        'contest': lambda: f'{who} contested the shot' if a.piece >= 0 else 'the defence let the shot go',
        'end_turn': lambda: f'the {"offence" if a.side == "O" else "defence"} ended its turn',
        'pick': lambda: f'the ball went to O{a.target + 1}',
    }.get(k, lambda: str(a))()


def _cap(t):
    return t[:1].upper() + t[1:] if t else t


def _series(words):
    words = [w for w in words if w]
    if len(words) <= 1:
        return ''.join(words)
    return ', '.join(words[:-1]) + ', then ' + words[-1]


def _names(xs):
    xs = [f'O{a + 1}' for a in xs]
    return ' and '.join(xs) if len(xs) <= 2 else ', '.join(xs[:-1]) + ' and ' + xs[-1]


def _look(v):
    return round(v) if v is not None else None


def turns(game, possession):
    steps = [st for st in game.__dict__.get('_trails', {}).get(possession, []) if st[1] is not None and st[1].kind != 'target']
    out = []
    for b, a, n, turn in steps:
        key = (b.phase, turn)
        if not out or out[-1]['key'] != key:
            out.append(dict(key=key, phase=b.phase, turn=turn, steps=[]))
        out[-1]['steps'].append((b, a, n))
    return out


def turn_lines(game, t):
    """The two lines of one turn, and the numbers behind them."""
    steps = t['steps']
    s0 = steps[0][0]
    off = [x for x in steps if x[1].side == 'O']
    dfn = [x for x in steps if x[1].side == 'X']
    s1 = off[-1][2] if off else s0
    s2 = steps[-1][2]
    c0, c1, c2 = coverage_at(game, s0), coverage_at(game, s1), coverage_at(game, s2)
    v0, v1, v2 = (_look(c['strength']) if c else None for c in (c0, c1, c2))
    # the offence
    shot = next((x for x in off if x[1].kind in ('shot', 'forced_shot')), None)
    o_words = _cap(_series([act_words(a) for _, a, _ in off])) if off else 'No action'
    o_eff = None
    if shot is None and v0 is not None and v1 is not None:
        o_eff = (f'their best look by next phase rose from {v0} to {v1}' if v1 > v0 else
                 f'their best look by next phase fell from {v0} to {v1}' if v1 < v0 else f'their best look stayed at {v0}')
        for d in range(5):
            was, now = c0['covers'][d], c1['covers'][d]
            if len(now) >= 2 and len(now) > len(was):
                o_eff += f'; X{d + 1} now has {_names(now)} to cover'
                break
    offence = f'Offence: {o_words}.' if not o_eff else f'Offence: {o_words}: {o_eff}.'
    # the defence's answer
    d_words = _cap(_series([act_words(a) for _, a, _ in dfn])) if dfn else 'No answer'
    d_eff = None
    if s2.stage == 'over':
        d_eff = 'the possession ended'
    elif v1 is not None and v2 is not None:
        new_phase = s2.phase != s1.phase
        d_eff = (f'that took their best look from {v1} back to {v2}' if v2 < v1 else
                 f'their best look still rose from {v1} to {v2}' if v2 > v1 else f'their best look held at {v1}')
        if new_phase:
            d_eff += ' as the phase ended'
    defence = f'Defence: {d_words}.' if not d_eff else f'Defence: {d_words}: {d_eff}.'
    shot_break = break_at(game, shot[0]) if shot else None
    return dict(phase=t['phase'], turn=t['turn'], offence=offence, defence=defence, shot_break=shot_break,
                offence_actions=[str(a) for _, a, _ in off], defence_actions=[str(a) for _, a, _ in dfn],
                numbers=dict(before=v0, after_offence=v1, after_defence=v2,
                             maps=dict(before=c0, after_offence=c1, after_defence=c2)),
                start=_start(s0), shot=dict(o=shot[1].piece, kind=shot[1].kind, shot=shot[1].shot) if shot else None,
                rose=(v1 - v0) if (v0 is not None and v1 is not None and shot is None) else None,
                answered=(v1 - v2) if (v1 is not None and v2 is not None and s2.stage != 'over') else None)


def _start(s):
    p = s.o
    return dict(o=[dict(sq=B.sq(q), ball=i == s.ball, screen=(dict(dir=s.screen_of(i)[1], t=B.sq(B.add(q, B.DIRS[s.screen_of(i)[1]]))) if s.screen_of(i) else None))
                   for i, q in enumerate(p)],
                x=[dict(sq=B.sq(q), arrow=s.arrows[i]) for i, q in enumerate(s.x)])


def _shot_words(sn):
    return f"O{sn['o'] + 1}'s {SHOT.get(sn.get('kind'), 'shot')} on {sn['sq']}, worth {round(sn['worth'])}"


def phase_assessment(game, phase, lines, next_map, broke):
    """Two or three lines a side for one finished phase, leading into the next."""
    mine = [ln for ln in lines if ln['phase'] == phase]
    if not mine:
        return None
    start = mine[0]['numbers']['before']
    end = _look(next_map['strength']) if next_map else None
    off, dfn = [], []
    if start is not None and end is not None:
        off.append(f'Their best look went from {start} to {end} this phase: the defence got {"weaker" if end > start else "stronger" if end < start else "no weaker"}.')
    took = any(ln['shot'] for ln in mine)
    for ln in mine:
        if ln['shot']:
            br = ln.get('shot_break')
            off.append(f"Turn {ln['turn']}: the shot went up" + (' with the defence broken.' if br and br.get('broken') else ' with the defence not broken.' if br else '.'))
            dfn.append(f"Turn {ln['turn']}: the shot went up against them" + (' with the defence broken.' if br and br.get('broken') else '.'))
    rises = [ln for ln in mine if ln['rose'] is not None and ln['rose'] > 0]
    if rises:
        b = max(rises, key=lambda ln: ln['rose'])
        off.append(f"Best turn: turn {b['turn']}, {b['offence'][len('Offence: '):].split(':')[0].rstrip('.')}.")
    if broke and not took:
        off.append(f'Missed: the defence was broken ({_shot_words(broke)}) and the shot was not taken.')
    elif not rises and not took:
        off.append('No turn raised their best look this phase.')
    answers = [ln for ln in mine if ln['answered'] is not None and ln['answered'] > 0]
    if answers:
        b = max(answers, key=lambda ln: ln['answered'])
        dfn.append(f"Best answer: turn {b['turn']}, {b['defence'][len('Defence: '):].split(':')[0].rstrip('.')}.")
    elif not took:
        dfn.append('No answer brought their best look down this phase.')
    if next_map and next_map.get('best'):
        bst = next_map['best']
        if bst.get('cover') is not None and bst['cover'] < 0:
            dfn.append(f"Left open: O{bst['o'] + 1} can get a {SHOT.get(bst['shot'], bst['shot'])} on {bst['sq']} next phase, with nobody to cover it.")
    nxt = None
    if next_map and next_map.get('best'):
        bst = next_map['best']
        cov = f"X{bst['cover'] + 1} covers it" if bst.get('cover') is not None and bst['cover'] >= 0 else 'nobody covers it'
        nxt = f"Next phase, look for O{bst['o'] + 1}'s {SHOT.get(bst['shot'], bst['shot'])} on {bst['sq']}, worth {round(bst['worth'])}: {cov}."
    return dict(phase=phase, start=start, end=end, offence=off[:3], defence=dfn[:3], next=nxt)


def build(game, possession, upto_phase=None):
    """The report of one possession: every turn's lines, every finished phase's assessment, and (once the possession
    is over) the whole possession's: the shot taken, the best shot on offer, the trend, the verdict, and one thing to
    keep and one to change for each side."""
    ts = turns(game, possession)
    lines = [turn_lines(game, t) for t in ts if upto_phase is None or t['phase'] <= upto_phase]
    steps = [st for st in game.__dict__.get('_trails', {}).get(possession, []) if st[1] is not None]
    over = bool(steps) and steps[-1][2].stage == 'over'
    # each phase's first position, and whether the defence was broken at any point with the shot not taken
    starts = {}
    for b, a, n, turn in steps:
        if b.stage == 'play' and b.phase not in starts:
            starts[b.phase] = b
        if n.stage == 'play' and n.phase not in starts:
            starts[n.phase] = n
    phases = []
    broken_seen = {}
    for ln in lines:
        for k in ('before', 'after_offence'):
            m = ln['numbers']['maps'][k]
            if m and m.get('broken') and m.get('shot_now') and ln['phase'] not in broken_seen:
                broken_seen[ln['phase']] = m['shot_now']
    for ph in sorted({ln['phase'] for ln in lines}):
        finished = ph + 1 in starts or over
        if not finished:
            continue
        nm = coverage_at(game, starts.get(ph + 1)) if ph + 1 in starts else None
        pa = phase_assessment(game, ph, lines, nm, broken_seen.get(ph))
        if pa:
            phases.append(pa)
    out = dict(possession=possession, teams=list(game.teams), code=game.code, turns=lines, phases=phases, over=over)
    if over and upto_phase is None:
        out['summary'] = summary(game, possession, steps, lines, phases, broken_seen)
    return out


def summary(game, possession, steps, lines, phases, broken_seen):
    from playmaker_engine.scoring import score, shot_rating
    final = steps[-1][2]
    sc = score(final)
    shot = next(((b, a) for b, a, n, t in reversed(steps) if a.kind in ('shot', 'forced_shot')), None)
    shot_line = None
    if shot:
        b, a = shot
        pts = RC.ZONE_POINTS.get(B.zone(b.o[a.piece]), 2)
        rating = shot_rating(b, a.piece, a.shot)
        open_v = pts * rating
        shot_line = (f"The shot: O{a.piece + 1}'s {SHOT.get(a.shot, a.shot)} from {B.sq(b.o[a.piece])}. Open, it was worth {open_v}; "
                     f"the contest took {open_v - sc.shot_value} off, leaving {sc.shot_value}.")
    else:
        shot_line = 'No shot went up.'
    extras = []
    if sc.free_throws:
        extras.append(f'free throws {sc.free_throws}')
    if sc.bonus:
        extras.append(f'fouls +{sc.bonus}')
    if sc.turnovers:
        extras.append(f'turnovers {sc.turnover_points}')
    score_line = f"Scored {sc.total} ({sc.band})" + (f": {', '.join(extras)}." if extras else '.')
    # the best shot that could have gone up, and when (the map's shot now, every turn)
    best = None
    for ln in lines:
        for k in ('before', 'after_offence'):
            m = ln['numbers']['maps'][k]
            if m and m.get('shot_now') and (best is None or m['shot_now']['worth'] > best[0]['worth']):
                best = (m['shot_now'], ln['phase'], ln['turn'])
    best_line = None
    if shot and (best is None or sc.shot_value >= round(best[0]['worth'])):
        best_line = 'The shot taken was the best one on offer all possession.'
    elif best:
        sn, ph, tn = best
        best_line = f"The best shot on offer: {_shot_words(sn)}, in phase {ph}, turn {tn}."
    trend = [p['start'] for p in phases if p['start'] is not None]
    if phases and phases[-1]['end'] is not None:
        trend.append(phases[-1]['end'])
    trend_line = ('Their best look, phase by phase: ' + ', '.join(str(v) for v in trend) + '.') if len(trend) > 1 else None
    shot_ln = next((ln for ln in lines if ln['shot']), None)
    took_broken = bool(shot_ln and shot_ln.get('shot_break') and shot_ln['shot_break'].get('broken'))
    missed = [ph for ph in sorted(broken_seen) if not (shot is not None and shot[0].phase == ph)]
    if took_broken:
        verdict = 'Good: the defence broke and the shot was taken.'
    elif missed:
        verdict = f'Wasted: the defence was broken in phase {missed[0]} and the shot was not taken.'
    else:
        verdict = 'Weak: the defence was never broken.'
    rises = [ln for ln in lines if ln['rose'] is not None]
    answers = [ln for ln in lines if ln['answered'] is not None]
    off_keep = off_change = dfn_keep = dfn_change = None
    up = max(rises, key=lambda ln: ln['rose'], default=None)
    if up and up['rose'] > 0:
        off_keep = f"Keep: phase {up['phase']}, turn {up['turn']}: their best look rose from {up['numbers']['before']} to {up['numbers']['after_offence']}."
    elif took_broken:
        off_keep = 'Keep: the shot went up when the defence was broken.'
    if missed:
        off_change = f'Change: in phase {missed[0]} the defence was broken; take that shot.'
    elif phases and phases[0]['end'] is not None and phases[0]['start'] is not None and phases[0]['end'] <= phases[0]['start']:
        off_change = 'Change: phase one only got you into position. Set up with a plan to weaken the defence from the start.'
    else:
        down = min(rises, key=lambda ln: ln['rose'], default=None)
        if down and down['rose'] < 0:
            off_change = f"Change: phase {down['phase']}, turn {down['turn']} let their best look fall from {down['numbers']['before']} to {down['numbers']['after_offence']}."
    good = max(answers, key=lambda ln: ln['answered'], default=None)
    if good and good['answered'] > 0:
        dfn_keep = f"Keep: phase {good['phase']}, turn {good['turn']}: the answer took their best look from {good['numbers']['after_offence']} back to {good['numbers']['after_defence']}."
    bad = min(answers, key=lambda ln: ln['answered'], default=None)
    if took_broken:
        dfn_change = f'Change: the defence was broken in phase {shot[0].phase}, and the shot went up.'
    elif bad and bad['answered'] < 0:
        dfn_change = f"Change: phase {bad['phase']}, turn {bad['turn']}: their best look still rose from {bad['numbers']['after_offence']} to {bad['numbers']['after_defence']}."
    return dict(shot=shot_line, score=score_line, best=best_line, trend=trend_line, verdict=verdict,
                offence=dict(keep=off_keep, change=off_change), defence=dict(keep=dfn_keep, change=dfn_change),
                numbers=dict(total=sc.total, band=sc.band, shot_value=sc.shot_value, free_throws=sc.free_throws, bonus=sc.bonus,
                             turnover_points=sc.turnover_points, trend=trend, best=best[0] if best else None))
