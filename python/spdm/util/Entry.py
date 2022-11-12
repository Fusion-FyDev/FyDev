import collections

from .logger import logger
from .utilities import whoami


class Entry(object):
    '''The access point of map-like objects'''

    def __init__(self, *args, readable=True, writable=True, **kwargs):
        super().__init__()
        self._readable = readable
        self._writeable = writable

    # @property
    # def root(self):
    #     return Pointer(self)

    @property
    def type(self):
        return self.__class__.__name__

    @classmethod
    def deserialize(cls, *args, **kwargs):
        raise NotImplementedError(whoami(cls))

    def serialize(self):
        return {"@class": self.__class__.__name__}

    def do_fetch(self, path, *args, **kwargs):
        raise NotImplementedError(whoami(self))

    def do_update(self, path, value: any, *args, **kwargs):
        raise NotImplementedError(whoami(self))

    def do_delete(self, path, *args, **kwargs):
        raise NotImplementedError(whoami(self))

    def do_check_if(self, predicate, *args, **kwargs):
        raise NotImplementedError(whoami(self))

    def contains(self, path):
        raise NotImplementedError(whoami(self))

    def dir(self, *args, **kwargs):
        raise NotImplementedError(whoami(self))

    def flush(self, *args, **kwargs):
        raise NotImplementedError(whoami(self))

    def __delete__(self, arg):
        self.flush()

    def __getitem__(self, p):
        return self.do_fetch(p)

    def __setitem__(self, p, v):
        return self.do_update(p, v)

    def __delitem__(self, p):
        self.do_delete(p)

    def __contains__(self, p):
        return self.contains(p)

    def __dir__(self):
        return self.dir()


class OldPointer(object):
    """
        Pointer identify a value within a '''Document Object''',
        i.e. dict, collections.abc.Mapping

        example: # path
            p=Pointer()
            asssertEqual(p.a.b.c.d._path=="/a/b/c/d")

        example: # get value
            d={"a":{"b":{"c":3.14159}}}
            p=Pointer(d)
            assertEqual(  p.a.b.c._value==3.14159)

        example: # set value
            d={}
            p=Pointer(d)
            p.a=1234.5
            assertEqual(d['a']==1234.5)
    """
    DELIMITER = '/'
    SLICE_TAG_LEFT = '['
    SLICE_TAG_RIGHT = ']'
    SLICE_TAG_DELIMITER = ':'

    @classmethod
    def canonical_path(cls, *path) -> tuple:
        n_path = []
        for p in path:
            if type(p) is str:
                # TODO(salmon) parse slice and in uri template
                n_path.extend(p.split(Pointer.DELIMITER))
            else:
                n_path.append(p)

        return tuple(p for p in n_path if (p != "" and p != None))

    @classmethod
    def path_to_str(cls, p):
        if isinstance(p, str):
            return p
        elif isinstance(p, collections.abc.Sequence):
            return "[" + (",".join([cls.path_to_str(a) for a in p]))+"]"
        elif isinstance(p, slice):
            return (str(p.start) if p.start is not None else "") + ":" \
                + (str(p.stop) if p.stop is not None else "") \
                + (f":{p.step}" if p.step is not None else "")
        else:
            return str(p)

    def __init__(self, target, *prefix, eager_execution=False,
                 enable_index=False,
                 **kwargs):
        super().__init__()
        assert(isinstance(target, Entry))
        self.__dict__['_prefix'] = Pointer.canonical_path(*prefix)
        self.__dict__['_entry'] = target
        self.__dict__['_eager_execution'] = eager_execution
        self.__dict__['_enable_index'] = enable_index

    def __setattr__(self, n, v):
        return self._update(n, v)

    def __getattr__(self, p):  # pylint: disable no-member
        if not self._eager_execution:
            return self._extend(p)
        else:
            return self._fetch(p)

    def __delattr__(self, n):  # pylint: disable no-member
        return self._delete(n)

    def __repr__(self):
        path = Pointer.DELIMITER.join([self.path_to_str(p)
                                       for p in self._prefix])
        return f"<{self.__class__.__name__} path='{path}'  />"

    def __getitem__(self, path=None):
        if self._eager_execution or not self._enable_index:
            return self._fetch()[path]
        else:
            return self._extend(path)

    def __setitem__(self, path: str, value: any):
        if self._eager_execution or not self._enable_index:
            self._fetch()[path] = value
        else:
            self._update(path, value)

    def __delitem__(self, path):
        if self._eager_execution or not self._enable_index:
            del self._fetch()[path]
        else:
            return self._delete(path)

    def __contains__(self, path: str):
        if self._eager_execution or not self._enable_index:
            return path in self._fetch()
        else:
            return self._contains(path)

    def __call__(self, *args, **kwargs):
        obj = self._fetch()
        # TODO(salmon 20190720): checking obj is callable
        return obj(*args, **kwargs)

    def __dir__(self):
        return self._entry.dir()

    def __bool__(self):
        return self._entry.fetch(self._prefix, None) != None

    def __eq__(self, other):
        if not isinstance(other, Pointer):
            return self._fetch() == other
        elif self._entry == other._entry and self._prefix == other._prefix:
            return True
        else:
            return self._fetch() == other._fetch()

    def _extend(self, p):
        return self.__class__(self._entry, *self._prefix,
                              *Pointer.canonical_path(p))

    #####################################################################
    # Entry Intreface

    def _contains(self, p=None):
        return self._entry.contains(self._prefix+Pointer.canonical_path(p))

    def _fetch(self, p=None):
        return self._entry.do_fetch(self._prefix+Pointer.canonical_path(p))

    def _update(self, p,  value: any):
        return self._entry.do_update(self._prefix+Pointer.canonical_path(p),
                                     value)

    def _delete(self, p=None):
        return self._entry.do_delete(self._prefix+Pointer.canonical_path(p))

    #####################################################################

    _value = property(_fetch, _update, _delete, "value of Pointer")

    class Iterator(collections.abc.Iterator):
        def __init__(self, entry, key_iter):
            self._entry = entry
            self._key_iter = key_iter

        def __next__(self):
            k = next(self._key_iter)
            return (k, self._entry.fetch(k))

    def __iter__(self):
        p = self._fetch()
        return Pointer.Iterator(p, iter(self.dir()))


class ContainerEntry(Entry):
    '''Entry of container, i.e dict '''

    def __init__(self, origin_data=None, *args, checkAttribute=True,
                 checkItem=True, **kwargs):
        super().__init__(*args, **kwargs)
        self._data = origin_data
        self._checkAttribute = checkAttribute
        self._checkItem = checkItem

    def _try_fetch(self, current, path):

        if not isinstance(path, collections.abc.Sequence):
            path = [path]
        for idx, p in enumerate(path):
            sub = None
            if self._checkAttribute and isinstance(p, str):
                sub = getattr(current, p, None)
            if sub is None and self._checkItem and (p in current):
                sub = current[p]
            if sub is not None:
                current = sub
            else:
                return current, path[idx:]
        return current, []

    @property
    def root(self):
        return Pointer(self, eager_execution=False)

    @property
    def entry(self):
        return self._data

    @property
    def is_empty(self):
        return self._data is None

    @entry.setter
    def set_entry(self, c):
        self._data = c

    def do_fetch(self, path, default_value: any = None):
        current, r_path = self._try_fetch(self._data, path)
        return current if len(r_path) == 0 else default_value

    def do_update(self, path, value: any):
        if not self._writeable:
            raise RuntimeError(f"Not writable! path=[{path}]")
        if not isinstance(path, collections.abc.Sequence):
            path = [path]
        current, r_path = self._try_fetch(self._data, path[:-1])

        if len(r_path) > 0:
            if not isinstance(current, collections.abc.MutableMapping):
                raise ValueError(
                    f"Object is not insertable! {current} path={path}")
            for p in r_path:
                current[p] = {}
                current = current[p]

        if self._checkItem and isinstance(current, collections.abc.MutableMapping):
            current[path[-1]] = value
        elif self._checkAttribute:
            setattr(current, path[-1], value)
        else:
            raise KeyError(f"Insert value error! {path}")

    def do_delete(self, path, shallow=True):
        if not self._writeable:
            raise RuntimeError(f"Not writable! path=[{path}]")
        if not isinstance(path, collections.abc.Sequence):
            path = [path]
        current, _ = self._try_fetch(self._data, path[:-1])
        if current is None:
            pass
        elif self._checkAttribute:
            delattr(current, path[-1])
        elif self._checkItem:
            del current[path[-1]]

    def do_check_if(self, path, cond):
        return cond is None and self.contains(path)

    def contains(self, path):
        if not isinstance(path, collections.abc.Sequence):
            path = [path]
        _, r_path = self._try_fetch(self._data, path)
        return len(r_path) == 0

    def dir(self):
        return self._data.keys()


def entry(target, *args, **kwargs):
    if isinstance(target, Pointer):
        return target._extend(*args)
    elif not isinstance(target, Entry):
        return ContainerEntry(target, **kwargs).root
