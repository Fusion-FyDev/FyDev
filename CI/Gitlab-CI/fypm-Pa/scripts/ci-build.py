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
from fypm.ModulePa import ModulePa
from deal_yamlfile import record_variable,record_variable_append,load_templefile
import shutil
def usage():
    sys.stderr.write('Usage: %s NAME VERSION TAG  tempfile\n' % sys.argv[0])

def touch_keyword_file(file_name):
    filename=pathlib.Path(file_name).touch()
    if pathlib.Path(file_name).is_file():
        return file_name
if __name__ == "__main__":
    # logger.disable('logger.debug')

    if len(sys.argv) < 2:
        sys.stderr.write('%s: too few arguments\n' % sys.argv[0])
        usage()
        sys.exit(1)
    path = '/gpfs/fuyun/software/FyBuild/python/tests/data/FuYun/configure.yaml'
    # logger.info("====== START =======")
    # os.environ['modulename']=str(COMMITMES)
    # templefile="/tmp/temple.yaml"
    templefile=sys.argv[1]
    load_result = load_templefile(templefile)
    name=load_result['name']
    version=load_result['version']
    tag=load_result['tag']
    module = ModulePa(name,version,tag,repo_name='FuYun', repo_tag='FY', path=path)
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
        record_variable_append(templefile ,py_object)       
    except:
        sys.exit(1)
    MoResp_Dir = module._conf.get("MoResp_dir")
    if pathlib.Path(MoResp_Dir).exists() :
        targetpath=MoResp_Dir+name
        if pathlib.Path(targetpath).exists() :
            shutil.copy(sys.argv[1],targetpath)
        else:
            path=pathlib.Path(targetpath)
            path.mkdir()
            shutil.copy(sys.argv[1],targetpath)
    else:
       sys.stderr.write('the MoResp_Dir is not exsit ,p;ease the manager') 
       sys.exit(1) 
