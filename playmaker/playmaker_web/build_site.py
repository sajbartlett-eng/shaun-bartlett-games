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
                'defence.py', 'solver.py', 'solver_config.py']
DATA_FILES = ['data.py', 'teams.py', 'scenarios.py', 'court_zones.json']
WEB_FILES = ['__init__.py', 'game.py', 'view.py', 'api.py']


def bundle():
    files = {}
    for f in ENGINE_FILES:
        files[f'playmaker_engine/{f}'] = open(os.path.join(ROOT, 'playmaker_engine', f)).read()
    for f in DATA_FILES:
        files[f'playmaker_engine/data/{f}'] = open(os.path.join(ROOT, 'playmaker_engine', 'data', f)).read()
    for f in WEB_FILES:
        files[f'playmaker_web/{f}'] = open(os.path.join(ROOT, 'playmaker_web', f)).read()
    files['playtest_logs/README.txt'] = 'Logs of games played in this browser tab.\n'
    return dict(version=1, files=files)


def page(inline=False):
    html = open(os.path.join(STATIC, 'index.html')).read()
    adapter = open(os.path.join(STATIC, 'pyodide-adapter.js')).read()
    app = open(os.path.join(STATIC, 'app.js')).read()
    css = open(os.path.join(STATIC, 'style.css')).read()
    if not inline:
        return html.replace('<script src="app.js"></script>',
                            '<script src="pyodide-adapter.js"></script>\n<script src="app.js"></script>')
    data = json.dumps(bundle()).replace('</', '<\\/')
    html = html.replace('<link rel="stylesheet" href="style.css">', f'<style>\n{css}\n</style>')
    return html.replace('<script src="app.js"></script>',
                        f'<script>window.PM_BUNDLE = {data};</script>\n<script>\n{adapter}\n</script>\n<script>\n{app}\n</script>')


def build(out_site=None, out_dist=None):
    out_site = out_site or os.path.join(ROOT, 'site')
    out_dist = out_dist or os.path.join(ROOT, 'dist')
    os.makedirs(out_site, exist_ok=True)
    os.makedirs(out_dist, exist_ok=True)
    with open(os.path.join(out_site, 'index.html'), 'w') as f:
        f.write(page())
    for name in ('app.js', 'style.css', 'pyodide-adapter.js'):
        with open(os.path.join(STATIC, name)) as src, open(os.path.join(out_site, name), 'w') as dst:
            dst.write(src.read())
    with open(os.path.join(out_site, 'engine_bundle.json'), 'w') as f:
        json.dump(bundle(), f)
    with open(os.path.join(out_dist, 'playmaker.html'), 'w') as f:
        f.write(page(inline=True))
    return out_site, out_dist


if __name__ == '__main__':
    print('built', *build())
