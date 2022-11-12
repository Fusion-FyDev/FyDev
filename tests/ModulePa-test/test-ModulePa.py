import os
import sys
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/SpDB/python')
import spdm
from spdm.flow.ModuleRepository import ModuleRepository
from spdm.util.logger import logger
import pprint
# sys.path.append('/scratch/liuxj/FYDEV-Workspace/FyBuild/python')
from fypm.ModulePa import ModulePa
class List(test):
    def list(self):
        self.module = ModulePa(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path="/scratch/liuxj/FYDEV-Workspace/FyDev/python/tests/data/FuYun/configure.yaml")
        print(dir(module))
        print("hello world")

        # module3 = module.init()
        result = self.module.listdepend()
        # print(dir(module3))
        # print(module3)
        print(result)
if __name__ == "__main__":
    logger.info("====== START =======")
    # module = ModulePa(name='genray-mpi',version='201213',tag="gompi-2020a ",repo_name='FuYun', repo_tag='FY', path="/scratch/liuxj/FYDEV-Workspace/FyDev/python/tests/data/FuYun/configure.yaml")
    # print(dir(module))
    # print("hello world")

    # # module3 = module.init()
    # result = module.listdepend()
    # # print(dir(module3))
    # # print(module3)
    # print(result)
    List()
    logger.info("====== END =======")   