# -*- coding: utf-8 -*-
import collections
import os
import pathlib
import shlex
import subprocess
import traceback
import uuid
import sys
import unittest
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/SpDB/python')
import spdm
from spdm.flow.ModuleRepository import ModuleRepository
from spdm.util.logger import logger
import pprint
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/FyBuild/python')
from fypm.ModuleEb import ModuleEb
from deal_yamlfile import record_variable,record_variable_append,load_templefile

def usage():
    sys.stderr.write('Usage: %s path  tempfile\n' % sys.argv[0])

if __name__ == "__main__":
    # logger.disable('logger.debug')

    if len(sys.argv) < 3:
        sys.stderr.write('%s: too few arguments\n' % sys.argv[0])
        usage()
        sys.exit(1)
    # path = '/gpfs/fuyun/software/FyBuild/python/fypm/tests/data/FuYun/configure.yaml'
    path = sys.argv[1]
    # logger.info("====== START =======")
    # os.environ['modulename']=str(COMMITMES)
    load_result = load_templefile(sys.argv[2])
    name=load_result['name']
    version=load_result['version']
    tag=load_result['tag']
    # module = ModuleEb(name,version,tag,repo_name='FuYun', repo_tag='FY', path=path)
    # configure_path ="/gpfs/fuyun/software/FyBuild/tests/data//FuYun/configure.yaml"
    module = ModuleEb(name,version,tag,repo_name='FuYun',install_args=['-r', '--minimal-toolchains'] ,repo_tag='FY', path=path)
    # module = ModuleEb(name,version,tag=,repo_name='FuYun', install_args=['-r', '--minimal-toolchains'] ,repo_tag='FY', path=configure_path)
    ebfilespath=module.search_ebfiles()
    print(f'the check ebfiles result is',ebfilespath)
    if os.path.exists(ebfilespath) == True : 
        py_object={'ebfiles-keyword':"EBexists"}
        record_variable_append(sys.argv[2] ,py_object)
        templename=sys.argv[2].split("/")[-1]
        os.rename(templename,"EBexists-"+templename)
        # gitadd = "git add ."
        # gitcommit = 'git commit -m '+ ' '+ '"'+ deployfile[0] +'"' 
        # gitcommand = gitadd +  ' ' +"&&" + ' ' +gitcommit 
        # git_system_out = module._run_command(gitcommand) 
    else:
        py_object={"keyword":"Non-EBexists"}
        record_variable_append(sys.argv[2] ,py_object)
        templename=sys.argv[2].split("/")[-1]
        os.rename(templename,"Non-EBexists-"+templename)
        # os.rename(sys.argv[2],"uninstall-"+sys.argv[2])
    # keyword=py_object['keyword']   
    # file_name = keyword+".txt"
    # result=touch_keyword_file(file_name)
    # if result == file_name:
    #     sys.exit(0)
    # else:
    #     sys.exit(1)