
import collections
import logging
import os
import pathlib
import re
import uuid
from functools import reduce
from typing import Any, Dict

import h5py
import numpy

from ..File import File
from ..Entry import Entry

from spdm.util.logger import logger
from spdm.util.utilities import whoami


class HDF5Node(Entry):

    def __init__(self, holder,  *args, mode="w", **kwargs):
        super().__init__(holder,  *args, **kwargs)

    def _insert(self, grp, path, value, **kwargs):
        if grp is None:
            raise RuntimeError("None group")
        if isinstance(path, str):
            path = path.split('/')

        if not path:
            if isinstance(value, collections.abc.Mapping):
                for k, v in value.items():
                    self._insert(grp, [k], v, **kwargs)
            elif isinstance(value, list):
                raise NotImplementedError()
            elif not path:
                raise RuntimeError(f"Empty path!")
        elif len(path) > 1:
            return self._insert(grp.require_group('/'.join(path[:-1])), path[-1:], value, **kwargs)
        else:
            path = path[0]

        if path in grp.keys() and path != '/':
            del grp[path]

        if type(value) in [str, int, float]:
            grp.attrs[path] = value
        elif type(value) is list:
            value = numpy.array(value)
            # h5py does not support unicode string.
            if value.dtype.type is numpy.unicode_:
                value = value.astype(h5py.special_dtype(vlen=str))

            if len(value) < SPDM_LIGHTDATA_MAX_LENGTH:
                grp.attrs[path] = value
            else:
                grp[path] = value

        elif type(value) is dict:
            g = grp.require_group(path)
            for k, v in value.items():
                self._insert(g, k, v)
        elif type(value) is numpy.ndarray:
            grp[path] = value
        else:
            raise RuntimeError(f"Unsupported data type {type(value)}")
        return

    def _fetch(self, obj, projection=None):
        if not projection:
            if isinstance(obj, h5py.Group):
                return {**self._fetch(obj.attrs),
                        **{k: self._fetch(obj[k]) for k in obj}}
            elif isinstance(obj, h5py.AttributeManager):
                return {k: self._fetch(obj[k]) for k in obj}
            else:
                return obj
        elif isinstance(projection, collections.abc.Mapping):
            if isinstance(obj, h5py.Group):
                return {**self._fetch(obj.attrs, projection),
                        **{k: self._fetch(obj[k])
                           for k, v in projection.items() if v > 0 and k in obj}}
            elif isinstance(obj, h5py.AttributeManager):
                return {k: self._fetch(obj[k])
                        for k, v in projection.items() if v > 0 and k in obj}
        elif isinstance(projection, str):
            return self._fetch(obj, projection.split('/'))
        elif not isinstance(projection, list):
            raise TypeError(type(projection))
        elif len(projection) > 1:
            return self._fetch(obj.get('/'.join(projection[:-1])), projection[-1:])
        else:
            key = projection[0]
            if isinstance(obj, h5py.Group):
                return self._fetch(obj.attrs, key) \
                    or self._fetch(obj.get(key, None))
            elif isinstance(obj, h5py.AttributeManager):
                return self._fetch(obj.get(key, None))

    def update(self, d: Dict[str, Any]):
        return self._insert(self._holder, "/", d)

    # def fetch_if(self,
    #              projection: Dict[str, Any],
    #              predicate: Dict[str, Any] = None):
    #     raise NotImplementedError(whoami(self))

    # def update_if(self,
    #               update: Dict[str, Any],
    #               predicate: Dict[str, Any] = None):
    #     raise NotImplementedError(whoami(self))

    def put(self, path, value, *args, **kwargs):
        return self._insert(self.holder, path, value, *args, **kwargs)

    def get(self, path, *args, **kwargs):
        data = self._fetch(self._holder, path, *args, **kwargs)
        if isinstance(data, h5py.Dataset):
            data = data[()]  # TODO:if  data has attributes return   Profile
        return data


class HDF5File(File):
    model_map = {
        "r": "r",
        "rw": "r+",
        "w": "w",
        "w-": "w-",
        "x": "x",
    }

    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)

    def close(self):
        if self._data is not None:
            self._data.close()
        super().close()

    @property
    def root(self):
        if self._data is None:
            self._data = h5py.File(self.path, mode=HDF5File.model_map.get(self.mode, "r"))
        return HDF5Node(self._data, mode=self.mode)


__SP_EXPORT__ = HDF5File
