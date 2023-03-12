import bisect
import collections
import collections.abc
import copy
import functools
import inspect
import pprint
import typing
from enum import IntFlag
from functools import cached_property
from typing import (Any, Generic, Iterator, Mapping, MutableMapping, Iterable,
                    MutableSequence, Sequence, TypeVar, Union, get_args)

import numpy as np

from ..util.logger import logger
from ..util.utilities import serialize
from .Entry import _NEXT_TAG_, Entry, _last_, _next_, _not_found_

_TObject = TypeVar('_TObject')
_TKey = TypeVar('_TKey', int, str)
_TIndex = TypeVar('_TIndex', int, slice, _NEXT_TAG_)


class Node(object):
    r"""
        @startuml

        class Node{
            name    : String
            parent  : Node
            value   : Group or Data
        }

        class Group{
            children : Node[*]
        }

        Node *--  Node  : parent

        Node o--  Group : value
        Node o--  Data  : value

        Group *-- "*" Node

        @enduml
    """
    __slots__ = "_parent", "_entry", "_default_factory", "__orig_class__"

    def __init__(self, data: Any = None, *args, default_factory=None, parent=None, **kwargs):
        super().__init__()
        self._default_factory = default_factory
        self._parent = parent

        if isinstance(data, Node):
            self._entry = data._entry
        elif isinstance(data, Entry):
            self._entry = data
        else:
            self._entry = Entry(data, *args, **kwargs)

    def __repr__(self) -> str:
        return pprint.pformat(self.__serialize__())

    def __serialize__(self):
        if isinstance(self._entry, Entry):
            return f"<{self.__class__.__name__} type={self._entry.__class__.__name__} path={ self._entry.__normalize_path__()}>"
        else:
            return serialize(self._entry)

    def __duplicate__(self, desc=None):
        return self.__class__(desc if desc is not None else self.__serialize__(), parent=self._parent)

    # @staticmethod
    # def deserialize(cls, d):
    #     return cls(d)

    def _as_dict(self) -> Mapping:
        return Entry._DICT_TYPE_

    def _as_list(self) -> Sequence:
        return Entry._LIST_TYPE_

    @property
    def __parent__(self):
        return self._parent

    def __hash__(self) -> int:
        return hash(self._name)

    def __clear__(self):
        self._entry = None

    class Category(IntFlag):
        UNKNOWN = 0
        ITEM = 0x000
        DICT = 0x100
        LIST = 0x200
        ENTRY = 0x400

        ARRAY = 0x010

        INT = 0x001
        FLOAT = 0x002
        COMPLEX = 0x004
        STRING = 0x008

    @staticmethod
    def __type_category__(d) -> IntFlag:
        flag = Node.Category.UNKNOWN
        if isinstance(d, (Entry)):
            flag |= Node.Category.ENTRY
        elif isinstance(d, np.ndarray):
            flag |= Node.Category.ARRAY
            if np.issubdtype(d.dtype, np.int64):
                flag |= Node.Category.INT
            elif np.issubdtype(d.dtype, np.float64):
                flag |= Node.Category.FLOAT
        elif isinstance(d, collections.abc.Mapping):
            flag |= Node.Category.DICT
        elif isinstance(d, collections.abc.Sequence):
            flag |= Node.Category.LIST
        elif isinstance(d, int):
            flag |= Node.Category.INT
        elif isinstance(d, float):
            flag |= Node.Category.FLOAT
        elif isinstance(d, str):
            flag |= Node.Category.STRING

        return flag

    def empty(self):
        return self._entry is None or (isinstance(self._entry, (collections.abc.Sequence, collections.abc.Mapping)) and len(self._entry) == 0)

    """
        @startuml
        [*] --> Empty
        Empty       --> Sequence        : as_sequence, __update__(list), __setitem__(int,v),__getitem__(int)
        Empty       --> Mapping         : as_mapping , __update__(dict), __setitem__(str,v),__getitem__(str)
        Empty       --> Empty           : clear


        Item        --> Item            : "__fetch__"
        Item        --> Empty           : clear
        Item        --> Sequence        : __setitem__(_next_,v),__getitem__(_next_),as_sequence
        Item        --> Illegal         : as_mapping

        Sequence    --> Empty           : clear
        Sequence    --> Sequence        : as_sequence
        Sequence    --> Illegal         : as_mapping

        Mapping     --> Empty           : clear
        Mapping     --> Mapping         : as_mapping
        Mapping     --> Sequence        :  __setitem__(_next_,v),__getitem__(_next_),as_sequence


        Illegal     --> [*]             : Error

        @enduml
    """
    @property
    def __category__(self):
        return Node.__type_category__(self._entry)

    def __genreric_template_arguments__(self):
        #  @ref: https://stackoverflow.com/questions/48572831/how-to-access-the-type-arguments-of-typing-generic?noredirect=1
        orig_class = getattr(self, "__orig_class__", None)
        if orig_class is not None:
            return get_args(self.__orig_class__)
        else:
            return None

    def __check_template__(self, cls):
        orig_class = getattr(self, "__orig_class__", None)
        if orig_class is not None:
            return issubclass(cls,  get_args(orig_class))
        else:
            return False

    def __new_child__(self,  *args, parent=None,  **kwargs):
        if parent is None:
            parent = self
        value = None
        if self._default_factory is not None:
            value = self._default_factory(*args,  parent=parent, ** kwargs)
        else:
            factory = self.__genreric_template_arguments__()
            if factory is not None and len(factory) > 0 and inspect.isclass(factory[0]):
                value = factory[0](*args,  parent=parent, ** kwargs)
        if value is None and len(args) > 0:
            value = args[0]

        if isinstance(value, Node):
            pass
        elif isinstance(value, collections.abc.MutableSequence):
            value = List[Node](value, *args, parent=parent, **kwargs)
        elif isinstance(value, collections.abc.MutableMapping):
            value = Dict[str, Node](value, *args, parent=parent,  **kwargs)
        elif isinstance(value, (Entry)):
            value = Node(value, *args, parent=parent, *kwargs)

        return value

    def __pre_process__(self, value, *args, **kwargs):
        return value

    def __post_process__(self, value, *args,   **kwargs):
        return value if isinstance(value, Node) else self.__new_child__(value, *args, **kwargs)

    def __fetch__(self, path=None, default_value=None):
        return self._entry.get(path or [], default_value=default_value)

    def __setitem__(self, path, value):
        self._entry.put(path, self.__pre_process__(value))

    def __getitem__(self, path):
        return self.__post_process__(self._entry.get(path))

    def __delitem__(self, path):
        if isinstance(self._entry, Entry):
            self._entry.delete(path)
        elif not path:
            self.__clear__()
        elif not isinstance(self._entry, (collections.abc.Mapping, collections.abc.MutableSequence)):
            raise TypeError(type(self._entry))
        else:
            del self._entry[path]

    def __contains__(self, path):
        if isinstance(self._entry, Entry):
            return self._entry.contains(path, None)
        elif isinstance(path, str) and isinstance(self._entry, collections.abc.Mapping):
            return path in self._entry
        elif not isinstance(path, str):
            return path >= 0 and path < len(self._entry)
        else:
            return False

    def __len__(self):
        if isinstance(self._entry, Entry):
            return self._entry.count()
        elif isinstance(self._entry,  (collections.abc.Mapping, collections.abc.MutableSequence)):
            return len(self._entry)
        else:
            return 0 if self._entry is _not_found_ else 1

    def __iter__(self):
        if isinstance(self._entry, Entry):
            for obj in self._entry.iter():
                yield self.__post_process__(obj)
        else:
            d = self._entry.get([], [])
            if isinstance(d, (collections.abc.MutableSequence)):
                yield from map(lambda v: self.__post_process__(v), d)
            elif isinstance(d, collections.abc.Mapping):
                yield from d

            else:
                yield self.__post_process__(d)

    def __eq__(self, other) -> bool:
        if isinstance(other, Node):
            other = other._entry

        if isinstance(self._entry, Entry):
            return self._entry.equal(other)
        else:
            return self._entry == other

    def __bool__(self) -> bool:
        return False if isinstance(self._entry, Entry) else (not not self._entry)


class List(MutableSequence[_TObject], Node):
    __slots__ = ()

    def __init__(self, d: collections.abc.Sequence = [], *args,  **kwargs):
        Node.__init__(self, d, *args, **kwargs)

    def __serialize__(self) -> Sequence:
        return [serialize(v) for v in self._entry._data]

    def _as_list(self) -> Sequence:
        return self.__serialize__()

    @property
    def __category__(self):
        return super().__category__() | Node.Category.LIST

    def __len__(self) -> int:
        return Node.__len__(self)

    def __new_child__(self,   *args, parent=None,  **kwargs) -> _TObject:
        return super().__new_child__(*args, parent=parent if parent is not None else self._parent, **kwargs)

    def __setitem__(self, k: _TIndex, v: _TObject) -> None:
        self._entry.put(k, self.__pre_process__(v))

    def __getitem__(self, k: _TIndex) -> _TObject:
        obj = self._entry.get(k)
        if not self.__check_template__(obj.__class__):
            obj = self.__new_child__(obj)
            if self._entry.writable:
                self._entry.put(k, obj)
        return obj

    def __delitem__(self, k: _TIndex) -> None:
        Node.__delitem__(self, k)

    def __iter__(self) -> Iterable[_TObject]:
        for idx in range(self.__len__()):
            yield self.__post_process__(self.__getitem__(idx))

    def insert(self, idx, value=None, sorted=True) -> _TObject:
        if value is None:
            value = idx
            idx = None
        if value is None:
            pass
        elif not self.__check_template__(value.__class__):
            value = self.__new_child__(value)

        if idx is not None:
            self._entry.put(idx, value)
        elif not sorted:
            self._entry.put(-1, value)
        elif isinstance(self._entry, Entry):
            data = self._entry._data
            if not isinstance(data, collections.abc.MutableSequence):
                raise NotImplementedError(f"{type(data)} is not  MutableSequence!")
            else:
                idx = bisect.bisect_right(data, value)
                data.insert(idx, value)
        else:
            raise TypeError(type(self._entry))
        return value

    def find_first(self, func):
        idx, v = next(filter(lambda t: func(t[1]), enumerate(self._entry)))
        return idx, v

    def sort(self):
        if hasattr(self._entry.__class__, "sort"):
            self._entry.sort()
        else:
            raise NotImplementedError()


class Dict(MutableMapping[_TKey, _TObject], Node):
    __slots__ = ()

    def __init__(self, data: Mapping = {}, *args,  **kwargs):
        Node.__init__(self, data, *args, **kwargs)

    def __serialize__(self, ignore=None) -> Mapping:
        cls = self.__class__
        ignore = (ignore or []) + getattr(cls, '_serialize_ignore', [])

        res = {}
        for k in filter(lambda k: k[0] != '_' and k not in ignore, self.__dir__()):
            prop = getattr(cls, k, None)
            if inspect.isfunction(prop) or inspect.isclass(prop) or inspect.ismethod(prop):
                continue
            elif isinstance(prop, cached_property):
                v = prop.__get__(self)
            elif isinstance(prop, property):
                v = prop.fget(self)
            else:
                v = getattr(self, k, None)

            if v is None or isinstance(v, (Entry)):
                continue

            res[k] = serialize(v)

        if isinstance(self._entry._data, (collections.abc.Mapping)):
            for k in filter(lambda k: k not in res and k[0] != '_', self._entry._data):
                res[k] = serialize(self._entry.get(k))
        return res
        # return {k: serialize(v) for k, v in res.items()}
        #  if isinstance(v, (int, float, str, collections.abc.Mapping, collections.abc.Sequence))}

    @classmethod
    def __deserialize__(cls, desc: Mapping):
        ids = desc.get("@ids", None)
        if ids is None:
            raise ValueError(desc)
        else:
            raise NotImplementedError(ids)

    def _as_dict(self) -> Mapping:
        return self.__serialize__()

    @property
    def __category__(self):
        return super().__category__ | Node.Category.LIST

    def get(self, key: _TKey, default_value=None) -> _TObject:
        return self.__post_process__(self._entry.get(key, default_value=default_value))

    def __getitem__(self, k: _TKey) -> _TObject:
        obj = self._entry.get(k)
        if isinstance(obj, Entry):
            obj = self.__post_process__(obj)
        elif not self.__check_template__(obj.__class__):
            obj = self.__post_process__(obj)
            # self._entry.put(k, obj)
        return obj

    def __setitem__(self, key: _TKey, value: _TObject) -> None:
        self._entry.put(key, self.__pre_process__(value))

    def __delitem__(self, key: _TKey) -> None:
        return Node.__delitem__(self, key)

    def __iter__(self) -> Iterator[Node]:
        yield from Node.__iter__(self)

    def __len__(self) -> int:
        return Node.__len__(self)

    def __eq__(self, o: object) -> bool:
        return Node.__eq__(self, o)

    def __contains__(self, o: object) -> bool:
        return Node.__contains__(self, o)

    def __ior__(self, other):
        if self._entry is None:
            self._entry = other
        elif isinstance(self._entry, Entry):
            self._entry.put(None, other)
        elif isinstance(self._entry, collections.abc.Mapping):
            for k, v in other.items():
                self.__setitem__(k, v)
        else:
            raise TypeError(f"{type(other)}")

    def __iter__(self):
        return super().__iter__()

    def __reset_cache__(self, namelist=None):
        if namelist is None:
            namelist = dir(self)

        for k in namelist:
            op = getattr(self.__class__, k, None)
            if isinstance(op, functools.cached_property) and hasattr(self, k):
                delattr(self, k)
