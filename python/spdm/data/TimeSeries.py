import collections
from typing import (Any, Generic, Mapping, MutableMapping, Sequence, TypeVar,
                    Union)

import numpy as np

from ..util.logger import logger
from .AoS import AoS, SoA
from .Node import Dict, List, _TIndex, _TKey, _TObject


class TimeSequence(list):
    def __init__(self, time_start=0.0, time_step=1.0) -> None:
        super().__init__([time_start])
        self._time_step = time_step

    @property
    def current(self):
        return self[-1]

    @property
    def previous(self):
        return self[-2] if len(self) > 1 else None

    @property
    def next(self):
        return self[-1] + self._time_step

    def advance(self, time=None, dt=None):
        if time is None:
            time = (self.previous or 0.0) + (dt if dt is not None else self._time_step)
        elif self.previous is not None and time <= self.previous:
            raise RuntimeError(f"Time can't go back!")
        self.append(time)
        return time


class TimeSlice(Dict):
    r"""
        Time Slice
        - collection of property at same time point
        - collection of property interpolation at same time
    """
    __slots__ = ("_time")

    def __init__(self, *args, time: float = None,   **kwargs) -> None:
        Dict.__init__(self, *args, **kwargs)
        if time is None:
            time = self["time"] or -np.inf
        self._time = time

    @property
    def time(self) -> float:
        return self._time

    def __serialize__(self):
        res = super().__serialize__()
        res["time"] = self.time
        return res

    def __lt__(self, other):
        if isinstance(other, float):
            return self._time < other
        elif isinstance(other, TimeSlice):
            return self._time < other._time
        else:
            return False
            # raise TypeError(type(other))


class TimeSeries(List[_TObject]):
    r"""
        Time Series
        - the collestion of propertis' time series . SOA (structure of array)
        - time series of the collection of properties  AOS (array of structure)
    """
    __slots__ = ("_time_step", "_time_start", "_roll")

    def __init__(self, d, *args, time_start=None, time_step=None, roll=-1, **kwargs) -> None:
        super().__init__(d or [], *args, **kwargs)
        self._time_start = time_start or 0.0
        self._time_step = time_step or 1.0
        self._roll = roll

    @property
    def time(self) -> np.ndarray:
        return np.asarray([t_slice.time for t_slice in self])

    def last_time(self):
        if len(self) == 0:
            return self._time_start
        else:
            return float(self[-1].time)

    def next_time(self, dt=None):
        if len(self) == 0:
            return self._time_start
        else:
            return float(self[-1].time) + (dt or self._time_step)

    def __getitem__(self, k: _TIndex) -> _TObject:
        obj = self._entry.get(k)

        if not self.__check_template__(obj.__class__):
            n = len(self)
            obj = self.__new_child__(obj, time=self._time_start+((k+n) % n)*self._time_step)
            self._entry.put(k, obj)
        return obj

    def __setitem__(self, k: _TIndex, obj: Any) -> _TObject:
        return self.insert(k, obj)

    def insert(self,  *args, time=None, **kwargs) -> _TObject:
        return super().insert(self.__new_child__(*args, time=time or self.next_time(),  **kwargs))

    def push_back(self,  *args, time=None, **kwargs):
        if len(args) > 0 and self.__check_template__(args[0].__class__):
            super().insert(args[0])
        else:
            if time is None:
                time = self.next_time()
            return super().insert(self.__new_child__(*args, time=time, **kwargs))

    def next(self, *args, time=None, dt=None, **kwargs):
        if time is None:
            time = self.next_time(dt)
        if self.empty():
            return self.push_back(*args, time=time, **kwargs)
        else:
            return self.insert(self[-1].__duplicate__(*args, time=time, **kwargs))

    @property
    def prev(self):
        if len(self) > 1:
            raise RuntimeError()
        return self[-2]

    @property
    def last(self):
        if len(self) == 0:
            raise RuntimeError()
        return self[-1]

    def __call__(self, time: float = None) -> _TObject:
        r"""
            Time Interpolation of slices
        """

        if len(self) == 0:
            raise RuntimeError("Empty!")

        if time is None:
            t_slice = self[-1]
        else:
            try:
                idx, t_slice_next = self.find_first(lambda t_slice: t_slice.time >= time)
            except Exception:
                raise RuntimeError(f"Out of range! {self[-1].time} < {time}")
            else:
                if t_slice_next.time > time:
                    t_slice_prev = self[idx-1]
                    logger.debug(f"Time interpolation {t_slice_prev.time} < {time} < {t_slice_next.time}")
                    raise NotImplementedError()
                else:
                    t_slice = t_slice_next
        return t_slice
