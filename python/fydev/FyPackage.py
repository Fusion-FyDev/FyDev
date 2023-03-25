
import collections
import collections.abc
import os
import pathlib
import pprint
import typing
from copy import copy, deepcopy
from urllib.parse import urlparse

import yaml

from spdm.util.logger import logger
from spdm.util.utilities import (fetch_request, get_many_value, get_value, get_value_by_path,
                                 replace_tokens, set_value_by_path)

from .FyExecutor import FyExecutor

_TFyPackage = typing.TypeVar('_TFyPackage', bound='FyPackage')


class FyPackage(object):

    MODULE_FILE_NAME = "fy_module.yaml"

    def __init__(self, desc: typing.Union[str, typing.Mapping] = {},
                 install_dir=None,
                 envs: typing.Mapping = None,
                 **kwargs):
        super().__init__()

        self._desc = deepcopy(desc)

        self._envs = envs if envs is not None else {}

        install_prefix = pathlib.Path(
            get_value(self._envs, "install_prefix", None) or
            get_value(self._envs, "FY_INSTALL_PREFIX", None) or
            "~/fydev"
        )
        if install_dir is None:
            self._install_dir = install_prefix/self.tag.name / \
                f"{self.tag.version}-{self.tag.toolchain}{self.tag.versionsuffix}"
        self._install_dir = pathlib.Path(install_dir).expanduser()
        if self._install_dir.is_file:
            self._install_dir = self._install_dir.parent

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
        return self.install_dir.is_dir()

    def sanity_check(self) -> bool:
        return (self.install_dir/FyPackage.MODULE_FILE_NAME).is_file()

    def fetch_source(self) -> None:
        logger.info(f"Fetch source of package {self.tag_str}.")

    def build(self) -> None:
        logger.info(f"Build package {self.tag_str}.")

    def update_desc(self, repo) -> None:
        # if not package.valid:
        #     raise ModuleNotFoundError(f"Can not find module {tag}-{kwargs}")

        raise NotImplementedError()

    def install(self, install_prefix: pathlib.Path = None, force=False) -> None:
        if install_prefix is not None:
            self._install_prefix = pathlib.Path(install_prefix)

        logger.info(f"Install package {self.tag_str} to {self.install_dir}.")

        self.fetch_source()

        self.build()

        # 创建module目录，如果目录存在则报错
        self.install_dir.mkdir(mode=get_value(self._desc, "mode", 511), parents=force, exist_ok=force)

        self.install_description(force=force)

    def install_description(self) -> None:
        if not self.install_dir.is_dir():
            raise FileNotFoundError(self.install_dir)

        with open(self.install_dir/FyPackage.MODULE_FILE_NAME, mode="w") as fid:
            yaml.dump(self._desc, fid)

    def uninstall(self) -> None:
        self.install_dir.rmdir()

    def reinstall(self) -> None:
        self.uninstall(force=True)
        self.install(force=True)

    def load(self,  exec="", **kwargs) -> FyExecutor:
        """
            load module 为 FyExecutor
            path: package 中 sub-module 路径

        """
        exec = self._desc.setdefault("run", {}).setdefault("exec_file", exec)

        logger.info(f"Load package {self.tag_str} [exec:{exec}].")

        return FyExecutor(exec,
                          package=self,
                          session=collections.ChainMap(kwargs, self._envs))
