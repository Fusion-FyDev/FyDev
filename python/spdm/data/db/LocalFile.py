import collections
import inspect
import pathlib
import re
import urllib
from typing import Any, Dict, List, NewType, Tuple

import numpy
from spdm.util.logger import logger
from spdm.util.sp_export import sp_find_module
from spdm.util.urilib import urisplit, uriunsplit

from ..Document import Document
from ..Plugin import find_plugin
from ..Collection import Collection
from ..File import File


class FileCollection(Collection):

    def __init__(self, uri, *args,
                 file_extension=".dat",
                 file_factory=None,
                 **kwargs):

        super().__init__(uri, *args, **kwargs)

        if isinstance(uri, str):
            uri = urisplit(uri)

        path = getattr(uri, "path", ".").replace("*", "{_id}")

        if isinstance(path, str) and path.find("{_id}") < 0:  # not path.endswith(file_extension):
            path = f"{path}{{_id}}{file_extension}"

        self._path = pathlib.Path(path).resolve().expanduser()

        logger.debug(self._path)

        if self._path.suffix == '':
            self._path = self._path.with_suffix(file_extension)

        if "{_id}" not in self._path.stem:
            self._path = self._path.with_name(f"{self._path.stem}{{_id}}{self._path.suffix}")

        if not self._path.parent.exists():
            if "w" not in self._mode:
                raise RuntimeError(f"Can not make dir {self._path}")
            else:
                self._path.parent.mkdir()
        elif not self._path.parent.is_dir():
            raise NotADirectoryError(self._path.parent)

        self._file_factory = file_factory or File

    def guess_id(self, d, auto_inc=True):
        fid = super().guess_id(d, auto_inc=auto_inc)

        if fid is None and auto_inc:
            fid = self.count()

        return fid

    def guess_filepath(self, *args, **kwargs):
        return self._path.with_name(self._path.name.format(_id=self.guess_id(*args, **kwargs)))

    def open_document(self, fid, mode=None):
        fpath = self.guess_filepath({"_id": fid})
        logger.debug(f"Opend Document: {fpath} mode=\"{ mode or self.metadata.mode}\"")
        return Document(root=self._file_factory(fpath, mode or self.metadata.mode), fid=fid, envs=self.envs, handler=self._handler)

    def insert_one(self, data=None, *args,  **kwargs):
        doc = self.open_document(self.guess_id(data or kwargs, auto_inc=True), mode="w")
        doc.update(data or kwargs)
        return doc

    def find_one(self, predicate=None, projection=None, **kwargs):
        fpath = self.guess_filepath(predicate or kwargs)

        doc = None
        if fpath.exists():
            doc = self.open_document(fpath)
        else:
            for fp in self._path.parent.glob(self._path.name.format(_id="*")):
                if not fp.exists():
                    continue
                doc = self.open_document(fp, mode="r")
                if doc.check(predicate):
                    break
                else:
                    doc = None

        if projection is not None:
            raise NotImplementedError()

        return doc

    def update_one(self, predicate, update,  *args, **kwargs):
        raise NotImplementedError()

    def delete_one(self, predicate,  *args, **kwargs):
        raise NotImplementedError()

    def count(self, predicate=None,   *args, **kwargs) -> int:

        if predicate is None:
            logger.warning("NOT IMPLEMENTED! count by predicate")

        return len(list(self._path.parent.glob(self._path.name.format(_id="*"))))


__SP_EXPORT__ = FileCollection
