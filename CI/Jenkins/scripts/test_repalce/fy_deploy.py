from shutil import copyfile
from sys import exit
import os
import subprocess
import yaml
import sys
DEPLOY_PATH = "/gpfs/fuyun"
# list all file in directory


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
# check the directory is exit or not ,
#   if exsit ,check the file in the directory
#       ok,flag +=1


def check_filename_exit(rootdir, filename,name,fy_filename):
    flag = 0
    print(rootdir+"/"+name)
    if os.path.exists(rootdir+"/"+ name):
        _fs = list_all_files(rootdir)
        # moduledir = ''
        # print(len(_fs))
        for i in range(0, len(_fs)):
            _fs_1ist = _fs[i].split("/", -1)
            _fs_filename = _fs_1ist[-1]
            if(filename == _fs_filename):
                # print(_fs_filename)
                # print(_fs[i])
                # moduledir = _fs[i]
                flag += 1
        return flag
        print(flag)
    else:
        print("the directory  is not exist,please create it", rootdir)
        os.makedirs(rootdir+"/"+ name)
        os.makedirs(rootdir+"/"+ name+"/"+fy_filename)
        return flag


def replace_value(moduleversion, fy_file, rootdir):
    # os.environ['Modulename'] = str(modulename)
    # os.environ['Modulename_version'] = str(mduleversion)
    # os.system('(module spider $Modulename) 2>/tmp/$Modulename_version.log')
    # os.system('cmd1 && cmd2') get the direcotry of successful eb file ,and the best way is copy it to the key [build]
    cmd1 = "module use " + DEPLOY_PATH + "/modules/all"
    cmd2 = " module load " + moduleversion
    cmd3 = "echo $EBROOTGENRAY"
    cmd = cmd1 + " && " + cmd2 + " && " + cmd3
    print("moduleversion:", moduleversion)
    print(cmd)
    out = subprocess.run(cmd, stdout=subprocess.PIPE, shell=True).stdout.decode(
        'utf-8').replace('\n', '').replace('\r', '')
    # result3 = subprocess.run(cmd, stdout=subprocess.PIPE)
    # module use /gpfs/fuyun/modules/all &&  module load genray/201213-gompi-2019b && echo $EBROOTGENRAY'
    print("the command out is ", out)

    filename = os.path.join(os.path.dirname(__file__),
                            fy_file).replace("\\", "/")
    print(filename)
    print("hello world")
    # f = open("/gpfs/fuyun/fy_modules/physics/"+filename)
    print("hello world")
    # y = yaml.load(f)
    # print(filename)
    with open(rootdir + "/" + fy_file) as f:
        print("the fy_file is", fy_file)
        doc = yaml.load(f, Loader=yaml.FullLoader)
        print("the init file is", doc)
        print(out)
        doc['build']['eb'] = out
    with open(rootdir + "/" + fy_file, 'w', encoding='utf-8') as f:
        yaml.safe_dump(doc, f, default_flow_style=False,
                       encoding='utf-8', allow_unicode=True)
        print("the last replace file is", doc)


def fy_deploy(rootdir, commitdir, tmpname, modulename, moduleversion):
    fy_filename = moduleversion.split("/",1)[1]
    name= moduleversion.split("/",1)[0]
    fy_file = fy_filename + ".yaml"
    print("the fy_file is ", fy_file)
    falg_value = check_filename_exit(rootdir, fy_file,name,fy_filename)
    print("falg_value:", falg_value)
    if(falg_value == 1):
        copyfile(rootdir+"/"+name+"/"+fy_file, rootdir+"/"+name+"/"+fy_file+".bak")
    # if falg_value =0 ,the fy_modulefile is not exsit
    tmpl_falg_value = check_filename_exit(commitdir, tmpname,name,fy_filename)
    print("the tmple file is ", tmpname)
    print("tmpl_falg_value:", tmpl_falg_value)
    if(tmpl_falg_value == 1):
        try:
            # copyfile(tmpname, deploydir+"/"+fy_filename)
            print("the commit dir is", commitdir)
            print("the rootdir dir is", rootdir)
            copyfile(commitdir+"/"+name+"/"+tmpname, rootdir+"/"+name+"/"+fy_file)
            print("hello world")
            replace_value(moduleversion, fy_file, rootdir+"/"+name)
            file_org=rootdir+"/"+name+"/"+fy_file
            file_tmp=rootdir+"/"+name+"/"+fy_filename+"/"+"default.yaml"
            linkcmd="ln" + " "+"-sn"+" "+file_org+" "+ file_tmp
            subprocess.run(linkcmd,shell=True, check=True, stdout=subprocess.PIPE)
        except IOError as e:
            print("Unable to copy file. %s" % e)
            exit(1)
        except:
            print("Unexpected error:", sys.exc_info())
            exit(1)
        print("\nFile copy done!\n")
    else:
        print("the tmple is not exsit and canot to deploy")


# the path and filename is get from  env.COMMITMES   and  env.WORKSPACE

if __name__ == '__main__':
    # falg_value = check_filename_exit(sys.argv[1], sys.argv[2])
    # fy_deploy(rootdir,fy_filename,deploydir,tmplname,modulename)
    fy_deploy(sys.argv[1], sys.argv[2], sys.argv[3],
              sys.argv[4], sys.argv[5])

#  python fy_deploy.py  /gpfs/fuyun/fy_modules/physics/ genray-201213-gompi-2019b.yaml \
#  /scratch/liuxj/workspace/python-api/fy_modules/physics genray-10.8-foss-2019b.json  \
#  genray-201213-gompi-2019b   genray/201213-gompi-2019b
