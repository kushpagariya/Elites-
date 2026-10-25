"""Small, transport-independent checks for frozen analytical inputs."""
import hashlib
import json
from math import isfinite
from numbers import Real


class DomainUnavailable(ValueError):
    """Inputs cannot support a numerical result; transport must expose the reason."""


def number(value, name, *, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    value = float(value)
    if minimum is not None and value < minimum or maximum is not None and value > maximum:
        raise ValueError(f'{name} outside supported bounds')
    return value


def unique(rows, key, cap=None):
    ids = [r[key] for r in rows]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError(f'{key} must be unique nonempty strings')
    if cap is not None and len(ids) > cap:
        raise ValueError(f'{key} exceeds cap {cap}')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()
