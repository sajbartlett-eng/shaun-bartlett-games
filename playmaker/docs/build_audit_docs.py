"""Build the three code-audit documents (docs/audit/*.pdf): the game logic, the computer offence and the
computer defence. Every line comes straight from the source, with its real file and line numbers.

computer.py and solver.py hold code for both sides, so they are split function by function: each line
belongs to the shared core (printed in both computer documents), the offence, the defence, or the
solver-search appendix. The build fails if any function of either file is not placed.

Run:  python docs/build_audit_docs.py
"""
import ast
import datetime
import html
import json
import os
import subprocess

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import JsonLexer, PythonLexer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENG = os.path.join(ROOT, 'playmaker_engine')
OUT = os.path.join(ROOT, 'docs', 'audit')

GAME_FILES = [
    ('rules_config.py', 'Every rule setting and constant (clock, tokens, limits, zones, the open-question switches).'),
    ('board.py', 'The court grid: squares, zones, distances, movement shapes, arrow-line geometry.'),
    ('geometry.py', 'Arrow lines and contest position (step 3h settings; defaults reproduce the current rules).'),
    ('cards.py', 'Player cards: ratings and ▲ / ▼ bands, teams.'),
    ('data/data.py', 'Card data: every player card and its ratings.'),
    ('data/teams.py', 'The prescribed teams.'),
    ('data/scenarios.py', 'The 16 scenario cards.'),
    ('data/court_zones.json', 'The zone of every square (rim, three, mid, long two, wood).'),
    ('scenarios.py', 'Starting positions: scenario cards and normal games, setup checks.'),
    ('state.py', 'The game state (an immutable snapshot of a possession).'),
    ('actions.py', 'Legal actions: movement, passes, shots, screens, dribbles, steals, interceptions, the reaction.'),
    ('resolve.py', 'Applying an action: tokens, turns and phases, rolls, locks, passes, contests, turnovers.'),
    ('scoring.py', 'Shot values, contests, fouls and free throws, the score and its bands.'),
    ('timer.py', 'The optional decision timer and its token forfeits.'),
    ('__init__.py', 'Package entry.'),
]

# ---- placing computer.py and solver.py ---------------------------------------------------------------
C_OFF = {'pass_risk', 'pass_outcomes', 'Computer._spot', 'Computer._remember', 'Computer._note_pass',
         'Computer._loop_penalty', 'Computer.targets', 'Computer._ensure_plan', 'Computer._plan_bonus',
         'Computer._attack', 'Computer._filter_plays', 'Computer._play_value', 'Computer._banked',
         'Computer._pick_off_value', 'Computer._pass_play_value', 'Computer._after_value', 'Computer._o_next',
         'Computer._maps', 'Computer._advs', 'Computer._note_handover', 'Computer._prev', 'Computer._exploit',
         'Computer._tempo', 'Computer._adv_value', 'Computer._adv_plays', 'Computer._advantage_attack',
         'Computer._play_words', 'Computer._plan_note', 'Computer._contested', 'Computer._chances',
         'Computer._last_chance', 'Computer._bar', 'Computer._patient', 'Computer._plan_kind',
         'Computer.PASS_KINDS', 'Computer._ALT'}
C_DEF = {'Computer._threat', 'Computer._defend', 'Computer._comfort_key', 'Computer._concept_filter',
         'Computer._habit_rewrite', 'Computer._contest', 'Computer._nearest_reaction', '_next_to', 'place_defence',
         '_assign'}
C_SHARED = {'reaction_budget', 'reachable_contest', '_reachable_contest_geo', '_positions', '_mids', 'SeenCard',
            'seen_context', 'seen_state', '_evaluator_class', 'Computer.__init__', 'Computer._context',
            'Computer.describe', 'Computer._fire', 'Computer.choose', 'Computer._choose', 'Computer._queue',
            'Computer._immediate', 'Computer._node_value', 'Computer._value_fn', 'Computer._rank', 'Computer._pick',
            'Computer._with_end', 'Computer._stop', 'Computer._late', 'Computer._search', 'make'}
S_OFF = {'Generator.offence_plays'}
S_DEF = {'Generator.defence_plays', 'Generator.step_shots', 'Generator.reaction_plays'}
S_SEARCH = {'NodeCap', '_terminal_turn', 'pruned_actions', 'exact_solve', 'Entry', 'Searcher', 'describe_terminal'}
S_SHARED = {'Timeout', 'Val', 'mix', 'terminal_vals', '_with_x', '_paths', 'defender_reach', 'ReachMaps', 'Evaluator',
            'Play', '_contest_arrow', '_seq_actions', 'quick_legal', 'apply_play', 'Generator.__init__',
            'Generator.plays', 'Generator._value_after', 'Generator.raw_plays', 'expected'}
SPLIT_CLASSES = {'Computer', 'Generator'}


def owners(path, buckets):
    """Line number -> bucket for one file. Named nodes go to their bucket; everything else (imports,
    constants, section comments, class headers) is 'shared'. Raises if a named node isn't placed."""
    src = open(path).read()
    lines = src.splitlines()
    tree = ast.parse(src)
    own = {i: 'shared' for i in range(1, len(lines) + 1)}
    placed = set()

    def bucket(name):
        for b, names in buckets.items():
            if name in names:
                placed.add(name)
                return b
        raise SystemExit(f'{os.path.basename(path)}: {name} is not placed in any document')

    def span(n):
        start = min([n.lineno] + [d.lineno for d in getattr(n, 'decorator_list', [])])
        return start, n.end_lineno

    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            if isinstance(n, ast.ClassDef) and n.name in SPLIT_CLASSES:
                for m in n.body:
                    if isinstance(m, ast.FunctionDef):
                        b = bucket(f'{n.name}.{m.name}')
                    elif isinstance(m, ast.Assign) and isinstance(m.targets[0], ast.Name):
                        name = f'{n.name}.{m.targets[0].id}'
                        b = next((k for k, v in buckets.items() if name in v), 'shared')
                    else:
                        continue
                    a, z = span(m)
                    for i in range(a, z + 1):
                        own[i] = b
            else:
                b = bucket(n.name)
                a, z = span(n)
                for i in range(a, z + 1):
                    own[i] = b
    return lines, own


WHERE = {'shared': 'the shared core (Part 1)', 'offence': 'the offence document', 'defence': 'the defence document',
         'search': 'the appendix'}


def labeller(own, here):
    """Say where the lines a part skips are printed."""
    def lab(a, z):
        kinds = []
        for i in range(a, z + 1):
            k = own[i]
            if k != here and k not in kinds:
                kinds.append(k)
        return 'printed in ' + ' and '.join(WHERE[k] for k in kinds) if kinds else 'blank'
    return lab


def runs(lines, own, wanted):
    """Contiguous runs of lines whose owner is in `wanted`: [(first line number, [text, ...])]."""
    out, cur = [], None
    for i, text in enumerate(lines, start=1):
        if own[i] in wanted:
            if cur is None:
                cur = (i, [])
            cur[1].append(text)
        elif cur is not None:
            out.append(cur)
            cur = None
    if cur:
        out.append(cur)
    return out


# ---- rendering ---------------------------------------------------------------------------------------
FMT = dict(nowrap=False, linenos='inline', cssclass='code')


def code_block(text, start, lexer):
    return highlight(text, lexer, HtmlFormatter(linenostart=start, **FMT))


def file_section(rel, note, pieces=None, lexer=None, gap_label=None):
    """A whole file, or `pieces` [(start, lines)] of it, under one heading."""
    path = os.path.join(ENG, rel)
    lexer = lexer or (JsonLexer() if rel.endswith('.json') else PythonLexer())
    body = []
    if pieces is None:
        text = open(path).read()
        n = text.count('\n') + (0 if text.endswith('\n') else 1)
        body.append(code_block(text, 1, lexer))
        count = n
    else:
        count = sum(len(ls) for _, ls in pieces)
        prev_end = None
        for k, (start, ls) in enumerate(pieces):
            if k:
                body.append(f'<div class="gap">⋯ lines {prev_end + 1}–{start - 1}: {gap_label(prev_end + 1, start - 1)} ⋯</div>'
                            if gap_label else '<div class="gap">⋯ lines not in this part ⋯</div>')
            body.append(code_block('\n'.join(ls) + '\n', start, lexer))
            prev_end = start + len(ls) - 1
    anchor = rel.replace('/', '_').replace('.', '_') + ('' if pieces is None else '_part')
    return anchor, count, (f'<h2 id="{anchor}">playmaker_engine/{html.escape(rel)}</h2>'
                           f'<p class="note">{html.escape(note)}</p>' + ''.join(body))


def json_section(title, note, data, anchor):
    text = json.dumps(data, indent=2, ensure_ascii=False)
    return anchor, text.count('\n') + 1, (f'<h2 id="{anchor}">{html.escape(title)}</h2><p class="note">{html.escape(note)}</p>'
                                         + code_block(text + '\n', 1, JsonLexer()))


CSS = """
@page { size: A4; margin: 12mm 10mm 12mm 10mm; }
body { font-family: Helvetica, Arial, sans-serif; color: #1d1b18; font-size: 10px; }
h1 { font-size: 22px; margin: 0 0 4px; } h2 { font-size: 13px; margin: 18px 0 2px; page-break-after: avoid;
  border-bottom: 2px solid #1d1b18; padding-bottom: 2px; }
h3 { font-size: 12px; margin: 14px 0 4px; }
p.note { margin: 2px 0 6px; color: #444; }
.lead p, .lead li { font-size: 11px; line-height: 1.45; }
table.toc { border-collapse: collapse; width: 100%; margin: 6px 0 10px; }
table.toc td, table.toc th { border: 1px solid #bbb; padding: 3px 6px; text-align: left; vertical-align: top; font-size: 10px; }
table.toc th { background: #eee; }
.gap { font-family: Menlo, Consolas, monospace; color: #888; font-size: 8px; margin: 2px 0 2px 40px; }
div.code { border-left: 1px solid #ddd; }
.code pre { margin: 0; font-family: Menlo, Consolas, 'DejaVu Sans Mono', monospace; font-size: 8px;
  line-height: 1.32; white-space: pre-wrap; word-break: break-all; padding-left: 4px; }
.code .linenos { color: #999; display: inline-block; min-width: 30px; padding-right: 6px; text-align: right;
  user-select: none; }
"""


def page(title, subtitle, intro_html, sections):
    style = HtmlFormatter(style='friendly').get_style_defs('.code')
    toc = ''.join(f'<tr><td><a href="#{a}">{html.escape(t)}</a></td><td>{n}</td><td>{html.escape(w)}</td></tr>'
                  for a, t, n, w in sections['toc'])
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f'<style>{CSS}{style}</style></head><body>'
            f'<h1>{html.escape(title)}</h1><p>{subtitle}</p><div class="lead">{intro_html}</div>'
            f'<h3>Contents</h3><table class="toc"><tr><th>Section</th><th>Lines</th><th>What it is</th></tr>{toc}</table>'
            + ''.join(sections['body']) + '</body></html>')


def commit():
    try:
        h = subprocess.run(['git', 'log', '-1', '--format=%h %ad', '--date=short'], cwd=ROOT, capture_output=True,
                           text=True).stdout.strip()
        dirty = subprocess.run(['git', 'status', '--porcelain', '--', 'playmaker_engine'], cwd=ROOT, capture_output=True,
                               text=True).stdout.strip()
        return h + (' (with uncommitted engine changes)' if dirty else '')
    except Exception:
        return 'unknown'


def to_pdf(html_path, pdf_path):
    js = os.path.join(OUT, '_pdf.js')
    open(js, 'w').write("const { chromium } = require('playwright'); (async () => { const [s, o] = process.argv.slice(2);"
                        " const b = await chromium.launch(); const p = await b.newPage(); await p.goto('file://' + s);"
                        " await p.pdf({ path: o, format: 'A4', printBackground: true,"
                        " displayHeaderFooter: true, headerTemplate: '<span></span>',"
                        " footerTemplate: '<div style=\"font-size:8px;width:100%;text-align:center;color:#777\">"
                        "<span class=\"title\"></span> · page <span class=\"pageNumber\"></span> of <span class=\"totalPages\"></span></div>',"
                        " margin: { top: '12mm', bottom: '14mm', left: '10mm', right: '10mm' } }); await b.close(); })();")
    try:
        subprocess.run(['node', js, html_path, pdf_path], check=True)
    finally:
        os.remove(js)


def build():
    os.makedirs(OUT, exist_ok=True)
    stamp = f'Code at commit {commit()}. Built {datetime.date.today().isoformat()}. Line numbers are the real ones in each file.'
    c_lines, c_own = owners(os.path.join(ENG, 'computer.py'), {'offence': C_OFF, 'defence': C_DEF, 'shared': C_SHARED})
    s_lines, s_own = owners(os.path.join(ENG, 'solver.py'),
                            {'offence': S_OFF, 'defence': S_DEF, 'search': S_SEARCH, 'shared': S_SHARED})
    levels = json.load(open(os.path.join(ENG, 'computer_levels.json')))
    common = {k: v for k, v in levels.items() if k not in ('offence', 'defence')}
    off_words = {'habit_words': {k: v for k, v in levels['habit_words'].items() if k in levels['offence']['habits']
                                 or k in ('settles_for_first_shot',)},
                 'concept_words': levels['concept_words']}

    # ---- 1. game logic
    secs = {'toc': [], 'body': []}
    for rel, note in GAME_FILES:
        a, n, h = file_section(rel, note)
        secs['toc'].append((a, rel, n, note))
        secs['body'].append(h)
    intro = ('<p>The rules engine: everything that decides what is legal and what happens. The computer players, '
             'the solver, the web page and the research tools are not here; the computer documents cover the '
             'computer players.</p><p><b>How it fits together.</b> <code>scenarios.py</code> builds a starting '
             '<code>GameState</code> (<code>state.py</code>). <code>actions.legal_actions(state)</code> lists every '
             'legal action. <code>resolve.apply(state, action)</code> returns the next state, or a '
             '<code>ChanceNode</code> when a d20 roll decides it (each outcome with its probability). '
             '<code>scoring.score(state)</code> values a finished possession. Every switchable rule reads '
             '<code>state.ctx.rules</code> (<code>rules_config.Rules</code>); the defaults are the rules as '
             'ruled.</p>')
    hp = os.path.join(OUT, 'Game_logic.html')
    open(hp, 'w').write(page('Playmaker: game logic', stamp, intro, secs))
    to_pdf(hp, hp.replace('.html', '.pdf'))
    made = [hp.replace('.html', '.pdf')]

    # ---- 2 and 3. the computer, offence and defence
    for side in ('offence', 'defence'):
        secs = {'toc': [], 'body': []}

        def add(item):
            a, n, h = item[:3]
            secs['body'].append(h)
            return a, n

        secs['body'].append('<h2>Part 1. The shared core (the same in both computer documents)</h2>'
                            '<p class="note">The computer player framework, card reading, contest reach, and the '
                            'solver\'s evaluation and reach model that both sides use to value positions.</p>')
        a, n = add(file_section('computer.py', 'Shared: the Computer class framework (choose, queue, values, ranking), '
                                'card reading by level, reachable contests.', runs(c_lines, c_own, {'shared'}), gap_label=labeller(c_own, 'shared')))
        secs['toc'].append((a, 'computer.py (shared core)', n, 'The Computer framework, card reading, reachable contests.'))
        a, n = add(file_section('solver.py', 'Shared: position values (Evaluator), defender reach, plays and how they '
                                'apply.', runs(s_lines, s_own, {'shared'}), gap_label=labeller(s_own, 'shared')))
        secs['toc'].append((a, 'solver.py (shared core)', n, 'The evaluation both sides use, defender reach, applying plays.'))
        a, n = add(file_section('solver_config.py', 'Shared: every width and weight the evaluation uses.'))
        secs['toc'].append((a, 'solver_config.py', n, 'Evaluation widths and weights.'))
        a, n = add(json_section('computer_levels.json (shared keys)', 'Thinking time, level names.', common, 'levels_common'))
        secs['toc'].append((a, 'computer_levels.json (shared keys)', n, 'Thinking time, level names.'))

        secs['body'].append(f'<h2>Part 2. The {side}</h2>')
        if side == 'offence':
            a, n = add(file_section('computer.py', 'The offence: targets and plan, the shot bars, passing judgement '
                                    '(step 3f), advantage plays (step 3g), loops and memory.',
                                    runs(c_lines, c_own, {'offence'}), gap_label=labeller(c_own, 'offence')))
            secs['toc'].append((a, 'computer.py (offence)', n, 'Targets, shot bars, passing, advantage plays, the plan.'))
            a, n = add(file_section('advantage.py', 'The six advantage states (step 3g).'))
            secs['toc'].append((a, 'advantage.py', n, 'Beaten, mismatch, help pulled, bad closeout, spent, numbers.'))
            a, n = add(file_section('solver.py', 'The offence play generator (fallback candidates).',
                                    runs(s_lines, s_own, {'offence'}), gap_label=labeller(s_own, 'offence')))
            secs['toc'].append((a, 'solver.py (offence plays)', n, 'Offence candidate plays for the fallback search.'))
            data = dict(levels['offence'], **off_words)
        else:
            a, n = add(file_section('computer.py', 'The defence: choosing a defence play, the comfort line, the '
                                    'concepts and habits, contests and reactions, the threat of a dribble, the setup.',
                                    runs(c_lines, c_own, {'defence'}), gap_label=labeller(c_own, 'defence')))
            secs['toc'].append((a, 'computer.py (defence)', n, 'Defence choice, comfort line, habits, contests, setup.'))
            a, n = add(file_section('defence.py', 'Arrow jobs (on the ball, wall, lane, help) and the board-reading '
                                    'defence from step 3e (kept for the arrow-job labels and its tests).'))
            secs['toc'].append((a, 'defence.py', n, 'Arrow jobs; the step-3e reading defence.'))
            a, n = add(file_section('solver.py', 'The defence and reaction play generators: closeouts, help, deny, '
                                    'contain, recover / switch, combos; the reaction to a declared shot.',
                                    runs(s_lines, s_own, {'defence'}), gap_label=labeller(s_own, 'defence')))
            secs['toc'].append((a, 'solver.py (defence plays)', n, 'Defence and reaction candidate plays.'))
            data = dict(levels['defence'], habit_words={k: v for k, v in levels['habit_words'].items()
                                                         if k in levels['defence']['habits']},
                        concept_words=levels['concept_words'])
        a, n = add(json_section(f'computer_levels.json ({side})', f'The {side} levels, habits and levers.', data,
                                f'levels_{side}'))
        secs['toc'].append((a, f'computer_levels.json ({side})', n, f'The {side} presets: every lever.'))

        secs['body'].append('<h2>Appendix</h2>')
        a, n = add(file_section('policies.py', 'The base player class, and the greedy baseline computer (the "baseline" '
                                'option, not offered on the setup screen).'))
        secs['toc'].append((a, 'policies.py', n, 'The base class; the greedy baseline.'))
        a, n = add(file_section('solver.py', 'The solver\'s search and the exact endgame solver. A computer level uses '
                                'it only with lookahead "solver", which no level uses at present.',
                                runs(s_lines, s_own, {'search'}), gap_label=labeller(s_own, 'search')))
        secs['toc'].append((a, 'solver.py (search, appendix)', n, 'The search; not used by any level now.'))

        if side == 'offence':
            intro = ('<p>Everything the computer uses to choose the <b>offence\'s</b> actions. The computer sees only '
                     'what a human player sees (the Coach\'s Call target is masked for the defence, and card ratings are '
                     'read at the level\'s card reading).</p><p><b>The path of a decision.</b> '
                     '<code>Computer.choose</code> → <code>_attack</code>. On a play turn, '
                     '<code>_advantage_attack</code> generates advantage plays (<code>_adv_plays</code>), scores shots by '
                     'the shot bars (<code>_bar</code>, <code>_contested</code>) and every other play by create, reply, '
                     'exploit (<code>_adv_value</code>, <code>_exploit</code>, <code>pass_risk</code>), and returns the '
                     'best. If nothing scores above zero, <code>_attack</code> falls back to the older valuation of the '
                     'generator\'s plays (<code>_play_value</code>, step 3f). <code>_plan_note</code> keeps the plan (the '
                     'advantage play being worked) and writes the log notes the review reads.</p>')
        else:
            intro = ('<p>Everything the computer uses to choose the <b>defence\'s</b> actions, including the setup '
                     'placement.</p><p><b>The path of a decision.</b> <code>Computer.choose</code> → '
                     '<code>_defend</code>: habits that override first (jumps the first pass, nearest closes out), '
                     'the contest choice (<code>_contest</code>), then the generator\'s defence or reaction plays, '
                     'filtered by the level\'s concepts (<code>_concept_filter</code>), each valued by the offence\'s '
                     'best answer (<code>_value_fn</code> → <code>_threat</code>, which also weighs a dribble), and '
                     'picked with the comfort line (<code>_comfort_key</code>) and the habits '
                     '(<code>_habit_rewrite</code>). The setup is <code>place_defence</code>.</p>')
        title = f'Playmaker: computer {side}'
        hp = os.path.join(OUT, f'Computer_{side}.html')
        open(hp, 'w').write(page(title, stamp, intro, secs))
        to_pdf(hp, hp.replace('.html', '.pdf'))
        made.append(hp.replace('.html', '.pdf'))
    return made


if __name__ == '__main__':
    for p in build():
        print(p)
