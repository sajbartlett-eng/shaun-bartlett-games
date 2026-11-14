"""Step 2: the numbers the rules register marks Shared match the printed rulebook and trackers, and RULES_CURRENT.md is
what the register's generator writes now (python3 -m playmaker_engine.register --rules).
Step 3: RULES_CURRENT.md lists the ruled-but-unprinted and ruled-but-unbuilt rules, each pointing to a DECISIONS.md entry."""
import os
import re
import shutil
import subprocess

import pytest

from playmaker_engine import register as RG
from playmaker_engine import rules_config as RC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, 'reference')
needs_pdftotext = pytest.mark.skipif(shutil.which('pdftotext') is None, reason='needs pdftotext')


def printed(name):
    """The PDF's text, whitespace collapsed (reading order, not layout)."""
    out = subprocess.run(['pdftotext', os.path.join(REF, name), '-'], capture_output=True, text=True, check=True).stdout
    return re.sub(r'\s+', ' ', out)


def number(pattern, text):
    m = re.search(pattern, text)
    assert m, f'not found in the printed text: {pattern}'
    return [int(g.replace('−', '-')) for g in m.groups() if g is not None]


@pytest.fixture(scope='module')
def pages():
    return dict(book=printed('Playmaker_Rulebook.pdf'), off=printed('Offence_tracker.pdf'),
                dfn=printed('Defence_tracker.pdf'))


# the numbers the table plays by: Shared, or (step 18k, D-181: the steal foul's +5) the table's alone
SHARED = {e[0] for e in RG.ENTRIES if e[1] in (RG.SHARED, RG.TABLETOP)}

# (register entry, value the register holds, pattern in the printed text, page)
CHECKS = [
    ('Tokens per phase (6 a side)', [RC.TOKENS_PER_PHASE], r'their (\d+) action tokens', 'book'),
    ('Phase length (2 seconds), start clock 12', [RC.PHASE_SECONDS], r'phases of (\d+) seconds', 'book'),
    ('Phase length (2 seconds), start clock 12', [RC.START_CLOCK], r'shot clock marker on (\d+)', 'book'),
    ('Phase length (2 seconds), start clock 12', [RC.PHASE_SECONDS], r'shot clock down (\d+)', 'book'),
    ('Lock tokens (8)', [8], r'(\d+) lock tokens', 'book'),
    ('Turnover points (-5)', [RC.TURNOVER_POINTS], r'Intercept or steal ([−-]\d+), lose 2 seconds', 'book'),
    ('Turnover points (-5)', [RC.TURNOVER_POINTS], r'Intercepted: ([−-]\d+)', 'off'),
    ('Steal foul +5', [RC.STEAL_FOUL_BONUS], r'Foul on a steal \+(\d+), play on', 'book'),
    ('Steal foul +5', [RC.STEAL_FOUL_BONUS], r'Foul: \+(\d+) to them', 'dfn'),
    ('Far-contest -3', [-RC.FAR_CONTEST_PENALTY], r'contest at ([−-]\d+)', 'book'),
    ('Far-contest -3', [RC.FAR_CONTEST_PENALTY], r'than the shooter: contest [−-] ?(\d+)', 'dfn'),
    ('Free-throw multipliers (x2, x3)', [RC.FT_MULT_TWO, RC.FT_MULT_THREE],
     r'(\d+) × the shooter.s FT rating, or (\d+) ×', 'book'),
    ('Move shape (3 straight, 2 diagonal)', [RC.MOVE_STRAIGHT, RC.MOVE_DIAGONAL],
     r'Up to (\d+) straight, 1 straight \+ 1 diagonal, or (\d+) diagonal', 'off'),
    ('Move shape (3 straight, 2 diagonal)', [RC.MOVE_STRAIGHT, RC.MOVE_DIAGONAL],
     r'Up to (\d+) straight, 1 straight \+ 1 diagonal, or (\d+) diagonal', 'dfn'),
]


@needs_pdftotext
@pytest.mark.parametrize('entry,held,pattern,page', CHECKS, ids=[f'{c[0]}:{c[3]}:{c[2][:24]}' for c in CHECKS])
def test_every_shared_number_is_the_printed_number(pages, entry, held, pattern, page):
    assert entry in SHARED, f'{entry} is not marked Shared or Tabletop only in the register'
    assert number(pattern, pages[page]) == held


def test_rules_current_is_what_the_register_writes_now():
    doc = open(os.path.join(ROOT, 'RULES_CURRENT.md')).read()
    assert doc == RG.rules_markdown(), 'RULES_CURRENT.md is stale: run python3 -m playmaker_engine.register --rules'


def test_every_register_row_has_its_value_in_words():
    for name, *_ in RG.ENTRIES:
        w = RG.words_for(name)
        assert w.get('tab') and w.get('dig'), name
        for fmt, rules in (('tab', RC.DEFAULT_RULES), ('dig', RC.with_rules(digital=True))):
            raw = RG.value(rules, RG.ENTRIES_BY_NAME[name])
            assert '_' not in w[fmt], (name, w[fmt])                      # no setting or code name
            assert w[fmt] != str(raw), (name, w[fmt])                     # the value in words, not the raw value


def _section(doc, title):
    part = doc.split(f'## {title}\n', 1)
    assert len(part) == 2, f'RULES_CURRENT.md has no section {title!r}'
    return part[1].split('\n## ', 1)[0]


def _decisions():
    text = open(os.path.join(ROOT, 'DECISIONS.md')).read()
    return set(re.findall(r'^\*\*(D-\d+)\b', text, re.M))                # each entry starts **D-n


def test_the_two_ruled_lists_point_to_decisions():
    # step 6: Contest as an action (D-18) and overtime (D-19) are built; the rulings of 9 Nov 2026 not yet printed join
    # the first list
    doc = open(os.path.join(ROOT, 'RULES_CURRENT.md')).read()
    known = _decisions()
    printed = [l for l in _section(doc, 'Ruled, not yet printed').splitlines() if re.match(r'\d+\. ', l)]
    unbuilt = [l for l in _section(doc, 'Ruled, not yet built').splitlines() if re.match(r'\d+\. ', l)]
    assert printed and unbuilt == []
    for line in printed:
        d = re.findall(r'See (D-\d+)\.', line)
        assert len(d) == 1 and d[0] in known, line
    cited = {re.search(r'See (D-\d+)', l).group(1) for l in printed}
    assert {f'D-{n}' for n in range(1, 18)} | {'D-18', 'D-30', 'D-36', 'D-82', 'D-88', 'D-89'} <= cited
    assert 'OPEN_QUESTIONS.md' not in doc


def test_tied_match_is_an_approved_split_with_overtime_built():
    status = {e[0]: e[1] for e in RG.ENTRIES}
    assert status['Tied match'] == 'Split by format, approved'
    assert status['Junior growth'] == 'Split by format, approved'
