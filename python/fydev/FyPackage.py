
import collections
import collections.abc
import os
import pathlib
import pprint
import typing
from copy import copy, deepcopy
from urllib.parse import urlparse, ParseResult

import yaml

from spdm.util.logger import logger
from spdm.util.utilities import (fetch_request, get_many_value, get_value, get_value_by_path,
                                 replace_tokens, set_value_by_path)

from .FyExecutor import FyExecutor

_TFyPackage = typing.TypeVar('_TFyPackage', bound='FyPackage')


class FyPackage(object):

    MODULE_FILE_NAME = "fy_module.yaml"

    def __init__(self,
                 description: typing.Mapping = {},
                 envs: typing.Mapping = None,
                 install_dir=None,
                 modulefile_url: ParseResult = None,
                 **kwargs):
        super().__init__()

        self._desc: dict = deepcopy(description)

        self._envs = collections.ChainMap(kwargs, envs) if envs is not None else kwargs

        # if url is not None and url.scheme in ["file", "local", ""]:
        #         install_dir = pathlib.Path(url.path).expanduser().parent
        #     else:
        #         install_dir = None

        # if install_dir is None:
        #     install_prefix = pathlib.Path(
        #         get_value(self._envs, "install_prefix", None) or
        #         get_value(self._envs, "FY_INSTALL_PREFIX", None) or
        #         "~/fydev"
        #     )
        #     install_dir = install_prefix/self.tag.name / \
        #         f"{self.tag.version}-{self.tag.toolchain}{self.tag.versionsuffix}"
        # if self._install_dir.is_file:
        #     self._install_dir = self._install_dir.parent
        if install_dir is not None:
            self._install_dir = pathlib.Path(install_dir).expanduser()
        elif modulefile_url.scheme in ["file", "local", ""] and modulefile_url.path.endswith(FyPackage.MODULE_FILE_NAME):
            self._install_dir = pathlib.Path(modulefile_url.path).expanduser().parent
        else:
            self._install_dir = None

    Tag = collections.namedtuple("Tag", ["name", "version", "toolchain", "versionsuffix"])

    def __str__(self) -> str:
        return self.tag_str

    @ property
    def tag(self):
        information: dict = self._desc.setdefault("information", {})
        return FyPackage.Tag(name=information.get("name", "unnamed"),
                             version=information.get("version", "1.0.0"),
                             toolchain=information.get("toolchain", "GCC"),
                             versionsuffix=information.get("versionsuffix", ""))

    @ property
    def tag_str(self) -> str:
        return f"{self.tag.name}-{self.tag.version}-{self.tag.toolchain}{self.tag.versionsuffix}"

    @ property
    def install_dir(self) -> pathlib.Path:
        return self._install_dir

    @ property
    def description(self) -> dict:
        return self._desc

    @ property
    def valid(self) -> bool:
        return len(self.description) > 0

    @ property
    def installed(self) -> bool:
        return self._install_dir is not None and self._install_dir.is_dir()

    def sanity_check(self) -> bool:
        return (self.install_dir/FyPackage.MODULE_FILE_NAME).is_file()

    def fetch_source(self) -> None:
        logger.info(f"Fetch source of package {self.tag_str}.")

    def build(self) -> None:
        logger.info(f"Build package {self.tag_str}.")

    def test(self) -> None:
        logger.info(f"Test package {self.tag_str}.")

    def deploy(self) -> None:
        logger.info(f"Deploy package {self.tag_str}.")

    def update_description(self, desc: typing.Mapping, force=True) -> None:
        """
            从repo查找，并更新 package 的描述信息
        """
        logger.debug(desc)
        self._desc.update(desc)

    def install(self, install_dir: pathlib.Path = None, force=False) -> None:
        if self.installed and not force:
            raise FileExistsError(f"Package {self.tag_str} is already intalled !")
        elif self.installed:
            self.uninstall(force=force)

        if install_dir is not None:
            install_dir = pathlib.Path(install_dir)
        elif self._install_dir is not None:
            install_dir = self._install_dir
        else:
            raise ValueError(f"Install directory is not specified !")

        logger.info(f"Install package {self.tag_str} to {install_dir}.")

        self._install_dir = install_dir

        # 创建module目录，如果目录存在则报错
        self.install_dir.mkdir(mode=get_value(self._desc, "mode", 511), parents=force, exist_ok=force)

        self.fetch_source()

        self.build()

        self.test()

        self.deploy()

        self.install_description()

    def install_description(self) -> None:
        if not self.install_dir.is_dir():
            raise FileNotFoundError(self.install_dir)

        with open(self.install_dir/FyPackage.MODULE_FILE_NAME, mode="w") as fid:
            yaml.dump(self._desc, fid)

    def uninstall(self, force=True) -> None:
        self.install_dir.rmdir()

    def reinstall(self, force=True) -> None:
        self.uninstall(force=force)
        self.install(force=force)

    def load(self,  exec="", **kwargs) -> FyExecutor:
        """
            load module 为 FyExecutor
            path: package 中 sub-module 路径

        """
        if not self.installed:
            raise ModuleNotFoundError(self.tag_str)

        exec = self._desc.setdefault("run", {}).setdefault("exec", exec)

        logger.info(f"Load package {self.tag_str} [exec:{exec}].")

        return FyExecutor(exec,
                          package=self,
                          session=collections.ChainMap(kwargs, self._envs))
