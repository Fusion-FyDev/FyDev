
import collections
import collections.abc
import os
import pathlib
from urllib.parse import urlparse
import pprint
import typing
import yaml
from spdm.util.logger import logger
from ..FyPackage import FyPackage
from .util import get_value, fetch_request, replace_tokens
from copy import copy

FY_MODULE_FILE_NAME = "fy_module"

_TFyHandler = typing.TypeVar('_TFyHandler', bound='FyHandler')


class FyHandler(object):
    _registry = {}

    # 定义一个装饰器来自动注册子类到字典中

    @classmethod
    def register(cls, name=None, creator=None):
        if creator is None:
            # 返回一个装饰器函数
            def decorator(subclass):
                if name is None:
                    name = subclass.__name__
                # 注册子类
                cls._registry[name] = subclass
                # 返回子类
                return subclass
            return decorator
        else:
            cls._registry[name] = creator
            return creator

    @classmethod
    def create(cls, desc, *args, **kwargs) -> _TFyHandler:
        sub_cls = cls._registry.get(desc.get("CLASS", None), None)

        """
            根据路径拖回并解析module_file
        """
        # desc = None
        # try:
        #     if path.startswith('http://') or path.startswith('https://'):
        #         # path is a uri
        #         if not self._envs.get("enable_remote_access", False):
        #             logger.warning(f"Disable remote access to description files! {path}")
        #         else:  # TODO: 返回多个desc文件
        #             response = requests.get(path)
        #             if response.status_code == 200:
        #                 # request is successful
        #                 desc = yaml.safe_load(response.text)  # parse the response text as yaml
        #     elif path.startswith("git://") or path.startswith("git+https://"):
        #         logger.warning(f"NotImplemented: git is not supported! ignored path {path}")
        #     elif os.path.isfile(path):
        #         # file exists
        #         with open(path, 'r') as file:
        #             desc = yaml.safe_load(file)  # parse the file content as yaml
        #     elif not strict:
        #         # TODO: 进行模糊查找
        #         os.path.glob()
        #     else:
        #         logger.debug(f"Ignored path {path}")

        # except Exception as error:
        #     logger.debug(f"Invalid path: {path} Error:{error}")
        envs = {
            # Module file 文件路径
            "FY_MODULE_FILE": uri,
            # 当前Module目录，只当FY_MODULE_FILE路径为 x/x/x/fy_module.yaml 形式时有效
            "FY_MODULE_DIR":  ""
        }
        uri = urlparse(uri)
        if uri.scheme in ['http', 'https', 'local', 'file', '']:
            desc = fetch_request(uri, strict=strict)
            if uri.path.endswith(f"/{self._module_file_name}"):
                envs["FY_MODULE_DIR"] = uri[:-len(self._module_file_name)]
        else:

        desc = replace_tokens(desc, collections.ChainMap(envs, self._envs))
        handler = FyHandler.create(uri)
        if not handler.valid:
            continue
        if sub_cls is None:
            raise ModuleNotFoundError(
                f"Cannot find the creator of the module described by the description!\n {pprint.pformat(desc)}!")
        else:
            return object.__new__(sub_cls)

    def __init__(self, desc, path=None, mode=511,  session=None,  **kwargs):
        super().__init__()

        self._desc: dict = desc
        self._mode = mode
        self._install_prefix: pathlib.Path = pathlib.Path(path)
        self._session = session or {}

    @property
    def name(self) -> str:
        return self._desc.get("name", "unnamed")

    @property
    def version(self) -> str:
        return self._desc.get("version", "")

    @property
    def toolchain(self) -> str:
        return self._desc.get("toolchain", "")

    @property
    def suffix(self) -> str:
        return self._desc.get("suffix", "")

    @property
    def tag(self) -> str:
        return f"{self.version}-{self.toolchain}-{self.suffix}"

    @property
    def install_dir(self) -> pathlib.Path:
        return self._install_prefix/self.name/self.tag

    @property
    def description(self) -> dict:
        return self._desc

    @property
    def valid(self) -> bool:
        return len(self.description) > 0

    @property
    def installed(self) -> bool:
        return self.install_dir.is_dir()

    def sanity_check(self) -> bool:
        return (self.install_dir/f"{FY_MODULE_FILE_NAME}.yaml").is_file()

    def fetch_source(self) -> bool:
        pass

    def build(self) -> bool:
        pass

    def install(self, install_dir: pathlib.Path, force=False) -> None:

        self.fetch_source()

        self.build()

        # 创建module目录，如果目录存在则报错
        self.install_dir.mkdir(mode=self._mode, parents=force, exist_ok=force)

        self.install_description(force=force)

    def install_description(self) -> None:
        self._desc["install_dir"] = self.install_dir.as_posix()

        with open(self.install_dir/f"{FY_MODULE_FILE_NAME}.yaml", mode="w") as fid:
            yaml.dump(self._desc, fid)

    def uninstall(self) -> None:
        self.install_dir.rmdir()

    def reinstall(self) -> None:
        self.uninstall(force=True)
        self.install(force=True)

    class _LazyEval(object):

        def __init__(self, handler: _TFyHandler) -> None:
            super().__init__()
            self._handler = handler
            self._path = []

        def _duplicate(self):
            other = object.__new__(self.__class__)
            other._handler = self._handler
            other._path = copy(self._path)
            return other

        def _child(self, k):
            other: FyHandler._LazyEval = self._duplicate()
            other._path = self._path+[k]
            return other

        def __getattr__(self, k: str):
            return self._child(k)

        def __getitem__(self, k):
            return self._child(k)

        def __call__(self, *args, **kwargs):
            return self._handler.exec(self._path, *args, **kwargs)

    def load(self):
        return FyHandler._LazyEval(self)

    def exec(self, path, *args, **kwargs) -> typing.Any:
        raise NotImplementedError()
