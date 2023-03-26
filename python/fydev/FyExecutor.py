
import collections
import collections.abc

import inspect
import os
import pathlib
import pprint
import subprocess
import sys
import typing
import uuid
from functools import cached_property
from copy import copy

from spdm.util.logger import logger

from .util import get_value

_TFyExecutor = typing.TypeVar('_TFyExecutor', bound='FyExecutor')


class FyExecutor(object):

    def __init__(self, exec: typing.Union[str, list],  package=None, session: typing.Dict = None):
        """
            Create a FyExecutor object
            @param exec_file: the file to be executed
            @param package: the package that contains the file
            @param session: the session that contains the execution context
        """
        super().__init__()

        self._package = package  # type: FyPackage

        self._session = session if session is not None else {}  # type: typing.Dict

        self._exec = exec if isinstance(exec, list) else [exec]  # type: typing.List[str]

        self._inputs = None

        self._output = None

    def __call__(self, *args, **kwargs) -> typing.Any:
        """
            Execute the function
            @param args: positional arguments
            @param kwargs: keyword arguments
            @return: the result of the execution
        """

        self._output = None
        self._inputs = (args, kwargs)

        if hasattr(self, 'signature'):
            del self.signature

        if self._session.get("lazy_eval", False):
            return self
        else:
            return self.__value__

    @property
    def __value__(self) -> typing.Any:
        if self._output is None:
            logger.info(f"Start\t: {self.signature}")

            args, kwargs = self._inputs

            args, kwargs = self.pre_process(*args, **kwargs)

            self._output = self.post_process(self.execute(*args, **kwargs))

            logger.info(f"End\t: {self.signature}")

        return self._output

    @cached_property
    def signature(self) -> str:

        f_name = self._exec  # self._module_desc.get('name', 'unnamed')+'.'+'.'.join(map(str, self._rel_path))

        if self._package is not None:
            f_name = f"{self._package.tag_str}/{f_name}"

        if self._inputs is None:
            args, kwargs = self._module_desc.get("inputs", ([], {}))
        else:
            args, kwargs = self._inputs

        para_str = ','.join([str(v) for v in args] + [f"{k}={v}" for k, v in kwargs.items()])

        return f"{f_name}({para_str})"

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
        for p_name, p_metadata in self.metadata["in_ports"].items():
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

    def outputs(self):
        if self.outputs is not None:
            return self.outputs
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

        self.outputs = collections.ChainMap(
            outputs, {k: v for k, v in result.items() if k not in self.metadata.out_ports})

        self._inputs = None
        os.chdir(cwd)
        return self.outputs

    def pre_process(self, *args, **kwargs):
        logger.info(f"Pre-process")
        # self._execute_script(self.metadata.prescript)
        return args, kwargs

    def post_process(self, value):
        logger.info(f"Post-process")
        # self._execute_script(self.metadata.postscript)
        return value

    def execute(self, *args, **kwargs) -> typing.Any:

        if not isinstance(self._exec, pathlib.Path):

            if self._package is not None:
                exec_file = self._package.install_dir/self._exec[0]
            else:
                exec_file = self._exec[0]

            exec_file = pathlib.Path(exec_file)

        if not os.access(exec_file, os.X_OK):
            raise RuntimeError(f"File {exec_file} is not executable!")

        exec_cmd = [exec_file.as_posix(), *self._exec[1:]]
        logger.info(f"Execute {' '.join(exec_cmd)}")

        return None
        error_msg = None

        try:
            logger.debug(f"Execute Start: {self.metadata.annotation.label}")
            res = self.execute(*args, **kwargs)
            logger.debug(f"Execute Done : {self.metadata.annotation.label}")
        except Exception as error:
            error_msg = error
            logger.error(f"Execute Error! {error}")
            res = None

        if error_msg is not None:
            raise error_msg

        return res


class FyExecutorDummy(FyExecutor):
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

    def _create_dobject(self, data,  _metadata=None, *args, envs=None, **kwargs):

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
        n_cls = SpObject.schema.get(n_cls, n_cls)

        if not n_cls:
            return data
        if inspect.isclass(n_cls):
            return n_cls(data) if data is not None else None
        elif isinstance(data, DataObject):  # FIXME: !! and data.metadata["$class"] == n_cls:
            return data
        else:
            res = DataObject(collections.ChainMap({"$class": n_cls}, _metadata), *args,  **kwargs)
            if data is not None:
                res.update(data)
            return res


class FyExecutorLocal(FyExecutor):
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
        elif exec_file.suffix in FyExecutorLocal.script_call.keys():
            command = [FyExecutorLocal.script_call[exec_file.suffix], exec_file.as_posix()]
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

        working_dir = os.getcwd()

        execute: pathlib.Path = self._install_dir/self._desc.get("execute")
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


class FyExecutorPy(FyExecutor):
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
