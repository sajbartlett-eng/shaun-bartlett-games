"""Playtest server: endpoints, legality, remote play, the golden game and log replay."""
import json
import urllib.error
import urllib.request

import pytest
from conftest import P

from playmaker_engine import board as B
from playmaker_engine.policies import play, RandomPolicy
from playmaker_engine.scenarios import scenario_state
from playmaker_web.game import action_to_json
from playmaker_web.server import start_background


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


def state(base, g):
    return get(base, f'/api/state?code={g["code"]}&token={g["token"]}')


def test_endpoints(web):
    opts = get(web, '/api/options')
    assert len(opts['scenarios']) == 16 and len(opts['teams']) == 10
    g = post(web, '/api/new', dict(mode='hotseat', scenario=6, seed=3))
    s = state(web, g)
    assert s['clock'] == 6 and s['can_act'] and s['legal'] and s['scenario']['title'] == 'Need a Three'
    legal = get(web, f'/api/legal?code={g["code"]}&token={g["token"]}')
    assert [a['text'] for a in legal] == [a['text'] for a in s['legal']]
    a = next(a for a in legal if a['kind'] == 'hesitate')
    r = post(web, '/api/act', dict(code=g['code'], token=g['token'], action=a))
    assert r['state']['side'] == 'X'
    log = get(web, f'/api/log?code={g["code"]}')
    assert log[0]['type'] == 'setup' and log[1]['type'] == 'action' and log[1]['legal']
    html = urllib.request.urlopen(web + '/').read().decode()
    assert 'Playmaker' in html and 'app.js' in html


def test_illegal_action_refused_with_reason(web):
    g = post(web, '/api/new', dict(mode='hotseat', scenario=6, seed=3))
    bad = dict(kind='move', side='O', piece=0, dest=[8, 10], arrow=-1, target=-1, shot='')   # X1 stands on I10
    r = post(web, '/api/act', dict(code=g['code'], token=g['token'], action=bad), ok=False)
    assert r['status'] == 400 and 'illegal action' in r['error']
    r2 = post(web, '/api/act', dict(code=g['code'], token='nope', action=bad), ok=False)
    assert r2['status'] == 400 and 'token' in r2['error']
    r3 = post(web, '/api/act', dict(code=g['code'], token=g['token'], action={'kind': 'move'}), ok=False)
    assert r3['status'] == 400
    assert state(web, g)['version'] == 0          # nothing changed the state


def test_scripted_game_matches_engine_play(web):
    seed = 21
    acts = []
    res = play(scenario_state(7), RandomPolicy(), RandomPolicy(), seed=seed, check=lambda b, a, s: acts.append(a))
    g = post(web, '/api/new', dict(mode='hotseat', scenario=7, seed=seed))
    for a in acts:
        post(web, '/api/act', dict(code=g['code'], token=g['token'], action=action_to_json(a)))
    s = state(web, g)
    assert s['stage'] == 'over' and s['result']['total'] == res['score'].total
    log = get(web, f'/api/log?code={g["code"]}')
    last = [r for r in log if r['type'] == 'action'][-1]
    assert last['after'] == res['final'].encode()


def test_remote_two_clients_see_the_same_game(web):
    g = post(web, '/api/new', dict(mode='remote', scenario=13, seed=5))
    o = dict(code=g['code'], token=post(web, '/api/join', dict(code=g['code'], seat='O'))['token'])
    x = dict(code=g['code'], token=post(web, '/api/join', dict(code=g['code'], seat='X'))['token'])
    assert post(web, '/api/join', dict(code=g['code'], seat='O'), ok=False)['status'] == 400   # seat taken
    so, sx = state(web, o), state(web, x)
    assert so['can_act'] and not sx['can_act'] and sx['legal'] == []
    a = next(a for a in so['legal'] if a['kind'] == 'hesitate')
    r = post(web, '/api/act', dict(x, action=a), ok=False)                # X can't act on O's turn
    assert r['status'] == 400
    post(web, '/api/act', dict(o, action=a))
    so, sx = state(web, o), state(web, x)
    assert so['version'] == sx['version'] and sx['can_act'] and not so['can_act']
    b = next(a for a in sx['legal'] if a['kind'] == 'move')
    post(web, '/api/act', dict(x, action=b))
    so, sx = state(web, o), state(web, x)
    assert so['version'] == sx['version'] and so['x'] == sx['x']
    # undo needs both players in a remote game
    if sx['can_undo']:
        r1 = post(web, '/api/undo', dict(o))
        assert 'waiting' in r1


def test_golden_game_through_the_api(web):
    # Seed 1: the first roll comes up 3, so the intercept on O1 -> O3 fails for the defence (pass completes).
    g = post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], seed=1))
    tok = dict(code=g['code'], token=g['token'])

    def do(pred):
        s = state(web, g)
        a = next(a for a in s['legal'] if pred(a))
        return post(web, '/api/act', dict(tok, action=a))

    do(lambda a: a['kind'] == 'pass' and a['target'] == 2)
    do(lambda a: a['kind'] == 'move' and a['piece'] == 2 and a['dest'] == [11, 10] and a['arrow'] == 7)
    r = do(lambda a: a['kind'] == 'intercept')
    assert r['rolls'][0]['face'] <= r['rolls'][0]['need'] == 13 and r['rolls'][0]['picked'] == 'success'
    do(lambda a: a['kind'] == 'move' and a['piece'] == 2 and a['dest'] == list(P('N7')))
    do(lambda a: a['kind'] == 'move' and a['piece'] == 0 and a['dest'] == list(P('G10')))
    do(lambda a: a['kind'] == 'move' and a['piece'] == 4 and a['dest'] == list(P('N6')) and a['arrow'] == 0)
    do(lambda a: a['kind'] == 'move' and a['piece'] == 0 and a['dest'] == list(P('H9')) and a['arrow'] == 7)
    s = state(web, g)
    assert (s['tokens']['O'], s['tokens']['X']) == (3, 2) and s['side'] == 'O'
    assert [p['sq'] for p in s['o']] == ['G10', 'C9', 'N7', 'A3', 'Q3'] and s['o'][2]['ball']
    assert [p['sq'] for p in s['x']] == ['H9', 'D8', 'L10', 'G4', 'N6']


def test_log_replays_to_the_same_final_state(web, tmp_path):
    from playmaker_engine.review import replay, read
    g = post(web, '/api/new', dict(mode='hotseat', scenario=1, seed=9, ai=dict(X='greedy')))
    tok = dict(code=g['code'], token=g['token'])
    for _ in range(40):
        s = state(web, g)
        if s['stage'] == 'over':
            break
        if not s['can_act']:
            continue
        a = next((a for a in s['legal'] if a['kind'] == 'pass'), s['legal'][0])
        post(web, '/api/act', dict(tok, action=a))
    log = get(web, f'/api/log?code={g["code"]}')
    path = tmp_path / 'log.jsonl'
    path.write_text('\n'.join(json.dumps(r) for r in log))
    finals = replay(read(str(path)))
    last = [r for r in log if r['type'] == 'action'][-1]
    assert finals[-1][1].encode() == last['after']
    assert any(r['actor'] == 'ai' for r in log if r['type'] == 'action')     # the test opponent played


def test_full_game_two_possessions_and_feedback(web):
    g = post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], full=True, seed=4,
                                   ai=dict(O='greedy', X='greedy')))
    tok = dict(code=g['code'], token=g['token'])
    s = state(web, g)
    assert s['stage'] == 'over' and s['possession'] == 1
    post(web, '/api/next', tok)
    s = state(web, g)
    assert s['possession'] == 2 and s['stage'] == 'over' and s['teams'] == ['High-Low', 'Five Out']
    assert s['match'] and s['match']['winner'] in ('A', 'B', 'tie') and len(s['scores']) == 2
    post(web, '/api/feedback', dict(tok, answers={'0': 'yes', '4': 'arrows'}))
    log = get(web, f'/api/log?code={g["code"]}')
    fb = [r for r in log if r['type'] == 'feedback'][0]
    assert fb['answers'][0]['answer'] == 'yes' and len(fb['answers']) == 5


# ---- step 3b ------------------------------------------------------------------------------------

def test_contest_decision_through_the_api(web):
    g = post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], seed=2))
    tok = dict(code=g['code'], token=g['token'])
    s = state(web, g)
    # O1 to I9 (long two, X1 adjacent with its arrow off the shooter) then declare the shot
    mv = next(a for a in s['legal'] if a['kind'] == 'move' and a['piece'] == 0 and a['dest'] == list(P('J10')))
    post(web, '/api/act', dict(tok, action=mv))
    s = state(web, g)
    shot = next(a for a in s['legal'] if a['kind'] == 'shot')
    post(web, '/api/act', dict(tok, action=shot))
    post(web, '/api/act', dict(tok, action=next(a for a in state(web, g)['legal'] if a['kind'] == 'end_turn')))
    s = state(web, g)
    assert s['stage'] == 'contest' and s['side'] == 'X'
    opts = s['legal']
    assert {a['kind'] for a in opts} == {'contest'} and any(a['piece'] == -1 for a in opts)
    adj = [a for a in opts if a['piece'] >= 0]
    assert adj and all(('clean' in a['option']) == a['clean'] for a in adj)
    assert all('foul on' in a['option'] for a in adj if not a['clean'])
    r = post(web, '/api/act', dict(tok, action=next(a for a in opts if a['piece'] == -1)))
    assert r['state']['stage'] == 'over' and r['state']['result']['detail'].endswith('contested by nobody')


def test_every_roll_names_the_side_rolling(web):
    rolls, games = [], 0
    for seed in range(200):                      # scripted random games until three of them have rolled
        acts = []
        res = play(scenario_state(15), RandomPolicy(), RandomPolicy(), seed=seed, check=lambda b, a, s: acts.append(a))
        if not any(e[3] for e in res['log']):
            continue
        g = post(web, '/api/new', dict(mode='hotseat', scenario=15, seed=seed))
        for a in acts:
            post(web, '/api/act', dict(code=g['code'], token=g['token'], action=action_to_json(a)))
        rolls += [r for r in get(web, f'/api/log?code={g["code"]}') if r['type'] == 'roll']
        games += 1
        if games == 3:
            break
    assert len(rolls) >= 3
    for r in rolls:
        assert r['roller'] in ('O', 'X')
        assert r['text'].startswith('Offence rolls' if r['roller'] == 'O' else 'Defence rolls')
        if 'foul' in r['what'].lower():
            assert r['roller'] == 'X'


def test_feedback_only_at_the_end_of_the_match(web):
    g = post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], full=True, seed=4,
                                   place=False, ai=dict(O='greedy', X='greedy')))
    tok = dict(code=g['code'], token=g['token'])
    s = state(web, g)
    assert s['stage'] == 'over' and s['possession'] == 1 and not s['feedback_due']
    assert post(web, '/api/feedback', dict(tok, answers={'0': 'x'}), ok=False)['status'] == 400
    post(web, '/api/next', tok)
    assert state(web, g)['feedback_due']
    g2 = post(web, '/api/new', dict(mode='hotseat', scenario=6, seed=1, ai=dict(O='greedy', X='greedy')))
    assert state(web, g2)['feedback_due']                   # a scenario ends: the form is due


def test_placement_rules_and_preview_shortcut(web):
    g = post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], full=True, seed=6))
    tok = dict(code=g['code'], token=g['token'])
    s = state(web, g)
    assert s['placing']['side'] == 'O' and 'I11' in s['placing']['ball_squares'] and 'I9' not in s['placing']['ball_squares']
    bad = [
        dict(squares=['I11', 'C9', 'O9', 'A3'], ball=0),                       # four pieces
        dict(squares=['I11', 'I11', 'O9', 'A3', 'Q3'], ball=0),                # shared square
        dict(squares=['I9', 'C9', 'O9', 'A3', 'Q3'], ball=0),                  # ball not on plain wood
        dict(squares=['I11', 'C9', 'O9', 'A3', 'R3'], ball=0),                 # off the court
    ]
    for b in bad:
        r = post(web, '/api/place', dict(tok, **b), ok=False)
        assert r['status'] == 400
    assert 'plain wood' in post(web, '/api/place', dict(tok, **bad[2]), ok=False)['error']
    post(web, '/api/place', dict(tok, squares=['I12', 'C9', 'O9', 'A3', 'Q3'], ball=0))
    s = state(web, g)
    assert s['placing']['side'] == 'X'
    r = post(web, '/api/place', dict(tok, squares=['I12', 'D8', 'N8', 'G4', 'N4'], arrows=['N'] * 5), ok=False)
    assert r['status'] == 400 and 'empty' in r['error']
    post(web, '/api/place', dict(tok, squares=['I11', 'D8', 'N8', 'G4', 'N4'], arrows=['S', 'NE', 'NW', 'N', 'N']))
    s = state(web, g)
    assert s['placing'] is None and s['o'][0]['sq'] == 'I12' and s['x'][0]['sq'] == 'I11' and s['can_act']
    # the shortcut gives exactly the preview table setup
    g3 = post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], full=True, seed=6))
    post(web, '/api/place', dict(code=g3['code'], token=g3['token'], preview=True))
    g4 = post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], seed=6))
    a3 = [r for r in get(web, f'/api/log?code={g3["code"]}') if r['type'] == 'placement'][-1]['start']
    a4 = get(web, f'/api/log?code={g4["code"]}')[0]['start']
    assert a3 == a4


def test_computer_places_man_to_man(web):
    g = post(web, '/api/new', dict(mode='hotseat', teams=['Five Out', 'High-Low'], full=True, seed=8, ai=dict(X='greedy')))
    tok = dict(code=g['code'], token=g['token'])
    post(web, '/api/place', dict(tok, squares=['I12', 'C9', 'O9', 'A3', 'Q3'], ball=0))
    s = state(web, g)
    assert s['placing'] is None
    for o, x in zip(s['o'], s['x']):
        assert max(abs(o['x'] - x['x']), abs(o['y'] - x['y'])) == 1       # next to its man
        d = (o['x'] - x['x'], o['y'] - x['y'])
        assert B.DIRS[x['arrow']] == d                                       # arrow on its man
