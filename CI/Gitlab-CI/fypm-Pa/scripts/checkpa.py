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
    path = '/gpfs/fuyun/software/FyBuild/python/fypm/tests/data/FuYun/configure.yaml'
    # logger.info("====== START =======")
    # os.environ['modulename']=str(COMMITMES)
    load_result = load_templefile(sys.argv[1])
    name=load_result['name']
    version=load_result['version']
    tag=load_result['tag']
    module = ModulePa(name,version,tag,repo_name='FuYun', repo_tag='FY', path=path)
    checkresult=module.checkpa()
    print(f'the check result is ',checkresult)
    if checkresult == True :
        py_object={'keyword':"Installed"}
        record_variable_append(sys.argv[1] ,py_object)
        templename=sys.argv[1].split("/")[-1]
        os.rename(templename,"Installed-"+templename)
    else:
        py_object={"keyword":"Non-Install"}
        record_variable_append(sys.argv[1] ,py_object)
        templename=sys.argv[1].split("/")[-1]
        os.rename(templename,"Non-Install-"+templename)
        # os.rename(sys.argv[1],"uninstall-"+sys.argv[1])
    # keyword=py_object['keyword']   
    # file_name = keyword+".txt"
    # result=touch_keyword_file(file_name)
    # if result == file_name:
    #     sys.exit(0)
    # else:
    #     sys.exit(1)