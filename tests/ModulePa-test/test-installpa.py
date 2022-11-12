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
        self.module = ModulePa(name='genray-mpi',version='201213',tag=" ",repo_name='FuYun', repo_tag='FY', path="/scratch/liuxj/FYDEV-Workspace/FyBuild/python/tests/data/FuYun/configure.yaml")
        # testcase_dir = os.path.split(os.path.realpath(__file__))[0]
        # load(testcase_dir + "\input.h")
        pass

    def test_init(self):
        modulename=[{'name': 'genray-mpi/201213-gompi-2020a', 'collection': False, 'path': '/gpfs/fuyun/modules/all', 'ebfile': '/gpfs/fuyun/software/genray-mpi/201213-gompi-2020a/easybuild/genray-mpi-201213-gompi-2020a.eb'}]
        # build_command = 'eb genray-mpi-201213-gompi-2019b.eb -D --minimal-toolchains --experimental --use-existing-modules --info --robot-paths=/gpfs/fuyun/software/EasyBuild/4.3.2/easybuild/easyconfigs:/scratch/liuxj/FYDEV-Workspace/FyBuild/EbfilesRespository'

        installtest = self.module.installpa()

        print(installtest)
        # self.assertEqual(installtest[0],modulename)
    


    def tearDown(self):
        return super().tearDown()

if __name__ == '__main__':
    unittest.main()