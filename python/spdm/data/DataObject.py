import collections
import inspect
import os
import pathlib
import pprint
from typing import Type

import numpy as np
from ..util.logger import logger
from ..util.SpObject import SpObject
from ..util.urilib import urisplit

from .Entry import Entry


def load_ndarray(desc, value, *args, **kwargs):
    if isinstance(value, np.ndarray):
        return value
    else:
        return NotImplemented


SpObject.schema.update(
    {
        "general": ".data.General",
        "integer": int,
        "float": float,
        "string": str,
        "ndarray": np.ndarray,
    }
)


class DataObject(SpObject):

    def __new__(cls, metadata, *args, **kwargs):
        if cls is not DataObject:
            return super().__new__(cls, metadata, *args, **kwargs)

    def __init__(self, metadata=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._metadata = metadata or {}

    def __repr__(self):
        return f"<{self.__class__.__name__}>"

    def serialize(self, *args, **kwargs):
        return super().serialize(*args, **kwargs)

    @classmethod
    def deserialize(cls, metadata):
        if isinstance(metadata, collections.abc.Mapping):
            n_cls = metadata.get("$class", None)
        elif isinstance(metadata, str):
            n_cls = urisplit(metadata)["schema"] or metadata
        else:
            n_cls = None

        if cls is not DataObject and not n_cls:
            n_cls = cls
        elif isinstance(n_cls, str) and not n_cls.startswith("."):
            n_cls = DataObject.schema.get(n_cls.lower(), None)

        return super().deserialize(n_cls)

    @property
    def metadata(self):
        return self._metadata

    @property
    def entry(self):
        return Entry(self)

    @property
    def value(self):
        return NotImplemented

    def update(self, value):
        raise NotImplementedError(type(value))
