from pprint import pprint
import sys
import os
sys.path.append("/home/salmon/workspace/FyDev/python")
sys.path.append("/home/salmon/workspace/SpDB/python")
#####################

FY_TAG_TEMPLATE = "{name}/{version}-{toolchain}{versionsuffix}"

os.environ["FY_ROOT"] = "/home/salmon/workspace/FyDev/examples/fydev"

if __name__ == '__main__':
    from fydev.FyPackage import FyPackage, FY_INSTALL_DIR
    from spdm.util.logger import logger
    # os.environ["FY_INSTALL_PREFIX"] = "/home/salmon/workspace/FyDev/examples/fydev/software/"
    # pkg: FyPackage = FyPackage({"information": {"name": "genray", "version": "1.1.1", "toolchain": "GCC"}})
    os.environ["FY_INSTALL_DIR"] = FY_INSTALL_DIR

    envs = {k: v for k, v in os.environ.items() if k.startswith("FY_")}

    pkg: FyPackage = FyPackage.create("phys/genray", version="201213", toolchain="gompi", suffix="2020b",
                                      # "file://{FY_ROOT}/repository/physics/genray-201213-gompi-2020b.yaml",
                                      # "module://physics/genray?version=1.1.1&toolchain=GCC",
                                      envs=envs,
                                      auto_install=True)

    genray = pkg.load("bin/xgenray -i {input} -o {output} -v {verbose}",
                      input="input.dat",
                      output="output.dat",
                      verbose=True)

    # logger.debug(pkg.description)

    res = genray(dt=0.1, ne=1.0e19)
