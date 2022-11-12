import os
import sys
import subprocess


def check_module_exit(FY_MODULENAME, FY_MODULEVERSION):
    infor = 'Unable to find'
    flag = True
    os.environ['Modulename'] = str(FY_MODULENAME)
    # os.environ['Module'] = str(MODULENAME)
    # os.environ['Modulename_version'] = str(FY_MODULEVERSION)
    # os.system('(module load $Modulename) && echo $EBROOT')
    os.environ['Modulename_version'] = str(FY_MODULEVERSION)
    os.system('(module spider $Modulename) 2>/tmp/$Modulename_version.log')
    with open("/tmp/{0}.log".format(FY_MODULEVERSION), "r") as result:
        for line in result:
            # results.append(line)
            if (infor in line):
                flag = False
                # print(flag)
    os.remove("/tmp/"+FY_MODULEVERSION+".log")
    return flag


    #
if __name__ == '__main__':
    # falg_value=check_module_exit(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
    flag_value = check_module_exit(sys.argv[1], sys.argv[2])
    # print(len(falg_value))
    print(flag_value)
