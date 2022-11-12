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
        self.module = ModulePa(name='genray-mpi',version='201213',tag="gompi-2020a",repo_name='FuYun', repo_tag='FY', path="/scratch/liuxj/FYDEV-Workspace/FyDev/python/tests/data/FuYun/configure.yaml")
        # testcase_dir = os.path.split(os.path.realpath(__file__))[0]
        # load(testcase_dir + "\input.h")
        pass
    def test_init(self):
        FULLname='genray-mpi/200118-gompi-2019b'
        version = self.module._version

        modulename = self.module.listpa(max_list=True)
        ebfilename = self.module._ebfilename
        print(ebfilename)
        self.assertEqual(modulename[0],FULLname)


    def tearDown(self):
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()