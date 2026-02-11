"""JSON encoding and decoding tools for RAMP objects"""
import json
from typing import Hashable, Any

from ramp_core.serializable import Serializable

IDENTIFIER = 'cls'
DATA = '__data'


class RampJSONEncoder(json.JSONEncoder):
    """JSONEncoder for ramp objects that can handle Serializable objects.

    It is useful to have a single json-compatible class to handle our long-term serialization of Ramp objects.

    """

    def default(self, obj):
        try:
            ident, s = obj.serialize()
            return s | {IDENTIFIER: ident} if isinstance(s, dict) else {IDENTIFIER: ident, DATA: s}
        except AttributeError:
            pass
        return json.JSONEncoder.default(self, obj)


class RampJSONDecoder(json.JSONDecoder):
    """JSONDecoder for ramp objects that can reconstruct Serializable objects.

    It will be useful to be able to recreate our Python objects for the ramp objects if we serialize them in a
    long term, non-pickle method.

    The idea is that we save an identifier which allows us to know which Python object to reconstruct.
    To avoid the Pickle problem, the way we do this is that we assume the decoding user can create a mapping of
    serialization identifiers to factory classes that have a deserialize method.

    Examples
    --------
    >>> class A:
    ...     ser_identifier = "AA"
    ...
    ...     def __init__(self, a):
    ...         self.a = a
    ...
    ...     def serialize(self):
    ...         return self.ser_identifier, {'a': self.a}
    ...
    ...     @classmethod
    ...     def deserialize(cls, d, **_):
    ...         return cls(**d)
    >>>
    >>> b = A(5)
    >>> s = json.dumps(b, cls=RampJSONEncoder)
    >>> try:  # This fails because we didn't set the supported attribute
    ...     v = json.loads(s, cls=RampJSONDecoder)
    ... except AttributeError:
    ...     pass
    ... else:
    ...     raise RuntimeError("Should have crashed")
    >>> RampJSONDecoder.supported = {type(b).ser_identifier: b}
    >>> v = json.loads(s, cls=RampJSONDecoder)  # And now it succeeds
    >>> v.a == b.a
    True

    """

    supported: dict[str, Serializable]


    def decode(self, s: str, **kw):
        pobj = super().decode(s, **kw)
        if not isinstance(pobj, dict):
            return pobj
        if IDENTIFIER not in pobj:
            return pobj
        styp = pobj[IDENTIFIER]
        if styp in self.supported:
            del pobj[IDENTIFIER]
            typ = self.supported[styp]
            if DATA in pobj:
                return typ.deserialize(pobj[DATA], supported=self.supported)
            return typ.deserialize(pobj, supported=self.supported)
        return pobj


def unserializable(d: dict | list | tuple) -> list[tuple[list[Hashable], Any]]:
    """Returns which items were unserializable. Useful to debug serializability.
    """
    lst = []
    if isinstance(d, dict):
        iters = d.items()
    elif isinstance(d, (list, tuple)):
        iters = enumerate(d)
    else:
        try:
            json.dumps(d, cls=RampJSONEncoder)
        except TypeError:
            return [([], d)]
        else:
            return []

    for a, b in iters:
        if isinstance(b, (dict, list, tuple)):
            lst.extend([([a] + access, v) for access, v in unserializable(b)])
        else:
            try:
                json.dumps(b, cls=RampJSONEncoder)
            except TypeError:
                lst.append(([a], b))
    return lst

