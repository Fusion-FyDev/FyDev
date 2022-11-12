# from ..util.SpObject import SpObject
# from ..util.logger import logger

# from .Session import Session


# class Actor(SpObject):
#     @staticmethod
#     def __new__(cls, *args, **kwargs):
#         if cls is not Actor:
#             return object.__new__(cls)
#         else:
#             return SpObject.__new__(cls, *args, **kwargs)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._job_id = Session.current().job_id(self.__class__.__name__)

#     @property
#     def job_id(self):
#         return self._job_id
import collections
from functools import cached_property
from typing import Any, Generic, Mapping, TypeVar, NewType

import numpy as np
from ..util.utilities import guess_class_name
from ..data.Combiner import Combiner
from ..data.Function import Function
from ..data.Node import Dict, List, _TObject
from ..data.Profiles import Profiles
from ..data.TimeSeries import TimeSequence, TimeSeries, TimeSlice
from ..util.logger import logger
from ..util.sp_export import sp_find_module
from ..util.SpObject import SpObject
from ..util.logger import logger

from .Session import Session


class Actor(SpObject):

    _stats_ = []

    # def __new__(cls, desc=None, *args, **kwargs):
    #     prefix = getattr(cls, "_actor_module_prefix", None)
    #     n_cls = cls
    #     if cls is not Actor and prefix is None:
    #         pass
    #     elif isinstance(desc, collections.abc.Mapping):
    #         name = desc.get("code", {}).get("name", None)
    #         if name is not None:
    #             try:
    #                 n_cls = sp_find_module(f"{prefix}{name}")
    #             except Exception:
    #                 logger.error(f"Can not find actor '{prefix}{name}'!")
    #                 raise ModuleNotFoundError(f"{prefix}{name}")
    #             else:
    #                 logger.info(f"Load actor '{guess_class_name(n_cls)}'!")

    #     return object.__new__(n_cls)

    def __new__(cls, *args, **kwargs):
        if cls is not Actor:
            return object.__new__(cls)
        else:
            return SpObject.__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._time = 0
        self._prev_time = None
        self._kwargs = kwargs
        self._job_id = Session.current().job_id(self.__class__.__name__)

    @property
    def job_id(self):
        return self._job_id

    @property
    def previous_time(self) -> float:
        return self._prev_time

    @property
    def current_time(self) -> float:
        return self._time

    @property
    def previous_state(self) -> _TObject:
        def fetch(k, obj=self):
            attr = getattr(obj, k, None)
            if isinstance(attr, TimeSeries):
                attr = attr[-2]
            return attr

        return TimeSlice({"time": self.previous_time, **{k: fetch(k) for k in self._stats_}})

    @property
    def current_state(self) -> _TObject:
        def fetch(k, obj=self):
            attr = getattr(obj, k, None)
            if isinstance(attr, TimeSeries):
                attr = attr[-1]
            return attr

        return TimeSlice({"time": self.current_time, **{k: fetch(k) for k in self._stats_}})

    def advance(self, *args, time=None, dt=None,   **kwargs) -> float:
        """
            Advance the state of the Actor to the next time step.
            current -> next
        """
        self._prev_time = self.current_time
        if time is None:
            time = self.current_time+(dt or 1.0)
        self._time = time
        logger.info(f"Advance actor from {self._prev_time} to {time}. '{guess_class_name(self)}' ")
        return time

    def update(self,  *args,  **kwargs) -> bool:
        """
          Update the current state of the Actor without advancing the time.
        """
        logger.info(f"Update actor at time={self._time}. '{guess_class_name(self)}'")
        return True


_TActor = TypeVar('_TActor')


class ActorBundle(List[_TActor], Actor):

    def __init__(self, d, *args, parent=None, **kwargs):
        super(List, self).__init__(d, *args, parent=parent)
        super(Actor, self).__init__(**kwargs)

    def advance(self, *args, time=None, dt=None, **kwargs) -> float:
        time = Actor.advance(self, time=time, dt=dt)
        # TODO: Need to be parallelized
        success = [m.advance(*args, time=time, **kwargs) for m in self.__iter__()]
        return time

    def update(self, *args, **kwargs) -> float:
        # TODO: Need to be parallelized
        success = [m.update(*args, **kwargs) for m in self]
        return all(success)
