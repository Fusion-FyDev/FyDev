import collections
import os
import pathlib
import shlex
import subprocess
import traceback
import uuid
import sys
from fypm.StandardModule import StandardModule
from deal_yamlfile import record_variable,record_variable_append
# from ruamel import yaml

def usage():
    sys.stderr.write('Usage: %s NAME \n' % sys.argv[0])


# def record_variable(yaml_file,py_object):
#     file = open(yaml_file, 'w', encoding='utf-8')
#     # yaml=YAML(typ='unsafe', pure=True)
#     yaml.dump(py_object, file, Dumper=yaml.RoundTripDumper)
#     file.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write('%s: too few arguments\n' % sys.argv[0])
        usage()
        sys.exit(1)
    # logger.info("====== START =======")
    # os.environ['modulename']=str(COMMITMES)
    module = StandardModule(sys.argv[1] ,collection=False, path=None)
    # print(module.name,module.version,module.tag,module.fullmodulename)
    py_object = {
        'name':module.name,
        'version':module.version,
        'tag':module.tag,
        'fullname':module.fullname,
        'fullmodulename':module.fullmodulename,
    }
    # os.chdir('/scratch/liuxj/workspace/autodev')
    record_variable(sys.argv[2] ,py_object)
    # print(dir(module))
    # name = module.name
    # version = module.version
    # tag = module.tag
    # print(name,version,tag)
    # print(module)
    # print("hello world")

    
    # print(dir(module3))
    # print(module3)
    # logger.info("====== END =======")