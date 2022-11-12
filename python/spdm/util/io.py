import collections
import json
import pathlib
from urllib.request import urlopen

import requests
import yaml
import json5
from .logger import logger
from .sp_export import sp_pkg_data_path
from .urilib import urisplit
from .dict_util import deep_merge_dict
FAIL_SAFE = None
ENABLE_REMOTE = False


def write(path, content, force=True):
    success = True
    o = urisplit(path)
    if o.schema in ["local", "file", None]:
        p = pathlib.Path(o.path)
        if not p.parent.exists():
            p.parent.mkdir(exists_ok=force, parents=True)
        with p.open(mode="w") as fid:
            if o.path.endswith(".yaml"):
                yaml.dump(content, fid,  Dumper=yaml.CDumper)
            elif o.path.endswith(".json"):
                json.dump(content, fid)
            else:
                success = False
    if not success:
        raise RuntimeError(f"Can not write  {path}")
    # else:
    #     raise NotImplementedError(f"Can not write {path}")


def _read(uri, **kwargs):
    content = None
    path = []
    if isinstance(uri, pathlib.PosixPath):
        path = [uri]
    else:
        o = urisplit(uri)
        if o.schema in [None, 'file', 'local']:
            path = [pathlib.Path(o.path).expanduser()]
        elif o.schema in ['pkgdata']:
            pkg = str(o.authority) or __package__.split('.')[0]
            if pkg:
                path = sp_pkg_data_path(pkg, o.path[1:])
        elif o.schema in ['http', 'https'] and ENABLE_REMOTE:
            content = requests.get(uri).json()

    for p in path:
        if not p.is_file():
            continue
        elif p.suffix in (".json", ".yaml", ''):
            with p.open() as fid:
                content = yaml.load(fid, Loader=yaml.FullLoader)
                break
        else:
            raise NotImplementedError(f"Unknown file type {p}")

    if content is None and FAIL_SAFE is not None:
        content = FAIL_SAFE(uri).read()
    return content


def read(path, **kwargs):
    if isinstance(path, (str, pathlib.Path)):
        path = [path]
    elif not isinstance(path, collections.abc.Sequence):
        raise TypeError(f"Type of path should be a string, Path or list of string/Path!")
    content = {}
    for p in path:
        deep_merge_dict(content, _read(p))

    return content


def glob(n_uri):

    o = urisplit(n_uri)
    path_list = []
    prefix, suffix = o.path.split('%_PATH_%')
    if o.schema in [None, 'file', 'local']:
        path_list = [prefix]
    elif o.schema in ['pkgdata']:
        path_list = [p for p in sp_pkg_data_path(
            o.authority or __package__.split('.', 1)[0], prefix)]

    for p in path_list:
        p = pathlib.Path(p)
        for f in p.rglob(f"**/*{suffix}"):
            fp = f.as_posix()
            name = fp[len(p.as_posix()):len(fp)-len(suffix)]
            yield name, f

    if len(path_list) == 0 and FAIL_SAFE is not None:
        handler = FAIL_SAFE(n_uri)
        if handler is not None:
            for p, f in handler.glob():
                yield p, f
