import collections
import inspect
import os
import pathlib
import pprint
import shlex
import subprocess
import sys
from functools import cached_property
from pathlib import Path
from string import Template
from typing import List

from ..data.DataObject import DataObject
from ..util.dict_util import DictTemplate, deep_merge_dict
from ..util.logger import logger
from ..util.Signature import Signature
from ..util.sp_export import sp_find_module
from .Actor import Actor
from .Session import Session


class SpModule(Actor):

    def __init__(self, *args, envs=None, metadata=None,  **kwargs):
        super().__init__(metadata=metadata)

        self._envs = envs or {}
        self._args = args
        self._kwargs = kwargs
        self._inputs = None
        self._outputs = None
        self._envs["JOB_ID"] = self.job_id

    # def __del__(self):
    #     super().__del__()

    @cached_property
    def name(self):
        return str(self.metadata.annotation.name)

    @cached_property
    def root_path(self):
        module_root = os.environ.get(f"EBROOT{self.name.upper()}", None)
        if not module_root:
            logger.error(f"Load module '{self.name}' failed! ")
            raise RuntimeError(f"Load module '{self.name}' failed!")

        return pathlib.Path(module_root).expanduser()

    @property
    def envs(self):
        return collections.ChainMap(self._envs, {"metadata": self.metadata})

    def _execute_module_command(self, cmd, working_dir=None):
        # py_command = self._execute_process([f"{os.environ['LMOD_CMD']}", 'python', *args])
        # process = os.popen(f"{os.environ['LMOD_CMD']} python {' '.join(args)}  ")
        if isinstance(cmd, list):
            cmd = ' '.join(cmd)

        lmod_cmd = os.environ.get('LMOD_CMD', None)

        if not lmod_cmd:
            raise RuntimeError(f"Can not find lmod!")

        # process = subprocess.run([lmod_cmd, "python", *cmd], capture_output=True)

        mod_cmd = ' '.join([lmod_cmd, "python", cmd])
        process = os.popen(mod_cmd, mode='r')
        py_command = process.read()
        exitcode = process.close()
        if not exitcode:
            res = exec(py_command)
            logger.debug(f"MODULE CMD: module {cmd}")
        else:
            logger.error(f"Module command failed! [module {cmd}] [exitcode: {exitcode}] ")
            raise RuntimeError(f"Module command failed! [module {cmd}] [exitcode: {exitcode}]")

        return res

    def _execute_process(self, cmd, working_dir='.'):
        # logger.debug(f"CMD: {cmd} : {res}")
        logger.info(f"Execute Shell command [{working_dir}$ {' '.join(cmd)}]")
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

    def _execute_object(self, cmd):
        return NotImplemented

    def _execute_script(self, cmds):
        if cmds is None:
            return None
        elif isinstance(cmds, collections.abc.Sequence) and not isinstance(cmds, str):
            pass
        else:
            cmds = [cmds]

        res = None

        for cmd in cmds:
            if isinstance(cmd, collections.abc.Mapping):
                res = self._execute_object(cmd)
            elif isinstance(cmd, str):
                if cmd.startswith("module "):
                    res = self._execute_module_command(cmd[len("module "):])
                elif not self._only_module_command:
                    res = self._execute_process(cmd)
                else:
                    raise RuntimeError(f"Illegal command! [{cmd}] Only 'module' command is allowed.")
            elif isinstance(cmd, collections.abc.Sequence):
                res = self._execute_script(cmd)
            elif not cmd:
                res = None
            else:
                raise NotImplementedError(cmd)

        return res

    def _convert_data(self, data, metadata, envs):

        if metadata is None:
            metadata = {}

        metadata = format_string_recursive(metadata, envs)

        if data is None:
            data = metadata.get("default", None)

        elif isinstance(data, str):
            data = format_string_recursive(data, envs)
        elif isinstance(data, collections.abc.Mapping):
            format_string_recursive(data,  l_envs)
            data = {k: (v if k[0] == '$' else self._convert_data(v)) for k, v in data.items()}
        elif isinstance(data, collections.abc.Sequence):
            format_string_recursive(data,  l_envs)
            data = [self._convert_data(v) for v in data]

        if isinstance(data, collections.abc.Mapping) and "$class" in data:
            d_class = data.get("$class", None)
            p_class = p_in.get("$class", None)
            d_schema = data.get("$schema", None)
            p_schema = p_in.get("$schema", None)
            if d_class == p_class and (d_schema or p_schema) == p_schema:
                obj = self.create_dobject(_metadata=collections.ChainMap(deep_merge_dict(data, metadata), envs))
            else:
                data = self.create_dobject(_metadata=collections.ChainMap(data, envs))
                obj = self.create_dobject(data, _metadata=collections.ChainMap(p_in, envs))
        else:
            obj = self.create_dobject(data, _metadata=metadata)
        return obj

    def create_dobject(self, data,  _metadata=None, *args, envs=None, **kwargs):

        if not envs:
            envs = {}

        _metadata = _metadata or {}

        if isinstance(_metadata, str):
            _metadata = {"$class": _metadata}

        if isinstance(data, collections.abc.Mapping) and "$class" in data:
            if (_metadata.get("$class", None) or data["$class"]) != data["$class"]:
                raise RuntimeError(f"Class mismatch! {_metadata.get('$class',None)}!={ data['$class']}")
            _metadata = deep_merge_dict(data, _metadata or {})
            data = None

        if "default" in _metadata:
            if data is None:
                data = _metadata["default"]
            del _metadata["default"]

        if isinstance(data, collections.abc.Mapping) and "$ref" in data:
            data = envs.get(data["$ref"], None)

        if hasattr(envs.__class__, "apply"):
            if isinstance(data, (str, collections.abc.Mapping)):
                data = envs.apply(data)
            if isinstance(_metadata, (str, collections.abc.Mapping)):
                _metadata = envs.apply(_metadata)

        if isinstance(data, collections.abc.Mapping):
            data = {k: self.create_dobject(v, envs=envs) for k, v in data.items()}
        elif isinstance(data, list):
            data = [self.create_dobject(v, envs=envs) for v in data]

        if _metadata is None:
            return data
        elif isinstance(_metadata, str):
            _metadata = {"$class": _metadata}
        elif not isinstance(_metadata, collections.abc.Mapping):
            raise TypeError(type(_metadata))

        n_cls = _metadata.get("$class", "")

        n_cls = n_cls.replace("/", ".").lower()
        n_cls = DataObject.associations.get(n_cls, n_cls)

        if not n_cls:
            return data
        if inspect.isclass(n_cls):
            return n_cls(data) if data is not None else None
        elif isinstance(data, DataObject) and data.metadata["$class"] == n_cls:
            return data
        else:
            res = DataObject(collections.ChainMap({"$class": n_cls}, _metadata), *args,  **kwargs)
            if data is not None:
                res.update(data)
            return res

    @property
    def inputs(self):
        """
            Collect and convert inputs
        """
        if self._inputs is not None:
            return self._inputs

        cwd = pathlib.Path.cwd()

        os.chdir(self.envs.get("WORKING_DIR", None) or cwd)

        envs_map = DictTemplate(collections.ChainMap(
            {"inputs": collections.ChainMap(self._kwargs, {"_VAR_ARGS_": self._args})}, self.envs))

        args = []
        kwargs = {}
        for p_name, p_metadata in self.metadata.in_ports:
            if p_name != '_VAR_ARGS_':
                kwargs[p_name] = self.create_dobject(self._kwargs.get(p_name, None),
                                                     _metadata=p_metadata, envs=envs_map)
            elif not isinstance(p_metadata, list):
                args = [self.create_dobject(arg,  _metadata=p_metadata, envs=envs_map) for arg in self._args]
            else:
                l_metada = len(p_metadata)
                args = [self.create_dobject(arg, _metadata=p_metadata[min(idx, l_metada-1)], envs=envs_map)
                        for idx, arg in enumerate(self._args)]

        self._inputs = args, kwargs

        os.chdir(cwd)
        return self._inputs

    @property
    def outputs(self):
        if self._outputs is not None:
            return self._outputs
        cwd = pathlib.Path.cwd()
        os.chdir(self.envs.get("WORKING_DIR", None) or cwd)

        result = self.run() or {}

        inputs = self.inputs[1]

        envs_map = DictTemplate(collections.ChainMap({"RESULT": result}, {"inputs": inputs}, self.envs))

        # for p_name, p_metadata in self.metadata.out_ports:

        #     p_metadata = envs_map.apply(p_metadata)

        #     data = result.get(p_name, None) or p_metadata["default"]

        #     if not data:
        #         data = None

        #     outputs[p_name] = self.create_dobject(data, _metadata=p_metadata)

        outputs = {p_name: self.create_dobject(result.get(p_name, None),
                                               _metadata=p_metadata, envs=envs_map) for p_name, p_metadata in self.metadata.out_ports}

        self._outputs = collections.ChainMap(
            outputs, {k: v for k, v in result.items() if k not in self.metadata.out_ports})

        self._inputs = None
        os.chdir(cwd)
        return self._outputs

    def preprocess(self):
        logger.debug(f"Preprocess: {self.__class__.__name__}")
        self._execute_script(self.metadata.prescript)

    def postprocess(self):
        logger.debug(f"Postprocess: {self.__class__.__name__}")
        self._execute_script(self.metadata.postscript)

    def execute(self):
        logger.debug(f"Execute: {self.__class__.__name__}")
        return None

    def run(self):

        args, kwargs = self.inputs

        self.preprocess()

        error_msg = None

        try:
            logger.debug(f"Execute Start: {self.metadata.annotation.label}")
            res = self.execute(*args, **kwargs)
            logger.debug(f"Execute Done : {self.metadata.annotation.label}")
        except Exception as error:
            error_msg = error
            logger.error(f"Execute Error! {error}")
            res = None

        self.postprocess()

        if error_msg is not None:
            raise error_msg

        return res


class SpModuleLocal(SpModule):
    """Call subprocess/shell command
    {PKG_PREFIX}/bin/xgenray
    """

    script_call = {
        ".py": sys.executable,
        ".sh": "bash",
        ".csh": "tcsh"
    }

    def __init__(self, *args, working_dir=None, **kwargs):
        super().__init__(*args, **kwargs)

        working_dir = working_dir or Session.current().cwd

        if isinstance(working_dir, str):
            working_dir = pathlib.Path(working_dir)

        working_dir /= f"{self.job_id}"
        working_dir = working_dir.expanduser().resolve()

        working_dir.mkdir(exist_ok=False, parents=True)

        self._working_dir = working_dir

        self._envs["WORKING_DIR"] = working_dir

        logger.debug(f"Initialize: {self.__class__.__name__} at {self.working_dir} ")

    # def __del__(self):
    #     logger.debug(f"Finalize: {self.__class__.__name__} ")

    @property
    def working_dir(self):
        return self._working_dir

    @property
    def inputs(self):
        if self._inputs is not None:
            return self._inputs

        pwd = pathlib.Path.cwd()
        os.chdir(self.working_dir)
        res = super().inputs
        os.chdir(pwd)
        return res

    def execute(self, *args, **kwargs):
        module_name = str(self.metadata.annotation.name)

        module_root = os.environ.get(f"EBROOT{module_name.upper()}", None)

        if not module_root:
            logger.error(f"Load module '{module_name}' failed! {module_root}")
            raise RuntimeError(f"Load module '{module_name}' failed!")

        module_root = pathlib.Path(module_root).expanduser()

        exec_file = module_root / str(self.metadata.run.exec)

        exec_file.resolve()

        try:
            exec_file.relative_to(module_root)
        except ValueError:
            logger.error(f"Try to call external programs [{exec_file}]! module_root={module_root}")
            raise RuntimeError(f"It is forbidden to call external programs! [{exec_file}]!  module_root={module_root}")

        command = []

        if not exec_file.exists():
            raise FileExistsError(module_root/exec_file)
        elif exec_file.suffix in SpModuleLocal.script_call.keys():
            command = [SpModuleLocal.script_call[exec_file.suffix], exec_file.as_posix()]
        elif os.access(exec_file, os.X_OK):
            command = [exec_file.as_posix()]
        else:
            raise TypeError(f"File '{exec_file}'  is not executable!")

        cmd_arguments = str(self.metadata.run.arguments)

        try:
            arguments = cmd_arguments.format_map(collections.ChainMap({"VAR_ARGS": args}, kwargs,  self.envs))
        except KeyError as key:
            raise KeyError(f"Missing argument {key} ! [ {cmd_arguments} ]")

        command.extend(shlex.split(arguments))

        working_dir = self.envs.get("WORKING_DIR", "./")

        exitcode = self._execute_process(command, working_dir)
        # try:
        #     command_line_process = subprocess.Popen(
        #         command,
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.STDOUT,
        #         # env=self.envs,
        #         shell=True,
        #         cwd=working_dir
        #     )
        #     # process_output, _ = command_line_process.communicate()
        #     with command_line_process.stdout as pipe:
        #         for line in iter(pipe.readline, b''):  # b'\n'-separated lines
        #             logger.info(line)
        #     exitcode = command_line_process.wait()
        # except (OSError, subprocess.CalledProcessError) as error:
        #     logger.error(
        #         f"""Command failed! [{command}]
        #            STDOUT:[{error.stdout}]
        #            STDERR:[{error.stderr}]""")
        #     raise error

        return {"EXITCODE": exitcode}


class SpModulePy(SpModule):
    def __init__(self, *args,   **kwargs):
        super().__init__(*args, **kwargs)

        self._path_cache = []

    def preprocess(self):
        super().preprocess()
        self._path_cache = sys.path
        pythonpath = os.environ.get('PYTHONPATH', []).split(':')
        if not not pythonpath:
            sys.path.extend(pythonpath)

    def postprocess(self):
        super().preprocess()
        if not not self._path_cache:
            sys.path.clear()
            sys.path.extend(self._path_cache)

    def execute(self, *args, **kwargs):
        root_path = self.root_path

        pythonpath = [root_path/p for p in str(self.metadata.run.pythonpath or '').split(':') if not not p]

        func_name = str(self.metadata.run.exec)

        func = sp_find_module(func_name, pythonpath=pythonpath)

        if callable(func):
            logger.info(f"Execute Py-Function [ {func_name}]")
            res = func(*args, **kwargs)
        else:
            raise RuntimeError(f"Can not load py-function {func_name}")

        return res
