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
