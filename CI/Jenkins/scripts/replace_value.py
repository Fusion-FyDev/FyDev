import os 
import sys
import subprocess
DEPLOY_PATH = '/gpfs/fuyun'
# FY_MODULENAME = 'genray/201213-gompi-2019b'
def replace_value(modulename,tmpname):
    # os.environ['Modulename'] = str(FY_MODULENAME)
    # os.environ['Modulename_version'] = str(FY_MODULEVERSION)
    # os.system('(module spider $Modulename) 2>/tmp/$Modulename_version.log') 
    #os.system('cmd1 && cmd2') get the direcotry of successful eb file ,and the best way is copy it to the key [build]
    cmd1 = "module use"+ DEPLOY_PATH+ "/modules/all"
    cmd2 = " module load"+ modulename
    cmd3 = "echo $EBROOTGENRAY"
    cmd = cmd1 + " && " + cmd2 + " && "+cmd3
    out=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    # print out.stdout.read()
    # for i in iter(out.stdout.readline,'b'):
    # 　　print i
    with open(tmpname) as f:
        doc = yaml.safe_load(f)       
    doc['build'] = out
    with open(file_name, 'w') as f:
        yaml.safe_dump(doc, f, default_flow_style=False)
if __name__=='__main__':
    replace_value(modulename,tmpname)
    # falg_value=check_filename_exit(sys.argv[1],sys.argv[2])
    # if(falg_value=0):
    #     tmpl_falg_value=check_filename_exit(sys.argv[1],sys.argv[3])
    #     if(tmpl_falg_value=1):
    #         cp sys.argv[3] sys.argv[4]+"/"+sys.argv[1]

    # # print(len(falg_value))
    # print(falg_value)
