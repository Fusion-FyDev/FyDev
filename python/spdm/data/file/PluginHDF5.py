from ..Collection import FileCollection
from ..Document import Document
from ..Entry import Entry
import h5py
import numpy
import collections
import pathlib
from typing import (Dict, Any)
from spdm.util.logger import logger
from spdm.util.LazyProxy import LazyProxy

SPDM_LIGHTDATA_MAX_LENGTH = 128


def h5_require_group(grp, path):
    for p in path:
        if isinstance(p, str):
            pass
        elif isinstance(p, int):
            if p < 0:
                num = len(grp)
                p = p % num
            p = f"__index__{p}"

        grp = grp.require_group(p)

    return grp


def h5_put_value(grp, path, value):
    res = None
    if path is None:
        path = []
    elif type(path) is not list:
        path = [path]

    if isinstance(value, collections.abc.Mapping):
        grp = h5_require_group(grp, path)
        for k, v in value.items():
            h5_put_value(grp, [k], v)
    elif len(path) == 0:
        raise KeyError(f"Empty path!")
    else:
        grp = h5_require_group(grp, path[:-1])
        path = path[-1]

        if isinstance(path, int):
            path = f"__index__{path}"
        # elif not isinstance(path, str):
        #     raise KeyError(path)
        if path != '' and path in grp.keys():
            del grp[path]

        if type(value) is list:
            array_value = numpy.array(value)

            if array_value.dtype.type is numpy.object_:
                grp = h5_require_group(grp, path)

                grp.attrs["__is_list__"] = True

                for idx, v in enumerate(value):
                    h5_put_value(grp, idx, v)

            elif array_value.dtype.type is numpy.unicode_:
                # h5py does not support unicode string.
                array_value = array_value.astype(h5py.special_dtype(vlen=str))
                h5_put_value(grp, path, array_value)
            else:
                h5_put_value(grp, path, array_value)
        elif type(value) is numpy.ndarray and len(value) > SPDM_LIGHTDATA_MAX_LENGTH:
            grp[path] = value
        else:  # type(value) in [str, int, float]:
            grp.attrs[path] = value

    return res


def h5_get_value(obj, path=None, projection=None):
    if obj is None:
        raise RuntimeError("None group")

    prefix = []
    if path is not None:
        for p in path:
            if isinstance(p, str):
                pass
            elif isinstance(p, int):
                if p < 0:
                    num = len(grp)
                    p = p % num
                p = f"__index__{p}"

            prefix.append(p)

            if p in obj:
                obj = obj[p]
            elif p in obj.attrs:
                obj = obj.attrs[p]
            else:
                raise KeyError(f"Can not find element at {'/'.join(prefix)} !")

    if projection is None:
        if isinstance(obj, h5py.Group):
            if obj.attrs.get("__is_list__", False):
                res = [h5_get_value(obj[k]) for k in obj]
            else:
                res = {**(h5_get_value(obj.attrs)), **{k: h5_get_value(obj[k]) for k in obj}}
        elif isinstance(obj, h5py.AttributeManager):
            res = {k: h5_get_value(obj[k]) for k in obj if not k.startswith("__")}
        else:
            res = obj
    elif isinstance(projection, str):
        if isinstance(obj, h5py.Group):
            res = h5_get_value(obj.attrs, projection) or h5_get_value(obj.get(projection, None))
        elif isinstance(obj, h5py.AttributeManager):
            res = h5_get_value(obj.get(projection, None))

    elif isinstance(obj, h5py.Group):
        if obj.attrs.get("__is_list__", False):
            res = []
        else:
            res = {**h5_get_value(obj.attrs, projection),
                   **{k: h5_get_value(obj[k]) for k, v in projection.items() if v > 0 and k in obj}}
    elif isinstance(obj, h5py.AttributeManager):
        res = {k: h5_get_value(obj[k]) for k, v in projection.items() if v > 0 and k in obj}
    else:
        res = obj

    return res


class HDF5Node(Entry):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def copy(self, other):
        if isinstance(other, LazyProxy):
            other = other.__real_value__()
        elif isinstance(other, Entry):
            other = other.entry.__real_value__()
        self.put(None, other)

    def put(self, path, value, *args, **kwargs):
        return h5_put_value(self.holder, path, value)

    def get(self, path=[], projection=None, *args, **kwargs):
        return h5_get_value(self.holder, path, projection=projection)

    def iter(self,  path, *args, **kwargs):
        raise NotImplementedError()


class HDF5Document(Document):
    def __init__(self, path, *args, mode="r", **kwargs):
        super().__init__(path, *args, mode=mode, **kwargs)
        self._path = None
        if self._path is not None:
            self.load(path)

    def load(self,  path=None, *args, mode=None, **kwargs):
        if path == self._path and self.root._holder is not None:
            return

        self._path = path or self._path
        try:
            logger.debug(f"Open HDF5 File {self._path}")
            self._root = HDF5Node(h5py.File(self._path,  mode=mode or self.mode or "r"))
        except OSError as error:
            raise FileExistsError(f"Can not open file {self._path}! {error}")

    def save(self,   path=None, *args, mode=None, **kwargs):
        if (path is None or path == self._path) and isinstance(self.root._holder, h5py.File):
            self.root._holder.flush()
        elif isinstance(self.root._holder, collections.abc.Mapping):
            d = self.root._holder
            self.load(path, mode=mode or "w")
            self.copy(d)
        else:
            raise NotImplementedError()


class HDF5Collection(FileCollection):
    def __init__(self, uri, *args, **kwargs):
        super().__init__(uri, *args,
                         file_extension=".h5",
                         file_factory=lambda *a, **k: HDF5Document(*a, **k),
                         ** kwargs)


__SP_EXPORT__ = HDF5Collection
