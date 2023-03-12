import collections
import json

import numpy as np
from spdm.util.logger import logger

from ..File import File


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        logger.debug(type(obj))
        return super().default(obj)


class JSONFile(File):
    def __init__(self, path, *args, **kwargs):
        super().__init__(path, *args, **kwargs)

    def read(self, *args,   **kwargs):
        with open(self._path, mode="r") as fid:
            res = json.load(fid)
        return res

    def write(self,   d, *args,  **kwargs):
        with open(self._path, mode="w") as fid:
            json.dump(d, fid, cls=NumpyEncoder)


__SP_EXPORT__ = JSONFile
