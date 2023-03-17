
import collections
import os
import sys
sys.path.append('/scratch/liuxj/FYDEV-Workspace/SpDB/python')
import pathlib
import shlex
import subprocess
import signal
import traceback
import uuid
import re
# from ..util import io
# from ..util.dict_util import deep_merge_dict, format_string_recursive
# from ..util.Factory import Factory
# from ..util.LazyProxy import LazyProxy
from spdm.util.logger import logger
# from ..util.RefResolver import RefResolver
# from ..util.sp_export import sp_find_module
# from ..util.urilib import urisplit
# from .SpModule import SpModule
sys.path.append('/scratch/liuxj/FYDEV-Workspace/FyBuild/python')
from spdm.flow.ModuleRepository import ModuleRepository
import pprint
from fypm.StandardModule import  StandardModule

def fetch_max(self, **kwargs):
    #because is max ,so just work for name  
    substr = self.init(**kwargs)
    # substr = self._fullname
    output = self.execute('-t', 'avail', substr)
    # the output is standard moudles ,such as genrar/2013-foss-2021a
    # print("the out put is",output)
    ret = []
    for line in output.split('\n'):
        if not line or line[-1] == ':':
            # Ignore empty lines and path entries
            continue
        # print(line)
        module = re.sub(r'\(\S+\)', '', line)
        print("the module is",module)
        ## what's different between the flowing two lines???
        # ret.append(StandardModule(module))
        ret.append(module)
    return [str(m) for m in ret]
    # return ret 

def fetch_min(self, **kwargs):
    """
    because is min ,so just work for name/version-tag ,so now we need to check the version 
    and tag .if version and tag is null ,we need read the basic information from the configure.yaml.
    such as :  
    version is null ,then I cannot work ,I dont know what you want ,and I just fetch the max to you.
    version is not null:
        tag is null ,and tag = default-tag ,then fetch_min(name/version-default-tag )
        tag is tag ,then fetch_min(name/version-tag)
    """
    substr = self.init(**kwargs).fullname
    logger.info(f"the init result  is {substr}")
    output = self.execute('-t', 'avail', substr)
    # print("the out put is",output)
    ret = []
    for line in output.split('\n'):
        if not line or line[-1] == ':':
            # Ignore empty lines and path entries
            continue
        print(line)
        module = re.sub(r'\(\S+\)', '', line)
        print("the module is",module)
        ret.append(StandardModule(module))
        # ret.append(module)
    return [str(m) for m in ret]
    # return ret





if __name__ == "__main__":

    logger.info("====== START =======")

    # module = ModuleRepoitory(repo_name='FuYun', repo_tag='FY')
    module = Module(name='genray',version='2013',tag="gompi-2019a ",repo_name='FuYun', repo_tag='FY', path="/scratch/liuxj/FYDEV-Workspace/FyDev/python/tests/data/FuYun/configure.yaml")
    print(dir(module))
    print((module.fullname))
    # ## test for init :
    # moduleinit = module.init(name='genray',version='10.13',tag=" ")
    # print(moduleinit)
## test for fetch
    module3 = module.fetch_max(name='genray',version=' ',tag="  ", path="/scratch/liuxj/FYDEV-Workspace/FyDev/python/tests/data/FuYun/configure.yaml")
    print(dir(module3))
    print(module3)
    logger.info("====== Done =======")


