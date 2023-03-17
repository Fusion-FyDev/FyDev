
from fydev.FyRepository import FyRepository
from pprint import pprint

if __name__ == '__main__':
    repo = FyRepository()
    repo.path[""].append("{FY_ROOT}")
    repo.path["fydev.physics."].append("/work/software/physics")
    repo.path["fydev.physics."].append("/work/software2/physics")
    repo.path["fydev.physics."].append("http://fydev.asipp.ac.cn/modules/physics")
    repo.path["asipp.numeric."].append("/gpfs/fydev")
    repo.path["fydev.physics."].append("/home/salmon/workspace/FyDev/tests/ModuleRepository/")

    repo.envs["FY_ROOT"] = "/home/salmon"

    desc = repo.fetch_description("fydev.physics.genray", "10.13_200117-gompi-2020a")

    pprint(desc)

    foo = repo.create("fydev.physics.genray", "10.13_200117-gompi-2020a")
