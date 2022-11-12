
import collections
import re

from .logger import logger
from .Multimap import Multimap


class Alias:
    """ Multi-Mapping of path alias

       Example:
            >>> alias=Alias()
            >>> alias.append("http://a.b.c.d.com/schemas/draft-00","/some/local/dir/%PLACEHOLDER%.json")
            >>> alias.append("http://a.b.c.d.com/schemas/draft-00/flow","/other/local/dir/")
            >>> [ p for p in alias.get("http://a.b.c.d.com/schemas/draft-00/flow/Entry")]
            ["/some/local/dir/flow/Node.json",
            "/other/local/dir/Node",
            "http://a.b.c.d.com/schemas/draft-00/flow/Node"]

            TODO (salmon 2020.04.14): need regex match
    """

    def __init__(self, *args,  **kwarg):
        self._mmap = collections.deque()

    def _compile(self, s, t):

        if not isinstance(s, re.Pattern):
            if '*' in s:
                s = s.replace('*', "(?P<_path_>[^?#]*)")+"(#(?P<fragment>.*))?"

            if '(' not in s:
                re_s = re.compile(f"{s}(?P<_path_>[^?#]*)(#(?P<fragment>.*))?")
            else:
                re_s = re.compile(s)

        if '*' in t:
            t = t.replace('*', '{_path_}')
        elif '{' not in t:
            t = t+'{_path_}'

        return re_s, t

    def match(self, *keys):
        """ if key is re.Pattern and  match(s)
            or key is string and s.startswith(key)
        """

        for s in keys:
            if s is None:
                continue
            for pattern, target in self._mmap:
                if isinstance(pattern, re.Pattern):
                    m = pattern.match(s)
                elif isinstance(pattern, str):
                    m = re.match(pattern, s)
                else:
                    m = None
                    logger.warning(
                        f"Type of key is not string or re.Pattern! {pattern}")
                if m is not None:
                    yield target.format(*m.groups(), **m.groupdict())

    def append(self, source: str, target: str):
        return self._mmap.append((self._compile(source, target)))

    def prepend(self, source: str, target: str):
        return self._mmap.appendleft((self._compile(source, target)))

    def append_many(self, m):
        if m is None:
            pass
        elif isinstance(m, collections.abc.Mapping):
            self.append_many(m.items())
        elif isinstance(m, collections.abc.Sequence):
            for k, v in m:
                self.append(k, v)
        else:
            raise TypeError(f"Require list or map, not [{type(m)}]")

    def prepend_many(self, m):
        if m is None:
            pass
        elif isinstance(m, collections.abc.Mapping):
            self.prepend_many(m.items())
        elif isinstance(m, collections.abc.Sequence):
            for k, v in m:
                self.prepend(k, v)
        else:
            raise TypeError(f"Require list or map, not [{type(m)}]")

    def add(self, *args, **kwargs):
        return self.append(*args, **kwargs)

    def remove(self, range_start: str, range_end: str = None):
        raise NotImplementedError()
        # self._mmap.remove(range_start, range_end)
