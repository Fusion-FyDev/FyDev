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
        self.module = ModulePa(name='genray',version='2013',tag="gompi-2019a ",repo_name='FuYun', repo_tag='FY', path="/scratch/liuxj/FYDEV-Workspace/FyDev/python/tests/data/FuYun/configure.yaml")
        # testcase_dir = os.path.split(os.path.realpath(__file__))[0]
        # load(testcase_dir + "\input.h")
        pass
    def test_init(self):
        fulname='genray/2013-gompi-2019a'
        version = self.module._version

        modulename = self.module.initpa()
        self.assertEqual(modulename,fulname)
        if version == " ":
            self.assertNotIn('/',modulename)
        # print("hello wold")

    def tearDown(self):
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()