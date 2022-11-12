import os
import sys


def check_module_exit(argv):
    # modulename = 'cql3d'
    infor = 'Unable to find'
    namelist = []
    # print(argv)
    print(len(argv))
    # print(argv[2])
    for i in range(1, len(argv)):
        # print(i)
        # j=i+1
        namelist.append(argv[i])
    for i in range(0, len(namelist)):
        print(namelist[i])
    # namelist=[modulename,moduleversion,toolchainname,toolchainversion]
    fuhaolist = ['/', '-', '-', '-']
    fuhaolist2 = ['-', '-', '-', '-']
    flag = True
    results = []
    global Modulename
    global Modulename_verison
    global MODULENAME
    MODULENAME = namelist[0]
    global MODULENAME_VERSION
    MODULENAME_VERSION = namelist[0]
    # print(MODULENAME)
    # print(MODULENAME_VERSION)
    # modulename_version=''
    while flag:
        for i in range(0, len(namelist)-1):
            print(MODULENAME)
            print(MODULENAME_VERSION)
            os.environ['Modulename'] = str(MODULENAME)
            os.environ['Modulename_version'] = str(MODULENAME_VERSION)
            os.system('(module spider $Modulename) 2>$Modulename_version.log')
            # val = os.system('(module spider $Modulename) 2>$MODULENAME_VERSION.log')
            with open("{0}.log".format(MODULENAME_VERSION), "r") as result:
                for line in result:
                    results.append(line)
                    if (infor in line):
                        flag = False
            print(flag)
            if (flag == False):
                break
            else:
                print(fuhaolist[i])
                MODULENAME = MODULENAME+fuhaolist[i]+namelist[i+1]
                # MODULENAME.join(fuhaolist[i])
                MODULENAME_VERSION = MODULENAME_VERSION + \
                    fuhaolist2[i]+namelist[i+1]
                # MODULENAME_VERSION.join(fuhaolist2[i])
                print(MODULENAME)
                print(MODULENAME_VERSION)
                continue
        return(flag)


if __name__ == '__main__':
    # falg_value=check_module_exit(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4])
    flag_value = check_module_exit(sys.argv)
    # print(len(falg_value))
    print(flag_value)
