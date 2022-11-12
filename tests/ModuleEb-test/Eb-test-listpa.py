# -*- coding: utf-8 -*-
import unittest
import os
import sys
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/SpDB/python')
import spdm

from spdm.flow.ModuleRepository import ModuleRepository
from spdm.util.logger import logger
import pprint
sys.path.append('/scratch/liuxj/FYDEV-Workspace/FyBuild/python')
from fypm.ModuleEb import ModuleEb

import warnings 
# configure_path ="/gpfs/fuyun/software/FyBuild/python/tests/data//FuYun/configure.yaml"
# module = ModuleEb(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path=configure_path)
# checkresult = module.checkpa()
# print(checkresult)

class Test(unittest.TestCase):
    def setUp(self):
        warnings.simplefilter('ignore', ResourceWarning)
        """ setUp()"""
        configure_path ="/gpfs/fuyun/software/FyBuild/python/tests/data//FuYun/configure.yaml"
        self.module = ModuleEb(name='genray-mpi',version='201213',tag=" ",repo_name='FuYun', repo_tag='FY', path=configure_path)
        # testcase_dir = os.path.split(os.path.realpath(__file__))[0]
        # load(testcase_dir + "\input.h")
        pass
    def test_init(self):
        fulname='genray-mpi/201213-gompi-2020a'

        checkresult  = self.module.list_avail_pa()
        print(checkresult)
        # self.assertEqual(checkresult[1][0],fulname)
        self.assertIn(fulname,checkresult)

        # print("hello wold")

    def tearDown(self):
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()