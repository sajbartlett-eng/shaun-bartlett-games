"""Step 3l: playing levels (the designer's two dials, Age and Standard) on top of the cards. No rule of play changes:
only which ratings the cards carry. data/levels_data.py is the source of truth (pure literals, never edited).

  effective_card(card, age, growth_tag, slot)  the card as it plays at that age, with that growth tag, in that slot
  Age   senior  the pro cards (data.CARDS), unchanged
        youth   the pro cards + YOUTH_MODIFIER (marks unchanged: the band edges shift by the same amounts)
        junior  JUNIOR_CARDS (the U16 cards), + the growth tag's changes (marks unchanged: the card shows on time)
  Clamps after any modifier or tag: ratings 0 to 19 (Pass 20), Quick Step 0 to 2.
"""
import random

from . import cards as CD

LD = CD._load('levels_data')
AGES = LD.AGES
STANDARDS = LD.STANDARDS
TIER_VALUE = LD.TIER_VALUE
GROWTH = LD.GROWTH
GROWTH_DEAL = LD.GROWTH_DEAL
YOUTH_MODIFIER = LD.YOUTH_MODIFIER
LEVEL_INFO = LD.LEVEL_INFO
AGE_ORDER = ('senior', 'youth', 'junior')
STANDARD_ORDER = ('pro', 'semi_pro', 'amateur')
TAGS = ('early', 'typical', 'late')   # D-88: internal names only; a log from before step 6 says on_time
LABEL = {'senior': None, 'youth': 'U20', 'junior': 'U16'}

JUNIOR = {row[0]: CD.Card(*row) for row in LD.JUNIOR_CARDS}


def clamp(name, v):
    if name == 'qs':
        return max(0, min(2, v))
    return max(0, min(20 if name == 'pass' else 19, v))


_CACHE = {}


def effective_card(card, age='senior', growth_tag=None, slot=None):
    """The card as it plays: base ratings for the age, the youth modifier or the growth tag, clamped. Marks (bands) are
    the printed card's. slot: the slot it fills (1 to 5; None = its own position)."""
    key = card.key if hasattr(card, 'key') else card
    age = age or 'senior'
    tag = growth_tag if (age == 'junior' and growth_tag in ('early', 'late')) else None
    slot = slot or CD.CARDS[key].num
    ck = (key, age, tag, slot)
    hit = _CACHE.get(ck)
    if hit is not None:
        return hit
    base = JUNIOR[key] if age == 'junior' else CD.CARDS[key]
    delta = {}
    if age == 'youth':
        delta.update(YOUTH_MODIFIER)
    if tag:
        for k, v in GROWTH[tag].items():
            delta[k] = delta.get(k, 0) + v
    c = CD.Card.__new__(CD.Card)
    c.key, c.num, c.role, c.tier, c.tagline = base.key, base.num, base.role, base.tier, base.tagline
    c.qs = clamp('qs', base.qs + delta.get('qs', 0))
    c.r = {n: clamp(n, v + delta.get(n, 0)) for n, v in base.r.items()}
    c.bands = dict(base.bands)                    # marks never change
    c.age, c.growth, c.slot = age, tag, slot      # step 6: only a growth that changes the card (early or late) is recorded
    c.flex = slot != base.num
    _CACHE[ck] = c
    return c


def team(entries, age='senior', tags=None):
    """A team as it plays: entries [(key, slot)] or [key, ...] (slot = list position + 1), ordered by slot (the slot
    sets the piece: O1 is slot 1). tags: {slot: 'early' | 'typical' | 'late'} or a list in slot order."""
    ents = []
    for i, e in enumerate(entries):
        k, s = (e if isinstance(e, (tuple, list)) else (e, i + 1))
        ents.append((k.key if hasattr(k, 'key') else k, int(s)))
    ents.sort(key=lambda e: e[1])
    if isinstance(tags, (list, tuple)):
        tags = {i + 1: t for i, t in enumerate(tags)}
    tags = tags or {}
    return [effective_card(k, age, tags.get(s), s) for k, s in ents]


def deal_growth(rng):
    """One team's growth tags, slot order: 1 early, 3 typical, 1 late, shuffled (the same deal as before step 6)."""
    bag = [t for t, n in (('early', GROWTH_DEAL['early']), ('typical', GROWTH_DEAL['typical']), ('late', GROWTH_DEAL['late']))
           for _ in range(n)]
    rng.shuffle(bag)
    return bag


def growth_line(tag):
    """D-88: Coach Vision's one line on a junior whose growth changes his card (no tag names); None for the others."""
    if tag == 'early':
        return 'Bigger and stronger than most players his age.'
    if tag == 'late':
        return 'Still growing: smaller and slower than most players his age.'
    return None


def card_label(card):
    """'U16 · TIER A' for a junior card, 'U20 · TIER A' for a youth card, 'TIER A' for a senior card."""
    lab = LABEL.get(getattr(card, 'age', 'senior') or 'senior')
    return f'{lab} · TIER {card.tier}' if lab else f'TIER {card.tier}'


# ---- the levels sheet's wording (the in-app text matches the printed sheet) -----------------------------------------
AGE_WORDS = {
    'senior': 'Senior: the pro cards.',
    'youth': 'Elite youth · U18 to U20: the pro cards, plus every shot and free throw −1; Steal and Intercept +1. '
             'Young players shoot about 4 points worse and lose the ball to steals more often; fouls and contests are the same.',
    'junior': 'Junior · U14 to U16: the U16 cards. Weaker shooting and ball security, types closer together, and size and '
              'speed set by growth, not position.',
}
STANDARD_WORDS = {
    'pro': 'Pro: BBBBB · ABBBC · AABCC. The full range of tiers.',
    'semi_pro': 'Semi-pro: BBBBC · ABBCC. A little below pro.',
    'amateur': 'Amateur: BBCCC · ACCCC. Mostly C. ACCCC is the club with one standout.',
}
SHEET_INTRO = ('These levels are representative: they reproduce how each level of basketball differs from the pros, not any '
               'one league exactly. The pro cards are set at senior pro level (FIBA and NBL). The rules never change. Set two '
               'dials before you build teams, the same for both sides.')
STANDARD_NOTE = ('Pick any shape in your standard; every shape in a row is equal strength (A = +1, B = 0, C = −1). Lower tiers '
                 'weaken offence and defence together, as real lower leagues do, and amateur players are the most spread out: '
                 'the best are close to pro, the rest well short. For a handicap, give the less experienced player a higher standard.')
GROWTH_BOX = ('In the app, growth changes two players on each junior team, dealt at random: one is bigger and stronger than most '
              'players his age, one is still growing. The cards show the ratings he plays with, and Coach Vision names the two. '
              'At the table the junior cards play as printed.')


# ---- lineups in the logs (the review rebuilds the teams as they played) ---------------------------------------------
def lineup_spec(cards):
    """[[key, slot, tag or None], ...] in slot order: enough, with the age, to rebuild the team."""
    return [[c.key, getattr(c, 'slot', c.num), getattr(c, 'growth', None)] for c in cards]


def from_spec(spec, age='senior'):
    return team([(k, s) for k, s, _ in spec], age, {s: t for _, s, t in spec if t})


def as_printed(cards):
    """The same team with its growth face down (every junior card as printed)."""
    return [effective_card(c.key, getattr(c, 'age', 'senior'), None, getattr(c, 'slot', c.num)) for c in cards]


def flex_words(card):
    """'playing the 4' for a card in a slot next to its printed position, else ''."""
    return f'playing the {card.slot}' if getattr(card, 'flex', False) else ''


ROSTER_WORDS = {
    'prescribed': 'Prescribed teams: the six designed teams, as printed (pro standard). The age dial still applies.',
    'build': 'Build your teams, rules on: five different cards in a shape of your standard, one card in each slot 1 to '
             '5. The slot sets the piece: a centre in slot 4 is O4 or X4. At most one card plays one position up or '
             'down (PG 2, SG 1 or 3, SF 2 or 4, PF 3 or 5, C 4).',
    'free': 'Your team, rules off: any five cards, any tiers, any slots, duplicates allowed (digital only). Both strength '
            'totals show; uneven teams are allowed.',
    'random': 'Random deal: every legal roster is equally likely. Coherent deals give each team a creator, two '
              'shooters, a rim anchor and a stopper; pure deals are any legal roster. The deal code gives the same '
              'teams again.',
    'draft': 'Draft: snake order 1, 2, 2, 1, 1, 2, 2, 1, 1, 2. Each pick names its slot and must leave a legal roster '
             'that can still be finished from the cards left. At junior age, growth is dealt after the draft.',
}
