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
        configure_path ="/gpfs/fuyun/software/FyBuild/tests/data//FuYun/configure.yaml"
        self.module = ModuleEb(name='zlib',version='1.2.11',tag="GCCcore-9.3.0 ",repo_name='FuYun', repo_tag='FY', path=configure_path)
        # testcase_dir = os.path.split(os.path.realpath(__file__))[0]
        # load(testcase_dir + "\input.h")
        pass
    def test_init(self):
        fulname='zlib/1.2.11-GCCcore-9.3.0.eb'

        checkresult  = self.module.fetch_sources(dry_run=True)
        print(checkresult)
        # self.assertEqual(checkresult[1][0],fulname)
        # self.assertIn(fulname,checkresult)

        # print("hello wold")

    def tearDown(self):
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()