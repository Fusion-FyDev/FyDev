
from pprint import pprint
from fydev.FyRepository import FyRepository
import sys
import os
sys.path.append("/home/salmon/workspace/FyDev/python")
sys.path.append("/home/salmon/workspace/SpDB/python")
#####################

FY_TAG_TEMPLATE = "{name}/{version}-{toolchain}{versionsuffix}"

os.environ["FY_ROOT"] = "/home/salmon/workspace/FyDev/examples/fydev"

if __name__ == '__main__':
    fydev = FyRepository({
        "name": "FyDev",
        "install_path": {
            "": [f"{{FY_ROOT}}/software/{FY_TAG_TEMPLATE}/fy_module.yaml",
                 "module:///work/modulefiles/all", ],
            "physics.": [f"/work/software/physics/{FY_TAG_TEMPLATE}/fy_module.yaml",
                         f"/home/salmon/workspace/FyDev/tests/ModuleRepository/{FY_TAG_TEMPLATE}/fy_module.yaml"]
        },
        "repository_path": {
            "": ["{FY_ROOT}/repository/{name}-{version}-{toolchain}{versionsuffix}.yaml",
                 "http://fydev.asipp.ac.cn/modules/{name}-{version}-{toolchain}{versionsuffix}", ]
        }}
    ).entry

    # with Session("~/workdir/TEST_GENRAY") as session:
    genray = fydev.physics.genray[{"version": "1.1.1", "toolchain": "GCC"}](dt=0.1, ne=1.0e19)

    cql3d = fydev.physics.cql3d[{"version": "1.2.0", "toolchain": "GCC"}].bin.cql3d(dt=0.1, ne=1.0e19, input=genray)

    print(cql3d.result)

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
