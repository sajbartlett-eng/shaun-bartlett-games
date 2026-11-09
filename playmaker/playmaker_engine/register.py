"""Step 3n Part K: the shared rules register. Every rule value and mechanism, marked Shared (both formats), Digital
only or Tabletop only, with the reason; docs/rules_register.md is written from it (python3 -m playmaker_engine.register)
and tests/test_step3n.py asserts that every Shared entry has identical values in both formats.

A setting is read from rules_config.Rules (rules=...), a constant from rules_config (const=...), or it is a mechanism
the engine applies by format (how=...).
"""
from dataclasses import fields

from . import rules_config as RC

SHARED, DIGITAL, TABLETOP, SPLIT = 'Shared', 'Digital only', 'Tabletop only', 'Split by format'

# (name, status, source, what it is, reason for a split / note)
ENTRIES = [
    # ---- the format itself and what differs on purpose
    ('digital', SPLIT, dict(rules='digital'), 'The match format switch.', 'The two formats themselves.'),
    ('Turnover cost', SPLIT, dict(rules='turnover_cost'), 'A successful Intercept or Steal (and a steal of a declared shot).',
     'Tabletop: -5 and the shot clock loses a phase, play on (the setting). Digital, whatever the setting: the possession ends and scores 0, '
     'because a digital match is several possessions a side and the next possession is the cost.'),
    ('Shot-clock expiry', SPLIT, dict(how='expiry'), 'The clock reaches 0.',
     'Tabletop: -5 and a forced shot. Digital: a turnover, the possession scores 0 (as in basketball).'),
    ('Match length', SPLIT, dict(how='match'), 'Possessions a side.',
     'Tabletop: one possession each. Digital: 2 to 8 a side (per_side), sides alternating.'),
    ('Steal-foul bonus', SPLIT, dict(how='bonus'), 'When a steal foul gives free throws.',
     'Tabletop: the first steal foul of the possession is +5 and play on, the second gives free throws (one '
     'possession is the whole game). Digital (step 3n F3): team fouls run across a quarter; from the 5th a steal foul '
     'gives free throws and ends the possession.'),
    ('quarter_possessions', DIGITAL, dict(rules='quarter_possessions'), 'Possessions a side in a quarter (18).',
     'Team fouls across matches need a running quarter; the table plays one possession.'),
    ('bonus_from', DIGITAL, dict(rules='bonus_from'), 'The team foul that starts the bonus (5th).', 'As above.'),
    ('Team fouls carried across matches', DIGITAL, dict(how='pairing'), 'Stored with the pairing record.',
     'The table has no record between games.'),
    ('Decision timer', DIGITAL, dict(how='timer'), 'Optional per-player thinking clock (step 3c).',
     'An app feature; at the table players agree their own pace.'),
    ('Computer opponents and the trainer', DIGITAL, dict(how='engine'), 'Levels, grading, ratings.', 'App features.'),
    # ---- constants (shared)
    ('Board 17 x 14, rim I2', SHARED, dict(const=('BOARD_COLS', 'BOARD_ROWS', 'RIM')), 'The court.', ''),
    ('Tokens per phase (6 a side)', SHARED, dict(const=('TOKENS_PER_PHASE',)), '', ''),
    ('Phase length (2 seconds), start clock 12', SHARED, dict(const=('PHASE_SECONDS', 'START_CLOCK')), '', ''),
    ('d20 rolls', SHARED, dict(const=('DIE',)), 'Every roll: d20 at or under the target.', ''),
    ('Far-contest -3', SHARED, dict(const=('FAR_CONTEST_PENALTY',)), 'Contester further from the rim than the shooter.', ''),
    ('Turnover points (-5)', SHARED, dict(const=('TURNOVER_POINTS',)), 'The value of a turnover where one is scored.',
     'The number is shared; when it applies is the turnover-cost split above.'),
    ('Steal foul +5', SHARED, dict(const=('STEAL_FOUL_BONUS',)), 'A steal foul before the bonus.', ''),
    ('Free-throw multipliers (x2, x3)', SHARED, dict(const=('FT_MULT_TWO', 'FT_MULT_THREE')), '', ''),
    ('Two actions a turn', SHARED, dict(const=('MAX_ACTIONS_PER_TURN',)), '', ''),
    ('Move shape (3 straight, 2 diagonal)', SHARED, dict(const=('MOVE_STRAIGHT', 'MOVE_DIAGONAL')), '', ''),
    ('Inbound phases (2)', SHARED, dict(const=('INBOUND_PHASES',)), '', ''),
    ('Per-phase limits', SHARED, dict(const=('LIMITS',)), 'Quick Steps, passes, screens, dribbles, waits, shots; '
     'intercepts, challenges, steals.', ''),
    ('Turn-ending actions', SHARED, dict(const=('TURN_ENDERS',)), '', ''),
    ('Zones and shot types', SHARED, dict(const=('ZONE_SHOTS', 'ZONE_POINTS')), '', ''),
    ('Look bands and Coach\'s Call bonus', SHARED, dict(const=('BANDS', 'COACH_BONUS', 'SCENARIO_GOAL')), '', ''),
    ('Playing levels (ages, standards, growth tags)', SHARED, dict(how='levels'),
     'Step 3l: the ratings by age and standard, junior growth tags.', 'Ratings carry age; both formats use the same cards.'),
]
# every Rules setting not named above is shared: the same ruling in both formats
_NAMED = {e[2].get('rules') for e in ENTRIES if e[2].get('rules')}
for f in fields(RC.Rules):
    if f.name not in _NAMED:
        ENTRIES.append((f.name, SHARED, dict(rules=f.name), '', ''))

# tokens and markers the table needs for shared mechanisms with memory (K4)
TOKENS = [
    ('Locks (failed Challenge, lost Dribble, beaten-by-Dribble defender, failed Steal: F1)', 'grey lock tokens',
     'printed: 4 lock tokens (rulebook p1)', 'see the F5 worst case: up to 2 Dribbles, 2 Challenges and 2 Steals a phase can '
     'lock up to 6 pieces in one phase'),
    ('Screens (hold until the screener moves)', 'the O piece flipped to its T side', 'printed: the pieces have a T side', 'covered'),
    ('A player\'s Move used this phase', 'Move token', 'printed: the action token pool', 'covered'),
    ('A player\'s Quick Step used this phase (one each, OQ-52)', 'none printed', 'not on the component list',
     'needs a marker or a note: flag for the designer'),
    ('Dribble wins this phase (the carrier is free of that defender\'s zone)', 'the beaten defender\'s lock token', 'printed',
     'covered by the lock token on the beaten defender'),
    ('Growth tags at junior (Early, On time, Late)', 'one tag per card', 'the levels sheet lists them; no printed tag markers',
     'needs 10 tag markers (5 a team) or written on the team sheet: flag for the designer'),
    ('Steal fouls this possession (tabletop bonus)', 'none needed', 'one possession: players count 0, 1, 2', 'covered'),
]


def value(rules, src):
    if 'rules' in src:
        return getattr(rules, src['rules'])
    if 'const' in src:
        norm = lambda v: tuple(sorted(v)) if isinstance(v, (set, frozenset)) else v
        return tuple(norm(getattr(RC, c)) for c in src['const'])
    return None


def markdown():
    dig, tab = RC.with_rules(digital=True), RC.DEFAULT_RULES
    out = ['# Playmaker rules register', '',
           'Every rule value and mechanism, marked **Shared** (both formats), **Digital only**, **Tabletop only** or '
           '**Split by format** (deliberately different, with the reason). Written by `python3 -m playmaker_engine.register`; '
           '`tests/test_step3n.py` asserts every Shared entry has identical values in both formats, and any change to a '
           'shared value must be tested under both formats.', '',
           '| Rule | Status | Value (tabletop) | Value (digital) | Notes |', '|---|---|---|---|---|']
    for name, status, src, what, note in ENTRIES:
        vt, vd = value(tab, src), value(dig, src)
        fmt = lambda v: '' if v is None else str(v).replace('|', '/')[:60]
        out.append(f'| {name} | {status} | {fmt(vt)} | {fmt(vd)} | {" ".join(x for x in (what, note) if x)} |')
    out += ['', '## Splits for the designer', '',
            'Where the best value differs between formats (a designer decision, not a bug):', '',
            '- Turnover cost and shot-clock expiry: the engine values a risky pass or a reach differently by format, so a '
            'digital-tuned habit (gambling for a steal late in a possession) is wrong at the table, where play goes on '
            'at -5. The trainer grades each game under its own format.',
            '- The steal-foul bonus: within the possession at the table, across a quarter in digital. A defence two fouls '
            'from the bonus behaves differently in each.',
            '- The coarse phase table (engine data, not a rule) is solved from digital self-play; tabletop possessions '
            'play on after a turnover, so their late-phase values differ.', '',
            '## Tokens and markers', '', '| Mechanism | Token | Printed | Check |', '|---|---|---|---|']
    for m, t, p, c in TOKENS:
        out.append(f'| {m} | {t} | {p} | {c} |')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'rules_register.md')
    open(path, 'w').write(markdown())
    print(path)
