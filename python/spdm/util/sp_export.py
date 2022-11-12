import collections
import functools
import importlib
import inspect
import os
import pathlib
import sys
import pkgutil
from .logger import logger
from .utilities import getattr_r

SP_EXPORT_KEYWORD = "__SP_EXPORT__"


def export(fn):
    logger.debug((fn.__name__, fn.__package__))
    mod = sys.modules[fn.__module__]
    if hasattr(mod, '__all__'):
        mod.__all__.append(fn.__name__)
    else:
        mod.__all__ = [fn.__name__]
    return fn


def sp_load_module(filepath, name=None, export_entry: str = None):
    if isinstance(filepath, str):
        filepath = pathlib.Path(filepath)
    name = name or filepath.stem
    logger.debug((name, filepath))
    return lambda p: p


def sp_find_module(path, fragment=None, pythonpath=None):
    if path is None:
        return None
    if not isinstance(path, str) and isinstance(path, collections.abc.Sequence):
        path = ".".join(path)

    o = path.strip('/.').replace('/', '.').split('#')

    mod_name = o[0]
    if fragment is None and len(o) > 1:
        fragment = o[1]

    module = sys.modules.get(mod_name, None)  # if module is loaded, use it

    if module is None:
        if not pythonpath:
            try:
                spec = importlib.util.find_spec(mod_name)
            except ModuleNotFoundError:
                spec = None
        else:
            if isinstance(pythonpath, str):
                pythonpath = pythonpath.split(':')
            for p in pythonpath:
                mod_path = pathlib.Path(p) / mod_name.replace('.', '/')
                if mod_path.is_dir():
                    mod_path = mod_path/"__init__.py"
                else:
                    mod_path = mod_path.with_suffix(".py")

                if not(mod_path.exists() and mod_path.is_file()):
                    continue
                try:
                    spec = importlib.util.spec_from_file_location(mod_name, mod_path)
                except ModuleNotFoundError:
                    spec = None
                else:
                    if spec is not None:
                        break

        if spec is not None:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

    if not isinstance(module, object):
        raise ModuleNotFoundError(f"{path}")

    if fragment is None:
        module = getattr(module, SP_EXPORT_KEYWORD, None) or getattr(module, path.split('.')[-1], None) or module
    elif hasattr(module, fragment):
        module = getattr(module, fragment)
    elif hasattr(module, SP_EXPORT_KEYWORD):
        module = getattr(getattr(module, SP_EXPORT_KEYWORD), fragment, None)
    else:
        module = None

    return module


def sp_find_subclass(cls, path: list):
    if len(path) == 0:
        return cls
    if not hasattr(cls, "__subclasses__"):
        return None

    for sub in cls.__subclasses__():
        if getattr(sub, "__name__", None) == path[0]:
            return sp_find_subclass(sub, path[1:])
    return None


def sp_pkg_data_path(pkg, rpath):
    if type(pkg) is str:
        pkg = sys.modules.get(pkg, None)

    plist = []
    if hasattr(pkg, "__path__"):  # check namespace package
        plist = pkg.__path__
    elif hasattr(pkg, "__file__"):  # check normal package
        plist = [pkg.__file__]
        yield pkgutil.get_data(pkg, rpath)
    # else:
    #     # raise ModuleNotFoundError(f"Module '{pkg}' is not loaded!")
    #     # return
    #     plist = []

    for p in plist:
        np = pathlib.Path(p)/rpath
        if np.exists():
            yield np


def make_canonical_path_dot(path):
    if isinstance(path, str):
        path = path.replace("/", ".").strip(".")
    elif isinstance(path, collections.abc.Sequence):
        path = ".".join([p for p in path if p is not None])
    else:
        raise KeyError(f"Illegal path {path}")
    return path


def make_canonical_path_slash(path):
    if isinstance(path, str):
        path = path.replace(".", "/")
    elif isinstance(path, collections.abc.Sequence):
        path = "/".join([p for p in path if p is not None])
    else:
        raise KeyError(f"Illegal path {path}")
    return path


def make_canonical_path_list(path):
    if not isinstance(path, collections.abc.Sequence):
        path = [path]

    new_path = []
    for p in path:
        if isinstance(p, str):
            new_path.extend(p.split("/"))
        else:
            new_path.append(p)

    return [p for p in new_path if p is not None]


def absoluate_path_dot(path, prefix):
    if isinstance(path, str):
        path = path.split('.')
    if isinstance(prefix, str):
        prefix = prefix.split('.')

    if path[0] == '':
        path = prefix.append(path)

    return ".".join([p for p in path if p != ''])


def absoluate_path_slash(path, prefix):
    if isinstance(path, str):
        path = path.split('/')
    if isinstance(prefix, str):
        prefix = prefix.split('/')

    logger.debug((path, prefix))
    if path[0] != '':
        path = prefix.append(path)

    logger.debug(path)

    return "/"+"/".join([p for p in path if p != ''])


def relativce_module_path(cls, base):
    return [p.__name__.lower()
            for p in inspect.getmro(cls) if issubclass(p, base) and p is not base and p is not cls][:: -1]+[cls.__name__]
