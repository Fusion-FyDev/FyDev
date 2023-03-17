
# For basic module
import os
import subprocess
import signal
from pathlib import Path, PurePath, PurePosixPath
import time
import linecache
import yaml
# For  utils
from spdm.util.logger import logger

from fydev.FyHandler import FyModule

# import module tool  from EasyBuild
from easybuild.tools.filetools import remove_dir
from easybuild.tools.modules import get_software_root_env_var_name, modules_tool, get_software_libdir
from easybuild.tools.options import set_up_configuration
from easybuild.tools.run import run_cmd

#  import easyconfig  from EasyBuild  framework
from easybuild.framework.easyconfig.tools import det_easyconfig_paths, parse_easyconfigs, skip_available

# import robot  from EasyBuild  tools (-Dr)
from easybuild.tools.robot import check_conflicts, dry_run, missing_deps, resolve_dependencies, search_easyconfigs

#  import easyblock  from EasyBuild  framework
from easybuild.framework.easyblock import EasyBlock, get_easyblock_instance

#  import easybuild.main and testng   from EasyBuild  framework

from easybuild.main import build_and_install_software
from easybuild.tools.testing import create_test_report, overall_test_report, regtest, session_state
# for log or error
from easybuild.tools.build_log import EasyBuildError, print_error, print_msg, stop_logging
# for hook
from easybuild.tools.hooks import START, END, load_hooks, run_hook


class ModuleEb(FyModule):
    '''Module wrapper.

    This class represents internally a module. Concrete module system
    implementation should deal only with that.
    the init will provide the name ,version ,toolchain,tag and fullname .
    if the version is null ,I dont know what you want .
    If the toolchain is null ,I can read the default toolchain from configure,yaml \
        which by def load_configure() in class ModuleRepository .
    '''

    def __init__(self, name, version, toolchain, tag="", collection=False, depend_args=[],
                 install_args=[], path=None, repo_name=None, repo_tag=None, *args, **kwargs):

        super().__init__(repo_name=None, repo_tag=None, *args, **kwargs)

        name = name.strip()
        logger.info(f"Now start to init the software {name}.")
        if not name:
            raise ValueError('name cannot be empty,I dont know what you want')
        if not isinstance(name, str):
            raise TypeError('name not a string')

        version = version.strip()

        if not isinstance(version, str):
            raise TypeError('version not a string')
        toolchain = toolchain.strip()
        tag = tag.strip()

        if not isinstance(toolchain, str):
            raise TypeError('toolchain not a string')
        if not isinstance(tag, str):
            raise TypeError('tag not a string')

        # first check the contition ,get the all value
        if not version:
            # for version=NULL , if need to give the error and exit????
            try:
                logger.warning(f"The version is empty. I don't know what you want "
                               f"You can use 'fetch' to check which module is installed")
                self._name = name
                self._version = " "
                self.toolchain = " "
                self._tag = " "
                self._fullname = name
            except:
                raise ValueError(f"The version is empty. I don't know what you want ")

        if not tag:
            try:
                self._name = name
                self._version = version
                self._toolchain = toolchain
                self._modulename = '-'.join((self._name, self._version))
                self._modulefullname = '-'.join((self._name, self._version, self._toolchain))
                self._fullname = '-'.join(('/'.join((self._name, self._version)), self._toolchain))

            except:
                raise ValueError('I cannot get fullname ,I dont know what you want')
        elif not toolchain:
            try:
                """
                default_toolchain = self.load_configure(self),here is the interface with the class ModuleRepository
                which get the default toolchain from the configure file .
                """
                # default_module = self.__init__( name, version,toolchain,tag,collection=False, path=None,repo_name=None, repo_tag=None,*args,**kwargs)
                self.load_configure(path)
                default_toolchain = self._conf.get("default_toolchain")
                logger.debug(f"the default_toolchain name from the default-configure  is '{default_toolchain}'")
                # default_toolchain = 'foss-2020a'
                self._name = name
                self._version = version
                self._toolchain = default_toolchain
                self._modulename = '-'.join((self._name, self._version))
                self._modulefullname = '-'.join((self._name, self._version, self._toolchain))
                self._fullname = '-'.join(('/'.join((self._name, self._version)), self._toolchain))
                # self.eb_options = eb_options

            except:
                raise ValueError('I cannot get fullname ,I dont know what you want')
        else:
            try:
                self._name = name
                self._version = version
                self._toolchain = toolchain
                self._modulename = '-'.join((self._name, self._version))
                self._modulefullname = '-'.join((self._name, self._version, self._toolchain))
                self._fullname = '-'.join(('/'.join((self._name, self._version)), self._toolchain, self._tag))

            except:
                raise ValueError('I cannot get name ,I dont know what you want')
        logger.info(f"The ID for the software is {self._modulefullname}.")
        self._path = path
        self._ebfile_name = '-'.join(self._fullname.split('/'))

        self.install_args = install_args
        self.depend_args = depend_args

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def toolchain(self):
        return self._toolchain

    @property
    def tag(self):
        return self._tag

    @property
    def path(self):
        return self._path

    @property
    def modulename(self):
        return self._modulename

    @property
    def modulefullname(self):
        return self._modulefullname

    @property
    def fullname(self):
        return self._fullname

    @property
    def ebfile_name(self):
        return self._ebfile_name

    def __hash__(self):
        # Here we hash only over the name of the module, because foo/1.2 and
        # simply foo compare equal. In case of hash conflicts (e.g., foo/1.2
        # and foo/1.3), the equality operator will resolve it.
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        if self.path != other.path:
            return False

        if not self.version or not other.version:
            return self.name == other.name
        else:
            return self.name == other.name and self.version == other.version

    def __repr__(self):
        return self.fullname

    def __str__(self):
        return self.fullname

    def search_fymodule(self, *args, **kwargs):
        """Find fymodule in  /gpfs/fuyun/ModuleRepository/name/ .If the file is exsit,the package is exsit';not,you need to install it"""
        path = self.path
        # logger.debug(f'the path dir  is {path}')
        self.load_configure(path)
        software_path = self._conf.get("MoResp_dir")
        flag = 0
        name = self.name
        modulename = self.modulefullname
        # software_path = "/gpfs/fuyun/fy_modules/physics/"
        templefilename = modulename+'.yaml'
        # logger.debug(f'the fy-modulename   is {templefilename}')
        fymodule_path = software_path+'/'+name
        # logger.debug(f'the fymodule_path   is {fymodule_path}')
        if Path(fymodule_path).exists():
            if Path(Path(Path(fymodule_path).joinpath(templefilename))).is_file():
                flag += 1
                return flag, Path(Path(Path(fymodule_path).joinpath(templefilename)))
            else:
                raise FileNotFoundError(f"the {templefilename} file doesn't exist in the directpry {fymodule_path}.")
        else:
            raise FileNotFoundError(f"the {fymodule_path} path doesn't exist.")

    def load_package(self, *args, **kwargs):
        import subprocess
        if (self.check_package(*args, **kwargs)[0] == 1):
            modulename = self.check_package(*args, **kwargs)[1][0]
            mod_tool = modules_tool()
            # 这里只是得到变量名，没有解析变量
            env_var_name = get_software_root_env_var_name(self.name)
            mod_tool.load([modulename])
            # env_libdir = get_software_libdir(self.name)
            print("Current $%s value: %s" % (env_var_name, os.getenv(env_var_name, '(no set)')))
            # print(f"Current {env_var_name} lib: {env_libdir}")
            process = subprocess.Popen(['which', "${env_var_name}"], stdout=subprocess.PIPE)
            for line in process.stdout:
                print(line.decode())
            # result = subprocess.run(['which', env_var_name], capture_output=True)
            # print(result.stdout.decode())
            # print("Current $%s value: %s" % (env_var_name, os.getenv(printenv, '(no set)')))

    def list_avail_package(self, *args, **kwargs):
        fullname = self.fullname
        logger.debug(f'the fy-fullname   is {fullname}')
        if not isinstance(fullname, str):
            raise TypeError('module name not a string')
        opts, cfg_settings = set_up_configuration(args=[], silent=True)
        mod_tool = modules_tool()
        # fullname = "genray"
        list_avail_modules = mod_tool.available(fullname)
        logger.debug(f'the fy-list_avail_modules   is {list_avail_modules}')
        if len(list_avail_modules):
            return list_avail_modules
        else:
            other_avail_modules = mod_tool.available(self.name)
            logger.debug(f'The Other available packages have {other_avail_modules}')
            raise KeyError(f"the {fullname} is not installed,you can choose the other package ! .")

    def check_package(self, *args, **kwargs):
        # to check the modulename which will be install is installed or not
        logger.info(f'Use the ID {self._modulefullname} to check if the package is accessible.')
        fullname = self.fullname
        # check if fullname is a string
        if not isinstance(fullname, str):
            raise TypeError('module name not a string')
        opts, cfg_settings = set_up_configuration(args=[], silent=True)
        mod_tool = modules_tool()
        flag = 0
        # check if fullname contains "/"
        if "/" in fullname:
            avail_eb_modules = mod_tool.available(fullname)

            if len(avail_eb_modules):
                flag += 1
                logger.info(f"Accessible package is: {avail_eb_modules}")
                return flag, avail_eb_modules
            else:
                other_avail_modules = mod_tool.available(self.name)
                logger.info(f'the {fullname} is not installed.')
                logger.info(f'The Other available packages have {other_avail_modules}')
                logger.info(f'The system can try to install {self.fullname}')
                try:
                    # find discription file
                    fymodule = self.search_fymodule()
                    logger.info(f'The discription file is {fymodule}')
                    # fetcch sources
                    logger.info(f'Now Fetch sources ')
                    sourcedir = self.fetch_sources()
                    logger.info(f'The sources location  is {sourcedir}')
                    # parase the discription file to get configure file for EasyBuild
                    logger.info(f'Parase discription file ')
                    ebfile = self.search_ebfiles()
                    logger.info(f'Config file is {ebfile}')
                    # Install the package now!
                    logger.info(f'Install it now ')
                    installresult = self.install_package()
                    logger.info(f'Install is sucesful ,the install cmd is {installresult}  ')
                    avail_eb_modules = mod_tool.available(fullname)
                    if len(avail_eb_modules):
                        logger.info(f'the install is sucessful,please use it.')
                        return flag, avail_eb_modules
                    else:
                        raise RuntimeError('the install failed')
                except (KeyError, RuntimeError) as e:
                    logger.debug(e)
        else:
            # use try-except to catch KeyError
            try:
                raise KeyError(f"the {fullname} is incomplete.")
            except KeyError as e:
                logger.debug(e)

    def search_ebfiles(self, *args, **kwargs):
        """Find ebfiles in  /gpfs/fuyun/EbfilesRespository/name/ .If the file is exsit,you can use it ';not,you need to try-toolchain to use  it"""
        flag = 0
        name = self.name
        modulename = self.modulefullname
        opts, cfg_settings = set_up_configuration(args=[], silent=True)
        mod_tool = modules_tool()
        # software_path = "/gpfs/fuyun/fy_modules/physics/"
        ebfilename = modulename+'.eb'
        # logger.debug(f'the fy-ebfilename   is {ebfilename}')
        ebfile_path = det_easyconfig_paths([ebfilename])[0]
        if len(ebfile_path):
            flag += 1
            # logger.log(f"the output of installed module is {avail_eb_modules}")
            return ebfile_path
        else:
            logger.log(f"the output of installed module is null")
            return " "
            # delete at 2021-10-07
        #    ## add the try-funtction to yeild ebfiles .
        #     raise KeyError(f"the {ebfile_path} is not not exsit .")
        #     # self.listpa(fullname,max_list = True)

    def list_dependence(self, *args, **kwargs):
        """ TO check the ebfile is ok or not "-Dr" """
        args_list = []
        extend_args = self.depend_args
        if len(extend_args):
            for i in range(0, len(extend_args)):
                args_list.append(extend_args[i])
        modulename = self.modulefullname
        ebfilename = modulename+'.eb'
        opts, cfg_settings = set_up_configuration(args=args_list, silent=True)
        logger.debug(f'the cfg_settings  is {cfg_settings}')
        (build_specs, _log, logfile, robot_path, search_query, eb_tmpdir,
         try_to_generate, tweaked_ecs_paths, *other) = cfg_settings
        mod_tool = modules_tool()
        ebfile_path = det_easyconfig_paths([ebfilename])[0]
        ec_dicts, _ = parse_easyconfigs([(ebfile_path, False)])
        txt = dry_run(ec_dicts, mod_tool, short=False)
        deplist = txt.split('\n')
        if len(deplist) < 2:
            raise KeyError(f"the {ebfile_path} is unavailable .")

        dependcommand = ['eb -Dr']
        dependcommand.extend(args_list)
        dependcommand.extend(robot_path)
        dependcommandline = ' '.join(dependcommand)

        return dependcommandline, deplist
        remove_dir(opts.tmpdir)

    def fetch_sources(self, dry_run=False, *args, **kwargs):
        """ To get the sources ;if dry_run = False ,just get the easycofig itself ;if dry_run=Ture,get all sources in dependence"""
        eb_sources = []
        modulename = self.modulefullname
        ebfilename = modulename+'.eb'
        opts, cfg_settings = set_up_configuration(args=[], silent=True)
        mod_tool = modules_tool()
        # logger.debug(f'the cfg_settings  is {cfg_settings}')
        (build_specs, _log, logfile, robot_path, search_query, eb_tmpdir,
         try_to_generate, tweaked_ecs_paths, *other) = cfg_settings
        ebfile_path = det_easyconfig_paths([ebfilename])[0]
        ec_dicts, _ = parse_easyconfigs([(ebfile_path, False)])
        print(ec_dicts)
        if (dry_run == False):
            eb = get_easyblock_instance(ec_dicts[0])
            eb.fetch_sources()
            eb_sources = eb.src
        else:
            ordered_ecs = resolve_dependencies(ec_dicts, mod_tool, retain_all_deps=True)

            print(type(ordered_ecs))
            print(len(ordered_ecs))
            for ec in ordered_ecs:
                print(ec)
                eb = get_easyblock_instance(ec)
                print(dir(eb))
                eb.fetch_sources()
                eb_sources.append(eb.src[0])
        return eb_sources
        remove_dir(opts.tmpdir)

    def install_package(self, *args, **kwargs):
        args_list = []
        extend_args = self.install_args
        if len(extend_args):
            for i in range(0, len(extend_args)):
                args_list.append(extend_args[i])
        opts, cfg_settings = set_up_configuration(args=args_list, silent=True)

        mod_tool = modules_tool()
        logger.debug(f'the cfg_settings  is {cfg_settings}')
        # if len(cfg_settings)>8:
        #     (build_specs, _log, logfile, robot_path, search_query, eb_tmpdir, try_to_generate, tweaked_ecs_paths,other) = cfg_settings
        # else:
        #     (build_specs, _log, logfile, robot_path, search_query, eb_tmpdir, try_to_generate, tweaked_ecs_paths) = cfg_settings
        (build_specs, _log, logfile, robot_path, search_query, eb_tmpdir,
         try_to_generate, tweaked_ecs_paths, *other) = cfg_settings
        modulename = self.modulefullname
        ebfilename = modulename+'.eb'

        hooks = load_hooks(opts.options.hooks)
        run_hook(START, hooks)
        ebfile_path = det_easyconfig_paths([ebfilename])[0]
        easyconfigs, _ = parse_easyconfigs([(ebfile_path, False)])
        init_session_state = session_state()
        # update session state
        eb_config = opts.generate_cmd_line(add_default=True)
        modlist = mod_tool.list()  # build options must be initialized first before 'module list' works
        init_session_state.update({'easybuild_configuration': eb_config})
        init_session_state.update({'module_list': modlist})
        forced = opts.options.force or opts.options.rebuild
        # opts.options.dry_run = True
        dry_run_mode = opts.options.dry_run or opts.options.dry_run_short or opts.options.missing_modules
        logger.debug(f'the dry_run_mode  is {dry_run_mode} and {opts.options.robot}')
        # skip modules that are already installed unless forced, or unless an option is used that warrants not skipping
        if not (forced or dry_run_mode or opts.options.extended_dry_run or opts.options.inject_checksums):
            retained_ecs = skip_available(easyconfigs, mod_tool)
            for skipped_ec in [ec for ec in easyconfigs if ec not in retained_ecs]:
                print_msg("%s is already installed (module found), skipping" % skipped_ec['full_mod_name'])
            easyconfigs = retained_ecs

        if len(easyconfigs) > 0:
            # resolve dependencies if robot is enabled, except in dry run mode
            # one exception: deps *are* resolved with --new-pr or --update-pr when dry run mode is enabled
            opts.options.robot = 1
            if opts.options.robot and (not dry_run_mode):
                print_msg("resolving dependencies ...", log=_log)
                logger.debug(f'the dry_run_mode and opts.options.robot  is {dry_run_mode} and {opts.options.robot}')
                ordered_ecs = resolve_dependencies(easyconfigs, mod_tool)
                logger.debug(f'the ordered_ecs  is {len(ordered_ecs)}')
            else:
                logger.debug(f'the dry_run_mode and opts.options.robot  is {dry_run_mode} and {opts.options.robot}')
                ordered_ecs = easyconfigs
        # elif opts.options.pr_options:
        #     ordered_ecs = None
        else:
            print_msg("No easyconfigs left to be built.", log=_log)
            ordered_ecs = []
        if len(ordered_ecs) > 0:
            logger.debug(f'the ordered_ecs  is {len(ordered_ecs)}')
            ecs_with_res = build_and_install_software(ordered_ecs, init_session_state, exit_on_failure=True)
            logger.debug(f'the ecs_with_res  is {ecs_with_res}')

            modulename = mod_tool.available(self.fullname)
        if modulename:

            # 这里只是得到变量名，没有解析变量
            env_var_name = get_software_root_env_var_name(self.name)
            mod_tool.load(modulename)
            logger.debug("Current $%s value: %s" % (env_var_name, os.getenv(env_var_name, '(no set)')))
            ebfilepath = os.getenv(env_var_name, '(no set)')+'/easybuild/'+ebfilename
            moduleinstalldir = os.getenv(env_var_name, '(no set)')+'/easybuild/'
            eb_command = []
            str = "test_report.md"
            for filepath in os.listdir(moduleinstalldir):
                if str in filepath:
                    mdfile = moduleinstalldir+filepath
            with open(mdfile) as f:
                key = "* command line:"
                i = 0
                for line in f.readlines()[:100]:
                    i += 1
                    if key in line:
                        break
            with open(mdfile) as f:
                key2 = "* full configuration (includes defaults):"
                j = i
                for line in f.readlines()[i:100]:
                    j += 1
                    if key2 in line:
                        break
            for k in range(i+1, j):
                the_line = linecache.getline(mdfile, k)
                eb_command.append(the_line)
            print("the eb_command is: ", eb_command)
            eb_commandline = eb_command[1].strip()
            if len(eb_commandline) > 0:
                command = []
                command.extend([eb_commandline])
                command.extend(args_list)
                command.extend(robot_path)
                command.extend([ebfile_path])
                eb_commandline = ' '.join(command)
                # eb_commandline = command
        else:
            # add the try-funtction to yeild ebfiles .
            raise KeyError(f"the package {modulename} is not installed .")
        #  eb-command的解析有问题,因为，非命令行安装，没有解析到conmand-line，我需要自己生成command-line

            # 这是安装包的根目录，然后参考之前的deploy脚本，给出新的脚本。
            # mod_tool.load(modulename)
        # 然后判断，包是否存在，然后反馈eb文件位置和cmd命令:eb ebfilename
        #
        # return ordered_ecs
        return ebfilepath, eb_commandline
        remove_dir(opts.tmpdir)
        run_hook(END, hooks)

    def search_template_file(self, MoResp_dir=None, *args, **kwargs):
        """Find templefile match  packages  name (in /gpfs/fuyun/fy_modules and other  /gpfs/fuyun/fy_modules/gemray)."""
        path = self.path
        logger.debug(f'the path dir  is {path}')
        self.load_configure(path)
        if MoResp_dir == None:
            software_path = self._conf.get("MoResp_dir")
        else:
            software_path = MoResp_dir
        templepath = None
        flag = 0
        name = self.name
        # software_path = "/gpfs/fuyun/fy_modules/physics/"
        templefilename = "temple.yaml"
        # templefilename =
        logger.debug(f'the MoResp_dir dir  is {software_path}')

        if Path(software_path).exists():
            # templepath = Path(tmplefile).parent
            if Path(Path(Path(software_path).joinpath(templefilename))).is_file():
                flag += 1
                # search = Path(Path(Path(software_path).joinpath(name,templefilename)))
                # print(search)
                return flag, Path(Path(Path(software_path).joinpath(templefilename)))
            elif Path(Path(Path(software_path).joinpath(name, templefilename))).is_file():
                # search = Path(Path(Path(software_path).joinpath(name,templefilename)))

                # print(search)
                flag += 1
                return flag, Path(Path(Path(software_path).joinpath(name, templefilename)))
            else:
                return flag, Path(software_path)
        else:
            return flag, None
        #     raise  RuntimeError('could fount the templefile ,please gime me it  ')

    def generate_yaml_doc_ruamel(self, yaml_file):
        NAME = self.name
        VERSION = self.version
        toolchain = self.toolchain
        ID = NAME+'/'+VERSION+'-'+toolchain
        DATA = time.ctime()
        ebfile, build_cmd = self.install_package()
        BUILD_CMD = build_cmd
        eb_sources = self.fetch_sources()
        SOURCES = eb_sources
        EBFILE = ebfile
        depend_cmd, denpendlist = self.list_dependence()
        DEPEND_CMD = depend_cmd
        PACKLIST = denpendlist
        # PRESCRIPT = ["home_dir"+"/modules/all","module purge","module load"+" "+self.fullname]
        PRESCRIPT = [str(self._conf.get("home_dir"))+"/modules/all", "module purge", "module load"+" "+self.fullname]
        py_object = {'$id': ID,
                     '$schema':  'SpModule#SpModuleLocal',
                     'annotation': {'contributors': 'liuxj', 'date': DATA, 'email': 'lxj@ipp.ac.cn'},
                     'description': 'this is a template file. you can refer this template file to produce your own fy_module file of different packages.  If you have any question ,please connet to liuxj(lxj@ipp.ac.cn)',
                     'homepage': 'http://funyun.com/demo.html',
                     'information': {
                         'name': NAME,
                         'version': VERSION

                     },
                     'install': {
                         '$class': 'EasyBuild',
                         'process': {
                             'fetch': {
                                 'sources': SOURCES
                             },
                             'build': {
                                 'build_cmd': BUILD_CMD,
                                 'ebfile': EBFILE}
                         },
                         'depend': {
                             'depend_cmd': DEPEND_CMD,
                             'packageslist': PACKLIST},
                         'toolchain': {
                             'toolchain': toolchain},
                     },
                     'license': 'GPL',
                     'postscript': 'module purge',
                     'prescript': PRESCRIPT,
                     }
        with open(yaml_file, 'w', encoding='utf-8') as file:
            yaml.dump(py_object, file, Dumper=yaml.RoundTripDumper)
            file.close()
        # file = open(yaml_file, 'w', encoding='utf-8')
        # # yaml=YAML(typ='unsafe', pure=True)
        # yaml.dump(py_object, file, Dumper=yaml.RoundTripDumper)
        # file.close()

    def deploy(self, MoResp_dir=None, **kwargs):
        path = self.path
        self.load_configure(path)
        if MoResp_dir == None:
            MoResp_dir = self._conf.get("MoResp_dir")
        flag, templefile = self.search_template_file(MoResp_dir)
        logger.debug(f'the flag and the path  value  is {flag} and {templefile}')
        if flag == 1:
            with open(templefile) as f:
                doc = yaml.load(f, Loader=yaml.FullLoader)
                doc['annotation']['date'] = time.ctime()
                doc['information']['name'] = self.name
                doc['information']['version'] = self.version
                doc['install'][1]['process']['toolchain']['tag'] = self.toolchain
                depend_cmd, denpendlist = self.list_dependence()
                doc['install'][1]['process']['depend']['depend_cmd'] = depend_cmd
                doc['install'][1]['process']['depend']['packageslist'] = denpendlist
                eb_sources = self.fetch_sources()
                doc['install'][1]['process']['fetch']['sources'] = eb_sources
                ebfile, build_cmd = self.install_package()
                doc['install'][1]['process']['build']['budild_cmd'] = build_cmd
                doc['install'][1]['process']['build']['ebfile'] = ebfile
                doc['license'] = "GPL"
                prescript = [self._conf.get("home_dir")+"/modules/all", "module purge", "module load"+" "+self.fullname]
                doc['prescript'] = prescript
            with open(templefile, 'w') as f:
                # yaml=YAML(typ='unsafe', pure=True)
                yaml.dump(doc, f, Dumper=yaml.RoundTripDumper)
            desfile = templefile
        else:
            yaml_path = MoResp_dir + "/"+self.name
            if Path(yaml_path).exists() == False:
                Path(yaml_path).mkdir()
            yaml_name = self.modulefullname+".yaml"
            temple_path = os.path.join(yaml_path, yaml_name)
            logger.debug(f'temple-yaml_path and the taml_name is {temple_path} and {yaml_name}')
            self.generate_yaml_doc_ruamel(temple_path)
            desfile = temple_path
        return desfile

    def run_command(self, cmd, check=False, timeout=None, shell=False, log=True):
        logger.info(f"Execute Shell command {cmd}")
        # @ref: https://stackoverflow.com/questions/21953835/run-subprocess-and-print-output-to-logging
        # if isinstance(cmd, str) and not shell:
        #     cmd = shlex.split(cmd)
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                encoding="utf-8"
            )
            proc_stdout, proc_stderr = process.communicate(timeout=None)
            # for line in proc_stdout :  # b'\n'-separated lines
            #     logger.info(line)
            logger.info(f"Execute the proc_stdout is {proc_stdout}")
            logger.info(f"Execute the proc_stderr is {proc_stderr}")
        except subprocess.TimeoutExpired as e:
            os.killpg(process.pid, signal.SIGKILL)
            raise RuntimeError(e.cmd,
                               process.stdout.read(),
                               process.stderr.read(), timeout) from None
            # process_output, _ = command_line_process.communicate()
        completed = subprocess.CompletedProcess(cmd,
                                                returncode=process.returncode,
                                                stdout=proc_stdout,
                                                stderr=proc_stderr)
        if check and process.returncode != 0:
            raise process.subprocessCalledProcessError(completed.args,
                                                       completed.stdout, completed.stderr,
                                                       completed.returncode)
        return completed

    def run(self, modulename):
        logger.info(f"Now start to module load {modulename} and run it,")
        fymodule = self.search_fymodule()
        self.load_configure(fymodule[1])
        workdir = self._conf.get('workdir')
        cmdexe = self._conf.get("run")["exec"]
        exec_cmd = f"cd {workdir};{cmdexe}"
        logger.info(f'the cmd  is {exec_cmd}')
        mod_tool = modules_tool()
        mod_tool.load(modulename)
        logger.info(f"The all load module is{mod_tool.list()}")
        result = self.run_command(exec_cmd)
        return result
