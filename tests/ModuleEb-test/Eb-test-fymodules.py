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

class Test(unittest.TestCase):
    def setUp(self):
        """ setUp()"""
        configure_path ="/gpfs/fuyun/software/FyBuild/tests/data//FuYun/configure.yaml"
        self.module = ModuleEb(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path=configure_path)
        # testcase_dir = os.path.split(os.path.realpath(__file__))[0]
        # load(testcase_dir + "\input.h")
        pass
    def test_init(self):
        fulname='genray/201213-gompi-2019b'

        checkresult  = self.module.search_fymodule()
        checkresultsources  = self.module.fetchsources(dry_run=True)
        print(checkresult)
        print(checkresultsources)
        # self.assertEqual(modulename,fulname)

        # print("hello wold")

    def tearDown(self):
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()