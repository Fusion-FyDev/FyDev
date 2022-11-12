# -*- coding: utf-8 -*-
import unittest
import os
import sys
sys.path.append('/scratch/liuxj/FYDEV-Workspace/SpDB/python')
import spdm

from spdm.flow.ModuleRepository import ModuleRepository
from spdm.util.logger import logger
import pprint
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/FyBuild/python')
from fypm.ModuleEb import ModuleEb

import warnings 
configure_path ="/gpfs/fuyun/software/FyBuild/tests/data//FuYun/configure.yaml"
# module = ModuleEb(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path=configure_path)
module = ModulePa(name=' Eigen',version='3.3.8',tag="GCCcore-10.2.0 ",repo_name='FuYun', repo_tag='FY', path=configure_path)
# CMake-3.16.5-GCCcore-9.3.0.eb
# Vim-8.1.1209-GCCcore-8.2.0-Python-3.7.2
listresult=module.search_ebfiles()
print(listresult)
# checkresult=module.checkpa()
# # installresult = module.build_install(extend_args=['-r', '--minimal-toolchains'])
installresult = module.installpa()
# print('the list module result is %s' % listresult)
# print(checkresult)
# print(type(checkresult))
print(installresult)
# deployresult = module.deploy(MoResp_dir="/scratch/liuxj/workspace/fybuild-devops/ModuleRepository")
# print(deployresult)
# for i in range(0,len(checkresult)):
#     print(checkresult[i])


# class Test(unittest.TestCase):
#     def setUp(self):
#         warnings.simplefilter('ignore', ResourceWarning)
#         """ setUp()"""
#         configure_path ="/gpfs/fuyun/software/FyBuild/python/tests/data//FuYun/configure.yaml"
#         self.module = ModuleEb(name='vim',version='',tag=" ",repo_name='FuYun', repo_tag='FY', path=configure_path)
#         # testcase_dir = os.path.split(os.path.realpath(__file__))[0]
#         # load(testcase_dir + "\input.h")
#         pass
#     def test_init(self):
#         fulname='genray-mpi/201213-gompi-2020a'

#         checkresult  = self.module.checkpa()
#         print(checkresult)
#         self.assertEqual(checkresult[1][0],fulname)

#         # print("hello wold")

#     def tearDown(self):
#         return super().tearDown()

# if __name__ == '__main__':
#     unittest.main()