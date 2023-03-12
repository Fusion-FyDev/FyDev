import collections
import logging
import os
import pathlib

import netCDF4 as nc
# from scipy.io import netcdf
import numpy as np
from spdm.util.logger import logger
from spdm.util.utilities import whoami

from ..File import File
from ..Entry import Entry


class NetCDFNode(Entry):
    def __init__(self, data, *args,  **kwargs):
        super().__init__(data, *args, **kwargs)

    def _get(self, path, *args, **kwargs):
        if not path:
            return self._holder
        elif isinstance(path, str):
            path = path.split('.')

        path = self.prefix+path

        obj = self._holder

        for idx, key in enumerate(path):
            if obj is None:
                break
            elif isinstance(obj, nc.Dataset):
                obj = obj.groups.get(key, None) or obj.variables.get(key, None)
            elif isinstance(obj, nc.Group):
                obj = obj[key]
            elif isinstance(obj, nc.Variable) and (type(key) in [int, slice, tuple]):
                obj = np.array(obj[key])
            else:
                try:
                    obj = self._get_value(obj)[key]
                except Exception:
                    raise IndexError('.'.join(path[:idx+1]))
        return obj

    def _get_value(self, obj):
        if isinstance(obj, nc.Variable):
            if 'S1' in str(obj.dtype):
                obj = obj[:]
                res = obj[~obj.mask].tostring()
            else:
                res = np.array(obj)  # 　TODO: if dimension is not None , should return Profile
        elif isinstance(obj, (nc.Dataset, nc.Group)):
            res0 = {k: self._get_value(obj.variables[k]) for k in obj.variables.keys()}
            res1 = {k: self._get_value(obj.groups[k]) for k in obj.groups.keys()}
            res = {**res0, **res1}
        else:
            res = obj
        return res

    def get(self, path, *args, **kwargs):
        obj = self._get(path)
        if isinstance(obj, (nc.Group, nc.Dataset)):
            return NetCDFNode(obj)
        elif isinstance(obj, nc.Variable):
            return self._get_value(obj)
        else:
            return obj

    def get_value(self, path, *args, **kwargs):
        return self._get_value(self._get(path))

    def _update(self, grp, path, value, **kwargs):
        if grp is None:
            raise RuntimeError("None group")

        if path is None:
            raise RuntimeError(f"None path")

        if isinstance(path, str):
            path = path.split('/')

        if isinstance(value, collections.abc.Mapping):
            for k, v in value.items():
                self._update(grp, path+[k], v)
            return

        prefix = str(path.parent).replace("/", ".")

        attr_name = path.name
        if len(prefix) > 0 and prefix != '.':
            grp = grp.createGroup(prefix)
        if type(value) in [str, int, float]:
            setattr(grp, attr_name, value)
        elif not isinstance(value, np.ndarray):
            raise f"Unsupported data type {type(value)}"
        else:
            logger.debug(f"insert ndarray {value.shape} {value.dtype.str}")
            dimensions = np.linspace(len(value))
            for i in range(len(value.shape)):
                d_name = f"_{attr_name}_d{i}"
                grp.createDimension(d_name, value.shape[i])
                dimensions.append(d_name)
            data = grp.createVariable(attr_name, value.dtype.str, dimensions)
            data[:] = value

        return

    def update(self, d, *args, **kwargs):
        self._update(self._holder, [], d)

    def put(self, path, value, *args, **kwargs):
        if isinstance(path, str):
            path = pathlib.Path(path)
        return self._update(self._holder, path, value, *args, **kwargs)

    def _fetch(self, obj, path=None):
        if path is not None:
            if not isinstance(path, str):
                path = str(path).strip("/").replace("/", ".")
            try:
                return obj.getncattr(path)
            except AttributeError:
                return self._fetch(obj.get_variables_by_attributes(name=path)[0])
        elif type(obj) in [str, int, float]:
            return obj
        elif isinstance(obj, nc._nc.Variable):
            return obj[:]
        else:
            raise NotImplementedError(whoami(self))

    def do_fetch(self, path):
        if isinstance(path, str):
            path = pathlib.Path(path)
        return self._fetch(self._open(), path)

    def iter(self,  path, *args, **kwargs):
        raise NotImplementedError
        # for spath in PathTraverser(path):
        #     for child in self.xpath(spath).evaluate(self._holder):
        #         if child.tag is not _XMLComment:
        #             yield self._convert(child, path=spath)


class NetCDFFile(File):
    def __init__(self,   *args,   **kwargs):
        super().__init__(*args,   **kwargs)

    def close(self):
        if hasattr(self, "_data") and self._data is not None:
            self._data.close()
        super().close()

    @property
    def root(self):
        if self._data is None:
            self._data = nc.Dataset(self.path, self.mode)
        return NetCDFNode(self._data)


__SP_EXPORT__ = NetCDFFile
