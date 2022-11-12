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
import shutil
def usage():
    sys.stderr.write('Usage: %s path tempfile\n' % sys.argv[0])

def touch_keyword_file(file_name):
    filename=pathlib.Path(file_name).touch()
    if pathlib.Path(file_name).is_file():
        return file_name
if __name__ == "__main__":
    # logger.disable('logger.debug')

    if len(sys.argv) < 3:
        sys.stderr.write('%s: too few arguments\n' % sys.argv[0])
        usage()
        sys.exit(1)
    # path = '/gpfs/fuyun/software/FyBuild/python/tests/data/FuYun/configure.yaml'
    # logger.info("====== START =======")
    # os.environ['modulename']=str(COMMITMES)
    # templefile="/scratch/liuxj/workspace/FyBuild/CI/Gitlab-CI/fypm-Eb/scripts/temple.yaml"
    path = sys.argv[1]
    # templefile=sys.argv[1]
    load_result = load_templefile(sys.argv[2])
    # load_result = load_templefile(templefile)
    name=load_result['name']
    version=load_result['version']
    tag=load_result['tag']
    buildtype=load_result['buildtype']
    if buildtype == "None":
        module = ModuleEb(name,version,tag,repo_name='FuYun',install_args=['-r', '--minimal-toolchains'] ,repo_tag='FY', path=path)
    if buildtype == "rebuild":
        module = ModuleEb(name,version,tag,repo_name='FuYun',install_args=['-r','--rebuild', '--minimal-toolchains'] ,repo_tag='FY', path=path)    
    print(dir(module))
    print(path)
    module.load_configure(path)
    checkresult=module.installpa()
    try:
        
        print(f'the check result is ',checkresult)
        py_object={
            'ebfilepath':checkresult[0],
            'buildcmd':checkresult[1],    
                }
        record_variable_append(sys.argv[2] ,py_object)
        templename=sys.argv[2].split("/")[-1]
        os.rename(templename,"Tdeploy-"+templename)      
    except:
        sys.exit(1)
