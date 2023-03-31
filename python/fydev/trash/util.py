from spdm.util.logger import logger
import requests
import yaml
import pathlib
import typing
import collections.abc
import os


def get_value_by_path(data, path: str, default_value):
    # 将路径按 '/' 分割成列表
    if isinstance(path, str):
        segments = path.split("/")
    elif isinstance(path, collections.abc.Sequence):
        segment = path
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

    return True


def get_value(*args, **kwargs) -> typing.Any:
    return get_value_by_path(*args, **kwargs)


def get_many_value(d: collections.abc.Mapping, name_list: collections.abc.Sequence, default_value=None) -> collections.abc.Mapping:
    return {k: get_value(d, k, get_value(default_value, idx)) for idx, k in enumerate(name_list)}


def set_value(*args, **kwargs) -> bool:
    return set_value_by_path(*args, **kwargs)


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
    if isinstance(path, collections.abc.Mapping):
        return path
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
            logger.debug(f"Illegal path {path}")

    except Exception as error:
        logger.debug(f"Invalid path: {path} Error:{error}")

    return content
