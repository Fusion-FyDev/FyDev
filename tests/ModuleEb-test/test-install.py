#!/usr/bin/env python3
import sys
sys.path.append("/gpfs/fuyun/software/EasyBuild/4.3.2/lib/python3.6/site-packages")
import  easybuild.framework.easyconfig.tools
from easybuild.framework.easyconfig.tools import det_easyconfig_paths, parse_easyconfigs,skip_available
from easybuild.tools.options import set_up_configuration
from easybuild.tools.robot import check_conflicts, dry_run, missing_deps, resolve_dependencies, search_easyconfigs
from easybuild.tools.modules import get_software_root_env_var_name, modules_tool
from easybuild.framework.easyblock import EasyBlock, get_easyblock_instance

from easybuild.main import build_and_install_software
from easybuild.tools.testing import create_test_report, overall_test_report, regtest, session_state
# for log or error
from easybuild.tools.build_log import EasyBuildError, print_error, print_msg, stop_logging
# /gpfs/fuyun/software/EasyBuild/4.3.2/lib/python3.6/site-packages/easybuild/main.py
extend_args=['--module-only', '--rebuild']
args_list=[]
if len(extend_args):
    for i in range(0,len(extend_args)):
        args_list.append(extend_args[i])
opts,cfg_settings =set_up_configuration(args=args_list, silent=True)
# opts,cfg_settings =set_up_configuration(args=[], silent=True)
# opts,cfg_settings =set_up_configuration(args=['--rebuild', '--minimal-toolchains'], silent=True)
print(dir(opts))
print(opts.args)
mod_tool = modules_tool()
print(mod_tool)
print(mod_tool.NAME)
(build_specs, _log, logfile, robot_path, search_query, eb_tmpdir, try_to_generate, tweaked_ecs_paths) = cfg_settings
# def build_and_install_software(ecs, init_session_state, exit_on_failure=True):
print(robot_path)
# easyconfigs, generated_ecs = parse_easyconfigs(paths, validate=not options.inject_checksums)
# easyconfigs=["Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2.eb"]
ebfilename="CMake-3.16.5-GCCcore-9.3.0.eb"

ebfile_path = det_easyconfig_paths([ebfilename])[0]


easyconfigs, _ = parse_easyconfigs([(ebfile_path, False)])
init_session_state = session_state()
 # update session state
eb_config = opts.generate_cmd_line(add_default=True)
modlist = mod_tool.list()  # build options must be initialized first before 'module list' works
init_session_state.update({'easybuild_configuration': eb_config})
init_session_state.update({'module_list': modlist})
forced = opts.options.force or opts.options.rebuild
dry_run_mode = opts.options.dry_run or opts.options.dry_run_short or opts.options.missing_modules

# skip modules that are already installed unless forced, or unless an option is used that warrants not skipping
if not (forced or dry_run_mode or opts.options.extended_dry_run or opts.options.inject_checksums):
    retained_ecs = skip_available(easyconfigs, mod_tool)
    for skipped_ec in [ec for ec in easyconfigs if ec not in retained_ecs]:
        print_msg("%s is already installed (module found), skipping" % skipped_ec['full_mod_name'])
    easyconfigs = retained_ecs

if len(easyconfigs) > 0:
    # resolve dependencies if robot is enabled, except in dry run mode
    # one exception: deps *are* resolved with --new-pr or --update-pr when dry run mode is enabled
    if opts.options.robot and (not dry_run_mode):
        print_msg("resolving dependencies ...", log=_log)
        ordered_ecs = resolve_dependencies(easyconfigs, mod_tool)
    else:
        ordered_ecs = easyconfigs
# elif opts.options.pr_options:
#     ordered_ecs = None
else:
    print_msg("No easyconfigs left to be built.", log=_log)
    ordered_ecs = []

ecs_with_res=build_and_install_software(ordered_ecs, init_session_state, exit_on_failure=True)
print(dir(ecs_with_res))
print(ecs_with_res)
print(type(ecs_with_res))