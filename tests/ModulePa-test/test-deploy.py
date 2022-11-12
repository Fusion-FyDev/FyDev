# -*- coding: utf-8 -*-
import unittest
import os
import sys
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/SpDB/python')
import spdm

from spdm.flow.ModuleRepository import ModuleRepository
from spdm.util.logger import logger
import pprint
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/FyBuild/python')
from fypm.ModulePa import ModulePa

class Test(unittest.TestCase):
    def setUp(self):
        """ setUp()"""
        self.module = ModulePa(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path="/scratch/liuxj/FYDEV-Workspace/FyBuild/python/tests/data/FuYun/configure.yaml")
        # testcase_dir = os.path.split(os.path.realpath(__file__))[0]
        # load(testcase_dir + "\input.h")
        pass
    def test_search(self):
        templename='/gpfs/scratch/liuxj/FYDEV-Workspace/FyBuild/ModuleRepository/temple.yaml'
        falg = 1

        modulename = self.module.search_tmple_file()

        if modulename[0] != 0:
            self.assertEqual(modulename[0],falg)
        print(f"the result is  {modulename}")
        # if modulename[1] != " ":
        #     self.assertEqual(templename,modulename[1])
        self.module.deploy()
        # print("hello wold")

    def tearDown(self):
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()
