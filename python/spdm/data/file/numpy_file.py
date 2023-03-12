'''IO Plugin of JSON '''
import numpy
import collections
from spdm.util.logger import logger
from spdm.util.utilities import as_file_fun
import pathlib
__plugin_spec__ = {
    "name": "ndarray",
    "filename_pattern": [""],
    "support_data_type": [int, float, str, dict, list],
    "filename_extension": ".npy"

}


def read(fid, *args, **kwargs):

    if not isinstance(fid, pathlib.Path):
        fid = pathlib.Path(fid)

    fid = fid.with_suffix('.npy')
    if not fid.exists():
        logger.debug(fid)
        raise FileNotFoundError(fid)
    res = numpy.load(fid)
    # if isinstance(res, collections.abc.Sequence):
    #     res = numpy.asarray(res)
    logger.debug(type(res))
    return res


def write(fid, d,  *args, dtype=float, **kwargs):
    if not isinstance(fid, pathlib.Path):
        fid = pathlib.Path(fid)

    fid = fid.with_suffix('.npy')
    # if not fid.exists():
    #     logger.debug(fid)
    #     raise FileNotFoundError(fid)

    if isinstance(d, str):
        d = numpy.fromstring(d, dtype=dtype or float, sep=' ')
        # d = numpy.array([float(v) for v in d.split()])
    elif not isinstance(d, numpy.ndarray):
        d = numpy.array(d)

    logger.debug(d)

    numpy.save(fid.open(), d)
