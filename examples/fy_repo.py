
import sys
sys.path.append("/home/salmon/workspace/FyDev/python")
sys.path.append("/home/salmon/workspace/SpDB/python")
from fydev.FyRepository import FyRepository
from pprint import pprint

if __name__ == '__main__':
    repo = FyRepository(
        FY_ROOT="/home/salmon",
        install_path={
            "": ["/home/salmon/workspace/FyDev/examples/fydev/{name}/{version}-{toolchain}{versionsuffix}/fymodule.yaml",
                 "module:///work/modulefiles/all", ],
            "physics.": ["/work/software/physics/{name}/{suffix}/fymodule.yaml",
                         "/work/software2/physics/{id}.yaml",
                         "http://fydev.asipp.ac.cn/modules/physics/{id}",
                         "/gpfs/fydev/{id}/fymodule.yaml",
                         "/home/salmon/workspace/FyDev/tests/ModuleRepository/{id}/fymodule.yaml"]
        }
    ).entry

    # with Session("~/workdir/TEST_GENRAY") as session:
    genray = repo.physics.genray[{"version": "1.1.1", "toolchain": "GCC"}].bin.xgenray(dt=0.1, ne=1.0e19)
    # genray2 = repo.experimental.genray["1.1.1", "GCC"].bin.xgenray(dt=0.1, ne=1.0e19)
    # cql3d = repo.physics.cql3d(dt=0.1, input=genray)

    # repo.path[""].append("{FY_ROOT}")
    # repo.path["fydev."].append("python://")
    # repo.path["fydev."].append("python://xxx/python")
    # repo.path["fydev."].append("module:///work/modulefiles/all")
    # repo.path["fydev."].append("guix:///work/modulefiles/all")
    # repo.path["fydev.physics."].append("/work/software/physics")
    # repo.path["fydev.physics."].append("/work/software2/physics")
    # repo.path["fydev.physics."].append("http://fydev.asipp.ac.cn/modules/physics")
    # repo.path["asipp.numeric."].append("/gpfs/fydev")
    # repo.path["fydev.physics."].append("/home/salmon/workspace/FyDev/tests/ModuleRepository/")
    # repo.envs["FY_ROOT"] = "/home/salmon"
