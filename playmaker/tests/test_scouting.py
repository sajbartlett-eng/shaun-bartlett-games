"""Step 3c: scouting, card comparison and the review. The screen may arrange information, never judge it."""
import json
import re
import urllib.request

import pytest
from conftest import P

from playmaker_engine.cards import TEAMS
from playmaker_engine.scouting import report, report_text, BANNED, hunt_protect, best_edge
from playmaker_web.server import start_background

from playmaker_engine.cards import PRESCRIBED

TEAM_NAMES = list(PRESCRIBED)


@pytest.fixture(scope='module')
def web():
    srv, base = start_background()
    yield base
    srv.shutdown()


def post(base, path, body, ok=True):
    req = urllib.request.Request(base + path, json.dumps(body).encode(), {'Content-Type': 'application/json'})
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        if ok:
            raise AssertionError(e.read().decode())
        return dict(status=e.code, **json.loads(e.read()))


def get(base, path):
    return json.loads(urllib.request.urlopen(base + path).read())


# ---- the report (step 3d): words only, nothing average, a pure function of five cards -------------

import random

from playmaker_engine import scouting as S
from playmaker_engine.cards import CARDS

# step 18l: re-recorded from the cards, reason: D-184 cards (the jump-shot ratings and their bands moved, so fewer
# teams hold two above-average three-point shooters and no team holds three below-average three-point contesters)
GOLD = {
    'Pace and Space': (['fast and athletic'], ['limited half-court offence', 'foul-prone']),
    'Iron Wall': (['disruptive in the passing lanes'], ['no spacing', 'limited half-court offence']),
    'Twin Towers': (['multiple creators', 'attacks the rim', 'inside-out'], ['no spacing', 'leaks dribble penetration']),
    'Run and Gun': (['fast and athletic', 'multiple creators', 'attacks the rim', 'disruptive in the passing lanes'], ['no spacing']),
    'Ball Movement': (['fast and athletic', 'moves the ball', 'inside-out'], ['leaks dribble penetration']),
    'Shoot and Protect': (['shooters to space the floor'], ['leaks dribble penetration']),
    'Bucket Brigade': (['multiple creators', 'attacks the rim', 'inside-out'], ['leaks dribble penetration']),
    'Five Out': (['fast and athletic'], ['limited half-court offence']),
    'High-Low': (['inside-out'], ['no spacing', 'limited half-court offence', 'leaks dribble penetration', 'foul-prone']),
    'Lockdown': (['protects the paint', 'disruptive in the passing lanes'], ['no spacing', 'limited half-court offence']),
}
BAND_WORDS = ['above average', 'below average', 'poor', 'okay', 'great', 'excellent']


def _pairs():
    return [(a, b) for a in TEAM_NAMES for b in TEAM_NAMES if a != b]


def _clean(line):
    """Strip the allowed numbers (player numbers 1-5 at the start of a name line, and O1..X5 labels)."""
    line = re.sub(r'^[1-5] ', '', line)
    return re.sub(r'\b[OX][1-5]\b', '', line)


@pytest.mark.parametrize('level', ['learn', 'scout'])
def test_report_has_no_numbers_marks_or_band_names(level):
    for a, b in _pairs():
        for line in report_text(report(a, b, level, full=True)):
            c = _clean(line)
            assert not re.search(r'\d', c), line
            assert '▲' not in c and '▼' not in c, line
            low = c.lower()
            assert not any(re.search(r'\b' + w + r'\b', low) for w in BAND_WORDS), line


@pytest.mark.parametrize('level', ['learn', 'scout'])
def test_report_never_instructs(level):
    for a, b in _pairs():
        for line in report_text(report(a, b, level, full=True)):
            low = line.lower()
            for ok in S.ALLOWED:
                low = low.replace(ok, '')
            for w in S.BANNED:
                assert not re.search(r'\b' + re.escape(w) + r'\b', low), (w, line)
    assert 'attacks the rim' in S.ALLOWED and 'attack' in S.BANNED


def _check_phrase_traces(card, ph, side, kind):
    want = 'H' if kind == 'strength' else 'L'
    spec = S.PHRASES[ph['id']][kind]
    assert spec['text'] == ph['text']
    assert ph['ratings'] and all(S.band(card, r) == want for r in ph['ratings']), (card.key, ph)
    assert all(r in spec['any'] for r in ph['ratings'])


def _every_lineup_report(cards):
    return S.team_report('Lineup', cards)


def test_average_stays_out_and_every_phrase_traces_to_the_card():
    for name in TEAM_NAMES:
        for p, card in zip(S.team_report(name, TEAMS[name])['players'], TEAMS[name]):
            for side in ('off', 'def'):
                for kind, key in (('strength', 'strengths'), ('weakness', 'weaknesses')):
                    for ph in p[side][key]:
                        _check_phrase_traces(card, ph, side, kind)


def test_caps_and_order():
    for card in CARDS.values():
        pl = S.player_lists(card, 1)
        for side in ('off', 'def'):
            for kind, key in (('strength', 'strengths'), ('weakness', 'weaknesses')):
                shown = pl[side][key]
                assert len(shown) <= 3
                full = S.ordered(card, side, kind)
                assert [x['id'] for x in shown] == [x['id'] for x in full[:3]]
                keys = [(x['typical'], x['id'] != 'quick_step', -x['dist']) for x in full]
                assert keys == sorted(keys), (card.key, side, kind)


def test_typical_phrases_are_computed_from_the_cards():
    assert set(S.typical_text('PG')) == {'foul-prone', 'soft screens', 'no resistance at the rim', 'creates off the dribble'}
    assert set(S.typical_text('SG')) == {'limited passer', 'soft screens'}
    # step 18l: re-recorded, reason: D-184 cards
    assert set(S.typical_text('PF')) == {'limited passer', 'slow-footed', 'no threat from three', 'closes out on shooters'}
    assert S.typical_text('SF') == ['closes out on shooters']
    assert len(S.typical_text('C')) >= 6


def test_golden_reads():
    for name, (st, wk) in GOLD.items():
        read = S.team_read(TEAMS[name])
        assert (read['strengths'], read['weaknesses']) == (st, wk), name


def test_calibration_no_team_line_on_more_than_five_teams():
    from collections import Counter
    c = Counter()
    for name in TEAM_NAMES:
        c.update(l['id'] for l in S.team_lines(TEAMS[name]))
    assert max(c.values()) <= S.CONFIG['calibration_max_teams'], c
    assert c['leaks'] == 5


def _random_lineup(rng, legal):
    by = {p: [c for c in CARDS.values() if S.position(c) == p] for p in S.POSITIONS}
    while True:
        cards = [rng.choice(by[p]) for p in S.POSITIONS]
        shape = ''.join(sorted(c.tier for c in cards))
        if (shape in ('BBBBB', 'ABBBC', 'AABCC')) == legal:
            return cards


def _line_holds(cards, line):
    cfg = next(l for l in S.TEAM_LINES if l['id'] == line['id'])
    terms = cfg.get('all') or cfg.get('any')
    res = []
    for t, n in zip(terms, line['counts']):
        assert n == sum(S._passes(c, t) for c in cards)
        res.append({'>=': n >= t['n'], '<=': n <= t['n'], '==': n == t['n']}[t['op']])
    return all(res) if 'all' in cfg else any(res)


def test_custom_lineups_200_legal_and_50_experimental():
    rng = random.Random(7)
    for legal, n in ((True, 200), (False, 50)):
        for _ in range(n):
            cards = _random_lineup(rng, legal)
            t = S.team_report('Custom', cards)
            for line in t['lines']:
                assert _line_holds(cards, line), line
            for line in [t['name']] + t['strengths'] + t['weaknesses']:
                assert not S.banned_hits(line)
            for p, card in zip(t['players'], cards):
                for side in ('off', 'def'):
                    assert len(p[side]['strengths']) <= 3 and len(p[side]['weaknesses']) <= 3
                    for ph in p[side]['strengths']:
                        _check_phrase_traces(card, ph, side, 'strength')
                    for ph in p[side]['weaknesses']:
                        _check_phrase_traces(card, ph, side, 'weakness')


def test_shot_charts_match_the_card_marks():
    for card in CARDS.values():
        ch = S.shot_chart(card)
        for side, prefix in (('off', 'shot_'), ('def', 'con_')):
            for z, shots in (('K', ['layup', 'dunk']), ('M', ['mid']), ('L', ['long']), ('3', ['three'])):
                bands = [card.bands[prefix + t] for t in shots]
                want = 'H' if 'H' in bands else 'L' if 'L' in bands else 'A'
                assert ch[side]['marks'][z] == want
            alt = ch[side]['alt']
            assert alt and 'Strong (solid)' in alt and 'Weak (hatched)' in alt
            for z, (word, _) in S.CHART_ZONES.items():
                if ch[side]['marks'][z] == 'H':
                    assert word in alt.split('Weak')[0]
                if ch[side]['marks'][z] == 'L':
                    assert word in alt.split('Weak')[1]


def test_levels_show_and_hide_exactly():
    learn, scout, pro = (report('Five Out', 'High-Low', lv) for lv in ('learn', 'scout', 'pro'))
    assert learn['mismatches'] and 'mismatches' not in scout and scout['teams']
    assert pro['teams'] == []
    m = learn['mismatches'][0]
    assert m['attacking'] == 'Five Out' and all(re.match(r'^O[1-5] .*; X[1-5] ', x) for x in m['offence'])
    assert all(re.match(r'^X[1-5] .*; O[1-5] ', x) for x in m['defence'])
    assert len(report('Five Out', 'High-Low', 'learn', full=True)['mismatches']) == 2


def test_learn_mismatch_pairs_come_from_the_config():
    for a, b in _pairs():
        offs, defs = S.mismatches(TEAMS[a], TEAMS[b])
        for line in offs + defs:
            i = int(line[1]) - 1
            assert line.count(f'{i + 1}') >= 2           # the same numbered pairing on both sides


def test_team_sheet_hunt_protect():
    a, d = TEAMS['Five Out'], TEAMS['High-Low']
    hp = hunt_protect(a, d)
    edges = [best_edge(a[i], d[i])[0] for i in range(5)]
    assert hp['hunt']['o'] == edges.index(max(edges)) + 1 == hp['protect']['x']


def test_team_sheet_file_is_current():
    import os
    path = os.path.join(os.path.dirname(__file__), '..', 'docs', 'TEAM_SHEET_HUNT_PROTECT.md')
    assert open(path).read() == S.team_sheet_markdown()


# ---- the rule audit: no judgement anywhere during play ------------------------------------------------

BANNED_KEYS = {'value_now', 'ev', 'solver', 'recommend', 'recommended', 'best', 'rank', 'ranking', 'estimate',
               'score_if', 'heat', 'open_man'}


def _walk(obj, path=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield path + '.' + k, k, v
            yield from _walk(v, path + '.' + k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f'{path}[{i}]')


def test_rule_audit_no_judgement_in_play_payloads(web):
    from playmaker_engine.policies import play, RandomPolicy
    from playmaker_engine.scenarios import scenario_state
    from playmaker_web.game import action_to_json
    acts = []
    play(scenario_state(7), RandomPolicy(), RandomPolicy(), seed=5, check=lambda b, a, s: acts.append(a))
    g = post(web, '/api/new', dict(mode='hotseat', scenario=7, seed=5, level='learn'))
    payloads = []
    for a in acts:
        payloads.append(get(web, f'/api/state?code={g["code"]}&token={g["token"]}'))
        payloads.append(get(web, f'/api/legal?code={g["code"]}&token={g["token"]}'))
        r = post(web, '/api/act', dict(code=g['code'], token=g['token'], action=action_to_json(a)))
        payloads.append(r)
    for pl in payloads:
        for path, k, v in _walk(pl):
            assert k not in BANNED_KEYS, path
            if isinstance(v, str) and not path.startswith('.feed') and '.result' not in path and '.scores' not in path:
                # before a commit no text does the sum for the player (sums appear only in results)
                assert not re.search(r'\d+ × \(\d+ − \d+\) = ', v), (path, v)
                assert 'mistake' not in v.lower()


# ---- neutrality ------------------------------------------------------------------------------------

def test_both_players_get_identical_scouting_and_cards(web):
    g = post(web, '/api/new', dict(mode='remote', scenario=13, seed=2, level='scout'))
    o = post(web, '/api/join', dict(code=g['code'], seat='O'))['token']
    x = post(web, '/api/join', dict(code=g['code'], seat='X'))['token']
    so = get(web, f'/api/state?code={g["code"]}&token={o}')
    sx = get(web, f'/api/state?code={g["code"]}&token={x}')
    assert so['scout']['report'] is None and sx['scout']['report'] is None      # read the cards first
    assert so['matchups'] == sx['matchups']
    assert [p['card'] for p in so['o']] == [p['card'] for p in sx['o']] and [p['card'] for p in so['x']] == [p['card'] for p in sx['x']]
    # picks are private until the review
    post(web, '/api/scout', dict(code=g['code'], token=o, hunt=dict(o=3, x=3)))
    sx = get(web, f'/api/state?code={g["code"]}&token={x}')
    assert sx['scout']['done'] == ['O'] and 'hunt' not in json.dumps(sx['scout']['done'])
    assert '"o": 3, "x": 3' not in json.dumps(sx) and "'o': 3" not in json.dumps(sx)
    assert post(web, '/api/act', dict(code=g['code'], token=o, action={'kind': 'hesitate', 'side': 'O'}), ok=False)['status'] == 400
    so = get(web, f'/api/state?code={g["code"]}&token={o}')
    assert so['scout']['report'] and so['scout']['locked'] and so['scout']['mine'] == dict(hunt=dict(o=3, x=3))
    assert sx['scout']['report'] is None                                         # X has not picked yet
    assert post(web, '/api/scout', dict(code=g['code'], token=o, hunt=dict(o=1, x=1)), ok=False)['status'] == 400
    post(web, '/api/scout', dict(code=g['code'], token=x, protect=dict(x=2)))
    so = get(web, f'/api/state?code={g["code"]}&token={o}')
    sx = get(web, f'/api/state?code={g["code"]}&token={x}')
    assert so['can_act'] and so['scout']['report'] == sx['scout']['report']    # identical report for both
    assert sx['scout']['mine'] == dict(protect=dict(x=2)) and '"x": 3' not in json.dumps(sx['scout'])


def test_detail_levels_gate_the_picks(web):
    for level, needs in (('learn', []), ('scout', ['hunt']), ('pro', [])):
        g = post(web, '/api/new', dict(mode='hotseat', scenario=13, seed=2, level=level))
        s = get(web, f'/api/state?code={g["code"]}&token={g["token"]}')
        assert s['level'] == level and s['scout']['needs']['O'] == needs
        assert s['can_act'] == (not needs)
        rep = s['scout']['report']
        assert (rep is not None) == (level == 'learn')         # scout: hidden until the picks lock; pro: none
        if rep:
            assert 'mismatches' in rep


def test_matched_value_chips_during_a_pass(web):
    g = post(web, '/api/new', dict(mode='hotseat', scenario=3, seed=3, level='pro'))   # card 3: X1 stands on the swing lane
    s = get(web, f'/api/state?code={g["code"]}&token={g["token"]}')
    a = next(a for a in s['legal'] if a['kind'] == 'pass' and a['chips'])      # a pass some defender can answer
    assert re.match(r'Pass \d+[▲▼]? v Intercept \d+[▲▼]? \(X\d\)', a['chips'][0])
    assert all('%' not in c and '=' not in c for c in a['chips'])


# ---- the review --------------------------------------------------------------------------------------

def test_board_advantages_on_the_golden_position():
    """At the golden position the ▲ shots on the board are O4's corner three (no contester) and O2's three
    against X2's contest; the list must say so."""
    from playmaker_engine.review import board_advantages
    from helpers import golden_setup
    from playmaker_engine.actions import Action
    from playmaker_engine.resolve import apply, force
    s0 = golden_setup()
    # a one-action log at the golden position
    rec = [dict(type='setup', scenario=None, teams=['Five Out', 'High-Low'], seed=1, start=s0.encode())]
    a = Action('hesitate', 'O')
    nxt = apply(s0, a)
    rec.append(dict(type='action', actor='human', action=dict(kind='hesitate', side='O', piece=-1, dest=None, arrow=-1,
                                                                target=-1, shot='', text='Hesitate'), after=nxt.encode(), possession=1))
    top = board_advantages(rec)
    o4, o2 = TEAMS['Five Out'][3], TEAMS['Five Out'][1]
    x2 = TEAMS['High-Low'][1]
    # step 18l: re-recorded, reason: D-184 cards. O4's corner three (9) is an average three on the new bands, so it is
    # no longer a marked shot; O2's three against X2's contest is the one on the list
    assert o4.bands['shot_three'] == 'A' and o2.bands['shot_three'] == 'H'
    assert [t['o'] for t in top] == [2]
    assert (top[0]['square'], top[0]['shot'], top[0]['value'], top[0]['contester']) == ('C9', 'three', 3 * (o2.shot('three') - x2.con('three')), 2)
    assert all(not t['used'] for t in top)


def test_review_after_the_game_labels_estimates(web):
    g = post(web, '/api/new', dict(mode='hotseat', scenario=13, seed=4, level='scout', ai=dict(X='greedy')))
    tok = dict(code=g['code'], token=g['token'])
    assert post(web, '/api/review', tok, ok=False)['status'] == 400          # not before the end
    post(web, '/api/scout', dict(tok, side='O', hunt=dict(o=3, x=3)))
    for _ in range(30):
        s = get(web, f'/api/state?code={g["code"]}&token={g["token"]}')
        if s['stage'] == 'over':
            break
        a = next((a for a in s['legal'] if a['kind'] == 'shot'), None) or next(a for a in s['legal'] if a['kind'] in ('contest', 'end_turn', 'hesitate', 'move'))
        post(web, '/api/act', dict(tok, action=a))
    r = post(web, '/api/review', tok)
    assert r['picks']['O']['hunt'] == dict(o=3, x=3) and 'hunt' in r['engine']['O']
    assert r['solver'] is not None and all(x['label'] == 'estimate' for x in r['solver'])
    assert 'mistake' not in json.dumps(r).lower()


NODE_PHONE = r"""
const { chromium } = require('playwright');
const [base] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 412, height: 915 }, isMobile: true, hasTouch: true })).newPage();
  const g = await (await fetch(base + '/api/new', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: 'hotseat', scenario: 6, seed: 3, level: 'pro' }) })).json();
  await page.goto(`${base}/?code=${g.code}&token=${g.token}`); await page.waitForTimeout(900);
  await page.tap('g.piece[aria-label^="O2,"]'); await page.waitForTimeout(400);
  const res = await page.evaluate(() => ({ open: !document.getElementById('compare').classList.contains('hidden'),
    head: document.querySelector('#compare h3').textContent, cards: document.querySelectorAll('#compare .card').length,
    scroll: document.documentElement.scrollWidth, vw: document.documentElement.clientWidth }));
  console.log(JSON.stringify(res));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def test_phone_tap_opens_card_and_matchup(tmp_path):
    import subprocess
    srv, base = start_background()
    try:
        (tmp_path / 'p.js').write_text(NODE_PHONE)
        r = subprocess.run(['node', str(tmp_path / 'p.js'), base], capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr[-500:]
        res = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.shutdown()
    assert res['open'] and res['cards'] == 2 and 'matchup: X2' in res['head'], res
    assert res['scroll'] <= res['vw'], res


# ---- step 3d: custom teams, the report in play, the phone report ----------------------------------

def test_custom_team_game_logs_experimental_and_replays(web):
    from playmaker_engine.review import read, replay
    import os
    custom = [dict(slot=0, name='Lab Five', cards=['apgA', 'shsB', 'scsfB', 'pspfB', 'rpcA']),    # AABBB: experimental
              dict(slot=1, name='Lab Two', cards=['ppgA', 'shsB', 'pfsfC', 'arpfA', 'pscC'])]   # AABCC; shsB on both sides
    g = post(web, '/api/new', dict(mode='hotseat', teams=['x', 'y'], custom=custom, seed=3, level='scout',
                                   ai=dict(O='greedy', X='greedy')))
    s = get(web, f'/api/state?code={g["code"]}&token={g["token"]}')
    assert s['teams'] == ['Lab Five', 'Lab Two'] and s['experimental'] == ['Lab Five'] and s['stage'] == 'over'
    rep = s['scout']['report']
    assert [t['name'] for t in rep['teams']] == ['Lab Five', 'Lab Two']
    log = get(web, f'/api/log?code={g["code"]}')
    setup = log[0]
    # step 3m Part 0: the old route goes through the slot-based builder (card n in slot n); an illegal shape plays
    # with the rules off and stays labelled experimental
    assert setup['levels']['roster'] == 'free'
    assert {n: [k for k, _, _ in spec] for n, spec in setup['levels']['lineups'].items()} == \
        {'Lab Five': custom[0]['cards'], 'Lab Two': custom[1]['cards']}
    assert setup['experimental'] == ['Lab Five']
    r = post(web, '/api/review', dict(code=g['code'], token=g['token']))
    assert r['in_play'] and r['engine']['O']['hunt']
    bad = dict(slot=0, name='Bad', cards=['shsB', 'apgA', 'scsfB', 'pspfB', 'nonsense'])          # not a card
    assert post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], custom=[bad]), ok=False)['status'] == 400


def test_the_report_in_play_counts_match_the_log(web):
    g = post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], seed=1, level='scout'))
    tok = dict(code=g['code'], token=g['token'])
    post(web, '/api/scout', dict(tok, side='O', hunt=dict(o=2, x=2)))
    post(web, '/api/scout', dict(tok, side='X', protect=dict(x=2)))
    for _ in range(400):
        s = get(web, f'/api/state?code={g["code"]}&token={g["token"]}')
        if s['stage'] == 'over':
            break
        kinds = ['pass', 'dribble', 'shot', 'intercept', 'contest', 'steal', 'end_turn', 'hesitate', 'move']
        a = next((a for k in kinds for a in s['legal'] if a['kind'] == k), s['legal'][0])
        post(web, '/api/act', dict(tok, action=a))
    r = post(web, '/api/review', tok)
    log = get(web, f'/api/log?code={g["code"]}')
    acts = [x['action'] for x in log if x['type'] == 'action']
    passes = {i: sum(a['kind'] == 'pass' and a['piece'] == i for a in acts) for i in range(5)}
    threes = sum(a['kind'] in ('shot', 'forced_shot') and a['shot'] == 'three' for a in acts)
    five, high = r['in_play']
    assert five['team'] == 'Five Out' and high['team'] == 'High-Low'
    for it in five['items']:
        if it['line'] == 'shooters to space the floor':
            assert it['text'] == ('not tested' if not threes else f'{threes} three{"s" if threes != 1 else ""} taken')
        if it['line'] == 'sees the floor' and it['who'].startswith('O'):
            n = passes[int(it['who'][1]) - 1]
            assert it['text'] == 'not tested' if not n else it['text'].startswith(f'{n} pass')
        assert it['tested'] == (it['text'] != 'not tested')
    # High-Low never had the ball in this single possession: its offence lines were never tested
    assert all(it['text'] == 'not tested' for it in high['items'] if it['who'].startswith('O'))
    assert 'estimate' not in json.dumps(r['in_play']) and 'mistake' not in json.dumps(r).lower()
    assert r['picks']['O'] == dict(hunt=dict(o=2, x=2))


NODE_REPORT = r"""
const { chromium } = require('playwright');
const [base] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 412, height: 915 }, isMobile: true, hasTouch: true })).newPage();
  const g = await (await fetch(base + '/api/new', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mode: 'hotseat', teams: ['Twin Towers', 'Run and Gun'], seed: 3, level: 'scout' }) })).json();
  await page.goto(`${base}/?code=${g.code}&token=${g.token}`); await page.waitForTimeout(900);
  const locked = await page.evaluate(() => document.querySelectorAll('#modal .reads').length);
  for (let i = 0; i < 2; i++) { await page.click('#modal button.primary'); await page.waitForTimeout(500); }
  await page.evaluate(() => { document.getElementById('modalBox').scrollTop = 0; });
  const res = await page.evaluate(() => {
    const reads = [...document.querySelectorAll('#modal .teamread')];
    const bottom = Math.max(...reads.map(r => r.getBoundingClientRect().bottom));
    const text = [...document.querySelectorAll('#modal .reads *, #modal details.sidelist *')].filter(e => !e.children.length).map(e => e.textContent).join(' | ');
    return { locked: 0, n: reads.length, bottom, vh: window.innerHeight, scroll: document.documentElement.scrollWidth,
             vw: document.documentElement.clientWidth, text, charts: [...document.querySelectorAll('#modal svg.chart')].map(s => s.getAttribute('aria-label')) };
  });
  res.locked = locked;
  console.log(JSON.stringify(res));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def test_phone_report_fits_and_has_no_numbers(tmp_path):
    import subprocess
    srv, base = start_background()
    try:
        (tmp_path / 'r.js').write_text(NODE_REPORT)
        r = subprocess.run(['node', str(tmp_path / 'r.js'), base], capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr[-500:]
        res = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.shutdown()
    assert res['locked'] == 0                                # no report before the picks lock
    assert res['n'] == 2 and res['bottom'] <= res['vh'], res  # both teams' reads on the first screen
    assert res['scroll'] <= res['vw'], res
    text = ' | '.join(re.sub(r'^[1-5] ', '', t.strip()) for t in res['text'].split(' | '))
    assert not re.search(r'\d', text) and '▲' not in text and '▼' not in text, text[:300]
    assert res['charts'] and all('Strong (solid)' in c for c in res['charts'])
