"""Scout reports from the card data and the range table only (no solver, no position).

Step 3d: the report reads the way a scout writes. Strengths and weaknesses only, in words, no numbers,
and nothing average. Every phrase traces to a ▲ or ▼ rating on the card; every team line traces to a
threshold in scout_phrases.json. It describes; it never instructs.

The generator is a pure function of five cards (plus the range table the cards' bands come from), so it
works for any lineup, including custom teams.
"""
import json
import os

from .cards import TEAMS, CARDS, TEAMS_MOD, DATA

MARK = {'H': '▲', 'A': '', 'L': '▼'}
SHOTS = ['layup', 'dunk', 'post', 'floater', 'mid', 'long', 'three']
POSITIONS = ['PG', 'SG', 'SF', 'PF', 'C']
_SUFFIX = {'Point Guard': 'PG', 'Combo Guard': 'PG', 'Shooting Guard': 'SG', 'Small Forward': 'SF',
           'Power Forward': 'PF', 'Centre': 'C'}
_BY_NUM = {1: 'PG', 2: 'SG', 3: 'SF', 4: 'PF', 5: 'C'}

with open(os.path.join(os.path.dirname(__file__), 'scout_phrases.json')) as _f:
    CONFIG = json.load(_f)
PHRASES = {p['id']: p for p in CONFIG['player']}
TEAM_LINES = CONFIG['team']
BANNED = CONFIG['banned']
ALLOWED = CONFIG['allowed']
PRESCRIBED = [name for name, _, _ in TEAMS_MOD.TEAMS]


def position(card):
    for suffix, pos in _SUFFIX.items():
        if card.role.endswith(suffix):
            return pos
    if card.num in _BY_NUM:                  # a role that doesn't end in its position (the Slashing Wing): the card's number
        return _BY_NUM[card.num]
    raise ValueError(f'no position for {card.role}')


def short_role(card):
    """'Pass-First Point Guard' -> 'Pass-First PG' ('Combo Guard' stays as it is)."""
    for suffix in ('Point Guard', 'Shooting Guard', 'Small Forward', 'Power Forward', 'Centre'):
        if card.role.endswith(suffix):
            head = card.role[: -len(suffix)].strip()
            return f'{head} {_SUFFIX[suffix]}'.strip()
    return card.role


# ---- bands and distances -----------------------------------------------------------------------------

def band(card, r):
    if r == 'qs':
        return {2: 'H', 0: 'L'}.get(card.qs, 'A')
    return card.bands[r]


def distance(card, r):
    """How far past the band edge a ▲ / ▼ rating sits (0 = just over the line)."""
    if r == 'qs':
        return 0
    v, b = card.r[r], card.bands[r]
    if r in DATA.FOUL_RANGES:
        h, a = DATA.FOUL_RANGES[r]
        return (h - v) if b == 'H' else (v - a - 1)
    a, h = DATA.RANGES[r]
    return (v - h) if b == 'H' else (a - 1 - v)


def fires(card, spec, kind):
    """Which listed ratings make this phrase fire (empty = it does not)."""
    want = 'H' if kind == 'strength' else 'L'
    hit = [r for r in spec['any'] if band(card, r) == want]
    if not hit:
        return []
    if any(band(card, r) == 'H' for r in spec.get('unless_H', [])):
        return []
    if any(band(card, r) == 'L' for r in spec.get('unless_L', [])):
        return []
    return hit


def card_phrases(card, side, kind, learn=False):
    """Every phrase of one kind ('strength' / 'weakness') that fires on a card, unordered."""
    out = []
    for p in CONFIG['player']:
        if p['side'] != side or kind not in p:
            continue
        spec = p[kind]
        if spec.get('learn_only') and not learn:
            continue
        hit = fires(card, spec, kind)
        if hit:
            out.append(dict(id=p['id'], kind=kind, text=spec['text'], clause=spec['clause'], ratings=hit,
                            dist=max(distance(card, r) for r in hit)))
    return out


# ---- typical for the position (computed from all 75 cards) ------------------------------------------

def _typical():
    by_pos = {pos: [c for c in CARDS.values() if position(c) == pos] for pos in POSITIONS}
    out = {}
    for pos, cards in by_pos.items():
        counts = {}
        for c in cards:
            for side in ('off', 'def'):
                for kind in ('strength', 'weakness'):
                    for ph in card_phrases(c, side, kind):
                        counts[(ph['id'], kind)] = counts.get((ph['id'], kind), 0) + 1
        out[pos] = {k for k, n in counts.items() if n >= CONFIG['typical_share'] * len(cards)}
    return out


TYPICAL = _typical()


def typical_text(pos):
    return sorted(PHRASES[i][k]['text'] for i, k in TYPICAL[pos])


def ordered(card, side, kind, learn=False):
    """B2 order: unusual for the position first, then Quick Step, then distance past the band edge."""
    pos = position(card)
    order = [p['id'] for p in CONFIG['player']]
    phs = card_phrases(card, side, kind, learn)
    for ph in phs:
        ph['typical'] = (ph['id'], kind) in TYPICAL[pos]
    return sorted(phs, key=lambda ph: (ph['typical'], ph['id'] != 'quick_step', -ph['dist'], order.index(ph['id'])))


def player_lists(card, num, learn=False):
    k = CONFIG['max_per_list']
    out = dict(num=num, key=card.key, role=card.role, short=short_role(card), position=position(card))
    for side in ('off', 'def'):
        out[side] = dict(strengths=ordered(card, side, 'strength')[:k], weaknesses=ordered(card, side, 'weakness')[:k])
    return out


# ---- team lines --------------------------------------------------------------------------------------

def _passes(card, test):
    if 'H' in test:
        return any(card.bands[r] == 'H' for r in test['H'])
    if 'L' in test:
        return any(card.bands[r] == 'L' for r in test['L'])
    if 'qs' in test:
        return card.qs in test['qs']
    if 'weak' in test:
        return bool(fires(card, PHRASES[test['weak']]['weakness'], 'weakness'))
    raise ValueError(f'unknown test {test}')


def _term(cards, t):
    n = sum(_passes(c, t) for c in cards)
    return dict(count=n, holds={'>=': n >= t['n'], '<=': n <= t['n'], '==': n == t['n']}[t['op']])


def team_lines(cards):
    """Every team line that fires on these five cards, in config order, with the counts behind it."""
    fired = {}
    for line in TEAM_LINES:
        terms = line.get('all') or line.get('any')
        res = [_term(cards, t) for t in terms]
        ok = all(r['holds'] for r in res) if 'all' in line else any(r['holds'] for r in res)
        if ok and not any(u in fired for u in line.get('unless', [])):
            fired[line['id']] = dict(id=line['id'], kind=line['kind'], text=line['text'],
                                     counts=[r['count'] for r in res])
    return list(fired.values())


def team_read(cards):
    lines = team_lines(cards)
    return dict(strengths=[l['text'] for l in lines if l['kind'] == 'strength'],
                weaknesses=[l['text'] for l in lines if l['kind'] == 'weakness'], lines=lines)


# ---- shot charts (the card's own marks on the court) ----------------------------------------------

CHART_ZONES = {'K': ('rim zone', ['layup', 'dunk']), 'M': ('mid-range zone', ['mid']),
               'L': ('long-two zone', ['long']), '3': ('three-point zone', ['three'])}


def _zone_mark(card, prefix, shots):
    bands = [card.bands[prefix + s] for s in shots]
    if 'H' in bands:
        return 'H'
    return 'L' if 'L' in bands else 'A'


def shot_chart(card):
    out = {}
    for side, prefix in (('off', 'shot_'), ('def', 'con_')):
        marks = {z: _zone_mark(card, prefix, shots) for z, (_, shots) in CHART_ZONES.items()}
        strong = [CHART_ZONES[z][0] for z, m in marks.items() if m == 'H']
        weak = [CHART_ZONES[z][0] for z, m in marks.items() if m == 'L']
        what = 'Shooting' if side == 'off' else 'Contests'
        alt = (f'{what} chart. Strong (solid): {", ".join(strong) or "none"}. '
               f'Weak (hatched): {", ".join(weak) or "none"}.')
        out[side] = dict(marks=marks, alt=alt)
    return out


# ---- Learn level: mismatches by numbered pairing ---------------------------------------------------

def _has(card, pid, kind, side, learn=True):
    return any(ph['id'] == pid for ph in card_phrases(card, side, kind, learn))


def mismatches(attack, defend):
    """For one possession (attack has the ball): offence strengths meeting defence weaknesses, and defence
    strengths meeting offence weaknesses, pairing O1 with X1 and so on. Words only."""
    off_items, def_items = [], []
    for i in range(5):
        o, x = attack[i], defend[i]
        for pair in CONFIG['mismatches']['offence']:
            if not _has(x, pair['def'], 'weakness', 'def'):
                continue
            for pid in pair['off']:
                if _has(o, pid, 'strength', 'off'):
                    off_items.append(f"O{i + 1} {PHRASES[pid]['strength']['clause']}; "
                                     f"X{i + 1} {PHRASES[pair['def']]['weakness']['clause']}.")
        for pair in CONFIG['mismatches']['defence']:
            if not _has(o, pair['off'], 'weakness', 'off'):
                continue
            for pid in pair['def']:
                if _has(x, pid, 'strength', 'def'):
                    def_items.append(f"X{i + 1} {PHRASES[pid]['strength']['clause']}; "
                                     f"O{i + 1} {PHRASES[pair['off']]['weakness']['clause']}.")
    return off_items, def_items


# ---- the report --------------------------------------------------------------------------------------

def team_report(name, cards):
    read = team_read(cards)
    return dict(name=name, strengths=read['strengths'], weaknesses=read['weaknesses'],
                lines=read['lines'], nothing=CONFIG['nothing'],
                players=[dict(player_lists(c, i + 1), chart=shot_chart(c)) for i, c in enumerate(cards)])


def report(off_team, def_team, level='scout', full=False, teams=None):
    """The pre-game scout report, the same for both players. level: 'learn' | 'scout' | 'pro'.
    teams: optional {name: [cards]} for custom lineups (defaults to the prescribed TEAMS)."""
    if level == 'pro':
        return dict(level='pro', teams=[])
    lookup = teams or TEAMS
    out = dict(level=level, teams=[team_report(n, lookup[n]) for n in (off_team, def_team)])
    if level == 'learn':
        fixtures = [(off_team, def_team)] + ([(def_team, off_team)] if full else [])
        out['mismatches'] = []
        for a, d in fixtures:
            off_items, def_items = mismatches(lookup[a], lookup[d])
            out['mismatches'].append(dict(attacking=a, defending=d, offence=off_items, defence=def_items))
    return out


def report_text(rep):
    """Every sentence the report shows (for the banned-word and no-numbers scans)."""
    out = []
    for t in rep.get('teams', []):
        out += [t['name']] + t['strengths'] + t['weaknesses']
        if not t['strengths'] and not t['weaknesses']:
            out.append(t['nothing'])
        for p in t['players']:
            out.append(f"{p['num']} {p['short']}")
            for side in ('off', 'def'):
                out += [ph['text'] for ph in p[side]['strengths'] + p[side]['weaknesses']]
                out.append(p['chart'][side]['alt'])
    for m in rep.get('mismatches', []):
        out += m['offence'] + m['defence']
    return out


def banned_hits(text):
    low = text.lower()
    for ok in ALLOWED:
        low = low.replace(ok, '')
    return [w for w in BANNED if w in low]


# ---- the team sheet Hunt / Protect (unchanged from step 3c) ---------------------------------------

def _edge(o, x, t):
    pts = 3 if t == 'three' else 2
    return pts * (o.shot(t) - x.con(t))


def best_edge(o, x):
    """Best open-matchup shot edge for attacker o against defender x (points x (rating - contest))."""
    return max(((_edge(o, x, t), t) for t in SHOTS), key=lambda e: (e[0], -SHOTS.index(e[1])))


def hunt_protect(attack, defend):
    """The team-sheet calculation, by position (O1 v X1 ... O5 v X5):
    Hunt = the attacker whose best shot edge against their own defender is largest;
    Protect (for the defending team) = the defender giving up that largest edge."""
    edges = [(best_edge(attack[i], defend[i]), i) for i in range(5)]
    (val, t), i = max(edges, key=lambda e: (e[0][0], -e[1]))
    return dict(hunt=dict(o=i + 1, x=i + 1, shot=t, edge=val,
                          text=f'O{i + 1} ({attack[i].role}) {t} {attack[i].shot(t)}{MARK[attack[i].bands["shot_" + t]]} '
                               f'meets X{i + 1} ({defend[i].role}) {t} contest {defend[i].con(t)}{MARK[defend[i].bands["con_" + t]]}'),
                protect=dict(x=i + 1, text=f'X{i + 1} ({defend[i].role}) guarding O{i + 1}'))


def team_sheet_markdown():
    """The team sheet Hunt / Protect line for every ordered pairing of prescribed teams."""
    rows = ['# Team sheet: Hunt / Protect for every pairing', '',
            'Generated by `scouting.team_sheet_markdown()` from the card data (step 3d teams). By position '
            '(O1 v X1 ... O5 v X5): Hunt is the attacker with the largest best-shot edge on their own defender, '
            'Protect is that defender.', '',
            '| Offence | Defence | Hunt | Protect |', '|---|---|---|---|']
    for a in PRESCRIBED:
        for d in PRESCRIBED:
            if a != d:
                hp = hunt_protect(TEAMS[a], TEAMS[d])
                rows.append(f"| {a} | {d} | {hp['hunt']['text']} | {hp['protect']['text']} |")
    return '\n'.join(rows) + '\n'
