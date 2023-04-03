import collections
import collections.abc
import os
import pathlib
import typing

from spdm.common.DefaultSortedDict import DefaultSortedDict
from spdm.common.LazyCall import LazyCall
from spdm.util.logger import logger
from spdm.util.misc import fetch_request

from .FyPackage import FyPackage


class PathManager(DefaultSortedDict):
    """
    以有序字典管理路径， 根据键值作为前缀匹配path ，得到相应的实际目录。
    """

    def __init__(self,  *args, envs={},  **kwargs):
        """
        @param envs: 环境变量
        """
        super().__init__(*args, default_factory=list, **kwargs)
        self._envs = {} if envs is None else envs

    def _make_tag(self, name="unnamed",
                  version="1.0.0",
                  toolchain="dummy",
                  suffix="", **kwargs):
        """
        将参数转换为 FyPackage.Tag
        @param name: 包名
        @param version: 版本号
        @param toolchain: 工具链
        @param suffix: 版本后缀
        @param kwargs: 附加参数
        @return: FyPackage.Tag, kwargs
        """
        if suffix != "" and suffix[0] != "-":
            suffix = f"-{suffix}"
        return FyPackage.Tag(name=name.format(self._envs),
                             version=version, toolchain=toolchain,
                             suffix=suffix), kwargs

    def _normalize_uri(self, path: typing.Union[str, typing.List],
                       **kwargs) -> typing.Tuple[FyPackage.Tag, typing.Dict]:
        """
        将 path 转换为 FyPackage.Tag, 并将 kwargs 中的参数转换为 FyPackage.Tag 的属性
        @param path: str or list
        @param kwargs: 附加参数
        @return: FyPackage.Tag, kwargs
        """
        if isinstance(path, FyPackage.Tag):
            return path, kwargs
        elif isinstance(path, str):
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
                    return self._normalize_uri("/".join(path[:idx]), exec=["/".join(path[idx+1:])], **collections.ChainMap(item, kwargs))

        return self._normalize_uri(path="/".join(path), **kwargs)

    def glob(self, tag: FyPackage.Tag,  **kwargs) -> typing.Iterator[typing.Tuple[str, typing.Mapping]]:
        """
        遍历 path list 找到所有有效的 description 文件，返回 description 和 url
        @param tag: FyPackage.Tag
        @param kwargs: 附加参数
        """
        tag, kwargs = self._normalize_uri(tag, **kwargs)

        token_map = collections.ChainMap(tag._asdict(), self._envs)

        for key, paths in self.items()[::-1]:
            if not ((key == "" or key.endswith('.')) and tag.name.startswith(key)):
                continue
            for url in paths:
                yield url.format_map(token_map), tag, kwargs

    def find(self, *args, **kwargs) -> typing.Tuple[typing.Mapping, str]:
        """ 找到第一个满足要求的 description 文件，返回 description 和 url
            若找不到，则抛出异常
            @raise StopIteration: 找不到满足要求的 description 文件，则抛出异常
        """
        try:
            url = next(self.glob(*args, **kwargs))
        except StopIteration:
            raise ModuleNotFoundError(f"Can not find description for {args} !")
        else:
            return url


_TFyRepository = typing.TypeVar('_TFyRepository', bound='FyRepository')


class FyRepository(object):

    def __init__(self,  configure=None, /,  **kwargs):
        """
        @param install_path: 软件包的安装目录
        @param repositories: 软件包的仓库路径
        """
        super().__init__()

        if configure is None:
            self._configure = kwargs
        else:
            if isinstance(configure, str):
                configure = fetch_request(configure)
            self._configure = collections.ChainMap(kwargs, configure)

        self._envs = {k: v for k, v in os.environ.items() if k.startswith("FY_")}  # 环境变量

        self._envs.update(self._configure.get("envs", {}))  # 环境变量

        self._install_path = PathManager(self._configure.get("install_path"), envs=self._envs)  # 软件包的安装目录

        self._install_path[""].extend(self._envs.get("FY_INSTALL_PATH", "").split(":"))

        if len(self._install_path[""]) == 0:
            self._install_path[""].append(f"~/fydev/{{name}}/{{version}}-{{toolchain}}{{suffix}}")  # 默认安装路径

        self._repository_path = PathManager(self._configure.get("repository_path"), envs=self._envs)  # 软件包的仓库路径

        logger.info(f"Open repository {self._configure.get('name','FyDev')}")

    @property
    def envs(self) -> typing.Mapping[str, str]:
        return self._envs

    @property
    def configure(self) -> typing.Mapping:
        return self._configure

    @property
    def repository_path(self) -> PathManager:
        return self._repository_path

    @property
    def install_path(self) -> PathManager:
        return self._install_path

    @property
    def default_install_path(self) -> pathlib.Path:
        return self._install_path[""][0]

    def _glob(self, _search_paths: PathManager, *args, envs=None, **kwargs) -> typing.Iterator[FyPackage]:
        """ 找到所有满足要求的 module"""
        if isinstance(envs, collections.abc.Mapping):
            envs = collections.ChainMap(envs, self._envs)
        else:
            envs = self._envs

        for url, tag, create_kwargs in _search_paths.glob(*args,  **kwargs):
            try:
                package = FyPackage.create(url, tag=tag, envs=envs,  **create_kwargs)
            except ModuleNotFoundError:
                continue    # 忽略无法创建的 package
            else:
                if not package.valid:
                    continue
                else:
                    yield package  # 返回 package

    def glob(self, *args, **kwargs) -> typing.Iterator[FyPackage]:
        yield from self._glob(self._install_path, *args,  **kwargs)

    def find(self, *args,  **kwargs) -> FyPackage:
        """ 找到第一个满足要求的 module"""
        try:
            package = next(self.glob(*args,  **kwargs))
        except StopIteration:
            raise ModuleNotFoundError(f"Can not find module for {args} !")
        else:
            return package

    def __missing__(self, *args, **kwargs) -> FyPackage:
        # 当module 缺失时， 调用 install。参数 force=True 意味不必检查包是否存在
        return self.install(*args, **kwargs, force=True)

    def install(self, *args, install_dir=None, force=False, **kwargs) -> FyPackage:
        if not force:
            try:
                package = next(self._glob(self._install_path, *args, **kwargs))
            except StopIteration as _:
                pass
            else:
                raise FileExistsError(f"Package {package} is already installed !")
        else:
            try:
                package = next(self._glob(self._repository_path, *args, **kwargs))

            except StopIteration as _:
                raise ModuleNotFoundError(f"Can not find module for {args} in repository !")

        if package.install_dir is None and install_dir is None:
            install_dir = self.default_install_path.format_map(
                collections.ChainMap(package.tag._asdict(), self._envs))
            install_dir = pathlib.Path(install_dir)
            if not install_dir.is_dir():
                install_dir = install_dir.parent
        package.install(install_dir, force=force)

        if not package.sanity_check():
            raise RuntimeError(f"Install {package} failed!")

        return package

    def reinstall(self,  *args,  **kwargs) -> bool:

        try:
            package = self.find(*args,  **kwargs)
        except ModuleNotFoundError:
            return self.install(*args, **kwargs)
        else:
            return package.reinstall()

    def uninstall(self, *args, **kwargs) -> bool:
        try:
            package = self.find(*args, **kwargs)
        except ModuleNotFoundError:
            logger.debug(f"Can not find module for {args} !")
            return False
        else:
            return package.uninstall()

    def load(self, *args, **kwargs) -> typing.Callable:
        """
        载入一个模块，如果模块不存在，调用 __missing__ 安装模块
        """
        try:
            package = self.find(*args,  **kwargs)
        except ModuleNotFoundError:
            # 若找不到，调用 __missing__
            package = self.__missing__(*args, **kwargs)

        return package.load()

    @property
    def entry(self) -> LazyCall[_TFyRepository]:
        return LazyCall(self, handler=lambda s, p: s.load(p))
