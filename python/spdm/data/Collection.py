import collections
import pathlib
from functools import cached_property
from typing import Any, Dict, List, NewType, Tuple

from spdm.util.logger import logger
from spdm.util.SpObject import SpObject
from spdm.util.urilib import urisplit, uriunsplit

from .Document import Document
from .File import File

InsertOneResult = collections.namedtuple("InsertOneResult", "inserted_id success")
InsertManyResult = collections.namedtuple("InsertManyResult", "inserted_ids success")
UpdateResult = collections.namedtuple("UpdateResult", "upserted_id success")
DeleteResult = collections.namedtuple("DeleteResult", "deleted_id success")


class Collection(SpObject):
    ''' Collection of documents
    '''

    associations = {
        "mapping": f"{__package__}.Mapping#MappingCollection",
        "local": f"{__package__}.Collection#CollectionLocalFile",

        "mds": f"{__package__}.db.MDSplus#MDSplusCollection",
        "mdsplus": f"{__package__}.db.MDSplus#MDSplusCollection",

        "mongo": f"{__package__}.db.MongoDB",
        "mongodb": f"{__package__}.db.MongoDB",

        "imas": f"{__package__}.db.IMAS",
    }

    @staticmethod
    def __new__(cls, _metadata=None, *args, schema=None,  **kwargs):
        if cls is not Collection:
            return object.__new__(cls)

        if not schema:
            if isinstance(_metadata, str):
                schemas = urisplit(_metadata)["schema"]
            elif isinstance(_metadata, collections.abc.Mapping):
                schemas = _metadata.get("$class", None) or _metadata.get("schema", None)
            elif _metadata is None:
                schemas = ""

            schemas = (schemas or "").split('+')

            if not schemas:
                raise ValueError(_metadata)
            elif len(schemas) > 1:
                schema = "mapping"
            else:
                schema = schemas[0]

        n_cls = Collection.associations.get(schema.lower(), None)   # f"{__package__}.db.{schema}"

        if n_cls is not None:
            return SpObject.__new__(Collection, n_cls)
        else:
            return SpObject.__new__(CollectionLocalFile)

    def __init__(self, metadata, *args, mode="rw", envs=None,   **kwargs):
        super().__init__()
        if isinstance(metadata, str):
            metadata = urisplit(metadata)
        self._metadata = metadata
        self._mode = mode
        self._envs = collections.ChainMap(kwargs, envs or {})
        logger.info(f"Create {self.__class__.__name__} : {self._metadata}")

    def __del__(self):
        logger.info(f"Close  {self.__class__.__name__} : {self._metadata}")

    @property
    def metadata(self):
        return self._metadata

    @property
    def schema(self):
        return self._metadata.get("schema", None)

    @cached_property
    def envs(self):
        return self._envs

    @property
    def mode(self):
        return self._mode

    @property
    def is_writable(self):
        return "w" in self.mode or 'x' in self.mode

    def guess_id(self, *args, **kwargs):
        return NotImplemented

    @property
    def next_id(self):
        raise NotImplementedError()

    def open(self, *args, mode=None, **kwargs):
        mode = mode or self.mode
        if "x" in mode:
            return self.insert_one(*args,  **kwargs)
        else:
            return self.find_one(*args,   **kwargs)

    def create(self, *args, **kwargs):
        return self.insert_one(*args, mode="x", **kwargs)

    def insert(self, data, *args, **kwargs):
        if isinstance(data, list):
            return self.insert_many(data, *args, **kwargs)
        else:
            return self.insert_one(data, *args, **kwargs)

    def insert_one(self, data, * args,  **kwargs) -> InsertOneResult:
        doc = Document(self.guess_id(*args, **kwargs) or self.next_id, **kwargs)
        if data is not None:
            doc.update(data)
        return doc

    def insert_many(self, documents, *args, **kwargs) -> InsertManyResult:
        return [self.insert_one(doc, *args, **kwargs) for doc in documents]

    def find_one(self, *args, predicate=None, **kwargs):
        return Document(self.guess_id(*args, **kwargs), **kwargs).fetch(predicate)

    def find(self, predicate=None, projection=None, *args, **kwargs):
        raise NotImplementedError()

    def replace_one(self, predicate, replacement,  *args, **kwargs) -> UpdateResult:
        raise NotImplementedError()

    def update_one(self, predicate, update,  *args, **kwargs) -> UpdateResult:
        raise NotImplementedError()

    def update_many(self, predicate, updates: list,  *args, **kwargs) -> UpdateResult:
        return [self.update_one(predicate, update, *args, **kwargs) for update in updates]

    def delete_one(self, predicate,  *args, **kwargs) -> DeleteResult:
        raise NotImplementedError()

    def delete_many(self, predicate, *args, **kwargs) -> DeleteResult:
        raise NotImplementedError()

    def count(self, predicate=None, *args, **kwargs) -> int:
        raise NotImplementedError()

    ######################################################################
    # TODO(salmon, 2019.07.01) support index

    def create_indexes(self, indexes: List[str], session=None, **kwargs):
        raise NotImplementedError()

    def create_index(self, keys: List[str], session=None, **kwargs):
        raise NotImplementedError()

    def ensure_index(self, key_or_list, cache_for=300, **kwargs):
        raise NotImplementedError()

    def drop_indexes(self, session=None, **kwargs):
        raise NotImplementedError()

    def drop_index(self, index_or_name, session=None, **kwargs):
        raise NotImplementedError()

    def reindex(self, session=None, **kwargs):
        raise NotImplementedError()

    def list_indexes(self, session=None):
        raise NotImplementedError()


class CollectionLocalFile(Collection):
    """
        Collection of local files.
    """

    def __init__(self,   *args, file_format=None, mask=None,   **kwargs):
        super().__init__(*args, schema="local", **kwargs)

        logger.debug(self.metadata)

        self._path = pathlib.Path(self.metadata.get("authority", "") +
                                  self.metadata.get("path", ""))  # .replace("*", Collection.ID_TAG)

        self._file_format = file_format

        prefix = self._path

        while "*" in prefix.name or "{" in prefix.name:
            prefix = prefix.parent

        self._prefix = prefix
        self._filename = self._path.relative_to(self._prefix).as_posix()

        if "x" in self._mode:
            self._prefix.mkdir(parents=True, exist_ok=True, mode=mask or 0o777)
        elif not self._prefix.is_dir():
            raise NotADirectoryError(self._prefix)
        elif not self._prefix.exists():
            raise FileNotFoundError(self._prefix)

        self._path = self._path.as_posix().replace("*", "{id:06}")

    @property
    def next_id(self):
        pattern = self._filename if "*" in self._filename else "*"
        return len(list(self._prefix.glob(pattern)))

    def guess_path(self, *args, fid=None, **kwargs):
        return self._path.format(id=fid or self.next_id, **kwargs)

    def find_one(self, *args, projection=None, **kwargs):
        return File(self.guess_path(*args, **kwargs), mode=self.mode).fetch(projection)

    def insert_one(self, *args, projection=None, **kwargs):
        return File(self.guess_path(*args, **kwargs), mode="x")

    def update_one(self, predicate, update,  *args, **kwargs):
        raise NotImplementedError()

    def delete_one(self, predicate,  *args, **kwargs):
        raise NotImplementedError()
