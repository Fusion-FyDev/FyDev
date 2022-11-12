from typing import Mapping, TypeVar, Any
from collections import OrderedDict
from .logger import logger
ST = TypeVar('ST')
DT = TypeVar('DT')


class BiMap(OrderedDict, Mapping[ST, DT]):

    def __init__(self, init_value=None, *args, **kwargs):
        super(OrderedDict, self).__init__(*args, **kwargs)
        self._inv_map = OrderedDict()
        for k, v in (init_value or {}).items():
            super().__setitem__(k, v)
            self._inv_map[v] = k

    def check_key_type(self, key):
        return isinstance(key, self.__orig_class__.__args__[0])

    def inv_map(self, v):
        if self.check_key_type(v):
            return v
        else:
            return self._inv_map[v]

    def to_dest(self, k):
        if not self.check_key_type(k):
            return k
        else:
            return super().__getitem__(k)

    def __getitem__(self, s: [ST, DT]):
        return self.to_dest(s)

    def __setitem__(self, s: ST, d: DT):
        super().__setitem__(s, d)
        self._inv_map[d] = s

    def __delitem__(self, s: ST):
        v = super().__getitem__(s)
        del self._inv_map[v]
        super().__delitem__(s)
