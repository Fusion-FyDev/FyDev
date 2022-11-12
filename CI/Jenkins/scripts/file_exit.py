import os

import sys


def list_all_files(rootdir):
    _files = []
    list = os.listdir(rootdir)
    for i in range(0, len(list)):
        path = os.path.join(rootdir, list[i])
        if os.path.isdir(path):
            _files.extend(list_all_files(path))
        if os.path.isfile(path):
            _files.append(path)
    return _files


def check_filename_exit(rootdir, filename):
    flag = 0
    if os.path.exists(rootdir):
        _fs = list_all_files(rootdir)
        moduledir = ''
        # print(len(_fs))
        for i in range(0, len(_fs)):
            _fs_1ist = _fs[i].split("/", -1)
            _fs_filename = _fs_1ist[-1]
            if(filename == _fs_filename):
                # print(_fs_filename)
                # print(_fs[i])
                moduledir = _fs[i]
                flag += 1
        return flag
    else:
        print("the directory  is not exist,please create it", rootdir)
        os.makedirs(rootdir)
        return flag
# the path and filename is get from  env.COMMITMES   and  env.WORKSPACE


if __name__ == '__main__':
    falg_value = check_filename_exit(sys.argv[1], sys.argv[2])
    # print(len(falg_value))
    print(falg_value)
