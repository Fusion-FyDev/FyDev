'''IO Plugin of JSON '''
import json
import pathlib

import numpy
from spdm.util.logger import logger

from ..File import File


# class ndArrayEncoder(json.JSONEncoder):
#     def default(self, obj):
#         if isinstance(obj, numpy.ndarray):
#             return obj.tolist()
#         # Let the base class default method raise the TypeError
#         return json.JSONEncoder.default(self, obj)

class JSONFile(File):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read(self, *args, **kwargs):
        with self.open(mode="r") as fid:
            res = json.load(fid)
        return res

    def write(self, d, *args, **kwargs):
        with self.open(mode="w") as fid:
            json.dump(d, fid, cls=NumpyEncoder)


__SP_EXPORT__ = JSONFile
