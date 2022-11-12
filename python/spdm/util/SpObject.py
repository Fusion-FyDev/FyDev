import collections
import copy
import inspect
import re
import traceback
import uuid
from functools import cached_property
import io
import numpy as np

from .logger import logger
from .sp_export import sp_find_module
from .utilities import convert_to_named_tuple
_factory = None
_resolver = None


class SpObject(object):
    """
        Description:
            Super class of all spdm objects
        Attribute:
            parent      : parent node
            name        : short string
    """
    _default_prefix = ".".join(__package__.split('.')[:-1])

    schema = {}

    @staticmethod
    def find_class(metadata,  *args,  **kwargs):
        if isinstance(metadata, str):
            n_cls = metadata
        elif isinstance(metadata, collections.abc.Mapping):
            n_cls = metadata.get("$class")
        if isinstance(n_cls, str):
            if n_cls.startswith("."):
                n_cls = f"{SpObject._default_prefix}{n_cls}"
            n_cls = sp_find_module(n_cls)
        if not inspect.isclass(n_cls):
            raise ModuleNotFoundError(metadata)
        return n_cls

    def __new__(cls,   *args,  **kwargs):
        if cls is not SpObject:
            return object.__new__(cls)
        else:
            n_cls = SpObject.find_class(*args,  **kwargs)
            if issubclass(n_cls, cls):
                return object.__new__(n_cls)
            else:
                return n_cls(*args, **kwargs)

    @classmethod
    def deserialize(cls, spec):
        # @classmethod
        # def parse_metadata(cls,  metadata=None, *args, **kwargs):

        # return n_cls

        if hasattr(cls, "_factory"):
            return cls._factory.create(spec)
        elif isinstance(spec, str):
            spec = cls._resolver.fetch(spec) if hasattr(cls, "_resolver") else io.read(spec)

        if not isinstance(spec, collections.abc.Mapping):
            raise TypeError(type(spec))
        spec.setdefault("name", spec.get("name", cls.__name__))
        return cls(**spec)

    def serialize(self):
        return {"$schema": self._schema,
                "$class": self._class,
                "$id":  self._oid,
                "attributes": self._attributes.__as_native__(),
                }

    def __init__(self, metadata=None, *args,  **kwargs):
        super().__init__()
        self._oid = uuid.uuid1()

    # def __del__(self):
    #     if hasattr(self._parent, "remove_child"):
    #         self._parent.remove_child(self)

    @classmethod
    def from_json(cls, spec, *args, **kwargs):
        return cls.deserialize(spec, *args, **kwargs)

    def to_json(self):
        return self.serialize()

    @property
    def label(self):
        return self.attributes.label

    @property
    def name(self):
        return self.attributes.name

    @property
    def attributes(self):
        return self._attributes

    @cached_property
    def metadata(self):
        return (getattr(self.__class__, "_metadata", {}))

    def __hash__(self):
        return self._oid.int

    ##############################################################
    @property
    def parent(self):
        return self._parent

    @property
    def children(self):
        return self._children

    def remove_child(self, child):
        raise NotImplementedError

    def insert_child(self, child, name=None, *args, **kwargs):
        raise NotImplementedError

    @property
    def is_root(self):
        return self._parent is None

    @property
    def kind(self):
        return self.__class__.__name__

    @property
    def full_name(self):
        if self._parent is not None:
            return f"{self._parent.full_name}.{str(self.attributes.name)}"
        else:
            return str(self.attributes.name)

    def shorten_name(self, num=2):
        s = self.full_name.split('.')
        if len(s) <= num:
            return '.'.join(s)
        else:
            return f"{s[0]}...{'.'.join(s[-(num-1):])}"

    @property
    def oid(self):
        return self._oid

    def __repr__(self):
        return f"<{self.__class__.__name__}   />"

    def __str__(self):
        return f"<{self.__class__.__name__}   />"

    ######################################################
    # algorithm

    def find_shortest_path(self, s, t):
        return []


def as_spobject(cls, *args, **kwargs):
    pass


__SP_EXPORT__ = SpObject
