# -*- coding: utf-8 -*-
import unittest
import os
import sys
import shutil
import subprocess
sys.path.append('/scratch/liuxj/workspace/SpDB/python')
# import spdm
from spdm.flow.ModuleRepository import ModuleRepository
from spdm.util.logger import logger
import pprint
sys.path.append('/scratch/liuxj/workspace/FyBuild/python')

## check the module and fymodule_file is exsit or not
from fypm.ModulePa import ModulePa
# module = ModulePa(name='genray-mpi',version='201213',tag=" ",repo_name='FuYun', repo_tag='FY', path=configure_path)
configure_path ="/gpfs/fuyun/software/FyBuild/tests/data//FuYun/configure.yaml"
module = ModulePa(name='genray',version='10.13.200117',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path=configure_path)
fymodule_es = module.search_fymodule_file()
flag,fymodulefile,modulefilename = module.search_fymodule_file()

print(modulefilename)
print(module._conf.get("MoResp_dir"))
# print(module.fullname)
# modulename1 = module.search_tmple_file()
# MoResp_dir = module._conf.get("MoResp_dir")
gitdir = "/scratch/liuxj/workspace/fybuild-devops"
### check if the yamlfile is exit  in gitdir ?
# create a empty text file
# in current directory
try:
    file_path = gitdir +'/ModuleRepository/' + module.name+'/'+modulefilename
    # create file
    with open(file_path, 'x') as fp:
        pass
except:
    print('File already exists')
os.chdir(gitdir)
gitadd = "git add ."
gitcommit = 'git commit -m '+ ' '+ '"'+ module.fullname +'"'+"+"+"rebuild"
# gitcommit = 'git commit -m '+ ' '+ '"'+ module.fullname +'"'+"+"+" "
gitpush="git push"
        # modulecmd = "/usr/share/lmod/lmod/libexec/lmod purge " + "&&" + ' ' + modulecmd
gitcommand = gitadd +  ' ' +"&&" + ' ' +gitcommit + ' ' + "&&" + ' ' +gitpush
print(gitcommand)
git_system_out = module._run_command(gitcommand)
print(git_system_out.stdout)