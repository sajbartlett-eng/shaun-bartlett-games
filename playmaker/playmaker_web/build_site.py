"""Build the no-install versions:
  site/                    index.html + app.js + style.css + pyodide-adapter.js + engine_bundle.json
  dist/playmaker.html      one self-contained file (only Pyodide comes from the CDN)
Run:  python -m playmaker_web.build_site
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, 'playmaker_web', 'static')
ENGINE_FILES = ['__init__.py', 'rules_config.py', 'board.py', 'cards.py', 'state.py', 'actions.py', 'resolve.py',
                'scoring.py', 'scenarios.py', 'policies.py', 'review.py', 'scouting.py', 'scout_phrases.json', 'timer.py',
                'defence.py', 'solver.py', 'solver_config.py',
                'computer_levels.json', 'geometry.py', 'goal_library.json',
                'levels.py', 'rosters.py',
                'decide.py', 'reach.py', 'search.py', 'goals.py', 'agent.py', 'labels.py', 'trainer.py', 'glicko2.py', 'jsbridge.py', 'plain.py', 'register.py']
DATA_FILES = ['data.py', 'teams.py', 'scenarios.py', 'court_zones.json', 'levels_data.py', 'teamtools.py',
              'ai_profiles.json', 'vcoarse.json']
WEB_FILES = ['__init__.py', 'game.py', 'view.py', 'api.py']


def bundle():
    files = {}
    for f in ENGINE_FILES:
        files[f'playmaker_engine/{f}'] = open(os.path.join(ROOT, 'playmaker_engine', f)).read()
    for f in DATA_FILES + ['learned_weights.json']:        # step 17: the learned weights, when the file exists
        if os.path.exists(os.path.join(ROOT, 'playmaker_engine', 'data', f)):
            files[f'playmaker_engine/data/{f}'] = open(os.path.join(ROOT, 'playmaker_engine', 'data', f)).read()
    for f in WEB_FILES:
        files[f'playmaker_web/{f}'] = open(os.path.join(ROOT, 'playmaker_web', f)).read()
    files['playtest_logs/README.txt'] = 'Logs of games played in this browser tab.\n'
    # step 3n: the search core in JavaScript, run in the same worker (agent.JS['search'])
    engine_js = open(os.path.join(STATIC, 'engine.js')).read()
    return dict(version=1, files=files, engine_js=engine_js)


JS_FILES = ['speedtest.js', 'notation.js', 'coach.js', 'records.js', 'trainer.js', 'app.js']       # in load order; index.html names them in this order


def speedtest_positions():
    """Step 13C: what the hidden speed test (?speedtest=1, speedtest.js) runs: the exam's 22 decisions (boards 1 to 16,
    every copy, and C2) as the search reads them, and each level's profile, taken from the engine at build time. short:
    the 8 decisions of boards 2, 7, 9, 10 and 16, used when a device is too slow for all 22. Made in a process of its
    own, so the build loads no engine module the game itself doesn't."""
    import subprocess
    import sys
    out = subprocess.run([sys.executable, '-c', _SPEEDTEST], cwd=ROOT, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


_SPEEDTEST = '''
import json
from playmaker_engine import agent as AG, exam as EX, jsbridge
from playmaker_engine.search import actor
contexts, seen, positions = [], {}, []
jobs = [(n, EX.POSITIONS[n - 1]()[1]) for n in range(1, 17)] + [('C2', EX.c2()[1])]
for n, b in jobs:
    for k, s in (b.items() if isinstance(b, dict) else [('', b)]):
        ctx = json.dumps(jsbridge.ctx_json(s.ctx), sort_keys=True)
        if ctx not in seen:
            seen[ctx] = len(contexts)
            contexts.append(json.loads(ctx))
        positions.append(dict(name=str(n) + ((' ' + str(k)) if k else ''), short=n in (2, 7, 9, 10, 16),
                              state=jsbridge.state_json(s), ctx=seen[ctx]))
first = jobs[0][1]
first = list(first.values())[0] if isinstance(first, dict) else first
profiles = {lv: AG.Agent(actor(first), lv, seed=1).p for lv in ('rookie', 'starter', 'allstar')}
print(json.dumps(dict(profiles=profiles, contexts=contexts, positions=positions)))
'''


def page(inline=False):
    html = open(os.path.join(STATIC, 'index.html')).read()
    adapter = open(os.path.join(STATIC, 'pyodide-adapter.js')).read()
    css = open(os.path.join(STATIC, 'style.css')).read()
    tags = ''.join(f'<script src="{f}"></script>\n' for f in JS_FILES)
    if not inline:
        return html.replace(tags, '<script src="pyodide-adapter.js"></script>\n' + tags)
    data = json.dumps(dict(bundle(), speedtest=speedtest_positions())).replace('</', '<\\/')
    html = html.replace('<link rel="stylesheet" href="style.css">', f'<style>\n{css}\n</style>')
    scripts = ''.join(f'<script>\n{open(os.path.join(STATIC, f)).read()}\n</script>\n' for f in JS_FILES)
    return html.replace(tags, f'<script>window.PM_BUNDLE = {data};</script>\n<script>\n{adapter}\n</script>\n{scripts}')


def build(out_site=None, out_dist=None):
    out_site = out_site or os.path.join(ROOT, 'site')
    out_dist = out_dist or os.path.join(ROOT, 'dist')
    os.makedirs(out_site, exist_ok=True)
    os.makedirs(out_dist, exist_ok=True)
    with open(os.path.join(out_site, 'index.html'), 'w') as f:
        f.write(page())
    for name in JS_FILES + ['style.css', 'pyodide-adapter.js']:
        with open(os.path.join(STATIC, name)) as src, open(os.path.join(out_site, name), 'w') as dst:
            dst.write(src.read())
    os.makedirs(os.path.join(out_site, 'docs'), exist_ok=True)          # step 3l: the playing levels sheet
    for name in os.listdir(os.path.join(STATIC, 'docs')):
        with open(os.path.join(STATIC, 'docs', name), 'rb') as src, open(os.path.join(out_site, 'docs', name), 'wb') as dst:
            dst.write(src.read())
    with open(os.path.join(out_site, 'engine_bundle.json'), 'w') as f:
        json.dump(bundle(), f)
    with open(os.path.join(out_site, 'speedtest_positions.json'), 'w') as f:      # step 13C: the speed test's decisions
        json.dump(speedtest_positions(), f)
    with open(os.path.join(out_dist, 'playmaker.html'), 'w') as f:
        f.write(page(inline=True))
    return out_site, out_dist


if __name__ == '__main__':
    print('built', *build())
