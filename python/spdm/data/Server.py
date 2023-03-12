import collections
import contextlib
import pathlib
from urllib import parse

from spdm.util.logger import logger
from spdm.util.sp_export import sp_find_module
from spdm.util.urilib import urijoin, urisplit


class Connection(object):
    def __init__(self, path=None, *args,  protocol=None, template=None, schema=None, **kwargs):
        super().__init__()

        if not isinstance(path, pathlib.Path):
            path = pathlib.Path(path)
        path = path.expanduser().resolve()
        protocol = _guess_protocol(path, protocol)
        mod = _find_file_module(_guess_protocol(path, protocol))
        if mod is None:
            raise ModuleNotFoundError(f"protocol:'{protocol}'")
        self._prefix = SpURI(path)
        self._template = template
        self._backend = mod
        self._conn = None

    def __repr__(self):
        return self._prefix.path

    def open(self, *args, **kwargs):
        if hasattr(self._backend, "connect"):
            self._conn = self._backend.connect(
                self._prefix, template=self._template)
        return self

    def close(self):
        self._conn = None

    def write(self, d, path=None, *args,  **kwargs):
        if self._conn:
            self._conn.write(path, d, *args, **kwargs)
        else:
            self._backend.write((self._prefix/path).path, d, *args,
                                template=self._template, **kwargs)

    def read(self, path=None, *args, **kwargs):
        try:
            if self._conn:
                data = self._conn.read(path, *args, **kwargs)
            else:
                data = self._backend.read(
                    (self._prefix/path).path, *args,  **kwargs)

        except IOError:
            raise IOError(f"Can't read file '{self._prefix/path}'!")

        return data

    def put(self, path, *args, **kwargs):
        return self._backend.delete(*args, **kwargs)

    def post(self, path, *args, **kwargs):
        return self._backend.delete(*args, **kwargs)

    def get(self, path, *args, **kwargs):
        return self._backend.delete(*args, **kwargs)

    def delete(self, path, *args, **kwargs):
        return self._backend.delete(*args, **kwargs)


@contextlib.contextmanager
def connect(uri, *args, **kwargs):
    if isinstance(uri, Connection):
        conn = uri
        need_close = False
    else:
        conn = Connection(uri, *args, **kwargs)
        need_close = True
    try:
        yield conn
    finally:
        if need_close:
            conn.close()
