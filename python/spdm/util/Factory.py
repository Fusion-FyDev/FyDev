import collections
import copy
import functools
import inspect
import pprint
import os
import re
from functools import lru_cache
from .Alias import Alias
from .logger import logger
from .sp_export import sp_find_module
from .SpObject import SpObject
from .urilib import urijoin, urisplit
from .utilities import iteritems, whoami
from .dict_util import format_string_recursive


class Factory(object):
    """ Convert schema to class
    """

    def __init__(self, *args, module_prefix=None, resolver=None, handlers=None, ** kwargs):
        super().__init__()
        self._resolver = resolver
        self._cache = {}
        self._handlers = {self._resolver.normalize_uri(k): v for k, v in handlers or {}}

        if module_prefix is None:
            module_prefix = []
        elif isinstance(module_prefix, str):
            module_prefix = [module_prefix]

        self._module_prefix = [*module_prefix, f"{__package__}", ""]

    @property
    def resolver(self):
        assert(self._resolver is not None)
        return self._resolver

    def insert_handler(self, k, v=None):
        if v is None and hasattr(k, "__class__"):
            v = k
            k = k.__class__.__name__

        self._handlers[self._resolver.normalize_uri(k)] = v

    def find_handler(self, k):
        return self._handlers.get(self._resolver.normalize_uri(k), None)

    def remove_handler(self, k):
        k = self._resolver.normalize_uri(k)
        if k in self._handlers:
            del self._handlers[k]

    @property
    def handlers(self):
        return self._handlers

    def create(self, metadata=None, *args, **kwargs):
        """ Create a new class from metadata
            Parameters:
                metadata: metadata of class
        """
        if isinstance(metadata, collections.abc.Sequence):
            metadata = {"$id": ".".join(metadata)}

        if isinstance(metadata, str):
            metadata = {"$id": metadata}

        metadata = collections.ChainMap(metadata or {}, kwargs)

        cls_id = metadata.get("$id", "")

        if self._resolver is not None:
            cls_id = self._resolver.normalize_uri(cls_id)
            metadata["$id"] = cls_id

        n_cls = self._cache.get(cls_id, None)

        if n_cls is not None:
            return n_cls

        metadata = self._resolver.fetch(metadata)

        schema_id = metadata.get("$schema", "")

        n_cls = self._handlers.get(schema_id, None)

        if n_cls is None:
            mod_path = self._resolver.remove_prefix(schema_id).replace('/', '.')

            for prefix in self._module_prefix:
                n_cls = sp_find_module(mod_path if not prefix else f"{prefix}.{mod_path}")
                if n_cls is not None:
                    break
            if n_cls is None:
                raise LookupError(f"Can not find module {schema_id}!")

        if inspect.isclass(n_cls):
            n_cls_name = self._resolver.remove_prefix(cls_id)
            n_cls_name = re.sub(r'[-\/\.\:]', '_', n_cls_name)
            # n_cls_name = f"{n_cls.__name__}_{n_cls_name}"
            n_cls = type(n_cls_name, (n_cls,), {"_metadata": {**metadata}})

        return self._cache.setdefault(cls_id, n_cls)

    # def create(self, *args, ** kwargs):
    #     # key starts with '_' are resevered for classmethod new_class
    #     c_kwargs = {}
    #     o_kwargs = {}
    #     for k, v in kwargs.items():
    #         if k.startswith("_"):
    #             c_kwargs[k[1:]] = v
    #         else:
    #             o_kwargs[k] = v

    #     return self._create_from((args, o_kwargs), **c_kwargs)

    # def _create_from(self, init_args=None, *_args, **_kwargs):
    #     if len(_args) > 0 or len(_kwargs) > 0:
    #         cls = cls.new_class(*_args, **_kwargs)

    #     args = []
    #     kwargs = {}
    #     if init_args is None:
    #         pass
    #     elif isinstance(init_args, collections.abc.Mapping):
    #         kwargs = init_args
    #     elif isinstance(init_args, list):
    #         args = init_args
    #     elif isinstance(init_args, tuple):
    #         args, kwargs = init_args
    #     else:
    #         args = [init_args]

    #     return cls(*args, **kwargs)

    # def expand(self, spec, level_of_expanding=0):
    #     if isinstance(spec, collections.abc.Mapping) and "$schema" in spec:
    #         return self.create(spec)
    #     elif level_of_expanding <= 0:
    #         return spec
    #     elif isinstance(spec, collections.abc.Mapping):
    #         return {k: self.expand(v, level_of_expanding-1)
    #                 if k[0] != '@' and k[0] != '$' else v for k, v in spec.items()}
    #     elif not isinstance(spec, str) and isinstance(spec, collections.abc.Sequence):
    #         return [self.expand(v, level_of_expanding-1) for v in spec]
    #     else:
    #         return spec

    # def validate(self, spec, schema=None):
    #     if self._validater is None:
    #         # logger.warning("Validator is not defined!")
    #         return

    #     if isinstance(spec, collections.abc.Mapping):
    #         schema = schema or spec.get("$schema", None)

    #     if isinstance(schema, str):
    #         schema = {"$ref": schema}
    #     try:
    #         self._validater.validate(spec, schema)
    #     except Exception as error:
    #         raise error
    #     else:
    #         logger.info(f"Validate schema '{spec.get('$schema')}' ")
#  @classmethod
#     def new_class(cls,  desc=None, *args, ** kwargs):

#         description = (getattr(cls, "_description", {}))

#         if desc is None and len(kwargs) == 0:
#             return cls
#         elif isinstance(desc, str):
#             desc = {"$id": desc}

#         description.__update__(desc)
#         description.__update__(kwargs)

#         # if factory is not None:
#         #     description = factory.resolver.fetch(description)

#         # if not base_class:
#         #     base_class = cls
#         # elif factory is not None:
#         #     base_class = factory.new_class(base_class)
#         # else:
#         #     base_class = cls
#         # base_class = description["$base_class"]

#         o = urisplit(description["$id"] or f"{cls.__name__}_{uuid.uuid1().hex}")
#         n_cls_name = f"{o.authority.replace('.', '_')}_" if o.authority is not None else ""

#         path = re.sub(r'[-\/\.]', '_', o.path)

#         n_cls_name = f"{n_cls_name}{path}"

#         n_cls = type(n_cls_name, (cls,), {"_description": (description)})

#         return n_cls

#     @classmethod
#     def create(cls, *args,  ** kwargs):
#         # key starts with '_' are resevered for classmethod new_class
#         c_kwargs = {}
#         o_kwargs = {}
#         for k, v in kwargs.items():
#             if k.startswith("_"):
#                 c_kwargs[k[1:]] = v
#             else:
#                 o_kwargs[k] = v

#         return cls._create_from((args, o_kwargs), **c_kwargs)

#     @classmethod
#     def _create_from(cls, init_args=None, *_args, **_kwargs):
#         if len(_args) > 0 or len(_kwargs) > 0:
#             cls = cls.new_class(*_args, **_kwargs)

#         args = []
#         kwargs = {}
#         if init_args is None:
#             pass
#         elif isinstance(init_args, collections.abc.Mapping):
#             kwargs = init_args
#         elif isinstance(init_args, list):
#             args = init_args
#         elif isinstance(init_args, tuple):
#             args, kwargs = init_args
#         else:
#             args = [init_args]

#         return cls(*args, **kwargs)
