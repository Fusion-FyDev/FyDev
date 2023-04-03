
from pprint import pprint
import sys
import os
sys.path.append("/home/salmon/workspace/FyDev/python")
sys.path.append("/home/salmon/workspace/SpDB/python")
#####################

FY_TAG_TEMPLATE = "{name}/{version}-{toolchain}{suffix}"

os.environ["FY_ROOT"] = "/home/salmon/workspace/FyDev/examples/fydev"

if __name__ == '__main__':
    from fydev import FyRepository, FyExecutor

    fydev = FyRepository({
        "name": "FyDev",
        "install_path": {
            "": [
                # "module://{name}?version={version}&toolchain={toolchain}&suffix={suffix}",
                "{FY_ROOT}/software/{name}/{version}-{toolchain}{suffix}/fy_module.yaml",
            ],
        },
        "repository_path": {
            "": ["eb://{name}-{version}-{toolchain}{suffix}",
                 "{FY_ROOT}/repository/{name}-{version}-{toolchain}{suffix}.yaml",
                 "http://fydev.asipp.ac.cn/modules/{name}-{version}-{toolchain}{suffix}", ]
        }}
    ).entry

    # module load physics/genray/1.1.1-gompi-2020b
    # ${EBROOTGENRAY}/bin/xgenray --dt 01 --ne 1.0e19
    atok: FyExecutor = fydev.physics.atok[201213, "gompi-2020b"].load()

    # module load physics/cql3d/1.2.0-GCC-10.2.0
    # ${EBROOTCQL3D}/bin/cql3d --dt 01  --input <genray>
    bits: FyExecutor = fydev.physics.bits[{"version": "1.2.0", "toolchain": "GCC",
                                           "suffix": "10.2.0"}].bin.bits.load()

    res1 = atok(input1="input1.dat", input2="input2.dat",  output="output.dat", verbose=True")
                
    psi= res1["psi"]

    res2 = bits(dt=0.1, psi=res1.outputs["psi"])

    print(bits.outputs["profiles"])
