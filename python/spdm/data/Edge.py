from .Node import Node
from ..util.LazyProxy import LazyProxy
from ..util.logger import logger
from ..util.utilities import _empty
from ..util.SpObject import SpObject
# from .State import SpStage, SpState
import collections
import inspect


class Edge:

    """
     Description:
            An `Edge` defines a connection between two `Port`s.
     Attribute:
            source      : the start of edge which must be `OUTPUT Port`
            target      : the start of edge which must be `INPUT Port`
            dtype       : defines what `Port`s it can be connected, (default: string)
            label       : short string
            description : long string
    """

    def __init__(self, source, target, path=None, *,
                 name=None, label=None, parent=None, attributes=None,
                 **kwargs):
        super().__init__(name=name, label=label, parent=parent, attributes=attributes)

        self._source, prefix = self._unwrap(source)

        self._target, suffix = self._unwrap(target)

        self._path = (prefix or []) + (path or []) + (suffix or [])

    @property
    def tail(self):
        return self._tail

    @property
    def head(self):
        return self._head

    def _unwrap(self, v):
        if v is None:
            return v, []
        elif isinstance(v, LazyProxy):
            return self._unwrap(v.__fetch__())
        elif hasattr(v, "output"):
            return self._unwrap(v.output)
        elif isinstance(v, Edge):
            return v._source, v._path
        else:
            return v, []

    def copy(self):
        return Edge(self._source, self._target, self._path)

    @property
    def is_linked(self):
        return self._target is not None and self._source is not None

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target

    @property
    def path(self):
        return self._path

    def __repr__(self):
        return f"""<{self.__class__.__name__} \
                    source='{getattr(self._source,'full_name',None)}' \
                    target='{getattr(self._target,'full_name',None)}' \
                    label='{self.label}'/>"""

    @property
    def label(self):
        def _str(s):
            if s is None:
                return ""
            elif type(s) is str:
                return "."+s
            elif isinstance(s, slice):
                if s.stop is None:
                    return f"[{s.start or ''}:{s.step or ''}]"
                else:
                    return f"[{s.start or ''}:{s.step or ''}:{s.stop or ''}]"

            elif isinstance(s, collections.abc.Sequence):
                return "".join([f"{_str(t)}" for t in s])
            else:
                return f"[{s}]"
        return "".join([_str(s) for s in self._path])

    def __getitem__(self, p):
        return Edge(self._source, self._target, self._path+[p])

    @classmethod
    def create(cls, *args, **kwargs):
        e = Edge(*args, **kwargs)
        return LazyProxy(e, handler=lambda s,  p:  Edge(e._source, e._target, e._path+p))

    # def fetch_by_path(self, cache, path, default_value=None, delimiter='.'):
    #     return cache.get_r([self._source.parent.id, *path.split(delimiter)], default_value)

    def check_state(self, cache,  *args,  **kwargs):
        return cache.get_r([self._source.parent.id, "state"], SpState.null)

    def fetch(self, cache,  *args,  **kwargs):

        if self._source is not None:
            res = self._source.fetch(cache, *args, **kwargs)

        if res is not _empty and len(self._path) > 0:
            res = SpBag.get_r(res, self._path, _empty)

        if res is _empty:
            raise LookupError(
                f"Can not fecth value from {self._source.full_name}")
        return res

    def split(self, *args, **kwargs):
        """
            using Slot Node split edge into chain, add In(Out)Slot not to graph

            return list of splitted edges
        """
        source = self._source
        target = self._target

        s = collections.deque([source.parent] if source is not None else [])
        t = collections.deque([target.parent] if target is not None else [])

        if getattr(s[0], "parent", None) is getattr(t[0], "parent", None):
            return self

        while s[0] is not None:
            s.appendleft(s[0].parent)

        while t[0] is not None:
            t.appendleft(t[0].parent)

        s_rank = len(s)
        t_rank = len(t)
        pos = s_rank-2
        tag = ""
        while pos >= t_rank or (pos >= 0 and s[pos] is not t[pos]):
            tag = f"{tag}_{source.parent.name}"

            s[pos].slot[tag] = source

            source = s[pos].port[tag]

            pos = pos - 1

        tag = f"{tag}_{source.parent.name}"

        while pos < t_rank-2:
            pos = pos+1
            tag = f"{tag}_{source.parent.parent.name}"
            t[pos].port[tag] = source

            source = t[pos].slot[tag]

        src, prefix = self._unwrap(source)
        self._source = src
        self._path = prefix+self._path
        return self

    def remove_chain(self):
        raise NotImplementedError(self.__class__)
