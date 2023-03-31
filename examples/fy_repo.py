
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
            "": ["module://{name}/{version}-{toolchain}{versionsuffix}",
                 "{FY_ROOT}/software/{name}/{version}-{toolchain}{versionsuffix}/fy_module.yaml",
                 ],
        },
        "repository_path": {
            "": ["eb://{name}-{version}-{toolchain}{versionsuffix}",
                 "{FY_ROOT}/repository/{name}-{version}-{toolchain}{versionsuffix}.yaml",
                 "http://fydev.asipp.ac.cn/modules/{name}-{version}-{toolchain}{versionsuffix}", ]
        }}
    ).entry

    # module load physics/genray/1.1.1-gompi-2020b
    # ${EBROOTGENRAY}/bin/xgenray --dt 01 --ne 1.0e19
    genray = fydev.physics.genray[{"version": "1.1.1", "toolchain": "gompi",
                                   "versionsufix": "-2020b"}](nstep=100, dt=0.1, ne=1.0e19)

    # module load physics/cql3d/1.2.0-GCC-10.2.0
    # ${EBROOTCQL3D}/bin/cql3d --dt 01  --input <genray>
    cql3d = fydev.physics.cql3d[{"version": "1.2.0", "toolchain": "GCC",
                                 "versionsufix": "-10.2.0"}].bin.cql3d(dt=0.1, input=genray.nc_file)

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
