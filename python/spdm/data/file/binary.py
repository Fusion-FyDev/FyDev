'''IO Plugin of Binary '''
import json

from spdm.util.utilities import as_file_fun

__plugin_spec__ = {
    "name": "binary",
    "filename_pattern": ["*.bin"],
    "support_data_type": [int, float, str, dict, list],
    "filename_extension": "binary"

}


@as_file_fun(mode="r")
def read(fid, *args, **kwargs):
    return {}


@as_file_fun(mode="w")
def write(fid, d,  *args, **kwargs):
    pass
