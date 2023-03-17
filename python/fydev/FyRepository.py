import collections
import collections.abc
import os
import pathlib
import pprint
import subprocess
import typing
import uuid

import requests
import yaml
from spdm.util.logger import logger

from .DefaultSortedDict import DefaultSortedDict


FY_MODULE_FILE_NAME = "fy_module"


def get_value_by_path(data, path, default_value):
    # 将路径按 '/' 分割成列表
    segments = path.split("/")
    # 初始化当前值为 data
    current_value = data
    # 遍历路径中的每一段
    for segment in segments:
        # 如果当前值是一个字典，并且包含该段作为键
        if isinstance(current_value, dict) and segment in current_value:
            # 更新当前值为该键对应的值
            current_value = current_value[segment]
        else:
            # 否则尝试将该段转换为整数索引
            try:
                index = int(segment)
                # 如果当前值是一个列表，并且索引在列表范围内
                if isinstance(current_value, list) and 0 <= index < len(current_value):
                    # 更新当前值为列表中对应索引位置的元素
                    current_value = current_value[index]
                else:
                    # 否则返回默认值
                    return default_value
            except ValueError:
                # 如果转换失败，则返回默认值
                return default_value
    # 返回最终的当前值
    return current_value


def set_value_by_path(data, path, value):
    # 将路径按 '/' 分割成列表
    segments = path.split("/")
    # 初始化当前字典为 data
    current_dict = data
    # 遍历路径中除了最后一段以外的每一段
    for segment in segments[:-1]:
        # 如果当前字典包含该段作为键，并且对应的值也是一个字典
        if segment in current_dict and isinstance(current_dict[segment], dict):
            # 更新当前字典为该键对应的子字典
            current_dict = current_dict[segment]
        else:
            # 尝试将该段转换为整数索引
            try:
                index = int(segment)
                # 如果当前字典不包含该段作为键，或者对应的值不是一个列表
                if segment not in current_dict or not isinstance(current_dict[segment], list):
                    # 创建一个空列表作为该键对应的值
                    current_dict[segment] = []
                # 更新当前字典为该键对应的子列表
                current_dict = current_dict[segment]
            except ValueError:
                # 如果转换失败，则抛出一个异常，提示无法继续查找
                raise Exception(f"Cannot find {segment} in {current_dict}")
    # 在当前字典中设置最后一段作为键，给定的值作为值
    last_segment = segments[-1]
    # 尝试将最后一段转换为整数索引
    try:
        index = int(last_segment)
        # 如果当前字典包含最后一段作为键，并且对应的值是一个列表
        if last_segment in current_dict and isinstance(current_dict[last_segment], list):
            # 判断索引是否在列表范围内
            if 0 <= index < len(current_dict[last_segment]):
                # 更新列表中对应索引位置的元素为给定值
                current_dict[last_segment][index] = value
            else:
                # 否则抛出一个异常，提示无法更新列表元素
                raise Exception(f"Index {index} out of range for list {current_dict[last_segment]}")
        else:
            # 否则直接设置最后一段作为键，给定值作为值（此时会创建一个单元素列表）
            current_dict[last_segment] = value
    except ValueError:
        # 如果转换失败，则直接设置最后一段作为键，给定值作为值（此时会覆盖原有列表）
        current_dict[last_segment] = value


def replace_tokens(value, env):
    if isinstance(value, str):
        # 使用 format_map() 方法进行替换，并更新 document 中的 value
        return value.format_map(env)
    elif isinstance(value, list):
        return [replace_tokens(v, env) for v in value]
    elif isinstance(value, dict):
        return {k: replace_tokens(v, env) for k, v in value.items()}
    else:
        return value


def fetch_request(self,  path: str, *args, **kwargs) -> typing.Dict:
    """
        根据路径拖回并解析module_file
    """
    content = None
    try:
        if path.startswith('http://') or path.startswith('https://'):
            # path is a uri
            if not self._envs.get("enable_remote_access", False):
                logger.warning(f"Disable remote access to description files! {path}")
            else:  # TODO: 返回多个desc文件
                response = requests.get(path)
                if response.status_code == 200:
                    # request is successful
                    content = yaml.safe_load(response.text)  # parse the response text as yaml
        elif path.startswith("git://") or path.startswith("git+https://"):
            logger.warning(f"NotImplemented: git is not supported! ignored path {path}")
        elif os.path.isfile(path):
            # file exists
            with open(path, 'r') as file:
                content = yaml.safe_load(file)  # parse the file content as yaml
        # elif not strict:
        #     # TODO: 进行模糊查找
        else:
            logger.debug(f"Ignored path {path}")

    except Exception as error:
        logger.debug(f"Invalid path: {path} Error:{error}")

    return content


class PathManager(DefaultSortedDict):
    """
     以有序字典管理路径，根据 键值作为前缀匹配path ，得到相应的实际目录。
    """

    def __init__(self,  *args,
                 envs={},
                 default_module_file: str = "fy_module.yaml",
                 name_suffix="{version}-{toolchain}{versionsuffix}",
                 **kwargs):
        super().__init__(list, *args, **kwargs)

        self._envs = envs

        self._module_file_name = default_module_file

        mod_file_ext = self._module_file_name.split('.')[1]

        self._module_file_suffix = [f"/{self._module_file_name}", f".{mod_file_ext}", ]

        self._name_suffix = name_suffix

    def generate_path(self, name: str,  **suffix) -> typing.Iterator[str]:
        """
            根据“描述符”generate可能的备选路径,
        """

        tag = self._suffix_template.format(**suffix)

        for key in self.keys()[::-1]:
            if not ((key == "" or key.endswith('.')) and name.startswith(key)):
                continue
            for prefix in self._paths[key]:

                path = prefix + "/" if not prefix.endswith('/') else prefix

                path = path + name[len(key):].replace('.', '/')

                if prefix.startswith("http://") or prefix.startswith("https://"):
                    # TODO：将suffix 转化为query，
                    yield f"{path}/{tag}"
                else:
                    for file_suffix in self._module_file_suffix:
                        yield f"{path}/{tag}{file_suffix}"

    def fetch_desc(self,  path: str, strict=True) -> typing.Dict:
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

        desc = fetch_request(path, strict=strict)

        envs = {
            # Module file 文件路径
            "FY_MODULE_FILE": path,
            # 当前Module目录，只当FY_MODULE_FILE路径为 x/x/x/fy_module.yaml 形式时有效
            "FY_MODULE_DIR":  ""
        }

        if path.endswith(f"/{self._module_file_name}"):
            envs["FY_MODULE_DIR"] = path[:-len(self._module_file_name)]

        return replace_tokens(desc, collections.ChainMap(envs, self._envs))

    def find(self,  name: str,   ** suffix) -> typing.Tuple[typing.Dict, str]:
        """
          返回第一个满足 name，suffix 的 module 描述文件内容和module所在路径
          若无法找到则，抛出异常 FileNotFoundError
        """
        desc = None
        for path in self.generate_path(name,  **suffix):
            path = path.format_map(self._envs)
            desc = self.fetch_desc(path)
            if desc is None:
                continue
            else:
                break
        if desc is None:
            raise ModuleNotFoundError(f"Can not find description file for {name}-{suffix}!")
        else:
            logger.debug(f"Get description  {name}-{suffix} from {path}.")

        return desc, path

    def glob(self, name: str, **suffix):
        """
            列出所有符合要求的module_path
        """
        return [path.format_map(self._envs) for path in self.generate_path(name, **suffix)]


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

        if sub_cls is None:
            raise ModuleNotFoundError(
                f"Cannot find the creator of the module described by the description!\n {pprint.pformat(desc)}!")
        else:
            return object.__new__(sub_cls)

    def __init__(self, desc, path=None, mode=511,  envs=None,  **kwargs):
        super().__init__()

        self._desc = desc
        self._mode = mode
        self._install_dir: pathlib.Path = pathlib.Path(path)
        self._envs = envs or {}

    def sanity_check(self) -> bool:
        return True

    def fetch_source(self) -> bool:
        pass

    def build(self) -> bool:
        pass

    def install(self, force=False) -> bool:

        self.fetch_source()

        self.build()

        # 创建module目录，如果目录存在则报错
        self._install_dir.mkdir(mode=self._mode, parents=force, exist_ok=force)

        self.install_description(force=force)

    def install_description(self):
        self._desc["install_dir"] = self._install_dir.as_posix()

        with open(self._install_dir/f"{FY_MODULE_FILE_NAME}.yaml", mode="w") as fid:
            yaml.dump(self._desc, fid)

    def uninstall(self) -> bool:
        os.rmdir(self._install_dir)

    def reinstall(self) -> bool:
        self.uninstall(force=True)
        self.install(force=True)

    def load(self) -> typing.Callable:

        execute: pathlib.Path = self._install_dir / get_value_by_path(self._desc, "run/execute", None)

        if not execute.exists():
            raise FileNotFoundError(f"Can not find file {execute}!")

        working_dir = os.getcwd()

        if not execute.exists():
            raise FileNotFoundError(execute)

        def _simple_call(*args, **kwargs):
            # logger.debug(f"CMD: {cmd} : {res}")
            cmd = " ".join([execute]+args
                           + [f"-{k}{v}" for k, v in kwargs.items() if len(k) == 1]
                           + [f"--{k} {v}" for k, v in kwargs.items() if len(k) > 1])

            logger.info(f"Execute Shell command [{working_dir}$ {cmd}]")
            # @ref: https://stackoverflow.com/questions/21953835/run-subprocess-and-print-output-to-logging
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    # env=self.envs,
                    shell=True,
                    cwd=working_dir
                )
                # process_output, _ = command_line_process.communicate()

                with process.stdout as pipe:
                    for line in iter(pipe.readline, b''):  # b'\n'-separated lines
                        logger.info(line)

                exitcode = process.wait()

            except (OSError, subprocess.CalledProcessError) as error:
                logger.error(
                    f"""Command failed! [{cmd}]
                        STDOUT:[{error.stdout}]
                        STDERR:[{error.stderr}]""")
                raise error
            return exitcode

        return _simple_call


class FyRepository:

    registry = {}

    tag_tempalte = "{name}-{version}-{toolchain}{versionsuffix}"

    def __init__(self, configure=None,  **kwargs):

        self._envs = {}

        self._default_file_mode = 511

        self._module_file_suffix = [f"/{FY_MODULE_FILE_NAME}.yaml", ".yaml"]

        # 软件包的安装目录,
        self._install_path = PathManager()

        # 软件包的安装目录,
        self._repository_path = PathManager()

        self._suffix_tempalte = "{version}-{toolchain}{versionsuffix}"

        logger.debug(f"Open FyModule repository ")

        self._envs = {k: v for k, v in os.environ.items() if k.startswith("FY_")}

        if isinstance(configure, collections.abc.Mapping):
            self._envs.update(configure)
        elif configure is not None:
            raise TypeError(f"Can not parser configure {configure}!")

        self._envs.update(kwargs)

    @property
    def envs(self) -> typing.Mapping[str, str]:
        return self._envs

    @property
    def install_path(self) -> typing.Mapping[str, list]:
        return self._install_path

    @property
    def default_install_path(self) -> pathlib.Path:
        return pathlib.Path(self._install_path[""][0])

    def __missing__(self, name, **suffix) -> typing.Tuple[typing.Dict, str]:

        # 当module 缺失时， 调用 install。参数 force=True 意味不必检查包是否存在
        self.install(name, **suffix, force=True)

        return self._install_path.find(name, **suffix)

    def load(self,  name: str, **suffix) -> typing.Any:
        try:
            # 从 install_path 查找 module
            module_desc, module_path = self._install_path.find(name, **suffix)
        except ModuleNotFoundError as error:
            # 若找不到，调用 __missing__
            module_desc, module_path = self.__missing__(name, **suffix)

        # 根据描述文件 load Module
        return FyHandler(module_desc, path=module_path).load()

    def install(self, name: str, force=False, **suffix) -> FyHandler:
        if not force:
            # 检查包是否已经安装
            try:
                module_desc, _ = self._install_path.find(name, **suffix)
                if module_desc is not None:
                    # 如果已经安装抛出异常
                    raise FileExistsError(f"Module {name}-{suffix} is installed!")
            except ModuleNotFoundError as error:
                pass
        # 从 module 仓库查找描述
        module_desc, _ = self._repository_path.find(name, **suffix)

        # 确定安装目录
        install_dir = self.default_install_path/(self._suffix_tempalte.format_map(suffix))

        handler = FyHandler(module_desc, path=install_dir, mode=self._default_file_mode)

        handler.install(force=force)

        handler.sanity_check()

        return handler

    def glob(self, *args, **kwargs):
        return self._install_path.glob(*args, **kwargs)
