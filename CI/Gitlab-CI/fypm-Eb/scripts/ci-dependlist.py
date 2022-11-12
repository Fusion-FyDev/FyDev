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
    path = sys.argv[1]
    # logger.info("====== START =======")
    # os.environ['modulename']=str(COMMITMES)
    # templefile="/tmp/temple.yaml"
    # templefile=sys.argv[1]

    load_result = load_templefile(sys.argv[2])
    name=load_result['name']
    version=load_result['version']
    tag=load_result['tag']
    module = ModuleEb(name,version,tag,repo_name='FuYun',install_args=['-r', '--minimal-toolchains'] ,repo_tag='FY', path=path)
    checkresult=module.listdepend()
    try:
        
        print(f'the check result is ',checkresult)
        py_object={
            'depend_cmd':checkresult[0],
            'packageslist':checkresult[1],    
                }
        print(py_object)
        record_variable_append(sys.argv[2] ,py_object)    
    except:
        sys.exit(1)