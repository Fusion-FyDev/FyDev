import collections
import functools
import importlib
import inspect
import io
import json
import os
import pathlib
import pkgutil
import pwd
import re
import sys
import re
from .logger import logger
import numpy as np
import collections.abc


class _Empty:
    pass


_empty = _Empty()


def whoami(obj=None):
    cls = getattr(obj, "__class__", None)
    if cls is not None:
        return f"{cls.__name__}.{inspect.stack()[1][3]}"
    else:
        return inspect.stack()[1][3]


def getitem(obj, key=None, default_value=None):
    if key is None:
        return obj
    elif hasattr(obj, "__get__"):
        return obj.__get__(key, default_value)
    elif hasattr(obj, "__getitem__"):
        return obj.__getitem__(key) or default_value
    else:
        return default_value


def setitem(obj, key, value):
    if hasattr(obj, "__setitem__"):
        return obj.__setitem__(key, value)
    else:
        raise KeyError(f"Can not setitem {key}")


def iteritems(obj):
    if obj is None:
        return []
    elif isinstance(obj, collections.abc.Sequence):
        return obj
    elif isinstance(obj, collections.abc.Mapping):
        return obj.items()
    else:
        raise TypeError(f"Can not apply 'iteritems' on {type(obj)}!")


def get_cls_file_path(cls):
    return pathlib.Path(inspect.getfile(cls)).parent


def load_pkg_data(pkgname, path):
    data = pkgutil.get_data(pkgname, path)
    return json.loads(data.decode("utf-8"))


def try_getattr_r(obj, path: str):
    if path is None or path == '':
        return obj, ''
    start = 0
    path = path.strip(".")
    s_len = len(path)
    while start >= 0 and start < s_len:
        pos = path.find('.', start)
        if pos < 0:
            pos = s_len
        if not hasattr(obj, path[start:pos]):
            break
        obj = getattr(obj, path[start: pos])
        start = pos+1
    return obj, path[start:]


def getattr_r(obj, path: str):
    # o, p = try_getattr_r(obj, path)

    # if p != '':
    #     raise KeyError(f"Can for find path {path}")
    if type(path) is str:
        path = path.split('.')

    o = obj
    for p in path:
        o = getattr(o, p, None)
        if o is None:
            break
            # raise KeyError(f"Can not get attribute {p} from {o}")
    return o


def try_get(holder, path, default_value=None):
    path = normalize_path(path)
    obj = holder

    for k in path:
        if isinstance(k, str):
            op = getattr(obj.__class__, k, None)
        else:
            op = None
        if op is None:
            try:
                obj = obj.__getitem__(k)
            except KeyError:
                data = default_value
            except IndexError as error:
                raise IndexError(f"{k} > {len(obj)} Error: {error}")

        elif isinstance(op, functools.cached_property):
            obj = op.__get__(obj)
        elif isinstance(data, property):
            obj = op(data, "fget")(obj)
        else:
            obj = default_value

    return obj


def try_put(holder, path,  value):
    res = None
    if isinstance(path, str):
        res = getattr(holder.__class__, path, None)
    if res is None:
        holder.__setitem__(path, value)
    elif isinstance(res, property):
        getattr(res, "fset")(holder, path, value)
    else:
        raise KeyError(f"Can not set attribute {value}!")

    # def try_getitem_r(obj, path):
    #     if path is None or path == '':
    #         return obj, ''
    #     start = 0
    #     path = path.strip(".")
    #     s_len = len(path)
    #     while start >= 0 and start < s_len:
    #         pos = path.find('.', start)
    #         if pos < 0:
    #             pos = s_len
    #         if isinstance(obj, collections.abc.Mapping) and path[start:pos] in obj:
    #             obj = obj.get(path[start: pos])
    #             start = pos+1
    #         else:
    #             break
    #     return obj, path[start:]

    # def getitem_r(obj, path: str):
    #     o, p = try_getitem_r(obj, path)
    #     if p != '':
    #         raise KeyError(f"Can for find path {path}")
    #     return o


def normalize_path(path):
    if path is None:
        path = []
    elif isinstance(path, str):
        path = path.split('.')
    elif not isinstance(path, collections.abc.MutableSequence):
        path = [path]
    return path


def serialize(d):
    if hasattr(d.__class__, "__serialize__"):
        return d.__serialize__()
    elif isinstance(d, (int, float, str)):
        return d
    elif isinstance(d, np.ndarray):
        return d.copy()
    elif hasattr(d, "_as_dict"):
        return d._as_dict()
    elif hasattr(d, "__array__"):  # numpy.ndarray like
        return d.__array__()
    elif isinstance(d, collections.abc.Mapping):
        return {k: serialize(v) for k, v in d.items()}
    elif isinstance(d, collections.abc.Sequence):
        return [serialize(v) for v in d]
    else:
        # logger.warning(f"Can not serialize {d.__class__.__name__}!")
        return f"<{d.__class__.__name__}>NOT SERIALIZABLE!</{d.__class__.__name__}>"
        # raise TypeError(f"Can not serialize {type(d)}!")


def as_file_fun(func=None,  *f_args, **f_kwargs):
    """ Function wrapper: Convert  first argument (as file path) to File object
    TODO salmon (20190915): specify the position/key of the file path argument
    """
    def _decorate(wrapped):
        @functools.wraps(wrapped)
        def _wrapper(fp, *args, **kwargs):
            if isinstance(fp, str):
                with open(fp, *f_args, **f_kwargs) as fid:
                    res = wrapped(fid, *args, **kwargs)
            elif isinstance(fp, pathlib.Path):
                with fp.open(*f_args, **f_kwargs) as fid:
                    res = wrapped(fid, *args, **kwargs)
            elif isinstance(fp, io.IOBase):
                res = func(fp, *args, **kwargs)
            else:
                raise TypeError(
                    f"Can not convert type({type(fp)}) to file-like object!")

            return res
        return _wrapper

    if func is None:
        return _decorate
    else:
        return _decorate(func)


def as_lazy_object(func,  *f_args, **f_kwargs):
    def _decorate(wrapped):
        @functools.wraps(wrapped)
        def _wrapper(*args, **kwargs):
            def fun():
                return wrapped(*args, **kwargs)
            return LazyProxy(fun)
        return _wrapper

    if func is None:
        return _decorate
    else:
        return _decorate(func)


def getlogin():
    try:
        return os.getlogin()
    except Exception:
        return pwd.getpwuid(os.getuid())[0]


def get_username():
    return getlogin()


def _gusses_name(self, name_hint):
    count = sum(1 for k, v in self._graph.nodes.items()
                if k == name_hint or k.startswith(f"{name_hint}_"))
    if count > 0:
        name_hint = f"{name_hint}_{count}"
    return name_hint


def _try_insert(self, name_hint, node):
    return self.add_node(node, label=self._gusses_name(name_hint or node.__class__.__name__.lower()))


def compile_regex_pattern(pattern):
    try:
        res = re.compile(pattern)
    except re.error:
        res = None
    finally:
        return res


def as_namedtuple(d: dict, name=""):
    return collections.namedtuple(name, d.keys())(d.values())


def first_not_empty(*args):
    return next(x for x in args if len(x) > 0)


def convert_to_named_tuple(d=None, ntuple=None, **kwargs):
    if d is None and len(kwargs) > 0:
        d = kwargs
    if d is None:
        return d
    elif hasattr(ntuple, "_fields") and isinstance(ntuple, type):
        return ntuple(*[try_get(d, k) for k in ntuple._fields])
    elif isinstance(d, collections.abc.Mapping):
        keys = [k.replace('$', 's_') for k in d.keys()]
        values = [convert_to_named_tuple(v) for v in d.values()]
        if not isinstance(ntuple, str):
            ntuple = "__"+("_".join(keys))
        ntuple = ntuple.replace('$', '_')
        return collections.namedtuple(ntuple, keys)(*values)
    elif isinstance(d, collections.abc.MutableSequence):
        return [convert_to_named_tuple(v) for v in d]
    else:
        return d


def guess_class_name(obj):

    if not inspect.isclass(obj):
        cls = obj.__class__
        cls_name = getattr(obj, "__orig_class__", None)
    else:
        cls = obj
        cls_name = None

    return cls_name or f"{cls.__module__}.{cls.__name__}"
