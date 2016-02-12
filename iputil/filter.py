import inspect
import itertools
import json
import operator
import os

OPERATORS = {
    '<': operator.lt,
    '<=': operator.le,
    '==': operator.eq,
    '!=': operator.ne,
    '>=': operator.ge,
    '>': operator.gt,
    'in': operator.contains,
    'nin': lambda x, y: not operator.contains(x, y),
}


def can_take_n_args(func, n=2):
    """Returns true if the provided function can accept two arguments."""
    (pos, args, kwargs, defaults) = inspect.getargspec(func)
    if args is not None or len(pos) >= n:
        return True
    return False


def query(d, key, val, operator='==', keynotfound=None):
    """Performs a query on a list of dicts useing the provided operator."""
    d = itertools.tee(d, 2)[1]
    if callable(operator):
        if not can_take_n_args(operator, 2):
            raise ValueError('operator must take at least 2 arguments')
        op = operator
    else:
        op = OPERATORS.get(operator, None)
    if not op:
        raise ValueError('operator must be one of %r' % OPERATORS)

    def try_op(func, x, y):
        try:
            result = func(x, y)
            return result
        except Exception:
            return False

    return (x for x in d if try_op(op, x.get(key, keynotfound), val))


class Query(object):
    """Helper class to make queries chainable."""

    def __init__(self, d):
        self.d = itertools.tee(d, 2)[1]

    def to_list(self):
        return list(itertools.tee(self.d, 2)[1])

    def query(self, *args, **kwargs):
        return Query(query(self.d, *args, **kwargs))


def filter_ips(cache_path, query):
    """Filter IPs using the provided query parameters"""
    if not os.path.exists(cache_path) or not query:
        return []
    with open(cache_path, 'rb') as f:
        cache = json.loads(f.read())
    results = []
    or_clauses = query.split('or')
    for or_clause in or_clauses:
        q = Query(cache)
        and_clauses = or_clause.split('and')
        for and_clause in and_clauses:
            parts = and_clause.split(None, 2)
            if len(parts) == 3:
                q = q.query(parts[0].lower(), parts[2], parts[1])
        results = results + q.to_list()
    return results
