# -*- python -*-
import os
import sys
from tempfile import  TemporaryFile
# from __future__ import print_function
from subprocess import PIPE, Popen
lmod_dir = os.getenv('LMOD_DIR')
sys.path.append(lmod_dir + '/../init')

## just test how to run mdoule commnad and how to list genray 
def module(command, *arguments):
    numArgs = len(arguments)
    A = [lmod_dir+'/lmod', 'python', command]
    if (numArgs == 1):
        A += arguments[0].split()
    else:
        A += list(arguments)

    proc = Popen(A, stdout=PIPE, stderr=PIPE)
    stdout, stderr = proc.communicate()
    err_out=sys.stderr
    if (os.environ.get('LMOD_REDIRECT','no') != 'no'):
        err_out=sys.stdout
    # print(stderr.decode(),file=err_out)
    exec(stdout.decode())
    return(stderr.decode())
    return(stdout.decode())
def ListPa(command, *arguments):
    module('use','/gpfs/fuyun/modules/all')
    spider_file = module(command,*arguments)
    with TemporaryFile('w+t') as spider_out:
        spider_out.writelines(spider_file)

        spider_out.seek(0)
        data = spider_out.readlines()
        infor = 'Unable to find'
        for line in data:
            if (infor in line):
                print('the packages is not exit ')
                print(line)
        # else:
        #     print(data)
        print(len(data))
ListPa('spider','genray/201214-gompi-2019b')

