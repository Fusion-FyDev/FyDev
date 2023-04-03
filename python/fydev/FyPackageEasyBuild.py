from easybuild.tools.testing import (create_test_report,
                                     overall_test_report, regtest,
                                     session_state)
from easybuild.tools.run import run_cmd
from easybuild.tools.robot import (check_conflicts, dry_run, missing_deps,
                                   resolve_dependencies,
                                   search_easyconfigs)
from easybuild.tools.options import set_up_configuration
from easybuild.tools.modules import (get_software_libdir,
                                     get_software_root_env_var_name,
                                     modules_tool)
from easybuild.tools.hooks import END, START, load_hooks, run_hook
from easybuild.tools.filetools import remove_dir
from easybuild.tools.build_log import (EasyBuildError, print_error,
                                       print_msg, stop_logging)
from easybuild.main import build_and_install_software
from easybuild.framework.easyconfig.tools import (det_easyconfig_paths,
                                                  parse_easyconfigs,
                                                  skip_available)
from easybuild.framework.easyblock import EasyBlock, get_easyblock_instance
import collections.abc
import os
import pathlib
import shutil
import subprocess
import sys

from spdm.util.logger import logger

from .FyCommon import FY_ROOT
from .FyPackage import FyPackage
from .FyPackageModule import FyPackageModule

EBROOT = os.environ.get("EBROOTEASYBUILD", None)

sys.path.append(os.path.join(EBROOT, "lib", "python3.8", "site-packages"))


@FyPackage.register("easybuild")
class FyPackageEasyBuild(FyPackageModule):
    """
    A class to handle EasyBuild module files.
    module load EasyBuild
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._opts, self._cfg_settings = set_up_configuration(
            ['--installpath', FY_ROOT],
            logfile="~/fydev/easybuild.log",
            silent=True)

    def install(self, *args, **kwargs) -> None:
        """
        Install the package using EasyBuild.
        """

        install_conf = self._desc.get("install", None)

        if isinstance(install_conf, str):
            ebfile_path = install_conf
        elif isinstance(install_conf, collections.abc.Mapping):
            ebfile_path = install_conf.get("ebfile_path", None)
        else:
            ebfile_path = None

        if ebfile_path is None:
            mod_url = self._desc.get("$url", None)

            if mod_url is not None:
                if mod_url.startswith("file://"):
                    mod_url = mod_url[7:]

                ebfile_path = pathlib.Path(mod_url).with_suffix(".eb")

                if not ebfile_path.exists():
                    ebfile_path = None
                else:
                    ebfile_path = ebfile_path.resolve().expanduser().as_posix()
            else:
                ebfile_path = det_easyconfig_paths([self.ebfilename])[0]

        logger.info(f"Installing package {self.id} using EasyBuild [{ebfile_path}].")

        self._ebfile_path = ebfile_path

        self.deploy()

        easyconfigs, _ = parse_easyconfigs([(ebfile_path, False)])

        init_session_state = session_state()

        # update session state
        eb_config = self._opts.generate_cmd_line(add_default=True)

        mod_tool = modules_tool()

        modlist = mod_tool.list()  # build options must be initialized first before 'module list' works

        init_session_state.update({'easybuild_configuration': eb_config})

        init_session_state.update({'module_list': modlist})

        easyconfigs = resolve_dependencies(easyconfigs, mod_tool)

        # skip modules that are already installed
        easyconfigs = skip_available(easyconfigs, mod_tool)

        if len(easyconfigs) == 0:
            logger.warning(f"Package {self.id} not installed")
            return

        try:
            build_and_install_software(easyconfigs, init_session_state, exit_on_failure=True)
        except EasyBuildError as err:
            logger.error(err)
            # return
            # raise err

        self.install_description()

        logger.info(f"Package {self.id} installed")

        return

    def install_description(self) -> None:
        """
        Install the package description file.
        """
        ebfile_name = f"{self.id}.eb"

        shutil.copy(self._ebfile_path, self.install_dir/ebfile_name)

        self._desc.setdefault("install", ebfile_name)

        super().install_description()
