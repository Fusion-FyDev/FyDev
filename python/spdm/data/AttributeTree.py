import collections
import collections.abc
import functools
import typing
from logging import log
from typing import Any, MutableSequence, Sequence

import numpy as np

from ..util.logger import logger
from .Entry import Entry, _not_found_
from .Node import Dict, List, Node, _next_, _TObject


def do_getattr(obj, k):
    if getattr(obj.__class__, '__getattr__', None) == do_getattr:
        raise RuntimeError(f"Recursive call")

    if k[0] == '_':
        bcls = obj.__class__.__bases__[0]
        res = bcls.__getattr__(obj, k)
    else:
        res = getattr(obj.__class__, k, None)

        if isinstance(res, property):
            res = getattr(res, "fget")(obj)
        elif isinstance(res, functools.cached_property):
            res = res.__get__(obj)
        elif hasattr(obj.__class__, 'get'):
            res = obj.get(k, None)
        else:
            res = obj.__getitem__(k)
    if res is None:
        return AttributeTree(Entry(obj, [k]))
    elif isinstance(res, AttributeTree):
        return res
    elif isinstance(res, Node):
        return AttributeTree(res._entry, parent=res._parent)
    elif isinstance(res, (collections.abc.Mapping)):
        return AttributeTree(res)
    else:
        return res


def do_setattr(obj, k, v):
    if k[0] == '_':
        object.__setattr__(obj, k, v)
    else:
        res = getattr(obj.__class__, k, None)
        if res is None:
            obj.__setitem__(k, v)
        elif isinstance(res, property):
            res.fset(obj, k, v)
        elif isinstance(res, functools.cached_property):
            if isinstance(obj, Node) and isinstance(obj._cache, collections.abc.MutableMapping):
                obj._cache[k] = v
                if hasattr(obj, k):
                    delattr(obj, k)
            else:
                raise AttributeError(f"Can not set cached_property '{k}'! ")
        elif isinstance(v, collections.abc.Mapping):
            target = obj.__getattr__(k)
            for i, d in v.items():
                target.__setattr__(target, i, d)
        else:
            raise AttributeError(f"Can not set attribute {k}:{type(v)}!")


def do_delattr(obj, k):
    if k in Node.__slots__ or k in obj.__slots__:
        raise AttributeError(k)
    else:
        res = getattr(obj.__class__, k, None)
        if res is None:
            obj.__delitem__(k)
        elif isinstance(res, property):
            res.fdel(obj, k)
        elif isinstance(res, functools.cached_property):
            if k in obj.__dict__:
                del obj.__dict__[k]
            # raise AttributeError(f"Can not set cached_property")
        else:
            raise AttributeError(f"Can not delete attribute {k}!")


def as_attribute_tree(cls, *args, **kwargs):
    n_cls = type(f"{cls.__name__}__with_attr__", (cls,), {
        "__getattr__": do_getattr,
        "__setattr__": do_setattr,
        "__delattr__": do_delattr,
        # "__iter__": do_iter,
    })
    return n_cls


class AttributeTree(Dict[str, Node]):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __post_process__(self, value, *args, parent=None, **kwargs):
        if isinstance(value, (collections.abc.Mapping, collections.abc.MutableSequence, Entry)):
            return AttributeTree(value, *args, parent=parent or self, **kwargs)
        else:
            return value
        # return super().__post_process__(value, *args, **kwargs)

    def __new_child__(self, value, *args, parent=None,  **kwargs):
        if isinstance(value, (collections.abc.Mapping)):
            return AttributeTree(value, *args, parent=parent, **kwargs)
        else:
            return super().__new_child__(value, *args, parent=parent, **kwargs)

    def __getattr__(self, *args, **kwargs):
        return do_getattr(self, *args, **kwargs)

    def __setattr__(self, name: str, value: Any) -> None:
        return do_setattr(self, name, value)

    def __delattr__(self, name: str) -> None:
        return do_delattr(self, name)

    def __iter__(self) -> typing.Iterator[Node]:
        # for v in super(Node, self).__iter__():
        #     yield AttributeTree({v})
        yield from Node.__iter__(self)
