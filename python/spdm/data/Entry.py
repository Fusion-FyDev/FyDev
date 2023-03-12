
import collections
import collections.abc
import pprint
from typing import (Any, Generic, Iterator, Mapping, MutableMapping,
                    MutableSequence, Sequence, TypeVar, Union, get_args)

from spdm.util.utilities import normalize_path

from ..util.logger import logger


class _TAG_:
    pass


class _NOT_FOUND_(_TAG_):
    pass


class _NEXT_TAG_(_TAG_):
    pass


class _LAST_TAG_(_TAG_):
    pass


_not_found_ = _NOT_FOUND_()
_next_ = _NEXT_TAG_()
_last_ = _LAST_TAG_()


class Entry(object):

    _DICT_TYPE_ = dict
    _LIST_TYPE_ = list

    def __init__(self, data=None,  *args, prefix=None, parent=None, writable=True,   **kwargs):
        super().__init__()
        self._data = data
        self._parent = parent
        self._prefix = normalize_path(prefix)
        self._writable = writable

    @property
    def writable(self):
        return self._writable

    @property
    def data(self):
        return self._data

    @property
    def parent(self):
        return self._parent

    @property
    def prefix(self):
        return self._prefix

    def append(self, path):
        self._prefix += normalize_path(path)

    def extend(self, path):
        res = self.__class__(self._data, prefix=self._prefix, parent=self._parent)
        res.append(path)
        return res

    def child(self, path, *args, **kwargs):
        if not path:
            return self
        else:
            return self.__class__(self._data, prefix=self._normalize_path(path), parent=self._parent)

    def copy(self, other):
        # if isinstance(other, LazyProxy):
        #     other = other.__real_value__()
        # el
        if isinstance(other, Entry):
            other = other.entry.__real_value__()

        if isinstance(other, collections.abc.Mapping):
            for k, v in other.items():
                self._data[k] = v
        elif isinstance(other, collections.abc.MutableSequence):
            self._data.extend(other)
        else:
            raise ValueError(f"Can not copy {type(other)}!")

    def __normalize_path__(self, path=None):
        if path is None:
            pass
        elif isinstance(path, str):
            path = path.split(".")
        elif not isinstance(path, collections.abc.MutableSequence):
            path = [path]
        return path

    def _normalize_path(self, path):
        if isinstance(path, str):
            path = path.split(".")
        elif not isinstance(path, collections.abc.MutableSequence):
            path = [path]
        return self._prefix + path

    # def get(self, path=[], *args, default_value=_not_found_, **kwargs):
    #     path = self._normalize_path(path)
    #     obj = self._data
    #     if obj is None:
    #         obj = self._parent
    #     for p in path:
    #         if type(p) is str and hasattr(obj, p):
    #             obj = getattr(obj, p, _not_found_)
    #         elif obj is not None:
    #             try:
    #                 obj = obj[p]
    #             except IndexError:
    #                 obj = _not_found_
    #             except TypeError:
    #                 obj = _not_found_
    #         else:
    #             raise KeyError(path)
    #     return obj

    # def put(self,  path, value, *args, **kwargs):
    #     path = self._normalize_path(path)
    #     obj = self._data
    #     if len(path) == 0:
    #         return obj
    #     for p in path[:-1]:
    #         if type(p) is str and hasattr(obj, p):
    #             obj = getattr(obj, p)
    #         else:
    #             try:
    #                 t = obj[p]
    #             except KeyError:
    #                 obj[p] = {}
    #                 obj = obj[p]
    #             except IndexError as error:
    #                 raise IndexError(f"{p} > {len(obj)}! {error}")
    #             else:
    #                 obj = t
    #         # elif type(p) is int and p < len(obj):
    #         #     obj = obj[p]
    #         # else:
    #         #     obj[p] = {}
    #         #     obj = obj[p]
    #     if hasattr(obj, path[-1]):
    #         setattr(obj, path[-1], value)
    #     else:
    #         obj[path[-1]] = value

    #     return obj[path[-1]]

    def put(self, path, value: Any = None):
        path = self._prefix+normalize_path(path)

        if len(path) == 0 and self._data is None:
            self._data = value
            return self._data

        if self._data is None:
            self._data = Entry._DICT_TYPE_() if isinstance(path[0], str) else Entry._LIST_TYPE_()

        obj = self._data

        for idx, key in enumerate(path[:-1]):

            child = Entry._DICT_TYPE_() if isinstance(path[idx+1], str) else Entry._LIST_TYPE_()

            if hasattr(obj, "_entry"):
                obj = obj._entry
            if isinstance(obj, Entry):
                obj = obj._data

            if isinstance(obj, collections.abc.MutableMapping):
                if not isinstance(key, str):
                    raise TypeError(f"mapping indices must be str, not {key}")
                tmp = obj.setdefault(key, child)
                if tmp is None:
                    obj[key] = child
                    tmp = obj[key]
                obj = tmp
            elif isinstance(obj, collections.abc.MutableSequence):
                if isinstance(key, _NEXT_TAG_):
                    obj.append(child)
                    obj = obj[-1]
                elif isinstance(key, (int, slice)):
                    tmp = obj[key]
                    if tmp is None:
                        obj[key] = child
                        obj = obj[key]
                    else:
                        obj = tmp
                else:
                    raise TypeError(f"list indices must be integers or slices, not {type(key).__name__}")

            else:
                raise TypeError(f"Can not insert data to {path[:idx]}! type={type(obj)}")

        if hasattr(obj, "_entry"):
            obj = obj._entry

        if isinstance(path[-1], _NEXT_TAG_):
            obj.append(value)
        elif isinstance(obj, (collections.abc.Mapping, collections.abc.MutableSequence)):
            obj[path[-1]] = value
        elif isinstance(obj, Entry):
            obj.put(path[-1], value)
        else:
            raise KeyError(f"[{']['.join(path)}]")

    def get(self, path: Union[str, float, slice, Sequence, None], default_value=_not_found_):
        path = self._prefix + normalize_path(path)

        obj = self._data

        for idx, key in enumerate(path):
            if hasattr(obj, "_entry"):
                obj = obj._entry.get(path[idx:])
                break

            elif isinstance(key, _NEXT_TAG_):
                obj.append(_not_found_)
                obj = Entry(obj, prefix=[len(obj)-1] + path[idx:])
                break
            elif isinstance(obj, collections.abc.Mapping):
                if not isinstance(key, str):
                    raise TypeError(f"mapping indices must be str, not {type(key).__name__}! \"{path}\"")
                tmp = obj.get(key, _not_found_)
                if tmp is _not_found_:
                    obj = Entry(obj, prefix=path[idx:])
                    break
                else:
                    obj = tmp
            elif isinstance(obj, collections.abc.MutableSequence):
                if not isinstance(key, (int, slice)):
                    raise TypeError(f"list indices must be integers or slices, not {type(key).__name__}! \"{key}\"")
                elif isinstance(key, int) and isinstance(self._data, collections.abc.MutableSequence) and key > len(self._data):
                    raise IndexError(f"Out of range! {key} > {len(self._data)}")
                obj = obj[key]

        return obj

    def get_value(self,  path=[], *args, default_value=_not_found_, **kwargs):
        return self.get(path, *args, **kwargs)

    def insert(self, path, v, *args, **kwargs):
        path = self._normalize_path(path)
        # FIXME: self._normalize_path(path)
        try:
            parent = self.get(path[:-1])
        except KeyError:
            parent = None
        idx = path[-1]
        if parent is not None and idx in parent:
            pass
        elif parent is not None and idx not in parent:
            parent[idx] = v
        elif isinstance(idx, str):
            parent = self.put(path[:-1], {})
            parent[idx] = v
        elif type(path[-1]) is int and path[-1] <= 0:
            parent = self.put(path[:-1], [])
            idx = 0
            parent[idx] = v
        logger.debug(path)
        return parent[idx]

    def update(self, path, v, *args, **kwargs):
        raise NotImplementedError()

    def delete(self, path=[], *args, **kwargs):
        path = self._normalize_path(path)

        if len(path) > 1:
            obj = self.get(path[:-1], *args, **kwargs)
        else:
            obj = self._data
        if hasattr(obj, path[-1]):
            delattr(obj, path[-1])
        else:
            del obj[path[-1]]

    def count(self,  path=[], *args, **kwargs):
        res = self.get(path, *args, **kwargs)
        if isinstance(res, (list, collections.abc.Mapping)):
            return len(res)
        else:
            return 1

    def contains(self, path, v, *args, **kwargs):
        obj = self.get(path, *args, **kwargs)
        return v in obj

    def call(self,   path=[], *args, **kwargs):
        obj = self.get(path)
        if callable(obj):
            res = obj(*args, **kwargs)
        elif len(args)+len(kwargs) == 0:
            res = obj
        else:
            raise TypeError(f"'{type(obj)}' is not callable")

        return res

    def push_back(self, path, v=None):
        parent = self.insert(path, [])
        parent.append(v or {})
        return path+[len(parent)-1]

    def pop_back(self, path):
        obj = self.get(path)
        res = None
        if obj is None:
            pass
        elif isinstance(obj, collections.abc.MutableSequence):
            res = obj[-1]
            obj.pop()
        else:
            raise KeyError(path)

        return res

    def equal(self, other) -> bool:
        obj = self.get(None)
        return (isinstance(obj, Entry) and other is None) or (obj == other)

    def __iter__(self):
        obj = self.get([])
        yield from obj

    def iter(self, path=[], *args, **kwargs):
        obj = self.get(path, *args, **kwargs)
        logger.debug(type(obj))
        if isinstance(obj, (collections.abc.Mapping or collections.abc.MutableSequence)):
            yield from obj
        elif not isinstance(obj, Entry):
            yield obj
        elif obj is not self._data:
            yield from obj.iter()
        else:
            raise NotImplementedError(type(obj))
