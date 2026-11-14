"""Step 3l: roster modes (prescribed, build with the rules on, build with the rules off, random, draft). No rule of play
changes: only how teams are picked.

A roster is five (card key, slot) entries. Rules on (B2): five different cards; a tier shape the standard allows; each
card fills one slot, normally its own position's, and at most one card may play one position up or down (PG in 2, SG in
1 or 3, SF in 2 or 4, PF in 3 or 5, C in 4). The slot sets the piece: a centre playing the 4 is O4 / X4.
"""
import itertools
import random
from collections import Counter

from . import cards as CD
from .levels import STANDARDS, TIER_VALUE, STANDARD_ORDER, AGE_ORDER, deal_growth

POS_NAME = {1: 'PG', 2: 'SG', 3: 'SF', 4: 'PF', 5: 'C'}
PER = 5                                     # cards per position per tier at the table (the app has more: BY_POS_TIER)
BY_POS_TIER = {}
for _k, _c in CD.CARDS.items():
    BY_POS_TIER.setdefault((_c.num, _c.tier), []).append(_k)
for _v in BY_POS_TIER.values():
    _v.sort()


def shape_of(keys):
    return ''.join(sorted(CD.CARDS[k].tier for k in keys))


def strength(keys):
    return sum(TIER_VALUE[CD.CARDS[k].tier] for k in keys)


def allowed_shapes(standard):
    return {''.join(sorted(s)) for s in STANDARDS[standard]['shapes']}


def slot_ok(key, slot):
    return abs(CD.CARDS[key].num - int(slot)) <= 1


def problems(entries, standard='pro', rules=True):
    """Why a roster isn't legal (plain words); [] when it is. entries [(key, slot)]. rules=False ('Your team'): any five
    cards, any tiers, any slots, duplicates allowed; only five slots, each once."""
    out = []
    if len(entries) != 5:
        return ['A team is five cards.']
    keys = [k for k, _ in entries]
    slots = [int(s) for _, s in entries]
    if any(k not in CD.CARDS for k in keys):
        return ['Unknown card.']
    if sorted(slots) != [1, 2, 3, 4, 5]:
        out.append('Each slot, 1 to 5, takes one card.')
    if not rules:
        return out
    if len(set(keys)) != 5:
        out.append('A team needs five different cards (duplicates are for "Your team", rules off).')
    sh = shape_of(keys)
    if sh not in allowed_shapes(standard):
        nm = STANDARDS[standard]['name'].lower()
        out.append(f"Tier shape {sh} isn't {'an' if nm[0] in 'aeiou' else 'a'} {nm} shape "
                   f"({' · '.join(STANDARDS[standard]['shapes'])}).")
    flex = [(k, s) for k, s in zip(keys, slots) if CD.CARDS[k].num != s]
    for k, s in flex:
        c = CD.CARDS[k]
        if abs(c.num - s) > 1:
            out.append(f'{c.role} ({POS_NAME[c.num]}) can play its own slot, {c.num}, or one either side, not slot {s}.')
    if len(flex) > 1:
        out.append('Only one card may play out of position.')
    return out


def legal(entries, standard='pro', rules=True):
    return not problems(entries, standard, rules)


# ---- counting and dealing (uniform over legal rosters) -------------------------------------------------------------

def _templates(standard, flex=True):
    """Every (slot positions, slot tiers) pattern of a legal roster with the number of rosters it holds. A pattern:
    slot s (1..5) is filled by a card of position pos[s] and tier tier[s]; at most one pos[s] != s (|pos - s| = 1)."""
    shapes = allowed_shapes(standard)
    structures = [tuple(range(1, 6))]
    if flex:
        for s in range(1, 6):
            for p in (s - 1, s + 1):
                if 1 <= p <= 5:
                    pos = list(range(1, 6))
                    pos[s - 1] = p
                    structures.append(tuple(pos))
    out = []
    for pos in structures:
        for tiers in itertools.product('ABC', repeat=5):
            if ''.join(sorted(tiers)) not in shapes:
                continue
            n = 1
            for (p, t), k in Counter(zip(pos, tiers)).items():
                for i in range(k):
                    n *= len(BY_POS_TIER.get((p, t), ())) - i      # D-184: the app has 6 small forwards and centres a tier
            if n:
                out.append((pos, tiers, n))
    return out


def count(standard, flex=True):
    return sum(n for _, _, n in _templates(standard, flex))


def count_by_shape(standard, flex=True):
    c = Counter()
    for pos, tiers, n in _templates(standard, flex):
        c[''.join(sorted(tiers))] += n
    return dict(c)


_TEMPLATES = {}


def deal_one(standard, rng, coherent=False, exclude=(), age='senior', tries=10000):
    """A uniformly random legal roster (B2, flex allowed as often as legality allows): a pattern in proportion to its
    rosters, then cards uniformly within it. coherent: redealt until it covers the four jobs. [(key, slot)]"""
    if standard not in _TEMPLATES:
        ts = _templates(standard, True)
        _TEMPLATES[standard] = (ts, list(itertools.accumulate(n for _, _, n in ts)))
    ts, cum = _TEMPLATES[standard]
    for _ in range(tries):
        pos, tiers, _n = ts[_bisect(cum, rng.random() * cum[-1])]
        groups = {}
        for s, (p, t) in enumerate(zip(pos, tiers), start=1):
            groups.setdefault((p, t), []).append(s)
        entries, ok = [], True
        for (p, t), slots in groups.items():
            pool = [k for k in BY_POS_TIER[(p, t)] if k not in exclude]
            if len(pool) < len(slots):
                ok = False
                break
            for s, k in zip(slots, rng.sample(pool, len(slots))):
                entries.append((k, s))
        if not ok:
            continue
        entries.sort(key=lambda e: e[1])
        if coherent and not coherent_ok([k for k, _ in entries], age):
            continue
        return entries
    raise RuntimeError('no roster could be dealt')


def _bisect(cum, x):
    lo, hi = 0, len(cum) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if cum[mid] > x:
            hi = mid
        else:
            lo = mid + 1
    return lo


# ---- the four jobs (teamtools.jobs, the existing definitions, by card) ----------------------------------------------

_TT = None
# The four jobs as the data tools define them on the pro cards (teamtools.jobs): a rating at or above a threshold.
# D-184: the thresholds on rescaled ratings are carried through the same maps as the cards (three 10 -> 9, dunk
# contest 11 -> 5), so the same cards hold the same jobs where the maps allow
JOB_TESTS = {'creator': (('dribble', 17), ('pass', 17)), 'shooter': (('shot_three', 9),),
             'anchor': (('con_layup', 10), ('con_dunk', 5)), 'stopper': (('agility', 8),)}
_AGE_CUT = {}


def _cut(rating, pro_cut, age):
    """Step 3m Part 0: a job threshold at the playing age. The pro threshold is carried over as the same share of the
    deck: the cut at this age is the value that the same number of the cards (as they play at this age) reach as
    reach the pro cut on the pro cards. So a junior team's shooters are the cards that shoot well among juniors.
    Step 18l (D-188): where no cut gives the same number, the nearest is taken in proportion (15 against 24 is
    further off than 37 against 24), not by the difference. On the D-186 cards the difference picked a junior three
    of 7, which 15 cards reach, and coherent junior semi-pro deals stopped existing; in proportion it picks 6, which
    37 reach (36 before the card update)."""
    key = (rating, pro_cut, age)
    if key not in _AGE_CUT:
        if age == 'senior':
            _AGE_CUT[key] = pro_cut
        else:
            from .levels import effective_card
            share = sum(1 for c in CD.CARDS.values() if c.r[rating] >= pro_cut)
            vals = sorted((effective_card(k, age).r[rating] for k in CD.CARDS), reverse=True)
            import math
            off = lambda n: abs(math.log(n / share)) if n and share else float('inf')
            best = min(range(0, 21), key=lambda t: (round(off(sum(1 for v in vals if v >= t)), 9), -t))
            _AGE_CUT[key] = best
    return _AGE_CUT[key]


def jobs(key, age='senior'):
    """creator, shooter, anchor, stopper for one card at the playing age (effective ratings, no growth tag: the tags
    are dealt after the rosters). At senior age this is exactly teamtools.jobs."""
    c = CD.CARDS[key] if age == 'senior' else __import__('playmaker_engine.levels', fromlist=['x']).effective_card(key, age)
    return {job: any(c.r[r] >= _cut(r, cut, age) for r, cut in tests) for job, tests in JOB_TESTS.items()}


def cover(keys, age='senior'):
    J = [jobs(k, age) for k in keys]
    return dict(creator=sum(j['creator'] for j in J) >= 1, shooters=sum(j['shooter'] for j in J) >= 2,
                anchor=sum(j['anchor'] for j in J) >= 1, stopper=sum(j['stopper'] for j in J) >= 1)


def coherent_ok(keys, age='senior'):
    return all(cover(keys, age).values())


# ---- deal codes ----------------------------------------------------------------------------------------------------

AGE_CODE = {'senior': 'S', 'youth': 'Y', 'junior': 'J'}
STD_CODE = {'pro': 'P', 'semi_pro': 'M', 'amateur': 'A'}
_B36 = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def _b36(n, width=6):
    s = ''
    for _ in range(width):
        s = _B36[n % 36] + s
        n //= 36
    return s


def make_code(age, standard, coherent, seed):
    return f"{AGE_CODE[age]}{STD_CODE[standard]}{'C' if coherent else 'P'}-{_b36(int(seed) % 36 ** 6)}"


def read_code(code):
    """age, standard, coherent, seed from a deal code (ValueError if it isn't one)."""
    c = str(code or '').strip().upper().replace(' ', '')
    if len(c) != 10 or c[3] != '-':
        raise ValueError('A deal code looks like SPP-0ABC12.')
    inv_a = {v: k for k, v in AGE_CODE.items()}
    inv_s = {v: k for k, v in STD_CODE.items()}
    if c[0] not in inv_a or c[1] not in inv_s or c[2] not in 'CP' or any(ch not in _B36 for ch in c[4:]):
        raise ValueError('A deal code looks like SPP-0ABC12.')
    seed = 0
    for ch in c[4:]:
        seed = seed * 36 + _B36.index(ch)
    return inv_a[c[0]], inv_s[c[1]], c[2] == 'C', seed


def deal(age='senior', standard='pro', coherent=False, seed=None, code=None):
    """Both teams from one seed (home first), and the growth tags at junior age (dealt after the rosters). The same code
    always gives the same rosters and tags. {code, age, standard, coherent, seed, rosters: [[(key, slot)] x 2],
    tags: [[tag x 5] x 2] or None}"""
    if code:
        age, standard, coherent, seed = read_code(code)
    if seed is None:
        seed = random.randrange(36 ** 6)
    code = make_code(age, standard, coherent, seed)
    rng = random.Random(code)
    home = away = None
    try:
        # step 3m: one card pool, so the matchup plays with one printed deck. Both teams are dealt independently and
        # redealt together if they share a card (uniform over legal disjoint pairs); where coherent rosters are so
        # rare that pairs keep sharing (junior amateur), the second team is dealt from the cards the first left
        for _ in range(200):
            home = deal_one(standard, rng, coherent, age=age)
            away = deal_one(standard, rng, coherent, age=age)
            if not {k for k, _ in home} & {k for k, _ in away}:
                break
        else:
            for _ in range(50):
                home = deal_one(standard, rng, coherent, age=age)
                try:
                    away = deal_one(standard, rng, coherent, exclude={k for k, _ in home}, age=age, tries=400)
                    break
                except RuntimeError:
                    continue
            else:
                raise RuntimeError
    except RuntimeError:
        raise ValueError(f"No {'coherent ' if coherent else ''}{STANDARDS[standard]['name'].lower()} {age} deal gives "
                         f"two teams from one deck. Try a pure deal.")
    tags = [deal_growth(rng), deal_growth(rng)] if age == 'junior' else None
    return dict(code=code, age=age, standard=standard, coherent=coherent, seed=seed, rosters=[home, away], tags=tags)


# ---- the draft (B5) ------------------------------------------------------------------------------------------------

SNAKE = (1, 2, 2, 1, 1, 2, 2, 1, 1, 2)


class DraftError(ValueError):
    pass


def completable(roster, taken, standard):
    """Can a roster with these (slot -> key) picks still be finished legally from the cards no one has taken?"""
    used_flex = any(CD.CARDS[k].num != s for s, k in roster.items())
    tiers = [CD.CARDS[k].tier for k in roster.values()]
    shapes = allowed_shapes(standard)
    free = [s for s in range(1, 6) if s not in roster]
    avail = Counter((CD.CARDS[k].num, CD.CARDS[k].tier) for k in CD.CARDS if k not in taken and k not in roster.values())

    def go(i, flex, tiers):
        if i == len(free):
            return ''.join(sorted(tiers)) in shapes
        s = free[i]
        for p in ([s] + ([q for q in (s - 1, s + 1) if 1 <= q <= 5] if not flex else [])):
            for t in 'ABC':
                if avail[(p, t)] > 0:
                    avail[(p, t)] -= 1
                    ok = go(i + 1, flex or p != s, tiers + [t])
                    avail[(p, t)] += 1
                    if ok:
                        return True
        return False
    return go(0, used_flex, tiers)


class Draft:
    """Two sides alternate picks in snake order (1, 2, 2, 1, 1, 2, 2, 1, 1, 2). Each pick names its slot; every pick
    must leave a legal roster still completable from the cards left. standards: one per side (the handicap option) or
    the same for both."""

    def __init__(self, standard='pro', age='senior', standards=None, seed=None):
        self.age = age
        self.standards = {1: (standards or {}).get(1, standard), 2: (standards or {}).get(2, standard)}
        self.rosters = {1: {}, 2: {}}
        self.picks = []                              # (side, key, slot, reason)
        self.seed = seed if seed is not None else random.randrange(10 ** 6)

    @property
    def taken(self):
        return {k for r in self.rosters.values() for k in r.values()}

    @property
    def turn(self):
        return SNAKE[len(self.picks)] if len(self.picks) < len(SNAKE) else None

    def done(self):
        return len(self.picks) == len(SNAKE)

    def check(self, side, key, slot):
        """The reason a pick isn't allowed, or None."""
        if self.done():
            return 'The draft is over.'
        if side != self.turn:
            return f'It is side {self.turn}\'s pick.'
        if key not in CD.CARDS:
            return 'Unknown card.'
        if key in self.taken:
            return 'That card is gone.'
        slot = int(slot)
        r = self.rosters[side]
        if slot in r:
            return f'Slot {slot} is filled.'
        c = CD.CARDS[key]
        if not slot_ok(key, slot):
            return f'{c.role} ({POS_NAME[c.num]}) can play slot {c.num} or one either side, not slot {slot}.'
        if c.num != slot and any(CD.CARDS[k].num != s for s, k in r.items()):
            return 'Only one card may play out of position, and this roster has one.'
        trial = dict(r)
        trial[slot] = key
        std = self.standards[side]
        if not completable(trial, self.taken | {key}, std):
            nm = STANDARDS[std]['name'].lower()
            return f"This pick leaves no legal {nm} shape."
        return None

    def legal_picks(self, side):
        out = []
        for key in CD.CARDS:
            if key in self.taken:
                continue
            for slot in range(1, 6):
                if self.check(side, key, slot) is None:
                    out.append((key, slot))
        return out

    def pick(self, side, key, slot, reason=None):
        why = self.check(side, key, slot)
        if why:
            raise DraftError(why)
        self.rosters[side][int(slot)] = key
        self.picks.append((side, key, int(slot), reason))

    @property
    def log(self):
        """Every pick in order, with the computer's reason where it picked (the review shows them)."""
        return [dict(n=i + 1, side=sd, key=k, slot=s, role=CD.CARDS[k].role, tier=CD.CARDS[k].tier,
                     by='computer' if r else 'player', reason=r) for i, (sd, k, s, r) in enumerate(self.picks)]

    def roster(self, side):
        return sorted(((k, s) for s, k in self.rosters[side].items()), key=lambda e: e[1])

    def computer_pick(self, side, level):
        """The computer's pick at its level, with its reason in plain words.
        Rookie: the strongest single card. Starter: also fit (the four jobs, the goals it can build). All-Star: also
        denial (what the other side most needs that is still on the board)."""
        from .levels import effective_card
        cands = self.legal_picks(side)
        if not cands:
            raise DraftError('No legal pick is left.')
        mine = list(self.rosters[side].values())
        theirs = list(self.rosters[3 - side].values())
        need_me = _needs(mine, self.age)
        need_them = _needs(theirs, self.age)
        left = [k for k in CD.CARDS if k not in self.taken]
        best = None
        for key, slot in cands:
            card = effective_card(key, self.age, None, slot)
            v = card_strength(card)
            why = [f'the strongest card left ({v:.1f})'] if level == 'rookie' else []
            if level in ('starter', 'allstar'):
                fit = 0.0
                j = jobs(key, self.age)
                for job, short in need_me.items():
                    if short > 0 and j[_JOB_KEY[job]]:
                        fit += 3.0
                        why.append(f'fills our {job} job')
                kinds = _kinds(card) - set().union(*[_kinds(effective_card(k, self.age)) for k in mine]) if mine else _kinds(card)
                if kinds:
                    fit += 0.5 * len(kinds)
                    why.append('adds ' + ', '.join(sorted(kinds)))
                if card.num != slot:
                    fit -= 0.5
                v += fit
            if level == 'allstar':
                deny = 0.0
                j = jobs(key, self.age)
                for job, short in need_them.items():
                    if short > 0 and j[_JOB_KEY[job]]:
                        others = sum(1 for k in left if k != key and jobs(k, self.age)[_JOB_KEY[job]])
                        deny += 2.0 / (1 + others) * 5
                        why.append(f'denies them a {job} ({others} left after this)')
                v += deny
            k2 = (v, -len(why), key, -slot)
            if best is None or k2 > best[0]:
                best = (k2, key, slot, why)
        _, key, slot, why = best
        c = CD.CARDS[key]
        placed = f'slot {slot}' + (f', playing the {slot}' if c.num != slot else '')
        reason = f'Took {c.role} (tier {c.tier}) for {placed}: ' + ('; '.join(why[:3]) if why else 'the best legal pick') + '.'
        self.pick(side, key, slot, reason)
        return key, slot, reason


_JOB_KEY = {'creator': 'creator', 'shooter': 'shooter', 'anchor': 'anchor', 'stopper': 'stopper'}


def _needs(keys, age='senior'):
    J = [jobs(k, age) for k in keys]
    return dict(creator=1 - sum(j['creator'] for j in J), shooter=2 - sum(j['shooter'] for j in J),
                anchor=1 - sum(j['anchor'] for j in J), stopper=1 - sum(j['stopper'] for j in J))


def _kinds(card):
    """What a card can be the centre of, in the goal library's terms: a three, a post entry, a drive, a screen."""
    out = set()
    if card.bands.get('shot_three') == 'H':
        out.add('a shooter')
    if card.bands.get('shot_post') == 'H':
        out.add('a post scorer')
    if card.bands.get('dribble') == 'H':
        out.add('a creator')
    if card.bands.get('screen') == 'H':
        out.add('a screener')
    return out


def card_strength(card):
    """One card's strength for the draft: its tier, then its marks (▲ +1, ▼ −1 across the ratings), then Quick Step."""
    marks = sum(1 if b == 'H' else -1 if b == 'L' else 0 for b in card.bands.values())
    return 3 * TIER_VALUE[card.tier] + 0.25 * marks + 0.5 * card.qs
