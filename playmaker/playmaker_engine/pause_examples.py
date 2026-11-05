"""Step 2b section 2.3: positions where the best defence is Pause, with the alternatives' values."""
from .resolve import ChanceNode
from .solver import Searcher, apply_play
from .solver_report import _start, play_label


def pause_example(n, budget_s=90, after=None):
    """The defence position after the offence's best first play on card n: every defence play the search
    considered there, with its value (lower is better for the defence)."""
    s = _start(n)
    se = Searcher(seed=0)
    res = se.search(s, budget_s=budget_s)
    e = res['entry']
    first = after or e.best
    node = apply_play(s, first)
    while isinstance(node, ChanceNode):
        node = max(node.outcomes, key=lambda o: o[0])[2]
    se2 = Searcher(seed=0)
    r2 = se2.search(node, budget_s=budget_s)
    e2 = r2['entry']
    rows = sorted(((v[0].ev, p.text(), play_label(node, p)) for p, v in e2.children), key=lambda x: x[0])
    return dict(n=n, offence=first.text(), position=node.encode(), board=node.board(), depth=r2['depth'],
                best=e2.best.text() if e2.best else None, options=rows)
