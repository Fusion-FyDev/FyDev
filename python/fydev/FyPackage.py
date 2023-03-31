import collections
import collections.abc
import os
import pathlib
import shutil
import typing
from copy import copy, deepcopy
from functools import cached_property
from urllib.parse import urlparse
from urllib.request import urlopen

import yaml
from spdm.util.logger import logger
from spdm.util.misc import get_value, replace_tokens

from .FyCommon import *
from .FyExecutor import FyExecutor

_TFyPackage = typing.TypeVar('_TFyPackage', bound='FyPackage')

FY_MODULE_TEMPLTE = {
    "$class": "FyPackage",
    "$id": "{name}-{version}-{toolchain}{versionsuffix}",
    "information": {
        "name": "{name}",
        "version": "{version}",
        "toolchain": "{toolchain}",
        "versionsuffix": "{versionsuffix}",
    },
    "install_dir": "{FY_INSTALL_DIR}/{name}/{version}-{toolchain}{versionsuffix}",
    "run": {"exec": "{install_dir}/bin/{exec}"},
}


class FyPackage(object):
    MODULE_FILE_NAME = "fy_module.yaml"

    _registry = {}

    @classmethod
    def register(cls, name: str):
        def _register(cls):
            cls._registry[name] = cls
            return cls

        return _register

    @staticmethod
    def _parser_description(desc: typing.Union[str, typing.Mapping[str, typing.Any]] = None,
                            version=None, toolchain="", versionsuffix="", envs={},
                            **kwargs):
        """
        Parser description, which can be a string, a mapping, or None.
        If description is a string, it can be a path to a file, a url, or a tag.
        If description is a mapping, it must be a valid description.
        If description is None, an empty description will be created.

        :param desc: a string, a mapping, or None
        :param version: version
        :param toolchain: toolchain
        :param versionsuffix: version suffix
        :param kwargs: additional arguments
        """
        tokens = {"version": version,
                  "toolchain": toolchain,
                  "versionsuffix": versionsuffix}

        if isinstance(desc, collections.abc.Mapping):
            pass
        elif desc is None:
            desc = deepcopy(FY_MODULE_TEMPLTE)
        elif not isinstance(desc, str):
            raise TypeError(type(desc))
        else:
            url = desc.format_map(os.environ)
            desc = deepcopy(FY_MODULE_TEMPLTE)
            desc["$url"] = url
            url = urlparse(url)

            if url.query and url.scheme not in ['http', 'https']:
                # convert query string to dict
                tokens.update(dict(qc.split("=") for qc in url.query.split("&")))

            if url.scheme in ['http', 'https']:
                response = urlopen(url)
                if response.status_code == 200:
                    # request is successful
                    desc.update(yaml.safe_load(response.text))  # parse the response text as yaml
                else:
                    raise ModuleNotFoundError(url)
            elif url.scheme in ['local', 'file']:
                path = url.netloc+url.path
                if not os.path.isfile(path):
                    raise ModuleNotFoundError(path)

                # file exists
                with open(path, 'r') as file:
                    desc.update(yaml.safe_load(file))  # parse the file content as yaml

                if path.endswith(FyPackage.MODULE_FILE_NAME):
                    desc["install_dir"] = pathlib.Path(os.path.dirname(path))
            elif url.scheme == '':
                desc = FY_MODULE_TEMPLTE
                tokens["name"] = url.path.replace('.', '/')
            else:
                desc["$class"] = url.scheme
                tokens["name"] = (url.netloc+url.path).replace('.', '/')

        # 遍历desc，对其中类型为str的value，用tokens做format_map

        desc = replace_tokens(desc,  collections.ChainMap(tokens, envs))

        return desc, kwargs

    @classmethod
    def create(cls,  *args,  **kwargs) -> _TFyPackage:
        """
        Create a FyPackage instance.
        """
        desc, kwargs = FyPackage._parser_description(*args, **kwargs)  # Parser description

        class_desc = desc.get("$class", None)  # get class description

        if class_desc in [None, 'FyPackage']:  # default class
            return FyPackage(desc, ** kwargs)
        elif class_desc in cls._registry:  # registered class
            return cls._registry[class_desc](desc, **kwargs)
        else:  # unknown class
            raise ModuleNotFoundError(class_desc)

    def __init__(self,  *args, envs=None, **kwargs):
        """
        Initialize a FyPackage instance.
        :param args: description, version, toolchain, versionsuffix
        :param session: session information for the package
        :param kwargs: additional arguments
        """
        super().__init__()

        self._desc, kwargs = self._parser_description(*args, **kwargs)

        self._desc.update(kwargs)  # update description with additional arguments

        self._desc["$id"] = self.id

        self._envs = envs

    Tag = collections.namedtuple("Tag", ["name", "version", "toolchain", "versionsuffix"],
                                 defaults=("", "", "", ""))

    def __str__(self) -> str:
        return self.id

    @property
    def tag(self):
        information: dict = self._desc.get("information", {})
        return FyPackage.Tag(name=information.get("name", "unnamed"),
                             version=information.get("version", "1.0.0"),
                             toolchain=information.get("toolchain", "dummy"),
                             versionsuffix=information.get("versionsuffix", ""))

    @property
    def tag_suffix(self) -> str:
        suffix = str(self.tag.version)
        if self.tag.toolchain not in ['', None]:
            suffix += f"-{self.tag.toolchain}{self.tag.versionsuffix}"
        return suffix

    @property
    def tag_path(self) -> str:
        return f"{self.tag.name}/{self.tag_suffix}"

    @property
    def id(self) -> str:
        return f"{self.tag.name}-{self.tag_suffix}"

    @property
    def description(self) -> dict:
        return self._desc

    @property
    def valid(self) -> bool:
        return len(self.description) > 0

    @cached_property
    def install_dir(self) -> pathlib.Path:
        return pathlib.Path(self._desc.setdefault("install_dir", f"{FY_INSTALL_DIR}/{self.tag_path}")).resolve().expanduser()

    @property
    def installed(self) -> bool:
        return self.install_dir is not None and self.install_dir.is_dir()

    def sanity_check(self) -> bool:
        return (self.install_dir/FyPackage.MODULE_FILE_NAME).is_file()

    @property
    def source_dir(self) -> pathlib.Path:
        return pathlib.Path(FY_SOURCE_DIR)/self.tag.name

    def fetch_source(self) -> None:
        logger.info(f"Fetch source of  {self.id} to {self.source_dir}.")

    @property
    def build_dir(self) -> pathlib.Path:
        return pathlib.Path(FY_BUILD_DIR)/self.tag.name / \
            f"{self.tag.version}-{self.tag.toolchain}{self.tag.versionsuffix}"

    def build(self) -> None:
        logger.info(f"Build {self.id} in {self.build_dir}.")

    def test(self) -> None:
        logger.info(f"Test {self.id} in {self.build_dir}.")

    def deploy(self) -> None:
        """
        Deploy the package to the specified directory, or the default directory.
        Default directory is $FY_INSTALL_PREFIX/$name/$version-$toolchain$versionsuffix
        or ~/fydev/$name/$version-$toolchain$versionsuffix if $FY_INSTALL_PREFIX is not set.

        :param install_dir: the directory to deploy the package

        """

        if not self.install_dir.exists():
            # 创建package目录，如果目录存在则报错
            self.install_dir.mkdir(mode=get_value(self._desc, "mode", 511), parents=True, exist_ok=False)

        logger.info(f"Deploy {self.id} to {self.install_dir}.")

    def install(self, install_dir: str = None, exist_ok=True) -> None:
        """
        安装package,
        如果已经安装，则先卸载, 然后重新安装,
        如果force为True , 则强制安装, 不管是否已经安装

        :param install_dir: 安装目录
        :param force: 是否强制安装
        """

        if install_dir is None:
            install_dir = self._desc.get("install_dir", None)

        if install_dir is None:
            # default install prefix
            install_prefix = self._desc.get("install_prefix", None) or FY_INSTALL_DIR

            install_dir = pathlib.Path(install_prefix)/self.tag.name / \
                f"{self.tag.version}-{self.tag.toolchain}{self.tag.versionsuffix}"
        else:
            install_dir = pathlib.Path(install_dir)

        install_dir = install_dir.expanduser()

        self._desc["install_dir"] = install_dir.as_posix()

        if self.installed:
            if exist_ok:
                return
            else:
                raise FileExistsError(f"Package {self.id} is already intalled !")

        logger.info(f"Install {self.id} .")

        self.fetch_source()

        self.build()

        self.test()

        self.deploy()

        self.install_description()

    def update_description(self, desc: typing.Mapping, force=True) -> None:
        """
            从repo查找，并更新 package 的描述信息
        """
        logger.debug(desc)
        self._desc.update(desc)

    def install_description(self) -> None:
        if not self.install_dir.is_dir():
            raise FileNotFoundError(self.install_dir)

        logger.info(f"Install description of {self.id} to {self.install_dir}.")

        with open(self.install_dir/FyPackage.MODULE_FILE_NAME, mode="w") as fid:
            yaml.dump(self._desc, fid)

    def uninstall(self, force=True) -> None:
        if self.install_dir is None or not self.install_dir.exists:
            return

        install_dir = self.install_dir
        # 清空并删除目录 self.install_dir
        if force:
            logger.info(f"Uninstall {self.id} at {self.install_dir}.")
            shutil.rmtree(install_dir)
            # os.removedirs(install_dir)
            # os.rmdir(install_dir)

    def reinstall(self, force=True) -> None:
        self.uninstall(force=force)
        self.install(force=force)

    def pre_load(self, *args, **kwargs):

        return args, kwargs

    def post_load(self, value=None):
        return value

    def load(self,  *args, **kwargs) -> FyExecutor:
        """
        加载package, 并返回一个FyExecutor对象
        """
        if not self.installed:
            self.install()

        if self._desc.get("install_dir", None) is None:
            self._desc["install_dir"] = self.install_dir.as_posix()
            self._desc = replace_tokens(self._desc, self._desc)
        return FyExecutor(*args, _description=self._desc.get("run", {}), _package=self,  ** kwargs)
