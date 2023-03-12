import collections
import os
import pathlib

from ..util.LazyProxy import LazyProxy
from ..util.logger import logger
from ..util.PathTraverser import PathTraverser
from ..util.urilib import urisplit
from .Collection import Collection
from .Document import Document
from .Entry import Entry
from .File import File

SPDB_XML_NAMESPACE = "{http://fusionyun.org/schema/}"


class DocumentBundle(Document):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._handler = {}

    def handler(self, tag):
        if "}" in tag:
            tag = tag[tag.rfind("}")+1:]

        h = self._handler.get(tag, None)
        if not h:
            h = self._parent.get_handler(tag, fid=self.fid, mode=self.mode, envs=self._envs)
            self._handler[tag] = h
        return h

    def fetch(self, tag, request):
        return self.handler(tag).fetch(request)

    def update(self, tag, request):
        return self.handler(tag).update(request)


class CollectionBundle(Collection):
    def __init__(self, metadata, *args, **kwargs):
        super().__init__(metadata, *args,  **kwargs)
        self._source = {}
        tag = "local"
        if isinstance(metadata, str):
            source = urisplit(metadata)
            self._source[source.get("schema", tag)] = source
        elif isinstance(metadata, collections.abc.Mapping) and "schema" not in metadata:
            self._source = metadata
        elif isinstance(metadata, Collection):
            self._source[metadata.schema] = metadata
        else:
            logger.error(f"Illegal taget {metadata}")

    def insert_one(self, *args, fid=None, **kwargs):
        return DocumentBundle(*args, fid=fid,  parent=self,  mode="x",   **kwargs)

    def find_one(self,   *args,  fid=None,   **kwargs):
        return DocumentBundle(*args, fid=fid, parent=self,   mode=self._mode,   **kwargs)

    def get_handler(self, tag, fid=None, mode=None, **kwargs):

        source = self._source.get(tag, None)

        if source is None:
            raise KeyError(tag)
        elif not isinstance(source, Collection):
            source = Collection(source)
            self._source[tag] = source

        if "x" in mode:
            handler = source.insert_one(fid=fid, mode=mode, **kwargs)
        else:
            handler = source.find_one(fid=fid, mode=mode, **kwargs)

        return handler


class MappingEntry(Entry):
    def __init__(self, *args, mapping=None, source=None,  ** kwargs):
        super().__init__(*args, **kwargs)
        self._mapping = mapping  # self._data._mapping.entry
        self._source = source

    def __post_process__(self, request, *args, **kwargs):
        if isinstance(request, Entry):
            res = MappingEntry(source=self._source, mapping=request, parent=self._parent)
        elif isinstance(request, collections.abc.Mapping) and len(request) == 1:
            k, v = next(iter(request.items()))
            if k[0] == "{":
                res = self._source.fetch(k, v)
            else:
                res = super().__post_process__(request, *args, **kwargs)
        else:
            res = super().__post_process__(request, *args, **kwargs)
        return res

    def child(self, path, *args, **kwargs):
        return MappingEntry(source=self._source,
                            mapping=self._mapping.child(path, *args, **kwargs),
                            parent=self._parent)

    def get(self,  path, *args,  is_raw_path=False,  **kwargs):
        return self.__post_process__(self._mapping.get(path, *args, only_one=True, **kwargs))

    def get_value(self,  path, *args,  is_raw_path=False,  **kwargs):
        return self.__post_process__(self._mapping.get_value(path, *args, **kwargs))

    def put(self,  path, value, *args, is_raw_path=False,   **kwargs):
        if not is_raw_path:
            return PathTraverser(path).apply(lambda p: self.get(p, is_raw_path=True, **kwargs))
        else:
            request = self._mapping.get_value(path, *args, **kwargs)

            if isinstance(request, str):
                self._data.update(request, value, is_raw_path=True)
            elif isinstance(request, collections.abc.Sequence):
                raise NotImplementedError()
            elif isinstance(request, collections.abc.Mapping):
                raise NotImplementedError()
            elif request is not None:
                raise RuntimeError(f"Can not write to non-empty entry! {path}")

    def iter(self,  request, *args, **kwargs):
        for source_req in self._mapping.iter(request, *args, **kwargs):
            yield self.__post_process__(source_req)


class MappingDocument(Document):
    def __init__(self, *args,  source=None,  mapping=None,  **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(mapping, Document):
            self._mapping = Document(mapping)
        else:
            self._mapping = mapping

        if not isinstance(source, Document):
            self._source = Document(source, envs=self._envs)
        else:
            self._source = source

    @property
    def entry(self):
        return MappingEntry(source=self._source, mapping=self._mapping.entry, parent=self)

    def update(self, request, value=None, tag=None):
        pass


class MappingCollection(Collection):

    def __init__(self,  metadata=None, *args, source=None, mapping=None, id_hasher=None, schema=None, ** kwargs):
        super().__init__(metadata, *args, schema=schema or "mapping", **kwargs)

        id_hasher = id_hasher or "{shot}"

        if callable(id_hasher):
            self._id_hasher = id_hasher
        else:
            self._id_hasher = lambda *a, _pattern=id_hasher, **k: _pattern.format(**k)

        mapping_schema = "EAST"
        mapping_version = "imas/3"

        if isinstance(metadata, str):
            npos = metadata.find("+")
            if not npos:
                raise ValueError(metadata)

            mapping_schema = mapping_schema or metadata[:npos]
            source = source or metadata[npos+1:]

        if isinstance(mapping, Document):
            self._mapping = mapping
        else:
            if isinstance(mapping, str):
                mapping_path = mapping.split(";")
            elif isinstance(mapping, pathlib.PosixPath):
                mapping_path = [mapping]
            elif isinstance(mapping, collections.abc.Sequence):
                mapping_path = []
            elif isinstance(mapping, collections.abc.Mapping):
                dpth = mapping.get("path", [])
                if isinstance(dpth, str):
                    dpth = dpth.split(";")
                mapping_path = dpth
                mapping_version = mapping.get("version", mapping_version)
                mapping_schema = mapping.get("schema", mapping_schema)

            mapping_path.extend(os.environ.get("SP_DATA_MAPPING_PATH", "").split(";"))

            file_path_suffix = ["config.xml", "static/config.xml", "dynamic/config.xml"]

            mapping_conf_files = []
            for m_dir in mapping_path:
                if not m_dir:
                    continue
                elif isinstance(m_dir, str):
                    m_dir = pathlib.PosixPath(m_dir)
                for file_name in file_path_suffix:
                    p = m_dir / ('/'.join([mapping_schema, mapping_version, file_name]))
                    if p.exists():
                        mapping_conf_files.append(p)

            self._mapping = File(mapping_conf_files, format="XML")

        self._source = CollectionBundle(source)

    def __del__(self):
        self._source_bundle = None
        self._mapping = None
        super().__del__()

    def guess_id(self, *args,  **kwargs):
        if not args and not kwargs:
            return None
        else:
            return self._id_hasher(**kwargs)

    def insert_one(self, *args, **kwargs):
        fid = self.guess_id(*args, **kwargs) or self.next_id,
        return MappingDocument(fid=fid, parent=self, mode="x",
                               source=self._source.insert_one(fid=fid, envs=self._envs, **kwargs),
                               mapping=self._mapping)

    def find_one(self,   *args,   **kwargs):
        fid = self.guess_id(*args, **kwargs)
        return MappingDocument(fid=fid, parent=self, mode=self._mode,
                               source=self._source.find_one(fid=fid,  **kwargs),
                               mapping=self._mapping)


__SP_EXPORT__ = MappingCollection
