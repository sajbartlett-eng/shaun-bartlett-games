"""Scout reports from the card data and the range table only (no solver, no position).

The report describes; it never instructs. Every strength is a ▲ value and every liability a ▼ value
on the card (the bands come from the locked range table), so it says nothing the card does not.
"""
from .cards import TEAMS

MARK = {'H': '▲', 'A': '', 'L': '▼'}

# One phrase per rating and band. ▲ = above average, ▼ = below average (fouls: lower is better, and
# the card's band already says which way is good).
PHRASES = {
    'dribble': ('strong ball-handler', 'below-average ball-handler'),
    'pass': ('strong passer', 'below-average passer'),
    'screen': ('strong screener', 'below-average screener'),
    'shot_layup': ('strong finisher at the rim', 'below-average finisher at the rim'),
    'shot_dunk': ('strong dunker', 'below-average dunker'),
    'shot_post': ('strong post scorer', 'below-average post scorer'),
    'shot_floater': ('strong floater', 'below-average floater'),
    'shot_mid': ('strong mid-range shooter', 'below-average mid-range shooter'),
    'shot_long': ('strong long-two shooter', 'below-average long-two shooter'),
    'shot_three': ('strong three-point shooter', 'below-average three-point shooter'),
    'free_throw': ('strong at the line', 'below average at the line'),
    'agility': ('quick on-ball defender', 'below-average on-ball defender'),
    'intercept': ('reads passing lanes well', 'below average at reading passing lanes'),
    'challenge': ('strong at fighting through screens', 'below average at fighting through screens'),
    'steal': ('active hands', 'few steals'),
    'foul_steal': ('rarely fouls on steals', 'fouls easily on steals'),
    'con_layup': ('strong layup contest', 'below-average layup contest'),
    'con_dunk': ('strong dunk contest', 'below-average dunk contest'),
    'con_post': ('strong post contest', 'below-average post contest'),
    'con_floater': ('strong floater contest', 'below-average floater contest'),
    'con_mid': ('strong mid-range contest', 'below-average mid-range contest'),
    'con_long': ('strong long-two contest', 'below-average long-two contest'),
    'con_three': ('strong three-point contest', 'below-average three-point contest'),
    'foul_contest': ('rarely fouls on contests', 'fouls easily on contests'),
}
SHORT = {
    'dribble': 'Dribble', 'pass': 'Pass', 'screen': 'Screen', 'shot_layup': 'Layup', 'shot_dunk': 'Dunk',
    'shot_post': 'Post', 'shot_floater': 'Floater', 'shot_mid': 'Mid', 'shot_long': 'Long 2', 'shot_three': 'Three',
    'free_throw': 'FT', 'agility': 'Agility', 'intercept': 'Intercept', 'challenge': 'Challenge', 'steal': 'Steal',
    'foul_steal': 'Foul (steal)', 'con_layup': 'v Layup', 'con_dunk': 'v Dunk', 'con_post': 'v Post',
    'con_floater': 'v Floater', 'con_mid': 'v Mid', 'con_long': 'v Long 2', 'con_three': 'v Three',
    'foul_contest': 'Foul (contest)',
}
OFF_ORDER = ['shot_three', 'shot_layup', 'shot_dunk', 'shot_post', 'shot_mid', 'shot_floater', 'shot_long',
             'dribble', 'pass', 'screen', 'free_throw']
DEF_ORDER = ['agility', 'con_three', 'con_layup', 'con_dunk', 'con_post', 'con_mid', 'con_floater', 'con_long',
             'intercept', 'challenge', 'steal', 'foul_contest', 'foul_steal']
SHOTS = ['layup', 'dunk', 'post', 'floater', 'mid', 'long', 'three']
# Words the report must never contain: it describes, it does not instruct.
BANNED = ['attack', 'avoid', 'double', 'switch', 'run him', 'run her', 'run them', 'exploit', 'target', 'go at',
          'should', 'must', 'force him', 'hunt', 'help off', 'sag', 'deny him', 'mistake']


def _phrase(card, name):
    band = card.bands[name]
    if band == 'A':
        return None
    good, bad = PHRASES[name]
    return dict(rating=name, band=band, value=card.r[name],
                text=f'{good if band == "H" else bad} ({SHORT[name]} {card.r[name]}{MARK[band]})')


def _line(card, order, k=2):
    ups = [p for p in (_phrase(card, n) for n in order) if p and p['band'] == 'H'][:k]
    downs = [p for p in (_phrase(card, n) for n in order) if p and p['band'] == 'L'][:k]
    parts = [p['text'] for p in ups + downs]
    text = '; '.join(parts) if parts else 'average across the board'
    return dict(text=text[0].upper() + text[1:], strengths=ups, liabilities=downs)


def player_report(card, num):
    return dict(num=num, key=card.key, role=card.role, tier=card.tier,
                offence=_line(card, OFF_ORDER), defence=_line(card, DEF_ORDER))


def team_lists(cards):
    b = lambda c, n: c.bands[n]
    return dict(
        creators=[i + 1 for i, c in enumerate(cards) if b(c, 'dribble') == 'H' or b(c, 'pass') == 'H'],
        three_shooters=[i + 1 for i, c in enumerate(cards) if b(c, 'shot_three') == 'H'],
        rim_protectors=[i + 1 for i, c in enumerate(cards) if b(c, 'con_layup') == 'H' or b(c, 'con_dunk') == 'H'],
        defensive_liabilities=[i + 1 for i, c in enumerate(cards)
                               if sum(b(c, n) == 'L' for n in ['agility', 'intercept'] + ['con_' + t for t in SHOTS]) >= 2],
    )


def _edge(o, x, t):
    pts = 3 if t == 'three' else 2
    return pts * (o.shot(t) - x.con(t))


def best_edge(o, x):
    """Best open-matchup shot edge for attacker o against defender x (points x (rating - contest))."""
    return max(((_edge(o, x, t), t) for t in SHOTS), key=lambda e: (e[0], -SHOTS.index(e[1])))


def hunt_protect(attack, defend):
    """The team-sheet calculation, by position (O1 v X1 ... O5 v X5):
    Hunt = the attacker whose best shot edge against his own defender is largest;
    Protect (for the defending team) = the defender giving up that largest edge."""
    edges = [(best_edge(attack[i], defend[i]), i) for i in range(5)]
    (val, t), i = max(edges, key=lambda e: (e[0][0], -e[1]))
    return dict(hunt=dict(o=i + 1, x=i + 1, shot=t, edge=val,
                          text=f'O{i + 1} ({attack[i].role}) {t} {attack[i].shot(t)}{MARK[attack[i].bands["shot_" + t]]} '
                               f'meets X{i + 1} ({defend[i].role}) {t} contest {defend[i].con(t)}{MARK[defend[i].bands["con_" + t]]}'),
                protect=dict(x=i + 1, text=f'X{i + 1} ({defend[i].role}) guarding O{i + 1}'))


def cross_matchups(attack, defend, k=4):
    """Learn level: ▲ shooters meeting ▼ contests of the same shot type (by position)."""
    out = []
    for i in range(5):
        o, x = attack[i], defend[i]
        for t in SHOTS:
            if o.bands['shot_' + t] == 'H' and x.bands['con_' + t] == 'L':
                out.append(dict(o=i + 1, x=i + 1, shot=t, edge=_edge(o, x, t),
                                text=f"O{i + 1}'s {t} {o.shot(t)}▲ meets X{i + 1}'s {t} contest {x.con(t)}▼"))
    out.sort(key=lambda m: -m['edge'])
    return out[:k]


def report(off_team, def_team, level='scout'):
    """The pre-game scout report, the same for both players. level: 'learn' | 'scout' | 'pro'."""
    if level == 'pro':
        return dict(level='pro', teams=[])
    teams = []
    for name in (off_team, def_team):
        cards = TEAMS[name]
        teams.append(dict(name=name, players=[player_report(c, i + 1) for i, c in enumerate(cards)],
                          lists=team_lists(cards)))
    out = dict(level=level, teams=teams)
    if level == 'learn':
        a, d = TEAMS[off_team], TEAMS[def_team]
        out['matchups'] = cross_matchups(a, d)
        out['engine'] = hunt_protect(a, d)
    return out


def report_text(rep):
    """Every sentence the report shows (for the banned-word scan)."""
    out = []
    for t in rep.get('teams', []):
        for p in t['players']:
            out += [p['offence']['text'], p['defence']['text']]
    out += [m['text'] for m in rep.get('matchups', [])]
    if rep.get('engine'):
        out += [rep['engine']['hunt']['text'], rep['engine']['protect']['text']]
    return out
