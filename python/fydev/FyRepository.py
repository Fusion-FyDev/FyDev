import collections
import collections.abc
import os
import pathlib
import typing

from spdm.common.DefaultSortedDict import DefaultSortedDict
from spdm.common.LazyCall import LazyCall
from spdm.util.logger import logger
from spdm.util.utilities import fetch_request, replace_tokens
from .FyPackage import FyPackage


class PathManager(DefaultSortedDict):
    """
     以有序字典管理路径，根据 键值作为前缀匹配path ，得到相应的实际目录。
    """

    def __init__(self,  *args, envs={},  **kwargs):
        super().__init__(*args, default_factory=list, **kwargs)
        self._envs = {} if envs is None else envs

    def _make_tag(self, name="unnamed",
                  version="1.0.0",
                  toolchain="dummy",
                  versionsuffix="", **kwargs):
        if versionsuffix != "" and versionsuffix[0] != "-":
            versionsuffix = f"-{versionsuffix}"
        return FyPackage.Tag(name=name.format(self._envs),
                             version=version, toolchain=toolchain,
                             versionsuffix=versionsuffix), kwargs

    def _normalize_uri(self, path: typing.Union[str, typing.List],
                       **kwargs) -> typing.Tuple[FyPackage.Tag, typing.Dict]:
        if isinstance(path, str):
            return self._make_tag(path, **kwargs)
        elif isinstance(path, collections.abc.Mapping):
            return self._normalize_uri(**path, **kwargs)
        elif not isinstance(path, collections.abc.Sequence):
            raise TypeError(f"Illegal path {type(path)} !")

        for idx, item in enumerate(path):
            if isinstance(item, collections.abc.Mapping):
                if idx == len(path)-1:
                    return self._normalize_uri("/".join(path[:idx]),  ** collections.ChainMap(item, kwargs))
                else:
                    return self._normalize_uri("/".join(path[:idx]), exec_file="/".join(path[idx+1:]), **collections.ChainMap(item, kwargs))

        return self._normalize_uri(path="/".join(path), **kwargs)

    def glob(self, tag: FyPackage.Tag,  **kwargs) -> typing.Iterator[typing.Tuple[typing.Mapping, str]]:
        """
            根据“描述符”generate可能的备选路径,
        """
        if not isinstance(tag, FyPackage.Tag):
            tag, kwargs = self._normalize_uri(tag, **kwargs)

        token_map = collections.ChainMap(
            tag._asdict(),
            {
                "suffix": f"{tag.version}-{tag.toolchain}{tag.versionsuffix}",
                "id": f"{tag.name}-{tag.version}-{tag.toolchain}{tag.versionsuffix}"
            },
            self._envs)

        for key, paths in self.items()[::-1]:
            if not ((key == "" or key.endswith('.')) and tag.name.startswith(key)):
                continue
            for url in paths:
                url = url.format_map(token_map)
                try:
                    desc = fetch_request(url)
                except Exception:
                    continue
                else:
                    desc.setdefault("information", {}).update(tag._asdict())
                    desc.setdefault("run", {}).update(kwargs)
                    yield desc, url

    def find(self, *args, **kwargs) -> typing.Tuple[typing.Mapping, str]:
        # 遍历 path list 直到找到第一个有效的 description
        return next(self.glob(*args, **kwargs))


_TFyRepository = typing.TypeVar('_TFyRepository', bound='FyRepository')


class FyRepository(object):

    def __init__(self,  *args, install_path={}, **kwargs):
        super().__init__()

        self._envs = {k: v for k, v in os.environ.items() if k.startswith("FY_")}

        self._envs.update(kwargs)

        # 软件包的安装目录,
        self._install_path = PathManager(install_path, envs=self._envs)
        # 默认安装目录
        self._install_path[""].append("~/fydev/{name}/{version}-{toolchain}{versionsuffix}")

        # 软件包的安装目录,
        self._repositories = PathManager(envs=self._envs)

        logger.info(f"Open repository {self._envs.get('name','FyDev')}")

    @property
    def envs(self) -> typing.Mapping[str, str]:
        return self._envs

    @property
    def repositories(self) -> PathManager:
        return self._repositories

    @property
    def install_path(self) -> PathManager:
        return self._install_path

    @property
    def default_install_path(self) -> pathlib.Path:
        return pathlib.Path(self._install_path[""][0])

    def glob(self, *args, **kwargs) -> typing.Iterator[FyPackage]:
        """ 找到所有满足要求的 module"""
        for desc, url in self._install_path.glob(*args,  **kwargs):
            yield FyPackage(desc, install_dir=url, envs=self._envs)

    def find(self, *args, **kwargs) -> FyPackage:
        """ 找到第一个满足要求的 module"""
        return next(self.glob(*args, **kwargs))

    def __missing__(self, *args, **kwargs) -> FyPackage:
        # 当module 缺失时， 调用 install。参数 force=True 意味不必检查包是否存在
        return self.install(*args, **kwargs, force=True)

    def install(self, *args, force=False, **kwargs) -> FyPackage:

        package = self.find(*args,  **kwargs)

        if not force and package.installed:
            raise FileExistsError(f"Can not reinstall package {package} !")

        package.update_desc(self._repositories)

        package.install(install_prefix=self.default_install_path, force=force)

        if not package.sanity_check():
            raise ModuleNotFoundError(f"Install {package} failed!")

        return package

    def reinstall(self,  *args,  **kwargs) -> bool:
        package = self.find(*args,  **kwargs)

        if not package.installed:
            logger.warning(f"Pacakge {package} is not installed!")
            return False
        else:
            return package.reinstall()

    def uninstall(self, *args, **kwargs) -> bool:
        package = self.find(*args, **kwargs)

        if not package.installed:
            logger.warning(f"Pacakge {package} is not installed!")
            return False
        else:
            return package.uninstall()

    def load(self, *args, **kwargs) -> typing.Callable:
        package = self.find(*args,  **kwargs)

        if not package.valid:
            # 若找不到，调用 __missing__
            package = self.__missing__(*args, **kwargs)

        return package.load()

    @property
    def entry(self) -> LazyCall[_TFyRepository]:
        return LazyCall(self, handler=lambda s, p: s.load(p))
