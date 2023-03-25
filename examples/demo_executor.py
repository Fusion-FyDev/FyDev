
from fydev.FyExecutor import FyExecutor
import sys
sys.path.append("/home/salmon/workspace/FyDev/python")

if __name__ == '__main__':
    genray = FyExecutor(name="genray", path="/home/salmon/workspace/FyDev/examples")

    res = genray(1, 2, 3, 4, 5, path="/x/xx/s/d/", time=0.1)

    print(genray.metadata)

    print(res["NCDATA"])
