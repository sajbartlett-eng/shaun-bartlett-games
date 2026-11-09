"""Step 3l: playing levels (Age, Standard) and roster modes. No rule of play changes: only which ratings the cards
carry and how teams are picked. Unit tests and one browser check; no simulations or batch games."""
import ast
import json
import os
import random
import subprocess
from collections import Counter
from fractions import Fraction

import pytest

from playmaker_engine import cards as CD
from playmaker_engine import levels as LV
from playmaker_engine import rosters as RO
from playmaker_engine.cards import CARDS, TEAMS, FIRST_GAME
from playmaker_engine.scenarios import game_state
from playmaker_web.game import Game, GameError, TABLE_O, TABLE_X, TABLE_ARROWS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'playmaker_engine', 'data', 'levels_data.py')
OFF = ['dribble', 'pass', 'screen', 'shot_layup', 'shot_dunk', 'shot_post', 'shot_floater', 'shot_mid', 'shot_long',
       'shot_three', 'free_throw']


# ---- data -------------------------------------------------------------------------------------------------------
def test_levels_data_is_pure_literals():
    tree = ast.parse(open(DATA).read())
    assert not [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    for node in tree.body:
        if isinstance(node, ast.Assign):
            ast.literal_eval(node.value)                    # every value is a plain literal


def test_junior_cards_parse_and_match_the_pro_deck():
    assert len(LV.JUNIOR) == 75 == len(CARDS)
    for k, c in LV.JUNIOR.items():
        p = CARDS[k]
        assert (c.num, c.role, c.tier) == (p.num, p.role, p.tier)
        assert set(c.r) == set(p.r) and set(c.bands) == set(p.bands)


def test_shapes_sum_to_the_standard_strength():
    for std, d in LV.STANDARDS.items():
        for shape in d['shapes']:
            assert len(shape) == 5 and sum(LV.TIER_VALUE[t] for t in shape) == d['strength'], (std, shape)
    assert {s: LV.STANDARDS[s]['strength'] for s in LV.STANDARDS} == {'pro': 0, 'semi_pro': -1, 'amateur': -3}


# ---- youth -----------------------------------------------------------------------------------------------------
def test_youth_is_pro_plus_the_modifier_clamped_with_the_pro_marks():
    for k, p in CARDS.items():
        y = LV.effective_card(k, 'youth')
        assert y.qs == p.qs
        for n, v in p.r.items():
            assert y.r[n] == LV.clamp(n, v + LV.YOUTH_MODIFIER.get(n, 0)), (k, n)
        assert y.bands == p.bands                           # all 75 cards: marks the same as pro
    assert LV.YOUTH_MODIFIER['shot_three'] == -1 and LV.YOUTH_MODIFIER['free_throw'] == -1
    assert LV.YOUTH_MODIFIER['steal'] == 1 and LV.YOUTH_MODIFIER['intercept'] == 1


def test_senior_is_the_pro_card_unchanged():
    for k, p in CARDS.items():
        s = LV.effective_card(k, 'senior')
        assert s.r == p.r and s.qs == p.qs and s.bands == p.bands


# ---- junior (spot-checked against the printed U16 sheet, Playmaker_Cards_U16_Junior.pdf) ---------------------------
U16 = {   # key: (QS, offence in sheet order: dribble pass screen | layup dunk post floater mid long three ft)
    'apgA': (2, [18, 15, 14, 17, 16, 10, 11, 11, 9, 8, 12], 'HAAAHLHAAAA'),
    'apgC': (1, [15, 13, 11, 15, 13, 7, 8, 8, 6, 5, 9], 'ALLLLLALLLL'),
    'shsA': (1, [15, 14, 14, 17, 14, 10, 9, 13, 11, 9, 14], 'AAAAALAHHHH'),
    'shsB': (1, [14, 13, 12, 15, 13, 9, 8, 12, 10, 8, 13], 'ALLLLLAHHAA'),
    'twsfA': (1, [16, 15, 17, 17, 15, 13, 9, 11, 9, 8, None], 'AAHAAAAAAA-'),
    'pspfB': (0, [13, 13, 17, 17, 16, 15, 7, 10, 7, 5, None], 'LLHAHHLAAL-'),
    'pspfC': (0, [12, 13, 16, 15, 14, 13, 6, 8, 5, 4, None], 'LLALAALLLL-'),
    'rpcA': (0, [14, 13, 18, 17, 16, 15, 7, 9, 7, 6, 11], 'ALHAHHLAAAA'),
    'rpcB': (0, [13, 13, 17, 17, 15, 14, 7, 8, 7, 6, 11], 'LLHAAHLLAAA'),
}
SHEET = ['dribble', 'pass', 'screen', 'shot_layup', 'shot_dunk', 'shot_post', 'shot_floater', 'shot_mid', 'shot_long',
         'shot_three', 'free_throw']


def test_junior_is_the_u16_card_and_matches_the_printed_sheet():
    for k in CARDS:
        j = LV.effective_card(k, 'junior')
        assert j.r == LV.JUNIOR[k].r and j.qs == LV.JUNIOR[k].qs and j.bands == LV.JUNIOR[k].bands
    positions = set()
    for k, (qs, vals, marks) in U16.items():
        c = LV.effective_card(k, 'junior')
        positions.add(c.num)
        assert c.qs == qs, k
        for n, v, m in zip(SHEET, vals, marks):
            if v is None:
                continue
            assert c.r[n] == v, (k, n, c.r[n], v)
            assert c.bands[n] == m, (k, n, c.bands[n], m)
    assert positions == {1, 2, 3, 4, 5} and len(U16) >= 6
    back = LV.effective_card('apgA', 'junior')              # a defence side too: agility 8 H, intercept 10 H, steal 6 H
    assert (back.r['agility'], back.r['intercept'], back.r['challenge'], back.r['steal']) == (8, 10, 8, 6)
    assert (back.r['con_layup'], back.r['con_three']) == (7, 4)


def test_card_labels():
    assert LV.card_label(LV.effective_card('apgA', 'junior')) == 'U16 · TIER A'
    assert LV.card_label(LV.effective_card('apgA', 'youth')) == 'U20 · TIER A'
    assert LV.card_label(LV.effective_card('apgA', 'senior')) == 'TIER A'


# ---- growth tags -----------------------------------------------------------------------------------------------
def test_growth_changes_are_exact_and_clamped_with_marks_unchanged():
    assert LV.GROWTH['early'] == {'qs': 1, 'agility': 1, 'challenge': 1, 'screen': 2, 'shot_dunk': 2, 'shot_post': 2,
                                  'con_layup': 2, 'con_dunk': 2, 'con_post': 2}
    assert LV.GROWTH['late'] == {k: -v for k, v in LV.GROWTH['early'].items()}
    for k in CARDS:
        base = LV.effective_card(k, 'junior')
        for tag in ('early', 'late'):
            c = LV.effective_card(k, 'junior', tag)
            assert c.bands == base.bands
            assert c.qs == max(0, min(2, base.qs + LV.GROWTH[tag]['qs']))
            for n, v in base.r.items():
                assert c.r[n] == LV.clamp(n, v + LV.GROWTH[tag].get(n, 0))
    assert LV.effective_card('apgA', 'junior', 'early').qs == 2           # QS 2 stays 2
    assert LV.effective_card('rpcA', 'junior', 'late').qs == 0            # QS 0 stays 0
    assert LV.effective_card('rpcA', 'junior', 'early').r['screen'] == 19  # 18 + 2 clamps to 19
    assert LV.effective_card('apgA', 'senior', 'early').r == CARDS['apgA'].r   # tags only at junior age


def test_growth_deal_is_one_early_three_on_time_one_late():
    # step 6 (D-88): the internal names are early, typical and late; growth is applied in the app's format only
    rng = random.Random(7)
    for _ in range(200):
        assert Counter(LV.deal_growth(rng)) == Counter({'typical': 3, 'early': 1, 'late': 1})
    g = Game(age='junior', level='learn', seed=11, full=True, match_format='digital', per_side=4)
    for t in g.teams:
        assert Counter(g.levels['tags'][t]) == Counter({'typical': 3, 'early': 1, 'late': 1})


def test_growth_tags_hidden_before_setup_revealed_before_the_offence_places():
    from playmaker_web.view import state_json
    # step 6 (D-88): no tag names reach the page; Coach Vision's line names the two players growth changes
    from playmaker_engine.levels import growth_line
    lines = {growth_line('early'), growth_line('late')}
    g = Game(age='junior', level='scout', seed=12, place=True, ai={'B': 'rookie'}, full=True, match_format='digital',
             per_side=4)
    assert not g.tags_revealed() and g.picks_pending() == ['O']
    st = state_json(g, g.tokens['both'])                    # the human is O: sees its own growth, not the computer's
    assert [p['card']['coach_growth'] for p in st['x']] == [None] * 5
    mine = [p['card']['coach_growth'] for p in st['o']]
    assert {t for t in mine if t} == lines and sum(1 for t in mine if t) == 2
    assert set(st['levels']['tags']) == {g.teams[0]}
    assert g.seen_team('X', 'O').endswith('(tags face down)')
    away = TEAMS[g.seen_team('X', 'O')]                     # the computer's own picks read the human's tags face down
    assert all(c.growth is None for c in TEAMS[g.seen_team('O', 'X')])
    assert all(c.growth is None for c in away)
    g.scout(g.tokens['both'], {'side': 'O', 'hunt': {'o': 1, 'x': 1}, 'protect': {'x': 1}})   # a full match: both calls
    assert g.tags_revealed() and g.placing == 'O'           # setup has begun: tags up before the offence places
    st = state_json(g, g.tokens['both'])
    assert {p['card']['coach_growth'] for p in st['x'] if p['card']['coach_growth']} == lines
    kinds = [r['type'] for r in g.read_log()]
    assert 'reveal' in kinds and not any(k == 'place' for k in kinds[:kinds.index('reveal')])


# ---- effective ratings everywhere, on one hand-worked junior position ----------------------------------------------
@pytest.fixture(scope='module')
def junior_game():
    on = ['on_time'] * 5         # step 6 (D-88): the old name still reads as typical; growth only in the app's format
    return Game(age='junior', roster='free', level='learn', seed=1, full=True, match_format='digital', per_side=4,
                lineups=[{'name': 'Hand', 'cards': [['apgA', 1], ['shsA', 2], ['twsfA', 3], ['pspfB', 4], ['rpcA', 5]],
                          'tags': ['early', 'on_time', 'on_time', 'on_time', 'on_time']},
                         {'name': 'Hand D', 'cards': [['apgA', 1], ['shsB', 2], ['twsfA', 3], ['pspfC', 4], ['rpcB', 5]],
                          'tags': on}])


def test_engine_shot_value_and_roll_targets_use_junior_ratings(junior_game):
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    from playmaker_engine.scoring import contest_options, p_success
    off, dfn = junior_game.teams
    s = game_state(off, dfn, TABLE_O, TABLE_X, TABLE_ARROWS, ball=0)
    # O1 apgA (Early): dribble 18 (no growth change). X1 apgA on time: agility 8. Target 18 - 8 = 10.
    dr = next(a for a in legal_actions(s) if a.piece == 0 and a.kind == 'dribble' and a.target == 0)
    node = apply(s, dr)
    assert isinstance(node, ChanceNode)
    assert max(p for p, _, _ in node.outcomes) == max(p_success(10, s.ctx.rules), 1 - p_success(10, s.ctx.rules))
    assert p_success(10, s.ctx.rules) in [p for p, _, _ in node.outcomes]
    # A three by O1 (junior three 8; pro is higher) contested by X1 (junior three contest 4, nearer the rim):
    # 3 x (8 - 4) = 12; open, 3 x 8 = 24. Fouled on a three: 3 x junior FT 12 = 36.
    from playmaker_engine import board as B
    from playmaker_engine import rules_config as RC
    sq3 = next((x, y) for y in range(1, B.H + 1) for x in range(B.W) if B.zone((x, y)) == '3' and y > 3)
    near = min((B.add(sq3, d) for d in B.DIRS), key=lambda q: B.dist_rim(q))
    o_sq = [B.sq(sq3)] + [q for q in TABLE_O[1:] if B.parse_sq(q) not in (sq3, near)]
    x_sq = [B.sq(near)] + [q for q in TABLE_X[1:] if B.parse_sq(q) not in (sq3, near)]
    s3 = game_state(off, dfn, o_sq, x_sq, [B.dir_between(near, sq3)] + TABLE_ARROWS[1:], ball=0, check=False)
    opts = {o.defender: o for o in contest_options(s3, 0, 'three')}
    assert opts[-1].value == 24
    assert opts[0].contest == 4 and opts[0].value == 12
    assert opts[0].ft == RC.FT_MULT_THREE * 12 == 36
    # the pro card differs, so pro ratings leaking in would fail these numbers
    assert CARDS['apgA'].shot('three') != 8 and CARDS['apgA'].r['free_throw'] != 12


def test_scout_report_and_team_sheet_read_junior_cards(junior_game):
    from playmaker_engine.scouting import report, hunt_protect, player_lists
    off, dfn = junior_game.teams
    rep = report(off, dfn, 'learn')
    for i, k in enumerate(['apgA', 'shsA', 'twsfA', 'pspfB', 'rpcA']):
        p = rep['teams'][0]['players'][i]
        want = player_lists(LV.effective_card(k, 'junior', 'early' if i == 0 else None, i + 1), i + 1)
        assert p['num'] == i + 1 and p['off'] == want['off'] and p['def'] == want['def']
    hp = hunt_protect(TEAMS[off], TEAMS[dfn])
    i = hp['hunt']['o'] - 1
    t = hp['hunt']['shot']
    assert f"{t} {TEAMS[off][i].shot(t)}" in hp['hunt']['text']
    assert TEAMS[off][i].shot(t) == LV.JUNIOR[TEAMS[off][i].key].shot(t) + LV.GROWTH['early'].get('shot_' + t, 0) * (i == 0)


# ---- rules on: legality, slots and flex ------------------------------------------------------------------------------
def _roster(shape, flex=None):
    """A roster of the given tier shape, one card per position (PG..C), each in its own slot."""
    out = []
    for pos, t in zip(range(1, 6), shape):
        k = next(k for k, c in CARDS.items() if c.num == pos and c.tier == t)
        out.append((k, pos))
    return out


def test_every_standard_accepts_its_shapes_and_rejects_the_rest():
    import itertools
    all_shapes = {''.join(sorted(p)) for p in itertools.product('ABC', repeat=5)}
    for std, d in LV.STANDARDS.items():
        for shape in all_shapes:
            ok = RO.legal(_roster(shape), std)
            assert ok == (shape in d['shapes']), (std, shape)
            if not ok:
                assert any("isn't" in p and 'shape' in p for p in RO.problems(_roster(shape), std))


def test_flex_rules():
    base = _roster('ABBBC')
    # a centre in slot 4 and the PF in slot 5: two cards out of position, refused
    c, pf = base[4][0], base[3][0]
    two = base[:3] + [(c, 4), (pf, 5)]
    assert 'Only one card may play out of position.' in RO.problems(two, 'pro')
    # beyond one position: a PG in slot 3, a C in slot 3
    pg = base[0][0]
    bad = [(base[2][0], 1), base[1], (pg, 3), base[3], base[4]]
    assert any('not slot 3' in p for p in RO.problems(bad, 'pro'))
    bad = [base[0], base[1], (c, 3), (base[2][0], 4), (base[3][0], 5)]
    assert any('not slot 3' in p for p in RO.problems(bad, 'pro'))
    # one flex: a PF in slot 4's neighbour... the SF plays the 4 and a PF the 3? (two flex) - one swap of neighbours
    # is two cards out of position; a single flex needs a second card of the neighbour position
    sf2 = next(k for k, cc in CARDS.items() if cc.num == 3 and cc.tier == 'B' and k != base[2][0])
    one = [base[0], base[1], base[2], (sf2, 4), base[4]]
    assert RO.problems(one, 'pro') == []
    assert RO.slot_ok('apgA', 2) and not RO.slot_ok('apgA', 3) and RO.slot_ok('rpcA', 4) and not RO.slot_ok('rpcA', 3)


def test_a_centre_in_slot_4_plays_as_o4():
    pro = _roster('AABCC')                                  # A PG, A SG, B SF, C PF, C C
    c2 = next(k for k, cc in CARDS.items() if cc.num == 5 and cc.tier == 'C' and k != pro[4][0])
    home = [pro[0], pro[1], pro[2], (c2, 4), pro[4]]        # a second C-tier centre plays the 4
    assert RO.problems(home, 'pro') == []
    g = Game(roster='build', level='learn', seed=3, lineups=[{'name': 'Bigs', 'cards': home}, {'cards': _roster('BBBBB')}])
    o4 = g.state.ctx.off[3]
    assert o4.key == c2 and o4.slot == 4 and o4.flex and LV.flex_words(o4) == 'playing the 4'
    assert g.state.ctx.dfn[3].slot == 4 and not g.state.ctx.dfn[3].flex
    from playmaker_web.view import state_json
    st = state_json(g, g.tokens['both'])
    assert st['o'][3]['card']['flex'] == 'playing the 4' and st['o'][3]['card']['printed'] == 5


def test_build_refuses_an_illegal_roster_with_plain_reasons():
    with pytest.raises(GameError, match="isn't an amateur shape"):
        Game(roster='build', standard='amateur', lineups=[{'cards': _roster('ABBBC')}, {'cards': _roster('BBCCC')}])
    with pytest.raises(GameError, match='five different cards'):
        Game(roster='build', lineups=[{'cards': [('apgA', s) for s in range(1, 6)]}, {'cards': _roster('BBBBB')}])


def test_handicap_standard_per_side_with_totals():
    g = Game(roster='build', standard={'A': 'amateur', 'B': 'pro'}, level='learn', seed=4,
             lineups=[{'cards': _roster('ACCCC')}, {'cards': _roster('AABCC')}])
    assert g.levels['standard'] == {'A': 'amateur', 'B': 'pro'}
    assert list(g.levels['strength'].values()) == [-3, 0] and g.levels['uneven'] == 'Uneven teams: Away +3'
    with pytest.raises(GameError):
        Game(roster='prescribed', standard={'A': 'amateur', 'B': 'pro'})


# ---- rules off ("Your team") ---------------------------------------------------------------------------------------
def test_rules_off_allows_duplicates_and_any_shape_with_totals_and_notice():
    dup = [('apgA', s) for s in range(1, 6)]               # five copies of one A card, in any slots
    assert RO.problems(dup, rules=False) == []
    g = Game(roster='free', level='learn', seed=5, lineups=[{'name': 'Clones', 'cards': dup}, {'cards': _roster('BBBBC')}])
    assert [c.key for c in g.state.ctx.off] == ['apgA'] * 5
    assert list(g.levels['strength'].values()) == [5, -1]
    assert g.levels['uneven'] == 'Uneven teams: Home +6'


# ---- random deals -------------------------------------------------------------------------------------------------
@pytest.mark.parametrize('std', ['pro', 'semi_pro', 'amateur'])
def test_random_deals_are_legal_and_coherent(std):
    rng = random.Random(f'legal-{std}')
    for coherent in (True, False):
        for _ in range(1000):
            r = RO.deal_one(std, rng, coherent)
            assert RO.legal(r, std), r
            if coherent:
                assert RO.coherent_ok([k for k, _ in r]), r


def test_deal_codes_round_trip_with_tags():
    for age in LV.AGE_ORDER:
        for std in LV.STANDARD_ORDER:
            for coherent in (True, False):
                if (age, std, coherent) == ('junior', 'amateur', True):
                    continue                  # step 3m: one card pool; no such pair exists (tested in test_step3m)
                d = RO.deal(age, std, coherent)
                again = RO.deal(code=d['code'])
                assert again == d
                assert (again['age'], again['standard'], again['coherent']) == (age, std, coherent)
                assert (d['tags'] is not None) == (age == 'junior')
    with pytest.raises(ValueError, match='looks like'):
        RO.read_code('nonsense')
    g1 = Game(roster='random', deal='JMC-002N9C', level='learn', seed=1)
    g2 = Game(roster='random', deal='JMC-002N9C', level='learn', seed=99)
    assert [[(c.key, c.slot, c.growth) for c in TEAMS[t]] for t in g1.teams] == \
           [[(c.key, c.slot, c.growth) for c in TEAMS[t]] for t in g2.teams]


@pytest.mark.parametrize('std', ['pro', 'semi_pro', 'amateur'])
def test_pure_deal_shape_frequencies_match_the_legal_proportions(std):
    want = RO.count_by_shape(std)
    total = sum(want.values())
    rng = random.Random(f'shapes-{std}')
    n = 20000
    got = Counter(RO.shape_of([k for k, _ in RO.deal_one(std, rng, False)]) for _ in range(n))
    for shape, c in want.items():
        assert abs(got[shape] / n - c / total) < 0.02, (std, shape, got[shape] / n, c / total)


def test_legal_roster_counts():
    assert {s: RO.count(s, flex=False) for s in LV.STANDARD_ORDER} == {'pro': 159375, 'semi_pro': 109375, 'amateur': 46875}
    assert {s: RO.count(s, flex=True) for s in LV.STANDARD_ORDER} == {'pro': 1369375, 'semi_pro': 939375, 'amateur': 386875}


def test_random_for_one_side_keeps_the_other_prescribed():
    g = Game(roster='random', deal='SPP-00000B', random_for='opponent', level='learn', seed=1, ai={'B': 'rookie'})
    assert g.teams[0] == FIRST_GAME[0] and g.teams[1].startswith('Away (dealt)')
    assert g.levels['random'] == 'opponent' and g.levels['deal'] == 'SPP-00000B'


# ---- the draft ----------------------------------------------------------------------------------------------------
def test_draft_refuses_an_uncompletable_pick():
    d = RO.Draft('amateur')
    a = next(k for k, c in CARDS.items() if c.num == 1 and c.tier == 'A')
    d.pick(1, a, 1)                                         # Home: an A card (amateur allows ACCCC only with an A)
    for _ in range(2):
        k, s = d.legal_picks(2)[0]
        d.pick(2, k, s)
    b = next(k for k, c in CARDS.items() if c.num == 2 and c.tier == 'B' and k not in d.taken)
    assert d.check(1, b, 2) == 'This pick leaves no legal amateur shape.'
    with pytest.raises(RO.DraftError, match='no legal amateur shape'):
        d.pick(1, b, 2)
    assert d.check(2, b, 2).startswith("It is side 1")


@pytest.mark.parametrize('std', ['pro', 'semi_pro', 'amateur'])
def test_full_computer_draft_gives_two_legal_rosters_with_reasons(std):
    d = RO.Draft(std, 'junior')
    levels = {1: 'rookie', 2: 'allstar'} if std != 'semi_pro' else {1: 'starter', 2: 'starter'}
    while not d.done():
        d.computer_pick(d.turn, levels[d.turn])
    assert [p['side'] for p in d.log] == list(RO.SNAKE)
    for side in (1, 2):
        assert RO.legal(d.roster(side), std), d.roster(side)
    assert all(p['by'] == 'computer' and p['reason'].startswith('Took ') for p in d.log)
    assert not set(dict(d.roster(1))) & set(dict(d.roster(2)))  # one pool: no card twice
    g = Game(roster='draft', draft=d, level='learn', seed=8, full=True, match_format='digital', per_side=4)
    assert g.levels['draft'] == d.log and g.levels['tags']      # junior: tags dealt after the draft (step 6: in the app)
    rec = g.read_log()[0]
    assert rec['levels']['draft'][0]['reason'] == d.log[0]['reason']


def test_draft_api_logs_the_computer_reasons():
    from playmaker_web.api import Manager, handle
    m = Manager()
    st, d = handle(m, 'POST', '/api/draft', body={'new': {'standard': 'pro', 'computer': 'starter', 'human': 1}})
    assert st == 200 and d['turn'] == 1 and d['legal']
    while not d['done']:
        k = d['legal'][0]
        st, d = handle(m, 'POST', '/api/draft', body={'id': d['id'], 'key': k, 'slot': d['slots'][k][0]})
        assert st == 200, d
    assert [p['by'] for p in d['picks']] == ['player' if s == 1 else 'computer' for s in RO.SNAKE]
    assert all(p['reason'] for p in d['picks'] if p['by'] == 'computer')
    st, g = handle(m, 'POST', '/api/new', body={'roster': 'draft', 'draft': d['id'], 'level': 'learn', 'ai': {'B': 'starter'}})
    assert st == 200, g


# ---- interface and regression ---------------------------------------------------------------------------------------
def test_defaults_reproduce_the_game_before_step_3l():
    g = Game(seed=1)
    assert g.levels is None and g.teams == list(FIRST_GAME)
    assert [c is CARDS[c.key] for c in g.state.ctx.off] == [True] * 5
    assert g.state.encode() == game_state(*FIRST_GAME, TABLE_O, TABLE_X, TABLE_ARROWS).encode()
    assert 'levels' in g.read_log()[0] and g.read_log()[0]['levels'] is None
    with pytest.raises(GameError):
        Game(scenario=1, age='junior')


def test_logs_record_the_levels_and_the_review_rebuilds_the_teams():
    from playmaker_engine.review import register_custom, _start
    g = Game(age='junior', roster='random', deal='JAP-000123', level='learn', seed=2, full=True, match_format='digital',
             per_side=4)                                    # step 6 (D-88): growth only in the app's format
    setup = g.read_log()[0]
    lv = setup['levels']
    assert lv['age'] == 'junior' and lv['roster'] == 'random' and lv['deal'] == 'JAP-000123' and lv['standard'] == 'amateur'
    assert set(lv['tags']) == set(g.teams) and set(lv['lineups']) == set(g.teams)
    saved = {t: TEAMS.pop(t) for t in list(g.teams) + [n + ' (tags face down)' for n in g.teams] if t in TEAMS}
    try:
        register_custom(setup)                              # a fresh process: rebuilt from the log alone
        s = _start(setup, 1)
        for i in range(5):
            assert s.ctx.off[i].r == saved[g.teams[0]][i].r and s.ctx.off[i].growth == saved[g.teams[0]][i].growth
    finally:
        TEAMS.update(saved)


def test_api_options_carry_the_levels_sheet_words():
    from playmaker_web.api import Manager, handle
    st, o = handle(Manager(), 'GET', '/api/options')
    L = o['levels']
    assert [a['id'] for a in L['ages']] == ['senior', 'youth', 'junior']
    assert L['ages'][1]['words'].startswith('Elite youth · U18 to U20')
    assert L['standards'][2]['words'].startswith('Amateur: BBCCC · ACCCC')
    assert L['growth_box'].startswith('In the app, growth changes two players')      # step 6 (D-88)
    assert os.path.exists(os.path.join(ROOT, 'playmaker_web', 'static', L['sheet']))


NODE = r"""
const { chromium } = require('playwright');
const [base, out] = process.argv.slice(2);
const post = (p, body) => fetch(base + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(r => r.json());
(async () => {
  const b = await chromium.launch();
  const res = { errors: [] };
  const page = async () => { const p = await (await b.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 2 })).newPage();
    p.on('pageerror', e => res.errors.push(e.message)); return p; };
  const wide = p => p.evaluate(() => document.documentElement.scrollWidth);
  // the new-game screen with the two dials
  let p = await page();
  await p.goto(base + '/'); await p.waitForTimeout(600);
  await p.click('button.path[data-path=computer]'); await p.waitForTimeout(300);
  await p.selectOption('#age', 'junior'); await p.selectOption('#standard', 'semi_pro'); await p.waitForTimeout(200);
  res.ageNote = await p.textContent('#ageNote'); res.standardNote = await p.textContent('#standardNote');
  res.aiLabel = await p.textContent('#aiRow label');
  res.newWide = await wide(p);
  await (await p.$('#setup')).screenshot({ path: out + '/levels_new_game.png' });
  // the draft board
  await p.selectOption('#roster', 'draft'); await p.waitForTimeout(200);
  await p.click('#draftBtn'); await p.waitForTimeout(1200);
  await p.click('.draftpos summary'); await p.waitForTimeout(150);
  res.draftTurn = await p.textContent('.draftturn');
  res.draftWide = await wide(p);
  await p.click('.draftpos li button'); await p.waitForTimeout(1500);
  res.draftAfter = await p.textContent('.draftturn');
  res.draftLog = await p.$$eval('.draftlog li', l => l.map(x => x.textContent));
  await (await p.$('#draftRow')).screenshot({ path: out + '/levels_draft_board.png' });
  // a junior card with an E badge, and a centre playing the 4
  const g = await post('/api/new', { mode: 'hotseat', level: 'learn', age: 'junior', roster: 'free', seed: 5, full: true, match_format: 'digital', per_side: 4, place: false,
    lineups: [{ name: 'Lab', cards: [['apgA', 1], ['shsA', 2], ['twsfA', 3], ['rpcA', 4], ['rpcB', 5]], tags: ['on_time', 'on_time', 'late', 'early', 'on_time'] },
              { name: 'Club', cards: [['apgC', 1], ['shsB', 2], ['twsfB', 3], ['pspfB', 4], ['rpcC', 5]] }] });
  p = await page();
  await p.goto(`${base}/?code=${g.code}&token=${g.token}`); await p.waitForTimeout(1200);
  for (let i = 0; i < 4 && await p.evaluate(() => !document.getElementById('modal').classList.contains('hidden')); i++) { await p.keyboard.press('Escape'); await p.waitForTimeout(300); }
  await p.click('nav.tabs button[data-tab=cards]'); await p.waitForTimeout(300);
  const heads = await p.$$('#offCards .card .head'); await heads[3].click(); await p.waitForTimeout(250);
  res.o4 = await p.evaluate(() => document.querySelectorAll('#offCards .card')[3].textContent);
  res.badges = await p.$$eval('#court .growbadge', x => x.map(e => e.getAttribute('class')));
  res.o4label = await p.getAttribute('#court g.piece[aria-label^="O4"]', 'aria-label');
  res.gameWide = await wide(p);
  await (await p.$$('#offCards .card'))[3].screenshot({ path: out + '/levels_junior_card.png' });
  await p.click('nav.tabs button[data-tab=off]'); await p.waitForTimeout(200);
  await (await p.$('.clipboard')).screenshot({ path: out + '/levels_junior_board.png' });
  console.log(JSON.stringify(res));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def test_browser_new_game_dials_junior_card_flex_and_draft_board(tmp_path):
    from playmaker_web.server import start_background
    srv, base = start_background()
    docs = os.path.join(ROOT, 'docs')
    try:
        (tmp_path / 'levels.js').write_text(NODE)
        r = subprocess.run(['node', str(tmp_path / 'levels.js'), base, docs], capture_output=True, text=True, timeout=240,
                           cwd=str(tmp_path))
        assert r.returncode == 0, r.stderr[-1500:]
        out = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.shutdown()
    assert out['errors'] == []
    assert out['ageNote'].startswith('Junior · U14 to U16') and out['standardNote'].startswith('Semi-pro: BBBBC')
    assert 'how well the computer reads the play' in out['aiLabel']
    assert out['newWide'] == out['draftWide'] == out['gameWide'] == 412          # no horizontal scroll at 412 px
    assert out['draftTurn'].startswith('Pick 1 of 10') and out['draftAfter'].startswith('Pick 4 of 10')
    assert len(out['draftLog']) == 3 and all('Took ' in x for x in out['draftLog'][1:])
    # step 6 (D-88): no tag names or badges; Coach Vision's line under the card
    assert 'U16 · TIER A' in out['o4'] and 'playing the 4' in out['o4'] and 'Bigger and stronger than most players his age.' in out['o4']
    assert 'growth' not in out['o4label'] and 'playing the 4' in out['o4label']
    assert out['badges'] == []
    for f in ('levels_new_game.png', 'levels_draft_board.png', 'levels_junior_card.png', 'levels_junior_board.png'):
        assert os.path.getsize(os.path.join(docs, f)) > 5000
