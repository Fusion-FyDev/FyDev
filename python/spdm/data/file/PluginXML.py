import collections
import pathlib

import numpy as np
from spdm.util.dict_util import format_string_recursive
from spdm.util.logger import logger
from spdm.util.PathTraverser import PathTraverser

from ..AttributeTree import AttributeTree
from ..Document import Document
from ..Entry import Entry
from ..File import File
from ..Node import _not_found_

try:
    from lxml.etree import Comment as _XMLComment
    from lxml.etree import ParseError as _XMLParseError
    from lxml.etree import XPath as _XPath
    from lxml.etree import _Element as _XMLElement
    from lxml.etree import parse as parse_xml

    _HAS_LXML = True
except ImportError:
    from xml.etree.ElementTree import Comment as _XMLComment
    from xml.etree.ElementTree import Element as _XMLElement
    from xml.etree.ElementTree import ParseError as _XMLParseError
    from xml.etree.ElementTree import parse as parse_xml
    _XPath = str
    _HAS_LXML = False


def merge_xml(first, second):
    if first is None:
        raise ValueError(f"Try merge to None Tree!")
    elif second is None:
        return first
    elif first.tag != second.tag:
        raise ValueError(f"Try to merge tree to different tag! {first.tag}<={second.tag}")

    for child in second:
        if child.tag is _XMLComment:
            continue
        eid = child.attrib.get("id", None)
        if eid is not None:
            target = first.find(f"{child.tag}[@id='{eid}']")
        else:
            target = first.find(child.tag)
        if target is not None:
            merge_xml(target, child)
        else:
            first.append(child)


def load_xml(path, *args,  mode="r", **kwargs):
    # TODO: add handler non-local request ,like http://a.b.c.d/babalal.xml

    if type(path) is list:
        root = None
        for fp in path:
            if root is None:
                root = load_xml(fp, mode=mode)
            else:
                merge_xml(root, load_xml(fp, mode=mode))
        return root
    elif isinstance(path, str):
        path = pathlib.Path(path)

    root = None
    try:
        if path.exists() and path.is_file():
            root = parse_xml(path.as_posix()).getroot()
            logger.debug(f"Loading XML file from {path}")
    except _XMLParseError as msg:
        raise RuntimeError(f"ParseError: {path}: {msg}")

    if root is not None:
        for child in root.findall("{http://www.w3.org/2001/XInclude}include"):
            fp = path.parent/child.attrib["href"]
            root.insert(0, load_xml(fp))
            root.remove(child)

    return root


class XMLEntry(Entry):
    def __init__(self, *args, writable=False, **kwargs):
        super().__init__(*args, writable=writable, **kwargs)

    def xpath(self, path):
        envs = {}
        res = "."
        prev = None
        for p in path:
            if type(p) is int:
                res += f"[ @id='{p}' or position()= {p+1} or @id='*']"
                envs[prev] = p
            elif isinstance(p, str) and p[0] == '@':
                res += f"[{p}]"
            elif isinstance(p, str):
                res += f"/{p}"
                prev = p
            else:
                # TODO: handle slice
                raise TypeError(f"Illegal path type! {type(p)} {path}")

        if _HAS_LXML:
            res = _XPath(res)
        else:
            raise NotImplementedError()
        return res, envs

    def _convert(self, element, path=[], lazy=True, envs=None, projection=None):

        if isinstance(element, collections.abc.Sequence) and not isinstance(element, str):
            res = [self._convert(e, path=path, lazy=lazy, envs=envs, projection=property) for e in element]
            if len(res) == 1:
                res = res[0]
            return res
        res = None

        if len(element) > 0 and lazy:
            res = XMLEntry(element, prefix=[])
        elif element.text is not None and "dtype" in element.attrib or (len(element) == 0 and len(element.attrib) == 0):
            dtype = element.attrib.get("dtype", None)

            if dtype == "string" or dtype is None:
                res = [element.text]
            elif dtype == "int":
                res = [int(v.strip()) for v in element.text.strip(',').split(',')]
            elif dtype == "float":
                res = [float(v.strip()) for v in element.text.strip(',').split(',')]
            else:
                raise NotImplementedError(f"Not supported dtype {dtype}!")

            dims = [int(v) for v in element.attrib.get("dims", "").split(',') if v != '']
            if len(dims) == 0 and len(res) == 1:
                res = res[0]
            elif len(dims) > 0 and len(res) != 0:
                res = np.array(res).reshape(dims)
            else:
                res = np.array(res)
        else:
            res = {child.tag: self._convert(child, path=path+[child.tag], envs=envs, lazy=lazy)
                   for child in element if child.tag is not _XMLComment}
            for k, v in element.attrib.items():
                res[f"@{k}"] = v

            text = element.text.strip() if element.text is not None else None
            if text is not None and len(text) != 0:
                query = {}
                prev = None
                for p in self._prefix+path:
                    if type(p) is int:
                        query[f"{prev}"] = p
                    prev = p

                # if not self._envs.fragment:
                #     fstr = query
                # else:
                #     fstr = collections.ChainMap(query, self.envs.fragment.__data__, self.envs.query.__data__ or {})
                # format_string_recursive(text, fstr)  # text.format_map(fstr)
                res["@text"] = text

        if envs is not None and isinstance(res, (str, collections.abc.Mapping)):
            res = format_string_recursive(res, envs)
        return res

    def put(self,  path, value, *args, only_one=False, **kwargs):
        if self.wriable:
            path = self._normalize_path(path)
            if not only_one:
                return PathTraverser(path).apply(lambda p,  v=value, s=self, h=self._data: s._push(h, p, v))
            else:
                raise NotImplementedError()
        else:
            raise RuntimeError(f"Not writable!")

    def get(self,  path, *args, only_one=False, default_value=None, **kwargs):

        if not only_one:
            return PathTraverser(path).apply(lambda p: self.get(p, only_one=True, **kwargs))
        else:
            path = self._normalize_path(path)
            xp, envs = self.xpath(path)
            return self._convert(xp.evaluate(self._data), lazy=True, path=path, envs=envs, ** kwargs)

    def get_value(self,  path, *args,  only_one=False, default_value=_not_found_, **kwargs):

        if not only_one:
            return PathTraverser(path).apply(lambda p: self.get_value(p, only_one=True, **kwargs))
        else:
            path = self._normalize_path(path)
            xp, envs = self.xpath(path)
            obj = xp.evaluate(self._data)
            if isinstance(obj, collections.abc.Sequence) and len(obj) == 1:
                obj = obj[0]
            return self._convert(obj, lazy=False, path=path, envs=envs, **kwargs)

    def iter(self,  path, *args, envs=None, **kwargs):
        path = self._normalize_path(path)
        for spath in PathTraverser(path):
            xp, s_envs = self.xpath(spath)
            for child in xp.evaluate(self._data):
                if child.tag is _XMLComment:
                    continue
                res = self._convert(child, path=spath, envs=collections.ChainMap(s_envs, envs))

                yield res


class XMLFile(File):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ** kwargs)
        self._root = None

    @property
    def entry(self):
        if self._root is None:
            self._root = load_xml(self.path)
        return AttributeTree(XMLEntry(self._root, parent=self))


__SP_EXPORT__ = XMLFile
