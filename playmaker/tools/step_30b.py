"""Step 30b: speed foundations. Measure first; then check that nothing decided changed.

  python3 tools/step_30b.py profile [tag]     the three boards: an offence setup, a defence setup and one computer turn,
                                              each timed; every call into the JavaScript engine counted, timed and
                                              checked for repeats (the same request text twice); JS profile on request
  python3 tools/step_30b.py record [tag]      the same, run with no clock that can bind (fixed look-ahead), writing every
                                              request and its answer to docs/runs/step30b/<tag>_calls.jsonl
  python3 tools/step_30b.py replay <tag>      every recorded request sent again to today's engine: is each answer
                                              exactly the same text?
"""
import hashlib
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'docs', 'runs', 'step30b')
os.makedirs(RUN, exist_ok=True)

import step_28 as S28            # noqa: E402  (step 30's boards)

BLOCK_O = ['H4', 'C9', 'O9', 'A3', 'Q9']
BLOCK_X = ['D8', 'B8', 'N8', 'B3', 'H3']


class Meter:
    """Wraps agent.JS: every call timed, by function and kind; repeats (the same request text) counted with the time
    they took; optionally every request and answer written out."""

    def __init__(self, AG, log=None):
        self.AG, self.log = AG, log
        self.rows = {}
        self.seen = {}
        self.calls = []
        self.orig = dict(AG.JS)
        for fn in ('search', 'goals', 'reads', 'coverage'):
            if AG.JS.get(fn) is not None:
                AG.JS[fn] = self._wrap(fn, AG.JS[fn])

    def _wrap(self, fn, f):
        def g(text):
            t0 = time.time()
            out = f(text)
            dt = time.time() - t0
            try:
                req = json.loads(text)
                kind = fn if fn != 'coverage' else 'coverage:' + str(((req.get('options') or {}).get('only')) or 'full')
                if fn == 'search':
                    kind += ':budget' if req.get('budget') is not None else ':fixed'
            except Exception:
                kind = fn
            h = hashlib.sha1(text.encode()).hexdigest()
            r = self.rows.setdefault(kind, dict(n=0, s=0.0, rep=0, rep_s=0.0))
            r['n'] += 1
            r['s'] += dt
            if h in self.seen:
                r['rep'] += 1
                r['rep_s'] += dt
            self.seen[h] = self.seen.get(h, 0) + 1
            if self.log is not None:
                self.log.write(json.dumps(dict(fn=fn, req=text, out=out)) + '\n')
            return out
        return g

    def close(self):
        self.AG.JS.update(self.orig)

    def summary(self):
        tot = sum(r['s'] for r in self.rows.values())
        return dict(js_seconds=round(tot, 1), calls=sum(r['n'] for r in self.rows.values()),
                    repeats=sum(r['rep'] for r in self.rows.values()),
                    repeat_seconds=round(sum(r['rep_s'] for r in self.rows.values()), 1),
                    by_kind={k: dict(n=r['n'], s=round(r['s'], 1), repeats=r['rep'], repeat_s=round(r['rep_s'], 1))
                             for k, r in sorted(self.rows.items(), key=lambda kv: -kv[1]['s'])})


def boards():
    """(name, make, the block board's own position or None)."""
    import step_21 as T
    out = []
    for off, dfn, label in S28.BOARDS:
        if label in ('board 2', 'board 3'):
            out.append((f'{off} v {dfn}', S28._make(off, dfn), None))
    blk = T._state(BLOCK_O, BLOCK_X, [0] * 5, ball=0, off='Five Out', dfn='Iron Wall')
    out.append(('Five Out v Iron Wall (the block board)', S28._make('Five Out', 'Iron Wall'), blk))
    return out


def _turn(AG, B, RC, st, block):
    """One computer turn: on the block board, the defence's reply to O1's layup off a Sprint; elsewhere the offence's
    first turn from the setup."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    if block is not None:
        s = block.with_(side='O', turn_n=0, rush_o=RC.RUSH_SPRINT)
        decl = apply(s, next(a for a in legal_actions(s) if a.kind == 'shot' and a.arrow != 1 and a.shot == 'layup'))
        ag = AG.Agent('X', 'allstar', seed=1)
        t = time.time()
        a = ag.choose(decl)
    else:
        from playmaker_engine import plan as PL
        ag = AG.Agent('O', 'allstar', seed=1)
        ag.scout = PL.Scout(st.ctx, 'O')
        # step 31: under the possession's value the new setup hands the offence no list-led plan (setup31.place_offence), so
        # the app's computer carries none into play; the turn is timed as the app plays it
        ag.setup_plan = None if PL._value_led() else PL.read_plan(st, ag.scout, deep=True)
        t = time.time()
        a = ag.choose(st.with_(side='O', turn_n=0))
    note = next((n for n in reversed(ag.notes) if n.get('event') in ('decision', 'mix')), {})
    return dict(action=str(a), seconds=round(time.time() - t, 1), depth=note.get('depth'), value=note.get('value'),
                fake_chance=note.get('fake_chance'), replies=note.get('replies'))


def _run(tag, record=False, fixed=None, only=None):
    from playmaker_engine import agent as AG, board as B, jsbridge, plan as PL, rules_config as RC
    eng = jsbridge.NodeEngine().install()
    log = open(os.path.join(RUN, f'{tag}_calls.jsonl'), 'w') if record else None
    out = {}
    try:
        if fixed:
            AG.FIXED['depth'] = fixed
        for name, make, block in boards():
            if only and only not in name:
                continue
            row = {}
            m = Meter(AG, log)
            t0 = time.time()
            r = PL.place_offence(make, seed=1)
            t1 = time.time()
            row['offence_setup'] = dict(seconds=round(t1 - t0, 1), squares=[B.sq(q) for q in r['squares']], ball=r['ball'],
                                        line=(r.get('plan') or {}).get('line'), **m.summary())
            m.close()
            m = Meter(AG, log)
            t0 = time.time()
            d = PL.place_defence(make, r['squares'], r['ball'], seed=1)
            t1 = time.time()
            row['defence_setup'] = dict(seconds=round(t1 - t0, 1), squares=[B.sq(q) for q in d['squares']], arrows=d['arrows'],
                                        read=[z['text'] for z in d['read']][:5], **m.summary())
            m.close()
            st = make(r['squares'], r['ball'], d['squares'], d['arrows'])
            m = Meter(AG, log)
            t0 = time.time()
            row['turn'] = dict(**_turn(AG, B, RC, st, block), **m.summary())
            m.close()
            out[name] = row
            print(name, json.dumps({k: (v['seconds'], v['js_seconds'], v['calls'], v['repeats'], v['repeat_seconds']) for k, v in row.items()}), flush=True)
    finally:
        AG.FIXED['depth'] = None
        if log:
            log.close()
        eng.close()
    json.dump(out, open(os.path.join(RUN, f'{tag}.json'), 'w'), indent=1)
    return out


def cmd_profile(tag='before', only=None):
    _run(tag, only=only)


def cmd_record(tag='before_fixed', only=None):
    _run(tag, record=True, fixed=1, only=only)


def _norm(fn, text):
    """A search's answer carries how long it took: compared without that (its depths kept)."""
    if fn != 'search':
        return text
    o = json.loads(text)
    o.pop('seconds', None)
    o['depth_seconds'] = [d[0] for d in o.get('depth_seconds') or []]
    return json.dumps(o, sort_keys=True)


def cmd_replay(tag='before_fixed'):
    """Every recorded request again, on today's engine: the same text back?"""
    from playmaker_engine import jsbridge
    eng = jsbridge.NodeEngine()
    n = same = 0
    bad = []
    t0 = time.time()
    try:
        for ln in open(os.path.join(RUN, f'{tag}_calls.jsonl')):
            r = json.loads(ln)
            req = json.loads(r['req'])
            if r['fn'] == 'search' and req.get('budget') is not None:
                continue                                  # a clock-limited search: its answer depends on the clock
            fn = dict(search='searchJSON', goals='goalsJSON', reads='readsJSON', coverage='coverageJSON')[r['fn']]
            got = eng.call(fn, r['req'])
            n += 1
            if _norm(r['fn'], got) == _norm(r['fn'], r['out']):
                same += 1
            elif len(bad) < 5:
                bad.append(dict(fn=r['fn'], req=r['req'][:300], was=r['out'][:300], now=got[:300]))
    finally:
        eng.close()
    res = dict(requests=n, identical=same, seconds=round(time.time() - t0, 1), different=bad)
    json.dump(res, open(os.path.join(RUN, f'replay_{tag}.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'different'}))
    for b in bad[:3]:
        print(b)


SERVER = r"""
const fs = require('fs'), path = require('path'), readline = require('readline');
const E = require(process.argv[1]);
const root = process.argv[2];
const load = n => JSON.parse(fs.readFileSync(path.join(root, n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'),
  learned: fs.existsSync(path.join(root, 'learned_weights.json')) ? load('learned_weights.json') : null });
readline.createInterface({ input: process.stdin }).on('line', ln => {
  let out; try { const q = JSON.parse(ln); out = { ok: E[q.fn](q.text) }; } catch (e) { out = { error: String(e && e.stack || e) }; }
  process.stdout.write(JSON.stringify(out) + '\n');
});
"""


def _engine(path):
    """A NodeEngine on any engine.js file (the one before this step, or today's)."""
    import subprocess
    from playmaker_engine import jsbridge
    eng = jsbridge.NodeEngine.__new__(jsbridge.NodeEngine)
    data = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'playmaker_engine', 'data')
    eng.p = subprocess.Popen(['node', '-e', SERVER, os.path.abspath(path), data], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, text=True, bufsize=1)
    return eng


def exam_boards():
    """Step 31's exam boards that today's engine can already read (STEP31_PLAN.md, section 6). Arrows the plan leaves
    open are set facing the basket; the comparison is the same board on both engines, so this is fair to both."""
    import step_21 as T
    out = []
    s = T._state(['I11', 'C9', 'O9', 'J3', 'A3'], ['I10', 'D8', 'N8', 'L5', 'B4'], ['S'] * 5, ball=3,
                 off='High-Low', dfn='Iron Wall', clock=8)
    out.append(('E13 the cutter under the rim (offence)', s))
    s = T._state(['K9', 'C9', 'I12', 'A3', 'Q3'], ['K8', 'D8', 'P4', 'B4', 'N4'], ['S'] * 5, ball=0,
                 off='Five Out', dfn='Iron Wall', clock=10, side='X')
    out.append(('E24 a man the ball cannot reach (defence)', s))
    s = T._state(['I11', 'C9', 'O9', 'A3', 'L7'], ['I10', 'G5', 'K5', 'B4', 'I9'], ['S'] * 5, ball=0,
                 off='Five Out', dfn='Iron Wall', clock=10, side='X')
    out.append(('E28 two lanes or one (defence)', s))
    return out


def cmd_exam(old_engine, depth='1'):
    """Each exam board's decision at a fixed look-ahead, on the engine before this step and on today's: the same
    choice, value, mix odds and coach's line?"""
    from playmaker_engine import agent as AG
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'playmaker_web', 'static', 'engine.js')
    res = {}
    AG.FIXED['depth'] = int(depth)
    try:
        for tag, path in (('before', old_engine), ('after', here)):
            eng = _engine(path).install()
            for name, s in exam_boards():
                ag = AG.Agent(s.side, 'allstar', seed=1)
                t = time.time()
                a = ag.choose(s)
                note = next((n for n in reversed(ag.notes) if n.get('event') in ('decision', 'mix')), {})
                res.setdefault(name, {})[tag] = dict(action=str(a), seconds=round(time.time() - t, 1),
                                                     value=note.get('value'), depth=note.get('depth'),
                                                     odds=note.get('fake_chance'), line=note.get('why') or note.get('text'))
                print(tag, name, json.dumps(res[name][tag]), flush=True)
            eng.close()
    finally:
        AG.FIXED['depth'] = None
    for name, r in res.items():
        b, a = dict(r['before']), dict(r['after'])
        b.pop('seconds'), a.pop('seconds')
        r['same'] = a == b
    json.dump(res, open(os.path.join(RUN, f'exam_depth{depth}.json'), 'w'), indent=1)
    print(json.dumps({k: v['same'] for k, v in res.items()}))


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
