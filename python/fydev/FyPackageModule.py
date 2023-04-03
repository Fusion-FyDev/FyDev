import os
import pathlib
import signal
import subprocess
from functools import cached_property

from spdm.util.logger import logger

from .FyPackage import FyPackage


@FyPackage.register("module")
class FyPackageModule(FyPackage):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._lmod_cmd = os.environ.get("LMOD_CMD", None)

        if self._lmod_cmd is None:
            raise RuntimeError(f"Lmod command not found. Please set the environment variable LMOD_CMD.")

        del self._desc["install_dir"]

    def _lmod(self, *args, **kwargs):

        process = subprocess.run([self._lmod_cmd, "python", *args],
                                 stderr=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 encoding="utf-8", **kwargs)

        exec(process.stdout)

        return process

    @cached_property
    def module_name(self) -> str:
        return f"{self.tag.name}/{self.tag_suffix}"

    @property
    def valid(self) -> bool:
        return self._lmod("is-avail", self.module_name).returncode == 0

    @property
    def installed(self) -> bool:
        return self.valid and self.install_dir.is_dir()

    @cached_property
    def install_dir(self) -> pathlib.Path:
        _install_dir = self._desc.get("install_dir", None)
        if _install_dir is None and self.valid:
            self.pre_load()
            _install_dir = os.environ.get(f"EBROOT{self.tag.name.upper()}", None)
            self.post_load()
            if _install_dir is not None:
                self._desc["install_dir"] = _install_dir
                _install_dir = pathlib.Path(_install_dir).resolve().expanduser()

        if _install_dir is None:
            _install_dir = super().install_dir
        else:
            _install_dir = pathlib.Path(_install_dir).resolve().expanduser()
        return _install_dir

    def install(self, *args, **kwargs) -> None:
        if self.installed:
            pass
        elif not self.valid:
            raise RuntimeError(f"Can not install package {self.module_name} as module.")
        else:
            logger.warning(f"Package {self.module_name} is installed.")

    def install_description(self) -> None:
        self._desc["$class"] = "module"
        return super().install_description()

    def uninstall(self, force=True) -> None:
        raise RuntimeError(f"Can not uninstall 'module'!")

    def reinstall(self, force=True) -> None:
        raise RuntimeError(f"Can not uninstall 'module'!")

    def pre_load(self, *args, **kwargs):
        args, kwargs = super().pre_load(*args, **kwargs)
        self._lmod("load", self.module_name)
        return args, kwargs

    def post_load(self, *args, **kwargs):
        self._lmod("unload", self.module_name)
        return super().post_load(*args, **kwargs)

    def load(self, *args, **kwargs):
        self.pre_load()
        super().load(*args, **kwargs)
        self.post_load()
