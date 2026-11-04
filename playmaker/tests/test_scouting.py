"""Step 3c: scouting, card comparison and the review. The screen may arrange information, never judge it."""
import json
import re
import urllib.request

import pytest
from conftest import P

from playmaker_engine.cards import TEAMS
from playmaker_engine.scouting import report, report_text, BANNED, hunt_protect, best_edge
from playmaker_web.server import start_background

TEAM_NAMES = list(TEAMS)


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


# ---- the report: a pure function of the cards ------------------------------------------------------

@pytest.mark.parametrize('level', ['learn', 'scout'])
def test_report_never_instructs(level):
    for a in TEAM_NAMES:
        for b in TEAM_NAMES:
            if a == b:
                continue
            for line in report_text(report(a, b, level)):
                low = line.lower()
                for w in BANNED:
                    assert not re.search(r'\b' + re.escape(w) + r'\b', low), (w, line)


def test_every_strength_and_liability_matches_the_card_band():
    for name in TEAM_NAMES:
        rep = report(name, TEAM_NAMES[0] if name != TEAM_NAMES[0] else TEAM_NAMES[1])
        team = next(t for t in rep['teams'] if t['name'] == name)
        for p, card in zip(team['players'], TEAMS[name]):
            for side in ('offence', 'defence'):
                for s in p[side]['strengths']:
                    assert card.bands[s['rating']] == 'H' and f"{card.r[s['rating']]}▲" in s['text']
                for s in p[side]['liabilities']:
                    assert card.bands[s['rating']] == 'L' and f"{card.r[s['rating']]}▼" in s['text']


def test_levels_show_and_hide_exactly():
    learn, scout, pro = (report('Five Out', 'High-Low', lv) for lv in ('learn', 'scout', 'pro'))
    assert 'matchups' in learn and 'engine' in learn
    assert 'matchups' not in scout and 'engine' not in scout and scout['teams']
    assert pro['teams'] == [] and 'engine' not in pro


def test_team_sheet_hunt_protect():
    a, d = TEAMS['Five Out'], TEAMS['High-Low']
    hp = hunt_protect(a, d)
    edges = [best_edge(a[i], d[i])[0] for i in range(5)]
    assert hp['hunt']['o'] == edges.index(max(edges)) + 1 == hp['protect']['x']


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
    assert so['scout']['report'] == sx['scout']['report']
    assert so['matchups'] == sx['matchups']
    assert [p['card'] for p in so['o']] == [p['card'] for p in sx['o']] and [p['card'] for p in so['x']] == [p['card'] for p in sx['x']]
    # picks are private until the review
    post(web, '/api/scout', dict(code=g['code'], token=o, hunt=dict(o=3, x=3)))
    sx = get(web, f'/api/state?code={g["code"]}&token={x}')
    assert sx['scout']['done'] == ['O'] and 'hunt' not in json.dumps(sx['scout']['done'])
    assert '"o": 3, "x": 3' not in json.dumps(sx) and "'o': 3" not in json.dumps(sx)
    assert post(web, '/api/act', dict(code=g['code'], token=o, action={'kind': 'hesitate', 'side': 'O'}), ok=False)['status'] == 400
    post(web, '/api/scout', dict(code=g['code'], token=x, protect=dict(x=2)))
    assert get(web, f'/api/state?code={g["code"]}&token={o}')['can_act']


def test_detail_levels_gate_the_picks(web):
    for level, needs in (('learn', []), ('scout', ['hunt']), ('pro', [])):
        g = post(web, '/api/new', dict(mode='hotseat', scenario=13, seed=2, level=level))
        s = get(web, f'/api/state?code={g["code"]}&token={g["token"]}')
        assert s['level'] == level and s['scout']['needs']['O'] == needs
        assert s['can_act'] == (not needs)
        assert ('engine' in s['scout']['report']) == (level == 'learn')


def test_matched_value_chips_during_a_pass(web):
    g = post(web, '/api/new', dict(mode='hotseat', scenario=6, seed=3, level='pro'))
    s = get(web, f'/api/state?code={g["code"]}&token={g["token"]}')
    a = next(a for a in s['legal'] if a['kind'] == 'pass' and a['target'] == 1)
    assert a['chips'] and re.match(r'Pass \d+[▲▼]? v Intercept \d+[▲▼]? \(X\d\)', a['chips'][0])
    assert all('%' not in c and '=' not in c for c in a['chips'])


# ---- the review --------------------------------------------------------------------------------------

def test_board_advantages_on_the_golden_position():
    """At the golden position the ▲ shots on the board are O4's corner three (no contester) and O2's three
    against X2's contest; the list must say so."""
    from playmaker_engine.review import board_advantages
    from playmaker_engine.soak import golden_setup
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
    assert (top[0]['o'], top[0]['square'], top[0]['shot'], top[0]['value']) == (4, 'A3', 'three', 3 * o4.shot('three'))
    assert (top[1]['o'], top[1]['square'], top[1]['value'], top[1]['contester']) == (2, 'C9', 3 * (o2.shot('three') - x2.con('three')), 2)
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
