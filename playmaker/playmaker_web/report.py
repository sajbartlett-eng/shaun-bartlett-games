"""Step 19, stage 3: the play turn by turn, the coach's assessment of each phase and of the whole possession, and the
report to download. Step 20 (Shaun, 17 Nov 2026): the ruler fixed. Step 21 (D-206): the turn's numbers are read as the
computer reads them, with what each side has left this phase; phase starts (and the setup) are read like for like,
where both sides really are fresh, and a turn that ends a phase isn't put on the defence.

A turn is the offence's turn and the defence's answer (the feed's own turn numbers). Every number is the lasting gap
(D-204): what the offence can still force after the defence's best answer. A turn's change is read three times: before
it, after the offence's turn, after the defence's answer. The offence is credited with the first change, the defence
with the second, and a switch in the defence's answer is named ("Rotation: X2 took O3; X1 picked up O2."). Every roll
and its result, and every plus or minus 5, is named in the line it belongs to. Overloads are named only as the map
defines them. Before a line is printed it is checked against the numbers; a claim they can't support is rewritten as
what happened. Read-only: nothing here decides a rule or changes the computer."""
import re

from playmaker_engine import agent as AG
from playmaker_engine import board as B
from playmaker_engine import rules_config as RC

SHOT = dict(layup='layup', dunk='dunk', post='post shot', mid='mid-range two', floater='floater', long='long two', three='three')
DIRW = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west']


def _small(c):
    """What the report keeps of a coverage map: the lasting gap, what it leaves, the overloads and the answer."""
    if not c:
        return None
    left = c.get('left')
    last = c.get('clock') is not None and c['clock'] <= RC.PHASE_SECONDS
    # the last phase has no next phase: the lasting gap isn't defined there, only a shot counts (so a phase ending into
    # it can't read as the defence taking the number to 0)
    def cover_of(squares):                 # each attacker's best square, and who covers it there
        out = []
        for sq in squares or []:
            v = max(sq.values(), key=lambda r: r['worth'], default=None)
            out.append(v['cover'] if v is not None and v['worth'] > 0 else -1)
        return out
    return dict(L=None if last else c.get('lasting'), last=last, strength=c.get('strength'), before=c.get('before'), broken=c.get('broken'),
                covers_now=cover_of(c.get('squares')), covers_after=cover_of(c.get('squares_after')),
                shot_now=c.get('shot_now'), carry_on=c.get('carry_on'), words=c.get('words'),
                left=dict(o=left['o'], sq=left['sq'], shot=left['shot'], worth=left['worth'], cover=left['cover']) if left else None,
                overloads=[dict(x=v['x'], xs=v.get('xs', [v['x']]), value=v['value'], line=v['line'], threats=v['threats']) for v in c.get('overloads') or []],
                answers=c.get('answers'))


def coverage_at(game, s, fresh=False):
    """The coverage map of a position, kept for the game (read once). Step 21 (D-206): read with what each side has
    left this phase, as the computer reads it; fresh: the like-for-like read, for phase starts. None where it can't be
    read (a shot in the air, the possession over, no fast engine)."""
    if s is None or s.stage != 'play' or AG.JS.get('coverage') is None:
        return None
    memo = game.__dict__.setdefault('_covmemo', {})
    k = (s.encode(), fresh)
    if k not in memo:
        try:
            memo[k] = _small(AG.coverage(s, fresh=fresh))
        except Exception:                  # the report must never stop a game
            memo[k] = None
    return memo[k]


def _L(c):
    return round(c['L']) if c and c.get('L') is not None else None


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


def roll_words(a, entry):
    """What the dice decided, from the feed entry's own rolls: the dribble beat him, the steal won the ball, the pass
    was intercepted, the screen held. None: no roll."""
    rolls = (entry or {}).get('rolls') or []
    if not rolls:
        return None
    picked = [str(r.get('picked', '')) for r in rolls]
    last = picked[-1]
    foul = any('foul' in p and 'no foul' not in p for p in picked)
    if a.kind == 'dribble':
        return f'the dribble beat X{a.target + 1}' if last == 'success' else f'X{a.target + 1} stopped the dribble'
    if a.kind == 'intercept':
        return 'the pass got through' if last == 'success' else 'the pass was intercepted'
    if a.kind == 'steal':
        if foul:
            return 'fouled on the steal'
        return 'the steal won the ball' if last == 'stolen' else 'the steal missed'
    if a.kind == 'challenge':
        return 'the screen held' if last == 'success' else 'the challenge beat the screen'
    if a.kind == 'contest':
        return 'fouled on the contest' if foul else None
    return None


_PM5 = re.compile(r'[−+-]5\b')


def points_words(entry):
    """Every plus or minus 5 the action brought (a turnover, a foul), in the feed's own words (its first sentence)."""
    out = []
    for o in (entry or {}).get('outcomes') or []:
        t = o.get('text', '')
        if o.get('tone') in ('bad_O', 'good_O') and _PM5.search(t):
            out.append(t.split('. ')[0].rstrip('.'))
    return out


def _cap(t):
    return t[:1].upper() + t[1:] if t else t


def _low(t):
    return t[:1].lower() + t[1:] if t and not t[:2].isupper() else t


def _series(words):
    words = [w for w in words if w]
    if len(words) <= 1:
        return ''.join(words)
    return ', '.join(words[:-1]) + ', then ' + words[-1]


def _steps(game, possession):
    """The possession's steps with their feed entries: (before, action, after, turn, entry)."""
    tl = game.__dict__.get('_trails', {}).get(possession, [])
    ent = game.__dict__.get('_trail_entries', {})
    return [(b, a, n, t, ent.get((possession, i))) for i, (b, a, n, t) in enumerate(tl)]


def turns(game, possession):
    out = []
    for b, a, n, turn, e in _steps(game, possession):
        if a is None or a.kind == 'target':
            continue
        key = (b.phase, turn)
        if not out or out[-1]['key'] != key:
            out.append(dict(key=key, phase=b.phase, turn=turn, steps=[]))
        out[-1]['steps'].append((b, a, n, e))
    return out


def _side_words(steps, game=None):
    """A side's actions in words, each with its roll's result and (step 21, part 5) its own change in the lasting gap,
    read after that one action, so the turn's two actions are credited apart: "O1 moved to H10 (lasting gap from 18 to 22)".
    -> (words, plus or minus 5s, rolls, [per action: dict(text, before, after)])."""
    words, pts, rolls, each = [], [], [], []
    for b, a, n, e in steps:
        w = act_words(a)
        rw = roll_words(a, e)
        if rw:
            w += f' ({rw})'
            rolls.append(rw)
        vb = vn = None
        if game is not None and n.stage == 'play' and n.phase == b.phase:
            vb, vn = _L(coverage_at(game, b)), _L(coverage_at(game, n))
            if vb is not None and vn is not None:
                w += f' (lasting gap from {vb} to {vn})' if vn != vb else f' (lasting gap at {vb})'
        each.append(dict(text=act_words(a), before=vb, after=vn))
        words.append(w)
        pts += points_words(e)
    return _cap(_series(words)), pts, rolls, each


def _new_overload(c0, c1):
    """An overload the turn made: a defender the only cover for two attackers after it who wasn't before."""
    had = {v['x'] for v in (c0 or {}).get('overloads') or []}
    for v in (c1 or {}).get('overloads') or []:
        if v['x'] not in had:
            return v
    return None


def turn_lines(game, t):
    """The two lines of one turn, and the numbers behind them."""
    steps = t['steps']
    s0 = steps[0][0]
    off = [x for x in steps if x[1].side == 'O']
    dfn = [x for x in steps if x[1].side == 'X']
    s1 = off[-1][2] if off else s0
    s2 = steps[-1][2]
    c0, c1, c2 = coverage_at(game, s0), coverage_at(game, s1), coverage_at(game, s2)
    v0, v1, v2 = _L(c0), _L(c1), _L(c2)
    shot = next((x for x in off if x[1].kind in ('shot', 'forced_shot')), None)
    o_words, o_pts, o_rolls, o_each = _side_words(off, game) if off else ('No action', [], [], [])
    d_words, d_pts, d_rolls, d_each = _side_words(dfn, game) if dfn else ('No answer', [], [], [])
    # the offence: credited with the change its own turn made
    o_eff = None
    if shot is None and v0 is not None and v1 is not None:
        o_eff = (f'the lasting gap rose from {v0} to {v1}' if v1 > v0 else
                 f'the lasting gap fell from {v0} to {v1}' if v1 < v0 else f'the lasting gap stayed at {v0}')
        ov = _new_overload(c0, c1)
        if ov and v1 > v0:
            o_eff += f'. {ov["line"]}'
    offence = f'Offence: {o_words}.' + (f' {_cap(o_eff)}' + ('' if o_eff.endswith('.') else '.') if o_eff else '') + ''.join(f' {p}.' for p in o_pts)
    # the defence: credited with the change its answer made
    d_eff = None
    ended = s2.stage == 'play' and s2.phase != s1.phase      # the defence's turn ended the phase
    if s2.stage == 'over':
        d_eff = 'the possession ended'
    elif ended:
        # step 21: the next phase starts with both sides fresh, so the number there is read fresh, and the change
        # isn't put on the defence: the phase ended
        v2 = _L(coverage_at(game, s2, fresh=True))
        d_eff = (f'the phase ended: the next starts with the lasting gap at {v2}' if v2 is not None else None)
    elif v1 is not None and v2 is not None:
        d_eff = (f'that took the lasting gap from {v1} down to {v2}' if v2 < v1 else
                 f'the answer let the lasting gap rise from {v1} to {v2}' if v2 > v1 else f'the lasting gap held at {v1}')
    elif c2 and c2.get('last') and not (c1 and c1.get('last')):
        d_eff = 'the last phase begins: only a shot counts now'
    movers = {x[1].piece for x in dfn if x[1].kind in ('move', 'qs', 'sprint')}
    rot = rotation_words(c1, c2, movers) if dfn and not ended and s2.stage != 'over' else None
    defence = f'Defence: {d_words}.' + (f' {_cap(d_eff)}.' if d_eff else '') + (f' {rot}' if rot else '') + ''.join(f' {p}.' for p in d_pts)
    return dict(phase=t['phase'], turn=t['turn'], offence=offence, defence=defence,
                offence_actions=[str(x[1]) for x in off], defence_actions=[str(x[1]) for x in dfn],
                numbers=dict(before=v0, after_offence=v1, after_defence=v2, maps=dict(before=c0, after_offence=c1, after_defence=c2)),
                start=_start(s0), shot=dict(o=shot[1].piece, kind=shot[1].kind, shot=shot[1].shot) if shot else None,
                shot_break=break_at(game, shot[0]) if shot else None,
                rose=(v1 - v0) if (v0 is not None and v1 is not None and shot is None) else None,
                answered=(v1 - v2) if (v1 is not None and v2 is not None and s2.stage != 'over' and not ended) else None,
                rotation=rot,
                events=dict(rolls=o_rolls + d_rolls, points=o_pts + d_pts), words=dict(offence=o_words, defence=d_words),
                actions=dict(offence=o_each, defence=d_each))


def rotation_words(c1, c2, movers=None):
    """Step 21 (D-207): a switch the defence's answer made, read off the map: an attacker whose best look was covered by
    one defender before the answer and by another after it. A rotation when the first picked up someone else ("Rotation:
    X2 took O3; X1 picked up O2."); a switch otherwise ("Switch: X2 took O3 from X1."). None: no switch."""
    if not c1 or not c2:
        return None
    a1, a2 = c1.get('covers_now') or [], c2.get('covers_now') or []
    took = []
    for a in range(min(len(a1), len(a2))):
        d, e = a1[a], a2[a]
        if d >= 0 and e >= 0 and d != e and (movers is None or e in movers):   # only a defender who moved takes a man
            took.append((a, d, e))
    for a, d, e in took:
        picked = [b for b, d2, e2 in took if e2 == d and b != a]
        if picked:
            b = picked[0]
            return f'Rotation: X{e + 1} took O{a + 1}; X{d + 1} picked up O{b + 1}.'
    if took:                                    # a switch with no pick-up: name it (at most two)
        return 'Switch: ' + '; '.join(f'X{e + 1} took O{a + 1} from X{d + 1}' for a, d, e in took[:2]) + '.'
    return None


def _start(s):
    p = s.o
    return dict(o=[dict(sq=B.sq(q), ball=i == s.ball, screen=(dict(dir=s.screen_of(i)[1], t=B.sq(B.add(q, B.DIRS[s.screen_of(i)[1]]))) if s.screen_of(i) else None))
                   for i, q in enumerate(p)],
                x=[dict(sq=B.sq(q), arrow=s.arrows[i]) for i, q in enumerate(s.x)])


def _shot_words(sn):
    return f"O{sn['o'] + 1}'s {SHOT.get(sn.get('kind'), 'shot')} on {sn['sq']}, worth {round(sn['worth'])}"


def _left_words(c, lead):
    """What the defence's best answer leaves, from the map (the same number as the lasting gap's open part)."""
    lf = c.get('left') if c else None
    if not lf or round(lf['worth']) <= 0:
        return None
    cov = f"X{lf['cover'] + 1} covers it" if lf.get('cover') is not None and lf['cover'] >= 0 else 'nobody covers it'
    return f"{lead}O{lf['o'] + 1}'s {SHOT.get(lf['shot'], lf['shot'])} on {lf['sq']}, worth {round(lf['worth'])}: {cov}."


def phase_assessment(game, phase, lines, start_map, next_map, broke):
    """A few lines a side for one finished phase, leading into the next. Phase start against next phase start. Checked:
    a phase is called weaker (or stronger) only when one of its turns made it so; otherwise the line says only what the
    number did."""
    mine = [ln for ln in lines if ln['phase'] == phase]
    if not mine:
        return None
    start = _L(start_map) if start_map else mine[0]['numbers']['before']
    end = _L(next_map)
    off, dfn = [], []
    rises = [ln for ln in mine if ln['rose'] is not None and ln['rose'] > 0]
    falls = [ln for ln in mine if ln['rose'] is not None and ln['rose'] < 0]
    answers = [ln for ln in mine if ln['answered'] is not None and ln['answered'] > 0]
    let_up = [ln for ln in mine if ln['answered'] is not None and ln['answered'] < 0]
    took = [ln for ln in mine if ln['shot']]
    if start is not None and end is not None:
        if end > start and (rises or let_up):
            off.append(f'The lasting gap went from {start} to {end} this phase: the defence got weaker.')
        elif end < start and (answers or falls):
            off.append(f'The lasting gap went from {start} to {end} this phase: the defence got stronger.')
        elif end == start:
            off.append(f'The lasting gap held at {start} this phase.')
        else:                                          # the check: no turn did it, so say what the number did, not why
            off.append(f'The lasting gap went from {start} to {end} over the phase.')
    for ln in took:
        br = ln.get('shot_break')
        off.append(f"Turn {ln['turn']}: the shot went up" + (' with the defence broken.' if br and br.get('broken') else ' with the defence not broken.' if br else '.'))
        dfn.append(f"Turn {ln['turn']}: the shot went up against them" + (' with the defence broken.' if br and br.get('broken') else '.'))
    if rises:
        b = max(rises, key=lambda ln: ln['rose'])
        off.append(f"Best turn: turn {b['turn']}, {_low(b['words']['offence'])}: from {b['numbers']['before']} to {b['numbers']['after_offence']}.")
    if broke and not took:
        off.append(f'Missed: the defence was broken ({_shot_words(broke)}) and the shot was not taken.')
    elif not rises and not let_up and not took:          # (step 22b: a defence answer that let it rise is a turn that raised it)
        off.append('No turn raised the lasting gap this phase.')
    if answers:
        b = max(answers, key=lambda ln: ln['answered'])
        dfn.append(f"Best answer: turn {b['turn']}, {_low(b['words']['defence'])}: from {b['numbers']['after_offence']} down to {b['numbers']['after_defence']}.")
    for ln in let_up[:1]:
        dfn.append(f"Turn {ln['turn']}: the answer let the lasting gap rise from {ln['numbers']['after_offence']} to {ln['numbers']['after_defence']}.")
    if not answers and not let_up and not took:
        dfn.append('No answer moved the lasting gap this phase.')
    nxt = None
    if next_map:
        nxt = _left_words(next_map, 'Next phase, after the defence\'s best answer, look for ')
        for ov in (next_map.get('overloads') or [])[:1]:
            nxt = (nxt + ' ' if nxt else '') + ov['line']
    return dict(phase=phase, start=start, end=end, offence=off[:4], defence=dfn[:3], next=nxt)


def build(game, possession, upto_phase=None):
    """The report of one possession: every turn's lines, every finished phase's assessment, and (once the possession
    is over) the whole possession's: the shot taken, the best shot on offer, the trend, the verdict, and one thing to
    keep and one to change for each side."""
    ts = turns(game, possession)
    lines = [turn_lines(game, t) for t in ts if upto_phase is None or t['phase'] <= upto_phase]
    steps = [st for st in _steps(game, possession) if st[1] is not None]
    over = bool(steps) and steps[-1][2].stage == 'over'
    starts = {}                                       # each phase's first position
    for b, a, n, turn, e in steps:
        if b.stage == 'play' and b.phase not in starts:
            starts[b.phase] = b
        if n.stage == 'play' and n.phase not in starts:
            starts[n.phase] = n
    broken_seen = {}
    for ln in lines:
        for k in ('before', 'after_offence'):
            m = ln['numbers']['maps'][k]
            if m and m.get('broken') and m.get('shot_now') and ln['phase'] not in broken_seen:
                broken_seen[ln['phase']] = m['shot_now']
    phases = []
    for ph in sorted({ln['phase'] for ln in lines}):
        if not (ph + 1 in starts or over):
            continue
        nm = coverage_at(game, starts.get(ph + 1), fresh=True) if ph + 1 in starts else None      # phase starts: like for like
        pa = phase_assessment(game, ph, lines, coverage_at(game, starts.get(ph), fresh=True), nm, broken_seen.get(ph))
        if pa:
            phases.append(pa)
    out = dict(possession=possession, teams=list(game.teams), code=game.code, turns=lines, phases=phases, over=over,
               setup=setup_lines(game, steps[0][0]) if steps else None, switches=switches(game))
    if over and upto_phase is None:
        out['summary'] = summary(game, possession, steps, lines, phases, broken_seen)
    out['checks'] = consistency(out)
    return out


def consistency(rep):
    """The report checked against its own numbers (step 20): what failed, if anything. The builders above already
    rewrite a claim the numbers can't support; this is the record that they did, for the tests."""
    bad = []
    for p in rep['phases']:
        for x in p['offence']:
            if 'got weaker' in x and not any(ln['phase'] == p['phase'] and ((ln['rose'] or 0) > 0 or (ln['answered'] or 0) < 0) for ln in rep['turns']):
                bad.append(f"phase {p['phase']}: weaker with no turn that weakened it")
            if 'No turn raised' in x and p['start'] is not None and p['end'] is not None and p['end'] > p['start'] and 'got weaker' in ' '.join(p['offence']):
                bad.append(f"phase {p['phase']}: weaker beside no turn raised it")
    sm = rep.get('summary')
    if sm:
        if sm['verdict'].startswith('Good') and not any(ln.get('shot_break') and ln['shot_break'].get('broken') for ln in rep['turns']):
            bad.append('Good with no break')
        best = sm['numbers'].get('best')
        if sm['best'] and 'best one the measure saw' in sm['best'] and best and sm['numbers']['shot_value'] < round(best['worth']):
            bad.append('best shot claim')
    return bad


def setup_lines(game, s):
    """The setup as its own step: the board at tip-off and one line on what each side's setup was planning, read off
    the map after the defence's best answer (the same number as everything else)."""
    c = coverage_at(game, s, fresh=True)
    out = dict(start=_start(s), offence=None, defence=None)
    if not c:
        return out
    lw = _left_words(c, "Offence: set up so that, after the defence's best answer, the best it can still force next phase is ")
    out['offence'] = lw or "Offence: after the defence's best answer, nothing can be forced next phase from this setup."
    out['defence'] = f"Defence: set up to hold the lasting gap to {_L(c)}." + (' ' + c['overloads'][0]['line'] if c.get('overloads') else '')
    out['numbers'] = c
    return out


def switches(game):
    """What the computer played with: the reading's switches (ai_profiles.json eval) and the game's rule settings, so
    a report can be audited against the settings it came from. Nothing here is changed by the report."""
    import dataclasses
    from playmaker_engine.decide import CONFIG
    ev = CONFIG.get('eval', {})
    rules = game.state.ctx.rules
    r = {f.name: getattr(rules, f.name) for f in dataclasses.fields(rules)} if dataclasses.is_dataclass(rules) else {}
    return dict(eval={k: ev.get(k) for k in ('map', 'lane', 'pass_rules', 'leaf_mode', 'reach') if k in ev},
                computer=dict(getattr(game, 'ai', {}) or {}),
                rules={k: v for k, v in r.items() if isinstance(v, (bool, int, str, float)) or v is None})


def summary(game, possession, steps, lines, phases, broken_seen):
    from playmaker_engine.scoring import score, shot_rating
    final = steps[-1][2]
    sc = score(final)
    shot = next(((b, a) for b, a, n, t, e in reversed(steps) if a.kind in ('shot', 'forced_shot')), None)
    if shot:
        b, a = shot
        pts = RC.ZONE_POINTS.get(B.zone(b.o[a.piece]), 2)
        rating = shot_rating(b, a.piece, a.shot)
        open_v = pts * rating
        shot_line = (f"The shot: O{a.piece + 1}'s {SHOT.get(a.shot, a.shot)} from {B.sq(b.o[a.piece])}. Open, it was worth {open_v}; "
                     f"the contest took {open_v - sc.shot_value} off, leaving {sc.shot_value}.")
    else:
        shot_line = 'No shot went up.'
    events = [f"{p} (phase {ln['phase']}, turn {ln['turn']})" for ln in lines for p in ln['events']['points']]
    extras = []
    if sc.free_throws:
        extras.append(f'free throws {sc.free_throws}')
    if sc.bonus:
        extras.append(f'fouls +{sc.bonus}')
    if sc.turnovers:
        extras.append(f'turnovers {sc.turnover_points}')
    score_line = f"Scored {sc.total} ({sc.band})" + (f": {', '.join(extras)}." if extras else '.') + (f" {'; '.join(events)}." if events else '')
    # the best shot that could have gone up, and when (the map's shot now, every turn), against the shot taken
    best = None
    for ln in lines:
        for k in ('before', 'after_offence'):
            m = ln['numbers']['maps'][k]
            if m and m.get('shot_now') and (best is None or m['shot_now']['worth'] > best[0]['worth']):
                best = (m['shot_now'], ln['phase'], ln['turn'])
    if shot and (best is None or sc.shot_value >= round(best[0]['worth'])):
        best_line = 'The shot taken was the best one the measure saw all possession.'
    elif best:
        sn, ph, tn = best
        best_line = f"The best shot on offer: {_shot_words(sn)}, in phase {ph}, turn {tn}."
    else:
        best_line = None
    trend = [p['start'] for p in phases if p['start'] is not None]
    if phases and phases[-1]['end'] is not None:
        trend.append(phases[-1]['end'])
    trend_line = ('The lasting gap at the start of each phase: ' + ', '.join(str(v) for v in trend) + '.') if len(trend) > 1 else None
    shot_ln = next((ln for ln in lines if ln['shot']), None)
    took_broken = bool(shot_ln and shot_ln.get('shot_break') and shot_ln['shot_break'].get('broken'))
    missed = [ph for ph in sorted(broken_seen) if not (shot is not None and shot[0].phase == ph)]
    if took_broken:                                   # the check: "broke" only with a break the measure saw
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
        off_keep = f"Keep: phase {up['phase']}, turn {up['turn']}: the lasting gap rose from {up['numbers']['before']} to {up['numbers']['after_offence']}."
    elif took_broken:
        off_keep = 'Keep: the shot went up when the defence was broken.'
    if missed:
        off_change = f'Change: in phase {missed[0]} the defence was broken; take that shot.'
    elif phases and phases[0]['end'] is not None and phases[0]['start'] is not None and phases[0]['end'] <= phases[0]['start']:
        off_change = 'Change: phase one only got you into position. Set up with a plan to weaken the defence from the start.'
    else:
        down = min(rises, key=lambda ln: ln['rose'], default=None)
        if down and down['rose'] < 0:
            off_change = f"Change: phase {down['phase']}, turn {down['turn']} let the lasting gap fall from {down['numbers']['before']} to {down['numbers']['after_offence']}."
    good = max(answers, key=lambda ln: ln['answered'], default=None)
    if good and good['answered'] > 0:
        dfn_keep = f"Keep: phase {good['phase']}, turn {good['turn']}: the answer took the lasting gap from {good['numbers']['after_offence']} down to {good['numbers']['after_defence']}."
    bad = min(answers, key=lambda ln: ln['answered'], default=None)
    if took_broken:
        dfn_change = f'Change: the defence was broken in phase {shot[0].phase}, and the shot went up.'
    elif bad and bad['answered'] < 0:
        dfn_change = f"Change: phase {bad['phase']}, turn {bad['turn']}: the answer let the lasting gap rise from {bad['numbers']['after_offence']} to {bad['numbers']['after_defence']}."
    return dict(shot=shot_line, score=score_line, best=best_line, trend=trend_line, verdict=verdict,
                offence=dict(keep=off_keep, change=off_change), defence=dict(keep=dfn_keep, change=dfn_change),
                numbers=dict(total=sc.total, band=sc.band, shot_value=sc.shot_value, free_throws=sc.free_throws, bonus=sc.bonus,
                             turnover_points=sc.turnover_points, trend=trend, best=best[0] if best else None, events=events))
