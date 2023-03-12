import collections
import copy
import pathlib
import pprint
import shutil
from typing import Any, Dict

import f90nml
from spdm.util.logger import logger
from spdm.util.dict_util import normalize_data
from ..File import File


class FileNamelist(File):
    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self, data=None, *args, **kwargs):
        if data is None:
            data = kwargs
        if not isinstance(data, collections.abc.Mapping):
            super().update(data, *args, **kwargs)
        else:
            data = normalize_data(data)
            f90nml.patch(self.template.as_posix(), data, self.path.as_posix())

    def root(self) -> Dict[str, Any]:
        return Entry(f90nml.read(self.path.open(mode="r")).todict(complex_tuple=True))

    # def normalize_r(self, prefix, nobj):
    #     if isinstance(nobj, str):
    #         return nobj
    #     elif isinstance(nobj, collections.abc.Mapping):
    #         return {k: self.normalize_r(f"{prefix}.{k}", p) for k, p in nobj.items()}
    #     elif isinstance(nobj, collections.abc.Sequence):
    #         return [self.normalize_r(f"{prefix}.{k}", p) for k, p in enumerate(nobj)]
    #     elif type(nobj) not in [str, int, float, bool, type(None)]:
    #         return str(nobj)
    #     else:
    #         return nobj



__SP_EXPORT__ = FileNamelist
