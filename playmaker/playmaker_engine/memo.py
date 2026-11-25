"""Step 30b: a memory that lasts one think (engine.js keeps the same memory for one request).

A think is one side deciding: a computer turn (agent.Agent.choose) or a setup (plan.place_offence, plan.place_defence).
Inside it the same board is reached by different orders of moves, and the same reading is asked for again by another
part of the reading. Each such reading is worked out once. Nothing carries to the next turn, the next possession or
the other side: the memory is opened when the outermost think starts and thrown away when it ends.

It holds readings, never choices. Every key is built from the state itself: a GameState compares and hashes on all of
its fields (only the context is left out, and the key adds the context's identity), and a request to the JavaScript
engine is keyed on its whole text. Two states that differ in any way never share a reading."""
import contextlib

MAX_ENTRIES = 2000              # a full memory is cleared, never trimmed by choice: a cleared reading is just read again
_S = dict(depth=0, maps=None, calls=None)


@contextlib.contextmanager
def think():
    if _S['depth'] == 0:
        _S['maps'], _S['calls'] = {}, {}
    _S['depth'] += 1
    try:
        yield
    finally:
        _S['depth'] -= 1
        if _S['depth'] == 0:
            _S['maps'] = _S['calls'] = None


def get(kind, key, make):
    """The reading under key in this think's memory, made once; with no think open, made every time."""
    store = _S['maps'] if kind == 'map' else _S['calls']
    if store is None:
        return make()
    v = store.get(key)
    if v is None:
        v = make()
        if len(store) >= MAX_ENTRIES:
            store.clear()
        store[key] = v
    return v


def is_open():
    return _S['depth'] > 0
