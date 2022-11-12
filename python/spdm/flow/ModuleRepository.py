# from FyDev.python.tests.test_basic import module
import collections
import os
import pathlib
import shlex
import subprocess
import signal
import traceback
import uuid
import re
from ..util import io
from ..util.dict_util import deep_merge_dict, format_string_recursive
from ..util.Factory import Factory
from ..util.LazyProxy import LazyProxy
from ..util.logger import logger
from ..util.RefResolver import RefResolver
from ..util.sp_export import sp_find_module
from ..util.urilib import urisplit
from .SpModule import SpModule
import pprint


class ModuleRepository:
    def __init__(self, *args, repo_name=None, repo_tag=None,  envs=None, module_file_suffix=None, **kwargs):
        self._resolver = None
        self._factory = None
        self._repo_name = repo_name or __package__.split('.')[0]
        self._repo_tag = repo_tag or self._repo_name[:2]
        self._module_file_suffix = module_file_suffix or f"/{self._repo_tag.lower()}_module.yaml"
        self._envs = envs or {}

        logger.debug(f"Open module repository '{self._repo_name} ({self._repo_tag})'")
    def load_configure(self, path, **kwargs):
       

        return self.configure(io.read(path))
    def save_configure(self, path):
        io.write(path, self._envs)

    def configure(self, conf=None, enable_sys_confile=True, **kwargs):

        conf_file_list = []

        if isinstance(conf, (str, pathlib.PosixPath)):
            conf_file_list = [conf]
            conf = None
        elif isinstance(conf, collections.abc.Sequence):
            conf_file_list = conf
            conf = None

        if enable_sys_confile:
            conf_file_list.extend(
                [
                    *os.environ.get(f"{self._repo_name.upper()}_CONFIGURE_PATH", "").split(';'),
                    *os.environ.get(f"{self._repo_tag.upper()}_CONFIGURE_PATH", "").split(';'),
                    # f"pkgdata://{self._repo_name}/configure.yaml"
                ])

        extra_conf = {}
        for conf_file in conf_file_list:
            if isinstance(conf_file, str):
                conf_file = pathlib.Path(conf_file)
            d = io.read(conf_file)
            format_string_recursive(d, {"CURRENT_CONFIGURE_FILE_DIR": conf_file.parent})
            deep_merge_dict(extra_conf, d)
        # extra_conf = io.read(conf_file_list)

        # TODO:  list in dict should be appended not overwrote .
        f_conf = collections.ChainMap(kwargs, conf or {}, extra_conf)

        self._factory = Factory(**collections.ChainMap(
            f_conf.get("factory", {}),
            {
                "alias": [["https://fusionyun.org/", "SpModule:///*#{fragment}"]],
                "module_prefix": f"{__package__}"
            }),
            resolver=RefResolver(**f_conf.get("resolver", {})))

        self._home_dir = f_conf.get("home_dir", None) or \
            os.environ.get(f"{self._repo_tag.upper()}_HOME_DIR", None)

        if self._home_dir is not None:
            self._home_dir = pathlib.Path(self._home_dir)
        else:
            self._home_dir = pathlib.Path.home()/f".{self._repo_name.lower()}"

        self._modules_dir = self._home_dir / \
            f_conf.get(f"{self._repo_tag.upper()}_MODULES_DIR", "modules")

        self._env_modules_dir = self._home_dir / \
            f_conf.get(f"{self._repo_tag.upper()}_ENV_MODULEFILES_DIR", "env_modulefiles")

        self._software_dir = self._home_dir / \
            f_conf.get(f"{self._repo_tag.upper()}_SOFTWARE_DIR", "software")

        self._sources_dir = self._home_dir / \
            f_conf.get(f"{self._repo_tag.upper()}_SOURCES_DIR", "source")

        self._build_dir = self._home_dir / \
            f_conf.get(f"{self._repo_tag.upper()}_BUILD_DIR", "build")

        self.resolver.alias.append(
            self.resolver.normalize_uri("/modules/*"),
            self._modules_dir.as_posix()+f"/*{self._module_file_suffix}")

        self._conf = f_conf
        self.factory.insert_handler("SpModule", SpModule)

    @property
    def entry(self):
        return LazyProxy(self, [], handler=lambda c, o, p: o.new_class_by_path(p))

    @property
    def resolver(self):
        return self._factory.resolver

    @property
    def factory(self):
        return self._factory

    def resolve_metadata(self, metadata, *args, expand_template=True, envs=None, version=None, tag=None, ** kwargs):
        """
           Format of searching path
                <desc>/<version>-<tag>
                file link:
                    <repo_path>/physics/genray/10.8.1   -> <repo_path>/physics/genray/10.8.1-foss-2019
                    <repo_path>/physics/genray/10.8     -> <repo_path>/physics/genray/10.8.1-foss-2019
                    <repo_path>/physics/genray/10       -> <repo_path>/physics/genray/10.8.1-foss-2019
                    <repo_path>/physics/genray/default  -> <repo_path>/physics/genray/10.8.1-foss-2019

           Example:
                    <repo_path>/physics/genray/10.8-foss-2019
                    <repo_path>/physics/genray/10.8
                    <repo_path>/physics/genray/default
                    <repo_path>/physics/genray/
        """
        version = version or 'default'
        tag = tag or ''
        if isinstance(metadata, str):
            n_metadata = self.resolver.fetch(f"{metadata}/{version}{tag}", envs)
            if not n_metadata:
                n_metadata = self.resolver.fetch(f"{metadata}/default", envs)
                if isinstance(n_metadata, (collections.abc.Mapping, collections.abc.Sequence)):
                    format_string_recursive(n_metadata, {"version": version, "tag": tag})

        else:
            n_metadata = self.resolver.fetch(metadata, envs)

        if not n_metadata:
            raise LookupError(f"Can not find module {metadata}!")

        if isinstance(n_metadata, (collections.abc.Mapping, collections.abc.Sequence)) and expand_template:

            modulefile_path = pathlib.Path(n_metadata.get("$source_file", ""))

            doc_vars = {k: v for k, v in n_metadata.items() if k.startswith('$') and isinstance(v, str)}

            envs = collections.ChainMap(
                {
                    "version": version,
                    "tag": tag,
                    "module_path": self.resolver.remove_prefix(n_metadata.get("$id", "")),
                    f"{self._repo_tag.upper()}_MODULEFILE_DIR": modulefile_path.parent,
                    f"{self._repo_tag.upper()}_MODULEFILE_PATH": modulefile_path
                },
                doc_vars,
                envs or {},
                kwargs,
                self._envs)

            format_string_recursive(n_metadata, envs)

        n_metadata[f"{self._repo_tag.upper()}_MODULEFILE_DIR"] = modulefile_path.parent
        n_metadata[f"{self._repo_tag.upper()}_MODULEFILE_PATH"] = modulefile_path
        return n_metadata

    def new_class_by_path(self, path):
        if isinstance(path, str):
            res = self.new_class(path)
        elif isinstance(path, list) and isinstance(path[-1], collections.Mapping):
            res = self.new_class('/'.join(path[:-1]), **path[-1])
        elif isinstance(path, list) and not isinstance(path[-1], collections.Mapping):
            res = self.new_class('/'.join(path))
        else:
            raise TypeError(type(path))
        return res

    def new_class(self, metadata, *args, **kwargs):
        n_cls = self._factory.create(self.resolve_metadata(metadata, *args, **kwargs))

        if n_cls is None:
            raise ValueError(f"Can not make module {metadata}!")

        return n_cls

    def glob(self, prefix=None):
        return self.resolver.glob(prefix or "/modules/")

    def install_spec(self, spec, no_build=False, force=False, **kwargs):
        ver = spec.get("version", "0.0.0")

        mid = spec.get("$id", None) or kwargs.get("id", None) or f"unkown/unamed_{uuid.uuid1().hex()}"

        spec["$id"] = mid

        spec_path = self._modules_dir/mid.replace('.', '/')/(ver+self._suffix)

        if not force and spec_path.exists():
            raise FileExistsError(f"'{spec_path}' exists!")

        spec_path.parent.mkdir(parents=True, exist_ok=force)

        write(spec_path, spec)

        if not no_build:
            self.build(spec_path, force=force)

    def install_from_repository(self, repo, *args, **kwargs):
        # TODO: clone repo to source_dir, find fy_module.yaml
        raise NotImplementedError()

       
    def install(self, spec, *args,   **kwargs):
        """ install specification
        """

        if isinstance(spec, (str, pathlib.Path, URISplitResult, collections.abc.Sequence)):
            spec = io.read(spec)

        if isinstance(spec, collections.abc.Mapping):
            return self.install_spec(spec, *args, **kwargs)
        else:
            raise TypeError(
                f"Need string or list of string or pathlib.Path. {type(spec)}")

    def build_repo(self, path, *args, **kwargs):
        raise NotImplementedError()

    def build(self, path,  *args, **kwargs):

        if isinstance(path, pathlib.Path) and path.is_dir():
            return self.build_repo(path, *args, **kwargs)

        spec = self.resolver.fetch(path)

        annotation = spec.get("annotation", {})

        eb_file = spec.get("build", {})

        eb_file["name"] = annotation.get("name", "unamed")
        eb_file["version"] = annotation.get("version", "0.0.0")
        eb_file["homepage"] = annotation.get("homepage", "")
        eb_file["description"] = annotation.get("description", "")

        eb_file["toolchain"]["version"] = eb_file["toolchain"]["version"].fomat(
            FY_TOOLCHAIN_VERSION=os.environ.get("FY_TOOLCHAIN_VERSION"))

        from env_modules_python import module

        module("load", build_cfg.get("eb_module", "EasyBuild"))

        # spec = DataEntry(self._get_module_spec_file(name)).read()

        # build_spec = spec.get("build", {})

        # build_ebfile = self._dirs["TEMP_DIR"]/f"{name.replace('.', '_')}.eb"

        # DataEntry(build_ebfile, format="yaml").write(build_spec)

        cmd = shlex.split(build_cfg.get("build_cmd", "eb"))

        try:
            logger.debug(f"Command:[ {' '.join(cmd)} ]")
            exit_status = subprocess.run(
                cmd, env=envs,
                capture_output=True,
                check=True,
                shell=False,
                text=True
            )
        except subprocess.CalledProcessError as error:
            logger.error(
                f"""Command failed! [{cmd}]
                   STDOUT:[{error.stdout}]
                   STDERR:[{error.stderr}]""")
            raise error

    def remove(self, name):
        raise NotImplementedError()
