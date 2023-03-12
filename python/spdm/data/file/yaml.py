'''IO Plugin of yaml '''
import pathlib

import yaml

from spdm.data.DataEntry import DataEntry
from spdm.util.logger import logger

from .file import FileEntry

__plugin_spec__ = {
    "name": "yaml",
    "filename_extension": "yaml",
    "filename_pattern": ["*.yaml", "*.yml"]
}


class YamlEntry(FileEntry):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read(self, *args, **kwargs):
        with self.open(mode="r") as fid:
            if fid is not None:
                res = yaml.load(fid, Loader=yaml.CLoader)
            else:
                res = None
        return res

    def write(self, d, *args, **kwargs):
        with self.open(mode="w") as fid:
            if fid is not None:
                return yaml.dump(d, fid,  Dumper=yaml.CDumper)
            else:
                return None


__SP_EXPORT__ = YamlEntry
