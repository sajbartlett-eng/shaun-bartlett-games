"""Step 3n Part J: plain language for every number and action a person reads.

The engine scores however it likes inside; what reaches a human goes through here. Numbers are game points (the
scoreboard's points): whole numbers, signed only when they are a change, anchored once to a look the player knows.
Actions are sentences about the play, with the player numbers and squares the board shows, never a code string.
"""
from . import board as B

# Interface words the engine uses inside but a player never reads (tests/test_step3n.py greps every screen for these)
BANNED = ('turn group', 'credit', 'residual', 'threat', 'coverage', 'hinge', 'dilemma', 'capacity', 'drain', 'value lost',
          'leaf', 'depth', 'principal variation', 'glicko', 'volatility', '±',
          'pick-off', 'picked off', 'clean miss')          # D-85: say intercepted, stolen, a Steal that misses without a foul
BANNED_RE = (r'(?i)\bon time\b',                         # D-88: no growth tag names
             r'\bRD\b', r'\b[OX]\d? (Move|Quick Step|Sprint|Pass|Hesitate|Pause|Steal|Dribble|Screen|Shot|Intercept|Challenge)\b',
             r'\b[OX] (Hesitate|Pause|End turn)\b', r'[a-z]+:[OX]\|c\d+')

DIRS = {'N': 'north', 'NE': 'north-east', 'E': 'east', 'SE': 'south-east', 'S': 'south', 'SW': 'south-west', 'W': 'west',
        'NW': 'north-west'}
SHOTS = {'layup': 'a layup', 'dunk': 'a dunk', 'post': 'a post shot', 'mid': 'a mid-range two', 'floater': 'a floater',
         'long': 'a long two', 'three': 'a three'}
# looks a player knows, in game points (shot value = points x (rating - contest), as the scoreboard scores it)
ANCHORS = ((30, 'an excellent look'), (24, 'about an open three'), (16, 'about an open two'), (8, 'about a contested two'),
           (5, 'about a foul bonus'))


def whole(v):
    """A game-point number as a whole number."""
    return str(int(round(v)))


def change(v):
    """A change in game points: signed, whole, and '+0' never shown (say 'no change')."""
    n = int(round(v))
    return 'no change' if n == 0 else f'{n:+d}'


def anchor(v):
    """What a size of game points is like (used once per summary)."""
    v = abs(v)
    if v < 3:
        return 'a small edge'
    return min(ANCHORS, key=lambda a: abs(a[0] - v))[1]


def worth_more(v, anchored=True):
    n = int(round(abs(v)))
    if n == 0:
        return 'about the same'
    return f'worth {n} more' + (f' ({anchor(v)})' if anchored else '')


def act(a):
    """One action as a phrase: 'O3 moves to P14', 'O1 holds the ball (Hesitate)'."""
    who = f'{a.side}{a.piece + 1}' if a.piece >= 0 else ('the offence' if a.side == 'O' else 'the defence')
    k = a.kind
    to = B.sq(a.dest) if a.dest is not None else ''
    if k == 'move':
        face = f', facing {DIRS[B.DIR_NAMES[a.arrow]]}' if a.arrow >= 0 else ''
        return f'{who} moves to {to}{face}'
    if k == 'qs':
        return f'{who} takes a quick step to {to}'
    if k == 'sprint':
        return f'{who} sprints to {to}'
    if k == 'pass':
        return f'{who} passes to O{a.target + 1}'
    if k == 'screen':
        return f'{who} sets a screen'
    if k == 'dribble':
        return f'{who} drives at X{a.target + 1} (Dribble)'
    if k == 'shot':
        return f'{who} shoots {SHOTS.get(a.shot, "")}'.rstrip()
    if k == 'hesitate':
        return 'the ball handler holds the ball (Hesitate)'
    if k == 'pause':
        return 'the defence holds its ground (Pause)'
    if k == 'steal':
        return f'{who} reaches for the steal'
    if k == 'intercept':
        return f'{who} goes for the interception'
    if k == 'challenge':
        return f'{who} fights through the screen of O{a.target + 1}'
    if k == 'end_turn':
        return f'{who} ends the turn'
    if k == 'contest':
        return f'{who} contests the shot' if a.piece >= 0 else 'nobody contests'
    if k == 'forced_shot':
        return f'{who} takes the forced shot ({SHOTS.get(a.shot, a.shot)})'
    return f'{who} {k.replace("_", " ")}'


def turn(acts):
    """A whole turn as one sentence fragment: 'O3 moves to P14, then O4 moves to A9'."""
    parts = [act(a) for a in acts]
    if not parts:
        return 'nothing'
    return parts[0] if len(parts) == 1 else ', then '.join(parts)


def possessive(strs):
    """'O5's move to I5' for a movement (the first action of a stored turn), else the turn as a sentence."""
    acts = [act_from_str(t) for t in strs or []]
    if acts and acts[0] is not None and acts[0].kind in ('move', 'qs', 'sprint') and acts[0].piece >= 0:
        a = acts[0]
        verb = {'move': 'move', 'qs': 'quick step', 'sprint': 'sprint'}[a.kind]
        return f"{a.side}{a.piece + 1}'s {verb} to {B.sq(a.dest)}"
    return turn_str(strs)


def cap(text):
    return text[:1].upper() + text[1:] if text else text


def act_from_str(text):
    """An Action from its str() form (the trainer stores turns that way); None if it doesn't parse."""
    import re
    from .actions import Action
    m = re.match(r'^([OX])(\d)? ?(.*)$', text or '')
    if not m:
        return None
    side, num, rest = m.group(1), m.group(2), m.group(3)
    piece = int(num) - 1 if num else -1
    if rest.startswith('Move to '):
        mm = re.match(r'Move to ([@A-R]\d+)(?: facing (\w+))?', rest)
        return Action('move', side, piece, B.parse_sq(mm.group(1)), B.DIR_NAMES.index(mm.group(2)) if mm.group(2) else -1)
    if rest.startswith('Quick Step to '):
        return Action('qs', side, piece, B.parse_sq(rest.split(' to ')[1]))
    if rest.startswith('Sprint to '):
        return Action('sprint', side, piece, B.parse_sq(rest.split(' to ')[1]))
    if rest.startswith('Pass to O'):
        return Action('pass', side, piece, target=int(rest[9:]) - 1)
    if rest.startswith('Screen'):
        return Action('screen', side, piece, target=B.DIR_NAMES.index(rest.split('T ')[1]))
    if rest.startswith('Dribble vs X'):
        return Action('dribble', side, piece, target=int(rest[12:]) - 1)
    if rest.startswith('Shot ('):
        return Action('shot', side, piece, shot=rest[6:-1])
    if rest.startswith('Challenge screen of O'):
        return Action('challenge', side, piece, target=int(rest[21:]) - 1)
    for k in ('Hesitate', 'Pause', 'Steal', 'Intercept'):
        if rest.startswith(k):
            return Action(k.lower(), side, piece)
    if rest.startswith('End turn'):
        return Action('end_turn', side, piece)
    return None


def turn_str(strs):
    """A turn stored as action strings, as a sentence."""
    acts = [act_from_str(t) for t in strs or []]
    if any(a is None for a in acts):
        return '; '.join(strs or [])
    return turn(acts)


def confidence(rd):
    """The rating's uncertainty in words."""
    return 'still settling' if rd > 110 else 'settled'


BAND_WORDS = {'best': 'best', 'good': 'slip', 'inaccuracy': 'slip', 'mistake': 'mistake', 'blunder': 'big mistake'}


def check(text):
    """The banned terms a string contains (the Part J check)."""
    import re
    low = (text or '').lower()
    hits = [w for w in BANNED if w in low]
    hits += [p for p in BANNED_RE if re.search(p, text or '')]
    return hits
