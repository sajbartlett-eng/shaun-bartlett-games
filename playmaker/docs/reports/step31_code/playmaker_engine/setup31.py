"""Step 31 (Shaun, 25 Nov 2026): both setups, from the Gravity and Spacing Design. No clock anywhere (D-293): each
thinks until its reading is complete. The thinking itself is the JavaScript engine's (engine.js stanceSearch and
offenceSetup, read through agent.coverage, as the map's settlement was before it); this module asks, and puts the
answer into the words the app shows. Each side reads only the board, the cards and the rules: nothing here is passed
from one side's setup to the other's (separate thinking, step 24)."""
from . import board as B

SEG_WORDS = None


def _state(make, o_sq, ball):
    """The board for the request: the offence as placed, the defence on stand-in squares (the search replaces them)."""
    from playmaker_web.game import man_to_man
    xs, arrows = man_to_man(list(o_sq), ball)
    return make(list(o_sq), ball, xs, arrows)


def _where(q):
    """Plain words for where a square is."""
    x, y = q
    rim = B.dist_rim(q)
    if rim <= 2:
        return 'at the rim'
    if 6 <= x <= 10 and y <= 6:
        return 'in the key'
    side = 'left' if x < 7 else 'right' if x > 9 else 'middle'
    if y <= 5:
        return f'on the {side} baseline' if side != 'middle' else 'in the key'
    return f'on the {side} side' if side != 'middle' else 'at the top'


def defender_lines(s, xs, arrows, man, lifted, value):
    """Each defender's line (the design's "What the player sees"): his man, where he stands, and what he is saving
    there: what the possession would be worth to the offence with him lifted off the court, less what it is worth now."""
    out = []
    for d in range(5):
        a, q = man[d], xs[d]
        gap = B.cheb(q, s.o[a])
        save = lifted[d]
        num = f' (worth {round(save, 1):g} to the offence if he weren\'t there)' if save > 1e-9 else ''
        if a == s.ball and gap <= 1:
            why = f'on the ball: he walls O{a + 1}\'s drive and contests his shot'
            text = f'X{d + 1} on O{a + 1}, the ball handler{num}.'
            sags = False
        elif gap <= 1:
            why = f'his man\'s look is worth more than any help he could give from there'
            text = f'X{d + 1} stays on O{a + 1}: O{a + 1}\'s look is worth more than any help X{d + 1} could give{num}.'
            sags = False
        else:
            why = f'he sags {gap - 1} off O{a + 1} toward the weight, {_where(q)}'
            text = (f'X{d + 1} sags {gap - 1} square{"s" if gap - 1 != 1 else ""} off O{a + 1}, {_where(q)}: '
                    f'O{a + 1} is little danger from {B.sq(s.o[a])} right now{num}.')
            sags = True
        if save <= 1e-9:
            text = text[:-1] + ' Lifting him changes nothing as the board stands.'
        out.append(dict(x=d, o=a, why=why, sags=sags, saves=save, text=text))
    return out


def place_defence(make, o_sq, ball, seed=0, level='allstar', budget=None, nth=0, scout=None):
    """The defence sets up: the weight map, the goal-side base positions, then the five stances improved together by
    the possession's value (engine.js stanceSearch). -> dict(squares, arrows, perm, value, text, read, avoided, watching)."""
    from . import agent as AG
    s = _state(make, o_sq, ball)
    r = AG.coverage(s, only='stances')
    if r is None:
        return None
    xs = [B.parse_sq(q) for q in r['x']]
    man = list(r['man'])
    lines = defender_lines(s, xs, r['arrows'], man, r['lifted'], r['value'])
    text = (f"The defence starts goal-side and improves all five stances by what the possession is worth: {r['value']:g} "
            f"after {len(r['steps'])} change{'s' if len(r['steps']) != 1 else ''} from the base positions.")
    return dict(squares=xs, arrows=list(r['arrows']), perm=man, value=round(float(r['value']), 2), read=lines, avoided=[], watching=[],
                text=text, base=dict(squares=[B.parse_sq(q) for q in r['base']['x']], arrows=list(r['base']['arrows'])),
                steps=r['steps'], lifted=r['lifted'], lines=[z['text'] for z in lines])


def place_offence(make, seed=0, level='allstar', budget=None, nth=0, scout=None, fixed=None, **_kw):
    """The offence sets up in the design's order (engine.js offenceSetup): the scout, the ball handler's start, each
    attacker's best segments, ranked against the defence's answer. fixed: (squares, ball) to keep as given (an inbound).
    -> dict(squares, ball, value, plan, words, text, candidates, within, ranked, scout)."""
    from . import agent as AG
    from playmaker_web.game import TABLE_O
    s = _state(make, [B.parse_sq(q) for q in TABLE_O], 0)
    extra = {}
    if fixed is not None:
        extra['fixed'] = dict(o=[B.sq(q) for q in fixed[0]], ball=fixed[1])
    r = AG.coverage(s, only='offence_setup', **extra)
    if r is None:
        return None
    sq = [B.parse_sq(q) for q in r['squares']]
    ball = r['ball']
    where = []
    for a in range(5):
        if a == ball:
            where.append(f'O{a + 1} starts with the ball on {r["squares"][a]}')
        else:
            row = next((z for z in r['scout'][a] if z['c'] == r['squares'][a]), None)
            where.append(f'O{a + 1} on {r["squares"][a]}' + (f' (his shot there is worth {row["weight"]:g})' if row else ''))
    text = ('The offence sets up where each man\'s shot demands a defender: ' + '; '.join(where)
            + f'. Against the defence\'s answer the possession is worth {r["value"]:g}.')
    return dict(squares=sq, ball=ball, value=round(float(r['value']), 2), plan=None, words=where, text=text, steps=[],
                candidates=r['candidates'], within=1, ranked=r['ranked'], scout=r['scout'], defence=r['defence'], seconds=None)
